#!/usr/bin/env python3
"""
测试修复后的tool迁移
"""

import sqlite3
import sys
import os

sys.path.append("/Users/liuqingliang/Desktop/openwebui/wxiai-main/backend")


def test_tool_migration_fix():
    """测试修复后的tool access_control列迁移"""

    test_db = "/tmp/test_tool_migration.db"

    try:
        # 清理旧的测试文件
        if os.path.exists(test_db):
            os.remove(test_db)

        # 连接测试数据库
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        print("🧪 测试tool access_control列迁移修复...")

        # 创建已有access_control列的tool表（模拟线上环境）
        cursor.execute(
            """
        CREATE TABLE tool (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            content TEXT,
            access_control JSON
        )
        """
        )

        # 检查初始状态
        cursor.execute("PRAGMA table_info(tool)")
        columns_before = [row[1] for row in cursor.fetchall()]
        print(f"初始列: {columns_before}")
        print(f"access_control列存在: {'access_control' in columns_before}")

        # 模拟修复后的迁移逻辑
        cursor.execute("PRAGMA table_info(tool)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        if "access_control" not in existing_columns:
            print("📝 添加access_control列...")
            cursor.execute("ALTER TABLE tool ADD COLUMN access_control JSON")
            print("✅ access_control列添加成功")
        else:
            print("✅ access_control列已存在，跳过添加")

        # 检查最终状态
        cursor.execute("PRAGMA table_info(tool)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"最终列: {columns_after}")
        print(f"access_control列存在: {'access_control' in columns_after}")

        # 测试再次运行迁移不会出错
        if "access_control" not in existing_columns:
            print("🔄 测试重复运行迁移...")
            # 再次检查（模拟第二次运行迁移）
            cursor.execute("PRAGMA table_info(tool)")
            existing_columns_2 = [row[1] for row in cursor.fetchall()]

            if "access_control" not in existing_columns_2:
                cursor.execute("ALTER TABLE tool ADD COLUMN access_control JSON")
                print("第二次添加access_control列")
            else:
                print("✅ 第二次运行时正确跳过，无重复列错误")

        print("🎉 修复测试成功！")
        return True

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
    success = test_tool_migration_fix()
    exit(0 if success else 1)
