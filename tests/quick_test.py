#!/usr/bin/env python3
"""
快速测试API接口
"""
import requests
import json

def test_predict_api():
    """测试预测接口"""
    url = "http://119.96.28.202:8092/api/predict"
    
    # 测试数据
    test_cases = [
        {
            "name": "空路径测试",
            "data": {"image_path": ""},
            "expect_status": 400
        },
        {
            "name": "示例图片URL测试", 
            "data": {
                "image_path": "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800",
                "conf": 0.3,
                "top_k": 5
            },
            "expect_status": 200
        }
    ]
    
    print("🧪 测试 /api/predict 接口")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        try:
            response = requests.post(url, json=test_case['data'], timeout=30)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == test_case['expect_status']:
                print("   ✅ 状态码正确")
            else:
                print(f"   ❌ 状态码错误，期望: {test_case['expect_status']}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    result_data = data.get('data', {})
                    print(f"   检测类型: {result_data.get('type', 'unknown')}")
                    print(f"   检测结果数: {len(result_data.get('results', []))}")
                    if result_data.get('result_image_url'):
                        print(f"   结果图片: {result_data['result_image_url']}")
                else:
                    print(f"   API返回错误: {data.get('msg', 'unknown error')}")
            else:
                try:
                    error_data = response.json()
                    print(f"   错误信息: {error_data.get('detail', 'unknown')}")
                except:
                    print(f"   响应内容: {response.text[:200]}")
                    
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

def test_version_api():
    """测试版本接口"""
    url = "http://119.96.28.202:8092/api/version"
    
    print("\n🔍 测试 /api/version 接口")
    print("-" * 30)
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                result_data = data.get('data', {})
                print("✅ 版本接口正常")
                print(f"   版本: {result_data.get('version', 'unknown')}")
                print(f"   训练时间: {result_data.get('trained_at', 'unknown')}")
            else:
                print(f"❌ API返回错误: {data.get('msg', 'unknown error')}")
        else:
            print(f"❌ 版本接口错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    test_version_api()
    test_predict_api()
    print("\n🏁 测试完成")