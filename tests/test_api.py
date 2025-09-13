#!/usr/bin/env python3
"""
测试FastAPI服务的简单脚本
"""
import requests
import json
import sys
from pathlib import Path

def test_api_connection(base_url="http://localhost:8092"):
    """测试API连接和基本功能"""
    
    print(f"测试API连接: {base_url}")
    
    # 测试版本接口
    try:
        response = requests.get(f"{base_url}/api/version", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                version_info = data.get('data', {})
                print(f"✅ 版本接口正常: {version_info}")
            else:
                print(f"❌ API错误: {data.get('msg', 'unknown error')}")
        else:
            print(f"❌ 版本接口错误: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到API服务: {e}")
        return False
    
    # 测试预测接口（使用示例图片）
    test_image_path = "dataset/train/images"
    image_files = list(Path(test_image_path).glob("*.jpg"))
    
    if image_files:
        test_image = str(image_files[0])
        print(f"使用测试图片: {test_image}")
        
        try:
            payload = {
                "image_path": test_image,
                "conf": 0.5,
                "top_k": 10
            }
            
            response = requests.post(
                f"{base_url}/api/predict",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    result = data.get('data', {})
                    print(f"✅ 预测接口正常: 检测到 {len(result.get('results', []))} 个对象")
                    print(f"   类型: {result.get('type', 'unknown')}")
                else:
                    print(f"❌ API错误: {data.get('msg', 'unknown error')}")
            else:
                print(f"❌ 预测接口错误: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 预测请求失败: {e}")
            return False
    else:
        print("⚠️  未找到测试图片，跳过预测测试")
    
    print("✅ API测试完成")
    return True

def main():
    """主函数"""
    base_url = "http://localhost:8092"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    success = test_api_connection(base_url)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()