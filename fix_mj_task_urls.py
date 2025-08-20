#!/usr/bin/env python3
"""
修复Midjourney任务的图片URL，将外部URL替换为云存储URL
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from open_webui.internal.db import get_db
from sqlalchemy import text


def fix_mj_task_urls():
    """修复MJ任务URL"""
    print("\n🔧 修复Midjourney任务URL...")
    print("=" * 80)

    with get_db() as db:
        # 查询需要修复的任务
        result = db.execute(
            text(
                """
            SELECT DISTINCT 
                mt.id as task_id,
                mt.image_url as old_url,
                gf.cloud_url as new_url
            FROM mj_tasks mt
            INNER JOIN generated_files gf ON gf.source_task_id = mt.id
            WHERE gf.source_type = 'midjourney'
                AND gf.status = 'uploaded'
                AND gf.cloud_url IS NOT NULL
                AND (mt.image_url NOT LIKE '%myqcloud.com%' OR mt.image_url IS NULL)
            ORDER BY mt.created_at DESC
        """
            )
        )

        tasks_to_fix = result.fetchall()

        if not tasks_to_fix:
            print("✅ 所有任务URL都已经是云存储URL，无需修复")
            return

        print(f"\n找到 {len(tasks_to_fix)} 个需要修复的任务:")

        fixed_count = 0
        for task in tasks_to_fix:
            task_id, old_url, new_url = task
            print(f"\n  任务ID: {task_id}")
            print(f"    旧URL: {old_url[:80] if old_url else '无'}...")
            print(f"    新URL: {new_url[:80]}...")

            # 更新URL
            try:
                db.execute(
                    text(
                        """
                    UPDATE mj_tasks 
                    SET image_url = :new_url,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :task_id
                """
                    ),
                    {"new_url": new_url, "task_id": task_id},
                )

                fixed_count += 1
                print(f"    ✅ 已更新")
            except Exception as e:
                print(f"    ❌ 更新失败: {e}")

        # 提交事务
        db.commit()

        print(f"\n✅ 修复完成！共更新 {fixed_count} 个任务的URL")

        # 验证修复结果
        print("\n验证修复结果...")
        result = db.execute(
            text(
                """
            SELECT COUNT(*) 
            FROM mj_tasks 
            WHERE image_url LIKE '%myqcloud.com%'
        """
            )
        )
        cloud_count = result.scalar()

        result = db.execute(
            text(
                """
            SELECT COUNT(*) 
            FROM mj_tasks 
            WHERE image_url NOT LIKE '%myqcloud.com%' 
                AND image_url IS NOT NULL
        """
            )
        )
        external_count = result.scalar()

        print(f"  云存储URL任务数: {cloud_count}")
        print(f"  外部URL任务数: {external_count}")


if __name__ == "__main__":
    try:
        fix_mj_task_urls()
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback

        traceback.print_exc()
