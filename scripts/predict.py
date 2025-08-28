import argparse
from pathlib import Path
import sys
import time
import shutil
import os

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.logging_utils import setup_logging

try:
    import yaml
except ImportError:  # pragma: no cover - handled at runtime
    yaml = None

torch = None
Image = None
F = None
estimate_length_weight = None
requests = None
cv2 = None


def load_config(path: str):
    if yaml is None:
        raise RuntimeError(
            "pyyaml is not installed. Please install dependencies from requirements.txt"
        )
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_model(cfg_path: str, weight_path: str):
    """Load model and return it along with optional metadata."""
    global torch
    if torch is None:
        import importlib
        torch = importlib.import_module('torch')
    from utils.model import create_model
    cfg = load_config(cfg_path)
    model = create_model(cfg['num_classes'] + 1)
    data = torch.load(weight_path, map_location='cpu')
    meta = {}
    if isinstance(data, dict) and any(k in data for k in ('model', 'state_dict')):
        state_dict = data.get('model') or data.get('state_dict')
        meta = data.get('meta', {})
    else:
        state_dict = data
    model.load_state_dict(state_dict)
    model.eval()
    return model, meta


def _ensure_deps_loaded():
    """Load heavy dependencies only when actually needed."""
    global Image, F, estimate_length_weight, cv2
    if Image is None or F is None:
        from PIL import Image as PILImage
        import torchvision.transforms.functional as TF
        Image = PILImage
        F = TF
    if estimate_length_weight is None:
        from utils.estimate import estimate_length_weight as elw
        estimate_length_weight = elw
    if cv2 is None:
        try:
            import importlib
            cv2 = importlib.import_module('cv2')
        except ImportError:
            print("\n错误: 未安装OpenCV库。请运行以下命令安装:")
            print("pip install opencv-python\n")
            raise


def _ensure_requests():
    global requests
    if requests is None:
        import importlib
        requests = importlib.import_module("requests")


def _download_if_url(image_path: str):
    """Download image if given a URL. Returns local path and temp dir."""
    if image_path.startswith("http://") or image_path.startswith("https://"):
        _ensure_requests()
        timestamp = str(int(time.time()))
        temp_dir = ROOT / "temp" / timestamp
        temp_dir.mkdir(parents=True, exist_ok=True)
        local_path = temp_dir / Path(image_path).name
        resp = requests.get(image_path, stream=True)
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return str(local_path), temp_dir
    return image_path, None


def predict_image_with_model(model, image_path: str, *, conf: float = 0.5, top_k: int | None = 10):
    """Run inference with a pre-loaded model."""
    _ensure_deps_loaded()
    local_path, temp_dir = _download_if_url(image_path)
    img = Image.open(local_path).convert('RGB')
    tensor = F.to_tensor(img)
    outputs = model([tensor])[0]
    boxes = outputs['boxes'].detach().numpy()
    scores = outputs['scores'].detach().numpy()

    results = []
    for box, score in zip(boxes, scores):
        if score < conf:
            continue
        x1, y1, x2, y2 = box
        length, weight = estimate_length_weight((x1, y1, x2, y2))
        results.append({
            'box': [float(x1), float(y1), float(x2), float(y2)],
            'score': float(score),
            'length': float(length),
            'weight': float(weight),
        })
        if top_k is not None and len(results) >= top_k:
            break
    if temp_dir:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return results


def predict_image(cfg_path: str, weight_path: str, image_path: str, *, conf: float = 0.5, top_k: int | None = 10):
    """Run inference on a single image and return results.

    Parameters
    ----------
    cfg_path : str
        Path to configuration YAML.
    weight_path : str
        Path to model weights.
    image_path : str
        Path to the image file.
    conf : float, optional
        Score threshold. Only predictions above this are returned.
    top_k : int | None, optional
        Maximum number of results to return. ``None`` means no limit.
    """
    model, _ = load_model(cfg_path, weight_path)
    return predict_image_with_model(model, image_path, conf=conf, top_k=top_k)


def draw_boxes_on_image(image_path, results, output_path=None):
    """在图片上绘制检测结果的边界框
    
    参数:
    image_path: 原始图片路径
    results: 检测结果列表
    output_path: 输出图片路径，如果为None则显示图片而不保存
    """
    try:
        _ensure_deps_loaded()
        
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            print(f"无法读取图片: {image_path}")
            return
    
        # 在图片上绘制边界框
        for r in results:
            x1, y1, x2, y2 = map(int, r['box'])  # 转换为整数坐标
            score = r['score']
            length = r['length']
            weight = r['weight']
            
            # 绘制红色边界框
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # 添加文本标签
            label = f"Pig: {score:.2f}, L:{length:.1f}, W:{weight:.1f}kg"
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # 保存或显示图片
        if output_path:
            # 确保输出路径有有效的图像扩展名
            if not any(output_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']):
                output_path = output_path + '.jpg'  # 添加默认扩展名
            cv2.imwrite(output_path, img)
            print(f"已保存标注图片到: {output_path}")
        else:
            # 显示图片
            cv2.imshow("Detection Result", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    except ImportError:
        print("无法绘制边界框: 未安装OpenCV库")
        print("请运行以下命令安装OpenCV:")
        print("pip install opencv-python")

def main(args):
    logger = setup_logging("predict")
    logger.info("Running prediction on %s", args.image)
    results = predict_image(args.config, args.weights, args.image)
    if not results:
        logger.info("Image does not contain pigs.")
        print("Image does not contain pigs.")
        return
    
    # 输出检测结果
    for r in results:
        x1, y1, x2, y2 = r['box']
        msg = (
            f"pig detected at [{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}], length={r['length']:.1f}, weight~{r['weight']:.1f}kg"
        )
        logger.info(msg)
        print(msg)
    
    # 在图片上绘制边界框
    if args.draw:
        try:
            if args.output:
                # 保存到指定路径
                draw_boxes_on_image(args.image, results, args.output)
            else:
                # 显示图片
                draw_boxes_on_image(args.image, results)
        except Exception as e:
            logger.error(f"绘制边界框时出错: {e}")
            print(f"绘制边界框时出错: {e}")
            print("如果是OpenCV相关错误，请运行: pip install opencv-python")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.yaml')
    parser.add_argument('--weights', default='models/best_model.pth')
    parser.add_argument('--image', required=True)
    parser.add_argument('--draw', action='store_true', help='在图片上绘制检测结果')
    parser.add_argument('--output', help='保存标注后的图片路径')
    args = parser.parse_args()
    main(args)
