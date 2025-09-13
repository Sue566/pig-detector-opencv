# 快速开始指南

## 🚀 项目快速启动

### 1. 环境设置
```bash
# 进入测试目录
cd tests

# 自动创建conda环境
python test_conda_setup.py

# 激活环境
conda activate pig-detector-test

# 配置API依赖
python test_conda_api_setup.py
```

### 2. 测试运行
```bash
# 在tests目录中运行API接口测试
python test_api_interfaces.py

# 运行基础功能测试
python test_ruler_detection.py
python test_color_fix.py
```

### 3. 启动FastAPI服务
```bash
# 启动FastAPI (端口8000)
uvicorn scripts.api:app --reload --port 8000

# 访问API文档
# 浏览器打开: http://localhost:8000/docs
```

### 4. 查看文档
```bash
# 查看完整使用说明
cat ../docs/conda_usage.md

# 查看API测试指南
cat ../docs/api_testing_guide.md

# 查看项目结构说明
cat ../docs/project_structure.md
```

## 📁 目录导航

- **测试**: `tests/` - 所有测试文件
- **文档**: `docs/` - 完整项目文档
- **示例**: `examples/` - 功能演示代码
- **脚本**: `scripts/` - 自动化脚本
- **部署**: `scripts/deployment/` - 部署相关脚本

## 🔧 常用命令

```bash
# conda环境管理
conda activate pig-detector-test
conda deactivate
conda env list

# API测试
curl http://localhost:5000/health
curl http://localhost:8000/health

# 查看API文档
# 浏览器访问: http://localhost:8000/docs
```

## 📖 更多信息

详细信息请查看 `docs/` 目录中的相关文档。