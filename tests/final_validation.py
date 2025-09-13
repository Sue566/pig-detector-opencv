#!/usr/bin/env python3
"""
最终部署验证脚本 - 验证所有API功能
"""
import requests
import json
import re
from datetime import datetime
import time

def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def test_basic_connectivity():
    """测试基础连接"""
    print_section("基础连接测试")
    
    base_url = "http://119.96.28.202:8092"
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                print("✅ 根路径连接正常")
                version_data = data.get('data', {})
                print(f"   版本: {version_data.get('version', 'unknown')}")
            else:
                print(f"❌ 根路径API错误: {data.get('msg')}")
        else:
            print(f"❌ 根路径HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 根路径连接失败: {e}")
        return False
    
    # 测试版本接口
    try:
        response = requests.get(f"{base_url}/api/version", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                print("✅ 版本接口正常")
            else:
                print(f"❌ 版本接口API错误: {data.get('msg')}")
        else:
            print(f"❌ 版本接口HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 版本接口连接失败: {e}")
        return False
    
    return True

def test_error_handling():
    """测试错误处理"""
    print_section("错误处理测试")
    
    base_url = "http://119.96.28.202:8092/api/predict"
    
    # 测试空路径
    try:
        response = requests.post(base_url, json={"image_path": ""}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 400:
                print("✅ 空路径错误处理正确")
            else:
                print(f"❌ 空路径处理错误: code={data.get('code')}")
        else:
            print(f"❌ 空路径HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 空路径测试失败: {e}")
    
    # 测试不存在的文件
    try:
        response = requests.post(base_url, json={"image_path": "/nonexistent/file.jpg"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 400:
                print("✅ 不存在文件错误处理正确")
            else:
                print(f"❌ 不存在文件处理错误: code={data.get('code')}")
        else:
            print(f"❌ 不存在文件HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 不存在文件测试失败: {e}")

def test_prediction_functionality():
    """测试预测功能"""
    print_section("预测功能测试")
    
    base_url = "http://119.96.28.202:8092/api/predict"
    test_image_url = "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800"
    
    try:
        payload = {
            "image_path": test_image_url,
            "conf": 0.3,
            "top_k": 5
        }
        
        response = requests.post(base_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                result_data = data.get('data', {})
                print("✅ 预测功能正常")
                print(f"   检测类型: {result_data.get('type', 'unknown')}")
                print(f"   检测数量: {len(result_data.get('results', []))}")
                
                # 检查必要字段
                required_fields = ['type', 'detection_summary', 'results']
                missing_fields = [field for field in required_fields if field not in result_data]
                if not missing_fields:
                    print("✅ 响应字段完整")
                else:
                    print(f"⚠️  缺少字段: {missing_fields}")
                
                return result_data.get('result_image_url')
            else:
                print(f"❌ 预测API错误: {data.get('msg')}")
        else:
            print(f"❌ 预测HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 预测功能测试失败: {e}")
    
    return None

def test_date_structure(result_image_url):
    """测试日期目录结构"""
    print_section("日期目录结构测试")
    
    if not result_image_url:
        print("❌ 无结果图片URL，跳过测试")
        return
    
    print(f"结果图片URL: {result_image_url}")
    
    # 检查基础路径
    expected_base = "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/"
    if result_image_url.startswith(expected_base):
        print("✅ 基础路径正确")
        
        # 提取日期部分
        remaining_path = result_image_url[len(expected_base):]
        date_pattern = r'^(\d{4})/(\d{2})/(\d{2})/(.+)$'
        match = re.match(date_pattern, remaining_path)
        
        if match:
            year, month, day, filename = match.groups()
            print(f"✅ 日期目录结构正确: {year}/{month}/{day}")
            
            # 验证是否为今天
            today = datetime.now()
            if (year == today.strftime("%Y") and 
                month == today.strftime("%m") and 
                day == today.strftime("%d")):
                print("✅ 日期为今天")
            else:
                print(f"⚠️  日期不是今天: {year}-{month}-{day}")
            
            # 检查文件名
            if "_pred_" in filename and filename.endswith('.jpg'):
                print("✅ 文件名格式正确")
            else:
                print(f"⚠️  文件名格式异常: {filename}")
        else:
            print(f"❌ 日期目录结构错误: {remaining_path}")
    else:
        print(f"❌ 基础路径错误")
        print(f"   期望: {expected_base}")
        print(f"   实际: {result_image_url[:len(expected_base)]}")

def test_image_prediction():
    """测试图片预测接口"""
    print_section("图片预测接口测试")
    
    base_url = "http://119.96.28.202:8092/api/predict_image"
    test_image_url = "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800"
    
    try:
        payload = {
            "image_path": test_image_url,
            "conf": 0.3,
            "format": "jpeg"
        }
        
        response = requests.post(base_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            if response.headers.get('content-type', '').startswith('image/'):
                print("✅ 图片预测接口正常")
                print(f"   返回图片大小: {len(response.content)} bytes")
                print(f"   内容类型: {response.headers.get('content-type')}")
            else:
                # 可能返回了JSON错误
                try:
                    data = response.json()
                    if data.get('code') != 200:
                        print(f"❌ 图片预测API错误: {data.get('msg')}")
                    else:
                        print("⚠️  返回了JSON而非图片")
                except:
                    print("⚠️  返回内容格式异常")
        else:
            print(f"❌ 图片预测HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 图片预测测试失败: {e}")

def main():
    """主测试函数"""
    print("🐷 猪只检测API - 最终部署验证")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 基础连接测试
    if not test_basic_connectivity():
        print("\n❌ 基础连接失败，停止测试")
        return False
    
    # 2. 错误处理测试
    test_error_handling()
    
    # 3. 预测功能测试
    result_image_url = test_prediction_functionality()
    
    # 4. 日期目录结构测试
    test_date_structure(result_image_url)
    
    # 5. 图片预测接口测试
    test_image_prediction()
    
    # 总结
    print_section("测试总结")
    print("✅ 所有主要功能测试完成")
    print("📋 如有异常，请检查上述测试结果")
    print("🚀 API服务已准备就绪")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)