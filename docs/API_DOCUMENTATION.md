# 高级猪检测API文档

## 概述

这是一个基于Flask的高级猪检测API，提供猪的检测、长度测量、重量估算和可视化功能。

## 功能特性

- 🐷 猪的智能检测
- 📏 基于尺子或底座的精确长度测量
- ⚖️ 重量估算（基于长度的经验公式）
- 🎨 高级可视化结果
- 📊 多种API接口满足不同需求

## 安装和启动

### 1. 安装依赖

```bash
pip install flask pillow requests
```

### 2. 启动服务

```bash
python start_advanced_api.py
```

或直接运行：

```bash
python advanced_pig_api.py
```

服务将在 `http://localhost:5000` 启动

## API接口

### 1. 完整检测接口

**接口**: `POST /api/detect_advanced`

**功能**: 执行完整的检测、测量和可视化

**请求参数**:
```json
{
    "image_url": "图片URL地址",
    "labels_data": [
        [class_id, x_center, y_center, width, height],
        ...
    ],
    "return_visualization": true
}
```

**响应格式**:
```json
{
    "success": true,
    "timestamp": "2024-01-01T12:00:00",
    "image_url": "原始图片URL",
    "detections": [
        {
            "class_name": "Pig",
            "class_id": 0,
            "confidence": 0.95,
            "bbox": [x1, y1, x2, y2],
            "width_px": 200,
            "height_px": 300
        }
    ],
    "measurements": {
        "length_cm": 85.5,
        "weight_kg": 45.2,
        "weight_range_kg": [36.2, 54.2],
        "calculation_method": "基于尺子(30cm)"
    },
    "image_info": {
        "width": 1920,
        "height": 1080
    },
    "visualization": {
        "image_base64": "base64编码的可视化图片",
        "filename": "生成的文件名"
    }
}
```

### 2. 可视化图片接口

**接口**: `POST /api/detect_and_visualize`

**功能**: 检测并直接返回可视化图片文件

**请求参数**: 同上

**响应**: 直接返回图片文件（JPEG格式）

### 3. 仅测量接口

**接口**: `POST /api/calculate_measurements`

**功能**: 仅计算测量结果，不返回可视化

**请求参数**: 同上（无需return_visualization参数）

**响应格式**:
```json
{
    "success": true,
    "timestamp": "2024-01-01T12:00:00",
    "measurements": {
        "length_cm": 85.5,
        "weight_kg": 45.2,
        "weight_range_kg": [36.2, 54.2],
        "calculation_method": "基于尺子(30cm)"
    },
    "detections_count": 2,
    "image_info": {
        "width": 1920,
        "height": 1080
    }
}
```

### 4. 健康检查接口

**接口**: `GET /api/health`

**功能**: 检查服务状态

**响应格式**:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00",
    "version": "1.0.0"
}
```

## 类别定义

- `0`: Pig (猪)
- `1`: Ruler (尺子)
- `2`: Base (底座)

## 测量原理

### 长度计算

1. **基于尺子**: 使用30cm标准尺子作为参考
2. **基于底座**: 使用60cm×40cm标准底座作为参考

### 重量估算

使用经验公式：`重量(kg) = 0.002 × 长度(cm)^2.5`

重量范围为估算值的±20%

## 使用示例

### Python示例

```python
import requests
import json

# 测试数据
data = {
    "image_url": "http://example.com/pig_image.jpg",
    "labels_data": [
        [0, 0.574219, 0.504101, 0.232813, 0.518453],  # pig
        [1, 0.398047, 0.518746, 0.086719, 0.562976]   # ruler
    ],
    "return_visualization": True
}

# 发送请求
response = requests.post(
    "http://localhost:5000/api/detect_advanced",
    json=data,
    headers={'Content-Type': 'application/json'}
)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print(f"检测成功！长度: {result['measurements']['length_cm']:.1f}cm")
else:
    print(f"请求失败: {response.text}")
```

### cURL示例

```bash
curl -X POST http://localhost:5000/api/detect_advanced \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "http://example.com/pig_image.jpg",
    "labels_data": [[0, 0.574219, 0.504101, 0.232813, 0.518453]],
    "return_visualization": true
  }'
```

## 测试

运行测试脚本：

```bash
python test_advanced_api.py
```

测试脚本会自动测试所有API接口并保存可视化结果。

## 错误处理

所有接口在出错时返回以下格式：

```json
{
    "success": false,
    "error": "错误描述",
    "traceback": "详细错误信息（仅调试模式）"
}
```

## 注意事项

1. 确保图片URL可访问
2. labels_data使用YOLO格式（归一化坐标）
3. 服务器需要网络访问权限下载图片
4. 临时文件会自动清理
5. 支持本地文件路径和HTTP/HTTPS URL

## 性能优化建议

1. 使用CDN加速图片访问
2. 考虑添加缓存机制
3. 对于大批量处理，建议使用异步接口
4. 生产环境建议使用WSGI服务器（如Gunicorn）

## 扩展功能

可以根据需要扩展以下功能：

- 支持更多参考对象类型
- 改进重量估算算法
- 添加批量处理接口
- 集成数据库存储
- 添加用户认证
- 支持更多图片格式