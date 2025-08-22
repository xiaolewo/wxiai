"""add_kling_lip_sync_tables

Revision ID: klz1a2b3c4d5
Revises: merge_heads_final
Create Date: 2025-01-21 15:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "klz1a2b3c4d5"
down_revision = "merge_heads_final"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级操作：添加可灵对口型功能相关表"""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # 1. 创建可灵对口型配置表
    if "kling_lip_sync_config" not in inspector.get_table_names():
        op.create_table(
            "kling_lip_sync_config",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "enabled", sa.Boolean(), default=False, comment="是否启用对口型功能"
            ),
            sa.Column(
                "base_url",
                sa.String(500),
                default="https://api.klingai.com",
                comment="API基础URL",
            ),
            sa.Column("api_key", sa.Text, comment="API密钥"),
            # 积分配置
            sa.Column(
                "credits_per_task",
                sa.Integer(),
                default=50,
                comment="每个对口型任务消耗积分",
            ),
            # API配置
            sa.Column(
                "api_path",
                sa.String(200),
                default="/kling/v1/videos/lip-sync",
                comment="API路径",
            ),
            sa.Column(
                "max_concurrent_tasks",
                sa.Integer(),
                default=3,
                comment="最大并发任务数",
            ),
            sa.Column(
                "task_timeout",
                sa.Integer(),
                default=300000,
                comment="任务超时时间(毫秒)",
            ),
            # 默认参数配置
            sa.Column(
                "default_mode", sa.String(50), default="text2video", comment="默认模式"
            ),
            sa.Column(
                "default_voice_id",
                sa.String(100),
                default="girlfriend_1_speech02",
                comment="默认音色ID",
            ),
            sa.Column(
                "default_voice_language",
                sa.String(10),
                default="zh",
                comment="默认语言",
            ),
            # 系统字段
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        print("✅ 创建 kling_lip_sync_config 表")
    else:
        print("⚠️ kling_lip_sync_config 表已存在")

    # 2. 创建可灵对口型任务表
    if "kling_lip_sync_tasks" not in inspector.get_table_names():
        op.create_table(
            "kling_lip_sync_tasks",
            sa.Column("id", sa.String(50), primary_key=True, comment="任务ID"),
            sa.Column(
                "user_id", sa.String(50), nullable=False, index=True, comment="用户ID"
            ),
            sa.Column("task_id", sa.String(100), comment="外部任务ID"),
            # 任务状态
            sa.Column("status", sa.String(50), default="submitted", comment="任务状态"),
            sa.Column("task_status_msg", sa.Text, comment="状态消息"),
            # 输入参数
            sa.Column("video_id", sa.String(100), comment="视频ID"),
            sa.Column("video_url", sa.Text, comment="视频URL"),
            sa.Column("uploaded_video_url", sa.Text, comment="上传的视频云存储URL"),
            sa.Column("mode", sa.String(50), default="text2video", comment="模式"),
            sa.Column("text", sa.Text, nullable=False, comment="对口型文本"),
            sa.Column("voice_id", sa.String(100), comment="音色ID"),
            sa.Column("voice_language", sa.String(10), comment="语言"),
            # 结果数据
            sa.Column("result_video_url", sa.Text, comment="生成结果视频URL"),
            sa.Column("cloud_result_url", sa.Text, comment="云存储结果视频URL"),
            sa.Column("fail_reason", sa.Text, comment="失败原因"),
            # 积分和时间
            sa.Column("credits_cost", sa.Integer(), default=0, comment="消耗积分"),
            sa.Column("submit_time", sa.DateTime(), comment="提交时间"),
            sa.Column("start_time", sa.DateTime(), comment="开始处理时间"),
            sa.Column("finish_time", sa.DateTime(), comment="完成时间"),
            # 请求响应数据
            sa.Column("request_data", sa.Text, comment="请求数据JSON"),
            sa.Column("response_data", sa.Text, comment="响应数据JSON"),
            # 元数据
            sa.Column("properties", sa.JSON, comment="扩展属性"),
            sa.Column("progress", sa.String(20), default="0%", comment="进度"),
            # 系统字段
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        print("✅ 创建 kling_lip_sync_tasks 表")
    else:
        print("⚠️ kling_lip_sync_tasks 表已存在")

    # 3. 创建可灵对口型积分表
    if "kling_lip_sync_credits" not in inspector.get_table_names():
        op.create_table(
            "kling_lip_sync_credits",
            sa.Column("id", sa.String(50), primary_key=True, comment="积分记录ID"),
            sa.Column(
                "user_id", sa.String(50), nullable=False, index=True, comment="用户ID"
            ),
            sa.Column("credits_balance", sa.Integer(), default=0, comment="剩余积分"),
            sa.Column("total_used", sa.Integer(), default=0, comment="总消耗积分"),
            sa.Column("total_recharged", sa.Integer(), default=0, comment="总充值积分"),
            # 系统字段
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        print("✅ 创建 kling_lip_sync_credits 表")
    else:
        print("⚠️ kling_lip_sync_credits 表已存在")

    # 4. 为任务表添加索引
    try:
        op.create_index(
            "idx_kling_lip_sync_tasks_status", "kling_lip_sync_tasks", ["status"]
        )
        op.create_index(
            "idx_kling_lip_sync_tasks_created_at",
            "kling_lip_sync_tasks",
            ["created_at"],
        )
        print("✅ 创建索引")
    except Exception as e:
        print(f"⚠️ 创建索引失败: {e}")


def downgrade() -> None:
    """降级操作：删除可灵对口型功能相关表（生产环境慎用）"""
    # 删除索引
    try:
        op.drop_index(
            "idx_kling_lip_sync_tasks_created_at", table_name="kling_lip_sync_tasks"
        )
        op.drop_index(
            "idx_kling_lip_sync_tasks_status", table_name="kling_lip_sync_tasks"
        )
    except Exception:
        pass

    # 删除表
    op.drop_table("kling_lip_sync_credits")
    op.drop_table("kling_lip_sync_tasks")
    op.drop_table("kling_lip_sync_config")
