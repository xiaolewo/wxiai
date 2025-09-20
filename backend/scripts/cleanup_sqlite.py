#!/usr/bin/env python3
"""
清理SQLite相关文件的脚本
删除所有与SQLite相关的文件和配置
"""

import os
import shutil
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DATA_DIR = BACKEND_DIR / "data"

# 要删除的SQLite相关文件和目录
SQLITE_FILES = [
    DATA_DIR / "webui.db",
    DATA_DIR / "ollama.db",
    DATA_DIR / "webui.db-shm",
    DATA_DIR / "webui.db-wal",
]

# 要清理的配置文件
CONFIG_FILES = [
    BACKEND_DIR / "open_webui" / "alembic.ini",
    BACKEND_DIR / "open_webui" / "migrations" / "env.py",
]


def remove_sqlite_files():
    """删除SQLite相关文件"""
    log.info("开始删除SQLite相关文件...")

    for file_path in SQLITE_FILES:
        if file_path.exists():
            try:
                if file_path.is_file():
                    file_path.unlink()
                    log.info(f"✅ 已删除文件: {file_path}")
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    log.info(f"✅ 已删除目录: {file_path}")
            except Exception as e:
                log.warning(f"⚠️ 删除 {file_path} 时出错: {e}")
        else:
            log.info(f"ℹ️ 文件不存在: {file_path}")


def clean_config_files():
    """清理配置文件中的SQLite相关配置"""
    log.info("开始清理配置文件...")

    # 清理 alembic.ini
    alembic_ini_path = BACKEND_DIR / "open_webui" / "alembic.ini"
    if alembic_ini_path.exists():
        try:
            with open(alembic_ini_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 移除SQLite相关的注释行
            lines = content.split("\n")
            cleaned_lines = []
            for line in lines:
                if "sqlite" not in line.lower() or line.strip().startswith("#"):
                    cleaned_lines.append(line)

            with open(alembic_ini_path, "w", encoding="utf-8") as f:
                f.write("\n".join(cleaned_lines))

            log.info("✅ 已清理 alembic.ini 中的SQLite相关配置")
        except Exception as e:
            log.warning(f"⚠️ 清理 alembic.ini 时出错: {e}")


def update_env_example():
    """更新.env.example文件，移除SQLite相关配置"""
    log.info("开始更新.env.example文件...")

    env_example_path = PROJECT_ROOT / ".env.example"
    if env_example_path.exists():
        try:
            with open(env_example_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 移除SQLite相关的配置行
            lines = content.split("\n")
            cleaned_lines = []
            in_sqlite_section = False

            for line in lines:
                # 检测SQLite相关配置段
                if "sqlite" in line.lower() and not line.strip().startswith("#"):
                    in_sqlite_section = True
                    continue
                elif (
                    in_sqlite_section
                    and line.strip().startswith("#")
                    and "====" not in line
                ):
                    # 继续跳过注释行
                    continue
                elif in_sqlite_section and line.strip().startswith("# ===="):
                    # 结束SQLite段
                    in_sqlite_section = False
                    continue
                elif in_sqlite_section:
                    # 跳过SQLite配置行
                    continue
                else:
                    cleaned_lines.append(line)

            with open(env_example_path, "w", encoding="utf-8") as f:
                f.write("\n".join(cleaned_lines))

            log.info("✅ 已更新 .env.example 文件")
        except Exception as e:
            log.warning(f"⚠️ 更新 .env.example 时出错: {e}")


def main():
    """主函数"""
    log.info("🚀 开始清理SQLite相关文件...")

    try:
        remove_sqlite_files()
        clean_config_files()
        update_env_example()

        log.info("🎉 SQLite相关文件清理完成!")
        log.info("💡 请确保已正确配置MySQL数据库环境变量")

    except Exception as e:
        log.error(f"❌ 清理过程中发生错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
