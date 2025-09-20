#!/usr/bin/env python3
"""
修复数据库表结构问题的脚本
解决"no such column: prompt.access_control"错误
"""

import os
import sys
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# 添加项目路径到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from open_webui.internal.db import engine
    from sqlalchemy import text
except ImportError as e:
    log.error(f"导入项目模块失败: {e}")
    sys.exit(1)


def check_and_fix_prompt_table():
    """检查并修复prompt表结构"""
    log.info("检查prompt表结构...")

    try:
        with engine.connect() as conn:
            # 检查prompt表是否存在access_control列
            try:
                result = conn.execute(text("PRAGMA table_info(prompt)"))
                columns = [(row[1], row[2]) for row in result]  # (name, type)
                column_names = [row[0] for row in columns]

                log.info(f"prompt表当前列: {column_names}")

                # 如果access_control列不存在，则添加
                if "access_control" not in column_names:
                    log.info("添加access_control列...")
                    conn.execute(
                        text("ALTER TABLE prompt ADD COLUMN access_control TEXT")
                    )
                    log.info("✅ 成功添加access_control列")
                else:
                    log.info("✅ access_control列已存在")

                # 检查是否有其他缺失的列
                expected_columns = [
                    "command",
                    "user_id",
                    "title",
                    "content",
                    "timestamp",
                    "access_control",
                ]
                missing_columns = [
                    col for col in expected_columns if col not in column_names
                ]

                if missing_columns:
                    log.warning(f"发现缺失的列: {missing_columns}")
                    # 这里可以添加更多列修复逻辑
                else:
                    log.info("✅ prompt表结构完整")

                conn.commit()
                return True

            except Exception as e:
                log.error(f"检查prompt表结构失败: {e}")
                return False

    except Exception as e:
        log.error(f"连接数据库失败: {e}")
        return False


def run_database_migrations():
    """运行数据库迁移"""
    log.info("运行数据库迁移...")

    try:
        from open_webui.env import OPEN_WEBUI_DIR
        from alembic import command
        from alembic.config import Config

        # 设置 Alembic 配置
        alembic_cfg = Config(OPEN_WEBUI_DIR / "alembic.ini")
        migrations_path = OPEN_WEBUI_DIR / "migrations"
        alembic_cfg.set_main_option("script_location", str(migrations_path))

        # 运行迁移
        log.info("执行alembic upgrade head...")
        command.upgrade(alembic_cfg, "head")
        log.info("✅ 数据库迁移完成")

        return True

    except Exception as e:
        log.error(f"❌ 数据库迁移失败: {e}")
        return False


def verify_database_connection():
    """验证数据库连接"""
    log.info("验证数据库连接...")

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                log.info("✅ 数据库连接正常")
                return True
            else:
                log.error("❌ 数据库连接异常")
                return False
    except Exception as e:
        log.error(f"❌ 数据库连接失败: {e}")
        return False


def main():
    """主函数"""
    log.info("🚀 开始修复数据库表结构问题...")

    try:
        # 首先验证数据库连接
        if not verify_database_connection():
            log.error("数据库连接失败，无法继续")
            return 1

        # 运行数据库迁移
        if not run_database_migrations():
            log.warning("数据库迁移失败，尝试手动修复表结构")

        # 检查并修复prompt表
        if check_and_fix_prompt_table():
            log.info("🎉 数据库表结构修复完成!")
            return 0
        else:
            log.error("❌ 数据库表结构修复失败!")
            return 1

    except Exception as e:
        log.error(f"❌ 修复过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
