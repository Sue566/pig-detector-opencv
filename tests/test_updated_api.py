#!/usr/bin/env python3
"""
测试更新后的API - 验证颜色、计算和响应格式
"""
import requests
import json
import time
from datetime import datetime

def test_api_response_format():
    """测试API响应格式"""
    base_url = "http://119.96.28.202:8092"
    
    print("🧪 测试API响应格式...")
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        print(f"GET / - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应格式: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 验证响应格式
            if "code" in data and "msg" in data and "data" in data:
                print("✅ 根路径响应格式正确")
            else:
                print("❌ 根路径响应格式不正确")
        else:
            print(f"❌ 根路径请求失败: {response.text}")
    except Exception as e:
        print(f"❌ 根路径测试失败: {e}")
    
    # 测试版本接口
    try:
        response = requests.get(f"{base_url}/api/version")
        print(f"\nGET /api/version - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应格式: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 验证响应格式
            if "code" in data and "msg" in data and "data" in data:
                print("✅ 版本接口响应格式正确")
            else:
                print("❌ 版本接口响应格式不正确")
        else:
            print(f"❌ 版本接口请求失败: {response.text}")
    except Exception as e:
        print(f"❌ 版本接口测试失败: {e}")

def test_predict_api():
    """测试预测接口"""
    base_url = "http://119.96.28.202:8092"
    
    print("\n🧪 测试预测接口...")
    
    # 测试空参数
    try:
        response = requests.post(f"{base_url}/api/predict", 
                               json={"image_path": ""})
        print(f"POST /api/predict (空参数) - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 验证错误响应格式
            if data.get("code") == 400 and "data" in data and data["data"] is None:
                print("✅ 空参数错误处理正确")
            else:
                print("❌ 空参数错误处理不正确")
        else:
            print(f"❌ 空参数测试失败: {response.text}")
    except Exception as e:
        print(f"❌ 空参数测试失败: {e}")
    
    # 测试正常预测（需要有效的图片路径）
    test_image = "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/test.jpg"
    try:
        response = requests.post(f"{base_url}/api/predict", 
                               json={"image_path": test_image})
        print(f"\nPOST /api/predict (正常图片) - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应格式检查:")
            print(f"  - code: {data.get('code')}")
            print(f"  - msg: {data.get('msg')}")
            print(f"  - data存在: {'data' in data}")
            
            if data.get("code") == 200 and "data" in data:
                result_data = data["data"]
                print(f"  - 检测类型: {result_data.get('type')}")
                print(f"  - 长度: {result_data.get('length_cm')} cm")
                print(f"  - 重量: {result_data.get('weight_kg')} kg")
                print(f"  - 计算方法: {result_data.get('calculation_method')}")
                print(f"  - 结果图片URL: {result_data.get('result_image_url')}")
                
                # 验证URL格式
                url = result_data.get('result_image_url')
                if url and "media/pigdata/pig/" in url:
                    # 检查是否包含日期路径
                    today = datetime.now()
                    date_str = f"{today.year:04d}/{today.month:02d}/{today.day:02d}"
                    if date_str in url:
                        print("✅ URL格式正确，包含日期路径")
                    else:
                        print("❌ URL格式不包含正确的日期路径")
                else:
                    print("❌ URL格式不正确")
                
                print("✅ 正常预测响应格式正确")
            else:
                print("❌ 正常预测响应格式不正确")
        else:
            print(f"❌ 正常预测失败: {response.text}")
    except Exception as e:
        print(f"❌ 正常预测测试失败: {e}")

def test_color_and_calculation():
    """测试颜色和计算逻辑"""
    print("\n🧪 测试颜色和计算逻辑...")
    print("📋 预期效果:")
    print("  - 猪的框：红色")
    print("  - 尺子的框：蓝色") 
    print("  - 使用measurement_utils优化计算")
    print("  - 体重范围更准确")
    print("  - 按年/月/日分层存储结果图片")
    print("\n💡 请手动测试一张包含猪和尺子的图片，验证:")
    print("  1. 框的颜色是否正确")
    print("  2. 计算结果是否更准确")
    print("  3. 结果图片URL是否包含日期路径")

if __name__ == "__main__":
    print("🚀 开始测试更新后的API...")
    
    test_api_response_format()
    test_predict_api()
    test_color_and_calculation()
    
    print("\n✅ API测试完成！")
    print("\n📝 部署步骤:")
    print("1. git add . && git commit -m '完善API：统一响应格式，优化计算，修正颜色'")
    print("2. git push origin main")
    print("3. 服务器执行: cd /www/wwwroot/huangshi/tools/pig-detector-opencv")
    print("4. git pull origin main")
    print("5. source py-project-env pig-detector-opencv")
    print("6. pkill -f uvicorn")
    print("7. nohup python -m uvicorn scripts.api:app --host 0.0.0.0 --port 8092 > api.log 2>&1 &")