# 猪只检测API部署说明

## 🚀 快速部署

### 1. 本地准备和推送
```bash
# 1. 提交代码到git
git add .
git commit -m "完善API接口，统一JSON响应格式"
git push origin main

# 2. 运行部署脚本（可选）
./deploy_to_server.sh
```

### 2. 服务器部署
在服务器上执行以下命令：

```bash
# 进入项目目录
cd /www/wwwroot/huangshi/tools/pig-detector-opencv

# 拉取最新代码
git pull origin main

# 激活虚拟环境
source py-project-env pig-detector-opencv

# 安装/更新依赖
pip install -r requirements.txt

# 停止现有服务
pkill -f 'uvicorn.*api:app' || echo '没有运行的API服务'

# 启动API服务
nohup python -m uvicorn scripts.api:app --host 0.0.0.0 --port 8092 > api.log 2>&1 &

# 检查服务状态
sleep 3
curl -s http://localhost:8092/api/version
```

## 📋 API接口说明

### 服务器地址
- **基础URL**: `http://119.96.28.202:8092`
- **API文档**: `http://119.96.28.202:8092/docs`

### 统一响应格式
所有API接口都返回统一的JSON格式：

```json
{
    "code": 200,           // 状态码：200成功，400客户端错误，500服务器错误
    "msg": "操作成功",      // 消息描述
    "data": {              // 实际数据，失败时为null
        // 具体数据内容
    }
}
```

### 主要接口

#### 1. 预测接口 `/api/predict`
```bash
POST /api/predict
Content-Type: application/json

{
    "image_path": "图片路径或URL",
    "conf": 0.5,        // 置信度阈值 (可选，默认0.5)
    "top_k": 10         // 最大返回结果数 (可选，默认10)
}
```

**成功响应示例:**
```json
{
    "code": 200,
    "msg": "预测成功",
    "data": {
        "type": "pig",
        "detection_summary": {
            "pig": 1,
            "ruler": 0, 
            "scale": 0,
            "total": 1
        },
        "results": [
            {
                "box": [100, 200, 300, 400],
                "score": 0.95,
                "length": 85.2,
                "weight": 45.6
            }
        ],
        "length_cm": 85.2,
        "weight_kg": 45.6,
        "weight_range": [36.5, 54.7],
        "calculation_method": "ruler_30cm",
        "result_image_url": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/2024/01/15/filename_pred_timestamp.jpg"
    }
}
```

**错误响应示例:**
```json
{
    "code": 400,
    "msg": "image_path cannot be empty",
    "data": null
}
```

#### 2. 图片预测接口 `/api/predict_image`
```bash
POST /api/predict_image
Content-Type: application/json

{
    "image_path": "图片路径或URL",
    "conf": 0.5,        // 置信度阈值 (可选)
    "format": "jpeg"    // 返回格式: jpeg 或 png (可选)
}
```
- **成功**: 返回带标注的图片文件
- **失败**: 返回JSON错误信息

#### 3. 版本信息 `/api/version`
```bash
GET /api/version
```

**响应示例:**
```json
{
    "code": 200,
    "msg": "获取版本信息成功",
    "data": {
        "version": "v1.0",
        "trained_at": "2024-01-01"
    }
}
```

#### 4. 根路径 `/`
```bash
GET /
```

**响应示例:**
```json
{
    "code": 200,
    "msg": "服务正常运行",
    "data": {
        "version": "v1.0",
        "trained_at": "2024-01-01"
    }
}
```

## 🧪 测试方法

### 快速测试
```bash
# 运行快速测试
python tests/quick_test.py
```

### 完整测试
```bash
# 测试远程服务器
python tests/test_api_complete.py http://119.96.28.202:8092

# 测试本地服务器
python tests/test_api_complete.py http://localhost:8092
```

### 基础测试
```bash
# 基础连接测试
python tests/test_api.py
```

### 手动测试
```bash
# 测试版本接口
curl http://119.96.28.202:8092/api/version

# 测试预测接口
curl -X POST http://119.96.28.202:8092/api/predict \
  -H "Content-Type: application/json" \
  -d '{"image_path": "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800"}'

# 测试空路径（应该返回错误）
curl -X POST http://119.96.28.202:8092/api/predict \
  -H "Content-Type: application/json" \
  -d '{"image_path": ""}'
```

## 🔧 常见问题

