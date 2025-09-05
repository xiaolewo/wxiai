#!/usr/bin/env python3
"""
手动创建Google Images相关表的紧急修复脚本
当Alembic迁移失败时使用
"""

import sqlite3
import os
import sys
from datetime import datetime


def fix_google_images_tables():
    """手动创建Google Images相关的数据库表"""

    # 查找数据库文件
    db_paths = ["backend/data/webui.db", "webui.db", "backend/webui.db"]
    db_path = None

    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        print("❌ 错误: 未找到数据库文件")
        return False

    print(f"📍 使用数据库: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表是否已存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='google_images_config'"
        )
        if cursor.fetchone():
            print("✅ google_images_config 表已存在，跳过创建")
            return True

        print("🔧 开始创建Google Images相关表...")

        # 1. 创建google_images_config表
        cursor.execute(
            """
            CREATE TABLE google_images_config (
                id INTEGER NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT 0,
                base_url VARCHAR(500),
                api_key TEXT,
                default_model VARCHAR(50) NOT NULL DEFAULT 'nano-banana',
                max_images_per_request INTEGER NOT NULL DEFAULT 10,
                timeout INTEGER NOT NULL DEFAULT 60,
                credits_per_generation INTEGER NOT NULL DEFAULT 20,
                credits_per_image INTEGER NOT NULL DEFAULT 5,
                additional_config JSON,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                PRIMARY KEY (id),
                UNIQUE (id)
            )
        """
        )

        # 创建配置表索引
        cursor.execute(
            "CREATE INDEX ix_google_images_config_id ON google_images_config (id)"
        )

        # 插入默认配置
        cursor.execute(
            """
            INSERT INTO google_images_config (
                enabled, default_model, max_images_per_request,
                timeout, credits_per_generation, credits_per_image
            ) VALUES (0, 'nano-banana', 10, 60, 20, 5)
        """
        )

        print("✅ google_images_config 表创建成功")

        # 2. 创建google_images_tasks表
        cursor.execute(
            """
            CREATE TABLE google_images_tasks (
                id VARCHAR(50) NOT NULL,
                user_id VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'submitted',
                prompt TEXT NOT NULL,
                model VARCHAR(50) NOT NULL DEFAULT 'nano-banana',
                size VARCHAR(20),
                quality VARCHAR(20),
                style VARCHAR(20),
                input_images JSON,
                cloud_input_images JSON,
                result_images JSON,
                cloud_result_images JSON,
                progress VARCHAR(10) DEFAULT '0%',
                fail_reason TEXT,
                credits_cost INTEGER,
                properties JSON,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                finish_time DATETIME,
                PRIMARY KEY (id)
            )
        """
        )

        # 创建任务表索引
        cursor.execute(
            "CREATE INDEX ix_google_images_tasks_id ON google_images_tasks (id)"
        )
        cursor.execute(
            "CREATE INDEX ix_google_images_tasks_user_id ON google_images_tasks (user_id)"
        )
        cursor.execute(
            "CREATE INDEX ix_google_images_tasks_status ON google_images_tasks (status)"
        )
        cursor.execute(
            "CREATE INDEX ix_google_images_tasks_created_at ON google_images_tasks (created_at)"
        )

        print("✅ google_images_tasks 表创建成功")

        # 3. 创建google_images_credits表
        cursor.execute(
            """
            CREATE TABLE google_images_credits (
                id VARCHAR(50) NOT NULL,
                user_id VARCHAR(50) NOT NULL,
                task_id VARCHAR(50) NOT NULL,
                credit_amount INTEGER NOT NULL,
                credits_before INTEGER,
                credits_after INTEGER,
                operation_type VARCHAR(20) NOT NULL DEFAULT 'deduct',
                model_name VARCHAR(50),
                description TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            )
        """
        )

        # 创建积分表索引
        cursor.execute(
            "CREATE INDEX ix_google_images_credits_id ON google_images_credits (id)"
        )
        cursor.execute(
            "CREATE INDEX ix_google_images_credits_user_id ON google_images_credits (user_id)"
        )
        cursor.execute(
            "CREATE INDEX ix_google_images_credits_task_id ON google_images_credits (task_id)"
        )
        cursor.execute(
            "CREATE INDEX ix_google_images_credits_created_at ON google_images_credits (created_at)"
        )

        print("✅ google_images_credits 表创建成功")

        # 提交事务
        conn.commit()
        conn.close()

        print("🎉 所有Google Images表创建完成!")
        print("💡 建议稍后运行 'alembic upgrade head' 同步迁移状态")

        return True

    except Exception as e:
        print(f"❌ 创建表时出错: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def verify_tables():
    """验证表是否创建成功"""
    db_paths = ["backend/data/webui.db", "webui.db", "backend/webui.db"]
    db_path = None

    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ["google_images_config", "google_images_tasks", "google_images_credits"]
    all_exist = True

    for table in tables:
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
        )
        exists = bool(cursor.fetchone())
        print(f"📋 {table}: {'✅ 存在' if exists else '❌ 不存在'}")
        if not exists:
            all_exist = False

    conn.close()
    return all_exist


if __name__ == "__main__":
    print("🚀 Google Images表修复脚本")
    print("=" * 50)

    # 检查当前状态
    print("🔍 检查当前表状态...")
    if verify_tables():
        print("✅ 所有Google Images表都已存在，无需修复")
        sys.exit(0)

    # 执行修复
    if fix_google_images_tables():
        print("\n🔍 验证修复结果...")
        if verify_tables():
            print("\n🎉 修复成功! 可以继续使用Google Images功能")
        else:
            print("\n❌ 修复后仍有表缺失，请检查错误信息")
    else:
        print("\n❌ 修复失败，请查看错误信息或尝试其他方法")
