#!/usr/bin/env python3
"""
执行积分系统迁移脚本
将积分字段从小数精度改为整数精度，并迁移现有数据
"""
import os
import sys
import sqlite3
from pathlib import Path
from decimal import Decimal
import math

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# 导入配置
from open_webui.env import DATABASE_URL, DATA_DIR
from open_webui.internal.db import get_db


def backup_database():
    """备份数据库"""
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        backup_path = db_path + ".credit_migration_backup"

        print(f"📋 备份数据库到: {backup_path}")

        # 使用sqlite3备份
        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(backup_path)
        source.backup(backup)
        source.close()
        backup.close()

        print("✅ 数据库备份完成")
        return backup_path
    else:
        print("⚠️  非SQLite数据库，跳过备份")
        return None


def get_tables_with_credit_columns():
    """获取包含积分相关字段的表"""
    return [
        ("credit", "credit"),
        ("credit_log", "credit"),
        ("trade_ticket", "amount"),
        ("redemption_code", "amount"),
    ]


def migrate_credit_precision():
    """迁移积分字段精度"""
    print("🔄 开始执行积分精度迁移...")

    try:
        with get_db() as db:
            # 检查数据库引擎
            if "sqlite" in DATABASE_URL.lower():
                print("📊 检测到SQLite数据库，使用SQLite迁移策略")
                migrate_sqlite_credit_precision(db)
            else:
                print("📊 检测到非SQLite数据库，使用标准SQL迁移")
                migrate_standard_credit_precision(db)

    except Exception as e:
        print(f"❌ 迁移过程中出现错误: {e}")
        print("💡 请检查数据库备份并手动回滚")
        return False

    return True


def migrate_sqlite_credit_precision(db):
    """SQLite数据库迁移策略"""
    from sqlalchemy import text

    tables = get_tables_with_credit_columns()

    for table_name, column_name in tables:
        print(f"📋 处理表: {table_name}.{column_name}")

        # 检查表是否存在
        result = db.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
            ),
            {"table_name": table_name},
        ).fetchone()

        if not result:
            print(f"⏭️  表 {table_name} 不存在，跳过")
            continue

        try:
            # 检查字段是否存在
            cursor = db.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in cursor.fetchall()]

            if column_name not in columns:
                print(f"⏭️  字段 {table_name}.{column_name} 不存在，跳过")
                continue

            # 获取现有数据并转换为整数
            print(f"🔄 转换 {table_name}.{column_name} 数据...")

            # 查询现有数据
            cursor = db.execute(text(f"SELECT rowid, {column_name} FROM {table_name}"))
            rows = cursor.fetchall()

            # 更新每一行数据，将小数转换为整数
            for row_id, current_value in rows:
                if current_value is not None:
                    # 转换为整数
                    if isinstance(current_value, (int, float)):
                        new_value = int(round(float(current_value)))
                    else:
                        try:
                            new_value = int(round(float(str(current_value))))
                        except (ValueError, TypeError):
                            new_value = 0

                    # 更新数据
                    db.execute(
                        text(
                            f"UPDATE {table_name} SET {column_name} = :new_value WHERE rowid = :row_id"
                        ),
                        {"new_value": new_value, "row_id": row_id},
                    )

            print(f"✅ 表 {table_name}.{column_name} 数据转换完成")

        except Exception as e:
            print(f"❌ 处理表 {table_name} 时出错: {e}")
            raise e

    # 提交所有更改
    db.commit()
    print("✅ SQLite 积分精度迁移完成")


def migrate_standard_credit_precision(db):
    """标准SQL数据库迁移策略（PostgreSQL, MySQL等）"""
    tables = get_tables_with_credit_columns()

    for table_name, column_name in tables:
        print(f"📋 处理表: {table_name}.{column_name}")

        try:
            # 先更新数据（四舍五入为整数）
            print(f"🔄 转换 {table_name}.{column_name} 数据...")
            db.execute(
                f"""
                UPDATE {table_name} 
                SET {column_name} = ROUND({column_name}, 0)
                WHERE {column_name} IS NOT NULL
            """
            )

            # 然后更改字段类型
            print(f"🔧 更改 {table_name}.{column_name} 字段类型...")
            db.execute(
                f"""
                ALTER TABLE {table_name} 
                ALTER COLUMN {column_name} TYPE NUMERIC(8, 0)
            """
            )

            print(f"✅ 表 {table_name}.{column_name} 迁移完成")

        except Exception as e:
            print(f"❌ 处理表 {table_name} 时出错: {e}")
            raise e

    # 提交所有更改
    db.commit()
    print("✅ 标准SQL 积分精度迁移完成")


def verify_migration():
    """验证迁移结果"""
    print("🔍 验证迁移结果...")

    try:
        from sqlalchemy import text

        with get_db() as db:
            tables = get_tables_with_credit_columns()

            for table_name, column_name in tables:
                # 检查表是否存在
                if "sqlite" in DATABASE_URL.lower():
                    result = db.execute(
                        text(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
                        ),
                        {"table_name": table_name},
                    ).fetchone()

                    if not result:
                        print(f"⏭️  表 {table_name} 不存在，跳过验证")
                        continue

                    # 检查数据样本
                    cursor = db.execute(
                        text(f"SELECT {column_name} FROM {table_name} LIMIT 5")
                    )
                    samples = cursor.fetchall()

                    print(
                        f"📊 {table_name}.{column_name} 样本数据: {[row[0] for row in samples]}"
                    )

                    # 检查是否都是整数
                    for sample in samples:
                        value = sample[0]
                        if (
                            value is not None
                            and not isinstance(value, int)
                            and "." in str(value)
                        ):
                            print(f"⚠️  发现非整数值: {value}")
                        else:
                            print(f"✅ 验证通过: {value}")

        print("✅ 迁移验证完成")
        return True

    except Exception as e:
        print(f"❌ 验证过程中出现错误: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始执行积分系统数据库迁移")
    print(f"📍 数据库URL: {DATABASE_URL}")
    print(f"📁 数据目录: {DATA_DIR}")

    # 1. 备份数据库
    backup_path = backup_database()

    try:
        # 2. 执行迁移
        success = migrate_credit_precision()

        if not success:
            print("❌ 迁移失败")
            return 1

        # 3. 验证迁移结果
        if not verify_migration():
            print("❌ 迁移验证失败")
            return 1

        print("🎉 积分系统数据库迁移成功完成!")
        print("💡 所有积分相关字段已转换为整数格式")

        if backup_path:
            print(f"📋 数据库备份保存在: {backup_path}")

        return 0

    except KeyboardInterrupt:
        print("\n⏹️  迁移被用户中断")
        return 1
    except Exception as e:
        print(f"❌ 迁移过程中出现未预期错误: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
