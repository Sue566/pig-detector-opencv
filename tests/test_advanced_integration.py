#!/usr/bin/env python3
"""
测试高级API集成
"""
import requests
import json
from datetime import datetime

def test_advanced_api():
    """测试高级检测API"""
    base_url = "http://119.96.28.202:8092"
    
    print("🧪 测试高级检测API集成...")
    
    # 测试数据
    test_data = {
        "image_path": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/6ffd2a19045077324e3eda50cd6612aa.jpg",
        "conf": 0.5,
        "top_k": 10,
        "return_visualization": True,
        "ruler_length_cm": 30.0,
        "base_length_cm": 60.0,
        "base_width_cm": 40.0
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/predict_advanced",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 高级检测成功!")
            print(f"响应格式: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 验证响应格式
            if result.get("code") == 200 and "data" in result:
                data = result["data"]
                print(f"\n📊 检测结果:")
                print(f"- 检测类型: {data.get('type')}")
                print(f"- 检测对象数量: {len(data.get('detections', []))}")
                
                measurements = data.get('measurements', {})
                print(f"\n📏 测量结果:")
                print(f"- 长度: {measurements.get('length_cm'):.1f} cm" if measurements.get('length_cm') else "- 长度: 无法计算")
                print(f"- 重量: {measurements.get('weight_kg'):.1f} kg" if measurements.get('weight_kg') else "- 重量: 无法计算")
                if measurements.get('weight_range_kg'):
                    weight_range = measurements['weight_range_kg']
                    print(f"- 重量范围: {weight_range[0]:.1f} - {weight_range[1]:.1f} kg")
                print(f"- 计算方法: {measurements.get('calculation_method', '未知')}")
                
                # 检查可视化结果
                if 'result_image_url' in data:
                    print(f"\n🎨 可视化结果: {data['result_image_url']}")
                elif 'result_image_path' in data:
                    print(f"\n🎨 可视化结果: {data['result_image_path']}")
                elif 'visualization_error' in data:
                    print(f"\n❌ 可视化失败: {data['visualization_error']}")
                
                return True
            else:
                print("❌ 响应格式不正确")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_original_api():
    """测试原有API是否仍然正常工作"""
    base_url = "http://119.96.28.202:8092"
    
    print("\n🧪 测试原有API兼容性...")
    
    test_data = {
        "image_path": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/6ffd2a19045077324e3eda50cd6612aa.jpg",
        "conf": 0.5,
        "top_k": 10
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/predict",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 原有API正常工作!")
            
            if result.get("code") == 200 and "data" in result:
                data = result["data"]
                print(f"- 检测类型: {data.get('type')}")
                print(f"- 长度: {data.get('length_cm'):.1f} cm" if data.get('length_cm') else "- 长度: 无法计算")
                print(f"- 重量: {data.get('weight_kg'):.1f} kg" if data.get('weight_kg') else "- 重量: 无法计算")
                return True
            else:
                print("❌ 原有API响应格式异常")
                return False
        else:
            print(f"❌ 原有API请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 原有API测试失败: {e}")
        return False

def test_health_endpoints():
    """测试健康检查端点"""
    base_url = "http://119.96.28.202:8092"
    
    print("\n🧪 测试健康检查端点...")
    
    endpoints = [
        ("/", "根路径"),
        ("/api/version", "版本信息")
    ]
    
    results = []
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {name} 正常")
                results.append(True)
            else:
                print(f"❌ {name} 异常: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name} 测试失败: {e}")
            results.append(False)
    
    return all(results)

if __name__ == "__main__":
    print("🚀 开始测试高级API集成...")
    print("=" * 60)
    
    # 运行所有测试
    tests = [
        ("健康检查", test_health_endpoints),
        ("原有API兼容性", test_original_api),
        ("高级检测API", test_advanced_api)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        results.append((test_name, success))
    
    # 输出测试结果汇总
    print(f"\n{'='*60}")
    print("📋 测试结果汇总:")
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n🎯 总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！高级API集成成功！")
        print("\n📝 部署建议:")
        print("1. 提交代码: git add . && git commit -m '集成高级检测API'")
        print("2. 推送代码: git push origin main")
        print("3. 服务器部署:")
        print("   - cd /www/wwwroot/huangshi/tools/pig-detector-opencv")
        print("   - git pull origin main")
        print("   - source py-project-env pig-detector-opencv")
        print("   - pkill -f uvicorn")
        print("   - nohup python -m uvicorn scripts.api:app --host 0.0.0.0 --port 8092 > api.log 2>&1 &")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查问题后重新测试")