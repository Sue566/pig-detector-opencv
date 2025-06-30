import os
from pathlib import Path
from typing import List, Tuple
import json

from PIL import Image
import torch
from torch.utils.data import Dataset


class YoloDataset(Dataset):
    """读取YOLO格式标注的数据集"""

    def __init__(self, root: str, transforms=None):
        self.root = Path(root)
        self.transforms = transforms
        exts = ["*.jpg", "*.jpeg", "*.png"]
        imgs = []
        for ext in exts:
            imgs.extend((self.root / "images").glob(ext))
        self.imgs = sorted(imgs)
        self.labels = []
        for img in self.imgs:
            label = self.root / "labels" / f"{img.stem}.txt"
            if not label.exists():
                raise FileNotFoundError(f"Label file not found for {img.name}")
            self.labels.append(label)

    def __len__(self) -> int:
        return len(self.imgs)

    def __getitem__(self, idx: int) -> Tuple[Image.Image, dict]:
        img_path = self.imgs[idx]
        label_path = self.labels[idx]

        img = Image.open(img_path).convert("RGB")
        boxes: List[List[float]] = []
        with open(label_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                # YOLO 格式: class cx cy w h (相对值)
                cx, cy, w, h = map(float, parts[1:])
                if w <= 0 or h <= 0:
                    continue
                # 转为左上角-右下角绝对坐标并裁剪到图片范围
                x1 = max((cx - w / 2) * img.width, 0)
                y1 = max((cy - h / 2) * img.height, 0)
                x2 = min((cx + w / 2) * img.width, img.width)
                y2 = min((cy + h / 2) * img.height, img.height)
                if x2 > x1 and y2 > y1:
                    boxes.append([x1, y1, x2, y2])
        target = {
            "boxes": torch.tensor(boxes, dtype=torch.float32),
            "labels": torch.ones(len(boxes), dtype=torch.int64),
        }
        if self.transforms:
            img = self.transforms(img)
        return img, target


class JsonDataset(Dataset):
    """Dataset where annotations are stored as JSON per image.

    The JSON file is expected to have either a ``bboxes`` field containing a
    list of ``[x1, y1, x2, y2]`` coordinates or the LabelMe format with a
    ``shapes`` list. Only rectangular boxes are supported.
    """

    def __init__(self, img_dir: str, ann_dir: str, transforms=None):
        self.img_dir = Path(img_dir)
        self.ann_dir = Path(ann_dir)
        self.transforms = transforms

        exts = ["*.jpg", "*.jpeg", "*.png"]
        imgs = []
        for ext in exts:
            imgs.extend(self.img_dir.glob(ext))
        self.imgs = sorted(imgs)
        self.anns = [self.ann_dir / f"{p.stem}.json" for p in self.imgs]

    def __len__(self) -> int:
        return len(self.imgs)

    def _parse_boxes(self, data: dict) -> List[List[float]]:
        boxes = []
        if "bboxes" in data and isinstance(data["bboxes"], list):
            for box in data["bboxes"]:
                if len(box) == 4:
                    x1, y1, x2, y2 = map(float, box)
                    if x2 > x1 and y2 > y1:
                        boxes.append([x1, y1, x2, y2])
        elif "shapes" in data:
            for sh in data["shapes"]:
                pts = sh.get("points")
                if not pts:
                    continue
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
                if x2 > x1 and y2 > y1:
                    boxes.append([x1, y1, x2, y2])
        return boxes

    def __getitem__(self, idx: int) -> Tuple[Image.Image, dict]:
        img_path = self.imgs[idx]
        ann_path = self.anns[idx]
        img = Image.open(img_path).convert("RGB")
        boxes: List[List[float]] = []
        if ann_path.exists():
            with open(ann_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    boxes = self._parse_boxes(data)
                except Exception:
                    boxes = []
        target = {
            "boxes": torch.tensor(boxes, dtype=torch.float32),
            "labels": torch.ones(len(boxes), dtype=torch.int64),
        }
        if self.transforms:
            img = self.transforms(img)
        return img, target


def build_dataset(root: str, transforms=None) -> Dataset:
    """Auto-detect dataset type based on directory structure.

    Supported layouts::

        dataset/images/  dataset/labels/
        dataset/train/images/  dataset/train/labels/
        dataset/train_img/  dataset/train_json/ (JSON annotations)

    When ``train`` and ``val`` folders are both present, pass each subdirectory
    separately via ``train_dirs`` and ``val_dirs`` in the config.
    """
    root_path = Path(root)
    if (root_path / "images").exists() and (root_path / "labels").exists():
        return YoloDataset(root, transforms=transforms)
    if (root_path / "train_img").exists() and (root_path / "train_json").exists():
        return JsonDataset(root_path / "train_img", root_path / "train_json", transforms=transforms)
    if (root_path / "train" / "images").exists() and (root_path / "train" / "labels").exists():
        return YoloDataset(root_path / "train", transforms=transforms)
    raise ValueError(f"Unrecognized dataset structure at {root}")
