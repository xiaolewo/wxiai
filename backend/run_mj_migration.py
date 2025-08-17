#!/usr/bin/env python3
"""
执行Midjourney数据库迁移
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from open_webui.internal.db import engine
from sqlalchemy import text


def create_mj_tables():
    """创建Midjourney相关数据表"""

    # SQL for creating mj_config table
    mj_config_sql = """
    CREATE TABLE IF NOT EXISTS mj_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enabled BOOLEAN DEFAULT 0,
        base_url VARCHAR(500),
        api_key TEXT,
        modes TEXT,  -- JSON stored as TEXT in SQLite
        default_mode VARCHAR(50) DEFAULT 'fast',
        max_concurrent_tasks INTEGER DEFAULT 5,
        task_timeout INTEGER DEFAULT 300000,
        created_at DATETIME,
        updated_at DATETIME
    );
    """

    # SQL for creating mj_tasks table
    mj_tasks_sql = """
    CREATE TABLE IF NOT EXISTS mj_tasks (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(50),
        action VARCHAR(50),
        status VARCHAR(50) DEFAULT 'SUBMITTED',
        prompt TEXT,
        prompt_en TEXT,
        description TEXT,
        mode VARCHAR(50) DEFAULT 'fast',
        credits_cost INTEGER DEFAULT 0,
        submit_time DATETIME,
        start_time DATETIME,
        finish_time DATETIME,
        progress VARCHAR(20) DEFAULT '0%',
        image_url TEXT,
        fail_reason TEXT,
        properties TEXT,  -- JSON stored as TEXT in SQLite
        buttons TEXT,     -- JSON stored as TEXT in SQLite
        parent_task_id VARCHAR(50),
        created_at DATETIME,
        updated_at DATETIME
    );
    """

    # SQL for creating mj_credits table
    mj_credits_sql = """
    CREATE TABLE IF NOT EXISTS mj_credits (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(50),
        amount INTEGER,
        balance INTEGER,
        reason VARCHAR(200),
        task_id VARCHAR(50),
        created_at DATETIME
    );
    """

    # Create indexes
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_user_created ON mj_tasks (user_id, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_status_updated ON mj_tasks (status, updated_at);",
        "CREATE INDEX IF NOT EXISTS ix_mj_tasks_user_id ON mj_tasks (user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_created_credits ON mj_credits (user_id, created_at);",
        "CREATE INDEX IF NOT EXISTS ix_mj_credits_user_id ON mj_credits (user_id);",
    ]

    try:
        with engine.connect() as connection:
            # Create tables
            connection.execute(text(mj_config_sql))
            connection.execute(text(mj_tasks_sql))
            connection.execute(text(mj_credits_sql))

            # Create indexes
            for index_sql in indexes_sql:
                connection.execute(text(index_sql))

            connection.commit()
            print("✅ Midjourney数据表创建成功！")

            # Verify tables were created
            tables = connection.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mj_%';"
                )
            ).fetchall()
            print(f"📋 已创建的MJ数据表: {[table[0] for table in tables]}")

    except Exception as e:
        print(f"❌ 数据表创建失败: {e}")
        return False

    return True


if __name__ == "__main__":
    print("🚀 开始创建Midjourney数据表...")
    success = create_mj_tables()

    if success:
        print("🎉 Midjourney数据库迁移完成！系统已准备就绪。")

        # Insert default config if not exists
        try:
            with engine.connect() as connection:
                existing = connection.execute(
                    text("SELECT COUNT(*) FROM mj_config")
                ).scalar()
                if existing == 0:
                    default_config = {
                        "turbo": {"enabled": True, "credits": 10},
                        "fast": {"enabled": True, "credits": 5},
                        "relax": {"enabled": True, "credits": 2},
                    }
                    import json
                    from datetime import datetime

                    connection.execute(
                        text(
                            """
                        INSERT INTO mj_config (enabled, modes, default_mode, max_concurrent_tasks, task_timeout, created_at, updated_at)
                        VALUES (0, :modes, 'fast', 5, 300000, :created_at, :updated_at)
                    """
                        ),
                        {
                            "modes": json.dumps(default_config),
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        },
                    )
                    connection.commit()
                    print("🔧 默认配置已初始化")
        except Exception as e:
            print(f"⚠️ 初始化默认配置失败: {e}")
    else:
        print("💥 迁移失败，请检查错误信息")
        sys.exit(1)
