import os
from pathlib import Path
from typing import List, Tuple

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
        with open(label_path, "r") as f:
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
