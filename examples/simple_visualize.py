#!/usr/bin/env python3
"""
简化的可视化脚本 - 使用matplotlib绘制边界框
"""
import sys
sys.path.append('.')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.image import imread
from utils.measurement_utils import yolo_to_pixel, calculate_pig_measurements

def smart_measurement_selection(pig_box, ruler_box, base_box):
    """
    智能选择测量方法
    
    Args:
        pig_box: 猪的边界框
        ruler_box: 尺子边界框  
        base_box: 底座边界框
    
    Returns:
        tuple: (选择的方法, 测量结果, 详细信息)
    """
    if not pig_box:
        return "无法测量", None, "缺少猪的检测框"
    
    ruler_measurements = None
    base_measurements = None
    selection_info = []
    
    # 尝试基于尺子的测量
    if ruler_box:
        # 计算尺子的长宽比，判断类型
        ruler_width = abs(ruler_box[2] - ruler_box[0])
        ruler_height = abs(ruler_box[3] - ruler_box[1])
        ruler_aspect_ratio = max(ruler_width, ruler_height) / min(ruler_width, ruler_height)
        
        # 根据长宽比判断尺子类型
        if ruler_aspect_ratio > 8:
            ruler_length_cm = 30  # 细长的直尺
            ruler_type = "直尺"
        elif ruler_aspect_ratio > 4:
            ruler_length_cm = 50  # 中等长度尺子
            ruler_type = "中尺"
        else:
            ruler_length_cm = 100  # 卷尺或短粗尺子
            ruler_type = "卷尺"
        
        ruler_measurements = calculate_pig_measurements(
            pig_box=pig_box,
            ruler_box=ruler_box,
            ruler_length_cm=ruler_length_cm,
            weight_formula="standard"
        )
        
        selection_info.append(f"尺子检测: {ruler_type}({ruler_length_cm}cm), 长宽比={ruler_aspect_ratio:.1f}")
        if ruler_measurements["length_cm"]:
            selection_info.append(f"尺子测量: 长度={ruler_measurements['length_cm']:.1f}cm, 体重={ruler_measurements['weight_kg']:.2f}kg")
    
    # 尝试基于底座的测量
    if base_box:
        base_measurements = calculate_pig_measurements(
            pig_box=pig_box,
            base_box=base_box,
            base_length_cm=60,
            base_width_cm=40,
            weight_formula="standard"
        )
        
        selection_info.append("底座检测: 60x40cm")
        if base_measurements["length_cm"]:
            selection_info.append(f"底座测量: 长度={base_measurements['length_cm']:.1f}cm, 体重={base_measurements['weight_kg']:.2f}kg")
    
    # 智能选择策略
    selected_method = None
    selected_measurements = None
    
    # 优先级1: 合理范围内的尺子测量
    if ruler_measurements and ruler_measurements["length_cm"]:
        if 20 <= ruler_measurements["length_cm"] <= 80:  # 合理的猪长度范围
            selected_method = f"尺子测量 ({ruler_type} {ruler_length_cm}cm)"
            selected_measurements = ruler_measurements
            selection_info.append("✅ 选择尺子测量 - 长度在合理范围内")
    
    # 优先级2: 合理范围内的底座测量
    if not selected_measurements and base_measurements and base_measurements["length_cm"]:
        if 20 <= base_measurements["length_cm"] <= 80:
            selected_method = "底座测量 (60x40cm)"
            selected_measurements = base_measurements
            selection_info.append("✅ 选择底座测量 - 长度在合理范围内")
    
    # 优先级3: 任何可用的测量（带警告）
    if not selected_measurements:
        if ruler_measurements and ruler_measurements["length_cm"]:
            selected_method = f"尺子测量 ({ruler_type} {ruler_length_cm}cm) ⚠️"
            selected_measurements = ruler_measurements
            selection_info.append("⚠️ 使用尺子测量 - 长度可能不准确")
        elif base_measurements and base_measurements["length_cm"]:
            selected_method = "底座测量 (60x40cm) ⚠️"
            selected_measurements = base_measurements
            selection_info.append("⚠️ 使用底座测量 - 长度可能不准确")
    
    if not selected_measurements:
        return "无法测量", None, "所有测量方法都失败"
    
    return selected_method, selected_measurements, "\n".join(selection_info)

