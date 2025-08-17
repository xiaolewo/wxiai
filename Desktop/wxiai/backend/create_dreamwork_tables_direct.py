#!/usr/bin/env python3
"""
直接创建DreamWork数据库表的脚本
"""

import sys
import os
import sqlite3
from datetime import datetime

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def create_dreamwork_tables():
    """直接使用SQL创建DreamWork表"""

    # 数据库路径 - 通常在 ./webui.db
    db_path = os.path.join(os.path.dirname(__file__), "..", "webui.db")
    if not os.path.exists(db_path):
        # 如果不存在，尝试其他常见路径
        alt_paths = ["webui.db", "../webui.db", "./data/webui.db", "../data/webui.db"]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                db_path = alt_path
                break
        else:
            print(f"错误：找不到数据库文件。尝试的路径:")
            print(f"  - {db_path}")
            for alt_path in alt_paths:
                print(f"  - {alt_path}")
            return False

    print(f"使用数据库: {db_path}")

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表是否已存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='dreamwork_config'"
        )
        if cursor.fetchone():
            print("DreamWork表已存在，跳过创建")
            return True

        print("开始创建DreamWork表...")

        # 创建 dreamwork_config 表
        cursor.execute(
            """
            CREATE TABLE dreamwork_config (
                id INTEGER PRIMARY KEY,
                enabled BOOLEAN DEFAULT 0,
                base_url VARCHAR(500),
                api_key TEXT,
                text_to_image_model VARCHAR(100) DEFAULT 'doubao-seedream-3-0-t2i-250415',
                image_to_image_model VARCHAR(100) DEFAULT 'doubao-seededit-3-0-i2i-250628',
                default_size VARCHAR(20) DEFAULT '1024x1024',
                default_guidance_scale REAL DEFAULT 2.5,
                watermark_enabled BOOLEAN DEFAULT 1,
                credits_per_generation INTEGER DEFAULT 10,
                max_concurrent_tasks INTEGER DEFAULT 5,
                task_timeout INTEGER DEFAULT 300000,
                created_at DATETIME,
                updated_at DATETIME
            )
        """
        )
        print("✓ dreamwork_config 表创建成功")

        # 创建 dreamwork_tasks 表
        cursor.execute(
            """
            CREATE TABLE dreamwork_tasks (
                id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(50),
                action VARCHAR(50),
                status VARCHAR(50) DEFAULT 'SUBMITTED',
                prompt TEXT,
                model VARCHAR(100),
                size VARCHAR(20),
                guidance_scale REAL,
                seed INTEGER,
                watermark BOOLEAN DEFAULT 1,
                image_base64 TEXT,
                credits_cost INTEGER DEFAULT 0,
                submit_time DATETIME,
                start_time DATETIME,
                finish_time DATETIME,
                image_url TEXT,
                image_data TEXT,
                fail_reason TEXT,
                request_data TEXT,
                response_data TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        """
        )
        print("✓ dreamwork_tasks 表创建成功")

        # 创建 dreamwork_credits 表
        cursor.execute(
            """
            CREATE TABLE dreamwork_credits (
                id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(50),
                amount INTEGER,
                balance INTEGER,
                reason VARCHAR(200),
                task_id VARCHAR(50),
                created_at DATETIME
            )
        """
        )
        print("✓ dreamwork_credits 表创建成功")

        # 创建索引
        cursor.execute(
            "CREATE INDEX idx_dreamwork_user_created ON dreamwork_tasks (user_id, created_at)"
        )
        cursor.execute(
            "CREATE INDEX idx_dreamwork_status_updated ON dreamwork_tasks (status, updated_at)"
        )
        cursor.execute(
            "CREATE INDEX ix_dreamwork_tasks_user_id ON dreamwork_tasks (user_id)"
        )
        cursor.execute(
            "CREATE INDEX idx_dreamwork_user_created_credits ON dreamwork_credits (user_id, created_at)"
        )
        cursor.execute(
            "CREATE INDEX ix_dreamwork_credits_user_id ON dreamwork_credits (user_id)"
        )
        print("✓ 索引创建成功")

        # 提交事务
        conn.commit()
        print("✅ 所有DreamWork表创建完成!")

        # 验证表创建
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'dreamwork_%'"
        )
        tables = cursor.fetchall()
        print(f"已创建的表: {[table[0] for table in tables]}")

        return True

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    print("🎨 DreamWork数据库表创建脚本")
    print("=" * 50)

    success = create_dreamwork_tables()

    if success:
        print("\n✅ DreamWork数据库表创建成功!")
        print("现在可以重启应用并使用DreamWork功能了。")
    else:
        print("\n❌ 创建失败，请检查错误信息")
        sys.exit(1)
