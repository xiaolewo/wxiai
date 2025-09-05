#!/usr/bin/env python3
"""
完整的云存储表修复脚本
确保所有云存储相关表和字段都存在
"""

import sqlite3
import os


def get_db_connection():
    """获取数据库连接"""
    db_paths = ["backend/data/webui.db", "webui.db", "backend/webui.db"]
    for path in db_paths:
        if os.path.exists(path):
            return sqlite3.connect(path), path
    return None, None


def create_cloud_storage_tables():
    """创建云存储核心表"""
    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 使用数据库: {db_path}")
    cursor = conn.cursor()

    try:
        # 1. 检查并创建 cloud_storage_config 表
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cloud_storage_config'"
        )
        if not cursor.fetchone():
            print("🔧 创建 cloud_storage_config 表...")
            cursor.execute(
                """
                CREATE TABLE cloud_storage_config (
                    id VARCHAR(255) NOT NULL PRIMARY KEY,
                    provider VARCHAR(50) NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT 0,
                    secret_id TEXT,
                    secret_key TEXT,
                    region VARCHAR(50),
                    bucket VARCHAR(255),
                    domain TEXT,
                    auto_upload BOOLEAN NOT NULL DEFAULT 1,
                    allowed_types JSON,
                    max_file_size BIGINT NOT NULL DEFAULT 104857600,
                    base_path VARCHAR(255) NOT NULL DEFAULT 'generated/',
                    image_path VARCHAR(255) NOT NULL DEFAULT 'images/',
                    video_path VARCHAR(255) NOT NULL DEFAULT 'videos/',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 插入默认配置
            cursor.execute(
                """
                INSERT INTO cloud_storage_config 
                (id, provider, enabled, secret_id, secret_key, region, bucket, domain, 
                 auto_upload, allowed_types, max_file_size, base_path, image_path, video_path) 
                VALUES 
                ('default', 'tencent-cos', 0, '', '', 'ap-beijing', '', '', 
                 1, '["image/*", "video/*"]', 104857600, 'generated/', 'images/', 'videos/')
            """
            )
            print("✅ cloud_storage_config 表创建完成")
        else:
            print("✅ cloud_storage_config 表已存在")

        # 2. 检查并创建 generated_files 表
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='generated_files'"
        )
        if not cursor.fetchone():
            print("🔧 创建 generated_files 表...")
            cursor.execute(
                """
                CREATE TABLE generated_files (
                    id VARCHAR(255) NOT NULL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255),
                    file_type VARCHAR(20) NOT NULL,
                    mime_type VARCHAR(100),
                    file_size BIGINT,
                    storage_provider VARCHAR(50) NOT NULL DEFAULT 'local',
                    local_path TEXT,
                    cloud_url TEXT,
                    cloud_path TEXT,
                    source_type VARCHAR(50) NOT NULL,
                    source_task_id VARCHAR(255),
                    file_metadata JSON,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 创建索引
            indexes = [
                "CREATE INDEX idx_generated_files_user_id ON generated_files (user_id)",
                "CREATE INDEX idx_generated_files_source ON generated_files (source_type, source_task_id)",
                "CREATE INDEX idx_generated_files_status ON generated_files (status)",
                "CREATE INDEX idx_generated_files_created_at ON generated_files (created_at)",
                "CREATE INDEX idx_generated_files_user_status ON generated_files (user_id, status)",
            ]

            for index in indexes:
                try:
                    cursor.execute(index)
                except:
                    pass  # 索引可能已存在

            print("✅ generated_files 表创建完成")
        else:
            print("✅ generated_files 表已存在")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ 创建云存储表时出错: {e}")
        conn.rollback()
        conn.close()
        return False


def add_cloud_urls_to_task_tables():
    """为各AI服务任务表添加云存储URL字段"""
    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # 需要添加云存储字段的表和字段映射
    task_tables = {
        "mj_tasks": "cloud_image_url",
        "dreamwork_tasks": "cloud_image_url",
        "kling_tasks": "cloud_video_url",
        "jimeng_tasks": "cloud_video_url",
        "flux_tasks": "cloud_image_url",
        "google_images_tasks": "cloud_result_images",  # 这个表已经有了
        "veo_tasks": "cloud_video_url",
        "comfyui_tasks": "cloud_images",  # 这个表已经有了
        "jimeng_inpainting_tasks": "cloud_image_url",
        "jimeng_outpainting_tasks": "cloud_image_url",
        "kling_lip_sync_tasks": "cloud_video_url",
    }

    print("🔧 为AI任务表添加云存储字段...")

    for table_name, column_name in task_tables.items():
        try:
            # 检查表是否存在
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if not cursor.fetchone():
                print(f"   ⚠️  表 {table_name} 不存在，跳过")
                continue

            # 检查字段是否已存在
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            if column_name in columns:
                print(f"   ✅ {table_name}.{column_name} 已存在")
                continue

            # 添加字段
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT")
            print(f"   ✅ 已添加 {table_name}.{column_name}")

        except Exception as e:
            print(f"   ❌ 处理 {table_name} 时出错: {e}")
            continue

    try:
        conn.commit()
        conn.close()
        print("✅ 云存储字段添加完成")
        return True
    except Exception as e:
        print(f"❌ 提交更改时出错: {e}")
        conn.rollback()
        conn.close()
        return False


def create_cloud_storage_stats_table():
    """创建云存储统计表"""
    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 检查是否已存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cloud_storage_stats'"
        )
        if cursor.fetchone():
            print("✅ cloud_storage_stats 表已存在")
            conn.close()
            return True

        print("🔧 创建 cloud_storage_stats 表...")
        cursor.execute(
            """
            CREATE TABLE cloud_storage_stats (
                id VARCHAR(255) NOT NULL PRIMARY KEY,
                date DATE NOT NULL,
                provider VARCHAR(50) NOT NULL,
                total_files INTEGER NOT NULL DEFAULT 0,
                total_size BIGINT NOT NULL DEFAULT 0,
                uploaded_files INTEGER NOT NULL DEFAULT 0,
                failed_files INTEGER NOT NULL DEFAULT 0,
                storage_cost DECIMAL(10,2) DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建索引
        cursor.execute(
            "CREATE INDEX idx_cloud_storage_stats_date ON cloud_storage_stats (date)"
        )
        cursor.execute(
            "CREATE INDEX idx_cloud_storage_stats_provider ON cloud_storage_stats (provider)"
        )

        conn.commit()
        conn.close()
        print("✅ cloud_storage_stats 表创建完成")
        return True

    except Exception as e:
        print(f"❌ 创建 cloud_storage_stats 表时出错: {e}")
        conn.rollback()
        conn.close()
        return False


def verify_cloud_storage_setup():
    """验证云存储设置完整性"""
    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    print("\n🔍 云存储设置验证:")

    # 检查核心表
    core_tables = ["cloud_storage_config", "generated_files", "cloud_storage_stats"]
    for table in core_tables:
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
        )
        exists = bool(cursor.fetchone())
        status = "✅ 存在" if exists else "❌ 缺失"
        print(f"   {table:20}: {status}")

    # 检查cloud_storage_config配置
    try:
        cursor.execute("SELECT COUNT(*) FROM cloud_storage_config")
        config_count = cursor.fetchone()[0]
        print(f"   配置记录数量: {config_count}")
    except:
        print("   配置记录: ❌ 无法访问")

    # 检查任务表的云存储字段
    print("\n📊 任务表云存储字段:")
    task_tables = {
        "mj_tasks": "cloud_image_url",
        "dreamwork_tasks": "cloud_image_url",
        "kling_tasks": "cloud_video_url",
        "jimeng_tasks": "cloud_video_url",
        "flux_tasks": "cloud_image_url",
        "veo_tasks": "cloud_video_url",
    }

    for table_name, column_name in task_tables.items():
        try:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if cursor.fetchone():
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                has_field = column_name in columns
                status = "✅ 有字段" if has_field else "❌ 无字段"
            else:
                status = "❌ 无表"
        except:
            status = "❌ 错误"

        print(f"   {table_name:20}: {status}")

    conn.close()
    return True


def main():
    """主函数"""
    print("🚀 云存储完整设置修复")
    print("=" * 50)

    # 1. 创建云存储核心表
    print("\n📋 第一步：创建云存储核心表")
    if not create_cloud_storage_tables():
        print("❌ 核心表创建失败")
        return

    # 2. 为任务表添加云存储字段
    print("\n🔗 第二步：为任务表添加云存储字段")
    if not add_cloud_urls_to_task_tables():
        print("❌ 任务表字段添加失败")
        return

    # 3. 创建统计表
    print("\n📊 第三步：创建云存储统计表")
    create_cloud_storage_stats_table()

    # 4. 验证设置
    print("\n🔍 第四步：验证云存储设置")
    verify_cloud_storage_setup()

    print("\n" + "=" * 50)
    print("🎉 云存储设置修复完成！")
    print("✅ 现在支持：")
    print("   - 腾讯云COS集成")
    print("   - 生成文件自动上传")
    print("   - 存储统计和监控")
    print("   - 所有AI服务的云存储功能")


if __name__ == "__main__":
    main()