def visualize_detection(image_path, labels, output_path="temp/detection_result.png"):
    """
    可视化检测结果
    
    Args:
        image_path: 输入图片路径
        labels: YOLO格式标签列表
        output_path: 输出图片路径
    """
    try:
        # 读取图片
        img = imread(image_path)
        img_height, img_width = img.shape[:2]
        
        # 创建图形
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        ax.imshow(img)
        
        # 定义类别和颜色
        class_names = {0: "pig", 1: "ruler", 2: "base"}
        colors = {0: "green", 1: "red", 2: "blue"}
        
        # 处理检测结果
        pig_box = None
        ruler_box = None
        base_box = None
        
        for class_id, x_center, y_center, width, height in labels:
            box, width_px, height_px = yolo_to_pixel(
                [x_center, y_center, width, height], img_width, img_height
            )
            
            # 保存边界框
            if class_id == 0:  # pig
                pig_box = box
            elif class_id == 1:  # ruler
                ruler_box = box
            elif class_id == 2:  # base
                base_box = box
            
            # 绘制边界框
            x1, y1, x2, y2 = box
            rect_width = x2 - x1
            rect_height = y2 - y1
            
            rect = patches.Rectangle((x1, y1), rect_width, rect_height,
                                   linewidth=2, edgecolor=colors[class_id], 
                                   facecolor='none')
            ax.add_patch(rect)
            
            # 添加标签
            label = f"{class_names[class_id]}\n{width_px:.0f}x{height_px:.0f}px"
            ax.text(x1, y1-10, label, fontsize=10, color=colors[class_id],
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # 智能测量选择
        method, measurements, info = smart_measurement_selection(pig_box, ruler_box, base_box)
        
        # 显示测量结果
        result_text = f"测量方法: {method}\n"
        if measurements and measurements["length_cm"]:
            result_text += f"猪长度: {measurements['length_cm']:.1f}cm\n"
            result_text += f"估算体重: {measurements['weight_kg']:.2f}kg\n"
            if measurements['weight_range']:
                weight_min, weight_max = measurements['weight_range']
                result_text += f"体重范围: {weight_min:.2f}-{weight_max:.2f}kg\n"
            result_text += f"置信度: {measurements['confidence']}"
        
        # 在图片上显示结果
        ax.text(10, img_height-10, result_text, fontsize=12, color='white',
               verticalalignment='bottom',
               bbox=dict(boxstyle="round,pad=0.5", facecolor='black', alpha=0.7))
        
        ax.set_xlim(0, img_width)
        ax.set_ylim(img_height, 0)  # 翻转y轴
        ax.set_title(f"猪检测和测量结果\n图片尺寸: {img_width}x{img_height}")
        
        # 保存结果
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.show()
        
        # 打印详细信息
        print(f"\n=== 检测结果 ===")
        print(f"图片尺寸: {img_width} x {img_height}")
        print(f"\n=== 智能测量选择过程 ===")
        print(info)
        print(f"\n=== 最终测量结果 ===")
        print(f"选择方法: {method}")
        if measurements:
            print(f"猪长度: {measurements['length_cm']:.1f}cm")
            print(f"估算体重: {measurements['weight_kg']:.2f}kg")
            if measurements['weight_range']:
                weight_min, weight_max = measurements['weight_range']
                print(f"体重范围: {weight_min:.2f} - {weight_max:.2f}kg")
            print(f"置信度: {measurements['confidence']}")
        
        return True, measurements, method
        
    except Exception as e:
        print(f"可视化失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

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
    success, measurements, method = visualize_detection(image_path, labels)
    
    if success:
        print(f"\n✅ 可视化成功完成")
        print(f"结果已保存到: temp/detection_result.png")
    else:
        print("❌ 可视化失败")

if __name__ == "__main__":
    test_visualization()