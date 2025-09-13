#!/usr/bin/env python3
"""
测试conda虚拟环境设置脚本
仅用于测试环境的conda环境管理
"""

import subprocess
import sys
import os

def check_conda():
    """检查conda是否已安装"""
    try:
        result = subprocess.run(['conda', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Conda已安装: {result.stdout.strip()}")
            return True
        else:
            print("✗ Conda未安装或不在PATH中")
            return False
    except FileNotFoundError:
        print("✗ Conda未找到，请先安装Anaconda或Miniconda")
        return False

def create_conda_env():
    """创建conda虚拟环境"""
    env_file = os.path.join(os.path.dirname(__file__), "test_conda_env.yml")
    if not os.path.exists(env_file):
        print(f"✗ 环境配置文件 {env_file} 不存在")
        return False
    
    print("正在创建conda虚拟环境...")
    try:
        result = subprocess.run(['conda', 'env', 'create', '-f', env_file], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Conda虚拟环境创建成功")
            return True
        else:
            print(f"✗ 创建环境失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ 创建环境时出错: {e}")
        return False

def activate_env_instructions():
    """显示激活环境的说明"""
    print("\n" + "="*50)
    print("Conda虚拟环境设置完成！")
    print("="*50)
    print("\n要激活虚拟环境，请运行:")
    print("conda activate pig-detector-test")
    print("\n要停用虚拟环境，请运行:")
    print("conda deactivate")
    print("\n要删除虚拟环境，请运行:")
    print("conda env remove -n pig-detector-test")
    print("\n要查看所有环境，请运行:")
    print("conda env list")

def main():
    """主函数"""
    print("Pig Detector - Conda虚拟环境测试设置")
    print("="*40)
    
    if not check_conda():
        sys.exit(1)
    
    # 检查环境是否已存在
    try:
        result = subprocess.run(['conda', 'env', 'list'], capture_output=True, text=True)
        if 'pig-detector-test' in result.stdout:
            print("✓ 虚拟环境 'pig-detector-test' 已存在")
            activate_env_instructions()
            return
    except Exception as e:
        print(f"检查环境时出错: {e}")
    
    # 创建新环境
    if create_conda_env():
        activate_env_instructions()
    else:
        print("环境创建失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()