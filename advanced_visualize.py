#!/usr/bin/env python3
"""
高级检测结果可视化脚本 - 包含精确长度和重量计算
"""
from PIL import Image, ImageDraw, ImageFont
import sys
import os
import math
import requests
from io import BytesIO

def yolo_to_pixel(yolo_coords, img_width, img_height):
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

def calculate_pig_length_from_ruler(pig_box, ruler_box, ruler_length_cm=30):
    """
    根据尺子计算猪的长度
    假设尺子长度为30cm（可调整）
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
    底座尺寸：60cm x 40cm
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

def estimate_pig_weight(length_cm):
    """
    根据猪的长度估算重量
    使用经验公式：重量 ≈ 长度的立方关系
    这里使用一个简化的经验公式
    """
    if length_cm is None:
        return None, None
    
    # 经验公式：重量(kg) = k * 长度(cm)^2.5
    # 这里k是经验系数，可以根据实际情况调整
    k = 0.002  # 经验系数
    
    estimated_weight = k * (length_cm ** 2.5)
    
    # 给出重量范围（±20%）
    weight_min = estimated_weight * 0.8
    weight_max = estimated_weight * 1.2
    
    return estimated_weight, (weight_min, weight_max)

def _read_image_any(image_path):
    """支持本地与URL读取，返回PIL.Image"""
    if isinstance(image_path, str) and (image_path.startswith("http://") or image_path.startswith("https://")):
        r = requests.get(image_path, timeout=15)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    else:
        return Image.open(image_path).convert("RGB")

def draw_detection_boxes(image_path, output_path=None):
    """在图片上绘制检测框并计算长度重量"""
    
    try:
        # 读取图片（本地或URL）
        img = _read_image_any(image_path)
        img_width, img_height = img.size
        print(f"图片尺寸: {img_width} x {img_height}")
        
        # 标签数据 (class, x_center, y_center, width, height)
        # 根据你的描述，应该有三个类别：0=pig, 1=ruler, 2=base
        # 但当前标签文件只有两个对象，我们先处理现有的
        labels = [
            (0, 0.574219, 0.504101, 0.232813, 0.518453),  # pig
            (1, 0.398047, 0.518746, 0.086719, 0.562976)   # ruler (假设是尺子)
        ]
        
        # 类别定义（可能需要根据实际情况调整）
        class_names = {0: "Pig", 1: "Ruler", 2: "Base"}
        colors = {0: "red", 1: "blue", 2: "green"}
        
        detections = []
        pig_box = None
        ruler_box = None
        base_box = None
        
        # 处理检测结果
        for class_id, x_center, y_center, width, height in labels:
            box, width_px, height_px = yolo_to_pixel([x_center, y_center, width, height], img_width, img_height)
            
            detection = {
                'box': box,
                'class_id': class_id,
                'class_name': class_names.get(class_id, f"Class_{class_id}"),
                'color': colors.get(class_id, "black"),
                'score': 0.95,
                'width_px': width_px,
                'height_px': height_px
            }
            
            detections.append(detection)
            
            # 保存特定对象的边界框用于长度计算
            if class_id == 0:  # pig
                pig_box = box
            elif class_id == 1:  # ruler
                ruler_box = box
            elif class_id == 2:  # base
                base_box = box
        
        # 计算猪的长度
        pig_length_cm = None
        calculation_method = "未知"
        
        if pig_box is not None:
            if ruler_box is not None:
                # 优先使用尺子计算
                pig_length_cm = calculate_pig_length_from_ruler(pig_box, ruler_box, ruler_length_cm=30)
                calculation_method = "基于尺子(30cm)"
            elif base_box is not None:
                # 使用底座计算
                pig_length_cm = calculate_pig_length_from_base(pig_box, base_box)
                calculation_method = "基于底座(60x40cm)"
        
        # 计算重量
        pig_weight, weight_range = estimate_pig_weight(pig_length_cm)
        
        # 创建绘图对象
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
            small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # 绘制检测框
        for detection in detections:
            x1, y1, x2, y2 = detection['box']
            class_name = detection['class_name']
            color = detection['color']
            score = detection['score']
            
            # 绘制边界框
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            
            # 准备标签文本
            if detection['class_id'] == 0 and pig_length_cm is not None:
                # 猪的标签包含长度和重量信息
                label = f"{class_name}: {score:.2f}"
                length_text = f"长度: {pig_length_cm:.1f}cm"
                if weight_range:
                    weight_text = f"重量: {pig_weight:.1f}kg ({weight_range[0]:.1f}-{weight_range[1]:.1f}kg)"
                else:
                    weight_text = f"重量: {pig_weight:.1f}kg"
                method_text = f"计算方法: {calculation_method}"
                
                # 绘制多行文本
                texts = [label, length_text, weight_text, method_text]
                line_height = 20
                bg_height = len(texts) * line_height + 10
                
                # 计算背景宽度
                max_width = 0
                for text in texts:
                    text_bbox = draw.textbbox((0, 0), text, font=small_font)
                    text_width = text_bbox[2] - text_bbox[0]
                    max_width = max(max_width, text_width)
                
                bg_width = max_width + 10
                
                # 绘制背景
                draw.rectangle([x1, y1-bg_height, x1+bg_width, y1], fill=color)
                
                # 绘制文本
                for i, text in enumerate(texts):
                    y_offset = y1 - bg_height + 5 + i * line_height
                    draw.text((x1 + 5, y_offset), text, fill='white', font=small_font)
            else:
                # 其他对象的简单标签
                label = f"{class_name}: {score:.2f}"
                
                text_bbox = draw.textbbox((0, 0), label, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                bg_width = text_width + 10
                bg_height = text_height + 10
                
                draw.rectangle([x1, y1-bg_height, x1+bg_width, y1], fill=color)
                draw.text((x1 + 5, y1 - bg_height + 5), label, fill='white', font=font)
        
        # 保存图片
        if output_path is None:
            output_path = "advanced_detection_result.jpg"
        
        img.save(output_path)
        print(f"已保存标注图片到: {output_path}")
        
        # 输出计算结果
        print("\n=== 检测和测量结果 ===")
        for detection in detections:
            print(f"- {detection['class_name']}: 置信度 {detection['score']:.2f}")
        
        if pig_length_cm is not None:
            print(f"\n猪的测量结果:")
            print(f"- 长度: {pig_length_cm:.1f} cm")
            print(f"- 计算方法: {calculation_method}")
            if pig_weight is not None:
                print(f"- 估算重量: {pig_weight:.1f} kg")
                if weight_range:
                    print(f"- 重量范围: {weight_range[0]:.1f} - {weight_range[1]:.1f} kg")
        else:
            print("无法计算猪的长度：缺少参考对象（尺子或底座）")
        
        return True
        
    except Exception as e:
        print(f"处理图片时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    image_path = "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/57aca64f50a1c614a366132ec4fb188e.jpg"
    
    # 确保temp目录存在
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    output_path = os.path.join(temp_dir, "advanced_pig_detection_result.jpg")
    
    if draw_detection_boxes(image_path, output_path):
        print(f"\n可视化完成！请查看: {output_path}")
        # 尝试打开图片
        os.system(f"open {output_path}")
    else:
        print("可视化失败")