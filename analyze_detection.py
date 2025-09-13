#!/usr/bin/env python3
"""
文本形式的检测分析 - 不依赖图像库
"""
import sys
sys.path.append('.')

from utils.measurement_utils import yolo_to_pixel, calculate_pig_measurements

def smart_measurement_selection(pig_box, ruler_box, base_box):
    """
    智能选择测量方法
    
    Args:
        pig_box: 猪的边界框
        ruler_box: 尺子边界框  
        base_box: 底座边界框
    
    Returns:
        tuple: (选择的方法, 测量结果, 详细分析)
    """
    if not pig_box:
        return "无法测量", None, "缺少猪的检测框"
    
    analysis = []
    analysis.append("=== 智能测量选择分析 ===")
    
    ruler_measurements = None
    base_measurements = None
    
    # 分析尺子
    if ruler_box:
        ruler_width = abs(ruler_box[2] - ruler_box[0])
        ruler_height = abs(ruler_box[3] - ruler_box[1])
        ruler_aspect_ratio = max(ruler_width, ruler_height) / min(ruler_width, ruler_height)
        
        analysis.append(f"尺子分析:")
        analysis.append(f"  - 尺寸: {ruler_width:.1f} x {ruler_height:.1f} 像素")
        analysis.append(f"  - 长宽比: {ruler_aspect_ratio:.1f}")
        
        # 根据长宽比判断尺子类型和长度
        if ruler_aspect_ratio > 10:
            ruler_length_cm = 30
            ruler_type = "细长直尺"
            confidence = "高"
        elif ruler_aspect_ratio > 6:
            ruler_length_cm = 50
            ruler_type = "中等直尺"
            confidence = "中"
        elif ruler_aspect_ratio > 3:
            ruler_length_cm = 100
            ruler_type = "卷尺/短尺"
            confidence = "中"
        else:
            ruler_length_cm = 100
            ruler_type = "方形/不规则尺子"
            confidence = "低"
        
        analysis.append(f"  - 推断类型: {ruler_type} ({ruler_length_cm}cm)")
        analysis.append(f"  - 置信度: {confidence}")
        
        # 计算基于尺子的测量
        ruler_measurements = calculate_pig_measurements(
            pig_box=pig_box,
            ruler_box=ruler_box,
            ruler_length_cm=ruler_length_cm,
            weight_formula="standard"
        )
        
        if ruler_measurements["length_cm"]:
            analysis.append(f"  - 测量结果: 长度={ruler_measurements['length_cm']:.1f}cm, 体重={ruler_measurements['weight_kg']:.2f}kg")
            
            # 合理性检查
            if 20 <= ruler_measurements["length_cm"] <= 80:
                analysis.append(f"  - ✅ 长度在合理范围内 (20-80cm)")
                ruler_reasonable = True
            else:
                analysis.append(f"  - ⚠️ 长度可能不准确 (超出20-80cm范围)")
                ruler_reasonable = False
        else:
            analysis.append(f"  - ❌ 测量失败")
            ruler_reasonable = False
    else:
        analysis.append("尺子分析: 未检测到尺子")
        ruler_reasonable = False
    
    # 分析底座
    if base_box:
        base_width = abs(base_box[2] - base_box[0])
        base_height = abs(base_box[3] - base_box[1])
        base_aspect_ratio = max(base_width, base_height) / min(base_width, base_height)
        
        analysis.append(f"\n底座分析:")
        analysis.append(f"  - 尺寸: {base_width:.1f} x {base_height:.1f} 像素")
        analysis.append(f"  - 长宽比: {base_aspect_ratio:.1f}")
        
        # 底座合理性检查
        if 1.2 <= base_aspect_ratio <= 2.5:
            analysis.append(f"  - ✅ 长宽比合理 (矩形底座)")
            base_shape_ok = True
        else:
            analysis.append(f"  - ⚠️ 长宽比异常 (可能不是标准底座)")
            base_shape_ok = True  # 仍然尝试计算
        
        # 计算基于底座的测量
        base_measurements = calculate_pig_measurements(
            pig_box=pig_box,
            base_box=base_box,
            base_length_cm=60,
            base_width_cm=40,
            weight_formula="standard"
        )
        
        if base_measurements["length_cm"]:
            analysis.append(f"  - 测量结果: 长度={base_measurements['length_cm']:.1f}cm, 体重={base_measurements['weight_kg']:.2f}kg")
            
            # 合理性检查
            if 20 <= base_measurements["length_cm"] <= 80:
                analysis.append(f"  - ✅ 长度在合理范围内 (20-80cm)")
                base_reasonable = True
            else:
                analysis.append(f"  - ⚠️ 长度可能不准确 (超出20-80cm范围)")
                base_reasonable = False
        else:
            analysis.append(f"  - ❌ 测量失败")
            base_reasonable = False
    else:
        analysis.append("\n底座分析: 未检测到底座")
        base_reasonable = False
    
    # 智能选择决策
    analysis.append(f"\n=== 智能选择决策 ===")
    
    selected_method = None
    selected_measurements = None
    
    # 决策逻辑
    if ruler_measurements and ruler_reasonable:
        selected_method = f"尺子测量 ({ruler_type} {ruler_length_cm}cm)"
        selected_measurements = ruler_measurements
        analysis.append(f"✅ 选择尺子测量 - 长度合理且置信度较高")
    elif base_measurements and base_reasonable:
        selected_method = "底座测量 (60x40cm)"
        selected_measurements = base_measurements
        analysis.append(f"✅ 选择底座测量 - 长度合理")
    elif ruler_measurements and ruler_measurements["length_cm"]:
        selected_method = f"尺子测量 ({ruler_type} {ruler_length_cm}cm) ⚠️"
        selected_measurements = ruler_measurements
        analysis.append(f"⚠️ 使用尺子测量 - 长度可能不准确但是最佳选择")
    elif base_measurements and base_measurements["length_cm"]:
        selected_method = "底座测量 (60x40cm) ⚠️"
        selected_measurements = base_measurements
        analysis.append(f"⚠️ 使用底座测量 - 长度可能不准确但是唯一选择")
    else:
        selected_method = "无法测量"
        selected_measurements = None
        analysis.append(f"❌ 所有测量方法都失败")
    
    return selected_method, selected_measurements, "\n".join(analysis)

