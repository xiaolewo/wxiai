"""Unified complete migration - 统一完整迁移

Revision ID: unified_complete_migration_20250902
Revises: z9x8c7v6b5n4
Create Date: 2025-09-02 15:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text, func

# revision identifiers, used by Alembic.
revision = "unified_complete_migration_20250902"
down_revision = "z9x8c7v6b5n4"
branch_labels = None
depends_on = None


def table_exists(connection, table_name):
    """检查表是否存在"""
    result = connection.execute(
        text(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        )
    )
    return result.fetchone() is not None


def column_exists(connection, table_name, column_name):
    """检查列是否存在"""
    if not table_exists(connection, table_name):
        return False
    result = connection.execute(text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def upgrade():
    """升级数据库到完整状态"""
    connection = op.get_bind()

    # ========== AI服务配置表 ==========

    # 1. Google Images配置表
    if not table_exists(connection, "google_images_config"):
        op.create_table(
            "google_images_config",
            sa.Column("id", sa.String(255), primary_key=True, default="default"),
            sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
            sa.Column(
                "base_url",
                sa.String(500),
                nullable=False,
                default="https://api.googleimages.ai",
            ),
            sa.Column("api_key", sa.Text()),
            sa.Column("default_model", sa.String(100), default="nano-banana"),
            sa.Column("max_images_per_request", sa.Integer(), default=10),
            sa.Column("timeout", sa.Integer(), default=120),
            sa.Column("credits_per_generation", sa.Integer(), default=20),
            sa.Column("credits_per_image", sa.Integer(), default=5),
            sa.Column("additional_config", sa.Text(), default="{}"),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
        )
        # 插入默认配置
        connection.execute(
            text(
                """
            INSERT INTO google_images_config (id, enabled, base_url, api_key, default_model, max_images_per_request, timeout, credits_per_generation, credits_per_image, additional_config, created_at, updated_at)
            VALUES ('default', 0, 'https://api.googleimages.ai', '', 'nano-banana', 10, 120, 20, 5, '{}', datetime('now'), datetime('now'))
        """
            )
        )

    # 2. Veo配置表
    if not table_exists(connection, "veo_config"):
        op.create_table(
            "veo_config",
            sa.Column("id", sa.String(255), primary_key=True, default="default"),
            sa.Column(
                "base_url", sa.String(500), nullable=False, default="https://api.veo.ai"
            ),
            sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
            sa.Column("api_key", sa.Text()),
            sa.Column("model_credits_config", sa.JSON()),
            sa.Column("query_interval", sa.Integer(), nullable=False, default=15000),
            sa.Column(
                "default_enhance_prompt", sa.Boolean(), nullable=False, default=True
            ),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
        )
        connection.execute(
            text(
                """
            INSERT INTO veo_config (id, base_url, enabled, api_key, model_credits_config, query_interval, default_enhance_prompt, created_at, updated_at)
            VALUES ('default', 'https://api.veo.ai', 0, '', '{}', 15000, 1, datetime('now'), datetime('now'))
        """
            )
        )

    # 3. ComfyUI配置表
    if not table_exists(connection, "comfyui_config"):
        op.create_table(
            "comfyui_config",
            sa.Column("id", sa.String(255), primary_key=True, default="default"),
            sa.Column("access_key", sa.Text(), nullable=False),
            sa.Column("secret_key", sa.Text(), nullable=False),
            sa.Column(
                "base_url",
                sa.String(500),
                nullable=False,
                default="https://openapi.liblibai.cloud",
            ),
            sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
            sa.Column("timeout", sa.Integer(), nullable=False, default=300),
            sa.Column("max_concurrent_tasks", sa.Integer(), nullable=False, default=5),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
        )
        connection.execute(
            text(
                """
            INSERT INTO comfyui_config (id, access_key, secret_key, base_url, enabled, timeout, max_concurrent_tasks, created_at, updated_at)
            VALUES ('default', '', '', 'https://openapi.liblibai.cloud', 0, 300, 5, datetime('now'), datetime('now'))
        """
            )
        )

    # ComfyUI工作流表
    if not table_exists(connection, "comfyui_workflows"):
        op.create_table(
            "comfyui_workflows",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("template_uuid", sa.String(255), nullable=False),
            sa.Column("workflow_uuid", sa.String(255), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("category", sa.String(100)),
            sa.Column("preview_image", sa.Text()),
            sa.Column("parameter_schema", sa.JSON(), nullable=False),
            sa.Column("default_params", sa.JSON()),
            sa.Column("base_credits", sa.Integer(), nullable=False, default=10),
            sa.Column("complexity_multiplier", sa.Float(), nullable=False, default=1.0),
            sa.Column("enabled", sa.Boolean(), nullable=False, default=True),
            sa.Column("is_public", sa.Boolean(), nullable=False, default=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, default=0),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
        )

    # 4. 云存储配置表
    if not table_exists(connection, "cloud_storage_config"):
        op.create_table(
            "cloud_storage_config",
            sa.Column("id", sa.String(255), primary_key=True, default="default"),
            sa.Column("provider", sa.String(50), nullable=False, default="tencent-cos"),
            sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
            sa.Column("secret_id", sa.Text()),
            sa.Column("secret_key", sa.Text()),
            sa.Column("region", sa.String(50), default="ap-beijing"),
            sa.Column("bucket", sa.String(255)),
            sa.Column("domain", sa.String(500)),
            sa.Column("auto_upload", sa.Boolean(), nullable=False, default=True),
            sa.Column("allowed_types", sa.JSON()),
            sa.Column("max_file_size", sa.Integer(), default=104857600),
            sa.Column("base_path", sa.String(255), default="generated/"),
            sa.Column("image_path", sa.String(255), default="images/"),
            sa.Column("video_path", sa.String(255), default="videos/"),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
        )
        connection.execute(
            text(
                """
            INSERT INTO cloud_storage_config (id, provider, enabled, secret_id, secret_key, region, bucket, domain, auto_upload, allowed_types, max_file_size, base_path, image_path, video_path, created_at, updated_at)
            VALUES ('default', 'tencent-cos', 0, '', '', 'ap-beijing', '', '', 1, '["image/*", "video/*"]', 104857600, 'generated/', 'images/', 'videos/', datetime('now'), datetime('now'))
        """
            )
        )

    # 5. DreamWork配置表
    if not table_exists(connection, "dreamwork_config"):
        op.create_table(
            "dreamwork_config",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("enabled", sa.Boolean(), default=False),
            sa.Column("base_url", sa.String(500)),
            sa.Column("api_key", sa.Text()),
            sa.Column(
                "text_to_image_model",
                sa.String(100),
                default="doubao-seedream-3-0-t2i-250415",
            ),
            sa.Column(
                "image_to_image_model",
                sa.String(100),
                default="doubao-seededit-3-0-i2i-250628",
            ),
            sa.Column("default_size", sa.String(20), default="1024x1024"),
            sa.Column("default_guidance_scale", sa.Float(), default=2.5),
            sa.Column("watermark_enabled", sa.Boolean(), default=True),
            sa.Column("created_at", sa.Text()),
            sa.Column("updated_at", sa.Text()),
        )
        connection.execute(
            text(
                """
            INSERT INTO dreamwork_config (id, enabled, base_url, api_key, text_to_image_model, image_to_image_model, default_size, default_guidance_scale, watermark_enabled, created_at, updated_at)
            VALUES (1, 0, '', '', 'doubao-seedream-3-0-t2i-250415', 'doubao-seededit-3-0-i2i-250628', '1024x1024', 2.5, 1, datetime('now'), datetime('now'))
        """
            )
        )

    # 6. MidJourney配置表
    if not table_exists(connection, "mj_config"):
        op.create_table(
            "mj_config",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("enabled", sa.Boolean(), default=False),
            sa.Column("base_url", sa.String(500)),
            sa.Column("api_key", sa.Text()),
            sa.Column("modes", sa.JSON()),
            sa.Column("default_mode", sa.String(50), default="fast"),
            sa.Column("max_concurrent_tasks", sa.Integer(), default=3),
            sa.Column("task_timeout", sa.Integer(), default=600000),
            sa.Column("created_at", sa.Text()),
            sa.Column("updated_at", sa.Text()),
        )
        connection.execute(
            text(
                """
            INSERT INTO mj_config (id, enabled, base_url, api_key, modes, default_mode, max_concurrent_tasks, task_timeout, created_at, updated_at)
            VALUES (1, 0, '', '', '{"turbo": {"enabled": true, "credits": 10}, "fast": {"enabled": true, "credits": 5}, "relax": {"enabled": true, "credits": 2}}', 'fast', 3, 600000, datetime('now'), datetime('now'))
        """
            )
        )

    # 7. Kling配置表
    if not table_exists(connection, "kling_config"):
        op.create_table(
            "kling_config",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("enabled", sa.Boolean(), default=False),
            sa.Column("base_url", sa.String(500), default="https://api.klingai.com"),
            sa.Column("api_key", sa.Text()),
            sa.Column("text_to_video_model", sa.String(100), default="kling-v1"),
            sa.Column("image_to_video_model", sa.String(100), default="kling-v1"),
            sa.Column("default_mode", sa.String(20), default="std"),
            sa.Column("default_duration", sa.String(10), default="5"),
            sa.Column("default_aspect_ratio", sa.String(20), default="16:9"),
            sa.Column("created_at", sa.Text()),
            sa.Column("updated_at", sa.Text()),
        )
        connection.execute(
            text(
                """
            INSERT INTO kling_config (id, enabled, base_url, api_key, text_to_video_model, image_to_video_model, default_mode, default_duration, default_aspect_ratio, created_at, updated_at)
            VALUES (1, 0, 'https://api.klingai.com', '', 'kling-v1', 'kling-v1', 'std', '5', '16:9', datetime('now'), datetime('now'))
        """
            )
        )

    # 8. Flux配置表
    if not table_exists(connection, "flux_config"):
        op.create_table(
            "flux_config",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("api_key", sa.Text(), nullable=False),
            sa.Column(
                "base_url",
                sa.String(500),
                nullable=False,
                default="https://queue.fal.run",
            ),
            sa.Column("enabled", sa.Boolean(), nullable=False, default=True),
            sa.Column("timeout", sa.Integer(), nullable=False, default=300),
            sa.Column("max_concurrent_tasks", sa.Integer(), nullable=False, default=5),
            sa.Column(
                "default_model",
                sa.String(100),
                nullable=False,
                default="fal-ai/flux-1/dev",
            ),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
        )
        connection.execute(
            text(
                """
            INSERT INTO flux_config (id, api_key, base_url, enabled, timeout, max_concurrent_tasks, default_model, created_at, updated_at)
            VALUES ('default', '', 'https://queue.fal.run', 1, 300, 5, 'fal-ai/flux-1/dev', datetime('now'), datetime('now'))
        """
            )
        )

    # ========== 基础任务表创建 ==========

    # 1. DreamWork任务表
    if not table_exists(connection, "dreamwork_tasks"):
        op.create_table(
            "dreamwork_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=True, index=True),
            sa.Column("action", sa.String(50), nullable=True),
            sa.Column("status", sa.String(50), nullable=True),
            sa.Column("prompt", sa.Text, nullable=True),
            sa.Column("model", sa.String(100), nullable=True),
            sa.Column("size", sa.String(20), nullable=True),
            sa.Column("guidance_scale", sa.Float, nullable=True),
            sa.Column("seed", sa.Integer, nullable=True),
            sa.Column("watermark", sa.Boolean, nullable=True),
            sa.Column("input_image", sa.Text, nullable=True),
            sa.Column("credits_cost", sa.Integer, nullable=True),
            sa.Column("submit_time", sa.DateTime, nullable=True),
            sa.Column("start_time", sa.DateTime, nullable=True),
            sa.Column("finish_time", sa.DateTime, nullable=True),
            sa.Column("progress", sa.String(20), nullable=True),
            sa.Column("image_url", sa.Text, nullable=True),
            sa.Column("fail_reason", sa.Text, nullable=True),
            sa.Column("properties", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=True),
            sa.Column("updated_at", sa.DateTime, nullable=True),
            sa.Column("cloud_image_url", sa.Text, nullable=True),
            sa.Column("serviceType", sa.String(50), nullable=True),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
        )
        # 添加索引
        op.create_index(
            "idx_dreamwork_user_created", "dreamwork_tasks", ["user_id", "created_at"]
        )
        op.create_index(
            "idx_dreamwork_status_updated", "dreamwork_tasks", ["status", "updated_at"]
        )

    # 2. MidJourney任务表
    if not table_exists(connection, "mj_tasks"):
        op.create_table(
            "mj_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=True, index=True),
            sa.Column("action", sa.String(50), nullable=True),
            sa.Column("status", sa.String(50), nullable=True),
            sa.Column("prompt", sa.Text, nullable=True),
            sa.Column("prompt_en", sa.Text, nullable=True),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("mode", sa.String(50), nullable=True),
            sa.Column("credits_cost", sa.Integer, nullable=True),
            sa.Column("submit_time", sa.DateTime, nullable=True),
            sa.Column("start_time", sa.DateTime, nullable=True),
            sa.Column("finish_time", sa.DateTime, nullable=True),
            sa.Column("progress", sa.String(20), nullable=True),
            sa.Column("image_url", sa.Text, nullable=True),
            sa.Column("fail_reason", sa.Text, nullable=True),
            sa.Column("properties", sa.JSON, nullable=True),
            sa.Column("buttons", sa.JSON, nullable=True),
            sa.Column("parent_task_id", sa.String(50), nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=True),
            sa.Column("updated_at", sa.DateTime, nullable=True),
            sa.Column("cloud_image_url", sa.Text, nullable=True),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
        )
        # 添加索引
        op.create_index("idx_user_created", "mj_tasks", ["user_id", "created_at"])
        op.create_index("idx_status_updated", "mj_tasks", ["status", "updated_at"])

    # 3. ComfyUI任务表
    if not table_exists(connection, "comfyui_tasks"):
        op.create_table(
            "comfyui_tasks",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("user_id", sa.String(255), nullable=False, index=True),
            sa.Column("workflow_id", sa.String(255), nullable=False),
            sa.Column("generate_uuid", sa.String(255), nullable=True),
            sa.Column("input_params", sa.JSON, nullable=False),
            sa.Column("template_uuid", sa.String(255), nullable=False),
            sa.Column("workflow_uuid", sa.String(255), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("generate_status", sa.Integer, nullable=True),
            sa.Column("percent_completed", sa.Float, nullable=False),
            sa.Column("output_images", sa.JSON, nullable=True),
            sa.Column("output_videos", sa.JSON, nullable=True),
            sa.Column("cloud_images", sa.JSON, nullable=True),
            sa.Column("cloud_videos", sa.JSON, nullable=True),
            sa.Column("credits_cost", sa.Integer, nullable=True),
            sa.Column("generation_time", sa.Float, nullable=True),
            sa.Column("error_message", sa.Text, nullable=True),
            sa.Column("retry_count", sa.Integer, nullable=False),
            sa.Column("liblib_response", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False),
            sa.Column("completed_at", sa.DateTime, nullable=True),
            # 标准云存储字段
            sa.Column("cloud_image_url", sa.Text, nullable=True),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
        )
        # 添加索引
        op.create_index(
            "idx_comfyui_tasks_user_status", "comfyui_tasks", ["user_id", "status"]
        )
        op.create_index(
            "idx_comfyui_tasks_workflow_status",
            "comfyui_tasks",
            ["workflow_id", "status"],
        )

    # 4. Kling视频生成任务表
    if not table_exists(connection, "kling_tasks"):
        op.create_table(
            "kling_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("external_task_id", sa.String(100), nullable=True),
            sa.Column("action", sa.String(50), nullable=False),
            sa.Column("status", sa.String(50), default="SUBMITTED"),
            sa.Column("task_status_msg", sa.Text, nullable=True),
            sa.Column("generation_mode", sa.String(20), default="single_image"),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("image_count", sa.Integer, default=0),
            sa.Column("model_name", sa.String(100), nullable=True),
            sa.Column("prompt", sa.Text, nullable=True),
            sa.Column("negative_prompt", sa.Text, nullable=True),
            sa.Column("cfg_scale", sa.Float, nullable=True),
            sa.Column("mode", sa.String(20), nullable=True),
            sa.Column("duration", sa.String(10), nullable=True),
            sa.Column("aspect_ratio", sa.String(20), nullable=True),
            sa.Column("input_image", sa.Text, nullable=True),
            sa.Column("image_tail", sa.Text, nullable=True),
            sa.Column("static_mask", sa.Text, nullable=True),
            sa.Column("dynamic_masks", sa.JSON, nullable=True),
            sa.Column("camera_control", sa.JSON, nullable=True),
            sa.Column("credits_cost", sa.Integer, default=0),
            sa.Column("submit_time", sa.DateTime, nullable=True),
            sa.Column("start_time", sa.DateTime, nullable=True),
            sa.Column("finish_time", sa.DateTime, nullable=True),
            sa.Column("video_id", sa.String(100), nullable=True),
            sa.Column("video_url", sa.Text, nullable=True),
            sa.Column("cloud_video_url", sa.Text, nullable=True),
            sa.Column("video_duration", sa.String(10), nullable=True),
            sa.Column("fail_reason", sa.Text, nullable=True),
            sa.Column("request_data", sa.Text, nullable=True),
            sa.Column("response_data", sa.Text, nullable=True),
            sa.Column("properties", sa.JSON, nullable=True),
            sa.Column("progress", sa.String(20), default="0%"),
            sa.Column("parent_task_id", sa.String(50), nullable=True),
            sa.Column("is_extended", sa.Boolean, default=False),
            sa.Column("original_duration", sa.String(10), nullable=True),
            sa.Column("extend_count", sa.Integer, default=0),
            sa.Column("created_at", sa.DateTime, default=func.now()),
            sa.Column("updated_at", sa.DateTime, default=func.now()),
            # 标准云存储字段
            sa.Column("cloud_image_url", sa.Text, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
        )
        # 添加索引
        op.create_index(
            "idx_kling_user_created", "kling_tasks", ["user_id", "created_at"]
        )
        op.create_index(
            "idx_kling_status_updated", "kling_tasks", ["status", "updated_at"]
        )

    # 5. Flux任务表
    if not table_exists(connection, "flux_tasks"):
        op.create_table(
            "flux_tasks",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("user_id", sa.String(255), nullable=False, index=True),
            sa.Column("request_id", sa.String(255), nullable=False, index=True),
            sa.Column("model", sa.String(100), nullable=False),
            sa.Column("task_type", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, default="PENDING"),
            sa.Column("prompt", sa.Text, nullable=True),
            sa.Column("input_image_url", sa.Text, nullable=True),
            sa.Column("input_image_urls", sa.JSON, nullable=True),
            sa.Column("uploaded_image_url", sa.Text, nullable=True),
            sa.Column("num_images", sa.Integer, default=1),
            sa.Column("aspect_ratio", sa.String(20), default="1:1"),
            sa.Column("image_size", sa.JSON, nullable=True),
            sa.Column("guidance_scale", sa.Float, default=3.5),
            sa.Column("num_inference_steps", sa.Integer, default=28),
            sa.Column("seed", sa.Integer, nullable=True),
            sa.Column("safety_tolerance", sa.Integer, default=2),
            sa.Column("strength", sa.Float, default=0.95),
            sa.Column("sync_mode", sa.Boolean, default=False),
            sa.Column("output_format", sa.String(10), default="jpeg"),
            sa.Column("enable_safety_checker", sa.Boolean, default=True),
            sa.Column("image_url", sa.Text, nullable=True),
            sa.Column("cloud_image_url", sa.Text, nullable=True),
            sa.Column("generation_time", sa.Float, nullable=True),
            sa.Column("queue_position", sa.Integer, nullable=True),
            sa.Column("error_message", sa.Text, nullable=True),
            sa.Column("retry_count", sa.Integer, default=0),
            sa.Column("flux_response", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, default=func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, default=func.now()),
            sa.Column("completed_at", sa.DateTime, nullable=True),
            # 标准云存储字段
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
        )
        # 添加索引
        op.create_index(
            "idx_flux_tasks_user_status", "flux_tasks", ["user_id", "status"]
        )
        op.create_index(
            "idx_flux_tasks_model_status", "flux_tasks", ["model", "status"]
        )

    # 6. Veo任务表
    if not table_exists(connection, "veo_tasks"):
        op.create_table(
            "veo_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), default="submitted", nullable=False),
            sa.Column("prompt", sa.Text, nullable=False),
            sa.Column("model", sa.String(50), nullable=False),
            sa.Column("enhance_prompt", sa.Boolean, default=True, nullable=False),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_video_url", sa.Text, nullable=True),
            sa.Column("cloud_video_url", sa.Text, nullable=True),
            sa.Column("external_task_id", sa.String(100), nullable=True),
            sa.Column("progress", sa.String(10), default="0%"),
            sa.Column("fail_reason", sa.Text, nullable=True),
            sa.Column("credits_cost", sa.Integer, nullable=True),
            sa.Column("properties", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, default=func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=True),
            sa.Column("finish_time", sa.DateTime, nullable=True),
            # 标准云存储字段
            sa.Column("cloud_image_url", sa.Text, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
        )
        # 添加索引
        op.create_index("idx_veo_user_created", "veo_tasks", ["user_id", "created_at"])
        op.create_index("idx_veo_status_updated", "veo_tasks", ["status", "updated_at"])

    # 7. Google Images任务表
    if not table_exists(connection, "google_images_tasks"):
        op.create_table(
            "google_images_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), default="submitted", nullable=False),
            sa.Column("prompt", sa.Text, nullable=False),
            sa.Column("model", sa.String(50), default="nano-banana", nullable=False),
            sa.Column("size", sa.String(20), nullable=True),
            sa.Column("quality", sa.String(20), nullable=True),
            sa.Column("style", sa.String(20), nullable=True),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
            sa.Column("progress", sa.String(10), default="0%"),
            sa.Column("fail_reason", sa.Text, nullable=True),
            sa.Column("credits_cost", sa.Integer, nullable=True),
            sa.Column("properties", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, default=func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=True),
            sa.Column("finish_time", sa.DateTime, nullable=True),
            # 标准云存储字段
            sa.Column("cloud_image_url", sa.Text, nullable=True),
        )
        # 添加索引
        op.create_index(
            "idx_google_images_user_created",
            "google_images_tasks",
            ["user_id", "created_at"],
        )
        op.create_index(
            "idx_google_images_status_updated",
            "google_images_tasks",
            ["status", "updated_at"],
        )

    # 8. Jimeng任务表
    if not table_exists(connection, "jimeng_tasks"):
        op.create_table(
            "jimeng_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), default="submitted", nullable=False),
            sa.Column("prompt", sa.Text, nullable=False),
            sa.Column("model", sa.String(50), nullable=False),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
            sa.Column("progress", sa.String(10), default="0%"),
            sa.Column("fail_reason", sa.Text, nullable=True),
            sa.Column("credits_cost", sa.Integer, nullable=True),
            sa.Column("properties", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, default=func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=True),
            sa.Column("finish_time", sa.DateTime, nullable=True),
            # 标准云存储字段
            sa.Column("cloud_image_url", sa.Text, nullable=True),
        )
        # 添加索引
        op.create_index(
            "idx_jimeng_user_created", "jimeng_tasks", ["user_id", "created_at"]
        )
        op.create_index(
            "idx_jimeng_status_updated", "jimeng_tasks", ["status", "updated_at"]
        )

    # 9. Jimeng Inpainting任务表
    if not table_exists(connection, "jimeng_inpainting_tasks"):
        op.create_table(
            "jimeng_inpainting_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), default="submitted", nullable=False),
            sa.Column("prompt", sa.Text, nullable=False),
            sa.Column("model", sa.String(50), nullable=False),
            sa.Column("mask_image", sa.Text, nullable=True),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
            sa.Column("progress", sa.String(10), default="0%"),
            sa.Column("fail_reason", sa.Text, nullable=True),
            sa.Column("credits_cost", sa.Integer, nullable=True),
            sa.Column("properties", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, default=func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=True),
            sa.Column("finish_time", sa.DateTime, nullable=True),
            # 标准云存储字段
            sa.Column("cloud_image_url", sa.Text, nullable=True),
        )
        # 添加索引
        op.create_index(
            "idx_jimeng_inpainting_user_created",
            "jimeng_inpainting_tasks",
            ["user_id", "created_at"],
        )
        op.create_index(
            "idx_jimeng_inpainting_status_updated",
            "jimeng_inpainting_tasks",
            ["status", "updated_at"],
        )

    # 10. Jimeng Outpainting任务表
    if not table_exists(connection, "jimeng_outpainting_tasks"):
        op.create_table(
            "jimeng_outpainting_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), default="submitted", nullable=False),
            sa.Column("prompt", sa.Text, nullable=False),
            sa.Column("model", sa.String(50), nullable=False),
            sa.Column("expand_direction", sa.String(20), nullable=True),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
            sa.Column("progress", sa.String(10), default="0%"),
            sa.Column("fail_reason", sa.Text, nullable=True),
            sa.Column("credits_cost", sa.Integer, nullable=True),
            sa.Column("properties", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, default=func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=True),
            sa.Column("finish_time", sa.DateTime, nullable=True),
            # 标准云存储字段
            sa.Column("cloud_image_url", sa.Text, nullable=True),
        )
        # 添加索引
        op.create_index(
            "idx_jimeng_outpainting_user_created",
            "jimeng_outpainting_tasks",
            ["user_id", "created_at"],
        )
        op.create_index(
            "idx_jimeng_outpainting_status_updated",
            "jimeng_outpainting_tasks",
            ["status", "updated_at"],
        )

    # 11. Kling唇语同步任务表
    if not table_exists(connection, "kling_lip_sync_tasks"):
        op.create_table(
            "kling_lip_sync_tasks",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False, index=True),
            sa.Column("status", sa.String(50), nullable=True),
            sa.Column("task_status_msg", sa.Text, nullable=True),
            sa.Column("mode", sa.String(20), nullable=False),
            sa.Column("video_input", sa.Text, nullable=False),
            sa.Column("input_type", sa.String(20), nullable=False),
            sa.Column("text", sa.Text, nullable=True),
            sa.Column("voice_id", sa.String(50), nullable=True),
            sa.Column("voice_language", sa.String(10), nullable=True),
            sa.Column("voice_speed", sa.Float, nullable=True),
            sa.Column("audio_file", sa.Text, nullable=True),
            sa.Column("audio_type", sa.String(10), nullable=True),
            sa.Column("video_url", sa.Text, nullable=True),
            sa.Column("video_duration", sa.String(10), nullable=True),
            sa.Column("fail_reason", sa.Text, nullable=True),
            sa.Column("credits_cost", sa.Integer, nullable=True),
            sa.Column("submit_time", sa.DateTime, nullable=True),
            sa.Column("finish_time", sa.DateTime, nullable=True),
            sa.Column("progress", sa.String(10), nullable=True),
            sa.Column("properties", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=True),
            sa.Column("updated_at", sa.DateTime, nullable=True),
            # 标准云存储字段
            sa.Column("cloud_image_url", sa.Text, nullable=True),
            sa.Column("input_images", sa.JSON, nullable=True),
            sa.Column("cloud_input_images", sa.JSON, nullable=True),
            sa.Column("result_images", sa.JSON, nullable=True),
            sa.Column("cloud_result_images", sa.JSON, nullable=True),
        )
        # 添加索引
        op.create_index(
            "ix_kling_lip_sync_tasks_status", "kling_lip_sync_tasks", ["status"]
        )
        op.create_index(
            "ix_kling_lip_sync_tasks_user_id", "kling_lip_sync_tasks", ["user_id"]
        )

    # ========== 任务表完善 ==========

    # 为所有任务表添加标准的云存储字段
    task_tables = [
        "dreamwork_tasks",
        "mj_tasks",
        "flux_tasks",
        "kling_tasks",
        "veo_tasks",
        "google_images_tasks",
        "jimeng_tasks",
        "comfyui_tasks",
        "jimeng_inpainting_tasks",
        "jimeng_outpainting_tasks",
        "kling_lip_sync_tasks",
    ]

    standard_columns = [
        ("cloud_image_url", "TEXT"),
        ("input_images", "JSON"),
        ("cloud_input_images", "JSON"),
        ("result_images", "JSON"),
        ("cloud_result_images", "JSON"),
    ]

    for table_name in task_tables:
        if table_exists(connection, table_name):
            for col_name, col_type in standard_columns:
                if not column_exists(connection, table_name, col_name):
                    try:
                        connection.execute(
                            text(
                                f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                            )
                        )
                        print(f"Added {table_name}.{col_name}")
                    except Exception as e:
                        if "duplicate column name" not in str(e).lower():
                            print(f"Failed to add {table_name}.{col_name}: {e}")

    # 特殊处理 veo_tasks 的 enhance_prompt 列
    if table_exists(connection, "veo_tasks") and not column_exists(
        connection, "veo_tasks", "enhance_prompt"
    ):
        connection.execute(
            text(
                "ALTER TABLE veo_tasks ADD COLUMN enhance_prompt BOOLEAN NOT NULL DEFAULT 1"
            )
        )

    # ========== 注意：积分表由原始迁移链创建，这里不重复创建 ==========
    print("✅ 积分系统表由原始迁移链管理，无需重复创建")

    # ========== 文件管理表 ==========

    if not table_exists(connection, "generated_files"):
        op.create_table(
            "generated_files",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("user_id", sa.String(255), nullable=False),
            sa.Column("service_type", sa.String(50), nullable=False),
            sa.Column("task_id", sa.String(255)),
            sa.Column("original_filename", sa.String(255)),
            sa.Column("stored_filename", sa.String(255), nullable=False),
            sa.Column("file_path", sa.String(500), nullable=False),
            sa.Column("cloud_url", sa.String(500)),
            sa.Column("file_type", sa.String(50), nullable=False),
            sa.Column("file_size", sa.Integer()),
            sa.Column("mime_type", sa.String(100)),
            sa.Column("upload_status", sa.String(20), default="pending"),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
        )

    print("✅ 统一完整迁移执行完成")


def downgrade():
    """降级（不建议使用）"""
    print("⚠️ 降级操作可能导致数据丢失")
    pass
