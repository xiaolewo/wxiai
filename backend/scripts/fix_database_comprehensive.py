#!/usr/bin/env python3
"""
一键数据库修复脚本
解决所有已知的数据库表结构问题
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
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    # 从环境变量获取，或使用默认路径
    db_path = os.environ.get("DATABASE_URL", "")
    if db_path.startswith("sqlite:///"):
        db_file = db_path.replace("sqlite:///", "")
        if not db_file.startswith("/"):
            return project_root / db_file
        return Path(db_file)
    else:
        # 默认SQLite数据库路径
        db_file = data_dir / "webui.db"
        if db_file.exists():
            return db_file
        db_file = project_root / "backend" / "data" / "webui.db"
        if db_file.exists():
            return db_file
        return db_file


def fix_database_comprehensive():
    """全面修复数据库"""
    db_path = get_database_path()
    log.info(f"开始全面修复数据库: {db_path}")

    # 如果文件不存在，尝试其他可能的路径
    if not db_path.exists():
        possible_paths = [
            Path(__file__).parent.parent / "backend" / "data" / "webui.db",
            Path(__file__).parent.parent / "data" / "webui.db",
            Path("/app/backend/data/webui.db"),
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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 定义需要修复的表和列
        table_fixes = {
            "prompt": [("access_control", "TEXT")],
            "chat": [
                ("pinned", "INTEGER DEFAULT 0"),
                ("meta", "TEXT"),
                ("folder_id", "TEXT"),
            ],
            "user": [("phone", "TEXT")],
            "tool": [("access_control", "TEXT")],
            "tag": [("meta", "TEXT")],
        }

        fixed_count = 0
        total_fixes = 0

        # 遍历所有需要修复的表
        for table_name, columns_to_add in table_fixes.items():
            try:
                # 检查表是否存在
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )
                if not cursor.fetchone():
                    log.info(f"表 {table_name} 不存在，跳过")
                    continue

                # 获取当前表结构
                cursor.execute(f"PRAGMA table_info({table_name})")
                current_columns = [col[1] for col in cursor.fetchall()]

                log.info(f"{table_name}表当前列: {current_columns}")

                # 添加缺失的列
                for column_name, column_type in columns_to_add:
                    total_fixes += 1
                    if column_name not in current_columns:
                        try:
                            cursor.execute(
                                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                            )
                            conn.commit()
                            log.info(
                                f"✅ 添加列 {column_name} ({column_type}) 到 {table_name} 表"
                            )
                            fixed_count += 1
                        except Exception as e:
                            log.warning(
                                f"添加列 {column_name} 到 {table_name} 表失败: {e}"
                            )
                    else:
                        log.info(f"✅ 列 {column_name} 已存在于 {table_name} 表")

            except Exception as e:
                log.error(f"处理表 {table_name} 时出错: {e}")

        conn.close()

        log.info(
            f"🎉 修复完成! 总共尝试修复 {total_fixes} 个列，成功修复 {fixed_count} 个列"
        )
        return True

    except Exception as e:
        log.error(f"数据库修复失败: {e}")
        return False


def main():
    """主函数"""
    log.info("🚀 开始一键数据库修复...")

    try:
        if fix_database_comprehensive():
            log.info("🎉 数据库修复完成! 请重启应用程序以确保更改生效")
            return 0
        else:
            log.error("❌ 数据库修复失败!")
            return 1

    except Exception as e:
        log.error(f"❌ 修复过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
