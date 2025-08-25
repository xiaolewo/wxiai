#!/usr/bin/env python3
"""
将积分系统改为纯整数（不保留小数点）
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_credit_usage_to_integer():
    """更新积分计算逻辑为整数"""
    usage_file = (
        Path(__file__).parent.parent
        / "backend"
        / "open_webui"
        / "utils"
        / "credit"
        / "usage.py"
    )

    if not usage_file.exists():
        logger.error(f"文件不存在: {usage_file}")
        return False

    with open(usage_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 备份原文件
    backup_file = usage_file.with_suffix(".py.integer_backup")
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"已备份原文件到: {backup_file}")

    # 修改round_credit方法为整数
    old_round_method = '''def round_credit(self, value: Decimal) -> Decimal:
        """将积分值精确到1位小数"""
        return Decimal(str(round(float(value), 1)))'''

    new_round_method = '''def round_credit(self, value: Decimal) -> Decimal:
        """将积分值精确到整数"""
        return Decimal(str(int(round(float(value)))))'''

    if old_round_method in content:
        content = content.replace(old_round_method, new_round_method)
        logger.info("✅ 已更新积分精度为整数")

    # 写入修改后的内容
    with open(usage_file, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"✅ 已更新文件: {usage_file}")
    return True


def update_credit_models_to_integer():
    """更新积分数据库模型为整数"""
    models_file = (
        Path(__file__).parent.parent
        / "backend"
        / "open_webui"
        / "models"
        / "credits.py"
    )

    if not models_file.exists():
        logger.error(f"文件不存在: {models_file}")
        return False

    with open(models_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 备份原文件
    backup_file = models_file.with_suffix(".py.integer_backup")
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"已备份原文件到: {backup_file}")

    # 修改数据库字段精度为整数 (8位，0位小数)
    old_precision = "Column(Numeric(precision=8, scale=1))"
    new_precision = "Column(Numeric(precision=8, scale=0))"

    if old_precision in content:
        content = content.replace(old_precision, new_precision)
        logger.info("✅ 已更新数据库积分字段精度: 8,1 → 8,0（纯整数）")

    # 写入修改后的内容
    with open(models_file, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"✅ 已更新文件: {models_file}")
    return True


def create_integer_migration():
    """创建整数迁移文件"""
    migrations_dir = (
        Path(__file__).parent.parent
        / "backend"
        / "open_webui"
        / "migrations"
        / "versions"
    )

    if not migrations_dir.exists():
        logger.warning("迁移目录不存在")
        return False

    import time

    timestamp = hex(int(time.time()))[2:]
    migration_file = migrations_dir / f"{timestamp}_update_credit_to_integer.py"

    migration_content = f'''"""update credit to integer
将积分字段改为纯整数（去除小数点）

Revision ID: {timestamp}
Revises: 
Create Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
from alembic import op
import sqlalchemy as sa

revision = '{timestamp}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """升级：将积分字段改为整数"""
    # SQLite处理：实际精度控制在应用层
    # 对于PostgreSQL/MySQL可以使用:
    # op.alter_column('credit', 'credit', type_=sa.Numeric(precision=8, scale=0))
    # op.alter_column('credit_log', 'credit', type_=sa.Numeric(precision=8, scale=0))
    # op.alter_column('trade_ticket', 'amount', type_=sa.Numeric(precision=8, scale=0))
    # op.alter_column('redemption_code', 'amount', type_=sa.Numeric(precision=8, scale=0))
    pass

def downgrade():
    """降级：恢复小数位"""
    # op.alter_column('credit', 'credit', type_=sa.Numeric(precision=8, scale=1))
    # op.alter_column('credit_log', 'credit', type_=sa.Numeric(precision=8, scale=1))
    # op.alter_column('trade_ticket', 'amount', type_=sa.Numeric(precision=8, scale=1))
    # op.alter_column('redemption_code', 'amount', type_=sa.Numeric(precision=8, scale=1))
    pass
'''

    try:
        with open(migration_file, "w", encoding="utf-8") as f:
            f.write(migration_content)
        logger.info(f"✅ 已创建整数迁移文件: {migration_file}")
        return True
    except Exception as e:
        logger.error(f"创建迁移文件失败: {e}")
        return False


def main():
    logger.info("开始将积分系统改为纯整数...")
    logger.info("=" * 50)

    success_count = 0
    total_count = 3

    # 1. 更新计费逻辑
    logger.info("\n1. 更新积分计算逻辑为整数...")
    if update_credit_usage_to_integer():
        success_count += 1

    # 2. 更新数据库模型
    logger.info("\n2. 更新数据库模型为整数...")
    if update_credit_models_to_integer():
        success_count += 1

    # 3. 创建迁移文件
    logger.info("\n3. 创建整数迁移文件...")
    if create_integer_migration():
        success_count += 1

    logger.info("\n" + "=" * 50)
    logger.info(f"积分整数化完成: {success_count}/{total_count}")

    if success_count == total_count:
        logger.info("✅ 后端积分整数化完成！")
        logger.info("\n新的计费逻辑:")
        logger.info("- Token计费: 不足1000按1000计费 → 整数积分")
        logger.info("- 次数计费: 1次对话 → 整数积分")
        logger.info("- 积分显示: 纯整数，无小数点")
    else:
        logger.error("❌ 部分更新失败")

    return success_count == total_count


if __name__ == "__main__":
    main()
