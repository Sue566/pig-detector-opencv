#!/usr/bin/env python3
"""
测试颜色修复
"""

import sys
from pathlib import Path

# 添加高级检测模块到路径
advanced_detection_path = Path(__file__).parent / "advanced_detection"
if str(advanced_detection_path) not in sys.path:
    sys.path.insert(0, str(advanced_detection_path))

from advanced_detection.core.config import CLASS_DEFINITIONS, get_class_info
from advanced_detection.visualization.renderer import AdvancedRenderer
from PIL import Image, ImageDraw

def test_color_definitions():
    """测试颜色定义"""
    print("🎨 测试颜色定义...")
    
    for class_id in [0, 1, 2]:
        info = get_class_info(class_id)
        print(f"类别 {class_id}: {info['name_cn']} - RGB: {info['color_rgb']}")
    
    return True

def create_test_image_with_colors():
    """创建测试图片验证颜色"""
    print("🖼️  创建测试图片...")
    
    # 创建测试图片
    img = Image.new('RGB', (800, 600), 'white')
    draw = ImageDraw.Draw(img)
    
    # 模拟检测结果
    detections = [
        {
            'class_id': 0,  # 猪
            'confidence': 0.95,
            'box': [100, 100, 300, 250]
        },
        {
            'class_id': 1,  # 尺子
            'confidence': 0.88,
            'box': [400, 100, 500, 120]
        },
        {
            'class_id': 2,  # 底座
            'confidence': 0.92,
            'box': [100, 300, 300, 400]
        }
    ]
    
    # 绘制不同颜色的框
    colors = {
        0: (255, 0, 0),    # 红色 - 猪
        1: (0, 100, 255),  # 蓝色 - 尺子
        2: (0, 200, 0)     # 绿色 - 底座
    }
    
    names = {0: "猪", 1: "尺子", 2: "底座"}
    
    for detection in detections:
        class_id = detection['class_id']
        confidence = detection['confidence']
        box = detection['box']
        
        x1, y1, x2, y2 = box
        color = colors[class_id]
        name = names[class_id]
        
        # 绘制边界框
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        
        # 绘制标签
        label = f"{name}: {confidence:.2f}"
        draw.rectangle([x1, y1-25, x1+150, y1], fill=color)
        draw.text((x1+5, y1-20), label, fill='white')
    
    # 保存测试图片
    output_path = "test_colors.jpg"
    img.save(output_path)
    print(f"✅ 测试图片已保存: {output_path}")
    
    return output_path

def test_api_with_real_data():
    """使用真实数据测试API"""
    print("🌐 测试API...")
    
    import requests
    
    # 使用您提供的图片
    test_data = {
        "image_path": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/6ffd2a19045077324e3eda50cd6612aa.jpg",
        "conf": 0.5,
        "return_visualization": True
    }
    
    try:
        response = requests.post(
            "http://119.96.28.202:8092/api/predict_advanced",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功")
            
            if result.get("code") == 200:
                data = result["data"]
                detections = data.get("detections", [])
                
                print(f"检测到 {len(detections)} 个对象:")
                for i, det in enumerate(detections):
                    class_id = det["class_id"]
                    confidence = det["confidence"]
                    class_names = {0: "猪", 1: "尺子", 2: "底座"}
                    class_name = class_names.get(class_id, f"未知类别{class_id}")
                    print(f"  {i+1}. {class_name} (ID:{class_id}) - 置信度: {confidence:.3f}")
                
                if "result_image_url" in data:
                    print(f"可视化图片: {data['result_image_url']}")
                
                return True
            else:
                print(f"❌ API返回错误: {result}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 开始颜色修复测试...")
    
    # 测试颜色定义
    test_color_definitions()
    
    # 创建测试图片
    create_test_image_with_colors()
    
    # 测试真实API
    test_api_with_real_data()
    
    print("\n📝 颜色配置说明:")
    print("🔴 猪: RGB(255, 0, 0) - 纯红色")
    print("🔵 尺子: RGB(0, 100, 255) - 蓝色") 
    print("🟢 底座: RGB(0, 200, 0) - 绿色")
    print("\n如果API返回的图片中颜色仍然不正确，请检查服务器是否已更新代码。")