#!/usr/bin/env python3
"""
简化版数据库修复脚本
解决"no such column: prompt.access_control"错误
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


def fix_prompt_table():
    """修复prompt表结构"""
    db_path = get_database_path()
    log.info(f"尝试修复数据库: {db_path}")

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
        # 列出可能的数据库文件
        project_root = Path(__file__).parent.parent
        log.info("在项目中搜索数据库文件...")
        for db_file in project_root.rglob("*.db"):
            log.info(f"  找到: {db_file}")
        return False

    try:
        # 连接数据库
        log.info(f"连接数据库: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查是否存在prompt表
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='prompt'"
        )
        if not cursor.fetchone():
            log.info("prompt表不存在，无需修复")
            conn.close()
            return True

        # 检查prompt表结构
        cursor.execute("PRAGMA table_info(prompt)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]  # 第二列是列名

        log.info(f"prompt表当前列: {column_names}")

        # 检查是否缺少access_control列
        if "access_control" not in column_names:
            log.info("添加access_control列...")
            cursor.execute("ALTER TABLE prompt ADD COLUMN access_control TEXT")
            conn.commit()
            log.info("✅ 成功添加access_control列")
        else:
            log.info("✅ access_control列已存在")

        # 检查其他可能缺失的列
        expected_columns = [
            "command",
            "user_id",
            "title",
            "content",
            "timestamp",
            "access_control",
        ]
        missing_columns = [col for col in expected_columns if col not in column_names]

        if missing_columns:
            log.warning(f"发现其他缺失的列: {missing_columns}")
        else:
            log.info("✅ prompt表结构完整")

        conn.close()
        return True

    except Exception as e:
        log.error(f"修复数据库表结构失败: {e}")
        return False


def main():
    """主函数"""
    log.info("🚀 开始修复数据库表结构...")

    try:
        if fix_prompt_table():
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
