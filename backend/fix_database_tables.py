#!/usr/bin/env python3
"""
数据库表修复脚本
用于确保所有必需的表都存在，解决部署和Docker环境中的数据库迁移问题
"""

import sqlite3
import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_path():
    """获取数据库文件路径"""
    # 尝试多个可能的路径
    possible_paths = [
        "data/webui.db",
        "../data/webui.db",
        "./data/webui.db",
        os.path.join(os.path.dirname(__file__), "data", "webui.db"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # 如果都不存在，使用默认路径
    return "data/webui.db"


def execute_sql(cursor, sql, description):
    """执行SQL并处理错误"""
    try:
        cursor.execute(sql)
        logger.info(f"✅ {description}")
        return True
    except Exception as e:
        logger.warning(f"⚠️ {description}: {e}")
        return False


def fix_database_tables():
    """修复所有缺失的数据库表"""
    db_path = get_db_path()
    logger.info(f"使用数据库文件: {db_path}")

    # 确保数据目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 添加chat表缺失的字段
        execute_sql(
            cursor,
            "ALTER TABLE chat ADD COLUMN folder_id VARCHAR(255);",
            "为chat表添加folder_id字段",
        )

        execute_sql(
            cursor,
            "ALTER TABLE chat ADD COLUMN pinned INTEGER DEFAULT 0;",
            "为chat表添加pinned字段",
        )

        execute_sql(
            cursor, "ALTER TABLE chat ADD COLUMN meta JSON;", "为chat表添加meta字段"
        )

        # 1.1 为tag表添加meta字段
        execute_sql(
            cursor, "ALTER TABLE tag ADD COLUMN meta JSON;", "为tag表添加meta字段"
        )

        # 2. 创建channel表
        execute_sql(
            cursor,
            """
            CREATE TABLE IF NOT EXISTS channel (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                type VARCHAR(20) NOT NULL DEFAULT 'private',
                name VARCHAR(255) NOT NULL,
                description TEXT,
                data JSON,
                meta JSON,
                access_control JSON,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
            "创建channel表",
        )

        # 3. 创建folder表
        execute_sql(
            cursor,
            """
            CREATE TABLE IF NOT EXISTS folder (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                parent_id VARCHAR(255),
                data JSON,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
            "创建folder表",
        )

        # 3.1 为folder表添加parent_id字段（如果表已存在）
        execute_sql(
            cursor,
            "ALTER TABLE folder ADD COLUMN parent_id VARCHAR(255);",
            "为folder表添加parent_id字段",
        )

        # 4. 创建mj_tasks表
        execute_sql(
            cursor,
            """
            CREATE TABLE IF NOT EXISTS mj_tasks (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                action VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                prompt TEXT,
                prompt_en TEXT,
                description TEXT,
                mode VARCHAR(50),
                credits_cost FLOAT DEFAULT 0,
                submit_time DATETIME,
                start_time DATETIME,
                finish_time DATETIME,
                progress INTEGER DEFAULT 0,
                image_url TEXT,
                fail_reason TEXT,
                properties JSON,
                buttons JSON,
                parent_task_id VARCHAR(255),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
            "创建mj_tasks表",
        )

        # 5. 创建dreamwork_tasks表
        execute_sql(
            cursor,
            """
            CREATE TABLE IF NOT EXISTS dreamwork_tasks (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                action VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                prompt TEXT,
                model VARCHAR(100),
                size VARCHAR(50),
                guidance_scale FLOAT,
                seed INTEGER,
                watermark BOOLEAN DEFAULT true,
                credits_cost FLOAT DEFAULT 0,
                submit_time DATETIME,
                start_time DATETIME,
                finish_time DATETIME,
                progress INTEGER DEFAULT 0,
                image_url TEXT,
                fail_reason TEXT,
                input_image TEXT,
                properties JSON,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
            "创建dreamwork_tasks表",
        )

        # 6. 创建kling_tasks表
        execute_sql(
            cursor,
            """
            CREATE TABLE IF NOT EXISTS kling_tasks (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                action VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                prompt TEXT,
                model VARCHAR(100),
                mode VARCHAR(50),
                aspect_ratio VARCHAR(20),
                duration INTEGER,
                cfg_scale FLOAT,
                credits_cost FLOAT DEFAULT 0,
                submit_time DATETIME,
                start_time DATETIME,
                finish_time DATETIME,
                progress INTEGER DEFAULT 0,
                video_url TEXT,
                image_url TEXT,
                fail_reason TEXT,
                properties JSON,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
            "创建kling_tasks表",
        )

        # 7. 创建jimeng_tasks表
        execute_sql(
            cursor,
            """
            CREATE TABLE IF NOT EXISTS jimeng_tasks (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                action VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                prompt TEXT,
                model VARCHAR(100),
                size VARCHAR(50),
                credits_cost FLOAT DEFAULT 0,
                submit_time DATETIME,
                start_time DATETIME,
                finish_time DATETIME,
                progress INTEGER DEFAULT 0,
                image_url TEXT,
                fail_reason TEXT,
                properties JSON,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
            "创建jimeng_tasks表",
        )

        # 8. 创建云存储相关表
        execute_sql(
            cursor,
            """
            CREATE TABLE IF NOT EXISTS cloud_storage_config (
                id VARCHAR(255) PRIMARY KEY,
                enabled BOOLEAN NOT NULL DEFAULT FALSE,
                provider VARCHAR(50) NOT NULL DEFAULT 'tencent_cos',
                secret_id VARCHAR(255),
                secret_key VARCHAR(500),
                region VARCHAR(50),
                bucket VARCHAR(100),
                cdn_url VARCHAR(500),
                upload_path VARCHAR(200) DEFAULT 'generated/',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
            "创建cloud_storage_config表",
        )

        execute_sql(
            cursor,
            """
            CREATE TABLE IF NOT EXISTS generated_files (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                filename VARCHAR(500) NOT NULL,
                file_type VARCHAR(20) NOT NULL,
                file_size INTEGER,
                source_type VARCHAR(50) NOT NULL,
                source_task_id VARCHAR(255),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                cloud_path VARCHAR(1000),
                cloud_url VARCHAR(1000),
                file_metadata JSON,
                error_message TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
            "创建generated_files表",
        )

        # 提交所有更改
        conn.commit()

        # 验证表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库中现有表: {sorted(tables)}")

        # 必需表列表
        required_tables = [
            "chat",
            "user",
            "auth",
            "config",
            "channel",
            "folder",
            "flux_config",
            "flux_tasks",
            "flux_credits",
            "mj_tasks",
            "dreamwork_tasks",
            "kling_tasks",
            "jimeng_tasks",
            "cloud_storage_config",
            "generated_files",
            "credit",
            "credit_log",
            "group",
        ]

        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            logger.warning(f"⚠️ 仍然缺失的表: {missing_tables}")
        else:
            logger.info("✅ 所有必需的表都已存在")

        logger.info("✅ 数据库表修复完成")

    except Exception as e:
        logger.error(f"❌ 数据库修复失败: {e}")
        return False
    finally:
        if "conn" in locals():
            conn.close()

    return True


if __name__ == "__main__":
    """直接运行脚本时执行修复"""
    print("🔧 开始修复数据库表...")
    success = fix_database_tables()
    if success:
        print("✅ 数据库表修复成功！")
        sys.exit(0)
    else:
        print("❌ 数据库表修复失败！")
        sys.exit(1)
