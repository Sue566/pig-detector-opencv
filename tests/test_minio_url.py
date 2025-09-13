#!/usr/bin/env python3
"""
测试Minio URL生成的脚本
"""
import requests
import json

def test_minio_url_format():
    """测试Minio URL格式是否正确"""
    url = "http://119.96.28.202:8092/api/predict"
    
    # 使用示例图片测试
    test_image_url = "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800"
    
    print("🧪 测试Minio URL格式")
    print("=" * 50)
    
    try:
        payload = {
            "image_path": test_image_url,
            "conf": 0.3,
            "top_k": 5
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                result_data = data.get('data', {})
                result_image_url = result_data.get('result_image_url')
                
                if result_image_url:
                    print(f"✅ 获得结果图片URL: {result_image_url}")
                    
                    # 检查URL格式是否正确
                    expected_pattern = "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/"
                    if result_image_url.startswith(expected_pattern):
                        print("✅ URL格式正确")
                        
                        # 检查是否包含年/月/日路径结构
                        import re
                        date_pattern = r"/\d{4}/\d{2}/\d{2}/"
                        if re.search(date_pattern, result_image_url):
                            print("✅ 日期目录结构正确")
                        else:
                            print("⚠️  缺少年/月/日目录结构")
                        
                        # 尝试访问图片URL
                        try:
                            img_response = requests.head(result_image_url, timeout=10)
                            if img_response.status_code == 200:
                                print("✅ 图片URL可访问")
                            else:
                                print(f"⚠️  图片URL返回状态码: {img_response.status_code}")
                        except Exception as e:
                            print(f"⚠️  无法访问图片URL: {e}")
                    else:
                        print(f"❌ URL格式不正确，期望以 {expected_pattern} 开头")
                        print(f"   实际URL: {result_image_url}")
                else:
                    print("⚠️  未返回结果图片URL")
            else:
                print(f"❌ API返回错误: {data.get('msg', 'unknown error')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_minio_url_format()