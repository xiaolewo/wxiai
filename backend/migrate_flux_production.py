#!/usr/bin/env python3
"""
线上环境 Flux 模型积分迁移脚本
用于在生产环境中安全地添加 model_credits 列
"""

import sqlite3
import json
import os
import sys
from datetime import datetime


def backup_database(db_path):
    """备份数据库"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil

        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 数据库备份失败: {e}")
        return None


def migrate_flux_production():
    """生产环境迁移脚本"""

    # 寻找数据库文件 - 优先查找 data 目录
    db_paths = [
        "./data/webui.db",
        "/app/backend/data/webui.db",
        "/app/data/webui.db",
        "./webui.db",
        "../data/webui.db",
    ]

    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        print("❌ 未找到数据库文件")
        print("请确保在正确的目录中运行此脚本")
        print(f"搜索路径: {db_paths}")
        return False

    print(f"📁 找到数据库文件: {db_path}")

    # 备份数据库
    backup_path = backup_database(db_path)
    if not backup_path:
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查 flux_config 表是否存在
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='flux_config';
        """
        )

        if not cursor.fetchone():
            print("⚠️  flux_config 表不存在，跳过迁移")
            conn.close()
            return True

        # 检查 model_credits 列是否已存在
        cursor.execute("PRAGMA table_info(flux_config);")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 现有列: {columns}")

        if "model_credits" in columns:
            print("✅ model_credits 列已存在，无需迁移")
            conn.close()
            return True

        print("🔄 开始添加 model_credits 列...")

        # 开始事务
        cursor.execute("BEGIN TRANSACTION;")

        try:
            # 添加 model_credits 列
            cursor.execute(
                """
                ALTER TABLE flux_config 
                ADD COLUMN model_credits TEXT;
            """
            )
            print("✅ 成功添加 model_credits 列")

            # 设置默认值
            default_credits = {
                "fal-ai/flux-1/schnell": 5,
                "fal-ai/flux-1/dev": 10,
                "fal-ai/flux-1/dev/image-to-image": 10,
                "fal-ai/flux-pro": 20,
                "fal-ai/flux-pro/kontext": 25,
                "fal-ai/flux-pro/kontext/multi": 30,
                "fal-ai/flux-pro/max": 35,
            }

            cursor.execute(
                """
                UPDATE flux_config 
                SET model_credits = ? 
                WHERE model_credits IS NULL;
            """,
                (json.dumps(default_credits),),
            )

            print("✅ 设置默认模型积分配置")

            # 验证修改
            cursor.execute(
                "SELECT COUNT(*) FROM flux_config WHERE model_credits IS NOT NULL;"
            )
            updated_count = cursor.fetchone()[0]
            print(f"✅ 已更新 {updated_count} 条记录")

            # 提交事务
            cursor.execute("COMMIT;")
            print("✅ 事务提交成功")

        except Exception as e:
            # 回滚事务
            cursor.execute("ROLLBACK;")
            print(f"❌ 迁移失败，已回滚: {e}")
            return False

        finally:
            conn.close()

        # 验证迁移结果
        print("🔍 验证迁移结果...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(flux_config);")
        final_columns = [row[1] for row in cursor.fetchall()]

        if "model_credits" in final_columns:
            cursor.execute("SELECT model_credits FROM flux_config LIMIT 1;")
            sample_credits = cursor.fetchone()
            if sample_credits and sample_credits[0]:
                print("✅ 迁移验证成功")
                print(f"📋 最终列结构: {final_columns}")
                print(f"💰 示例积分配置: {sample_credits[0][:100]}...")
                conn.close()
                return True
            else:
                print("❌ 积分配置为空")
                conn.close()
                return False
        else:
            print("❌ model_credits 列未找到")
            conn.close()
            return False

    except Exception as e:
        print(f"❌ 迁移过程出错: {e}")
        return False


def main():
    print("🚀 Flux 生产环境数据库迁移")
    print("=" * 50)

    # 确认操作
    confirm = input("⚠️  这将修改生产数据库，是否继续？(yes/no): ")
    if confirm.lower() != "yes":
        print("❌ 操作已取消")
        return

    print("\n开始迁移...")
    success = migrate_flux_production()

    if success:
        print("\n🎉 迁移完成！")
        print("✅ 现在可以重启应用服务")
        print("✅ model_credits 功能将正常工作")
    else:
        print("\n💥 迁移失败！")
        print("❌ 请检查错误信息并联系技术支持")
        print("❌ 数据库备份文件可用于恢复")


if __name__ == "__main__":
    main()
