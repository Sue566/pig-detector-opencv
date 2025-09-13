#!/usr/bin/env python3
"""
可视化工具模块 - 用于绘制检测结果和测量信息
"""
from PIL import Image, ImageDraw, ImageFont
import os

def load_fonts(font_size=18, small_font_size=14):
    """
    加载字体
    
    Args:
        font_size: 主字体大小
        small_font_size: 小字体大小
    
    Returns:
        tuple: (主字体, 小字体)
    """
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", small_font_size)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    return font, small_font

def draw_detection_box(draw, box, label_texts, color="red", font=None, small_font=None):
    """
    绘制单个检测框和标签
    
    Args:
        draw: PIL ImageDraw对象
        box: 边界框坐标 [x1, y1, x2, y2]
        label_texts: 标签文本列表
        color: 边界框颜色
        font: 主字体
        small_font: 小字体
    """
    x1, y1, x2, y2 = box
    
    # 绘制边界框
    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
    
    if not label_texts:
        return
    
    # 使用小字体作为默认字体
    text_font = small_font if small_font else font
    if not text_font:
        text_font = ImageFont.load_default()
    
    # 计算文本背景尺寸
    line_height = 20
    bg_height = len(label_texts) * line_height + 10
    
    # 计算背景宽度
    max_width = 0
    for text in label_texts:
        try:
            text_bbox = draw.textbbox((0, 0), text, font=text_font)
            text_width = text_bbox[2] - text_bbox[0]
            max_width = max(max_width, text_width)
        except:
            # 如果textbbox不可用，使用textsize（旧版本PIL）
            try:
                text_width, _ = draw.textsize(text, font=text_font)
                max_width = max(max_width, text_width)
            except:
                max_width = max(max_width, len(text) * 8)  # 估算宽度
    
    bg_width = max_width + 10
    
    # 绘制背景
    draw.rectangle([x1, y1-bg_height, x1+bg_width, y1], fill=color)
    
    # 绘制文本
    for i, text in enumerate(label_texts):
        y_offset = y1 - bg_height + 5 + i * line_height
        draw.text((x1 + 5, y_offset), text, fill='white', font=text_font)

def draw_simple_detection_box(draw, box, label, color="red", font=None):
    """
    绘制简单的检测框（单行标签）
    
    Args:
        draw: PIL ImageDraw对象
        box: 边界框坐标 [x1, y1, x2, y2]
        label: 标签文本
        color: 边界框颜色
        font: 字体
    """
    x1, y1, x2, y2 = box
    
    # 绘制边界框
    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
    
    if not label:
        return
    
    if not font:
        font = ImageFont.load_default()
    
    # 计算文本尺寸
    try:
        text_bbox = draw.textbbox((0, 0), label, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except:
        try:
            text_width, text_height = draw.textsize(label, font=font)
        except:
            text_width, text_height = len(label) * 8, 16
    
    bg_width = text_width + 10
    bg_height = text_height + 10
    
    # 绘制背景和文本
    draw.rectangle([x1, y1-bg_height, x1+bg_width, y1], fill=color)
    draw.text((x1 + 5, y1 - bg_height + 5), label, fill='white', font=font)

def create_detection_visualization(image_path, detections, measurements=None, 
                                 class_names=None, colors=None, output_path=None):
    """
    创建检测结果可视化图片
    
    Args:
        image_path: 原始图片路径
        detections: 检测结果列表，每个元素包含 {'box': [x1,y1,x2,y2], 'class_id': int, 'score': float}
        measurements: 测量结果字典（可选）
        class_names: 类别名称字典 {class_id: name}
        colors: 类别颜色字典 {class_id: color}
        output_path: 输出图片路径
    
    Returns:
        bool: 是否成功
    """
    try:
        # 读取图片
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        font, small_font = load_fonts()
        
        # 默认设置
        if class_names is None:
            class_names = {0: "Pig", 1: "Ruler", 2: "Base"}
        if colors is None:
            colors = {0: "red", 1: "blue", 2: "green"}
        
        # 绘制检测框
        for detection in detections:
            box = detection['box']
            class_id = detection.get('class_id', 0)
            score = detection.get('score', 0.0)
            
            class_name = class_names.get(class_id, f"Class_{class_id}")
            color = colors.get(class_id, "black")
            
            # 准备标签文本
            if class_id == 0 and measurements:  # 猪的检测框
                from .measurement_utils import format_measurement_text
                label_texts = [f"{class_name}: {score:.2f}"] + format_measurement_text(measurements)
                draw_detection_box(draw, box, label_texts, color, font, small_font)
            else:
                # 其他对象的简单标签
                label = f"{class_name}: {score:.2f}"
                draw_simple_detection_box(draw, box, label, color, font)
        
        # 保存图片
        if output_path is None:
            output_path = "detection_result.jpg"
        
        img.save(output_path)
        return True
        
    except Exception as e:
        print(f"可视化失败: {e}")
        return False

def print_detection_summary(detections, measurements=None, class_names=None):
    """
    打印检测和测量结果摘要
    
    Args:
        detections: 检测结果列表
        measurements: 测量结果字典（可选）
        class_names: 类别名称字典
    """
    if class_names is None:
        class_names = {0: "Pig", 1: "Ruler", 2: "Base"}
    
    print("\n=== 检测和测量结果 ===")
    
    # 打印检测结果
    for detection in detections:
        class_id = detection.get('class_id', 0)
        score = detection.get('score', 0.0)
        class_name = class_names.get(class_id, f"Class_{class_id}")
        print(f"- {class_name}: 置信度 {score:.2f}")
    
    # 打印测量结果
    if measurements and measurements.get("length_cm") is not None:
        print(f"\n猪的测量结果:")
        print(f"- 长度: {measurements['length_cm']:.1f} cm")
        print(f"- 计算方法: {measurements['calculation_method']}")
        print(f"- 置信度: {measurements['confidence']}")
        
        if measurements.get("weight_kg") is not None:
            print(f"- 估算重量: {measurements['weight_kg']:.1f} kg")
            if measurements.get("weight_range"):
                weight_min, weight_max = measurements["weight_range"]
                print(f"- 重量范围: {weight_min:.1f} - {weight_max:.1f} kg")
    else:
        print("\n无法计算猪的长度：缺少参考对象（尺子或底座）")