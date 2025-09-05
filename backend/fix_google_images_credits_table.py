#!/usr/bin/env python3
"""
修复google_images_credits表结构，添加缺失的列
"""

import sqlite3
import os
import sys
from datetime import datetime


def get_db_connection():
    """获取数据库连接"""
    db_paths = [
        "data/webui.db",
        "backend/data/webui.db",
        "webui.db",
        "backend/webui.db",
    ]
    for path in db_paths:
        if os.path.exists(path):
            return sqlite3.connect(path), path
    return None, None


def fix_google_images_credits_table():
    """修复google_images_credits表结构"""
    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 使用数据库: {db_path}")
    cursor = conn.cursor()

    try:
        print("🔧 修复google_images_credits表结构...")

        # 1. 检查当前表结构
        cursor.execute("PRAGMA table_info(google_images_credits)")
        current_columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"📊 当前表列: {list(current_columns.keys())}")

        # 2. 期望的表结构（基于模型定义）
        expected_columns = {
            "credits_before": "INTEGER",
            "credits_after": "INTEGER",
            "model_name": "VARCHAR(50)",
            "description": "TEXT",
        }

        # 3. 添加缺失的列
        missing_columns = []
        for col_name, col_type in expected_columns.items():
            if col_name not in current_columns:
                missing_columns.append((col_name, col_type))

        if missing_columns:
            print(f"📊 需要添加 {len(missing_columns)} 个缺失的列:")

            for col_name, col_type in missing_columns:
                try:
                    sql = f"ALTER TABLE google_images_credits ADD COLUMN {col_name} {col_type}"
                    cursor.execute(sql)
                    print(f"   ✅ 添加列: {col_name} ({col_type})")

                except Exception as e:
                    print(f"   ❌ 添加列 {col_name} 失败: {e}")
        else:
            print("✅ 所有必要的列都存在")

        # 4. 检查并修复其他积分表（保持一致性）
        print("\n🔧 检查其他积分表结构...")

        # 检查veo_credits表
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='veo_credits'"
        )
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(veo_credits)")
            veo_columns = {row[1]: row[2] for row in cursor.fetchall()}

            for col_name, col_type in expected_columns.items():
                if col_name not in veo_columns:
                    try:
                        sql = (
                            f"ALTER TABLE veo_credits ADD COLUMN {col_name} {col_type}"
                        )
                        cursor.execute(sql)
                        print(f"   ✅ 添加veo_credits列: {col_name}")
                    except Exception as e:
                        print(f"   ❌ 添加veo_credits列 {col_name} 失败: {e}")

        # 检查其他AI服务积分表
        other_credit_tables = [
            "jimeng_credits",
            "comfyui_credits",
            "flux_credits",
            "kling_credits",
            "midjourney_credits",
            "dreamwork_credits",
        ]

        for table_name in other_credit_tables:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if cursor.fetchone():
                cursor.execute(f"PRAGMA table_info({table_name})")
                table_columns = {row[1]: row[2] for row in cursor.fetchall()}

                for col_name, col_type in expected_columns.items():
                    if col_name not in table_columns:
                        try:
                            sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                            cursor.execute(sql)
                            print(f"   ✅ 添加{table_name}列: {col_name}")
                        except Exception as e:
                            print(f"   ❌ 添加{table_name}列 {col_name} 失败: {e}")

        # 5. 提交更改
        conn.commit()

        print("\n✅ google_images_credits表结构修复完成！")

        # 6. 验证修复结果
        print("\n🔍 验证修复结果...")
        cursor.execute("PRAGMA table_info(google_images_credits)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 最终google_images_credits列: {final_columns}")

        return True

    except Exception as e:
        print(f"❌ 修复表结构时发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def test_credit_record_creation():
    """测试积分记录创建"""
    print("\n🔍 测试积分记录创建...")

    try:
        import sys
        import os

        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        from open_webui.models.google_images import GoogleImagesCredit
        import uuid

        user_id = "1e402f55-88cc-4eb9-a364-8b51a441518a"
        task_id = f"test_{uuid.uuid4().hex[:8]}"

        log_data = {
            "user_id": user_id,
            "task_id": task_id,
            "credit_amount": 20,
            "credits_before": 9960,
            "credits_after": 9940,
            "operation_type": "deduct",
            "model_name": "nano-banana",
            "description": "测试积分扣除",
        }

        # 尝试创建积分记录
        credit_log = GoogleImagesCredit.create_credit_log(log_data)

        if credit_log:
            print(f"✅ 积分记录创建成功: ID={credit_log.id}")
            return True
        else:
            print("❌ 积分记录创建失败")
            return False

    except Exception as e:
        print(f"❌ 测试积分记录创建失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 开始修复google_images_credits表结构...")
    print("=" * 60)

    if fix_google_images_credits_table():
        if test_credit_record_creation():
            print("\n🎉 google_images_credits表修复成功！现在应该可以正常扣除积分了")
            print("\n🚀 建议操作：")
            print("1. 重新测试 Google Images 生成功能")
            print("2. 检查积分扣除是否正常")
            print("3. 验证积分记录是否正确创建")
        else:
            print("❌ 表结构修复后仍无法创建积分记录")
    else:
        print("❌ 表结构修复失败")
        sys.exit(1)
