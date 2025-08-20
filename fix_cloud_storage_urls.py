#!/usr/bin/env python3
"""
修复历史记录显示云存储URL的脚本
将现有任务的云存储URL同步到任务表中，让用户在历史记录中看到云存储URL而不是原始第三方URL
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from open_webui.internal.db import get_db
from open_webui.models.midjourney import MJTask
from open_webui.models.dreamwork import DreamWorkTask
from open_webui.models.kling import KlingTask
from open_webui.models.jimeng import JimengTask
from open_webui.models.cloud_storage import GeneratedFile


def sync_midjourney_cloud_urls():
    """同步Midjourney任务的云存储URL"""
    print("\n🖼️ 【MJ修复】同步Midjourney任务的云存储URL...")

    with get_db() as db:
        # 获取所有成功的MJ任务但没有云存储URL的
        tasks = (
            db.query(MJTask)
            .filter(
                MJTask.status == "SUCCESS",
                MJTask.image_url.isnot(None),
                MJTask.cloud_image_url.is_(None),
            )
            .all()
        )

        updated_count = 0
        for task in tasks:
            # 查找对应的云存储文件
            cloud_files = (
                db.query(GeneratedFile)
                .filter(
                    GeneratedFile.source_type == "midjourney",
                    GeneratedFile.source_task_id == task.id,
                    GeneratedFile.status == "uploaded",
                    GeneratedFile.cloud_url.isnot(None),
                )
                .all()
            )

            if cloud_files:
                # 使用第一个成功上传的云存储URL
                cloud_file = cloud_files[0]
                task.cloud_image_url = cloud_file.cloud_url
                updated_count += 1
                print(f"   ✅ 任务 {task.id} 已更新云存储URL")

        db.commit()
        print(f"   📊 总共更新了 {updated_count} 个Midjourney任务")


def sync_dreamwork_cloud_urls():
    """同步DreamWork任务的云存储URL"""
    print("\n🎨 【DW修复】同步DreamWork任务的云存储URL...")

    with get_db() as db:
        tasks = (
            db.query(DreamWorkTask)
            .filter(
                DreamWorkTask.status == "SUCCESS",
                DreamWorkTask.image_url.isnot(None),
                DreamWorkTask.cloud_image_url.is_(None),
            )
            .all()
        )

        updated_count = 0
        for task in tasks:
            cloud_files = (
                db.query(GeneratedFile)
                .filter(
                    GeneratedFile.source_type == "dreamwork",
                    GeneratedFile.source_task_id == task.id,
                    GeneratedFile.status == "uploaded",
                    GeneratedFile.cloud_url.isnot(None),
                )
                .all()
            )

            if cloud_files:
                cloud_file = cloud_files[0]
                task.cloud_image_url = cloud_file.cloud_url
                updated_count += 1
                print(f"   ✅ 任务 {task.id} 已更新云存储URL")

        db.commit()
        print(f"   📊 总共更新了 {updated_count} 个DreamWork任务")


def sync_kling_cloud_urls():
    """同步Kling任务的云存储URL"""
    print("\n🎬 【KL修复】同步Kling任务的云存储URL...")

    with get_db() as db:
        tasks = (
            db.query(KlingTask)
            .filter(
                KlingTask.status == "succeed",
                KlingTask.video_url.isnot(None),
                KlingTask.cloud_video_url.is_(None),
            )
            .all()
        )

        updated_count = 0
        for task in tasks:
            cloud_files = (
                db.query(GeneratedFile)
                .filter(
                    GeneratedFile.source_type == "kling",
                    GeneratedFile.source_task_id == task.id,
                    GeneratedFile.status == "uploaded",
                    GeneratedFile.cloud_url.isnot(None),
                )
                .all()
            )

            if cloud_files:
                cloud_file = cloud_files[0]
                task.cloud_video_url = cloud_file.cloud_url
                updated_count += 1
                print(f"   ✅ 任务 {task.id} 已更新云存储URL")

        db.commit()
        print(f"   📊 总共更新了 {updated_count} 个Kling任务")


def sync_jimeng_cloud_urls():
    """同步Jimeng任务的云存储URL"""
    print("\n🎥 【JM修复】同步Jimeng任务的云存储URL...")

    with get_db() as db:
        tasks = (
            db.query(JimengTask)
            .filter(
                JimengTask.status == "succeed",
                JimengTask.video_url.isnot(None),
                JimengTask.cloud_video_url.is_(None),
            )
            .all()
        )

        updated_count = 0
        for task in tasks:
            cloud_files = (
                db.query(GeneratedFile)
                .filter(
                    GeneratedFile.source_type == "jimeng",
                    GeneratedFile.source_task_id == task.id,
                    GeneratedFile.status == "uploaded",
                    GeneratedFile.cloud_url.isnot(None),
                )
                .all()
            )

            if cloud_files:
                cloud_file = cloud_files[0]
                task.cloud_video_url = cloud_file.cloud_url
                updated_count += 1
                print(f"   ✅ 任务 {task.id} 已更新云存储URL")

        db.commit()
        print(f"   📊 总共更新了 {updated_count} 个Jimeng任务")


def main():
    """主函数"""
    print("🔧 开始修复历史记录云存储URL显示问题...")
    print("=" * 60)

    try:
        sync_midjourney_cloud_urls()
        sync_dreamwork_cloud_urls()
        sync_kling_cloud_urls()
        sync_jimeng_cloud_urls()

        print("\n" + "=" * 60)
        print("✅ 所有任务的云存储URL同步完成！")
        print("📋 现在用户在历史记录中将看到云存储URL而不是原始第三方URL")

    except Exception as e:
        print(f"\n❌ 修复过程中出现错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
