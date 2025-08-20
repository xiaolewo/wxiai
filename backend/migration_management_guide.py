#!/usr/bin/env python3
"""
数据库迁移管理解决方案
解决添加新功能时影响其他功能的根本问题

问题分析：
1. 项目中存在多个未同步的迁移文件
2. 不同功能的迁移文件相互依赖但不一致
3. 数据库状态与迁移历史不匹配

解决方案：
1. 创建统一的迁移状态检查工具
2. 提供迁移冲突解决机制
3. 建立标准的功能添加流程
"""

import sqlite3
import os
import sys
import json
from datetime import datetime
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationManager:
    """数据库迁移管理器"""

    def __init__(
        self, db_path="data/webui.db", migrations_dir="open_webui/migrations/versions"
    ):
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir)
        self.ensure_db_directory()

    def ensure_db_directory(self):
        """确保数据库目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_current_db_version(self):
        """获取数据库当前版本"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查alembic_version表是否存在
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='alembic_version';
            """
            )

            if not cursor.fetchone():
                conn.close()
                return None

            cursor.execute("SELECT version_num FROM alembic_version LIMIT 1;")
            result = cursor.fetchone()
            conn.close()

            return result[0] if result else None

        except Exception as e:
            logger.error(f"获取数据库版本失败: {e}")
            return None

    def get_migration_files(self):
        """获取所有迁移文件信息"""
        migration_files = []

        if not self.migrations_dir.exists():
            logger.warning(f"迁移目录不存在: {self.migrations_dir}")
            return migration_files

        for file_path in sorted(self.migrations_dir.glob("*.py")):
            if file_path.name == "__init__.py":
                continue

            try:
                # 从文件名提取版本信息
                filename = file_path.name
                if "_" in filename:
                    version = filename.split("_")[0]
                    description = "_".join(filename.split("_")[1:]).replace(".py", "")

                    migration_files.append(
                        {
                            "file": filename,
                            "version": version,
                            "description": description,
                            "path": str(file_path),
                        }
                    )

            except Exception as e:
                logger.warning(f"解析迁移文件失败 {file_path}: {e}")

        return migration_files

    def get_actual_tables(self):
        """获取数据库中实际存在的表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%';
            """
            )

            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return sorted(tables)

        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            return []

    def get_table_columns(self, table_name):
        """获取表的列信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            return columns

        except Exception as e:
            logger.error(f"获取表 {table_name} 列信息失败: {e}")
            return []

    def analyze_migration_state(self):
        """分析迁移状态"""
        logger.info("🔍 开始分析数据库迁移状态...")

        current_version = self.get_current_db_version()
        migration_files = self.get_migration_files()
        actual_tables = self.get_actual_tables()

        analysis = {
            "current_version": current_version,
            "migration_files_count": len(migration_files),
            "actual_tables_count": len(actual_tables),
            "migration_files": migration_files,
            "actual_tables": actual_tables,
            "issues": [],
            "recommendations": [],
        }

        # 检查版本一致性
        if not current_version:
            analysis["issues"].append("数据库没有版本记录，可能未初始化Alembic")
            analysis["recommendations"].append(
                "运行 'alembic stamp head' 初始化版本记录"
            )

        # 检查已知的问题表
        expected_tables = [
            "user",
            "auth",
            "config",
            "chat",
            "tag",
            "channel",
            "folder",
            "mj_tasks",
            "dreamwork_tasks",
            "kling_tasks",
            "jimeng_tasks",
            "flux_config",
            "flux_tasks",
            "flux_credits",
            "cloud_storage_config",
            "generated_files",
            "credit",
            "credit_log",
            "group",
        ]

        missing_tables = [
            table for table in expected_tables if table not in actual_tables
        ]
        if missing_tables:
            analysis["issues"].append(f"缺失的表: {missing_tables}")
            analysis["recommendations"].append("运行数据库修复脚本或重新执行迁移")

        # 检查核心表的必需字段
        table_required_columns = {
            "chat": ["id", "user_id", "title", "folder_id", "pinned", "meta"],
            "tag": ["id", "name", "user_id", "meta"],
            "user": ["id", "email", "name", "phone"],
        }

        for table, required_cols in table_required_columns.items():
            if table in actual_tables:
                actual_cols = self.get_table_columns(table)
                missing_cols = [col for col in required_cols if col not in actual_cols]
                if missing_cols:
                    analysis["issues"].append(f"表 {table} 缺失字段: {missing_cols}")
                    analysis["recommendations"].append(f"为表 {table} 添加缺失字段")

        return analysis

    def create_migration_snapshot(self):
        """创建当前迁移状态快照"""
        logger.info("📸 创建迁移状态快照...")

        analysis = self.analyze_migration_state()
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "database_path": self.db_path,
            "analysis": analysis,
        }

        snapshot_file = (
            f"migration_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 快照已保存到: {snapshot_file}")
        return snapshot_file

    def reset_migration_state(self):
        """重置迁移状态（危险操作）"""
        logger.warning("⚠️ 这是一个危险操作，将重置所有迁移状态！")

        response = input("确认重置迁移状态？输入 'YES' 确认: ")
        if response != "YES":
            logger.info("操作已取消")
            return False

        try:
            # 备份数据库
            backup_path = (
                f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            import shutil

            shutil.copy2(self.db_path, backup_path)
            logger.info(f"数据库已备份到: {backup_path}")

            # 删除alembic_version表
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS alembic_version;")
            conn.commit()
            conn.close()

            logger.info("✅ 迁移状态已重置")
            return True

        except Exception as e:
            logger.error(f"重置迁移状态失败: {e}")
            return False

    def fix_migration_conflicts(self):
        """修复迁移冲突"""
        logger.info("🔧 开始修复迁移冲突...")

        # 首先运行数据库修复脚本
        try:
            from fix_database_tables import fix_database_tables

            logger.info("运行数据库表修复脚本...")
            if fix_database_tables():
                logger.info("✅ 数据库表修复完成")
            else:
                logger.error("❌ 数据库表修复失败")
                return False
        except ImportError:
            logger.warning("未找到数据库修复脚本，跳过...")

        # 检查并修复Alembic版本记录
        try:
            current_version = self.get_current_db_version()
            if not current_version:
                # 设置为最新的迁移版本
                migration_files = self.get_migration_files()
                if migration_files:
                    latest_version = migration_files[-1]["version"]

                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    # 创建alembic_version表
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS alembic_version (
                            version_num VARCHAR(32) NOT NULL,
                            PRIMARY KEY (version_num)
                        );
                    """
                    )

                    # 插入最新版本
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO alembic_version (version_num) 
                        VALUES (?);
                    """,
                        (latest_version,),
                    )

                    conn.commit()
                    conn.close()

                    logger.info(f"✅ 已设置数据库版本为: {latest_version}")

            return True

        except Exception as e:
            logger.error(f"修复迁移冲突失败: {e}")
            return False


