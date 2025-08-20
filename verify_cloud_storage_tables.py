#!/usr/bin/env python3
"""
验证云存储相关表是否已创建
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from open_webui.internal.db import get_db
from sqlalchemy import inspect, text


def verify_cloud_storage_tables():
    """验证云存储相关表"""
    print("\n🔍 验证云存储相关表...")
    print("=" * 80)

    with get_db() as db:
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()

        # 需要检查的表
        required_tables = ["cloud_storage_config", "generated_files"]

        print("\n📊 数据库中的所有表:")
        for table in sorted(tables):
            print(f"  - {table}")

        print(f"\n✅ 云存储相关表验证:")
        all_exist = True

        for table_name in required_tables:
            if table_name in tables:
                # 获取表的列信息
                columns = inspector.get_columns(table_name)
                print(f"\n  ✓ {table_name} 表存在 ({len(columns)} 列)")

                # 显示前5个列
                print(f"    列示例:")
                for col in columns[:5]:
                    col_type = str(col["type"])
                    nullable = "NULL" if col["nullable"] else "NOT NULL"
                    print(f"      - {col['name']}: {col_type} {nullable}")

                # 获取记录数
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"    记录数: {count}")
                except Exception as e:
                    print(f"    记录数: 无法获取 ({e})")
            else:
                print(f"\n  ✗ {table_name} 表不存在!")
                all_exist = False

        # 检查索引
        if "generated_files" in tables:
            print("\n📑 generated_files 表的索引:")
            indexes = inspector.get_indexes("generated_files")
            if indexes:
                for idx in indexes:
                    print(f"  - {idx['name']}: {', '.join(idx['column_names'])}")
            else:
                print("  没有找到索引")

        return all_exist


if __name__ == "__main__":
    try:
        all_exist = verify_cloud_storage_tables()

        if all_exist:
            print("\n✅ 所有云存储相关表都已成功创建!")
        else:
            print("\n⚠️ 部分云存储表未创建，请运行数据库迁移:")
            print("  cd backend && alembic upgrade head")
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback

        traceback.print_exc()
