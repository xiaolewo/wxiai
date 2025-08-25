"""update credit precision
更新积分字段精度为1位小数

Revision ID: 68ab2b32
Revises:
Create Date: 2025-08-24 23:09:38

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "68ab2b32"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级：将积分字段精度改为8位总长度，1位小数"""
    # SQLite不直接支持ALTER COLUMN，需要重新创建表

    # 对于SQLite，这个迁移主要是为了记录更改
    # 实际的精度控制在应用层面处理

    # 如果是PostgreSQL或MySQL，可以使用以下语句：
    # op.alter_column('credit', 'credit',
    #                type_=sa.Numeric(precision=8, scale=1))
    # op.alter_column('credit_log', 'credit',
    #                type_=sa.Numeric(precision=8, scale=1))
    # op.alter_column('trade_ticket', 'amount',
    #                type_=sa.Numeric(precision=8, scale=1))
    # op.alter_column('redemption_code', 'amount',
    #                type_=sa.Numeric(precision=8, scale=1))

    pass


def downgrade():
    """降级：恢复到原来的精度设置"""
    # op.alter_column('credit', 'credit',
    #                type_=sa.Numeric(precision=24, scale=12))
    # op.alter_column('credit_log', 'credit',
    #                type_=sa.Numeric(precision=24, scale=12))
    # op.alter_column('trade_ticket', 'amount',
    #                type_=sa.Numeric(precision=24, scale=12))
    # op.alter_column('redemption_code', 'amount',
    #                type_=sa.Numeric(precision=24, scale=12))

    pass
