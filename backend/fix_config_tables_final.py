#!/usr/bin/env python3
"""
最终修复配置表问题
"""

import sqlite3
import os


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


def fix_config_tables():
    """修复配置表问题"""
    print("🔧 最终修复配置表...")

    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 1. 删除并重建cloud_storage_config表
        print("   🗑️ 重建cloud_storage_config表...")
        cursor.execute("DROP TABLE IF EXISTS cloud_storage_config")
        cursor.execute(
            """
            CREATE TABLE cloud_storage_config (
                id TEXT PRIMARY KEY DEFAULT 'default',
                provider TEXT NOT NULL DEFAULT 'tencent-cos',
                enabled INTEGER NOT NULL DEFAULT 0,
                secret_id TEXT DEFAULT '',
                secret_key TEXT DEFAULT '',
                region TEXT DEFAULT 'ap-beijing',
                bucket TEXT DEFAULT '',
                domain TEXT DEFAULT '',
                auto_upload INTEGER NOT NULL DEFAULT 1,
                allowed_types TEXT DEFAULT '["image/*", "video/*"]',
                max_file_size INTEGER DEFAULT 104857600,
                base_path TEXT DEFAULT 'generated/',
                image_path TEXT DEFAULT 'images/',
                video_path TEXT DEFAULT 'videos/',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """
        )

        cursor.execute(
            """
            INSERT INTO cloud_storage_config (id, provider, enabled, secret_id, secret_key, region, bucket, domain,
             auto_upload, allowed_types, max_file_size, base_path, image_path, video_path)
            VALUES ('default', 'tencent-cos', 0, '', '', 'ap-beijing', '', '', 1, 
             '["image/*", "video/*"]', 104857600, 'generated/', 'images/', 'videos/')
        """
        )
        print("   ✅ cloud_storage_config表重建完成")

        # 2. 删除并重建google_images_config表
        print("   🗑️ 重建google_images_config表...")
        cursor.execute("DROP TABLE IF EXISTS google_images_config")
        cursor.execute(
            """
            CREATE TABLE google_images_config (
                id TEXT PRIMARY KEY DEFAULT 'default',
                enabled INTEGER NOT NULL DEFAULT 0,
                base_url TEXT NOT NULL DEFAULT 'https://api.googleimages.ai',
                api_key TEXT DEFAULT '',
                default_model TEXT DEFAULT 'nano-banana',
                max_images_per_request INTEGER DEFAULT 10,
                timeout INTEGER DEFAULT 120,
                credits_per_generation INTEGER DEFAULT 20,
                credits_per_image INTEGER DEFAULT 5,
                additional_config TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """
        )

        cursor.execute(
            """
            INSERT INTO google_images_config (id, enabled, base_url, api_key, default_model, 
             max_images_per_request, timeout, credits_per_generation, credits_per_image, additional_config)
            VALUES ('default', 0, 'https://api.googleimages.ai', '', 'nano-banana', 
             10, 120, 20, 5, '{}')
        """
        )
        print("   ✅ google_images_config表重建完成")

        # 3. 确保veo_config表正确
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='veo_config'"
        )
        if not cursor.fetchone():
            print("   📝 创建veo_config表...")
            cursor.execute(
                """
                CREATE TABLE veo_config (
                    id TEXT PRIMARY KEY DEFAULT 'default',
                    base_url TEXT NOT NULL DEFAULT 'https://api.veo.ai',
                    enabled INTEGER NOT NULL DEFAULT 0,
                    api_key TEXT DEFAULT '',
                    model_credits_config TEXT DEFAULT '{}',
                    query_interval INTEGER NOT NULL DEFAULT 15000,
                    default_enhance_prompt INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """
            )

            cursor.execute(
                """
                INSERT INTO veo_config (id, base_url, enabled, api_key, model_credits_config, 
                 query_interval, default_enhance_prompt)
                VALUES ('default', 'https://api.veo.ai', 0, '', '{}', 15000, 1)
            """
            )
            print("   ✅ veo_config表创建完成")

        conn.commit()
        print("✅ 配置表修复完成")
        return True

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def test_functionality():
    """测试功能是否正常"""
    print("\n🔍 测试修复后的功能...")

    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 测试各个配置表的查询
        test_queries = [
            (
                "cloud_storage_config",
                "SELECT * FROM cloud_storage_config WHERE id = 'default'",
            ),
            (
                "google_images_config",
                "SELECT * FROM google_images_config WHERE id = 'default'",
            ),
            (
                "dreamwork_tasks",
                "SELECT id, cloud_image_url FROM dreamwork_tasks LIMIT 1",
            ),
        ]

        all_good = True
        for table_name, query in test_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                print(f"   ✅ {table_name} 查询正常")
            except Exception as e:
                print(f"   ❌ {table_name} 查询失败: {e}")
                all_good = False

        return all_good

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚨 最终修复配置表问题")
    print("=" * 40)

    if fix_config_tables():
        if test_functionality():
            print("\n🎉 修复完成！现在可以重启应用测试功能")
        else:
            print("\n❌ 修复完成但测试失败")
    else:
        print("\n❌ 修复失败")
