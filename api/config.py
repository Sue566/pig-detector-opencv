"""
API配置文件
"""
import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parents[1]

# 模型配置
CFG_PATH = Path(os.environ.get("CFG_PATH", ROOT_DIR / "config.yaml")).resolve()
WEIGHTS_PATH = Path(os.environ.get("WEIGHTS_PATH", ROOT_DIR / "models" / "v1_model.pth")).resolve()

# API配置
API_HOST = "0.0.0.0"
API_PORT = 8092
API_TITLE = "Pig Detector API"
API_VERSION = "2.0.0"

# 文件存储配置
MEDIA_BASE_URL = "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig"
UPLOAD_DIR = ROOT_DIR / "uploads"
TEMP_DIR = ROOT_DIR / "temp"

# 确保目录存在
UPLOAD_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# 检测结果类别映射
DETECTION_CLASSES = {
    0: "pig",
    1: "ruler", 
    2: "base"
}

# 可视化配置
VISUALIZATION_CONFIG = {
    "colors": {
        "pig": (255, 0, 0),      # 红色
        "ruler": (0, 0, 255),    # 蓝色
        "base": (0, 255, 0),     # 绿色
        "scale": (255, 165, 0)   # 橙色
    },
    "line_width": 3,
    "font_size": 16,
    "font_size_small": 14
}