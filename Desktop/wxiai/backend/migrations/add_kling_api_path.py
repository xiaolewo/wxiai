"""
数据库迁移：为可灵配置表添加API路径字段
Migration: Add detected_api_path column to kling_config table
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from open_webui.internal.db import get_db
from sqlalchemy import text


def migrate_kling_api_path():
    """为可灵配置表添加detected_api_path字段"""

    try:
        with get_db() as db:
            # 检查表是否存在
            result = db.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='kling_config'"
                )
            )
            if not result.fetchone():
                print("ℹ️ kling_config 表不存在，跳过迁移")
                return True

            # 检查字段是否已存在
            result = db.execute(text("PRAGMA table_info(kling_config)"))
            columns = [row[1] for row in result.fetchall()]

            if "detected_api_path" not in columns:
                print("🔧 添加 detected_api_path 字段到 kling_config 表...")
                db.execute(
                    text(
                        """
                    ALTER TABLE kling_config 
                    ADD COLUMN detected_api_path VARCHAR(200)
                """
                    )
                )
                db.commit()
                print("✅ detected_api_path 字段添加成功")
            else:
                print("ℹ️ detected_api_path 字段已存在，跳过迁移")

        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 开始可灵API路径字段迁移...")
    success = migrate_kling_api_path()
    if success:
        print("🎉 迁移完成！")
    else:
        print("💥 迁移失败！")
        sys.exit(1)
