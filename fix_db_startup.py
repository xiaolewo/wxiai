#!/usr/bin/env python3
"""
修复数据库启动问题的脚本
在应用启动前确保所有迁移都已执行
"""

import os
import sys
import logging
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent / "backend"))


def run_migrations_sync():
    """同步执行数据库迁移"""
    try:
        print("🔄 开始执行数据库迁移...")

        # 设置环境变量
        os.environ.setdefault(
            "OPEN_WEBUI_DIR", str(Path(__file__).parent / "backend" / "open_webui")
        )

        from open_webui.config import OPEN_WEBUI_DIR
        from alembic import command
        from alembic.config import Config

        # 配置 alembic
        alembic_cfg = Config(OPEN_WEBUI_DIR / "alembic.ini")
        migrations_path = OPEN_WEBUI_DIR / "migrations"
        alembic_cfg.set_main_option("script_location", str(migrations_path))

        print(f"📁 迁移目录: {migrations_path}")
        print(f"📁 Alembic 配置: {OPEN_WEBUI_DIR / 'alembic.ini'}")

        # 执行迁移到最新版本
        command.upgrade(alembic_cfg, "head")
        print("✅ 数据库迁移执行成功!")

        return True

    except Exception as e:
        print(f"❌ 迁移执行失败: {e}")

        # 尝试直接创建表
        try:
            print("🔄 尝试直接创建数据库表...")

            # 导入所有模型以确保表被创建
            from open_webui.models import (
                auths,
                chats,
                documents,
                files,
                folders,
                functions,
                groups,
                knowledge,
                models,
                prompts,
                tags,
                tools,
                users,
                flux,
                jimeng,
                kling,
                midjourney,
                dreamwork,
                credits,
                feedback,
                notes,
                configs,
                channels,
                redemption,
                trade_tickets,
            )
            from open_webui.internal.db import engine, Base

            # 创建所有表
            Base.metadata.create_all(bind=engine)
            print("✅ 数据库表创建成功!")

            return True

        except Exception as create_error:
            print(f"❌ 表创建也失败: {create_error}")
            return False


def main():
    """主函数"""
    print("🚀 Open WebUI 数据库修复工具")
    print("=" * 50)

    # 检查环境
    backend_dir = Path(__file__).parent / "backend"
    if not backend_dir.exists():
        print("❌ 找不到 backend 目录")
        return False

    db_file = backend_dir / "data" / "webui.db"
    print(f"📍 数据库位置: {db_file}")

    if db_file.exists():
        print(f"📊 数据库大小: {db_file.stat().st_size} bytes")
    else:
        print("⚠️  数据库文件不存在，将创建新数据库")

    # 执行迁移
    success = run_migrations_sync()

    if success:
        print("\n🎉 修复完成!")
        print("✅ 现在可以正常启动应用了")
        print("\n建议的启动命令:")
        print("cd backend && python -m open_webui.main")
        return True
    else:
        print("\n💥 修复失败!")
        print("❌ 请检查错误信息或联系技术支持")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
