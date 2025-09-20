#!/usr/bin/env python3
"""
MySQL数据库初始化脚本
确保在新环境中数据库能够正确初始化
"""

import os
import sys
import logging
import subprocess

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def create_mysql_database():
    """创建MySQL数据库和用户"""
    log.info("开始创建MySQL数据库...")

    try:
        import pymysql
        from pymysql import connect

        # 从环境变量获取数据库配置
        db_host = os.environ.get("DATABASE_HOST", "localhost")
        db_port = int(os.environ.get("DATABASE_PORT", 3306))
        db_user = os.environ.get("DATABASE_USER", "wxiai_user")
        db_password = os.environ.get("DATABASE_PASSWORD", "wxiai_password")
        db_name = os.environ.get("DATABASE_NAME", "wxiai_db")

        # 首先以root用户连接到MySQL（需要确保root用户可以无密码连接或已设置密码）
        try:
            # 尝试无密码连接
            conn = connect(host=db_host, port=db_port, user="root", charset="utf8mb4")
        except Exception as e:
            log.warning(f"无密码连接失败: {e}")
            # 如果无密码连接失败，尝试使用环境变量中的密码
            root_password = os.environ.get("MYSQL_ROOT_PASSWORD", "")
            if root_password:
                conn = connect(
                    host=db_host,
                    port=db_port,
                    user="root",
                    password=root_password,
                    charset="utf8mb4",
                )
            else:
                log.error("无法连接到MySQL服务器，请确保MySQL正在运行并正确配置")
                return False

        cursor = conn.cursor()

        # 创建数据库
        try:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            log.info(f"✅ 数据库 {db_name} 创建成功或已存在")
        except Exception as e:
            log.error(f"创建数据库失败: {e}")
            return False

        # 创建用户并授权
        try:
            cursor.execute(
                f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_password}'"
            )
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            log.info(f"✅ 用户 {db_user} 创建成功或已存在，并已授权")
        except Exception as e:
            log.error(f"创建用户或授权失败: {e}")
            return False

        cursor.close()
        conn.close()

        log.info("🎉 MySQL数据库初始化完成")
        return True

    except ImportError:
        log.error("❌ 未安装PyMySQL，请先安装: pip install PyMySQL")
        return False
    except Exception as e:
        log.error(f"❌ MySQL数据库初始化失败: {e}")
        return False


def run_database_migrations():
    """运行数据库迁移"""
    log.info("开始运行数据库迁移...")

    try:
        # 导入必要的模块
        from open_webui.env import OPEN_WEBUI_DIR
        from alembic import command
        from alembic.config import Config

        # 设置 Alembic 配置
        alembic_cfg = Config(OPEN_WEBUI_DIR / "alembic.ini")
        migrations_path = OPEN_WEBUI_DIR / "migrations"
        alembic_cfg.set_main_option("script_location", str(migrations_path))

        # 运行迁移
        log.info("运行数据库迁移...")
        command.upgrade(alembic_cfg, "head")
        log.info("✅ 数据库迁移完成")

        return True

    except Exception as e:
        log.error(f"❌ 数据库迁移失败: {e}")
        return False


def test_database_connection():
    """测试数据库连接"""
    log.info("测试数据库连接...")

    try:
        from open_webui.internal.db import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                log.info("✅ 数据库连接测试成功")
                return True
            else:
                log.error("❌ 数据库连接测试失败")
                return False

    except Exception as e:
        log.error(f"❌ 数据库连接测试失败: {e}")
        return False


if __name__ == "__main__":
    log.info("🚀 开始MySQL数据库初始化...")

    # 运行所有检查
    checks = [
        ("创建MySQL数据库", create_mysql_database),
        ("测试数据库连接", test_database_connection),
        ("运行数据库迁移", run_database_migrations),
    ]

    failed_checks = []

    for check_name, check_func in checks:
        log.info(f"\n--- {check_name} ---")
        if not check_func():
            failed_checks.append(check_name)

    if failed_checks:
        log.error(f"\n❌ 以下检查失败: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        log.info("\n🎉 所有检查通过！MySQL数据库已正确初始化。")
        sys.exit(0)
