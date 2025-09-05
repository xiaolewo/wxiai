#!/usr/bin/env python3
"""
完整的迁移修复脚本 - 解决云存储字段缺失问题
根本原因：迁移链断裂，云存储相关迁移从未执行
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
    for path in db_paths:
        if os.path.exists(path):
            return sqlite3.connect(path), path
    return None, None


def check_table_structure(cursor, table_name):
    """检查表结构"""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return {col[1]: col for col in columns}
    except Exception as e:
        print(f"   ❌ 无法检查表 {table_name}: {e}")
        return {}


def add_missing_cloud_fields():
    """添加所有缺失的云存储字段"""
    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 使用数据库: {db_path}")
    cursor = conn.cursor()

    try:
        print("🔧 修复云存储字段缺失问题...")

        # 备份当前数据库版本
        cursor.execute("SELECT version_num FROM alembic_version")
        current_version = cursor.fetchone()[0]
        print(f"📍 当前数据库版本: {current_version}")

        success_count = 0
        total_fixes = 0

        # 1. 修复 mj_tasks 表 - 添加 cloud_image_url 字段
        print("\n📊 修复 MidJourney 任务表...")
        total_fixes += 1
        try:
            table_info = check_table_structure(cursor, "mj_tasks")
            if "cloud_image_url" not in table_info:
                cursor.execute("ALTER TABLE mj_tasks ADD COLUMN cloud_image_url TEXT")
                print("   ✅ 添加 mj_tasks.cloud_image_url 字段")
                success_count += 1
            else:
                print("   ✅ mj_tasks.cloud_image_url 字段已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 修复 mj_tasks 失败: {e}")

        # 2. 修复 dreamwork_tasks 表 - 添加 cloud_image_url 字段
        print("\n📊 修复 DreamWork 任务表...")
        total_fixes += 1
        try:
            table_info = check_table_structure(cursor, "dreamwork_tasks")
            if "cloud_image_url" not in table_info:
                cursor.execute(
                    "ALTER TABLE dreamwork_tasks ADD COLUMN cloud_image_url TEXT"
                )
                print("   ✅ 添加 dreamwork_tasks.cloud_image_url 字段")
                success_count += 1
            else:
                print("   ✅ dreamwork_tasks.cloud_image_url 字段已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 修复 dreamwork_tasks 失败: {e}")

        # 3. 修复 kling_tasks 表 - 添加 cloud_video_url 字段
        print("\n📊 修复 Kling 任务表...")
        total_fixes += 1
        try:
            table_info = check_table_structure(cursor, "kling_tasks")
            if "cloud_video_url" not in table_info:
                cursor.execute(
                    "ALTER TABLE kling_tasks ADD COLUMN cloud_video_url TEXT"
                )
                print("   ✅ 添加 kling_tasks.cloud_video_url 字段")
                success_count += 1
            else:
                print("   ✅ kling_tasks.cloud_video_url 字段已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 修复 kling_tasks 失败: {e}")

        # 4. 修复 jimeng_tasks 表 - 添加 cloud_video_url 字段
        print("\n📊 修复 Jimeng 任务表...")
        total_fixes += 1
        try:
            table_info = check_table_structure(cursor, "jimeng_tasks")
            if "cloud_video_url" not in table_info:
                cursor.execute(
                    "ALTER TABLE jimeng_tasks ADD COLUMN cloud_video_url TEXT"
                )
                print("   ✅ 添加 jimeng_tasks.cloud_video_url 字段")
                success_count += 1
            else:
                print("   ✅ jimeng_tasks.cloud_video_url 字段已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 修复 jimeng_tasks 失败: {e}")

        # 5. 修复 flux_tasks 表 - 添加多图支持字段
        print("\n📊 修复 Flux 任务表...")
        total_fixes += 2  # 两个字段
        try:
            table_info = check_table_structure(cursor, "flux_tasks")

            if "input_image_urls" not in table_info:
                cursor.execute(
                    "ALTER TABLE flux_tasks ADD COLUMN input_image_urls JSON"
                )
                print("   ✅ 添加 flux_tasks.input_image_urls 字段")
                success_count += 1
            else:
                print("   ✅ flux_tasks.input_image_urls 字段已存在")
                success_count += 1

            if "image_size" not in table_info:
                cursor.execute("ALTER TABLE flux_tasks ADD COLUMN image_size JSON")
                print("   ✅ 添加 flux_tasks.image_size 字段")
                success_count += 1
            else:
                print("   ✅ flux_tasks.image_size 字段已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 修复 flux_tasks 失败: {e}")

        # 6. 确保云存储配置表存在
        print("\n📊 检查云存储配置表...")
        total_fixes += 1
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='cloud_storage_config'"
            )
            if not cursor.fetchone():
                # 创建云存储配置表
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
                print("   ✅ 创建 cloud_storage_config 表")
                success_count += 1
            else:
                print("   ✅ cloud_storage_config 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 修复 cloud_storage_config 失败: {e}")

        # 7. 确保生成文件记录表存在
        print("\n📊 检查生成文件记录表...")
        total_fixes += 1
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='generated_files'"
            )
            if not cursor.fetchone():
                # 创建生成文件记录表
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
                cursor.execute(
                    "CREATE INDEX idx_generated_files_user_id ON generated_files (user_id)"
                )
                cursor.execute(
                    "CREATE INDEX idx_generated_files_source ON generated_files (source_type, source_task_id)"
                )
                cursor.execute(
                    "CREATE INDEX idx_generated_files_created ON generated_files (created_at)"
                )

                print("   ✅ 创建 generated_files 表")
                success_count += 1
            else:
                print("   ✅ generated_files 表已存在")
                success_count += 1
        except Exception as e:
            print(f"   ❌ 修复 generated_files 失败: {e}")

        # 提交所有更改
        conn.commit()

        print(f"\n✅ 修复完成！成功修复 {success_count}/{total_fixes} 项")

        if success_count == total_fixes:
            print(
                "🎉 所有云存储相关字段已修复，MidJourney和DreamWork历史记录应该可以正常加载了"
            )
            return True
        else:
            print("⚠️  部分修复失败，请检查错误信息")
            return False

    except Exception as e:
        print(f"❌ 修复过程中发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_fixes():
    """验证修复结果"""
    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    print("\n🔍 验证修复结果...")

    # 检查关键字段是否存在
    checks = [
        ("mj_tasks", "cloud_image_url"),
        ("dreamwork_tasks", "cloud_image_url"),
        ("kling_tasks", "cloud_video_url"),
        ("jimeng_tasks", "cloud_video_url"),
        ("flux_tasks", "input_image_urls"),
        ("flux_tasks", "image_size"),
    ]

    all_good = True
    for table, field in checks:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if field in columns:
                print(f"   ✅ {table}.{field} - 存在")
            else:
                print(f"   ❌ {table}.{field} - 缺失")
                all_good = False
        except Exception as e:
            print(f"   ❌ 检查 {table}.{field} 失败: {e}")
            all_good = False

    # 检查表是否存在
    tables = ["cloud_storage_config", "generated_files"]
    for table in tables:
        try:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            if cursor.fetchone():
                print(f"   ✅ {table} 表 - 存在")
            else:
                print(f"   ❌ {table} 表 - 缺失")
                all_good = False
        except Exception as e:
            print(f"   ❌ 检查 {table} 表失败: {e}")
            all_good = False

    conn.close()

    if all_good:
        print("\n🎉 验证通过！所有字段和表都已正确创建")
        print("\n📝 建议操作：")
        print("1. 重启应用服务器")
        print("2. 访问MidJourney和DreamWork历史记录页面测试")
        print("3. 检查云存储配置是否正常")
        return True
    else:
        print("\n⚠️  验证失败，仍有问题需要解决")
        return False


if __name__ == "__main__":
    print("🚀 开始修复云存储字段缺失问题...")
    print("=" * 60)

    if add_missing_cloud_fields():
        verify_fixes()
    else:
        print("❌ 修复失败，请检查错误信息并重试")
        sys.exit(1)
