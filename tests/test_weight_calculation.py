#!/usr/bin/env python3
"""
体重计算测试脚本 - 验证优化后的体重计算公式
"""
import sys
sys.path.append('.')

from utils.measurement_utils import calculate_pig_measurements
from utils.measurement_utils import estimate_pig_weight

def test_weight_calculations():
    """测试不同长度下的体重计算结果"""
    
    # 模拟不同的猪长度和边界框 (更合理的尺寸比例)
    # 假设尺子在图像中占50像素，对应30cm实际长度，比例为 0.6 cm/pixel
    test_cases = [
        {"length_description": "小猪 (~30cm)", "pig_box": [100, 100, 150, 130], "ruler_box": [200, 120, 250, 130]},  # 猪50px≈30cm
        {"length_description": "中等猪 (~35cm)", "pig_box": [100, 100, 158, 135], "ruler_box": [200, 120, 250, 130]},  # 猪58px≈35cm  
        {"length_description": "大一点的猪 (~40cm)", "pig_box": [100, 100, 167, 140], "ruler_box": [200, 120, 250, 130]},  # 猪67px≈40cm
    ]
    
    print("=== 体重计算测试结果 ===\n")
    
    for i, case in enumerate(test_cases, 1):
        print(f"测试案例 {i}: {case['length_description']}")
        print("-" * 40)
        
        # 测试不同的体重计算公式
        for formula in ["standard", "young_pig", "medium_pig"]:
            measurements = calculate_pig_measurements(
                pig_box=case["pig_box"],
                ruler_box=case["ruler_box"],
                ruler_length_cm=30,  # 30cm尺子
                weight_formula=formula
            )
            
            if measurements["length_cm"] and measurements["weight_kg"]:
                length = measurements["length_cm"]
                weight = measurements["weight_kg"]
                weight_min, weight_max = measurements["weight_range"]
                
                print(f"{formula:12}: 长度={length:.1f}cm, 体重={weight:.2f}kg ({weight_min:.2f}-{weight_max:.2f}kg)")
        
        print()

def test_specific_lengths():
    """测试特定长度下的体重计算"""
    
    print("=== 特定长度体重计算 ===\n")
    
    # 模拟35cm长度的猪（应该产生2.5-3.78kg范围的体重）
    # 尺子50像素对应30cm，比例0.6cm/pixel，所以35cm的猪应该约58像素
    pig_box = [100, 100, 158, 135]  # 58像素宽度 ≈ 35cm
    ruler_box = [200, 120, 250, 130]  # 50像素宽度 = 30cm尺子
    
    measurements = calculate_pig_measurements(
        pig_box=pig_box,
        ruler_box=ruler_box,
        ruler_length_cm=30,
        weight_formula="standard"
    )
    
    if measurements["length_cm"] and measurements["weight_kg"]:
        length = measurements["length_cm"]
        weight = measurements["weight_kg"]
        weight_min, weight_max = measurements["weight_range"]
        
        print(f"检测长度: {length:.1f}cm")
        print(f"估算体重: {weight:.2f}kg")
        print(f"体重范围: {weight_min:.2f} - {weight_max:.2f}kg")
        print(f"计算方法: {measurements['calculation_method']}")
        print(f"置信度: {measurements['confidence']}")
        
        # 检查是否在期望范围内
        if 2.5 <= weight <= 3.78:
            print("✅ 体重在期望范围内 (2.5-3.78kg)")
        else:
            print("❌ 体重超出期望范围 (2.5-3.78kg)")
    else:
        print("❌ 无法计算体重")


def test_range_varies_with_length():
    """不同长度应产生不同的体重范围宽度"""
    small_weight, small_range = estimate_pig_weight(40)
    big_weight, big_range = estimate_pig_weight(100)

    small_margin = (small_range[1] - small_range[0]) / small_weight
    big_margin = (big_range[1] - big_range[0]) / big_weight

    assert small_margin < big_margin


if __name__ == "__main__":
    test_weight_calculations()
    test_specific_lengths()
    test_range_varies_with_length()