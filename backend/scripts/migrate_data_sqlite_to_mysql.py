#!/usr/bin/env python3
"""
数据迁移脚本 - 从SQLite迁移到MySQL
将现有SQLite数据库中的数据迁移到MySQL数据库
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migration.log"), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# 添加项目路径到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from open_webui.internal.db import engine
    from open_webui.env import DATA_DIR
    from sqlalchemy import text
except ImportError as e:
    log.error(f"导入项目模块失败: {e}")
    sys.exit(1)


def get_sqlite_connection():
    """获取SQLite数据库连接"""
    sqlite_db_path = os.path.join(DATA_DIR, "webui.db")
    if not os.path.exists(sqlite_db_path):
        log.error(f"SQLite数据库文件不存在: {sqlite_db_path}")
        return None

    try:
        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        log.info(f"✅ 成功连接到SQLite数据库: {sqlite_db_path}")
        return conn
    except Exception as e:
        log.error(f"连接SQLite数据库失败: {e}")
        return None


def get_table_names_sqlite(sqlite_conn):
    """获取SQLite数据库中的所有表名"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        log.info(f"SQLite数据库中的表: {tables}")
        return tables
    except Exception as e:
        log.error(f"获取SQLite表名失败: {e}")
        return []


def get_table_schema_mysql(table_name):
    """获取MySQL中表的结构"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"DESCRIBE {table_name}"))
            columns = []
            for row in result:
                columns.append(
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "key": row[3],
                        "default": row[4],
                        "extra": row[5],
                    }
                )
            return columns
    except Exception as e:
        log.warning(f"获取MySQL表 {table_name} 结构失败: {e}")
        return []


def migrate_table_data(table_name):
    """迁移单个表的数据"""
    log.info(f"开始迁移表: {table_name}")

    # 获取SQLite连接
    sqlite_conn = get_sqlite_connection()
    if not sqlite_conn:
        return False

    try:
        # 检查表是否存在
        cursor = sqlite_conn.cursor()
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
        )
        if not cursor.fetchone():
            log.warning(f"SQLite中表 {table_name} 不存在")
            return True

        # 获取SQLite表中的数据
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            log.info(f"表 {table_name} 无数据需要迁移")
            return True

        log.info(f"SQLite表 {table_name} 包含 {len(rows)} 条记录")

        # 获取列名
        column_names = [description[0] for description in cursor.description]
        log.info(f"表 {table_name} 列: {column_names}")

        # 获取MySQL表结构
        mysql_columns = get_table_schema_mysql(table_name)
        if not mysql_columns:
            log.warning(f"MySQL中表 {table_name} 不存在或无法获取结构")
            return False

        mysql_column_names = [col["name"] for col in mysql_columns]
        log.info(f"MySQL表 {table_name} 列: {mysql_column_names}")

        # 准备插入语句
        placeholders = ", ".join(
            [f":{col}" for col in column_names if col in mysql_column_names]
        )
        columns_for_insert = ", ".join(
            [f"`{col}`" for col in column_names if col in mysql_column_names]
        )

        insert_sql = f"INSERT IGNORE INTO `{table_name}` ({columns_for_insert}) VALUES ({placeholders})"
        log.info(f"插入语句: {insert_sql}")

        # 迁移数据
        with engine.connect() as mysql_conn:
            trans = mysql_conn.begin()
            try:
                inserted_count = 0
                for row in rows:
                    # 构建数据字典
                    data_dict = {}
                    for i, col_name in enumerate(column_names):
                        if col_name in mysql_column_names:
                            value = row[i]
                            # 处理特殊数据类型
                            if isinstance(value, str) and value.lower() in (
                                "true",
                                "false",
                            ):
                                value = value.lower() == "true"
                            elif value is not None and col_name in [
                                "created_at",
                                "updated_at",
                                "submit_time",
                                "start_time",
                                "finish_time",
                            ]:
                                # 处理时间戳
                                if (
                                    isinstance(value, (int, float))
                                    and value > 1000000000
                                ):
                                    # 假设是时间戳
                                    try:
                                        value = datetime.fromtimestamp(
                                            value / 1000
                                            if value > 1000000000000
                                            else value
                                        )
                                    except:
                                        value = str(value)
                            data_dict[col_name] = value

                    # 执行插入
                    try:
                        mysql_conn.execute(text(insert_sql), data_dict)
                        inserted_count += 1
                    except Exception as e:
                        log.warning(f"插入记录失败: {e}, 数据: {data_dict}")

                trans.commit()
                log.info(
                    f"✅ 表 {table_name} 迁移完成，成功插入 {inserted_count} 条记录"
                )
                return True

            except Exception as e:
                trans.rollback()
                log.error(f"事务执行失败: {e}")
                return False

    except Exception as e:
        log.error(f"迁移表 {table_name} 失败: {e}")
        return False
    finally:
        if sqlite_conn:
            sqlite_conn.close()


def migrate_all_tables():
    """迁移所有表的数据"""
    log.info("开始迁移所有表数据...")

    # 获取SQLite中的所有表
    sqlite_conn = get_sqlite_connection()
    if not sqlite_conn:
        return False

    try:
        table_names = get_table_names_sqlite(sqlite_conn)

        # 按依赖关系排序表（重要的基础表先迁移）
        priority_tables = [
            "users",
            "auth",
            "config",
            "models",
            "tools",
            "functions",
            "jimeng_config",
            "jimeng_tasks",
            "jimeng_credits",
            "dreamwork_config",
            "dreamwork_tasks",
            "dreamwork_credits",
            "kling_lip_sync_config",
            "kling_lip_sync_tasks",
            "kling_lip_sync_credits",
        ]

        # 先迁移优先级高的表
        migrated_tables = []
        for table in priority_tables:
            if table in table_names:
                if migrate_table_data(table):
                    migrated_tables.append(table)
                table_names.remove(table)

        # 迁移剩余的表
        for table in table_names:
            if migrate_table_data(table):
                migrated_tables.append(table)

        log.info(
            f"🎉 数据迁移完成，共迁移 {len(migrated_tables)} 个表: {migrated_tables}"
        )
        return True

    except Exception as e:
        log.error(f"迁移所有表失败: {e}")
        return False
    finally:
        if sqlite_conn:
            sqlite_conn.close()


def validate_migration():
    """验证迁移结果"""
    log.info("开始验证迁移结果...")

    try:
        # 检查关键表的记录数
        validation_tables = ["users", "config", "jimeng_config", "dreamwork_config"]

        sqlite_conn = get_sqlite_connection()
        if not sqlite_conn:
            return False

        for table in validation_tables:
            # 获取SQLite中的记录数
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]

            # 获取MySQL中的记录数
            with engine.connect() as mysql_conn:
                result = mysql_conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                mysql_count = result.fetchone()[0]

            if sqlite_count == mysql_count:
                log.info(f"✅ 表 {table} 记录数匹配: {sqlite_count}")
            else:
                log.warning(
                    f"⚠️ 表 {table} 记录数不匹配 - SQLite: {sqlite_count}, MySQL: {mysql_count}"
                )

        sqlite_conn.close()
        log.info("✅ 迁移验证完成")
        return True

    except Exception as e:
        log.error(f"验证迁移结果失败: {e}")
        return False


def main():
    """主函数"""
    log.info("🚀 开始SQLite到MySQL数据迁移...")

    try:
        # 迁移所有表数据
        if migrate_all_tables():
            # 验证迁移结果
            validate_migration()
            log.info("🎉 数据迁移成功完成!")
            return 0
        else:
            log.error("❌ 数据迁移失败!")
            return 1

    except Exception as e:
        log.error(f"❌ 数据迁移过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
