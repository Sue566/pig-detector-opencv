# API接口测试指南

## 概述
本指南详细说明如何在conda环境中测试pig-detector项目的API接口。

## 环境准备

### 1. 创建并激活conda环境
```bash
# 创建环境
conda env create -f tests/test_conda_env.yml

# 激活环境
conda activate pig-detector-test
```

### 2. 安装API依赖和配置
```bash
cd tests
python test_conda_api_setup.py
```

## API服务架构

### FastAPI服务
- **文件**: `scripts/api.py`  
- **端口**: 8000
- **特点**: 现代化API框架，自动文档生成，高性能异步处理

## 测试方法

### 方法1: 自动化测试（推荐）
```bash
cd tests
python test_api_interfaces.py
```

这个脚本会：
- 检查所有依赖
- 自动启动FastAPI服务
- 测试所有端点的连通性
- 提供详细的测试报告

### 方法2: 手动测试

#### 启动FastAPI
```bash
conda activate pig-detector-test
uvicorn scripts.api:app --reload --port 8000
```

#### 测试端点
```bash
# FastAPI健康检查
curl -X GET http://localhost:8000/health

# 查看FastAPI交互式文档
# 浏览器访问: http://localhost:8000/docs
```

## API端点详情

### FastAPI端点

| 端点 | 方法 | 描述 | 示例 |
|------|------|------|------|
| `/health` | GET | 健康检查 | `curl http://localhost:8000/health` |
| `/docs` | GET | 交互式文档 | 浏览器访问 |
| `/openapi.json` | GET | OpenAPI规范 | API规范文件 |
| `/predict` | POST | 预测接口 | 通过文档测试 |

## 测试数据准备

### 图片上传测试
```bash
# 使用curl上传图片测试Flask API
curl -X POST http://localhost:5000/api/detect \
  -F "image=@path/to/test/image.jpg"

# 使用curl上传图片测试FastAPI
curl -X POST http://localhost:8000/predict \
  -F "file=@path/to/test/image.jpg"
```

### JSON数据测试
```bash
# 测试JSON格式数据
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"image_url": "http://example.com/image.jpg"}'
```

## 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 查看端口占用
lsof -i :5000
lsof -i :8000

# 杀死占用进程
kill -9 <PID>
```

#### 2. 依赖包缺失
```bash
# 重新安装依赖
conda activate pig-detector-test
pip install -r requirements.txt
python tests/test_conda_api_setup.py
```

#### 3. 模型文件缺失
```bash
# 检查模型文件
ls -la models/
# 确保有必要的.pt模型文件
```

#### 4. 权限问题
```bash
# 给脚本执行权限
chmod +x tests/test_api_interfaces.py
chmod +x tests/test_conda_api_setup.py
```

### 调试模式

#### Flask调试
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python advanced_pig_api.py
```

#### FastAPI调试
```bash
uvicorn scripts.api:app --reload --log-level debug --port 8000
```

## 性能测试

### 简单压力测试
```bash
# 安装ab工具 (Apache Bench)
# macOS: brew install httpie
# Ubuntu: sudo apt-get install apache2-utils

# 测试健康检查端点
ab -n 100 -c 10 http://localhost:5000/health
ab -n 100 -c 10 http://localhost:8000/health
```

### 并发测试
```python
# 使用Python进行并发测试
import concurrent.futures
import requests
import time

def test_endpoint(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code
    except:
        return 0

# 测试并发请求
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(test_endpoint, "http://localhost:5000/health") 
               for _ in range(50)]
    results = [future.result() for future in futures]
    
print(f"成功请求: {results.count(200)}/{len(results)}")
```

## 监控和日志

### 查看日志
```bash
# Flask应用日志通常输出到控制台
# FastAPI使用uvicorn日志

# 如果需要保存日志到文件
python advanced_pig_api.py > flask_api.log 2>&1 &
uvicorn scripts.api:app --log-file fastapi.log --port 8000 &
```

### 健康监控
```bash
# 创建简单的健康检查脚本
#!/bin/bash
while true; do
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo "$(date): Flask API - OK"
    else
        echo "$(date): Flask API - DOWN"
    fi
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "$(date): FastAPI - OK"
    else
        echo "$(date): FastAPI - DOWN"
    fi
    
    sleep 30
done
```

## 最佳实践

1. **环境隔离**: 始终在conda虚拟环境中运行
2. **依赖管理**: 定期更新requirements.txt
3. **错误处理**: 实现适当的错误处理和日志记录
4. **安全性**: 在生产环境中配置适当的安全措施
5. **监控**: 实施健康检查和性能监控
6. **文档**: 保持API文档的更新

## 部署建议

### 开发环境
- 使用conda环境进行依赖管理
- 启用调试模式便于开发
- 使用自动重载功能

### 生产环境
- 使用Docker容器化部署
- 配置反向代理(nginx)
- 实施负载均衡
- 配置SSL/TLS加密
- 设置监控和告警