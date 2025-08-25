"""update credit to integer
将积分字段改为纯整数（去除小数点）

Revision ID: 68ab2be4
Revises:
Create Date: 2025-08-24 23:12:36
"""

from alembic import op
import sqlalchemy as sa

revision = "68ab2be4"
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
