#!/usr/bin/env python3
"""
自动执行即梦字段迁移脚本
"""

import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.abspath("."))

try:
    from open_webui.internal.db import get_db, engine
    import sqlalchemy as sa
    from sqlalchemy import text

    print("🚀 开始即梦字段迁移...")

    with get_db() as db:
        inspector = sa.inspect(db.bind)

        # 检查 jimeng_tasks 表是否存在
        if not inspector.has_table("jimeng_tasks"):
            print("❌ jimeng_tasks 表不存在，请先运行基础迁移")
            sys.exit(1)

        # 获取当前表字段
        columns = inspector.get_columns("jimeng_tasks")
        column_names = [col["name"] for col in columns]

        print(f"📋 jimeng_tasks 当前字段: {column_names}")

        # 添加 watermark 字段
        if "watermark" not in column_names:
            print("➕ 添加 watermark 字段到 jimeng_tasks...")
            try:
                db.execute(
                    text(
                        "ALTER TABLE jimeng_tasks ADD COLUMN watermark BOOLEAN NOT NULL DEFAULT FALSE"
                    )
                )
                db.commit()
                print("✅ watermark 字段添加成功")
            except Exception as e:
                print(f"❌ 添加 watermark 字段失败: {e}")
                db.rollback()
        else:
            print("⚠️  watermark 字段已存在，跳过")

        # 添加 cloud_video_url 字段
        if "cloud_video_url" not in column_names:
            print("➕ 添加 cloud_video_url 字段到 jimeng_tasks...")
            try:
                db.execute(
                    text("ALTER TABLE jimeng_tasks ADD COLUMN cloud_video_url TEXT")
                )
                db.commit()
                print("✅ cloud_video_url 字段添加成功")
            except Exception as e:
                print(f"❌ 添加 cloud_video_url 字段失败: {e}")
                db.rollback()
        else:
            print("⚠️  cloud_video_url 字段已存在，跳过")

        # 检查 jimeng_config 表
        if inspector.has_table("jimeng_config"):
            config_columns = inspector.get_columns("jimeng_config")
            config_column_names = [col["name"] for col in config_columns]

            print(f"📋 jimeng_config 当前字段: {config_column_names}")

            # 添加 default_watermark 字段
            if "default_watermark" not in config_column_names:
                print("➕ 添加 default_watermark 字段到 jimeng_config...")
                try:
                    db.execute(
                        text(
                            "ALTER TABLE jimeng_config ADD COLUMN default_watermark BOOLEAN NOT NULL DEFAULT FALSE"
                        )
                    )
                    db.commit()
                    print("✅ default_watermark 字段添加成功")
                except Exception as e:
                    print(f"❌ 添加 default_watermark 字段失败: {e}")
                    db.rollback()
            else:
                print("⚠️  default_watermark 字段已存在，跳过")
        else:
            print("⚠️  jimeng_config 表不存在，跳过配置表字段添加")

        # 验证迁移结果
        print("\n🔍 验证迁移结果...")
        updated_columns = inspector.get_columns("jimeng_tasks")
        updated_column_names = [col["name"] for col in updated_columns]

        print(f"📋 jimeng_tasks 更新后字段: {updated_column_names}")

        if (
            "watermark" in updated_column_names
            and "cloud_video_url" in updated_column_names
        ):
            print("✅ 即梦字段迁移完成！所有必需字段都已添加。")
        else:
            print("❌ 迁移未完全成功，某些字段可能缺失。")

        print("\n🎉 迁移执行完毕！")

except Exception as e:
    print(f"❌ 迁移执行失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
