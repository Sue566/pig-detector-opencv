# 高级猪检测API集成部署说明

## 概述

已成功将高级检测和可视化功能集成到现有的FastAPI系统中，新增了 `/api/predict_advanced` 接口，提供精确的长度测量、重量估算和高级可视化功能。

## 新增功能

### 1. 高级检测接口 `/api/predict_advanced`

**功能特性**:
- 🐷 智能检测猪、尺子、底座
- 📏 基于尺子(30cm)或底座(60×40cm)的精确长度测量
- ⚖️ 重量估算和范围计算
- 🎨 高级可视化标注（红色猪框、蓝色尺子框、绿色底座框）
- 📊 详细的测量信息显示

**请求格式**:
```json
{
    "image_path": "图片URL或路径",
    "conf": 0.5,
    "top_k": 10,
    "return_visualization": true,
    "ruler_length_cm": 30.0,
    "base_length_cm": 60.0,
    "base_width_cm": 40.0
}
```

**响应格式**:
```json
{
    "code": 200,
    "msg": "高级检测成功",
    "data": {
        "type": "advanced_detection",
        "detections": [
            {
                "class_id": 0,
                "confidence": 0.95,
                "box": [x1, y1, x2, y2],
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
        "result_image_url": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/2024/01/15/advanced_detection_20240115_143022.jpg"
    }
}
```

## 集成的核心功能

### 1. 精确长度计算
- **基于尺子**: 使用30cm标准尺子作为参考物
- **基于底座**: 使用60cm×40cm标准底座作为参考物
- **智能选择**: 优先使用尺子，其次使用底座

### 2. 改进的重量估算
- 使用经验公式：`重量(kg) = 0.002 × 长度(cm)^2.5`
- 提供重量范围（±20%）
- 更准确的估算结果

### 3. 高级可视化
- **颜色区分**: 红色(猪)、蓝色(尺子)、绿色(底座)
- **详细标注**: 在猪的检测框上显示长度、重量、计算方法
- **多行信息**: 清晰展示所有测量数据

### 4. 兼容性保证
- 保持原有API接口不变
- 统一的响应格式
- 相同的错误处理机制

## 部署步骤

### 1. 代码集成验证
```bash
# 本地测试
python test_advanced_integration.py
```

### 2. 提交代码
```bash
git add .
git commit -m "集成高级检测API：精确测量、重量估算、高级可视化"
git push origin main
```

### 3. 服务器部署
```bash
# 在服务器上执行
cd /www/wwwroot/huangshi/tools/pig-detector-opencv

# 拉取最新代码
git pull origin main

# 激活虚拟环境
source py-project-env pig-detector-opencv

# 安装新依赖
pip install pillow

# 停止现有服务
pkill -f uvicorn

# 启动新服务
nohup python -m uvicorn scripts.api:app --host 0.0.0.0 --port 8092 > api.log 2>&1 &
```

### 4. 验证部署
```bash
# 检查服务状态
ps aux | grep uvicorn

# 查看日志
tail -f api.log

# 测试API
curl http://119.96.28.202:8092/
curl http://119.96.28.202:8092/api/version
```

## 测试验证

### 1. 健康检查
```bash
curl http://119.96.28.202:8092/
curl http://119.96.28.202:8092/api/version
```

### 2. 原有API测试
```bash
curl -X POST http://119.96.28.202:8092/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/test.jpg",
    "conf": 0.5
  }'
```

### 3. 高级API测试
```bash
curl -X POST http://119.96.28.202:8092/api/predict_advanced \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/test.jpg",
    "return_visualization": true,
    "ruler_length_cm": 30.0
  }'
```

### 4. 完整测试
```bash
python test_advanced_integration.py
```

## 功能对比

| 功能 | 原有API (`/api/predict`) | 高级API (`/api/predict_advanced`) |
|------|-------------------------|-----------------------------------|
| 基础检测 | ✅ | ✅ |
| 长度测量 | ✅ 基础计算 | ✅ 精确测量（尺子/底座） |
| 重量估算 | ✅ 简单估算 | ✅ 改进算法+范围 |
| 可视化 | ✅ 基础标注 | ✅ 高级标注+测量信息 |
| 检测对象 | 猪 | 猪+尺子+底座 |
| 颜色区分 | 单一颜色 | 红色(猪)+蓝色(尺子)+绿色(底座) |
| 测量方法 | 固定算法 | 智能选择最佳参考物 |
| 详细信息 | 基础信息 | 完整测量报告 |

## 使用建议

### 1. 选择合适的接口
- **普通检测**: 使用 `/api/predict` - 快速、简单
- **高级检测**: 使用 `/api/predict_advanced` - 精确、详细

### 2. 图片要求
- 包含清晰的猪的图像
- 最好包含尺子或底座作为参考
- 图片质量良好，光线充足

### 3. 参数调整
- `ruler_length_cm`: 根据实际尺子长度调整
- `base_length_cm`, `base_width_cm`: 根据实际底座尺寸调整
- `conf`: 检测置信度阈值
- `return_visualization`: 是否需要可视化图片

## 技术实现

### 1. 核心算法
- **长度计算**: 基于像素比例和参考物体尺寸
- **重量估算**: 经验公式 `重量 = 0.002 × 长度^2.5`
- **智能选择**: 优先使用尺子，其次使用底座

### 2. 可视化增强
- 不同类别使用不同颜色边框
- 猪的标注包含完整测量信息
- 多行文本显示，信息丰富

### 3. 兼容性保证
- 保持原有API接口不变
- 统一的响应格式
- 相同的错误处理机制

## 监控和维护

### 1. 日志监控
```bash
# 查看API日志
tail -f api.log

# 查看错误日志
grep "ERROR" api.log
```

### 2. 性能监控
- 检测响应时间
- 可视化生成时间
- 内存使用情况

### 3. 定期维护
- 清理临时文件
- 更新模型权重
- 优化算法参数

## 故障排除

### 1. 常见问题
- **字体加载失败**: 检查系统字体路径
- **图片下载失败**: 检查网络连接和URL
- **可视化生成失败**: 检查输出目录权限

### 2. 解决方案
```bash
# 检查字体
ls /usr/share/fonts/truetype/dejavu/
ls /System/Library/Fonts/

# 检查Minio配置
cat config.yaml | grep -A 10 minio

# 重启服务
pkill -f uvicorn
nohup python -m uvicorn scripts.api:app --host 0.0.0.0 --port 8092 > api.log 2>&1 &
```

## 总结

高级检测API已成功集成到现有系统中，提供了：

✅ **更精确的测量**: 基于尺子和底座的智能测量  
✅ **更丰富的可视化**: 颜色区分和详细标注  
✅ **更详细的结果**: 完整的测量报告  
✅ **完全兼容**: 不影响现有API功能  
✅ **易于使用**: 统一的接口格式  

新接口与原有系统完全兼容，可以根据需要选择使用不同的检测接口。建议在需要精确测量和详细可视化的场景下使用高级API。