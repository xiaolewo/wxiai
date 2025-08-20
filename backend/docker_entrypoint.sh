#!/bin/bash

# Docker容器入口点脚本
# 确保数据库表完整性，然后启动应用

set -e

echo "🚀 Docker容器启动中..."

# 1. 修复数据库表结构
echo "🔧 检查并修复数据库表结构..."
python fix_database_tables.py

if [ $? -eq 0 ]; then
    echo "✅ 数据库表检查完成"
else
    echo "❌ 数据库表修复失败，继续启动..."
fi

# 2. 运行数据库迁移
echo "🔄 运行数据库迁移..."
python -c "
try:
    from open_webui.env import run_migrations
    run_migrations()
    print('✅ 数据库迁移完成')
except Exception as e:
    print(f'⚠️ 数据库迁移警告: {e}')
"

# 3. 启动应用
echo "🌟 启动Open WebUI应用..."
exec "$@"