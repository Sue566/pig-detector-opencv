#!/usr/bin/env python3
"""
测试高级猪检测API
"""
import requests
import json
import base64
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """测试健康检查接口"""
    print("=== 测试健康检查接口 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_advanced_detection():
    """测试高级检测接口"""
    print("\n=== 测试高级检测接口 ===")
    
    # 测试数据
    test_data = {
        "image_url": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/6ffd2a19045077324e3eda50cd6612aa.jpg",
        "labels_data": [
            [0, 0.574219, 0.504101, 0.232813, 0.518453],  # pig
            [1, 0.398047, 0.518746, 0.086719, 0.562976]   # ruler
        ],
        "return_visualization": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/detect_advanced",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("检测成功!")
            print(f"检测到 {len(result['detections'])} 个对象")
            
            # 打印测量结果
            measurements = result['measurements']
            print(f"测量结果:")
            print(f"- 长度: {measurements['length_cm']:.1f} cm" if measurements['length_cm'] else "- 长度: 无法计算")
            print(f"- 重量: {measurements['weight_kg']:.1f} kg" if measurements['weight_kg'] else "- 重量: 无法计算")
            if measurements['weight_range_kg']:
                print(f"- 重量范围: {measurements['weight_range_kg'][0]:.1f} - {measurements['weight_range_kg'][1]:.1f} kg")
            print(f"- 计算方法: {measurements['calculation_method']}")
            
            # 检查是否有可视化图片
            if 'visualization' in result:
                print("包含可视化图片 (base64编码)")
                # 可以选择保存图片
                img_data = base64.b64decode(result['visualization']['image_base64'])
                with open(f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg", 'wb') as f:
                    f.write(img_data)
                print("可视化图片已保存")
            
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_measurements_only():
    """测试仅计算测量结果接口"""
    print("\n=== 测试仅测量接口 ===")
    
    test_data = {
        "image_url": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/6ffd2a19045077324e3eda50cd6612aa.jpg",
        "labels_data": [
            [0, 0.574219, 0.504101, 0.232813, 0.518453],  # pig
            [1, 0.398047, 0.518746, 0.086719, 0.562976]   # ruler
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/calculate_measurements",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("测量计算成功!")
            
            measurements = result['measurements']
            print(f"测量结果:")
            print(f"- 长度: {measurements['length_cm']:.1f} cm" if measurements['length_cm'] else "- 长度: 无法计算")
            print(f"- 重量: {measurements['weight_kg']:.1f} kg" if measurements['weight_kg'] else "- 重量: 无法计算")
            print(f"- 计算方法: {measurements['calculation_method']}")
            
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_visualize_only():
    """测试仅可视化接口"""
    print("\n=== 测试可视化接口 ===")
    
    test_data = {
        "image_url": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/6ffd2a19045077324e3eda50cd6612aa.jpg",
        "labels_data": [
            [0, 0.574219, 0.504101, 0.232813, 0.518453],  # pig
            [1, 0.398047, 0.518746, 0.086719, 0.562976]   # ruler
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/detect_and_visualize",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 保存返回的图片文件
            filename = f"visualization_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"可视化图片已保存为: {filename}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    print("开始测试高级猪检测API...")
    
    # 运行所有测试
    tests = [
        ("健康检查", test_health_check),
        ("高级检测", test_advanced_detection),
        ("仅测量计算", test_measurements_only),
        ("仅可视化", test_visualize_only)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        success = test_func()
        results.append((test_name, success))
    
    # 输出测试结果汇总
    print(f"\n{'='*50}")
    print("测试结果汇总:")
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"- {test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n总计: {passed}/{total} 个测试通过")