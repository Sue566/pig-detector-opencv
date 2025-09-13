#!/usr/bin/env python3
"""
测量工具模块 - 用于计算猪的长度和重量
"""
import math

def yolo_to_pixel(yolo_coords, img_width, img_height):
    """
    将YOLO格式坐标转换为像素坐标
    
    Args:
        yolo_coords: [x_center, y_center, width, height] (归一化坐标)
        img_width: 图片宽度(像素)
        img_height: 图片高度(像素)
    
    Returns:
        tuple: (边界框坐标[x1,y1,x2,y2], 宽度像素, 高度像素)
    """
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

def calculate_pig_length_from_ruler(pig_box, ruler_box, ruler_length_cm=30):
    """
    根据尺子计算猪的长度
    
    Args:
        pig_box: 猪的边界框 [x1, y1, x2, y2]
        ruler_box: 尺子的边界框 [x1, y1, x2, y2]
        ruler_length_cm: 尺子的实际长度(cm)，默认30cm
    
    Returns:
        float: 猪的长度(cm)，如果计算失败返回None
    """
    pig_x1, pig_y1, pig_x2, pig_y2 = pig_box
    ruler_x1, ruler_y1, ruler_x2, ruler_y2 = ruler_box
    
    # 计算猪的像素长度（取较长的边）
    pig_width_px = abs(pig_x2 - pig_x1)
    pig_height_px = abs(pig_y2 - pig_y1)
    pig_length_px = max(pig_width_px, pig_height_px)
    
    # 计算尺子的像素长度（取较长的边）
    ruler_width_px = abs(ruler_x2 - ruler_x1)
    ruler_height_px = abs(ruler_y2 - ruler_y1)
    ruler_length_px = max(ruler_width_px, ruler_height_px)
    
    # 计算比例和猪的实际长度
    if ruler_length_px > 0:
        scale = ruler_length_cm / ruler_length_px  # cm/pixel
        pig_length_cm = pig_length_px * scale
        return pig_length_cm
    return None

def calculate_pig_length_from_base(pig_box, base_box, base_length_cm=60, base_width_cm=40):
    """
    根据底座计算猪的长度
    
    Args:
        pig_box: 猪的边界框 [x1, y1, x2, y2]
        base_box: 底座的边界框 [x1, y1, x2, y2]
        base_length_cm: 底座长度(cm)，默认60cm
        base_width_cm: 底座宽度(cm)，默认40cm
    
    Returns:
        float: 猪的长度(cm)，如果计算失败返回None
    """
    pig_x1, pig_y1, pig_x2, pig_y2 = pig_box
    base_x1, base_y1, base_x2, base_y2 = base_box
    
    # 计算猪的像素长度（取较长的边）
    pig_width_px = abs(pig_x2 - pig_x1)
    pig_height_px = abs(pig_y2 - pig_y1)
    pig_length_px = max(pig_width_px, pig_height_px)
    
    # 计算底座的像素尺寸
    base_width_px = abs(base_x2 - base_x1)
    base_height_px = abs(base_y2 - base_y1)
    
    # 确定底座的长边和短边对应关系
    if base_width_px > base_height_px:
        # 底座的宽度对应60cm，高度对应40cm
        scale = base_length_cm / base_width_px
    else:
        # 底座的高度对应60cm，宽度对应40cm
        scale = base_length_cm / base_height_px
    
    pig_length_cm = pig_length_px * scale
    return pig_length_cm