def main():
    """主函数"""
    print("🔧 数据库迁移管理工具")
    print("=" * 50)

    manager = MigrationManager()

    while True:
        print("\n可用操作：")
        print("1. 分析迁移状态")
        print("2. 创建状态快照")
        print("3. 修复迁移冲突")
        print("4. 重置迁移状态（危险）")
        print("0. 退出")

        choice = input("\n请选择操作 (0-4): ").strip()

        if choice == "0":
            print("再见！")
            break
        elif choice == "1":
            analysis = manager.analyze_migration_state()
            print(f"\n📊 迁移状态分析:")
            print(f"当前版本: {analysis['current_version']}")
            print(f"迁移文件数: {analysis['migration_files_count']}")
            print(f"实际表数: {analysis['actual_tables_count']}")

            if analysis["issues"]:
                print(f"\n⚠️ 发现问题:")
                for issue in analysis["issues"]:
                    print(f"  - {issue}")

            if analysis["recommendations"]:
                print(f"\n💡 建议:")
                for rec in analysis["recommendations"]:
                    print(f"  - {rec}")

        elif choice == "2":
            snapshot_file = manager.create_migration_snapshot()
            print(f"✅ 快照已创建: {snapshot_file}")

        elif choice == "3":
            if manager.fix_migration_conflicts():
                print("✅ 迁移冲突修复完成")
            else:
                print("❌ 迁移冲突修复失败")

        elif choice == "4":
            manager.reset_migration_state()

        else:
            print("❌ 无效选择，请重试")


if __name__ == "__main__":
    main()
