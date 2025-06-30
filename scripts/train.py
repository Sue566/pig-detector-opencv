import argparse
from pathlib import Path
from datetime import datetime
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.logging_utils import setup_logging

try:
    import yaml
except ImportError:  # pragma: no cover - handled at runtime
    yaml = None

try:
    import torch
    from torch.utils.data import DataLoader
    from torchvision.ops import misc as misc_nn_ops
except ImportError:  # pragma: no cover - handled at runtime
    torch = None

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover - handled at runtime
    tqdm = None



def load_config(path: str):
    if yaml is None:
        raise RuntimeError(
            "pyyaml is not installed. Please install dependencies from requirements.txt"
        )
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def train(args):
    if torch is None:
        raise RuntimeError(
            "PyTorch is not installed. Please install dependencies from requirements.txt"
        )
    if tqdm is None:
        raise RuntimeError(
            "tqdm is not installed. Please install dependencies from requirements.txt"
        )
    # 延迟导入其余依赖，避免在仅查看 --help 时出错
    from utils.dataset import build_dataset
    from utils.model import create_model
    from utils.transforms import get_train_transforms
    logger = setup_logging("train")
    logger.info("Training started")
    logger.info("Loading config from %s", args.config)
    cfg = load_config(args.config)

    # 支持多个训练目录，自动识别其结构
    train_dirs = cfg.get('train_dirs') or cfg.get('train_dir')
    if isinstance(train_dirs, (list, tuple)):
        from torch.utils.data import ConcatDataset
        datasets = [build_dataset(d, transforms=get_train_transforms()) for d in train_dirs]
        train_ds = ConcatDataset(datasets)
    else:
        train_ds = build_dataset(train_dirs, transforms=get_train_transforms())

    train_loader = DataLoader(train_ds, batch_size=cfg['batch_size'], shuffle=True, collate_fn=lambda x: tuple(zip(*x)))

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = create_model(cfg['num_classes'] + 1)  # +1 for background
    model.to(device)

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=cfg['learning_rate'], momentum=0.9, weight_decay=0.0005)

    for epoch in range(cfg['num_epochs']):
        model.train()
        # tqdm 显示当前 epoch 的批次进度
        epoch_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{cfg['num_epochs']}")
        for images, targets in epoch_bar:
            images = list(img.to(device) for img in images)
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

            loss_dict = model(images, targets)
            losses = sum(loss for loss in loss_dict.values())

            optimizer.zero_grad()
            losses.backward()
            optimizer.step()

            epoch_bar.set_postfix(loss=f"{losses.item():.4f}")

        # 每个 epoch 结束打印提示，防止用户误以为卡住
        logger.info("Epoch %s completed", epoch + 1)

    Path(cfg['model_dir']).mkdir(parents=True, exist_ok=True)
    meta = {"version": args.version, "trained_at": datetime.now().isoformat()}
    out_path = Path(cfg['model_dir']) / f"{args.version}_model.pth"
    torch.save({"model": model.state_dict(), "meta": meta}, out_path)
    logger.info("Training finished, model saved to %s", out_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train pig detector')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--version', default='v1', help='Model version tag')
    args = parser.parse_args()
    train(args)
