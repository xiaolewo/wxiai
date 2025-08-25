#!/usr/bin/env python3
"""
数据库迁移状态检查工具
用于检查数据库当前迁移状态和健康度
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import json


@dataclass
class DatabaseStatus:
    """数据库状态信息"""

    current_revision: Optional[str]
    total_tables: int
    migration_table_exists: bool
    last_migration_date: Optional[str]
    database_size: int


class DatabaseChecker:
    """数据库状态检查器"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认SQLite数据库路径
            self.db_path = Path("webui.db")
        else:
            self.db_path = Path(db_path)

    def check_database_exists(self) -> bool:
        """检查数据库是否存在"""
        return self.db_path.exists()

    def get_database_size(self) -> int:
        """获取数据库文件大小"""
        if self.db_path.exists():
            return self.db_path.stat().st_size
        return 0

    def get_current_revision(self) -> Optional[str]:
        """获取当前迁移版本"""
        if not self.check_database_exists():
            return None

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                # 检查alembic_version表是否存在
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='alembic_version'
                """
                )

                if not cursor.fetchone():
                    return "no_alembic_table"

                # 获取当前版本
                cursor.execute("SELECT version_num FROM alembic_version")
                result = cursor.fetchone()

                return result[0] if result else "no_version"

        except sqlite3.Error as e:
            print(f"❌ 数据库查询错误: {e}")
            return None

    def get_table_count(self) -> int:
        """获取表数量"""
        if not self.check_database_exists():
            return 0

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """
                )
                result = cursor.fetchone()
                return result[0] if result else 0

        except sqlite3.Error as e:
            print(f"❌ 获取表数量失败: {e}")
            return 0

    def list_tables(self) -> List[str]:
        """列出所有表"""
        if not self.check_database_exists():
            return []

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """
                )
                return [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"❌ 获取表列表失败: {e}")
            return []

    def check_required_tables(self) -> Dict[str, bool]:
        """检查必需的表是否存在"""
        required_tables = {
            "user": False,
            "chat": False,
            "file": False,
            "credit": False,
            "credit_log": False,
            "config": False,
            "mj_config": False,
            "mj_tasks": False,
            "dreamwork_config": False,
            "dreamwork_tasks": False,
            "flux_config": False,
            "flux_tasks": False,
            "jimeng_config": False,
            "jimeng_tasks": False,
            "kling_config": False,
            "kling_tasks": False,
        }

        existing_tables = self.list_tables()

        for table in required_tables.keys():
            required_tables[table] = table in existing_tables

        return required_tables

    def get_database_status(self) -> DatabaseStatus:
        """获取数据库完整状态"""
        current_revision = self.get_current_revision()
        total_tables = self.get_table_count()
        database_size = self.get_database_size()

        return DatabaseStatus(
            current_revision=current_revision,
            total_tables=total_tables,
            migration_table_exists=(current_revision not in [None, "no_alembic_table"]),
            last_migration_date=None,  # TODO: 实现获取最后迁移日期
            database_size=database_size,
        )

    def print_status_report(self):
        """打印状态报告"""
        print("🔍 数据库状态检查报告")
        print("=" * 50)

        # 基本信息
        print(f"📁 数据库路径: {self.db_path}")
        print(f"📊 数据库存在: {'✅' if self.check_database_exists() else '❌'}")

        if not self.check_database_exists():
            print("❌ 数据库文件不存在，需要运行迁移创建数据库")
            return

        # 获取状态
        status = self.get_database_status()

        # 迁移信息
        print(f"📋 当前迁移版本: {status.current_revision or 'N/A'}")
        print(f"📊 数据库大小: {status.database_size / 1024 / 1024:.2f} MB")
        print(f"🗃️  表数量: {status.total_tables}")

        # 检查必需的表
        print("\n📋 核心表检查:")
        required_tables = self.check_required_tables()

        missing_tables = []
        for table, exists in required_tables.items():
            status_icon = "✅" if exists else "❌"
            print(f"  {status_icon} {table}")
            if not exists:
                missing_tables.append(table)

        # 总结
        print(f"\n📊 总结:")
        if status.current_revision and status.current_revision not in [
            "no_alembic_table",
            "no_version",
        ]:
            print("✅ 数据库迁移系统正常")
        else:
            print("❌ 数据库迁移系统异常")

        if missing_tables:
            print(
                f"❌ 缺失 {len(missing_tables)} 个核心表: {', '.join(missing_tables)}"
            )
            print("💡 建议运行: python fix_database_tables.py")
        else:
            print("✅ 所有核心表都存在")

        # 健康度评分
        health_score = self._calculate_health_score(status, required_tables)
        print(f"🏥 数据库健康度: {health_score:.0f}%")

        return status

    def _calculate_health_score(
        self, status: DatabaseStatus, required_tables: Dict[str, bool]
    ) -> float:
        """计算数据库健康度评分"""
        score = 0.0

        # 数据库存在 (20分)
        if self.check_database_exists():
            score += 20

        # 迁移系统正常 (30分)
        if status.migration_table_exists and status.current_revision not in [
            None,
            "no_alembic_table",
            "no_version",
        ]:
            score += 30

        # 核心表存在 (40分)
        existing_tables = sum(1 for exists in required_tables.values() if exists)
        total_tables = len(required_tables)
        if total_tables > 0:
            score += (existing_tables / total_tables) * 40

        # 表数量合理 (10分)
        if status.total_tables >= 15:  # 预期至少15个表
            score += 10
        elif status.total_tables >= 10:
            score += 5

        return min(score, 100.0)

    def export_status_json(self, output_file: str = "db_status.json"):
        """导出状态为JSON文件"""
        status = self.get_database_status()
        required_tables = self.check_required_tables()
        tables = self.list_tables()

        status_data = {
            "database_path": str(self.db_path),
            "database_exists": self.check_database_exists(),
            "current_revision": status.current_revision,
            "total_tables": status.total_tables,
            "database_size_mb": status.database_size / 1024 / 1024,
            "migration_table_exists": status.migration_table_exists,
            "required_tables": required_tables,
            "all_tables": tables,
            "health_score": self._calculate_health_score(status, required_tables),
            "timestamp": "2025-08-24",
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)

        print(f"📄 状态已导出到: {output_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="检查数据库迁移状态")
    parser.add_argument("--db-path", help="数据库文件路径")
    parser.add_argument("--export", help="导出JSON报告到指定文件")

    args = parser.parse_args()

    # 创建检查器
    checker = DatabaseChecker(args.db_path)

    # 运行检查
    status = checker.print_status_report()

    # 导出报告
    if args.export:
        checker.export_status_json(args.export)

    return 0


if __name__ == "__main__":
    sys.exit(main())
