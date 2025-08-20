#!/bin/bash
set -e

echo "🔧 Installing additional dependencies..."

# 安装腾讯云COS SDK（如果未安装）
if ! python -c "import cos_python_sdk_v5" 2>/dev/null; then
    echo "📦 Installing Tencent Cloud COS SDK..."
    pip install cos-python-sdk-v5==1.9.30
    echo "✅ COS SDK installed successfully"
else
    echo "✅ COS SDK already installed"
fi

echo "🚀 Starting Open WebUI..."

# 启动原始命令
exec "$@"