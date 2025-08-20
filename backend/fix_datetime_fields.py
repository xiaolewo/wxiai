#!/usr/bin/env python3
"""
修复数据库时间字段问题
解决NOT NULL约束和默认值问题
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from open_webui.internal.db import get_db
from sqlalchemy import text
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_datetime_fields():
    """修复各表的时间字段问题"""

    with get_db() as db:
        try:
            logger.info("开始修复数据库时间字段...")

            # 1. 修复DreamWork表
            logger.info("修复DreamWork表...")

            # 先为NULL的记录设置当前时间
            result = db.execute(
                text(
                    """
                UPDATE dreamwork_tasks 
                SET created_at = datetime('now'), updated_at = datetime('now')
                WHERE created_at IS NULL OR updated_at IS NULL
            """
                )
            )
            logger.info(f"更新了 {result.rowcount} 条DreamWork记录")

            # 检查表结构是否需要添加约束
            # SQLite不支持直接修改列约束，所以我们确保代码层面正确处理

            # 2. 检查其他表
            tables_to_check = ["jimeng_tasks", "kling_tasks", "flux_tasks"]

            for table in tables_to_check:
                try:
                    result = db.execute(
                        text(
                            f"""
                        UPDATE {table}
                        SET created_at = datetime('now'), updated_at = datetime('now')
                        WHERE created_at IS NULL OR updated_at IS NULL
                    """
                        )
                    )
                    if result.rowcount > 0:
                        logger.info(f"更新了 {result.rowcount} 条{table}记录")
                except Exception as e:
                    logger.warning(f"处理表 {table} 时出错: {e}")
                    continue

            # 3. 提交更改
            db.commit()
            logger.info("✅ 数据库时间字段修复完成")

            # 4. 验证修复结果
            logger.info("验证修复结果...")

            result = db.execute(
                text(
                    """
                SELECT COUNT(*) as count FROM dreamwork_tasks 
                WHERE created_at IS NULL OR updated_at IS NULL
            """
                )
            )
            null_count = result.fetchone()[0]

            if null_count == 0:
                logger.info("✅ DreamWork表无NULL时间字段")
            else:
                logger.warning(f"⚠️ DreamWork表仍有 {null_count} 条记录的时间字段为NULL")

        except Exception as e:
            logger.error(f"❌ 修复过程中出错: {e}")
            db.rollback()
            raise


if __name__ == "__main__":
    print("🔧 开始修复数据库时间字段问题...")
    fix_datetime_fields()
    print("🏁 修复完成")
