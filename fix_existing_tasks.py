#!/usr/bin/env python3
"""
修复已有任务的URL，将外部URL更新为云存储URL
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from open_webui.internal.db import get_db
from open_webui.models.midjourney import MJTask
from open_webui.models.dreamwork import DreamWorkTask
from open_webui.models.kling import KlingTask
from open_webui.models.jimeng import JimengTask
from open_webui.models.cloud_storage import GeneratedFile


def fix_existing_tasks():
    """修复已有任务的URL"""
    print("\n🔧 开始修复已有任务的URL...")
    print("-" * 80)

    fixed_count = 0

    with get_db() as db:
        # 修复Midjourney任务
        print("\n📷 修复Midjourney任务...")
        mj_tasks = db.query(MJTask).filter(MJTask.status == "SUCCESS").all()

        for task in mj_tasks:
            if task.image_url and "myqcloud.com" not in task.image_url:
                # 查找对应的云存储文件记录
                file_record = (
                    db.query(GeneratedFile)
                    .filter(
                        GeneratedFile.source_type == "midjourney",
                        GeneratedFile.source_task_id == task.id,
                        GeneratedFile.status == "uploaded",
                    )
                    .first()
                )

                if file_record and file_record.cloud_url:
                    print(
                        f"  修复任务 {task.id}: {task.image_url[:50]}... -> {file_record.cloud_url[:50]}..."
                    )
                    task.image_url = file_record.cloud_url
                    fixed_count += 1

        # 修复DreamWork任务
        print("\n🎨 修复DreamWork任务...")
        dw_tasks = (
            db.query(DreamWorkTask).filter(DreamWorkTask.status == "SUCCESS").all()
        )

        for task in dw_tasks:
            if task.image_url and "myqcloud.com" not in task.image_url:
                file_record = (
                    db.query(GeneratedFile)
                    .filter(
                        GeneratedFile.source_type == "dreamwork",
                        GeneratedFile.source_task_id == task.id,
                        GeneratedFile.status == "uploaded",
                    )
                    .first()
                )

                if file_record and file_record.cloud_url:
                    print(
                        f"  修复任务 {task.id}: {task.image_url[:50]}... -> {file_record.cloud_url[:50]}..."
                    )
                    task.image_url = file_record.cloud_url
                    fixed_count += 1

        # 修复可灵视频任务
        print("\n🎬 修复可灵视频任务...")
        kling_tasks = db.query(KlingTask).filter(KlingTask.status == "succeed").all()

        for task in kling_tasks:
            if task.video_url and "myqcloud.com" not in task.video_url:
                file_record = (
                    db.query(GeneratedFile)
                    .filter(
                        GeneratedFile.source_type == "kling",
                        GeneratedFile.source_task_id == task.id,
                        GeneratedFile.status == "uploaded",
                    )
                    .first()
                )

                if file_record and file_record.cloud_url:
                    print(
                        f"  修复任务 {task.id}: {task.video_url[:50]}... -> {file_record.cloud_url[:50]}..."
                    )
                    task.video_url = file_record.cloud_url
                    fixed_count += 1

        # 修复即梦视频任务
        print("\n🎥 修复即梦视频任务...")
        jimeng_tasks = db.query(JimengTask).filter(JimengTask.status == "succeed").all()

        for task in jimeng_tasks:
            if task.video_url and "myqcloud.com" not in task.video_url:
                file_record = (
                    db.query(GeneratedFile)
                    .filter(
                        GeneratedFile.source_type == "jimeng",
                        GeneratedFile.source_task_id == task.id,
                        GeneratedFile.status == "uploaded",
                    )
                    .first()
                )

                if file_record and file_record.cloud_url:
                    print(
                        f"  修复任务 {task.id}: {task.video_url[:50]}... -> {file_record.cloud_url[:50]}..."
                    )
                    task.video_url = file_record.cloud_url
                    fixed_count += 1

        # 提交所有更改
        if fixed_count > 0:
            db.commit()
            print(f"\n✅ 成功修复 {fixed_count} 个任务的URL")
        else:
            print("\n✅ 没有需要修复的任务")

    return fixed_count


if __name__ == "__main__":
    try:
        fixed = fix_existing_tasks()

        if fixed > 0:
            print("\n💡 建议重启后端服务以确保修改生效")
            print("   运行: supervisorctl restart all 或重启Docker容器")
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback

        traceback.print_exc()
