#!/usr/bin/env python3
"""
完整的API测试脚本
"""
import requests
import json
import sys
import time
from pathlib import Path

def test_api_endpoints(base_url="http://119.96.28.202:8092"):
    """测试所有API端点"""
    
    print(f"🧪 测试API服务: {base_url}")
    print("=" * 60)
    
    # 1. 测试根路径
    print("1️⃣ 测试根路径 /")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                print(f"   ✅ 成功: {data.get('msg', '')}")
                print(f"   数据: {data.get('data', {})}")
            else:
                print(f"   ❌ API错误: {data.get('msg', 'unknown error')}")
        else:
            print(f"   ❌ 失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 2. 测试版本接口
    print("\n2️⃣ 测试版本接口 /api/version")
    try:
        response = requests.get(f"{base_url}/api/version", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                print(f"   ✅ 成功: {data.get('msg', '')}")
                print(f"   数据: {data.get('data', {})}")
            else:
                print(f"   ❌ API错误: {data.get('msg', 'unknown error')}")
        else:
            print(f"   ❌ 失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 3. 测试预测接口 - 使用空路径（应该报错）
    print("\n3️⃣ 测试预测接口 /api/predict - 空路径")
    try:
        payload = {"image_path": ""}
        response = requests.post(f"{base_url}/api/predict", json=payload, timeout=10)
        if response.status_code == 400:
            print(f"   ✅ 正确处理空路径: {response.json()}")
        else:
            print(f"   ⚠️  意外状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 4. 测试预测接口 - 使用不存在的文件
    print("\n4️⃣ 测试预测接口 /api/predict - 不存在的文件")
    try:
        payload = {"image_path": "/nonexistent/image.jpg"}
        response = requests.post(f"{base_url}/api/predict", json=payload, timeout=10)
        if response.status_code == 400:
            print(f"   ✅ 正确处理不存在文件: {response.json()}")
        else:
            print(f"   ⚠️  意外状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 5. 测试预测接口 - 使用示例URL图片
    print("\n5️⃣ 测试预测接口 /api/predict - 示例图片URL")
    test_image_url = "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800"
    try:
        payload = {
            "image_path": test_image_url,
            "conf": 0.3,
            "top_k": 5
        }
        response = requests.post(f"{base_url}/api/predict", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                result_data = data.get('data', {})
                print(f"   ✅ 成功: 检测类型={result_data.get('type')}, 结果数={len(result_data.get('results', []))}")
                if result_data.get('result_image_url'):
                    print(f"   🖼️  结果图片: {result_data['result_image_url']}")
            else:
                print(f"   ❌ API错误: {data.get('msg', 'unknown error')}")
        else:
            print(f"   ❌ 失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 6. 测试图片预测接口
    print("\n6️⃣ 测试图片预测接口 /api/predict_image")
    try:
        payload = {
            "image_path": test_image_url,
            "conf": 0.3,
            "format": "jpeg"
        }
        response = requests.post(f"{base_url}/api/predict_image", json=payload, timeout=30)
        if response.status_code == 200:
            print(f"   ✅ 成功: 返回图片大小={len(response.content)} bytes")
        else:
            print(f"   ❌ 失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 测试完成")

def test_local_image():
    """测试本地图片"""
    # 查找本地测试图片
    possible_paths = [
        "dataset/train/images",
        "dataset/val/images", 
        "test_images"
    ]
    
    test_image = None
    for path in possible_paths:
        if Path(path).exists():
            images = list(Path(path).glob("*.jpg")) + list(Path(path).glob("*.png"))
            if images:
                test_image = str(images[0])
                break
    
    if test_image:
        print(f"\n🖼️  测试本地图片: {test_image}")
        try:
            payload = {"image_path": test_image}
            response = requests.post("http://119.96.28.202:8092/api/predict", json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 成功: {data.get('type')}, 检测到 {len(data.get('results', []))} 个对象")
            else:
                print(f"   ❌ 失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
    else:
        print("\n⚠️  未找到本地测试图片")

def main():
    """主函数"""
    base_url = "http://119.96.28.202:8092"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
        print(f"   尝试连接... ({i+1}/10)")
    
    test_api_endpoints(base_url)
    test_local_image()

if __name__ == "__main__":
    main()