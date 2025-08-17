#!/usr/bin/env python3
"""
可灵视频生成数据库表创建脚本
基于可灵API规范设计的完整数据库结构
"""

import sqlite3
import sys
import os

# 添加项目路径
sys.path.append("/Users/liuqingliang/Desktop/openwebui/open-webui/backend")


def create_kling_tables():
    """创建可灵视频生成相关的数据库表"""

    # 数据库文件路径
    db_path = "/Users/liuqingliang/Desktop/openwebui/open-webui/backend/data/webui.db"

    print("🎬 开始创建可灵视频生成数据库表...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 可灵配置表
        print("📋 创建 kling_config 表...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS kling_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enabled BOOLEAN DEFAULT 0,
                base_url VARCHAR(500) DEFAULT 'https://api.klingai.com',
                api_key TEXT,
                
                -- 模型配置
                text_to_video_model VARCHAR(100) DEFAULT 'kling-v1',
                image_to_video_model VARCHAR(100) DEFAULT 'kling-v1',
                
                -- 默认参数
                default_mode VARCHAR(20) DEFAULT 'std',
                default_duration VARCHAR(10) DEFAULT '5',
                default_aspect_ratio VARCHAR(20) DEFAULT '16:9',
                default_cfg_scale REAL DEFAULT 0.5,
                
                -- 积分配置 (不同模式和时长的积分消耗)
                credits_per_std_5s INTEGER DEFAULT 50,
                credits_per_std_10s INTEGER DEFAULT 100,
                credits_per_pro_5s INTEGER DEFAULT 100,
                credits_per_pro_10s INTEGER DEFAULT 200,
                
                -- 系统配置
                max_concurrent_tasks INTEGER DEFAULT 3,
                task_timeout INTEGER DEFAULT 600000,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 2. 可灵任务表
        print("📋 创建 kling_tasks 表...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS kling_tasks (
                id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                external_task_id VARCHAR(100),
                
                -- 任务类型和状态
                action VARCHAR(50) NOT NULL, -- TEXT_TO_VIDEO, IMAGE_TO_VIDEO
                status VARCHAR(50) DEFAULT 'SUBMITTED', -- submitted, processing, succeed, failed
                task_status_msg TEXT,
                
                -- 基础视频生成参数
                model_name VARCHAR(100),
                prompt TEXT,
                negative_prompt TEXT,
                cfg_scale REAL,
                mode VARCHAR(20), -- std, pro
                duration VARCHAR(10), -- 5, 10
                aspect_ratio VARCHAR(20), -- 16:9, 9:16, 1:1
                
                -- 图生视频专用参数
                input_image TEXT, -- base64 or url
                image_tail TEXT, -- base64 or url for tail frame control
                static_mask TEXT, -- static brush mask
                dynamic_masks JSON, -- dynamic brush masks and trajectories
                
                -- 摄像机控制参数
                camera_control JSON,
                
                -- 积分和任务管理
                credits_cost INTEGER DEFAULT 0,
                submit_time DATETIME,
                start_time DATETIME,
                finish_time DATETIME,
                
                -- 结果数据
                video_id VARCHAR(100),
                video_url TEXT,
                video_duration VARCHAR(10),
                fail_reason TEXT,
                
                -- 请求和响应数据存储
                request_data TEXT,
                response_data TEXT,
                
                -- 元数据
                properties JSON,
                progress VARCHAR(20) DEFAULT '0%',
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 3. 可灵积分记录表
        print("📋 创建 kling_credits 表...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS kling_credits (
                id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                amount INTEGER NOT NULL,
                balance INTEGER NOT NULL,
                reason VARCHAR(200),
                task_id VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建索引
        print("📋 创建索引...")

        # 任务表索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_kling_tasks_user_id ON kling_tasks (user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_kling_tasks_status ON kling_tasks (status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_kling_tasks_external_id ON kling_tasks (external_task_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_kling_tasks_created_at ON kling_tasks (created_at)"
        )

        # 积分表索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_kling_credits_user_id ON kling_credits (user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_kling_credits_task_id ON kling_credits (task_id)"
        )

        # 插入默认配置
        print("📋 插入默认配置...")
        cursor.execute(
            """
            INSERT OR IGNORE INTO kling_config (id, enabled) VALUES (1, 0)
        """
        )

        conn.commit()
        print("✅ 可灵视频生成数据库表创建成功!")

        # 验证表结构
        print("\n📊 验证表结构:")
        tables = ["kling_config", "kling_tasks", "kling_credits"]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} 行")

            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"     列数: {len(columns)}")

        return True

    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if "conn" in locals():
            conn.close()


def main():
    """主函数"""
    print("🎬 可灵视频生成数据库初始化")
    print("=" * 50)

    success = create_kling_tables()

    if success:
        print("\n🎉 数据库表创建完成!")
        print("\n📋 创建的表:")
        print("   - kling_config: 可灵服务配置")
        print("   - kling_tasks: 视频生成任务记录")
        print("   - kling_credits: 积分消耗记录")
        print("\n✅ 可以开始可灵视频生成功能开发了!")
    else:
        print("\n❌ 数据库表创建失败，请检查错误信息")


if __name__ == "__main__":
    main()
