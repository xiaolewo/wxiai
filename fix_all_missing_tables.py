#!/usr/bin/env python3
"""
修复所有缺失的AI服务表
解决迁移链断裂导致的所有表缺失问题
"""

import sqlite3
import os
import sys
from datetime import datetime


def get_db_connection():
    """获取数据库连接"""
    db_paths = [
        "data/webui.db",
        "backend/data/webui.db",
        "webui.db",
        "backend/webui.db",
    ]
    # db_paths = ["C:\\Users\\29836\\Desktop\\wxiai-main\\backend\\data\\webui.db"]
    for path in db_paths:
        if os.path.exists(path):
            return sqlite3.connect(path), path
    print("没找到数据库")
    return None, None


def create_missing_tables():
    """创建所有缺失的表"""
    conn, db_path = get_db_connection()

    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 使用数据库: {db_path}")
    cursor = conn.cursor()

    try:
        print("🔧 创建缺失的AI服务表...")
        success_count = 0
        total_tables = 8

        # 1. 创建 veo_config 表
        print("\n📊 创建 Veo 配置表...")
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='veo_config'"
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE veo_config (
                        id VARCHAR(500) NOT NULL,
                        enabled BOOLEAN NOT NULL DEFAULT 0,
                        base_url VARCHAR(500),
                        api_key TEXT,
                        default_model VARCHAR(100),
                        max_concurrent_tasks INTEGER NOT NULL DEFAULT 5,
                        task_timeout INTEGER NOT NULL DEFAULT 600000,
                        credits_per_generation INTEGER NOT NULL DEFAULT 50,
                        default_duration INTEGER NOT NULL DEFAULT 5,
                        default_aspect_ratio VARCHAR(20) NOT NULL DEFAULT '16:9',
                        additional_config JSON,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME,
                        PRIMARY KEY (id),
                        UNIQUE (id)
                    )
                """
                )

                # 插入默认配置
                cursor.execute(
                    """
                    INSERT INTO veo_config 
                    (id, enabled, base_url, default_model, max_concurrent_tasks, task_timeout, 
                     credits_per_generation, default_duration, default_aspect_ratio) 
                    VALUES 
                    (1, 0, '', 'veo3', 5, 600000, 50, 5, '16:9')
                """
                )
                print("   ✅ 创建 veo_config 表")
                success_count += 1
            else:
                print("   ✅ veo_config 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 创建 veo_config 失败: {e}")

        # 2. 创建 google_images_config 表
        print("\n📊 创建 Google Images 配置表...")
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='google_images_config'"
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE google_images_config (
                        id VARCHAR(100) PRIMARY KEY AUTOINCREMENT,
                        enabled INTEGER NOT NULL DEFAULT 0,
                        base_url VARCHAR(500),
                        api_key TEXT,
                        default_model VARCHAR(50) NOT NULL DEFAULT 'nano-banana',
                        max_images_per_request INTEGER NOT NULL DEFAULT 10,
                        timeout INTEGER NOT NULL DEFAULT 60,
                        credits_per_generation INTEGER NOT NULL DEFAULT 20,
                        credits_per_image INTEGER NOT NULL DEFAULT 5,
                        additional_config TEXT,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME
                    )
                """
                )

                # 插入默认配置
                cursor.execute(
                    """
                    INSERT INTO google_images_config 
                    (id, enabled, base_url, default_model, max_images_per_request, timeout, 
                     credits_per_generation, credits_per_image) 
                    VALUES 
                    (1, 0, '', 'nano-banana', 10, 60, 20, 5)
                """
                )
                print("   ✅ 创建 google_images_config 表")
                success_count += 1
            else:
                print("   ✅ google_images_config 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 创建 google_images_config 失败: {e}")

        # 3. 创建 veo_tasks 表
        print("\n📊 创建 Veo 任务表...")
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='veo_tasks'"
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE veo_tasks (
                        id VARCHAR(50) NOT NULL,
                        user_id VARCHAR(50) NOT NULL,
                        action VARCHAR(50) NOT NULL DEFAULT 'generate',
                        status VARCHAR(50) NOT NULL DEFAULT 'submitted',
                        prompt TEXT NOT NULL,
                        model VARCHAR(100) NOT NULL,
                        duration INTEGER DEFAULT 5,
                        aspect_ratio VARCHAR(20) DEFAULT '16:9',
                        image_urls JSON,
                        video_mode VARCHAR(50) DEFAULT 'text_to_video',
                        credits_cost INTEGER NOT NULL DEFAULT 50,
                        submit_time DATETIME,
                        start_time DATETIME,
                        finish_time DATETIME,
                        progress VARCHAR(20) DEFAULT '0%',
                        result_video_url TEXT,
                        cloud_video_url TEXT,
                        fail_reason TEXT,
                        properties JSON,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME,
                        PRIMARY KEY (id)
                    )
                """
                )

                # 创建索引
                cursor.execute(
                    "CREATE INDEX idx_veo_tasks_user_id ON veo_tasks (user_id)"
                )
                cursor.execute(
                    "CREATE INDEX idx_veo_tasks_status ON veo_tasks (status)"
                )
                cursor.execute(
                    "CREATE INDEX idx_veo_tasks_created ON veo_tasks (created_at)"
                )

                print("   ✅ 创建 veo_tasks 表")
                success_count += 1
            else:
                print("   ✅ veo_tasks 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 创建 veo_tasks 失败: {e}")

        # 4. 创建 google_images_tasks 表
        print("\n📊 创建 Google Images 任务表...")
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='google_images_tasks'"
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE google_images_tasks (
                        id VARCHAR(50) NOT NULL,
                        user_id VARCHAR(50) NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'submitted',
                        prompt TEXT NOT NULL,
                        model VARCHAR(50) NOT NULL DEFAULT 'nano-banana',
                        images JSON,
                        size VARCHAR(20) DEFAULT '1024x1024',
                        n INTEGER DEFAULT 1,
                        quality VARCHAR(20) DEFAULT 'standard',
                        style VARCHAR(20) DEFAULT 'natural',
                        credits_cost INTEGER NOT NULL DEFAULT 20,
                        submit_time DATETIME,
                        start_time DATETIME,
                        finish_time DATETIME,
                        progress VARCHAR(20) DEFAULT '0%',
                        result_images JSON,
                        cloud_image_urls JSON,
                        fail_reason TEXT,
                        properties JSON,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME,
                        PRIMARY KEY (id)
                    )
                """
                )

                # 创建索引
                cursor.execute(
                    "CREATE INDEX idx_google_images_tasks_user_id ON google_images_tasks (user_id)"
                )
                cursor.execute(
                    "CREATE INDEX idx_google_images_tasks_status ON google_images_tasks (status)"
                )
                cursor.execute(
                    "CREATE INDEX idx_google_images_tasks_created ON google_images_tasks (created_at)"
                )

                print("   ✅ 创建 google_images_tasks 表")
                success_count += 1
            else:
                print("   ✅ google_images_tasks 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 创建 google_images_tasks 失败: {e}")

        # 5. 创建 jimeng_credits 表
        print("\n📊 创建 Jimeng 积分表...")
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='jimeng_credits'"
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE jimeng_credits (
                        id VARCHAR(50) NOT NULL,
                        user_id VARCHAR(50) NOT NULL,
                        task_id VARCHAR(50) NOT NULL,
                        credit_amount INTEGER NOT NULL,
                        operation_type VARCHAR(20) NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id)
                    )
                """
                )

                # 创建索引
                cursor.execute(
                    "CREATE INDEX idx_jimeng_credit_user ON jimeng_credits (user_id)"
                )
                cursor.execute(
                    "CREATE INDEX idx_jimeng_credit_task ON jimeng_credits (task_id)"
                )

                print("   ✅ 创建 jimeng_credits 表")
                success_count += 1
            else:
                print("   ✅ jimeng_credits 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 创建 jimeng_credits 失败: {e}")

        # 6. 创建 comfyui_credits 表
        print("\n📊 创建 ComfyUI 积分表...")
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='comfyui_credits'"
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE comfyui_credits (
                        id VARCHAR(50) NOT NULL,
                        user_id VARCHAR(50) NOT NULL,
                        task_id VARCHAR(50) NOT NULL,
                        credit_amount INTEGER NOT NULL,
                        operation_type VARCHAR(20) NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id)
                    )
                """
                )

                # 创建索引
                cursor.execute(
                    "CREATE INDEX idx_comfyui_credit_user ON comfyui_credits (user_id)"
                )
                cursor.execute(
                    "CREATE INDEX idx_comfyui_credit_task ON comfyui_credits (task_id)"
                )

                print("   ✅ 创建 comfyui_credits 表")
                success_count += 1
            else:
                print("   ✅ comfyui_credits 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 创建 comfyui_credits 失败: {e}")

        # 7. 创建 veo_credits 表
        print("\n📊 创建 Veo 积分表...")
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='veo_credits'"
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE veo_credits (
                        id VARCHAR(50) NOT NULL,
                        user_id VARCHAR(50) NOT NULL,
                        task_id VARCHAR(50) NOT NULL,
                        credit_amount INTEGER NOT NULL,
                        operation_type VARCHAR(20) NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id)
                    )
                """
                )

                # 创建索引
                cursor.execute(
                    "CREATE INDEX idx_veo_credit_user ON veo_credits (user_id)"
                )
                cursor.execute(
                    "CREATE INDEX idx_veo_credit_task ON veo_credits (task_id)"
                )

                print("   ✅ 创建 veo_credits 表")
                success_count += 1
            else:
                print("   ✅ veo_credits 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 创建 veo_credits 失败: {e}")

        # 8. 创建 google_images_credits 表
        print("\n📊 创建 Google Images 积分表...")
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='google_images_credits'"
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE google_images_credits (
                        id VARCHAR(50) NOT NULL,
                        user_id VARCHAR(50) NOT NULL,
                        task_id VARCHAR(50) NOT NULL,
                        credit_amount INTEGER NOT NULL,
                        operation_type VARCHAR(20) NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id)
                    )
                """
                )

                # 创建索引
                cursor.execute(
                    "CREATE INDEX idx_google_images_credit_user ON google_images_credits (user_id)"
                )
                cursor.execute(
                    "CREATE INDEX idx_google_images_credit_task ON google_images_credits (task_id)"
                )

                print("   ✅ 创建 google_images_credits 表")
                success_count += 1
            else:
                print("   ✅ google_images_credits 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 创建 google_images_credits 失败: {e}")

        # 提交所有更改
        conn.commit()

        print(f"\n✅ 表创建完成！成功创建/验证 {success_count}/{total_tables} 个表")

        if success_count == total_tables:
            print("🎉 所有缺失的AI服务表已创建，Google Images配置应该可以正常保存了")
            return True
        else:
            print("⚠️  部分表创建失败，请检查错误信息")
            return False

    except Exception as e:
        print(f"❌ 创建表过程中发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_all_tables():
    """验证所有表是否创建成功"""
    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    print("\n🔍 验证所有AI服务表...")

    # 检查刚才创建的表
    tables_to_check = [
        "veo_config",
        "google_images_config",
        "veo_tasks",
        "google_images_tasks",
        "jimeng_credits",
        "comfyui_credits",
        "veo_credits",
        "google_images_credits",
    ]

    all_good = True
    for table in tables_to_check:
        try:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            if cursor.fetchone():
                print(f"   ✅ {table} - 存在")
            else:
                print(f"   ❌ {table} - 缺失")
                all_good = False
        except Exception as e:
            print(f"   ❌ 检查 {table} 失败: {e}")
            all_good = False

    conn.close()

    if all_good:
        print("\n🎉 验证通过！所有AI服务表都已正确创建")
        print("\n📝 现在应该可以正常使用的功能：")
        print("   ✅ Google Images 配置保存")
        print("   ✅ Veo 视频生成配置")
        print("   ✅ 所有AI服务的积分记录")
        print("   ✅ 所有AI服务的任务历史")
        return True
    else:
        print("\n⚠️  验证失败，仍有表缺失")
        return False


def create_all_tables():
    if create_missing_tables():
        verify_all_tables()
        print("\n🚀 建议操作：")
        print("1. 重启应用服务器")
        print("2. 测试 Google Images 配置保存")
        print("3. 测试其他AI服务配置")
        print("4. 检查所有历史记录页面")
    else:
        print("❌ 表创建失败，请检查错误信息并重试")
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 开始创建所有缺失的AI服务表...")
    print("=" * 60)

    if create_missing_tables():
        verify_all_tables()
        print("\n🚀 建议操作：")
        print("1. 重启应用服务器")
        print("2. 测试 Google Images 配置保存")
        print("3. 测试其他AI服务配置")
        print("4. 检查所有历史记录页面")
    else:
        print("❌ 表创建失败，请检查错误信息并重试")
        sys.exit(1)
