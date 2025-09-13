#!/usr/bin/env python3
"""
使用测量工具的演示脚本
"""
import os
import sys
sys.path.append('.')

from utils.measurement_utils import yolo_to_pixel, calculate_pig_measurements

def process_image_with_measurements(image_path, labels, output_path=None):
    """
    处理图片并进行测量
    
    Args:
        image_path: 图片路径
        labels: YOLO格式标签列表 [(class_id, x_center, y_center, width, height), ...]
        output_path: 输出路径
    
    Returns:
        dict: 处理结果
    """
    try:
        from PIL import Image
        
        # 读取图片尺寸
        img = Image.open(image_path)
        img_width, img_height = img.size
        print(f"图片尺寸: {img_width} x {img_height}")
        
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
                'score': 0.95,  # 假设的置信度
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
        
        # 计算测量结果 - 使用优化的体重公式
        measurements = calculate_pig_measurements(
            pig_box=pig_box,
            ruler_box=ruler_box,
            base_box=base_box,
            ruler_length_cm=30,
            base_length_cm=60,
            base_width_cm=40,
            weight_formula="standard"  # 可选: "standard", "young_pig", "medium_pig"
        )
        
        # 添加调试信息 - 显示计算过程
        if measurements["length_cm"] is not None:
            print(f"\n=== 测量计算详情 ===")
            print(f"检测到的猪长度: {measurements['length_cm']:.1f}cm")
            print(f"计算方法: {measurements['calculation_method']}")
            print(f"置信度: {measurements['confidence']}")
            
            if measurements["weight_kg"] is not None:
                print(f"估算体重: {measurements['weight_kg']:.2f}kg")
                if measurements["weight_range"]:
                    weight_min, weight_max = measurements["weight_range"]
                    print(f"体重范围: {weight_min:.2f} - {weight_max:.2f}kg")
            
            # 尝试不同的体重计算公式进行对比
            print(f"\n=== 不同公式对比 ===")
            for formula_name in ["standard", "young_pig", "medium_pig"]:
                test_measurements = calculate_pig_measurements(
                    pig_box=pig_box,
                    ruler_box=ruler_box,
                    base_box=base_box,
                    ruler_length_cm=30,
                    base_length_cm=60,
                    base_width_cm=40,
                    weight_formula=formula_name
                )
                if test_measurements["weight_kg"] is not None:
                    print(f"{formula_name:12}: {test_measurements['weight_kg']:.2f}kg")
        
        # 创建可视化
        success = create_detection_visualization(
            image_path=image_path,
            detections=detections,
            measurements=measurements,
            output_path=output_path
        )
        
        # 打印结果
        print_detection_summary(detections, measurements)
        
        return {
            'success': success,
            'detections': detections,
            'measurements': measurements,
            'output_path': output_path
        }
        
    except Exception as e:
        print(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def simple_measurement_test():
    """简化的测量测试，不依赖图片文件"""
    print("=== 简化测量演示 ===\n")
    
    # 模拟图片尺寸
    img_width, img_height = 640, 480
    
    # 标签数据 (class_id, x_center, y_center, width, height) - 调整为合理尺寸
    # 让尺子和猪的比例更合理：猪约35cm，尺子30cm
    labels = [
        (0, 0.4, 0.5, 0.12, 0.2),   # pig - 35cm左右的猪
        (1, 0.7, 0.6, 0.1, 0.05)    # ruler - 30cm尺子，更细长
    ]
    
    print(f"模拟图片尺寸: {img_width} x {img_height}")
    
    # 处理检测结果
    detections = []
    pig_box = None
    ruler_box = None
    
    for class_id, x_center, y_center, width, height in labels:
        from utils.measurement_utils import yolo_to_pixel
        box, width_px, height_px = yolo_to_pixel(
            [x_center, y_center, width, height], img_width, img_height
        )
        
        detection = {
            'box': box,
            'class_id': class_id,
            'score': 0.95,
            'width_px': width_px,
            'height_px': height_px
        }
        
        detections.append(detection)
        
        if class_id == 0:  # pig
            pig_box = box
        elif class_id == 1:  # ruler
            ruler_box = box
    
    # 计算测量结果
    from utils.measurement_utils import calculate_pig_measurements
    measurements = calculate_pig_measurements(
        pig_box=pig_box,
        ruler_box=ruler_box,
        ruler_length_cm=30,
        weight_formula="standard"
    )
    
    # 显示结果
    if measurements["length_cm"] is not None:
        print(f"检测到的猪长度: {measurements['length_cm']:.1f}cm")
        print(f"计算方法: {measurements['calculation_method']}")
        print(f"置信度: {measurements['confidence']}")
        
        if measurements["weight_kg"] is not None:
            print(f"估算体重: {measurements['weight_kg']:.2f}kg")
            if measurements["weight_range"]:
                weight_min, weight_max = measurements["weight_range"]
                print(f"体重范围: {weight_min:.2f} - {weight_max:.2f}kg")
        
        # 不同公式对比
        print(f"\n=== 不同公式对比 ===")
        for formula_name in ["standard", "young_pig", "medium_pig"]:
            test_measurements = calculate_pig_measurements(
                pig_box=pig_box,
                ruler_box=ruler_box,
                ruler_length_cm=30,
                weight_formula=formula_name
            )
            if test_measurements["weight_kg"] is not None:
                print(f"{formula_name:12}: {test_measurements['weight_kg']:.2f}kg")
    else:
        print("无法计算长度和体重")

if __name__ == "__main__":
    # 运行简化测试
    simple_measurement_test()
    
    print("\n" + "="*50)
    print("注意：这是一个简化的演示版本")
    print("实际使用时需要安装PIL库来处理图片可视化")
    print("体重计算已优化，适合2.5-3.78kg范围的小猪")