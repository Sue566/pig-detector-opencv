#!/usr/bin/env python3
"""
测试尺子检测功能
验证模型是否能正确检测到尺子
"""

import sys
import os
from pathlib import Path
import requests
import json

# 添加scripts路径
scripts_path = Path(__file__).parent / "scripts"
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

def test_local_prediction():
    """测试本地预测功能"""
    print("🔍 测试本地预测...")
    
    try:
        from predict import load_model, predict_image_with_model
        
        # 加载模型
        print("📦 加载模型...")
        model = load_model()
        
        # 测试图片（您提供的有尺子的图片）
        image_path = "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/6ffd2a19045077324e3eda50cd6612aa.jpg"
        
        # 使用不同的置信度阈值测试
        confidence_levels = [0.1, 0.3, 0.5, 0.7]
        
        for conf in confidence_levels:
            print(f"\n🎯 测试置信度阈值: {conf}")
            
            results = predict_image_with_model(model, image_path, conf=conf, top_k=20)
            
            print(f"  检测到 {len(results)} 个对象:")
            
            class_names = {0: "猪", 1: "尺子", 2: "底座"}
            class_counts = {0: 0, 1: 0, 2: 0}
            
            for i, result in enumerate(results):
                class_id = result.get('class_id', result.get('class', 0))
                confidence = result.get('confidence', result.get('score', 0))
                class_name = class_names.get(class_id, f"未知类别{class_id}")
                
                print(f"    {i+1}. {class_name} (ID:{class_id}) - 置信度: {confidence:.4f}")
                
                if class_id in class_counts:
                    class_counts[class_id] += 1
            
            print(f"  统计: 猪={class_counts[0]}, 尺子={class_counts[1]}, 底座={class_counts[2]}")
            
            # 如果检测到尺子，说明模型工作正常
            if class_counts[1] > 0:
                print(f"  ✅ 在置信度 {conf} 下检测到尺子！")
                return True
        
        print("  ❌ 在所有置信度下都未检测到尺子")
        return False
        
    except Exception as e:
        print(f"❌ 本地预测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_with_low_confidence():
    """测试API在低置信度下的表现"""
    print("\n🌐 测试API低置信度...")
    
    base_url = "http://119.96.28.202:8092"
    image_path = "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/6ffd2a19045077324e3eda50cd6612aa.jpg"
    
    # 测试不同置信度
    confidence_levels = [0.1, 0.3, 0.5]
    
    for conf in confidence_levels:
        print(f"\n🎯 API测试置信度: {conf}")
        
        test_data = {
            "image_path": image_path,
            "conf": conf,
            "top_k": 20,
            "return_visualization": True
        }
        
        try:
            # 测试基础API
            response = requests.post(
                f"{base_url}/api/predict",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 200 and "data" in result:
                    detections = result["data"].get("detections", [])
                    print(f"  基础API检测到 {len(detections)} 个对象:")
                    
                    class_counts = {0: 0, 1: 0, 2: 0}
                    for det in detections:
                        class_id = det.get("class_id", det.get("class", 0))
                        confidence = det.get("confidence", det.get("score", 0))
                        class_name = {0: "猪", 1: "尺子", 2: "底座"}.get(class_id, f"类别{class_id}")
                        
                        print(f"    - {class_name} (ID:{class_id}): {confidence:.4f}")
                        
                        if class_id in class_counts:
                            class_counts[class_id] += 1
                    
                    if class_counts[1] > 0:
                        print(f"  ✅ API在置信度 {conf} 下检测到尺子！")
                        
                        # 测试高级API
                        print("  🔬 测试高级API...")
                        adv_response = requests.post(
                            f"{base_url}/api/predict_advanced",
                            json=test_data,
                            timeout=30
                        )
                        
                        if adv_response.status_code == 200:
                            adv_result = adv_response.json()
                            if adv_result.get("code") == 200:
                                adv_data = adv_result["data"]
                                measurements = adv_data.get("measurements", {})
                                
                                print(f"    长度: {measurements.get('length_cm')} cm")
                                print(f"    重量: {measurements.get('weight_kg')} kg")
                                print(f"    方法: {measurements.get('calculation_method')}")
                                
                                if measurements.get('length_cm'):
                                    print("  ✅ 高级API成功计算出长度！")
                                    return True
                        
                        return True
                else:
                    print(f"  ❌ API返回错误: {result}")
            else:
                print(f"  ❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ API请求失败: {e}")
    
    return False

def analyze_training_data():
    """分析训练数据"""
    print("\n📊 分析训练数据...")
    
    label_file = "dataset/train/labels/6ffd2a19045077324e3eda50cd6612aa.txt"
    
    if os.path.exists(label_file):
        print(f"📄 读取标签文件: {label_file}")
        
        with open(label_file, 'r') as f:
            lines = f.readlines()
        
        print("标签内容:")
        class_names = {0: "猪", 1: "尺子", 2: "底座"}
        
        for i, line in enumerate(lines):
            parts = line.strip().split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                class_name = class_names.get(class_id, f"未知类别{class_id}")
                
                print(f"  {i+1}. {class_name} (ID:{class_id})")
                print(f"     位置: ({x_center:.3f}, {y_center:.3f})")
                print(f"     尺寸: {width:.3f} x {height:.3f}")
        
        return True
    else:
        print(f"❌ 标签文件不存在: {label_file}")
        return False

def check_model_classes():
    """检查模型类别配置"""
    print("\n🔧 检查模型配置...")
    
    # 查找配置文件
    config_files = [
        "dataset.yaml",
        "data.yaml", 
        "config.yaml",
        "dataset/data.yaml"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"📄 找到配置文件: {config_file}")
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print("配置内容:")
                print(content)
                
                # 查找类别定义
                if 'names:' in content or 'classes:' in content:
                    print("✅ 找到类别定义")
                    return True
                    
            except Exception as e:
                print(f"❌ 读取配置文件失败: {e}")
    
    print("❌ 未找到模型配置文件")
    return False

if __name__ == "__main__":
    print("🔍 开始尺子检测问题诊断...")
    print("=" * 60)
    
    # 运行所有测试
    tests = [
        ("训练数据分析", analyze_training_data),
        ("模型配置检查", check_model_classes),
        ("本地预测测试", test_local_prediction),
        ("API低置信度测试", test_api_with_low_confidence)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
            results.append((test_name, False))
    
    # 输出诊断结果
    print(f"\n{'='*60}")
    print("🏥 诊断结果:")
    
    for test_name, success in results:
        status = "✅ 正常" if success else "❌ 异常"
        print(f"  {test_name}: {status}")
    
    # 给出建议
    print(f"\n💡 建议:")
    
    if not results[0][1]:  # 训练数据问题
        print("  - 检查训练数据标签文件是否正确")
    
    if not results[1][1]:  # 配置问题
        print("  - 检查模型配置文件中的类别定义")
    
    if not results[2][1]:  # 本地预测问题
        print("  - 模型可能未正确训练尺子类别")
        print("  - 或者需要降低置信度阈值")
    
    if not results[3][1]:  # API问题
        print("  - API默认置信度可能过高")
        print("  - 建议在API调用时设置 conf=0.3 或更低")
    
    print(f"\n🎯 快速修复建议:")
    print("  1. 在API调用时使用较低的置信度: conf=0.3")
    print("  2. 检查模型是否正确训练了尺子类别")
    print("  3. 如果模型正常，可能需要调整API默认参数")