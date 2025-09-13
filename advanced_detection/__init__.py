"""
高级猪检测模块
提供精确的长度测量、重量估算和高级可视化功能
"""

__version__ = "1.0.0"
__author__ = "Pig Detector Team"

from .core.detector import AdvancedPigDetector
from .core.measurement import MeasurementCalculator
from .visualization.renderer import AdvancedRenderer

# 尝试导入API端点，如果FastAPI不可用则跳过
try:
    from .api.endpoints import create_advanced_endpoints
    __all__ = [
        "AdvancedPigDetector",
        "MeasurementCalculator", 
        "AdvancedRenderer",
        "create_advanced_endpoints"
    ]
except ImportError:
    __all__ = [
        "AdvancedPigDetector",
        "MeasurementCalculator", 
        "AdvancedRenderer"
    ]