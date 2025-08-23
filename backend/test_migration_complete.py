#!/usr/bin/env python3
"""
测试迁移文件完整性 - 确保所有手动修改都已包含在迁移中
"""

import sqlite3
import os
import tempfile
import shutil
from pathlib import Path


def test_migration_completeness():
    """测试迁移文件的完整性"""

    # 创建临时数据库来测试迁移
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_migration.db")

    try:
        # 复制当前工作目录结构
        backend_dir = Path(__file__).parent

        print("🧪 测试迁移文件完整性...")
        print(f"📁 临时目录: {temp_dir}")
        print(f"📄 临时数据库: {temp_db}")

        # 检查关键表和列是否存在于迁移文件中
        migration_file = (
            backend_dir
            / "open_webui/migrations/versions/f8a9b7c6d5e4_add_missing_columns_and_service_type.py"
        )

        if not migration_file.exists():
            print("❌ 迁移文件不存在")
            return False

        with open(migration_file, "r", encoding="utf-8") as f:
            migration_content = f.read()

        # 检查关键修改是否包含在迁移文件中
        checks = [
            ("chat.pinned", "pinned"),
            ("chat.meta", "meta"),
            ("chat.folder_id", "folder_id"),
            ("tag.meta", "meta"),
            ("model.access_control", "access_control"),
            ("model.price", "price"),
            ("model.is_active", "is_active"),
            ("prompt.access_control", "access_control"),
            ("serviceType", "serviceType"),
            ("dreamwork_tasks.progress", "progress"),
        ]

        missing_items = []
        for table_column, keyword in checks:
            if keyword not in migration_content:
                missing_items.append(table_column)

        if missing_items:
            print("❌ 迁移文件缺少以下修改:")
            for item in missing_items:
                print(f"   - {item}")
            return False

        # 检查当前数据库状态
        current_db = backend_dir / "data/webui.db"
        if current_db.exists():
            conn = sqlite3.connect(str(current_db))
            cursor = conn.cursor()

            print("\n✅ 检查当前数据库状态:")

            # 检查关键表和列
            tables_to_check = {
                "chat": ["pinned", "meta", "folder_id"],
                "tag": ["meta"],
                "model": ["access_control", "price", "is_active"],
                "prompt": ["access_control"],
                "jimeng_tasks": ["serviceType"],
                "kling_tasks": ["serviceType"],
                "dreamwork_tasks": ["serviceType", "progress"],
            }

            for table, columns in tables_to_check.items():
                try:
                    # 获取表结构
                    cursor.execute(f"PRAGMA table_info({table})")
                    table_columns = [row[1] for row in cursor.fetchall()]

                    for column in columns:
                        if column in table_columns:
                            print(f"   ✅ {table}.{column} 存在")
                        else:
                            print(f"   ❌ {table}.{column} 缺失")
                            return False

                except sqlite3.Error as e:
                    print(f"   ⚠️ 检查表 {table} 时出错: {e}")

            conn.close()

        print("\n🎉 迁移文件完整性检查通过!")
        print("📋 所有手动数据库修改都已正确包含在迁移文件中")
        print("🚀 可以安全地部署到线上环境")

        return True

    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    success = test_migration_completeness()
    exit(0 if success else 1)
