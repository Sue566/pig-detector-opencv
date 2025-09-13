#!/usr/bin/env python3
"""
Conda环境下的API设置和测试脚本
结合conda环境管理和API接口测试
"""
import subprocess
import sys
import os
from pathlib import Path

def check_conda_env():
    """检查是否在正确的conda环境中"""
    try:
        result = subprocess.run(['conda', 'info', '--envs'], capture_output=True, text=True)
        current_env = os.environ.get('CONDA_DEFAULT_ENV', 'base')
        
        if 'pig-detector-test' in result.stdout:
            if current_env == 'pig-detector-test':
                print("✓ 当前在pig-detector-test环境中")
                return True
            else:
                print(f"✗ 当前在{current_env}环境中，需要切换到pig-detector-test")
                print("请运行: conda activate pig-detector-test")
                return False
        else:
            print("✗ pig-detector-test环境不存在")
            print("请先运行: python test_conda_setup.py")
            return False
            
    except Exception as e:
        print(f"检查conda环境时出错: {e}")
        return False

def install_additional_packages():
    """安装额外的API依赖包"""
    print("安装额外的API依赖包...")
    
    additional_packages = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "python-multipart==0.0.6",
        "ultralytics==8.0.196",
        "python-jose[cryptography]==3.3.0"
    ]
    
    for package in additional_packages:
        try:
            print(f"安装 {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ {package} 安装成功")
            else:
                print(f"✗ {package} 安装失败: {result.stderr}")
                
        except Exception as e:
            print(f"✗ 安装 {package} 时出错: {e}")

def create_health_endpoints():
    """为FastAPI添加健康检查端点"""
    project_root = Path(__file__).parent.parent
    
    # 检查FastAPI文件
    fastapi_file = project_root / "scripts" / "api.py"
    if fastapi_file.exists():
        with open(fastapi_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@app.get("/health")' not in content:
            print("为FastAPI添加健康检查端点...")
            health_endpoint = '''

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "pig-detector-fastapi",
        "timestamp": datetime.now().isoformat()
    }
'''
            # 在导入后添加
            if 'from datetime import datetime' not in content:
                content = content.replace(
                    'from pydantic import BaseModel',
                    'from pydantic import BaseModel\nfrom datetime import datetime'
                )
            
            # 在app定义后添加端点
            content = content.replace(
                'app = FastAPI(title="Pig Detector API")',
                f'app = FastAPI(title="Pig Detector API"){health_endpoint}'
            )
            
            with open(fastapi_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✓ FastAPI健康检查端点已添加")

def main():
    """主函数"""
    print("=" * 50)
    print("Conda环境API设置和测试")
    print("=" * 50)
    
    # 检查conda环境
    if not check_conda_env():
        return
    
    # 安装额外依赖
    install_additional_packages()
    
    # 添加健康检查端点
    create_health_endpoints()
    
    print("\n" + "=" * 50)
    print("设置完成！现在可以测试API接口")
    print("=" * 50)
    print("\n运行API测试:")
    print("python test_api_interfaces.py")
    print("\n手动启动服务:")
    print("Flask API: python ../advanced_pig_api.py")
    print("FastAPI: uvicorn scripts.api:app --reload --port 8000")

if __name__ == "__main__":
    main()