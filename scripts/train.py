import argparse
from pathlib import Path
from datetime import datetime
import shutil
import sys

# ---- 项目根路径注入 ----
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.logging_utils import setup_logging

# ---- 顶层 collate：Windows 多进程需要可 picklable 的函数（lambda 不可）----
def yolo_collate(batch):
    # batch: List[Tuple[image, target]]
    return tuple(zip(*batch))

# ---- 依赖延迟导入 ----
try:
    import yaml
except ImportError:
    yaml = None

try:
    import torch
    from torch.utils.data import DataLoader
except ImportError:
    torch = None

try:
    from tqdm.auto import tqdm
except ImportError:
    tqdm = None


def load_config(path: str):
    if yaml is None:
        raise RuntimeError(
            "pyyaml is not installed. Please install dependencies from requirements.txt"
        )
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def process_negative_images(cfg):
    """
    将 negative_dir 里的图片移动到第一个 train_dir 下的 images，
    并在 labels 下创建同名空 txt 作为负样本。
    """
    neg_dir = Path(cfg.get("negative_dir", "negative"))
    if not neg_dir.exists():
        return 0

    train_dirs = cfg.get("train_dirs") or cfg.get("train_dir")
    if isinstance(train_dirs, (list, tuple)):
        dest_root = Path(train_dirs[0])
    else:
        dest_root = Path(train_dirs)

    images_dest = dest_root / "images"
    labels_dest = dest_root / "labels"
    images_dest.mkdir(parents=True, exist_ok=True)
    labels_dest.mkdir(parents=True, exist_ok=True)

    moved = 0
    for img in neg_dir.iterdir():
        if not img.is_file():
            continue
        dest_img = images_dest / img.name
        dest_lbl = labels_dest / f"{img.stem}.txt"
        if dest_img.exists():
            # 已存在则删除源，避免重复
            try:
                img.unlink()
            except Exception:
                pass
            continue
        shutil.move(str(img), dest_img)
        # 空标注文件 = 负样本
        if not dest_lbl.exists():
            dest_lbl.write_text("", encoding="utf-8")
        moved += 1

    # 目录空了就尝试删除
    try:
        neg_dir.rmdir()
    except OSError:
        pass
    return moved


def resolve_device(arg_device: str) -> "torch.device":
    # 支持 cuda:X / cpu / mps
    if arg_device.startswith("cuda"):
        if torch.cuda.is_available():
            return torch.device(arg_device)
        else:
            print("[WARN] CUDA not available, fallback to CPU.")
            return torch.device("cpu")
    if arg_device == "mps":
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            print("[WARN] MPS not available, fallback to CPU.")
            return torch.device("cpu")
    return torch.device("cpu")


