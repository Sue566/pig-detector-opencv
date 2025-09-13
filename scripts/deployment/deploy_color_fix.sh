#!/bin/bash

echo "🚀 开始部署颜色修复..."

# 1. 提交代码
echo "📝 提交代码..."
git add .
git commit -m "修复颜色显示问题：确保猪=红色，尺子=蓝色，底座=绿色"
git push origin main

echo "✅ 代码已提交到仓库"

# 2. 服务器部署指令
echo ""
echo "🖥️  请在服务器上执行以下命令："
echo "----------------------------------------"
echo "cd /www/wwwroot/huangshi/tools/pig-detector-opencv"
echo "git pull origin main"
echo "source py-project-env pig-detector-opencv"
echo "pkill -f uvicorn"
echo "nohup python -m uvicorn scripts.api:app --host 0.0.0.0 --port 8092 > api.log 2>&1 &"
echo "----------------------------------------"

# 3. 测试指令
echo ""
echo "🧪 部署完成后，运行以下测试："
echo "python test_color_fix.py"

echo ""
echo "🎨 颜色配置确认："
echo "🔴 猪: RGB(255, 0, 0) - 纯红色"
echo "🔵 尺子: RGB(0, 100, 255) - 蓝色"
echo "🟢 底座: RGB(0, 200, 0) - 绿色"

echo ""
echo "✅ 部署脚本完成！"