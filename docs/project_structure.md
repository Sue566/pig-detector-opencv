# 项目目录结构说明

## 概述
本文档说明pig-detector-opencv项目的完整目录结构和文件组织方式。

## 目录结构

```
pig-detector-opencv/
├── 📁 tests/                          # 测试文件目录
│   ├── test_conda_env.yml             # conda环境配置文件
│   ├── test_conda_setup.py            # conda环境自动设置脚本
│   ├── test_conda_api_setup.py        # API依赖设置脚本
│   ├── test_api_interfaces.py         # API接口测试脚本
│   ├── test_*.py                      # 各种功能测试脚本
│   └── README.md                      # 测试说明文档
│
├── 📁 docs/                           # 文档目录
│   ├── conda_usage.md                 # conda环境使用说明
│   ├── api_testing_guide.md           # API测试指南
│   ├── project_structure.md           # 本文档
│   ├── README.md                      # 项目主要说明
│   ├── API_DOCUMENTATION.md           # API文档
│   ├── API部署说明.md                  # API部署说明
│   ├── 高级API集成部署说明.md           # 高级API集成说明
│   ├── 高级检测模块部署说明.md          # 高级检测模块说明
│   ├── 体重计算优化说明.md             # 体重计算优化说明
│   └── 颜色问题修复说明.md             # 颜色问题修复说明
│
├── 📁 examples/                       # 示例和演示文件
│   ├── measurement_demo.py            # 测量演示脚本
│   ├── simple_visualize.py            # 简单可视化脚本
│   ├── advanced_visualize.py          # 高级可视化脚本
│   ├── visualize_detection.py         # 检测结果可视化
│   └── analyze_detection.py           # 检测分析脚本
│
├── 📁 scripts/                        # 脚本目录
│   ├── api.py                         # FastAPI服务脚本
│   ├── start_advanced_api.py          # 高级API启动脚本
│   ├── advanced_api_integration.py    # API集成脚本
│   └── deployment/                    # 部署脚本子目录
│       ├── build_docker.sh           # Docker构建脚本
│       ├── deploy_color_fix.sh        # 颜色修复部署脚本
│       ├── package_api.sh             # API打包脚本
│       ├── start_api.sh               # API启动脚本
│       └── start_train.sh             # 训练启动脚本
│
├── 📁 advanced_detection/             # 高级检测模块
│   ├── core/                          # 核心功能
│   ├── visualization/                 # 可视化功能
│   └── api/                           # API接口
│
├── 📁 utils/                          # 工具函数
│   └── measurement_utils.py           # 测量工具函数
│
├── 📁 models/                         # 模型文件
├── 📁 dataset/                        # 数据集
├── 📁 logs/                           # 日志文件
├── 📁 temp/                           # 临时文件
├── 📁 venv/                           # Python虚拟环境
│
├── 🐷 advanced_pig_api.py             # Flask API主服务文件
├── ⚙️ config.yaml                     # 配置文件
├── 🐳 Dockerfile                      # Docker配置
├── 🐳 docker-compose.yml              # Docker Compose配置
├── 📦 requirements.txt                # Python依赖
├── 📦 pig-detector.tar                # 项目打包文件
└── 📄 .gitignore                      # Git忽略文件
```

## 目录功能说明

### 📁 tests/ - 测试目录
包含所有测试相关文件，包括：
- **conda环境管理**: 环境配置和自动化设置
- **API接口测试**: 完整的API功能测试
- **功能测试**: 各种检测功能的单元测试
- **集成测试**: 端到端的集成测试

### 📁 docs/ - 文档目录
包含所有项目文档，包括：
- **使用说明**: conda环境、API使用指南
- **部署文档**: 各种部署场景的详细说明
- **技术文档**: API文档、架构说明
- **问题解决**: 常见问题和修复说明

### 📁 examples/ - 示例目录
包含演示和示例代码：
- **可视化示例**: 各种检测结果的可视化演示
- **功能演示**: 测量、分析等功能的使用示例
- **学习材料**: 帮助理解项目功能的示例代码

### 📁 scripts/ - 脚本目录
包含各种自动化脚本：
- **API服务**: FastAPI和相关服务脚本
- **部署脚本**: Docker、打包、启动等自动化脚本
- **集成脚本**: 各种功能集成的辅助脚本

## 文件类型分类

### Python脚本分类
- **API服务**: `advanced_pig_api.py`, `scripts/api.py`
- **测试脚本**: `tests/test_*.py`
- **示例脚本**: `examples/*.py`
- **工具脚本**: `scripts/*.py`

### 文档分类
- **中文文档**: `docs/*说明.md`
- **英文文档**: `docs/*.md`
- **配置文档**: `tests/*.yml`, `config.yaml`

### 配置文件
- **Python环境**: `requirements.txt`, `tests/test_conda_env.yml`
- **Docker配置**: `Dockerfile`, `docker-compose.yml`
- **项目配置**: `config.yaml`, `.gitignore`

## 使用建议

### 开发环境设置
1. 使用`tests/`目录中的conda环境配置
2. 运行`tests/test_conda_setup.py`自动设置环境
3. 查看`docs/conda_usage.md`了解详细使用方法

### API开发和测试
1. 使用`tests/test_api_interfaces.py`进行API测试
2. 参考`docs/api_testing_guide.md`了解测试方法
3. 查看`examples/`目录了解API使用示例

### 部署和运维
1. 使用`scripts/deployment/`中的部署脚本
2. 参考`docs/`中的部署说明文档
3. 根据需要选择Docker或直接部署方式

## 维护说明

### 添加新功能
- 测试文件放入`tests/`目录
- 文档放入`docs/`目录
- 示例代码放入`examples/`目录
- 部署脚本放入`scripts/deployment/`目录

### 文件命名规范
- 测试文件: `test_*.py`
- 文档文件: `*.md`
- 脚本文件: `*.py`, `*.sh`
- 配置文件: `*.yml`, `*.yaml`, `*.json`

### 目录结构维护
- 保持目录功能单一性
- 定期清理临时文件
- 更新文档以反映结构变化
- 确保路径引用的正确性