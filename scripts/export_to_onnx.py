import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import yaml
except ImportError:  # pragma: no cover - handled at runtime
    yaml = None
torch = None


def load_config(path: str):
    if yaml is None:
        raise RuntimeError(
            "pyyaml is not installed. Please install dependencies from requirements.txt"
        )
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def export(cfg_path: str, weights: str, output: str, conf: float = 0.25, iou: float = 0.45, top_k: int | None = 100):
    global torch
    if torch is None:
        import importlib
        torch = importlib.import_module('torch')
    from utils.model import create_model
    import torchvision
    cfg = load_config(cfg_path)
    model = create_model(cfg['num_classes'] + 1)
    state_dict = torch.load(weights, map_location='cpu')
    model.load_state_dict(state_dict)
    model.eval()

    class ModelWithNMS(torch.nn.Module):
        def __init__(self, base: torch.nn.Module):
            super().__init__()
            self.base = base

        def forward(self, x):
            out = self.base(x)[0]
            boxes = out['boxes']
            scores = out['scores']
            labels = out['labels']

            mask = scores > conf
            boxes = boxes[mask]
            scores = scores[mask]
            labels = labels[mask]
            keep = torchvision.ops.nms(boxes, scores, iou)
            if top_k is not None:
                keep = keep[: top_k]
            boxes = boxes[keep]
            scores = scores[keep]
            labels = labels[keep]
            return boxes, scores, labels

    wrapped = ModelWithNMS(model)

    dummy = torch.zeros(1, 3, 640, 640)
    torch.onnx.export(
        wrapped,
        dummy,
        output,
        opset_version=11,
        input_names=["images"],
        output_names=["boxes", "scores", "labels"],
    )
    print(f'ONNX model saved to {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.yaml')
    parser.add_argument('--weights', default='models/best_model.pth')
    parser.add_argument('--output', default='models/model.onnx')
    parser.add_argument('--conf', type=float, default=0.25, help='score threshold')
    parser.add_argument('--iou', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--top-k', type=int, default=100, help='max detections to keep')
    args = parser.parse_args()
    export(args.config, args.weights, args.output, args.conf, args.iou, args.top_k)
