#!/usr/bin/env python3
"""
修复google_images_tasks表结构，添加缺失的列
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


def fix_google_images_tasks_table():
    """修复google_images_tasks表结构"""
    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 使用数据库: {db_path}")
    cursor = conn.cursor()

    try:
        print("🔧 修复google_images_tasks表结构...")

        # 1. 检查当前表结构
        cursor.execute("PRAGMA table_info(google_images_tasks)")
        current_columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"📊 当前表列: {list(current_columns.keys())}")

        # 2. 期望的表结构（基于模型定义）
        expected_columns = {
            "input_images": "JSON",  # 原始输入图片
            "cloud_input_images": "JSON",  # 云端输入图片URL
            "cloud_result_images": "JSON",  # 云端结果图片URL
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
                    sql = f"ALTER TABLE google_images_tasks ADD COLUMN {col_name} {col_type}"
                    cursor.execute(sql)
                    print(f"   ✅ 添加列: {col_name} ({col_type})")

                except Exception as e:
                    print(f"   ❌ 添加列 {col_name} 失败: {e}")
        else:
            print("✅ 所有必要的列都存在")

        # 4. 检查是否需要重命名列（images -> input_images的映射）
        if "images" in current_columns and "input_images" not in current_columns:
            print("🔄 检测到需要数据迁移: images -> input_images")
            # SQLite不支持直接重命名列，我们需要在应用层处理这个映射
            print("   💡 注意：应用将自动处理 images 列到 input_images 的映射")

        # 5. 检查其他AI服务任务表的一致性
        print("\n🔧 检查其他AI服务任务表结构...")

        # 标准化的图片列
        standard_image_columns = {
            "input_images": "JSON",
            "cloud_input_images": "JSON",
            "result_images": "JSON",
            "cloud_result_images": "JSON",
        }

        # 检查其他任务表
        other_task_tables = [
            "veo_tasks",
            "flux_tasks",
            "kling_tasks",
            "jimeng_tasks",
            "mj_tasks",
            "dreamwork_tasks",
        ]

        for table_name in other_task_tables:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if cursor.fetchone():
                cursor.execute(f"PRAGMA table_info({table_name})")
                table_columns = {row[1]: row[2] for row in cursor.fetchall()}

                # 只添加缺失的图片相关列
                for col_name, col_type in standard_image_columns.items():
                    if col_name not in table_columns:
                        try:
                            sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                            cursor.execute(sql)
                            print(f"   ✅ 添加{table_name}列: {col_name}")
                        except Exception as e:
                            # 忽略已存在的错误，某些表可能有不同的命名约定
                            if "duplicate column name" not in str(e).lower():
                                print(f"   ⚠️ 添加{table_name}列 {col_name} 失败: {e}")

        # 6. 提交更改
        conn.commit()

        print("\n✅ google_images_tasks表结构修复完成！")

        # 7. 验证修复结果
        print("\n🔍 验证修复结果...")
        cursor.execute("PRAGMA table_info(google_images_tasks)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 最终google_images_tasks列: {final_columns}")

        return True

    except Exception as e:
        print(f"❌ 修复表结构时发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def test_task_creation():
    """测试任务创建"""
    print("\n🔍 测试Google Images任务创建...")

    try:
        import sys
        import os

        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        from open_webui.models.google_images import GoogleImagesTask
        import uuid

        user_id = "1e402f55-88cc-4eb9-a364-8b51a441518a"
        task_id = str(uuid.uuid4())

        task_data = {
            "id": task_id,
            "user_id": user_id,
            "status": "submitted",
            "prompt": "测试图像生成",
            "model": "nano-banana",
            "size": "1024x1024",
            "quality": "standard",
            "style": "natural",
            "input_images": ["data:image/png;base64,test"],
            "cloud_input_images": ["https://example.com/test.png"],
            "credits_cost": 20,
            "properties": {"test": True},
        }

        # 尝试创建任务记录
        task = GoogleImagesTask.create_task(task_data)

        if task:
            print(f"✅ 任务创建成功: ID={task.id}")
            return True
        else:
            print("❌ 任务创建失败")
            return False

    except Exception as e:
        print(f"❌ 测试任务创建失败: {str(e)}")
        import traceback

        print(f"📊 错误堆栈:\n{traceback.format_exc()}")
        return False


if __name__ == "__main__":
    print("🚀 开始修复google_images_tasks表结构...")
    print("=" * 60)

    if fix_google_images_tasks_table():
        if test_task_creation():
            print("\n🎉 google_images_tasks表修复成功！现在应该可以正常创建任务了")
            print("\n🚀 建议操作：")
            print("1. 重新测试 Google Images 图像生成功能")
            print("2. 检查任务创建和状态更新")
            print("3. 验证图片上传和云存储功能")
        else:
            print("❌ 表结构修复后仍无法创建任务")
    else:
        print("❌ 表结构修复失败")
        sys.exit(1)
