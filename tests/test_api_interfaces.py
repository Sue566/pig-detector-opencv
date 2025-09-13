#!/usr/bin/env python3
"""
测试所有API接口的连通性和功能
"""
import os
import sys
import requests
import time
import subprocess
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class APITester:
    def __init__(self):
        self.fastapi_port = 8000
        self.fastapi_process = None
        
    def check_dependencies(self):
        """检查API依赖"""
        print("检查API依赖...")
        required_packages = [
            'fastapi', 'uvicorn', 'pydantic', 
            'pillow', 'requests', 'numpy', 'cv2'
        ]
        
        missing = []
        for package in required_packages:
            try:
                if package == 'cv2':
                    import cv2
                else:
                    __import__(package)
                print(f"✓ {package}")
            except ImportError:
                print(f"✗ {package}")
                missing.append(package)
        
        if missing:
            print(f"\n缺少依赖: {', '.join(missing)}")
            print("请运行: conda activate pig-detector-test")
            return False
        
        print("✓ 所有依赖检查通过")
        return True
    

    
    def start_fastapi(self):
        """启动FastAPI"""
        print("启动FastAPI...")
        try:
            # 检查FastAPI文件是否存在
            fastapi_file = project_root / "scripts" / "api.py"
            if not fastapi_file.exists():
                print("✗ FastAPI文件不存在")
                return False
            
            # 启动FastAPI服务
            self.fastapi_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "scripts.api:app", 
                "--host", "0.0.0.0", 
                "--port", str(self.fastapi_port),
                "--reload"
            ], cwd=str(project_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待服务启动
            time.sleep(5)
            
            # 检查服务是否启动
            try:
                response = requests.get(f"http://localhost:{self.fastapi_port}/docs", timeout=5)
                if response.status_code == 200:
                    print("✓ FastAPI启动成功")
                    return True
            except:
                pass
            
            print("✗ FastAPI启动失败")
            return False
            
        except Exception as e:
            print(f"✗ FastAPI启动错误: {e}")
            return False
    

    
    def test_fastapi_endpoints(self):
        """测试FastAPI端点"""
        print("\n测试FastAPI端点...")
        base_url = f"http://localhost:{self.fastapi_port}"
        
        endpoints = [
            ("/docs", "GET", "API文档"),
            ("/health", "GET", "健康检查"),
            ("/predict", "POST", "预测接口")
        ]
        
        for endpoint, method, desc in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{base_url}{endpoint}", 
                                           json={"test": True}, timeout=5)
                
                if response.status_code in [200, 400, 422]:
                    print(f"✓ {desc} ({endpoint}): {response.status_code}")
                else:
                    print(f"✗ {desc} ({endpoint}): {response.status_code}")
                    
            except Exception as e:
                print(f"✗ {desc} ({endpoint}): 连接失败 - {e}")
    
    def cleanup(self):
        """清理进程"""
        print("\n清理服务进程...")
        if self.fastapi_process:
            self.fastapi_process.terminate()
            self.fastapi_process.wait()
            print("✓ FastAPI进程已终止")
    
    def run_full_test(self):
        """运行完整的API测试"""
        print("=" * 50)
        print("Pig Detector API接口测试")
        print("=" * 50)
        
        try:
            # 检查依赖
            if not self.check_dependencies():
                return False
            
            print("\n" + "-" * 30)
            print("启动FastAPI服务...")
            print("-" * 30)
            
            # 启动FastAPI服务
            fastapi_ok = self.start_fastapi()
            
            if not fastapi_ok:
                print("✗ FastAPI服务启动失败")
                return False
            
            # 测试端点
            self.test_fastapi_endpoints()
            
            print("\n" + "=" * 50)
            print("测试完成！")
            print("=" * 50)
            
            print(f"FastAPI服务: http://localhost:{self.fastapi_port}")
            print(f"FastAPI文档: http://localhost:{self.fastapi_port}/docs")
            
            print("\n按Enter键停止服务...")
            input()
            
            return True
            
        except KeyboardInterrupt:
            print("\n用户中断测试")
            return False
        finally:
            self.cleanup()

def main():
    """主函数"""
    tester = APITester()
    tester.run_full_test()

if __name__ == "__main__":
    main()