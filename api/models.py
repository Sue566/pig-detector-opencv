"""
API数据模型
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple

class PredictRequest(BaseModel):
    """预测请求模型"""
    image_path: str
    conf: float = 0.5
    top_k: Optional[int] = 10

class PredictImageRequest(BaseModel):
    """预测图片请求模型"""
    image_path: str
    conf: float = 0.5
    top_k: Optional[int] = 10
    format: str = "jpeg"

class DetectionResult(BaseModel):
    """检测结果模型"""
    class_id: int
    class_name: str
    confidence: float
    box: List[float]  # [x1, y1, x2, y2]

class MeasurementResult(BaseModel):
    """测量结果模型"""
    pig_index: int
    pig_box: List[float]
    length_cm: Optional[float]
    length_method: Optional[str]
    used_reference: Optional[Dict[str, Any]]
    estimated_weight_kg: Optional[float]
    weight_range_kg: Optional[Tuple[float, float]]

class PredictResponse(BaseModel):
    """预测响应模型"""
    code: int
    data: Dict[str, Any]
    msg: str

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    version: str
    trained_at: str