def analyze_detection(image_path, labels):
    """
    分析检测结果
    
    Args:
        image_path: 图片路径
        labels: YOLO格式标签列表
    """
    # 假设图片尺寸（或者可以通过其他方式获取）
    img_width, img_height = 640, 640
    
    print(f"=== 检测结果分析 ===")
    print(f"图片: {image_path}")
    print(f"假设图片尺寸: {img_width} x {img_height}")
    print()
    
    # 定义类别
    class_names = {0: "pig", 1: "ruler", 2: "base"}
    
    # 处理检测结果
    detections = []
    pig_box = None
    ruler_box = None
    base_box = None
    
    print("=== 检测对象详情 ===")
    for i, (class_id, x_center, y_center, width, height) in enumerate(labels):
        box, width_px, height_px = yolo_to_pixel(
            [x_center, y_center, width, height], img_width, img_height
        )
        
        detection = {
            'box': box,
            'class_id': class_id,
            'class_name': class_names[class_id],
            'width_px': width_px,
            'height_px': height_px
        }
        detections.append(detection)
        
        # 保存边界框
        if class_id == 0:  # pig
            pig_box = box
        elif class_id == 1:  # ruler
            ruler_box = box
        elif class_id == 2:  # base
            base_box = box
        
        # 打印检测信息
        x1, y1, x2, y2 = box
        print(f"{i+1}. {class_names[class_id].upper()}")
        print(f"   - YOLO坐标: ({x_center:.6f}, {y_center:.6f}, {width:.6f}, {height:.6f})")
        print(f"   - 像素边界框: [{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}]")
        print(f"   - 像素尺寸: {width_px:.1f} x {height_px:.1f}")
        print()
    
    # 智能测量选择
    method, measurements, analysis = smart_measurement_selection(pig_box, ruler_box, base_box)
    
    print(analysis)
    
    print(f"\n=== 最终测量结果 ===")
    print(f"选择方法: {method}")
    if measurements and measurements["length_cm"]:
        print(f"猪长度: {measurements['length_cm']:.1f}cm")
        print(f"估算体重: {measurements['weight_kg']:.2f}kg")
        if measurements['weight_range']:
            weight_min, weight_max = measurements['weight_range']
            print(f"体重范围: {weight_min:.2f} - {weight_max:.2f}kg")
        print(f"测量置信度: {measurements['confidence']}")
        
        # 体重合理性评估
        if 2.0 <= measurements['weight_kg'] <= 4.5:
            print(f"✅ 体重在预期范围内 (2.0-4.5kg)")
        else:
            print(f"⚠️ 体重可能超出预期范围 (2.0-4.5kg)")
    else:
        print("❌ 无法获得有效测量结果")
    
    return method, measurements

def test_analysis():
    """测试分析功能"""
    
    # 图片路径和标签
    image_path = "dataset/train/images/7b12b90a9c9ce3b4dd8013dc792023f8.jpg"
    labels = [
        (0, 0.610156, 0.519918, 0.314063, 0.641476),  # pig
        (1, 0.389453, 0.514060, 0.083594, 0.625073),  # ruler  
        (2, 0.603906, 0.483597, 0.760938, 0.564148),  # base
    ]
    
    # 分析检测结果
    method, measurements = analyze_detection(image_path, labels)
    
    print(f"\n" + "="*60)
    print(f"分析完成！")
    if measurements:
        print(f"推荐使用: {method}")
        print(f"最终体重估算: {measurements['weight_kg']:.2f}kg")

if __name__ == "__main__":
    test_analysis()