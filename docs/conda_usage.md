# Conda虚拟环境使用说明

## 概述
本文档说明如何在测试环境中使用conda虚拟环境来运行pig-detector项目。

## 前提条件
- 已安装Anaconda或Miniconda
- conda命令在系统PATH中可用

## 快速开始

### 1. 自动设置（推荐）
```bash
cd tests
python test_conda_setup.py
```

### 2. 手动设置
```bash
# 创建虚拟环境
conda env create -f tests/test_conda_env.yml

# 激活虚拟环境
conda activate pig-detector-test

# 验证安装
python -c "import cv2, numpy, flask; print('所有依赖已安装')"
```

## 常用命令

### 环境管理
```bash
# 激活环境
conda activate pig-detector-test

# 停用环境
conda deactivate

# 查看所有环境
conda env list

# 删除环境
conda env remove -n pig-detector-test
```

### 包管理
```bash
# 在激活的环境中安装新包
conda install package_name

# 或使用pip安装
pip install package_name

# 查看已安装的包
conda list

# 导出环境配置
conda env export > test_environment_backup.yml
```

## 测试运行

### 基础测试
激活环境后，可以运行以下测试：

```bash
# 激活环境
conda activate pig-detector-test

# 运行基础测试脚本
python test_ruler_detection.py
python test_advanced_detection_complete.py
python test_color_fix.py

# 或在tests目录中运行
cd tests
python quick_test.py
python test_api_complete.py
```

### API接口测试

#### 1. 快速API设置和测试
```bash
# 激活conda环境
conda activate pig-detector-test

# 进入tests目录
cd tests

# 运行API设置脚本（安装额外依赖，添加健康检查端点）
python test_conda_api_setup.py

# 运行完整的API接口测试
python test_api_interfaces.py
```

#### 2. 手动启动FastAPI服务

```bash
conda activate pig-detector-test
uvicorn scripts.api:app --reload --port 8000
# 访问文档: http://localhost:8000/docs
```

#### 3. API端点测试
```bash
# 测试FastAPI健康检查  
curl http://localhost:8000/health

# 查看FastAPI交互式文档
# 浏览器访问: http://localhost:8000/docs
```

## 故障排除

### 常见问题

1. **conda命令未找到**
   - 确保已安装Anaconda/Miniconda
   - 重新启动终端或运行 `source ~/.bashrc`

2. **环境创建失败**
   - 检查网络连接
   - 尝试使用不同的conda频道：`conda config --add channels conda-forge`

3. **包安装失败**
   - 尝试使用pip安装：`pip install package_name`
   - 检查包名是否正确

### 清理和重置
```bash
# 完全删除环境并重新创建
conda env remove -n pig-detector-test
cd tests
python test_conda_setup.py
```

## 文件结构

```
pig-detector-opencv/
├── tests/
│   ├── test_conda_env.yml          # conda环境配置文件
│   ├── test_conda_setup.py         # 自动化conda环境设置脚本
│   ├── test_conda_api_setup.py     # API依赖设置和配置脚本
│   ├── test_api_interfaces.py      # 完整的API接口测试脚本
│   └── ...                         # 其他测试文件
├── docs/
│   ├── conda_usage.md              # 本文档
│   └── ...                         # 其他文档
├── advanced_pig_api.py             # Flask API服务
├── scripts/
│   ├── api.py                      # FastAPI服务
│   └── ...
└── ...
```

## API服务说明

项目使用FastAPI作为主要API框架：

### FastAPI (`scripts/api.py`)  
- **端口**: 8000
- **特点**: 现代化API框架，自动生成文档，高性能异步处理
- **主要端点**:
  - `GET /health` - 健康检查
  - `GET /docs` - 交互式API文档
  - `POST /predict` - 预测接口

### 依赖包说明
conda环境包含以下API相关依赖：
- `FastAPI` - 现代化API框架
- `uvicorn` - ASGI服务器
- `pydantic` - 数据验证和序列化
- `python-multipart` - 文件上传支持
- `ultralytics` - YOLO模型支持
- `torch` - PyTorch深度学习框架

## 注意事项
- 此配置仅用于测试环境
- 生产环境请使用适当的部署配置
- 定期更新依赖包以确保安全性
- 所有conda相关文件都位于tests目录中，保持项目结构清晰