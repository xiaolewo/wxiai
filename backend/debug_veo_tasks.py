#!/usr/bin/env python3
"""
查看Veo任务列表 - 检查任务状态
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))

# 设置环境变量
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

# 设置日志级别
logging.basicConfig(level=logging.WARNING)


async def check_veo_tasks():
    """检查现有的Veo任务"""
    try:
        print("🔧 正在导入Veo模块...")
        from open_webui.models.veo import VeoTask
        from open_webui.internal.db import get_db

        print("✅ 模块导入成功")

        # 查询所有任务
        print("🔍 查询所有Veo任务...")

        with get_db() as db:
            tasks = db.query(VeoTask).all()

            if not tasks:
                print("📝 没有找到任何Veo任务")
                return

            print(f"📊 找到 {len(tasks)} 个任务:")
            print("=" * 80)

            for task in tasks:
                print(f"任务ID: {task.id}")
                print(f"用户ID: {task.user_id}")
                print(f"状态: {task.status}")
                print(f"提示词: {task.prompt[:50]}...")
                print(f"模型: {task.model}")
                print(f"创建时间: {task.created_at}")
                print(f"积分消耗: {task.credits_cost}")
                if task.fail_reason:
                    print(f"失败原因: {task.fail_reason}")
                print("-" * 40)

            # 按状态分组统计
            status_count = {}
            for task in tasks:
                status = task.status
                status_count[status] = status_count.get(status, 0) + 1

            print("\n📈 状态统计:")
            for status, count in status_count.items():
                print(f"  {status}: {count} 个任务")

    except Exception as e:
        print(f"❌ 查询过程中发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 开始查看Veo任务列表...")
    print("=" * 60)

    asyncio.run(check_veo_tasks())

    print("=" * 60)
    print("✅ 任务列表查询完成")
