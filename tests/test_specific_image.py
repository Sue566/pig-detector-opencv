#!/usr/bin/env python3
"""
测试特定图片的识别和测量
"""
import sys
sys.path.append('.')

from utils.measurement_utils import yolo_to_pixel, calculate_pig_measurements

def test_specific_image():
    """测试7b12b90a9c9ce3b4dd8013dc792023f8.jpg图片"""
    
    # 图片路径
    image_path = "dataset/train/images/7b12b90a9c9ce3b4dd8013dc792023f8.jpg"
    
    # 从标签文件读取的数据 (class_id, x_center, y_center, width, height)
    labels = [
        (0, 0.610156, 0.519918, 0.314063, 0.641476),  # pig
        (1, 0.389453, 0.514060, 0.083594, 0.625073),  # ruler  
        (2, 0.603906, 0.483597, 0.760938, 0.564148),  # base
    ]
    
    try:
        # 假设图片尺寸（常见的训练图片尺寸）
        img_width, img_height = 640, 640  # 或者可以用其他方法获取
        print(f"图片: {image_path}")
        print(f"假设图片尺寸: {img_width} x {img_height}")
        print()
        
        # 处理检测结果
        detections = []
        pig_box = None
        ruler_box = None
        base_box = None
        
        class_names = {0: "pig", 1: "ruler", 2: "base"}
        
        for class_id, x_center, y_center, width, height in labels:
            box, width_px, height_px = yolo_to_pixel(
                [x_center, y_center, width, height], img_width, img_height
            )
            
            detection = {
                'box': box,
                'class_id': class_id,
                'class_name': class_names[class_id],
                'score': 1.0,  # 标签数据，置信度为1
                'width_px': width_px,
                'height_px': height_px
            }
            
            detections.append(detection)
            
            # 保存特定对象的边界框用于测量
            if class_id == 0:  # pig
                pig_box = box
            elif class_id == 1:  # ruler
                ruler_box = box
            elif class_id == 2:  # base
                base_box = box
            
            print(f"{class_names[class_id]:6}: 边界框 [{box[0]:.1f}, {box[1]:.1f}, {box[2]:.1f}, {box[3]:.1f}], 尺寸 {width_px:.1f}x{height_px:.1f}px")
        
        print("\n=== 测量结果 ===")
        
        # 使用尺子计算测量结果
        measurements_ruler = calculate_pig_measurements(
            pig_box=pig_box,
            ruler_box=ruler_box,
            base_box=None,  # 优先使用尺子
            ruler_length_cm=100,  # 这是100cm的卷尺
            weight_formula="standard"
        )
        
        if measurements_ruler["length_cm"] is not None:
            print(f"基于尺子测量:")
            print(f"  猪长度: {measurements_ruler['length_cm']:.1f}cm")
            print(f"  估算体重: {measurements_ruler['weight_kg']:.2f}kg")
            if measurements_ruler["weight_range"]:
                weight_min, weight_max = measurements_ruler["weight_range"]
                print(f"  体重范围: {weight_min:.2f} - {weight_max:.2f}kg")
            print(f"  置信度: {measurements_ruler['confidence']}")
        
        # 使用底座计算测量结果
        measurements_base = calculate_pig_measurements(
            pig_box=pig_box,
            ruler_box=None,
            base_box=base_box,
            base_length_cm=60,  # 假设底座60cm
            base_width_cm=40,   # 假设底座40cm
            weight_formula="standard"
        )
        
        if measurements_base["length_cm"] is not None:
            print(f"\n基于底座测量:")
            print(f"  猪长度: {measurements_base['length_cm']:.1f}cm")
            print(f"  估算体重: {measurements_base['weight_kg']:.2f}kg")
            if measurements_base["weight_range"]:
                weight_min, weight_max = measurements_base["weight_range"]
                print(f"  体重范围: {weight_min:.2f} - {weight_max:.2f}kg")
            print(f"  置信度: {measurements_base['confidence']}")
        
        # 不同公式对比
        print(f"\n=== 不同体重公式对比 (基于尺子) ===")
        for formula_name in ["standard", "young_pig", "medium_pig"]:
            test_measurements = calculate_pig_measurements(
                pig_box=pig_box,
                ruler_box=ruler_box,
                ruler_length_cm=100,
                weight_formula=formula_name
            )
            if test_measurements["weight_kg"] is not None:
                print(f"{formula_name:12}: {test_measurements['weight_kg']:.2f}kg")
        
    except Exception as e:
        print(f"处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_image()