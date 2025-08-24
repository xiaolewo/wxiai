#!/bin/bash

# Docker环境即梦字段迁移脚本
# 使用方法: ./docker_migrate.sh [容器名称或ID]

set -e

echo "🐳 Docker即梦字段迁移脚本"
echo "================================"

# 检查参数
CONTAINER_NAME=${1}

if [ -z "$CONTAINER_NAME" ]; then
    echo "📋 查找运行中的容器..."
    
    # 尝试常见的容器名称模式
    POSSIBLE_NAMES=("open-webui" "webui" "backend" "wxiai-backend" "app" "webui-backend")
    
    for name in "${POSSIBLE_NAMES[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$name"; then
            CONTAINER_NAME="$name"
            echo "✅ 找到容器: $CONTAINER_NAME"
            break
        fi
    done
    
    if [ -z "$CONTAINER_NAME" ]; then
        echo "❌ 未找到合适的容器，请手动指定:"
        echo "   用法: $0 <容器名称或ID>"
        echo ""
        echo "📋 当前运行的容器:"
        docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}"
        exit 1
    fi
else
    # 验证容器是否存在且运行中
    if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo "❌ 容器 '$CONTAINER_NAME' 未运行或不存在"
        echo ""
        echo "📋 当前运行的容器:"
        docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}"
        exit 1
    fi
    echo "✅ 使用容器: $CONTAINER_NAME"
fi

echo ""
echo "🚀 开始执行迁移..."

# 方法1: 直接在容器中执行迁移脚本
echo "📦 尝试方法1: 执行迁移脚本"
if docker exec "$CONTAINER_NAME" test -f run_jimeng_migration.py; then
    echo "✅ 找到迁移脚本，开始执行..."
    docker exec "$CONTAINER_NAME" python run_jimeng_migration.py
    echo "✅ 迁移脚本执行完成"
else
    echo "⚠️  容器内未找到迁移脚本，尝试方法2..."
    
    # 方法2: 复制脚本到容器并执行
    echo "📦 尝试方法2: 复制并执行迁移脚本"
    
    # 检查本地迁移脚本是否存在
    if [ ! -f "run_jimeng_migration.py" ]; then
        echo "❌ 本地也没有找到迁移脚本文件"
        exit 1
    fi
    
    echo "📋 复制迁移脚本到容器..."
    docker cp run_jimeng_migration.py "$CONTAINER_NAME":/app/
    
    echo "🔧 执行迁移..."
    docker exec "$CONTAINER_NAME" bash -c "cd /app && python run_jimeng_migration.py"
    
    echo "🧹 清理临时文件..."
    docker exec "$CONTAINER_NAME" rm -f /app/run_jimeng_migration.py
fi

echo ""
echo "✅ 迁移执行完成！"
echo ""
echo "🔍 验证建议："
echo "1. 检查容器日志："
echo "   docker logs $CONTAINER_NAME | tail -20"
echo ""
echo "2. 测试即梦功能："
echo "   curl http://your-domain/api/v1/jimeng/config/user"
echo ""
echo "3. 如果遇到问题，可以进入容器调试："
echo "   docker exec -it $CONTAINER_NAME bash"