# PyCharm环境中启动API服务

## 🎯 问题解决

你提到在PyCharm中环境是可以正常使用的，这说明依赖包都已经正确安装。现在MinIO上传功能已经集成到API中。

## 🚀 在PyCharm中启动API

### ⚠️ 重要：环境配置
确保使用正确的conda环境，不要同时激活多个环境：
```bash
conda activate pig-detector-opencv
```

### 方法1: 运行启动脚本（推荐）
1. 在PyCharm中打开 `start_new_api.py`
2. 确保PyCharm使用的是 `pig-detector-opencv` 环境
3. 右键选择 "Run 'start_new_api'"
4. 或者点击绿色运行按钮

### 方法2: 在Terminal中启动
在PyCharm的Terminal中运行:
```bash
# 确保环境正确
conda activate pig-detector-opencv

# 启动API服务
python start_new_api.py
```

### 方法3: 使用uvicorn命令
```bash
conda activate pig-detector-opencv
uvicorn api.endpoints:app --host 0.0.0.0 --port 8092 --reload
```

## 🌐 访问API

启动成功后，访问以下地址:
- **根路径**: http://127.0.0.1:8092/ (自动重定向到文档)
- **API文档**: http://127.0.0.1:8092/docs
- **健康检查**: http://127.0.0.1:8092/api/health

## 🔧 MinIO上传功能

现在API已经集成了真正的MinIO上传功能:

### 主要改进:
1. **真实上传**: 可视化图片会真正上传到MinIO对象存储
2. **正确URL**: 返回新格式的URL
3. **文件组织**: 按日期自动组织文件结构
4. **错误处理**: 上传失败时有备用方案

### URL格式变化:
- **旧格式**: `http://119.96.28.202:8094/api/v1/buckets/huangshi-mini/objects/download?preview=true&prefix=xxx.jpg`
- **新格式**: `http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/detection_results/2025/09/13/xxx.jpg`

### 文件组织结构:
```
huangshi-mini/
└── media/pigdata/pig/
    └── detection_results/
        └── 2025/
            └── 09/
                └── 13/
                    ├── image1_hash1.jpg
                    └── image2_hash2.jpg
```

## 🧪 测试API功能

### 1. 健康检查
```bash
curl -X GET "http://127.0.0.1:8092/api/health"
```

### 2. 检测接口测试
```bash
curl -X POST "http://127.0.0.1:8092/api/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "image_path": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/5ea39c6f3a60e59998a87d2235bb4e6c.jpg",
       "conf": 0.5
     }'
```

### 3. 在API文档中测试
1. 访问 http://127.0.0.1:8092/docs
2. 展开 `/api/predict` 接口
3. 点击 "Try it out"
4. 输入测试数据
5. 点击 "Execute"

## 📋 预期结果

现在API应该返回类似这样的响应，并且 `result_image_url` 指向的文件会真正存在于MinIO中:

```json
{
    "code": 0,
    "data": {
        "detection_summary": {
            "pig": 2,
            "ruler": 0,
            "scale": 0,
            "total": 2
        },
        "measurements": [
            {
                "pig_index": 0,
                "pig_box": [623.24, 234.35, 1003.07, 1339.86],
                "length_cm": 45.2,
                "length_method": "基于尺子(30cm)",
                "estimated_weight_kg": 12.5,
                "weight_range_kg": [10.0, 15.0]
            }
        ],
        "result_image_url": "http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/detection_results/2025/09/13/5ea39c6f3a60e59998a87d2235bb4e6c_abc123.jpg"
    },
    "msg": "success"
}
```

## 🔍 故障排除

如果遇到问题:

1. **检查依赖**: 确保所有包都已安装
2. **检查配置**: 验证 `config.yaml` 中的MinIO配置
3. **检查网络**: 确保能访问MinIO服务器
4. **查看日志**: 观察控制台输出的日志信息

## ✅ 完成状态

- ✅ API结构重组完成
- ✅ URL格式更新完成  
- ✅ MinIO上传功能集成完成 **（测试通过！）**
- ✅ 高级可视化功能集成完成
- ✅ 根路径重定向到文档完成
- ✅ 按日期组织文件结构完成
- ✅ 环境配置验证完成

## 🎉 测试结果确认

根据你的测试反馈，MinIO上传功能已经正常工作：

```
对象路径: media/pigdata/pig/detection_results/2025/09/13/image_3f63fdc4.jpg
结果URL: http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/detection_results/2025/09/13/image_3f63fdc4.jpg
✅ 所有测试通过！MinIO上传功能正常
```

## 🚀 现在可以启动API服务

使用 `(pig-detector-opencv)` 环境启动API服务，测试完整的检测和上传流程！

**重要提醒**：不要同时激活两个conda环境，确保只使用 `pig-detector-opencv` 环境。