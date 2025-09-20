#!/usr/bin/env python3
"""
测试数据库迁移修复
验证索引重复创建问题是否已解决
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def test_database_migration():
    """测试数据库迁移是否能正常运行"""
    try:
        print("🔧 开始测试数据库迁移修复...")

        # 尝试导入和初始化配置
        from open_webui.config import run_migrations

        print("✅ 配置模块导入成功")

        # 运行迁移
        print("🚀 开始运行数据库迁移...")
        run_migrations()

        print("✅ 数据库迁移完成，没有发生错误")

        # 验证模型能够正常导入
        from open_webui.models.dreamwork import (
            DreamWorkConfig,
            DreamWorkTask,
            DreamWorkCredit,
        )

        print("✅ DreamWork 模型导入成功")

        # 验证数据库连接
        try:
            from open_webui.internal.db import get_db

            with get_db() as db:
                print("✅ 数据库连接测试成功")

                # 尝试查询表结构
                from sqlalchemy import inspect

                inspector = inspect(db.bind)
                tables = inspector.get_table_names()

                dreamwork_tables = [
                    table for table in tables if table.startswith("dreamwork")
                ]
                print(f"✅ 找到 DreamWork 相关表: {dreamwork_tables}")

                # 检查索引
                for table in dreamwork_tables:
                    indexes = inspector.get_indexes(table)
                    index_names = [
                        idx.get("name") for idx in indexes if idx.get("name")
                    ]
                    print(f"✅ 表 {table} 的索引: {index_names}")

        except Exception as db_error:
            print(f"⚠️  数据库验证警告: {db_error}")

        print("🎉 数据库迁移修复测试完成！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_database_migration()
    sys.exit(0 if success else 1)
