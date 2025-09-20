#!/usr/bin/env python3
"""
紧急修复脚本 - 修复chat表的pinned列问题
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


def fix_chat_table_pinned_column():
    """修复chat表的pinned列"""
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
        cursor = conn.cursor()

        # 检查是否存在chat表
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chat'"
        )
        if not cursor.fetchone():
            log.info("chat表不存在，无需修复")
            conn.close()
            return True

        # 检查chat表结构
        cursor.execute("PRAGMA table_info(chat)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]  # 第二列是列名

        log.info(f"chat表当前列: {column_names}")

        # 检查是否缺少pinned列
        if "pinned" not in column_names:
            log.info("添加pinned列...")
            cursor.execute("ALTER TABLE chat ADD COLUMN pinned INTEGER DEFAULT 0")
            conn.commit()
            log.info("✅ 成功添加pinned列")
        else:
            log.info("✅ pinned列已存在")

        # 检查是否缺少meta列
        if "meta" not in column_names:
            log.info("添加meta列...")
            cursor.execute("ALTER TABLE chat ADD COLUMN meta TEXT")
            conn.commit()
            log.info("✅ 成功添加meta列")
        else:
            log.info("✅ meta列已存在")

        # 检查是否缺少folder_id列
        if "folder_id" not in column_names:
            log.info("添加folder_id列...")
            cursor.execute("ALTER TABLE chat ADD COLUMN folder_id TEXT")
            conn.commit()
            log.info("✅ 成功添加folder_id列")
        else:
            log.info("✅ folder_id列已存在")

        conn.close()
        return True

    except Exception as e:
        log.error(f"修复chat表失败: {e}")
        return False


def main():
    """主函数"""
    log.info("🚀 开始修复chat表结构问题...")

    try:
        if fix_chat_table_pinned_column():
            log.info("🎉 chat表结构修复完成!")
            return 0
        else:
            log.error("❌ chat表结构修复失败!")
            return 1

    except Exception as e:
        log.error(f"❌ 修复过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
