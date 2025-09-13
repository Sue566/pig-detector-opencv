"""
高级检测API模块
"""

from .endpoints import create_advanced_endpoints, AdvancedPredictRequest, AdvancedPredictResponse

__all__ = [
    "create_advanced_endpoints",
    "AdvancedPredictRequest", 
    "AdvancedPredictResponse"
]