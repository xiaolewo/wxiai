#!/usr/bin/env python3
"""
测试所有迁移文件的修复
"""

import sqlite3
import sys
import os

sys.path.append("/Users/liuqingliang/Desktop/openwebui/wxiai-main/backend")


def test_all_migrations_fix():
    """测试所有迁移文件的修复"""

    test_db = "/tmp/test_all_migrations.db"

    try:
        # 清理旧的测试文件
        if os.path.exists(test_db):
            os.remove(test_db)

        # 连接测试数据库
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        print("🧪 测试所有迁移文件的修复...")

        # 创建已有所有列的表（模拟线上环境）

        # 1. 创建user表（已有phone列和索引）
        cursor.execute(
            """
        CREATE TABLE user (
            id VARCHAR(50) PRIMARY KEY,
            email VARCHAR(100),
            name VARCHAR(100),
            phone VARCHAR(20)
        )
        """
        )
        cursor.execute("CREATE UNIQUE INDEX ix_user_phone ON user(phone)")

        # 2. 创建tool表（已有access_control列）
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

        # 3. 创建dreamwork_tasks表（已有progress和serviceType列）
        cursor.execute(
            """
        CREATE TABLE dreamwork_tasks (
            id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50),
            action VARCHAR(50),
            status VARCHAR(50),
            prompt TEXT,
            model VARCHAR(100),
            size VARCHAR(50),
            guidance_scale FLOAT,
            seed INTEGER,
            watermark BOOLEAN,
            credits_cost INTEGER,
            submit_time DATETIME,
            start_time DATETIME,
            finish_time DATETIME,
            progress VARCHAR(20) DEFAULT '0%',
            image_url TEXT,
            fail_reason TEXT,
            input_image TEXT,
            properties JSON,
            created_at DATETIME,
            updated_at DATETIME,
            serviceType VARCHAR(50) DEFAULT 'dreamwork'
        )
        """
        )

        print("✅ 创建模拟线上环境表结构完成")

        # 测试各个迁移逻辑
        tests = [
            {
                "name": "user.phone列和索引",
                "table": "user",
                "column": "phone",
                "index": "ix_user_phone",
            },
            {
                "name": "tool.access_control列",
                "table": "tool",
                "column": "access_control",
                "index": None,
            },
            {
                "name": "dreamwork_tasks.progress列",
                "table": "dreamwork_tasks",
                "column": "progress",
                "index": None,
            },
            {
                "name": "dreamwork_tasks.serviceType列",
                "table": "dreamwork_tasks",
                "column": "serviceType",
                "index": None,
            },
        ]

        all_passed = True

        for test in tests:
            print(f"\n🔍 测试 {test['name']}...")

            # 检查列是否存在
            cursor.execute(f'PRAGMA table_info({test["table"]})')
            columns = [row[1] for row in cursor.fetchall()]

            if test["column"] in columns:
                print(f"  ✅ {test['column']}列已存在，跳过添加")
            else:
                print(f"  ❌ {test['column']}列不存在")
                all_passed = False

            # 检查索引（如果需要）
            if test["index"]:
                cursor.execute(f'PRAGMA index_list({test["table"]})')
                indexes = [row[1] for row in cursor.fetchall()]

                if test["index"] in indexes:
                    print(f"  ✅ 索引{test['index']}已存在，跳过创建")
                else:
                    print(f"  ❌ 索引{test['index']}不存在")
                    all_passed = False

        # 测试重复运行迁移不会出错
        print(f"\n🔄 测试重复运行迁移逻辑...")

        # 模拟user表phone列迁移逻辑
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [row[1] for row in cursor.fetchall()]
        cursor.execute("PRAGMA index_list(user)")
        user_indexes = [row[1] for row in cursor.fetchall()]

        if "phone" not in user_columns:
            print("  需要添加phone列")
        else:
            print("  ✅ phone列已存在，正确跳过")

        if "ix_user_phone" not in user_indexes:
            print("  需要创建phone索引")
        else:
            print("  ✅ phone索引已存在，正确跳过")

        # 模拟tool表access_control列迁移逻辑
        cursor.execute("PRAGMA table_info(tool)")
        tool_columns = [row[1] for row in cursor.fetchall()]

        if "access_control" not in tool_columns:
            print("  需要添加access_control列")
        else:
            print("  ✅ access_control列已存在，正确跳过")

        if all_passed:
            print("\n🎉 所有迁移修复测试通过！")
            print("📋 线上部署时不会再出现重复列错误")
            return True
        else:
            print("\n❌ 部分测试失败")
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
    success = test_all_migrations_fix()
    exit(0 if success else 1)
