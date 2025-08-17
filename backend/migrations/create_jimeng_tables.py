#!/usr/bin/env python3
"""
创建即梦视频生成相关数据表
包含配置表和任务表
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from open_webui.internal.db import get_db
import sqlalchemy as sa
from sqlalchemy import text


def create_jimeng_tables():
    """创建即梦视频相关数据表"""
    print("🎬 【即梦迁移】开始创建即梦视频数据表...")

    try:
        with get_db() as db:
            # 检查表是否已存在
            inspector = sa.inspect(db.bind)
            existing_tables = inspector.get_table_names()

            if "jimeng_config" in existing_tables:
                print("⚠️  即梦配置表已存在，跳过创建")
            else:
                # 创建即梦配置表
                create_config_table_sql = """
                CREATE TABLE jimeng_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    enabled BOOLEAN DEFAULT FALSE NOT NULL,
                    base_url TEXT,
                    api_key TEXT,
                    
                    -- 默认参数配置
                    default_duration VARCHAR(10) DEFAULT '5' NOT NULL,
                    default_aspect_ratio VARCHAR(10) DEFAULT '16:9' NOT NULL,
                    default_cfg_scale REAL DEFAULT 0.5 NOT NULL,
                    
                    -- 积分配置
                    credits_per_5s INTEGER DEFAULT 30 NOT NULL,
                    credits_per_10s INTEGER DEFAULT 60 NOT NULL,
                    
                    -- 系统配置
                    max_concurrent_tasks INTEGER DEFAULT 5 NOT NULL,
                    task_timeout INTEGER DEFAULT 600000 NOT NULL,
                    query_interval INTEGER DEFAULT 10000 NOT NULL,
                    
                    -- API路径配置
                    detected_api_path TEXT,
                    
                    -- 时间戳
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
                """

                db.execute(text(create_config_table_sql))
                print("✅ 即梦配置表创建成功")

            if "jimeng_tasks" in existing_tables:
                print("⚠️  即梦任务表已存在，跳过创建")
            else:
                # 创建即梦任务表
                create_tasks_table_sql = """
                CREATE TABLE jimeng_tasks (
                    id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    status VARCHAR(50) DEFAULT 'submitted' NOT NULL,
                    
                    -- 生成参数
                    prompt TEXT NOT NULL,
                    duration VARCHAR(10) NOT NULL,
                    aspect_ratio VARCHAR(10) NOT NULL,
                    cfg_scale REAL NOT NULL,
                    
                    -- 图生视频参数
                    image_url TEXT,
                    input_image TEXT,
                    
                    -- 任务结果
                    external_task_id VARCHAR(255),
                    video_url TEXT,
                    progress VARCHAR(50) DEFAULT '0%',
                    fail_reason TEXT,
                    
                    -- 积分相关
                    credits_cost INTEGER NOT NULL,
                    
                    -- 扩展属性
                    properties JSON,
                    
                    -- 时间戳
                    submit_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    start_time DATETIME,
                    complete_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
                """

                db.execute(text(create_tasks_table_sql))
                print("✅ 即梦任务表创建成功")

                # 创建索引
                indices = [
                    "CREATE INDEX idx_jimeng_tasks_user_id ON jimeng_tasks(user_id)",
                    "CREATE INDEX idx_jimeng_tasks_status ON jimeng_tasks(status)",
                    "CREATE INDEX idx_jimeng_tasks_created_at ON jimeng_tasks(created_at)",
                    "CREATE INDEX idx_jimeng_tasks_user_status ON jimeng_tasks(user_id, status)",
                ]

                for index_sql in indices:
                    try:
                        db.execute(text(index_sql))
                    except Exception as e:
                        print(f"⚠️  创建索引失败: {e}")

                print("✅ 即梦任务表索引创建完成")

            db.commit()
            print("🎉 即梦视频数据表创建完成!")

    except Exception as e:
        print(f"❌ 创建即梦视频数据表失败: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    create_jimeng_tables()
