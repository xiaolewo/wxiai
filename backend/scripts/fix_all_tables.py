#!/usr/bin/env python3
"""
全面数据库结构修复脚本
修复所有可能缺失的表列问题
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def get_database_path():
    """获取数据库路径"""
    # 项目根目录
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    # 从环境变量获取，或使用默认路径
    db_path = os.environ.get("DATABASE_URL", "")
    if db_path.startswith("sqlite:///"):
        db_file = db_path.replace("sqlite:///", "")
        # 如果是相对路径，转换为绝对路径
        if not db_file.startswith("/"):
            return project_root / db_file
        return Path(db_file)
    else:
        # 默认SQLite数据库路径
        db_file = data_dir / "webui.db"
        if db_file.exists():
            return db_file
        # 尝试backend/data路径
        db_file = project_root / "backend" / "data" / "webui.db"
        if db_file.exists():
            return db_file
        return db_file  # 即使不存在也返回路径


def fix_table_columns(conn, table_name, required_columns):
    """修复表的列结构"""
    try:
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if not cursor.fetchone():
            log.info(f"表 {table_name} 不存在，跳过")
            return True

        # 获取当前表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        current_columns = {col[1]: col[2] for col in columns}  # {列名: 类型}

        log.info(f"{table_name}表当前列: {list(current_columns.keys())}")

        # 检查并添加缺失的列
        for column_name, column_type in required_columns.items():
            if column_name not in current_columns:
                log.info(f"添加列 {column_name} ({column_type}) 到 {table_name} 表...")
                cursor.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                )
                log.info(f"✅ 成功添加列 {column_name}")

        return True

    except Exception as e:
        log.error(f"修复表 {table_name} 失败: {e}")
        return False


def fix_all_tables():
    """修复所有表的结构"""
    db_path = get_database_path()
    log.info(f"修复数据库: {db_path}")

    # 如果文件不存在，尝试其他可能的路径
    if not db_path.exists():
        # 尝试不同的路径
        possible_paths = [
            Path(__file__).parent.parent / "backend" / "data" / "webui.db",
            Path(__file__).parent.parent / "data" / "webui.db",
            Path("/app/backend/data/webui.db"),  # Docker路径
        ]

        for path in possible_paths:
            if path.exists():
                db_path = path
                log.info(f"找到数据库文件: {db_path}")
                break

    if not db_path.exists():
        log.error(f"数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        log.info(f"连接数据库: {db_path}")
        conn = sqlite3.connect(db_path)

        # 定义所有表的预期结构
        table_definitions = {
            "prompt": {
                "command": "TEXT",
                "user_id": "TEXT",
                "title": "TEXT",
                "content": "TEXT",
                "timestamp": "INTEGER",
                "access_control": "TEXT",
            },
            "chat": {
                "id": "TEXT",
                "user_id": "TEXT",
                "title": "TEXT",
                "chat": "TEXT",
                "created_at": "INTEGER",
                "updated_at": "INTEGER",
                "share_id": "TEXT",
                "archived": "INTEGER",
                "pinned": "INTEGER DEFAULT 0",
                "meta": "TEXT",
                "folder_id": "TEXT",
            },
            "user": {
                "id": "TEXT",
                "name": "TEXT",
                "email": "TEXT",
                "role": "TEXT",
                "profile_image_url": "TEXT",
                "last_active_at": "INTEGER",
                "updated_at": "INTEGER",
                "created_at": "INTEGER",
                "api_key": "TEXT",
                "settings": "TEXT",
                "info": "TEXT",
                "oauth_sub": "TEXT",
                "phone": "TEXT",
            },
            "tool": {
                "id": "TEXT",
                "user_id": "TEXT",
                "name": "TEXT",
                "content": "TEXT",
                "specs": "TEXT",
                "meta": "TEXT",
                "valves": "TEXT",
                "updated_at": "INTEGER",
                "created_at": "INTEGER",
                "access_control": "TEXT",
            },
        }

        # 修复所有表
        success = True
        for table_name, columns in table_definitions.items():
            if not fix_table_columns(conn, table_name, columns):
                success = False

        # 提交更改
        conn.commit()
        conn.close()

        if success:
            log.info("✅ 所有表结构修复完成")
            return True
        else:
            log.error("❌ 部分表结构修复失败")
            return False

    except Exception as e:
        log.error(f"修复数据库表结构失败: {e}")
        return False


def main():
    """主函数"""
    log.info("🚀 开始全面修复数据库表结构...")

    try:
        if fix_all_tables():
            log.info("🎉 数据库表结构修复完成!")
            return 0
        else:
            log.error("❌ 数据库表结构修复失败!")
            return 1

    except Exception as e:
        log.error(f"❌ 修复过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