def estimate_pig_weight(length_cm, formula_type="standard"):
    """
    根据猪的长度估算重量
    
    Args:
        length_cm: 猪的长度(cm)
        formula_type: 计算公式类型 ("standard", "young_pig", "medium_pig")
    
    Returns:
        tuple: (估算重量(kg), (最小重量, 最大重量))
    """
    if length_cm is None:
        return None, None
    
    # 针对您数据集中猪的体重范围优化 (2.5-3.78kg)
    # 基于实际数据分布调整公式参数
    formulas = {
        # 标准公式 - 针对2.5-3.78kg体重范围优化
        "standard": {
            "base_weight": 2.5,      # 基础体重2.5kg
            "length_factor": 0.035,  # 长度影响系数
            "length_threshold": 30,  # 基准长度30cm
            "variance": 0.12         # 12%的变化范围
        },
        # 保守估算 - 倾向于较低体重
        "young_pig": {
            "base_weight": 2.3,
            "length_factor": 0.028,
            "length_threshold": 30,
            "variance": 0.10
        },
        # 积极估算 - 倾向于较高体重
        "medium_pig": {
            "base_weight": 2.7,
            "length_factor": 0.042,
            "length_threshold": 30,
            "variance": 0.15
        }
    }
    
    formula = formulas.get(formula_type, formulas["standard"])
    
    # 线性公式：重量(kg) = base_weight + length_factor * (长度 - threshold)
    # 这样可以更好地控制在2.5-3.78kg范围内
    length_diff = max(0, length_cm - formula["length_threshold"])
    estimated_weight = formula["base_weight"] + formula["length_factor"] * length_diff
    
    # 确保体重为正值
    estimated_weight = max(0.5, estimated_weight)
    
    # 给出重量范围
    variance = formula["variance"]
    weight_min = max(1.5, estimated_weight * (1 - variance))
    weight_max = min(8.0, estimated_weight * (1 + variance))
    
    return estimated_weight, (weight_min, weight_max)

def calculate_pig_measurements(pig_box, ruler_box=None, base_box=None, 
                             ruler_length_cm=30, base_length_cm=60, base_width_cm=40,
                             weight_formula="standard"):
    """
    综合计算猪的测量数据
    
    Args:
        pig_box: 猪的边界框 [x1, y1, x2, y2]
        ruler_box: 尺子的边界框（可选）
        base_box: 底座的边界框（可选）
        ruler_length_cm: 尺子长度(cm)
        base_length_cm: 底座长度(cm)
        base_width_cm: 底座宽度(cm)
        weight_formula: 重量计算公式类型
    
    Returns:
        dict: 包含长度、重量、计算方法等信息的字典
    """
    result = {
        "length_cm": None,
        "weight_kg": None,
        "weight_range": None,
        "calculation_method": "未知",
        "confidence": "低"
    }
    
    # 计算长度
    if pig_box is not None:
        if ruler_box is not None:
            # 优先使用尺子计算
            result["length_cm"] = calculate_pig_length_from_ruler(
                pig_box, ruler_box, ruler_length_cm
            )
            result["calculation_method"] = f"基于尺子({ruler_length_cm}cm)"
            result["confidence"] = "高"
        elif base_box is not None:
            # 使用底座计算
            result["length_cm"] = calculate_pig_length_from_base(
                pig_box, base_box, base_length_cm, base_width_cm
            )
            result["calculation_method"] = f"基于底座({base_length_cm}x{base_width_cm}cm)"
            result["confidence"] = "中"
    
    # 计算重量
    if result["length_cm"] is not None:
        weight_result = estimate_pig_weight(result["length_cm"], weight_formula)
        if weight_result[0] is not None:
            result["weight_kg"] = weight_result[0]
            result["weight_range"] = weight_result[1]
    
    return result

def format_measurement_text(measurements):
    """
    格式化测量结果为文本
    
    Args:
        measurements: calculate_pig_measurements返回的结果字典
    
    Returns:
        list: 格式化后的文本行列表
    """
    texts = []
    
    if measurements["length_cm"] is not None:
        texts.append(f"长度: {measurements['length_cm']:.1f}cm")
        
        if measurements["weight_kg"] is not None:
            texts.append(f"重量: {measurements['weight_kg']:.1f}kg")
            
            if measurements["weight_range"]:
                weight_min, weight_max = measurements["weight_range"]
                texts.append(f"范围: {weight_min:.1f}-{weight_max:.1f}kg")
        
        texts.append(f"方法: {measurements['calculation_method']}")
        texts.append(f"置信度: {measurements['confidence']}")
    else:
        texts.append("无法测量长度")
        texts.append("缺少参考对象")
    
    return texts