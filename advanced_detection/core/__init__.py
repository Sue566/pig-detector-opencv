"""
高级检测核心模块
"""

from .config import CLASS_DEFINITIONS, MEASUREMENT_CONFIG, get_class_info, get_class_color
from .detector import AdvancedPigDetector
from .measurement import MeasurementCalculator

__all__ = [
    "CLASS_DEFINITIONS",
    "MEASUREMENT_CONFIG", 
    "get_class_info",
    "get_class_color",
    "AdvancedPigDetector",
    "MeasurementCalculator"
]