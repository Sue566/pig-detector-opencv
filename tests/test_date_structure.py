#!/usr/bin/env python3
"""
测试日期目录结构的脚本
"""
import requests
import json
import re
from datetime import datetime

def test_date_directory_structure():
    """测试API是否正确生成按日期分层的目录结构"""
    url = "http://119.96.28.202:8092/api/predict"
    
    # 使用示例图片测试
    test_image_url = "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800"
    
    print("🗓️  测试日期目录结构")
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
                    
                    # 检查基础URL格式
                    base_pattern = "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/"
                    if result_image_url.startswith(base_pattern):
                        print("✅ 基础路径正确")
                        
                        # 提取并验证日期路径
                        remaining_path = result_image_url[len(base_pattern):]
                        date_pattern = r'^(\d{4})/(\d{2})/(\d{2})/(.+)$'
                        match = re.match(date_pattern, remaining_path)
                        
                        if match:
                            year, month, day, filename = match.groups()
                            print(f"✅ 日期目录结构正确: {year}/{month}/{day}")
                            
                            # 验证日期是否为今天
                            today = datetime.now()
                            expected_year = today.strftime("%Y")
                            expected_month = today.strftime("%m")
                            expected_day = today.strftime("%d")
                            
                            if year == expected_year and month == expected_month and day == expected_day:
                                print("✅ 日期为今天，符合预期")
                            else:
                                print(f"⚠️  日期不是今天")
                                print(f"   期望: {expected_year}/{expected_month}/{expected_day}")
                                print(f"   实际: {year}/{month}/{day}")
                            
                            # 检查文件名格式
                            if "_pred_" in filename and filename.endswith('.jpg'):
                                print("✅ 文件名格式正确")
                            else:
                                print(f"⚠️  文件名格式可能不正确: {filename}")
                                
                        else:
                            print("❌ 日期目录结构不正确")
                            print(f"   期望格式: YYYY/MM/DD/filename.jpg")
                            print(f"   实际路径: {remaining_path}")
                    else:
                        print(f"❌ 基础路径不正确")
                        print(f"   期望: {base_pattern}")
                        print(f"   实际: {result_image_url}")
                else:
                    print("⚠️  未返回结果图片URL")
            else:
                print(f"❌ API返回错误: {data.get('msg', 'unknown error')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_multiple_requests():
    """测试多次请求是否都使用正确的日期结构"""
    print("\n🔄 测试多次请求的日期一致性")
    print("-" * 30)
    
    urls = []
    for i in range(3):
        try:
            response = requests.post("http://119.96.28.202:8092/api/predict", json={
                "image_path": "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800",
                "conf": 0.3
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    result_url = data.get('data', {}).get('result_image_url')
                    if result_url:
                        urls.append(result_url)
                        print(f"请求 {i+1}: ✅")
                    else:
                        print(f"请求 {i+1}: ⚠️  无URL")
                else:
                    print(f"请求 {i+1}: ❌ {data.get('msg')}")
            else:
                print(f"请求 {i+1}: ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"请求 {i+1}: ❌ {e}")
    
    # 检查所有URL的日期部分是否一致
    if len(urls) > 1:
        date_parts = []
        for url in urls:
            match = re.search(r'/(\d{4}/\d{2}/\d{2})/', url)
            if match:
                date_parts.append(match.group(1))
        
        if len(set(date_parts)) == 1:
            print(f"✅ 所有请求使用相同日期: {date_parts[0]}")
        else:
            print(f"⚠️  不同请求使用了不同日期: {set(date_parts)}")

if __name__ == "__main__":
    test_date_directory_structure()
    test_multiple_requests()
    print("\n🏁 测试完成")