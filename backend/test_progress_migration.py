#!/usr/bin/env python3
"""
测试progress列迁移
"""

import sqlite3
import sys
import os

sys.path.append("/Users/liuqingliang/Desktop/openwebui/wxiai-main/backend")


def test_progress_migration():
    """测试progress列迁移逻辑"""

    test_db = "/tmp/test_dreamwork.db"

    try:
        # 连接测试数据库
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        print("🧪 测试progress列迁移...")

        # 检查初始状态
        cursor.execute("PRAGMA table_info(dreamwork_tasks)")
        columns_before = [row[1] for row in cursor.fetchall()]
        print(f"迁移前的列: {columns_before}")
        print(f"progress列存在: {'progress' in columns_before}")

        # 模拟迁移逻辑
        if "progress" not in columns_before:
            print("📝 添加progress列...")
            cursor.execute(
                'ALTER TABLE dreamwork_tasks ADD COLUMN progress VARCHAR(20) DEFAULT "0%"'
            )

            # 为现有记录设置默认值
            cursor.execute(
                "UPDATE dreamwork_tasks SET progress = '0%' WHERE progress IS NULL"
            )

            conn.commit()
            print("✅ progress列添加成功")

        # 检查迁移后状态
        cursor.execute("PRAGMA table_info(dreamwork_tasks)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"迁移后的列: {columns_after}")
        print(f"progress列存在: {'progress' in columns_after}")

        # 测试插入记录
        test_data = (
            "test-task-1",
            "test-user-1",
            "TEXT_TO_IMAGE",
            "SUBMITTED",
            "test prompt",
            "test-model",
            "1024x1024",
            2.5,
            None,
            1,
            10,
            "2025-08-18 17:30:00",
            None,
            None,
            "0%",  # progress
            None,
            None,
            None,
            "{}",
            "2025-08-18 17:30:00",
            "2025-08-18 17:30:00",
            "dreamwork",
        )

        cursor.execute(
            """
            INSERT INTO dreamwork_tasks 
            (id, user_id, action, status, prompt, model, size, guidance_scale, seed, watermark, 
             credits_cost, submit_time, start_time, finish_time, progress, image_url, fail_reason, 
             input_image, properties, created_at, updated_at, serviceType)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            test_data,
        )

        conn.commit()
        print("✅ 测试记录插入成功")

        # 查询验证
        cursor.execute(
            "SELECT id, progress FROM dreamwork_tasks WHERE id = ?", ("test-task-1",)
        )
        result = cursor.fetchone()
        print(f"查询结果: {result}")

        if result and result[1] == "0%":
            print("🎉 迁移测试成功！")
            return True
        else:
            print("❌ 迁移测试失败")
            return False

    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if "conn" in locals():
            conn.close()
        # 清理测试文件
        if os.path.exists(test_db):
            os.remove(test_db)


if __name__ == "__main__":
    success = test_progress_migration()
    exit(0 if success else 1)
