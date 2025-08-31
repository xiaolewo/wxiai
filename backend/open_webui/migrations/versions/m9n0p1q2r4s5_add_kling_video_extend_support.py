"""add kling video extend support

Revision ID: m9n0p1q2r4s5
Revises: l8m9n0p1q2r3
Create Date: 2025-08-31 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "m9n0p1q2r4s5"
down_revision: Union[str, None] = "l8m9n0p1q2r3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加可灵视频延长功能支持字段"""
    
    # 1. 扩展 kling_config 表 - 添加视频延长积分配置
    op.add_column(
        "kling_config",
        sa.Column("credits_per_extend", sa.Integer(), nullable=True, default=30)
    )
    
    # 2. 扩展 kling_tasks 表 - 添加延长相关字段
    op.add_column(
        "kling_tasks",
        sa.Column("parent_task_id", sa.String(length=50), nullable=True)
    )
    
    op.add_column(
        "kling_tasks", 
        sa.Column("is_extended", sa.Boolean(), nullable=False, default=False)
    )
    
    op.add_column(
        "kling_tasks",
        sa.Column("original_duration", sa.String(length=10), nullable=True)  
    )
    
    op.add_column(
        "kling_tasks",
        sa.Column("extend_count", sa.Integer(), nullable=False, default=0)
    )
    
    # 3. 添加外键约束 - 父任务关联
    op.create_foreign_key(
        "fk_kling_tasks_parent_task_id",
        "kling_tasks", 
        "kling_tasks",
        ["parent_task_id"], 
        ["id"],
        ondelete="SET NULL"
    )
    
    # 4. 添加索引提升查询性能
    op.create_index(
        op.f("ix_kling_tasks_parent_task_id"),
        "kling_tasks", 
        ["parent_task_id"]
    )
    
    op.create_index(
        op.f("ix_kling_tasks_is_extended"),
        "kling_tasks",
        ["is_extended"]  
    )
    
    # 5. 添加复合索引 - 延长任务查询优化
    op.create_index(
        op.f("ix_kling_tasks_user_extended"),
        "kling_tasks",
        ["user_id", "is_extended", "created_at"]
    )


def downgrade() -> None:
    """回滚视频延长功能字段"""
    
    # 删除索引
    op.drop_index(op.f("ix_kling_tasks_user_extended"), table_name="kling_tasks")
    op.drop_index(op.f("ix_kling_tasks_is_extended"), table_name="kling_tasks") 
    op.drop_index(op.f("ix_kling_tasks_parent_task_id"), table_name="kling_tasks")
    
    # 删除外键约束
    op.drop_constraint("fk_kling_tasks_parent_task_id", "kling_tasks", type_="foreignkey")
    
    # 删除字段
    op.drop_column("kling_tasks", "extend_count")
    op.drop_column("kling_tasks", "original_duration")
    op.drop_column("kling_tasks", "is_extended")
    op.drop_column("kling_tasks", "parent_task_id")
    op.drop_column("kling_config", "credits_per_extend")