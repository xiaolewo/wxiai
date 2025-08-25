#!/usr/bin/env python3
"""
数据库初始化脚本
确保在新环境中数据库能够正确初始化
"""

import os
import sys
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def ensure_database_initialized():
    """确保数据库正确初始化"""
    log.info("开始数据库初始化检查...")

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

        # 验证关键表是否存在
        from open_webui.internal.db import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            # 检查 config 表
            result = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='config'"
                )
            )
            if result.fetchone():
                log.info("✅ config 表存在")
            else:
                log.error("❌ config 表不存在")
                return False

            # 检查 jimeng 表
            result = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%jimeng%'"
                )
            )
            jimeng_tables = [row[0] for row in result]
            if "jimeng_config" in jimeng_tables and "jimeng_tasks" in jimeng_tables:
                log.info("✅ Jimeng 表存在")
            else:
                log.error(f"❌ Jimeng 表缺失，找到的表: {jimeng_tables}")
                return False

            # 检查可灵对口型表
            result = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%kling_lip_sync%'"
                )
            )
            kling_lip_sync_tables = [row[0] for row in result]
            expected_tables = [
                "kling_lip_sync_config",
                "kling_lip_sync_tasks",
                "kling_lip_sync_credits",
            ]
            missing_tables = [
                t for t in expected_tables if t not in kling_lip_sync_tables
            ]

            if not missing_tables:
                log.info("✅ 可灵对口型表存在")
            else:
                log.error(
                    f"❌ 可灵对口型表缺失: {missing_tables}，找到的表: {kling_lip_sync_tables}"
                )
                return False

        log.info("🎉 数据库初始化检查完成，所有表都存在")
        return True

    except Exception as e:
        log.error(f"❌ 数据库初始化失败: {e}")
        return False


def test_config_loading():
    """测试配置加载是否正常"""
    log.info("测试配置加载...")

    try:
        from open_webui.config import CONFIG_DATA, get_config

        log.info("✅ 配置模块导入成功")

        # 测试配置获取
        config = get_config()
        log.info(f"✅ 配置加载成功: {type(config)}")

        return True

    except Exception as e:
        log.error(f"❌ 配置加载失败: {e}")
        return False


def test_jimeng_models():
    """测试 Jimeng 模型是否正常工作"""
    log.info("测试 Jimeng 模型...")

    try:
        from open_webui.models.jimeng import JimengConfig

        # 测试获取配置
        config = JimengConfig.get_config()
        if config:
            log.info("✅ Jimeng 配置存在")
        else:
            log.info("✅ Jimeng 配置不存在（正常，首次运行）")

        return True

    except Exception as e:
        log.error(f"❌ Jimeng 模型测试失败: {e}")
        return False


def test_kling_lip_sync_models():
    """测试可灵对口型模型是否正常工作"""
    log.info("测试可灵对口型模型...")

    try:
        from open_webui.models.kling_lip_sync import KlingLipSyncConfigs

        # 测试获取配置
        config = KlingLipSyncConfigs.get_config()
        if config:
            log.info("✅ 可灵对口型配置存在")
        else:
            log.info("✅ 可灵对口型配置不存在（正常，首次运行）")

        return True

    except Exception as e:
        log.error(f"❌ 可灵对口型模型测试失败: {e}")
        return False


if __name__ == "__main__":
    log.info("🚀 开始数据库初始化和测试...")

    # 运行所有检查
    checks = [
        ("数据库初始化", ensure_database_initialized),
        ("配置加载测试", test_config_loading),
        ("Jimeng模型测试", test_jimeng_models),
        ("可灵对口型模型测试", test_kling_lip_sync_models),
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
        log.info("\n🎉 所有检查通过！数据库已正确初始化。")
        sys.exit(0)
