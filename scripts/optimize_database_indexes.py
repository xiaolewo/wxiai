#!/usr/bin/env python3
"""
数据库索引优化脚本
用于添加关键性能索引，提升查询效率
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseIndexOptimizer:
    """数据库索引优化器"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 使用默认数据库路径
            self.db_path = Path("webui.db")
        else:
            self.db_path = Path(db_path)

        # 定义所有需要的索引
        self.indexes = [
            # 用户和积分相关索引
            {
                "name": "idx_credit_user_id",
                "table": "credit",
                "columns": ["user_id"],
                "description": "优化用户积分查询",
            },
            {
                "name": "idx_credit_log_user_time",
                "table": "credit_log",
                "columns": ["user_id", "created_at"],
                "description": "优化积分日志查询",
            },
            {
                "name": "idx_user_email",
                "table": "user",
                "columns": ["email"],
                "description": "优化邮箱登录查询",
            },
            {
                "name": "idx_user_phone",
                "table": "user",
                "columns": ["phone"],
                "description": "优化手机号登录查询",
            },
            # Midjourney任务索引
            {
                "name": "idx_mj_tasks_user_status",
                "table": "mj_tasks",
                "columns": ["user_id", "status"],
                "description": "优化MJ任务状态查询",
            },
            {
                "name": "idx_mj_tasks_submit_time",
                "table": "mj_tasks",
                "columns": ["submit_time"],
                "description": "优化MJ任务时间排序",
            },
            {
                "name": "idx_mj_tasks_status_updated",
                "table": "mj_tasks",
                "columns": ["status", "updated_at"],
                "description": "优化MJ任务状态更新查询",
            },
            # Flux任务索引
            {
                "name": "idx_flux_tasks_user_created",
                "table": "flux_tasks",
                "columns": ["user_id", "created_at"],
                "description": "优化Flux任务用户查询",
            },
            {
                "name": "idx_flux_tasks_status",
                "table": "flux_tasks",
                "columns": ["status"],
                "description": "优化Flux任务状态查询",
            },
            # DreamWork任务索引
            {
                "name": "idx_dreamwork_tasks_user_created",
                "table": "dreamwork_tasks",
                "columns": ["user_id", "created_at"],
                "description": "优化DreamWork任务查询",
            },
            {
                "name": "idx_dreamwork_tasks_status_updated",
                "table": "dreamwork_tasks",
                "columns": ["status", "updated_at"],
                "description": "优化DreamWork任务状态查询",
            },
            # Jimeng任务索引
            {
                "name": "idx_jimeng_tasks_user_created",
                "table": "jimeng_tasks",
                "columns": ["user_id", "created_at"],
                "description": "优化Jimeng任务查询",
            },
            {
                "name": "idx_jimeng_tasks_status",
                "table": "jimeng_tasks",
                "columns": ["status"],
                "description": "优化Jimeng任务状态查询",
            },
            # Kling任务索引
            {
                "name": "idx_kling_tasks_user_created",
                "table": "kling_tasks",
                "columns": ["user_id", "created_at"],
                "description": "优化Kling任务查询",
            },
            {
                "name": "idx_kling_tasks_status",
                "table": "kling_tasks",
                "columns": ["status"],
                "description": "优化Kling任务状态查询",
            },
            # 聊天相关索引
            {
                "name": "idx_chat_user_updated",
                "table": "chat",
                "columns": ["user_id", "updated_at"],
                "description": "优化用户聊天列表查询",
            },
            {
                "name": "idx_chat_created_at",
                "table": "chat",
                "columns": ["created_at"],
                "description": "优化聊天时间排序",
            },
            {
                "name": "idx_message_chat_created",
                "table": "message",
                "columns": ["chat_id", "created_at"],
                "description": "优化聊天消息查询",
            },
            # 文件相关索引
            {
                "name": "idx_file_user_created",
                "table": "file",
                "columns": ["user_id", "created_at"],
                "description": "优化用户文件查询",
            },
            {
                "name": "idx_file_hash",
                "table": "file",
                "columns": ["hash"],
                "description": "优化文件去重查询",
            },
            # 生成文件索引
            {
                "name": "idx_generated_files_user_service",
                "table": "generated_files",
                "columns": ["user_id", "source_type"],
                "description": "优化生成文件查询",
            },
            {
                "name": "idx_generated_files_task",
                "table": "generated_files",
                "columns": ["source_task_id"],
                "description": "优化任务文件关联查询",
            },
            # 知识库索引
            {
                "name": "idx_knowledge_user_updated",
                "table": "knowledge",
                "columns": ["user_id", "updated_at"],
                "description": "优化用户知识库查询",
            },
            # 交易记录索引
            {
                "name": "idx_trade_ticket_user",
                "table": "trade_ticket",
                "columns": ["user_id"],
                "description": "优化用户交易记录查询",
            },
            {
                "name": "idx_trade_ticket_status",
                "table": "trade_ticket",
                "columns": ["status"],
                "description": "优化交易状态查询",
            },
        ]

    def check_database_exists(self) -> bool:
        """检查数据库是否存在"""
        return self.db_path.exists()

    def get_existing_indexes(self) -> List[str]:
        """获取现有的索引列表"""
        if not self.check_database_exists():
            return []

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND sql IS NOT NULL
                """
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"获取现有索引失败: {e}")
            return []

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        if not self.check_database_exists():
            return False

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name=?
                """,
                    (table_name,),
                )
                return cursor.fetchone()[0] > 0
        except sqlite3.Error as e:
            logger.error(f"检查表存在性失败: {e}")
            return False

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """检查列是否存在"""
        if not self.check_database_exists():
            return False

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                return column_name in columns
        except sqlite3.Error as e:
            logger.error(f"检查列存在性失败: {e}")
            return False

    def create_index(self, index_info: Dict) -> bool:
        """创建单个索引"""
        table_name = index_info["table"]
        index_name = index_info["name"]
        columns = index_info["columns"]
        description = index_info["description"]

        # 检查表是否存在
        if not self.table_exists(table_name):
            logger.warning(f"表 {table_name} 不存在，跳过索引 {index_name}")
            return False

        # 检查所有列是否存在
        for column in columns:
            if not self.column_exists(table_name, column):
                logger.warning(
                    f"表 {table_name} 中列 {column} 不存在，跳过索引 {index_name}"
                )
                return False

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                # 构建CREATE INDEX语句
                columns_str = ", ".join(columns)
                create_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns_str})"

                logger.info(f"创建索引: {index_name} - {description}")
                logger.debug(f"SQL: {create_sql}")

                cursor.execute(create_sql)
                conn.commit()
                return True

        except sqlite3.Error as e:
            logger.error(f"创建索引 {index_name} 失败: {e}")
            return False

    def analyze_database(self):
        """分析数据库统计信息"""
        if not self.check_database_exists():
            logger.error("数据库不存在")
            return

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                logger.info("分析数据库统计信息...")
                cursor.execute("ANALYZE")
                conn.commit()

                logger.info("数据库分析完成")

        except sqlite3.Error as e:
            logger.error(f"数据库分析失败: {e}")

    def optimize_database(self) -> Dict[str, Any]:
        """优化数据库 - 创建所有索引"""
        if not self.check_database_exists():
            logger.error("数据库文件不存在，请先运行应用创建数据库")
            return {
                "success": False,
                "error": "Database not found",
                "created_indexes": [],
                "skipped_indexes": [],
            }

        logger.info("开始数据库索引优化...")

        existing_indexes = self.get_existing_indexes()
        logger.info(f"现有索引数量: {len(existing_indexes)}")

        created_indexes = []
        skipped_indexes = []
        failed_indexes = []

        for index_info in self.indexes:
            index_name = index_info["name"]

            if index_name in existing_indexes:
                logger.info(f"索引 {index_name} 已存在，跳过")
                skipped_indexes.append(index_name)
                continue

            if self.create_index(index_info):
                created_indexes.append(index_name)
            else:
                failed_indexes.append(index_name)

        # 分析数据库以更新统计信息
        self.analyze_database()

        # 汇总结果
        result = {
            "success": len(failed_indexes) == 0,
            "total_indexes": len(self.indexes),
            "created_indexes": created_indexes,
            "skipped_indexes": skipped_indexes,
            "failed_indexes": failed_indexes,
            "existing_indexes_count": len(existing_indexes),
        }

        logger.info("数据库索引优化完成")
        logger.info(f"总索引: {result['total_indexes']}")
        logger.info(f"新创建: {len(created_indexes)}")
        logger.info(f"跳过: {len(skipped_indexes)}")
        logger.info(f"失败: {len(failed_indexes)}")

        return result

    def get_index_usage_stats(self) -> List[Dict]:
        """获取索引使用统计（SQLite支持有限）"""
        if not self.check_database_exists():
            return []

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                # 获取所有索引的基本信息
                cursor.execute(
                    """
                    SELECT name, tbl_name, sql 
                    FROM sqlite_master 
                    WHERE type='index' AND sql IS NOT NULL
                    ORDER BY tbl_name, name
                """
                )

                indexes = []
                for row in cursor.fetchall():
                    indexes.append({"name": row[0], "table": row[1], "sql": row[2]})

                return indexes

        except sqlite3.Error as e:
            logger.error(f"获取索引统计失败: {e}")
            return []

    def generate_optimization_report(self) -> str:
        """生成优化报告"""
        report = []
        report.append("# 数据库索引优化报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        if not self.check_database_exists():
            report.append("❌ 数据库文件不存在")
            return "\n".join(report)

        # 数据库基本信息
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()

                # 获取数据库大小
                db_size = self.db_path.stat().st_size / 1024 / 1024  # MB

                # 获取表数量
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """
                )
                table_count = cursor.fetchone()[0]

                report.append("## 数据库基本信息")
                report.append(f"- 数据库大小: {db_size:.2f} MB")
                report.append(f"- 表数量: {table_count}")
                report.append("")

        except Exception as e:
            report.append(f"获取数据库信息失败: {e}")

        # 现有索引
        existing_indexes = self.get_existing_indexes()
        report.append("## 现有索引")
        report.append(f"索引总数: {len(existing_indexes)}")

        for index in existing_indexes[:10]:  # 只显示前10个
            report.append(f"- {index}")

        if len(existing_indexes) > 10:
            report.append(f"... 还有 {len(existing_indexes) - 10} 个索引")

        report.append("")

        # 建议的索引优化
        report.append("## 建议的索引优化")
        missing_indexes = []

        for index_info in self.indexes:
            if index_info["name"] not in existing_indexes:
                if self.table_exists(index_info["table"]):
                    missing_indexes.append(index_info)

        if missing_indexes:
            report.append(f"发现 {len(missing_indexes)} 个可以添加的性能索引:")
            report.append("")

            for index_info in missing_indexes:
                report.append(f"### {index_info['name']}")
                report.append(f"- 表: {index_info['table']}")
                report.append(f"- 列: {', '.join(index_info['columns'])}")
                report.append(f"- 作用: {index_info['description']}")
                report.append("")
        else:
            report.append("✅ 所有建议的索引都已创建")

        # 执行建议
        report.append("## 执行建议")
        report.append("运行以下命令来优化数据库索引:")
        report.append("```bash")
        report.append("python scripts/optimize_database_indexes.py")
        report.append("```")

        return "\n".join(report)


def main():
    """主函数"""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="数据库索引优化工具")
    parser.add_argument("--db-path", help="数据库文件路径")
    parser.add_argument("--report", action="store_true", help="只生成报告，不执行优化")
    parser.add_argument("--stats", action="store_true", help="显示索引使用统计")

    args = parser.parse_args()

    # 创建优化器
    optimizer = DatabaseIndexOptimizer(args.db_path)

    if args.report:
        # 生成报告
        report = optimizer.generate_optimization_report()
        print(report)

        # 保存报告到文件
        report_file = (
            f"db_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n报告已保存到: {report_file}")

    elif args.stats:
        # 显示索引统计
        stats = optimizer.get_index_usage_stats()
        print("索引使用统计:")
        for stat in stats:
            print(f"- {stat['name']} (表: {stat['table']})")

    else:
        # 执行优化
        result = optimizer.optimize_database()

        if result["success"]:
            print("✅ 数据库索引优化成功完成!")
        else:
            print("❌ 数据库索引优化完成，但存在一些问题")

        print(f"总索引: {result['total_indexes']}")
        print(f"新创建: {len(result['created_indexes'])}")
        print(f"跳过: {len(result['skipped_indexes'])}")
        print(f"失败: {len(result['failed_indexes'])}")

        if result["created_indexes"]:
            print("\n新创建的索引:")
            for index in result["created_indexes"]:
                print(f"  ✅ {index}")

        if result["failed_indexes"]:
            print("\n创建失败的索引:")
            for index in result["failed_indexes"]:
                print(f"  ❌ {index}")


if __name__ == "__main__":
    main()
