#!/usr/bin/env python3
"""
启动猪只检测API服务器
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """启动API服务器"""
    # 设置项目根目录
    root_dir = Path(__file__).parent
    os.chdir(root_dir)
    
    print("🐷 启动猪只检测API服务器...")
    print(f"📁 工作目录: {root_dir}")
    
    # 检查必要文件
    required_files = [
        "scripts/api.py",
        "config.yaml",
        "models/v1_model.pth"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root_dir)
    
    # 启动服务器
    try:
        print("🚀 启动服务器在 http://0.0.0.0:8092")
        print("📖 API文档: http://localhost:8092/docs")
        print("🔍 版本信息: http://localhost:8092/api/version")
        print("⏹️  按 Ctrl+C 停止服务器")
        print("-" * 50)
        
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "scripts.api:app", 
            "--host", "0.0.0.0", 
            "--port", "8092",
            "--reload"
        ], env=env, cwd=root_dir)
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)