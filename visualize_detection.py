#!/usr/bin/env python3
"""
可视化检测结果并绘制边界框
"""
import sys
sys.path.append('.')

import cv2
import numpy as np
from utils.measurement_utils import yolo_to_pixel, calculate_pig_measurements

def draw_detection_boxes(image_path, labels, output_path="temp/detection_result.jpg"):
    """
    绘制检测边界框和测量结果
    
    Args:
        image_path: 输入图片路径
        labels: YOLO格式标签列表
        output_path: 输出图片路径
    """
    try:
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            print(f"无法读取图片: {image_path}")
            return False
            
        img_height, img_width = img.shape[:2]
        print(f"实际图片尺寸: {img_width} x {img_height}")
        
        # 定义类别和颜色
        class_names = {0: "pig", 1: "ruler", 2: "base"}
        colors = {0: (0, 255, 0), 1: (255, 0, 0), 2: (0, 0, 255)}  # BGR格式
        
        # 处理检测结果
        detections = []
        pig_box = None
        ruler_box = None
        base_box = None
        
        for class_id, x_center, y_center, width, height in labels:
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
            
            # 绘制边界框
            x1, y1, x2, y2 = [int(coord) for coord in box]
            color = colors[class_id]
            
            # 绘制矩形框
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            label = f"{class_names[class_id]} ({width_px:.0f}x{height_px:.0f}px)"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # 标签背景
            cv2.rectangle(img, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # 标签文字
            cv2.putText(img, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 智能选择测量方法
        measurement_method, measurements = smart_measurement_selection(
            pig_box, ruler_box, base_box
        )
        
        # 在图片上显示测量结果
        if measurements and measurements["length_cm"] is not None:
            result_text = [
                f"Method: {measurement_method}",
                f"Length: {measurements['length_cm']:.1f}cm",
                f"Weight: {measurements['weight_kg']:.2f}kg",
                f"Range: {measurements['weight_range'][0]:.2f}-{measurements['weight_range'][1]:.2f}kg" if measurements['weight_range'] else "",
                f"Confidence: {measurements['confidence']}"
            ]
            
            # 在图片底部显示结果
            y_offset = img_height - 120
            for i, text in enumerate(result_text):
                if text:  # 跳过空字符串
                    cv2.putText(img, text, (10, y_offset + i * 25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(img, text, (10, y_offset + i * 25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        
        # 保存结果
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, img)
        print(f"可视化结果已保存到: {output_path}")
        
        return True, measurements, measurement_method
        
    except Exception as e:
        print(f"可视化失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def smart_measurement_selection(pig_box, ruler_box, base_box):
    """
    智能选择测量方法
    
    Args:
        pig_box: 猪的边界框
        ruler_box: 尺子边界框
        base_box: 底座边界框
    
    Returns:
        tuple: (选择的方法, 测量结果)
    """
    if not pig_box:
        return "无法测量", None
    
    ruler_measurements = None
    base_measurements = None
    
    # 尝试基于尺子的测量
    if ruler_box:
        # 计算尺子的长宽比，判断是否为直尺
        ruler_width = abs(ruler_box[2] - ruler_box[0])
        ruler_height = abs(ruler_box[3] - ruler_box[1])
        ruler_aspect_ratio = max(ruler_width, ruler_height) / min(ruler_width, ruler_height)
        
        # 如果长宽比大于5，认为是直尺，使用较小的长度作为参考
        if ruler_aspect_ratio > 5:
            ruler_length_cm = 30  # 假设是30cm直尺
        else:
            ruler_length_cm = 100  # 假设是100cm卷尺
        
        ruler_measurements = calculate_pig_measurements(
            pig_box=pig_box,
            ruler_box=ruler_box,
            ruler_length_cm=ruler_length_cm,
            weight_formula="standard"
        )
    
    # 尝试基于底座的测量
    if base_box:
        base_measurements = calculate_pig_measurements(
            pig_box=pig_box,
            base_box=base_box,
            base_length_cm=60,
            base_width_cm=40,
            weight_formula="standard"
        )
    
    # 智能选择策略
    if ruler_measurements and ruler_measurements["length_cm"]:
        # 优先使用尺子，因为精度更高
        if ruler_measurements["length_cm"] < 80:  # 合理的猪长度范围
            return f"Ruler ({ruler_length_cm}cm)", ruler_measurements
    
    if base_measurements and base_measurements["length_cm"]:
        # 使用底座作为备选
        if base_measurements["length_cm"] < 80:  # 合理的猪长度范围
            return "Base (60x40cm)", base_measurements
    
    # 如果都不合理，返回最可能的结果
    if ruler_measurements and ruler_measurements["length_cm"]:
        return f"Ruler ({ruler_length_cm}cm) - Warning", ruler_measurements
    elif base_measurements and base_measurements["length_cm"]:
        return "Base (60x40cm) - Warning", base_measurements
    
    return "无法测量", None

def test_visualization():
    """测试可视化功能"""
    
    # 图片路径和标签
    image_path = "dataset/train/images/7b12b90a9c9ce3b4dd8013dc792023f8.jpg"
    labels = [
        (0, 0.610156, 0.519918, 0.314063, 0.641476),  # pig
        (1, 0.389453, 0.514060, 0.083594, 0.625073),  # ruler  
        (2, 0.603906, 0.483597, 0.760938, 0.564148),  # base
    ]
    
    # 绘制检测结果
    success, measurements, method = draw_detection_boxes(image_path, labels)
    
    if success:
        print(f"\n=== 智能测量结果 ===")
        print(f"选择的方法: {method}")
        if measurements:
            print(f"猪长度: {measurements['length_cm']:.1f}cm")
            print(f"估算体重: {measurements['weight_kg']:.2f}kg")
            if measurements['weight_range']:
                weight_min, weight_max = measurements['weight_range']
                print(f"体重范围: {weight_min:.2f} - {weight_max:.2f}kg")
            print(f"置信度: {measurements['confidence']}")
        
        # 尝试打开结果图片
        import os
        output_path = "temp/detection_result.jpg"
        if os.path.exists(output_path):
            os.system(f"open {output_path}")
    else:
        print("可视化失败")

if __name__ == "__main__":
    test_visualization()