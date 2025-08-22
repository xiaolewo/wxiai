#!/usr/bin/env python3
"""
修复inpainting表结构，添加缺失的字段
"""

import sqlite3
import os

# Database path
db_path = "/Users/liuqingliang/Desktop/wxiai/wxiai-main/backend/data/webui.db"


def fix_inpainting_table():
    """修复inpainting_tasks表结构"""

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔧 修复 inpainting_tasks 表结构...")

        # 需要添加的缺失字段
        missing_columns = [
            ("task_id", "TEXT", "外部任务ID"),
            ("uploaded_input_url", "TEXT", "上传的输入图片云存储URL"),
            ("uploaded_mask_url", "TEXT", "上传的Mask图片云存储URL"),
            ("result_image_url", "TEXT", "结果图片URL"),
            ("cloud_result_url", "TEXT", "云存储结果图片URL"),
            ("seed", "INTEGER DEFAULT 0", "随机种子"),
            ("request_data", "TEXT", "请求数据JSON"),
            ("response_data", "TEXT", "响应数据JSON"),
        ]

        # 检查每个字段是否存在，如果不存在则添加
        for column_name, column_type, description in missing_columns:
            try:
                # 尝试添加字段
                sql = f"ALTER TABLE inpainting_tasks ADD COLUMN {column_name} {column_type}"
                cursor.execute(sql)
                print(f"  ✅ 添加字段: {column_name} ({description})")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"  ⏭️  字段已存在: {column_name}")
                else:
                    print(f"  ❌ 添加字段失败 {column_name}: {e}")

        # 重命名字段：output_image_url -> result_image_url (如果需要)
        try:
            # 检查是否有 output_image_url 字段
            cursor.execute("PRAGMA table_info(inpainting_tasks)")
            columns = [col[1] for col in cursor.fetchall()]

            if "output_image_url" in columns and "result_image_url" not in columns:
                print("  🔄 重命名字段: output_image_url -> result_image_url")
                # SQLite 不支持直接重命名字段，需要通过更新来实现
                cursor.execute(
                    "ALTER TABLE inpainting_tasks ADD COLUMN result_image_url TEXT"
                )
                cursor.execute(
                    "UPDATE inpainting_tasks SET result_image_url = output_image_url"
                )
                print("  ✅ 字段数据已迁移")

            if "cloud_image_url" in columns and "cloud_result_url" not in columns:
                print("  🔄 重命名字段: cloud_image_url -> cloud_result_url")
                cursor.execute(
                    "ALTER TABLE inpainting_tasks ADD COLUMN cloud_result_url TEXT"
                )
                cursor.execute(
                    "UPDATE inpainting_tasks SET cloud_result_url = cloud_image_url"
                )
                print("  ✅ 字段数据已迁移")

        except Exception as e:
            print(f"  ⚠️  字段重命名操作: {e}")

        conn.commit()

        print("\n📋 验证表结构...")
        cursor.execute("PRAGMA table_info(inpainting_tasks)")
        columns = cursor.fetchall()

        print("当前表字段:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        conn.close()
        print("\n✅ inpainting_tasks 表结构修复完成!")
        return True

    except Exception as e:
        print(f"❌ Error fixing table: {e}")
        return False


if __name__ == "__main__":
    success = fix_inpainting_table()
    if success:
        print("\n🎨 现在可以正常使用图像编辑功能了!")
    else:
        print("\n❌ 表结构修复失败")
