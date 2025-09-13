"""
测量计算模块
提供基于参考物体的精确长度和重量计算
"""

import math
from typing import Optional, Tuple, List, Dict, Any
from .config import MEASUREMENT_CONFIG


class MeasurementCalculator:
    """测量计算器"""
    
    def __init__(self):
        self.config = MEASUREMENT_CONFIG
    
    def yolo_to_pixel(self, yolo_coords: List[float], img_width: int, img_height: int) -> Tuple[List[float], float, float]:
        """将YOLO格式坐标转换为像素坐标"""
        x_center, y_center, width, height = yolo_coords
        
        # 转换为像素坐标
        x_center_px = x_center * img_width
        y_center_px = y_center * img_height
        width_px = width * img_width
        height_px = height * img_height
        
        # 计算边界框坐标
        x1 = x_center_px - width_px / 2
        y1 = y_center_px - height_px / 2
        x2 = x_center_px + width_px / 2
        y2 = y_center_px + height_px / 2
        
        return [x1, y1, x2, y2], width_px, height_px
    
    def calculate_box_dimensions(self, box: List[float]) -> Tuple[float, float, float]:
        """计算边界框的尺寸"""
        x1, y1, x2, y2 = box
        width_px = abs(x2 - x1)
        height_px = abs(y2 - y1)
        length_px = max(width_px, height_px)  # 取较长边作为长度
        return width_px, height_px, length_px
    
    def calculate_pig_length_from_ruler(self, pig_box: List[float], ruler_box: List[float], 
                                      ruler_length_cm: float = None) -> Optional[float]:
        """根据尺子计算猪的长度"""
        if not pig_box or not ruler_box:
            return None
        
        if ruler_length_cm is None:
            ruler_length_cm = self.config["ruler"]["default_length_cm"]
        
        # 计算猪的像素长度（取较长的边）
        _, _, pig_length_px = self.calculate_box_dimensions(pig_box)
        
        # 计算尺子的像素长度（取较长的边）
        _, _, ruler_length_px = self.calculate_box_dimensions(ruler_box)
        
        # 计算比例和猪的实际长度
        if ruler_length_px > 0:
            scale = ruler_length_cm / ruler_length_px  # cm/pixel
            pig_length_cm = pig_length_px * scale
            return pig_length_cm
        
        return None
    
    def calculate_pig_length_from_base(self, pig_box: List[float], base_box: List[float],
                                     base_length_cm: float = None, base_width_cm: float = None) -> Optional[float]:
        """根据底座计算猪的长度"""
        if not pig_box or not base_box:
            return None
        
        if base_length_cm is None:
            base_length_cm = self.config["base"]["default_length_cm"]
        if base_width_cm is None:
            base_width_cm = self.config["base"]["default_width_cm"]
        
        # 计算猪的像素长度（取较长的边）
        _, _, pig_length_px = self.calculate_box_dimensions(pig_box)
        
        # 计算底座的像素尺寸
        base_width_px, base_height_px, _ = self.calculate_box_dimensions(base_box)
        
        # 确定底座的长边和短边对应关系
        if base_width_px > base_height_px:
            # 底座的宽度对应长边，高度对应短边
            scale = base_length_cm / base_width_px
        else:
            # 底座的高度对应长边，宽度对应短边
            scale = base_length_cm / base_height_px
        
        pig_length_cm = pig_length_px * scale
        return pig_length_cm
    
    def estimate_pig_weight(self, length_cm: Optional[float]) -> Tuple[Optional[float], Optional[Tuple[float, float]]]:
        """根据猪的长度估算重量"""
        if length_cm is None or length_cm <= 0:
            return None, None
        
        # 使用经验公式：重量(kg) = k * 长度(cm)^n
        k = self.config["weight"]["formula_coefficient"]
        n = self.config["weight"]["formula_exponent"]
        range_pct = self.config["weight"]["range_percentage"]
        
        estimated_weight = k * (length_cm ** n)
        
        # 给出重量范围
        weight_min = estimated_weight * (1 - range_pct)
        weight_max = estimated_weight * (1 + range_pct)
        
        return estimated_weight, (weight_min, weight_max)
    
    def estimate_pig_length_from_pixels(self, pig_box: List[float], img_width: int, img_height: int) -> Optional[float]:
        """基于像素尺寸估算猪的长度（无参考物体时使用）"""
        if not pig_box:
            return None
        
        # 计算猪的像素长度
        _, _, pig_length_px = self.calculate_box_dimensions(pig_box)
        
        # 基于经验数据的估算
        # 假设图片中猪的长度通常占图片较短边的30-70%
        # 成年猪的长度通常在80-150cm之间
        img_shorter_side = min(img_width, img_height)
        pig_ratio = pig_length_px / img_shorter_side
        
        # 根据猪在图片中的比例估算实际长度
        if pig_ratio > 0.6:
            # 猪占比较大，可能是近距离拍摄，估算为较大的猪
            estimated_length = 120 + (pig_ratio - 0.6) * 100  # 120-140cm
        elif pig_ratio > 0.4:
            # 中等比例
            estimated_length = 100 + (pig_ratio - 0.4) * 100  # 100-120cm
        elif pig_ratio > 0.2:
            # 较小比例
            estimated_length = 80 + (pig_ratio - 0.2) * 100   # 80-100cm
        else:
            # 很小比例，可能是远距离或小猪
            estimated_length = 60 + pig_ratio * 100           # 60-80cm
        
        return min(max(estimated_length, 50), 180)  # 限制在50-180cm范围内

    def calculate_comprehensive_measurements(self, pig_box: Optional[List[float]], 
                                           ruler_box: Optional[List[float]], 
                                           base_box: Optional[List[float]],
                                           ruler_length_cm: float = None,
                                           base_length_cm: float = None,
                                           base_width_cm: float = None,
                                           img_width: int = None,
                                           img_height: int = None) -> Dict[str, Any]:
        """综合计算测量结果"""
        
        measurements = {
            "length_cm": None,
            "weight_kg": None,
            "weight_range_kg": None,
            "calculation_method": "未知",
            "reference_object": None,
            "confidence": "low"
        }
        
        if pig_box is None:
            measurements["calculation_method"] = "无猪检测结果"
            return measurements
        
        # 优先使用尺子计算
        if ruler_box is not None:
            length_cm = self.calculate_pig_length_from_ruler(pig_box, ruler_box, ruler_length_cm)
            if length_cm is not None:
                measurements["length_cm"] = length_cm
                measurements["calculation_method"] = f"基于尺子({ruler_length_cm or self.config['ruler']['default_length_cm']}cm)"
                measurements["reference_object"] = "ruler"
                measurements["confidence"] = "high"
        
        # 其次使用底座计算
        if measurements["length_cm"] is None and base_box is not None:
            length_cm = self.calculate_pig_length_from_base(pig_box, base_box, base_length_cm, base_width_cm)
            if length_cm is not None:
                measurements["length_cm"] = length_cm
                base_l = base_length_cm or self.config["base"]["default_length_cm"]
                base_w = base_width_cm or self.config["base"]["default_width_cm"]
                measurements["calculation_method"] = f"基于底座({base_l}×{base_w}cm)"
                measurements["reference_object"] = "base"
                measurements["confidence"] = "medium"
        
        # 最后使用像素估算（无参考物体时）
        if measurements["length_cm"] is None and img_width and img_height:
            length_cm = self.estimate_pig_length_from_pixels(pig_box, img_width, img_height)
            if length_cm is not None:
                measurements["length_cm"] = length_cm
                measurements["calculation_method"] = "基于像素尺寸估算"
                measurements["reference_object"] = "pixel_estimation"
                measurements["confidence"] = "low"
        
        # 计算重量
        if measurements["length_cm"] is not None:
            weight_kg, weight_range = self.estimate_pig_weight(measurements["length_cm"])
            measurements["weight_kg"] = weight_kg
            measurements["weight_range_kg"] = weight_range
        
        return measurements
    
    def get_length_annotation_points(self, pig_box: List[float]) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """获取长度标注线的起止点"""
        x1, y1, x2, y2 = pig_box
        
        # 计算边界框的长边
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        if width >= height:
            # 水平方向是长边，在顶部绘制标注线
            start_point = (int(x1), int(y1 - 20))
            end_point = (int(x2), int(y1 - 20))
        else:
            # 垂直方向是长边，在左侧绘制标注线
            start_point = (int(x1 - 20), int(y1))
            end_point = (int(x1 - 20), int(y2))
        
        return start_point, end_point