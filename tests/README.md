# 测试脚本说明

## 📁 文件说明

### 🚀 启动脚本
- **start_api_server.py**: 本地启动API服务器
  ```bash
  cd tests
  python start_api_server.py
  ```

### 🧪 测试脚本
- **quick_test.py**: 快速API接口测试
  ```bash
  python tests/quick_test.py
  ```

- **test_api_complete.py**: 完整API功能测试
  ```bash
  python tests/test_api_complete.py
  ```

- **test_api.py**: 基础API连接测试
  ```bash
  python tests/test_api.py
  ```

- **test_minio_url.py**: 测试Minio URL格式和可访问性
  ```bash
  python tests/test_minio_url.py
  ```

- **test_date_structure.py**: 测试日期目录结构
  ```bash
  python tests/test_date_structure.py
  ```

## 🔧 使用方法

### 1. 启动本地服务器
```bash
# 在项目根目录执行
python tests/start_api_server.py
```

### 2. 测试远程服务器
```bash
# 快速测试
python tests/quick_test.py

# 完整测试
python tests/test_api_complete.py http://119.96.28.202:8092

# Minio URL测试
python tests/test_minio_url.py
```

### 3. 测试本地服务器
```bash
# 先启动本地服务器，然后在另一个终端测试
python tests/test_api_complete.py http://localhost:8092
```

## 📋 测试内容

### quick_test.py
- ✅ 版本接口测试
- ✅ 空路径错误处理
- ✅ 示例图片URL预测

### test_api_complete.py  
- ✅ 根路径测试
- ✅ 版本接口测试
- ✅ 错误处理测试
- ✅ 图片预测测试
- ✅ 本地图片测试

### test_api.py
- ✅ 基础连接测试
- ✅ 简单预测测试

### test_minio_url.py
- ✅ Minio URL格式验证
- ✅ 图片URL可访问性测试
- ✅ URL格式正确性检查

### test_date_structure.py
- ✅ 日期目录结构验证 (YYYY/MM/DD)
- ✅ 文件路径格式检查
- ✅ 多次请求日期一致性测试

## 🎯 测试流程建议

1. **开发阶段**: 使用 `quick_test.py` 快速验证功能
2. **部署前**: 运行 `test_api_complete.py` 全面测试
3. **部署后**: 使用 `test_minio_url.py` 验证图片上传和URL生成
4. **问题排查**: 使用 `test_api.py` 进行基础连接测试