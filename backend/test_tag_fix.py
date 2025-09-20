#!/usr/bin/env python3
"""
测试tag表meta列修复
验证tag表meta列缺失问题是否已解决
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def test_tag_meta_fix():
    """测试tag表meta列修复是否能正常运行"""
    try:
        print("🔧 开始测试tag表meta列修复...")

        # 尝试导入和初始化配置
        from open_webui.config import run_migrations

        print("✅ 配置模块导入成功")

        # 运行迁移
        print("🚀 开始运行数据库迁移...")
        run_migrations()

        print("✅ 数据库迁移完成，没有发生错误")

        # 验证tag模型能够正常导入
        from open_webui.models.tags import Tag, TagTable, Tags

        print("✅ Tag 模型导入成功")

        # 验证数据库连接和tag表结构
        try:
            from open_webui.internal.db import get_db
            from sqlalchemy import inspect

            with get_db() as db:
                print("✅ 数据库连接测试成功")

                # 检查tag表结构
                inspector = inspect(db.bind)

                if inspector.has_table("tag"):
                    columns = inspector.get_columns("tag")
                    column_names = [col["name"] for col in columns]
                    print(f"✅ Tag表列: {column_names}")

                    if "meta" in column_names:
                        print("✅ Tag表meta列存在")

                        # 尝试执行一个简单的查询来确保功能正常
                        try:
                            tags = Tags.get_tags_by_user_id("test_user_id")
                            print("✅ Tag查询功能测试成功")
                        except Exception as query_error:
                            print(f"⚠️  Tag查询功能测试警告: {query_error}")

                    else:
                        print("❌ Tag表meta列仍然缺失")
                        return False
                else:
                    print("❌ Tag表不存在")
                    return False

        except Exception as db_error:
            print(f"⚠️  数据库验证警告: {db_error}")
            return False

        print("🎉 Tag表meta列修复测试完成！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_tag_meta_fix()
    sys.exit(0 if success else 1)