def train(args):
    if torch is None:
        raise RuntimeError(
            "PyTorch is not installed. Please install dependencies from requirements.txt"
        )
    if tqdm is None:
        raise RuntimeError(
            "tqdm is not installed. Please install dependencies from requirements.txt"
        )

    from utils.dataset import build_dataset
    from utils.model import create_model
    from utils.transforms import get_train_transforms

    logger = setup_logging("train")
    logger.info("Training started")
    logger.info("Loading config from %s", args.config)
    cfg = load_config(args.config)

    # cuDNN 自动挑最优算法（卷积更快）
    torch.backends.cudnn.benchmark = True

    moved = process_negative_images(cfg)
    if moved:
        logger.info("Added %d negative images (as negatives)", moved)

    # 聚合多个训练目录
    train_dirs = cfg.get('train_dirs') or cfg.get('train_dir')
    if isinstance(train_dirs, (list, tuple)):
        from torch.utils.data import ConcatDataset
        datasets = []
        for d in train_dirs:
            ds = build_dataset(d, transforms=get_train_transforms())
            logger.info("Loaded %s with %d images", d, len(ds))
            datasets.append(ds)
        train_ds = ConcatDataset(datasets)
    else:
        train_ds = build_dataset(train_dirs, transforms=get_train_transforms())
        logger.info("Loaded %s with %d images", train_dirs, len(train_ds))

    # 设备先解析，再构建 DataLoader（决定 pin_memory）
    device = resolve_device(args.device)
    logger.info("Using device: %s", device)

    workers = max(0, int(args.workers))
    use_pin = (device.type == "cuda")
    train_loader = DataLoader(
        train_ds,
        batch_size=cfg['batch_size'],
        shuffle=True,
        num_workers=workers,
        pin_memory=use_pin,
        persistent_workers=(workers > 0),
        collate_fn=yolo_collate
    )

    # 模型
    model = create_model(cfg['num_classes'] + 1)  # +1 for background
    if args.compile and hasattr(torch, "compile"):
        try:
            model = torch.compile(model)  # 需要 PyTorch 2.x
            logger.info("torch.compile enabled")
        except Exception as e:
            logger.warning("torch.compile failed, continuing without it: %s", e)
    model.to(device)

    # 恢复
    if args.resume:
        logger.info("Resuming from %s", args.resume)
        data = torch.load(args.resume, map_location=device)
        if isinstance(data, dict) and any(k in data for k in ('model', 'state_dict')):
            state_dict = data.get('model') or data.get('state_dict')
        else:
            state_dict = data
        model.load_state_dict(state_dict, strict=False)
        logger.info("Weights loaded")

    # 优化器
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=cfg['learning_rate'], momentum=0.9, weight_decay=0.0005)

    # AMP（CUDA/MPS 上开启）
    use_amp = device.type in ("cuda", "mps")
    # 新写法（去掉旧版警告）
    try:
        from torch import amp
        scaler = amp.GradScaler('cuda', enabled=(use_amp and device.type == "cuda"))
        autocast_ctx = torch.autocast(device_type='cuda', enabled=(device.type == "cuda"))
    except Exception:
        # 兼容老写法
        scaler = torch.cuda.amp.GradScaler(enabled=(use_amp and device.type == "cuda"))
        autocast_ctx = torch.cuda.amp.autocast(enabled=(device.type == "cuda"))

    accum = max(1, int(args.accum))  # 梯度累积，放大有效 batch
    global_step = 0

    for epoch in range(cfg['num_epochs']):
        model.train()
        epoch_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{cfg['num_epochs']}")
        optimizer.zero_grad(set_to_none=True)

        for i, (images, targets) in enumerate(epoch_bar):
            # non_blocking + pin_memory 提速 Host->Device
            if isinstance(images, (list, tuple)):
                images = [img.to(device, non_blocking=True) for img in images]
            else:
                images = images.to(device, non_blocking=True)

            if isinstance(targets, (list, tuple)):
                targets = [{k: v.to(device, non_blocking=True) for k, v in t.items()} for t in targets]
            else:
                targets = {k: v.to(device, non_blocking=True) for k, v in targets.items()}

            # 前向 + 反向
            if use_amp and device.type == "cuda":
                with autocast_ctx:
                    loss_dict = model(images, targets)
                    losses = sum(loss for loss in loss_dict.values())
                scaler.scale(losses / accum).backward()
            else:
                loss_dict = model(images, targets)
                losses = sum(loss for loss in loss_dict.values())
                (losses / accum).backward()

            # 累积到一定步数再 step
            if (i + 1) % accum == 0:
                if use_amp and device.type == "cuda":
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                optimizer.zero_grad(set_to_none=True)

            epoch_bar.set_postfix(loss=f"{losses.item():.4f}")
            global_step += 1

        logger.info("Epoch %s completed", epoch + 1)

    # 保存
    Path(cfg['model_dir']).mkdir(parents=True, exist_ok=True)
    meta = {"version": args.version, "trained_at": datetime.now().isoformat()}
    out_path = Path(cfg['model_dir']) / f"{args.version}_model.pth"
    torch.save({"model": model.state_dict(), "meta": meta}, out_path)
    logger.info("Training finished, model saved to %s", out_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train pig detector')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--version', default='v1', help='Model version tag')
    parser.add_argument('--resume', help='Path to existing weights to resume training from')

    # 加速/稳定参数
    parser.add_argument('--device', default='cuda:0', help='cuda:0 / cpu / mps')
    parser.add_argument('--workers', type=int, default=0, help='DataLoader workers (Win 上先用 0，OK 再升 2/4/6)')
    parser.add_argument('--accum', type=int, default=1, help='gradient accumulation steps')
    parser.add_argument('--compile', action='store_true', help='use torch.compile if available (PyTorch 2.x)')

    args = parser.parse_args()
    train(args)