### 1. 服务启动失败
```bash
# 查看错误日志
tail -f /www/wwwroot/huangshi/tools/pig-detector-opencv/api.log

# 检查端口占用
netstat -tlnp | grep 8092

# 重启服务
pkill -f uvicorn
cd /www/wwwroot/huangshi/tools/pig-detector-opencv
source py-project-env pig-detector-opencv
nohup python -m uvicorn scripts.api:app --host 0.0.0.0 --port 8092 > api.log 2>&1 &
```

### 2. 依赖安装问题
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt

# 如果minio安装失败
pip install minio --no-cache-dir
```

### 3. 模型文件问题
```bash
# 检查模型文件
ls -la models/v1_model.pth

# 检查配置文件
cat config.yaml
```

### 4. API响应格式问题
- 所有接口都返回统一的JSON格式：`{code, msg, data}`
- 成功时 `code=200`，失败时 `code=400/500`
- 实际数据在 `data` 字段中，失败时 `data=null`

### 5. 图片存储路径结构
- 识别结果图片按日期分层存储：`huangshi-mini/media/pigdata/pig/年/月/日/filename.jpg`
- 例如：`huangshi-mini/media/pigdata/pig/2024/01/15/pig_pred_1234567890.jpg`
- 自动创建日期目录结构，便于管理和查找

## 📁 项目结构
```
pig-detector-opencv/
├── scripts/
│   ├── api.py              # API服务主文件 ⭐
│   └── predict.py          # 预测核心逻辑
├── tests/                  # 测试脚本目录 ⭐
│   ├── start_api_server.py # 本地启动脚本
│   ├── quick_test.py       # 快速测试
│   ├── test_api_complete.py# 完整测试
│   └── test_api.py         # 基础测试
├── models/
│   └── v1_model.pth        # 训练好的模型
├── config.yaml             # 配置文件
├── requirements.txt        # Python依赖 ⭐
├── deploy_to_server.sh     # 部署脚本
└── API部署说明.md          # 本文档
```

## 🔄 更新流程

1. **本地开发**: 修改代码并测试
   ```bash
   python tests/start_api_server.py  # 启动本地服务
   python tests/quick_test.py        # 测试功能
   ```

2. **提交代码**: 
   ```bash
   git add .
   git commit -m "更新说明"
   git push origin main
   ```

3. **服务器更新**: 
   ```bash
   cd /www/wwwroot/huangshi/tools/pig-detector-opencv
   git pull origin main
   ```

4. **重启服务**: 
   ```bash
   pkill -f uvicorn
   source py-project-env pig-detector-opencv
   nohup python -m uvicorn scripts.api:app --host 0.0.0.0 --port 8092 > api.log 2>&1 &
   ```

5. **验证**: 
   ```bash
   curl http://119.96.28.202:8092/api/version
   python tests/quick_test.py
   ```

## 📞 技术支持

### 检查清单
- [ ] 服务器日志: `tail -f api.log`
- [ ] 网络连接: `curl http://localhost:8092/api/version`
- [ ] 虚拟环境: `source py-project-env pig-detector-opencv`
- [ ] 依赖安装: `pip list | grep -E "(torch|fastapi|minio)"`
- [ ] 模型文件: `ls -la models/v1_model.pth`
- [ ] 配置文件: `cat config.yaml`

### 常用命令
```bash
# 查看服务状态
ps aux | grep uvicorn

# 查看端口占用
netstat -tlnp | grep 8092

# 重启服务
pkill -f uvicorn && nohup python -m uvicorn scripts.api:app --host 0.0.0.0 --port 8092 > api.log 2>&1 &

# 查看实时日志
tail -f /www/wwwroot/huangshi/tools/pig-detector-opencv/api.log
```

## 🎯 API使用示例

### Python客户端示例
```python
import requests

# 预测接口
response = requests.post('http://119.96.28.202:8092/api/predict', json={
    'image_path': 'https://example.com/pig.jpg',
    'conf': 0.5
})

data = response.json()
if data['code'] == 200:
    result = data['data']
    print(f"检测类型: {result['type']}")
    print(f"检测数量: {len(result['results'])}")
else:
    print(f"错误: {data['msg']}")
```

### JavaScript客户端示例
```javascript
fetch('http://119.96.28.202:8092/api/predict', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        image_path: 'https://example.com/pig.jpg',
        conf: 0.5
    })
})
.then(response => response.json())
.then(data => {
    if (data.code === 200) {
        console.log('检测类型:', data.data.type);
        console.log('检测数量:', data.data.results.length);
    } else {
        console.error('错误:', data.msg);
    }
});