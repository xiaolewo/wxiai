#!/usr/bin/env python3
"""
检查最近的Midjourney任务
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from open_webui.internal.db import get_db
from open_webui.models.midjourney import MJTask
from open_webui.models.cloud_storage import GeneratedFile
from datetime import datetime, timedelta


def check_recent_tasks():
    """检查最近的Midjourney任务"""
    print("\n🎨 检查最近的Midjourney任务...")
    print("-" * 80)

    with get_db() as db:
        # 获取最近24小时的任务
        recent_time = datetime.now() - timedelta(hours=24)
        recent_tasks = (
            db.query(MJTask)
            .filter(MJTask.status == "SUCCESS")
            .order_by(MJTask.submit_time.desc())
            .limit(5)
            .all()
        )

        if not recent_tasks:
            print("❌ 最近没有成功的Midjourney任务")
            return

        print(f"📋 找到 {len(recent_tasks)} 个成功的任务:\n")

        for i, task in enumerate(recent_tasks, 1):
            print(f"{i}. 任务ID: {task.id}")
            print(f"   提示词: {task.prompt[:50]}...")
            print(f"   状态: {task.status}")
            print(f"   提交时间: {task.submit_time}")

            # 检查image_url
            if task.image_url:
                print(f"   图片URL: {task.image_url[:100]}...")

                # 判断是否是云存储URL
                if "myqcloud.com" in task.image_url:
                    print(f"   ✅ 已更新为云存储URL")
                else:
                    print(f"   ⚠️ 仍是外部URL")

                # 检查对应的generated_files记录
                file_record = (
                    db.query(GeneratedFile)
                    .filter(
                        GeneratedFile.source_type == "midjourney",
                        GeneratedFile.source_task_id == task.id,
                    )
                    .first()
                )

                if file_record:
                    print(f"   📁 文件记录:")
                    print(f"      - 状态: {file_record.status}")
                    print(
                        f"      - 云存储URL: {file_record.cloud_url[:100] if file_record.cloud_url else 'None'}..."
                    )

                    if file_record.status == "uploaded" and file_record.cloud_url:
                        if task.image_url != file_record.cloud_url:
                            print(f"   ❌ 任务URL未同步更新！")
                            print(f"      建议：任务应该使用云存储URL")
                else:
                    print(f"   ⚠️ 没有找到文件上传记录")
            else:
                print(f"   ❌ 没有图片URL")

            print()


if __name__ == "__main__":
    try:
        check_recent_tasks()
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback

        traceback.print_exc()
