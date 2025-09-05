#!/usr/bin/env python3
"""
紧急修复全新部署的表结构问题
解决用户报告的表缺失和列缺失问题
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


def fix_cloud_storage_config_table():
    """修复云存储配置表"""
    print("🔧 修复云存储配置表...")

    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cloud_storage_config'"
        )
        if not cursor.fetchone():
            print("   📝 创建cloud_storage_config表...")
            cursor.execute(
                """
                CREATE TABLE cloud_storage_config (
                    id VARCHAR(255) NOT NULL PRIMARY KEY DEFAULT 'default',
                    provider VARCHAR(50) NOT NULL DEFAULT 'tencent-cos',
                    enabled BOOLEAN NOT NULL DEFAULT 0,
                    secret_id TEXT,
                    secret_key TEXT,
                    region VARCHAR(50) DEFAULT 'ap-beijing',
                    bucket VARCHAR(255),
                    domain VARCHAR(500),
                    auto_upload BOOLEAN NOT NULL DEFAULT 1,
                    allowed_types JSON,
                    max_file_size INTEGER DEFAULT 104857600,
                    base_path VARCHAR(255) DEFAULT 'generated/',
                    image_path VARCHAR(255) DEFAULT 'images/',
                    video_path VARCHAR(255) DEFAULT 'videos/',
                    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
                )
            """
            )
            print("   ✅ cloud_storage_config表已创建")

        # 确保有默认配置记录
        cursor.execute("SELECT id FROM cloud_storage_config WHERE id = 'default'")
        if not cursor.fetchone():
            print("   📝 插入默认云存储配置...")
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
            print("   ✅ 默认云存储配置已插入")

        conn.commit()
        print("✅ 云存储配置表修复完成")
        return True

    except Exception as e:
        print(f"❌ 修复云存储配置表失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def fix_google_images_config_table():
    """修复Google Images配置表"""
    print("🔧 修复Google Images配置表...")

    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='google_images_config'"
        )
        if not cursor.fetchone():
            print("   📝 创建google_images_config表...")
            cursor.execute(
                """
                CREATE TABLE google_images_config (
                    id VARCHAR(255) NOT NULL PRIMARY KEY DEFAULT 'default',
                    enabled BOOLEAN NOT NULL DEFAULT 0,
                    base_url VARCHAR(500) NOT NULL DEFAULT 'https://api.googleimages.ai',
                    api_key TEXT,
                    default_model VARCHAR(100) DEFAULT 'nano-banana',
                    max_images_per_request INTEGER DEFAULT 10,
                    timeout INTEGER DEFAULT 120,
                    credits_per_generation INTEGER DEFAULT 20,
                    credits_per_image INTEGER DEFAULT 5,
                    additional_config JSON,
                    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
                )
            """
            )
            print("   ✅ google_images_config表已创建")

        # 确保有默认配置记录
        cursor.execute("SELECT id FROM google_images_config WHERE id = 'default'")
        if not cursor.fetchone():
            print("   📝 插入默认Google Images配置...")
            cursor.execute(
                """
                INSERT INTO google_images_config
                (id, enabled, base_url, api_key, default_model, max_images_per_request, 
                 timeout, credits_per_generation, credits_per_image, additional_config)
                VALUES
                ('default', 0, 'https://api.googleimages.ai', '', 'nano-banana', 10,
                 120, 20, 5, '{}')
            """
            )
            print("   ✅ 默认Google Images配置已插入")

        conn.commit()
        print("✅ Google Images配置表修复完成")
        return True

    except Exception as e:
        print(f"❌ 修复Google Images配置表失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def fix_dreamwork_tasks_table():
    """修复DreamWork任务表"""
    print("🔧 修复DreamWork任务表...")

    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='dreamwork_tasks'"
        )
        if not cursor.fetchone():
            print("   ❌ dreamwork_tasks表不存在，需要完整创建")
            return False

        # 检查cloud_image_url列是否存在
        cursor.execute("PRAGMA table_info(dreamwork_tasks)")
        columns = [row[1] for row in cursor.fetchall()]

        if "cloud_image_url" not in columns:
            print("   📝 添加cloud_image_url列...")
            cursor.execute(
                "ALTER TABLE dreamwork_tasks ADD COLUMN cloud_image_url TEXT"
            )
            print("   ✅ cloud_image_url列已添加")

        # 检查其他可能缺失的列
        missing_columns = []
        expected_columns = {
            "input_images": "JSON",
            "cloud_input_images": "JSON",
            "result_images": "JSON",
            "cloud_result_images": "JSON",
        }

        for col_name, col_type in expected_columns.items():
            if col_name not in columns:
                missing_columns.append((col_name, col_type))

        for col_name, col_type in missing_columns:
            print(f"   📝 添加{col_name}列...")
            cursor.execute(
                f"ALTER TABLE dreamwork_tasks ADD COLUMN {col_name} {col_type}"
            )
            print(f"   ✅ {col_name}列已添加")

        conn.commit()
        print("✅ DreamWork任务表修复完成")
        return True

    except Exception as e:
        print(f"❌ 修复DreamWork任务表失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def fix_all_missing_tables_and_columns():
    """修复所有缺失的表和列"""
    print("🔧 全面修复所有表结构问题...")

    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 定义所有需要的表和它们的结构
        table_definitions = {
            "veo_config": """
                CREATE TABLE IF NOT EXISTS veo_config (
                    id VARCHAR(255) NOT NULL PRIMARY KEY DEFAULT 'default',
                    base_url VARCHAR(500) NOT NULL DEFAULT 'https://api.veo.ai',
                    enabled BOOLEAN NOT NULL DEFAULT 0,
                    api_key TEXT,
                    model_credits_config JSON,
                    query_interval INTEGER NOT NULL DEFAULT 15000,
                    default_enhance_prompt BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
                )
            """,
            "generated_files": """
                CREATE TABLE IF NOT EXISTS generated_files (
                    id VARCHAR(255) NOT NULL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    service_type VARCHAR(50) NOT NULL,
                    task_id VARCHAR(255),
                    original_filename VARCHAR(255),
                    stored_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    cloud_url VARCHAR(500),
                    file_type VARCHAR(50) NOT NULL,
                    file_size INTEGER,
                    mime_type VARCHAR(100),
                    upload_status VARCHAR(20) DEFAULT 'pending',
                    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
                )
            """,
        }

        # 创建缺失的表
        for table_name, create_sql in table_definitions.items():
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if not cursor.fetchone():
                print(f"   📝 创建{table_name}表...")
                cursor.execute(create_sql)
                print(f"   ✅ {table_name}表已创建")

        # 修复所有任务表的云存储列
        task_tables = [
            "mj_tasks",
            "dreamwork_tasks",
            "flux_tasks",
            "kling_tasks",
            "veo_tasks",
            "google_images_tasks",
        ]
        cloud_columns = [
            ("cloud_image_url", "TEXT"),
            ("input_images", "JSON"),
            ("cloud_input_images", "JSON"),
            ("result_images", "JSON"),
            ("cloud_result_images", "JSON"),
        ]

        for table_name in task_tables:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if cursor.fetchone():
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_columns = [row[1] for row in cursor.fetchall()]

                for col_name, col_type in cloud_columns:
                    if col_name not in existing_columns:
                        try:
                            cursor.execute(
                                f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                            )
                            print(f"   ✅ 添加{table_name}.{col_name}")
                        except Exception as e:
                            if "duplicate column name" not in str(e):
                                print(f"   ⚠️ 添加{table_name}.{col_name}失败: {e}")

        # 特殊处理veo_tasks的enhance_prompt列
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='veo_tasks'"
        )
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(veo_tasks)")
            veo_columns = [row[1] for row in cursor.fetchall()]
            if "enhance_prompt" not in veo_columns:
                cursor.execute(
                    "ALTER TABLE veo_tasks ADD COLUMN enhance_prompt BOOLEAN NOT NULL DEFAULT 1"
                )
                print("   ✅ 添加veo_tasks.enhance_prompt")

        # 修复积分表结构
        credit_tables = [
            "google_images_credits",
            "veo_credits",
            "comfyui_credits",
            "dreamwork_credits",
        ]
        credit_columns = [
            ("credits_before", "INTEGER"),
            ("credits_after", "INTEGER"),
            ("model_name", "VARCHAR(50)"),
            ("description", "TEXT"),
        ]

        for table_name in credit_tables:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if cursor.fetchone():
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_columns = [row[1] for row in cursor.fetchall()]

                for col_name, col_type in credit_columns:
                    if col_name not in existing_columns:
                        try:
                            cursor.execute(
                                f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                            )
                            print(f"   ✅ 添加{table_name}.{col_name}")
                        except Exception as e:
                            if "duplicate column name" not in str(e):
                                print(f"   ⚠️ 添加{table_name}.{col_name}失败: {e}")

        conn.commit()
        print("✅ 全面表结构修复完成")
        return True

    except Exception as e:
        print(f"❌ 全面修复失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_fix():
    """验证修复结果"""
    print("\n🔍 验证修复结果...")

    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 验证关键表是否存在
        critical_tables = [
            "cloud_storage_config",
            "google_images_config",
            "veo_config",
            "generated_files",
            "dreamwork_tasks",
            "veo_tasks",
            "google_images_tasks",
        ]

        all_good = True
        for table in critical_tables:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            if cursor.fetchone():
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} - 仍然缺失")
                all_good = False

        # 验证关键列是否存在
        if all_good:
            # 检查dreamwork_tasks.cloud_image_url
            cursor.execute("PRAGMA table_info(dreamwork_tasks)")
            dreamwork_columns = [row[1] for row in cursor.fetchall()]
            if "cloud_image_url" in dreamwork_columns:
                print("   ✅ dreamwork_tasks.cloud_image_url")
            else:
                print("   ❌ dreamwork_tasks.cloud_image_url - 仍然缺失")
                all_good = False

            # 检查veo_tasks.enhance_prompt
            cursor.execute("PRAGMA table_info(veo_tasks)")
            veo_columns = [row[1] for row in cursor.fetchall()]
            if "enhance_prompt" in veo_columns:
                print("   ✅ veo_tasks.enhance_prompt")
            else:
                print("   ❌ veo_tasks.enhance_prompt - 仍然缺失")
                all_good = False

        return all_good

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        conn.close()


def main():
    """主函数"""
    print("🚨 紧急修复全新部署的表结构问题")
    print("=" * 60)
    print("根据用户反馈的错误日志进行修复:")
    print("• cloud_storage_config表created_at约束问题")
    print("• google_images_config表不存在")
    print("• dreamwork_tasks.cloud_image_url列缺失")
    print()

    fixes = [
        ("云存储配置表", fix_cloud_storage_config_table),
        ("Google Images配置表", fix_google_images_config_table),
        ("DreamWork任务表", fix_dreamwork_tasks_table),
        ("所有表结构", fix_all_missing_tables_and_columns),
    ]

    success_count = 0

    for name, fix_func in fixes:
        print(f"🔧 修复{name}...")
        if fix_func():
            success_count += 1
            print(f"✅ {name}修复成功\n")
        else:
            print(f"❌ {name}修复失败\n")

    print("=" * 60)
    print(f"修复结果: {success_count}/{len(fixes)} 项成功")

    if success_count == len(fixes):
        if verify_fix():
            print("🎉 所有修复完成并验证通过!")
            print("\n📋 建议操作:")
            print("1. 重启你的Web应用")
            print("2. 重新测试所有AI服务功能")
            print("3. 在管理界面配置API密钥")
            return True
        else:
            print("❌ 修复完成但验证失败")
            return False
    else:
        print("❌ 部分修复失败，请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
