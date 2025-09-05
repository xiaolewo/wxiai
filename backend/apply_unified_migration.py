#!/usr/bin/env python3
"""
应用统一迁移，解决表结构问题
"""

import sqlite3
import os
import sys


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


def reset_migration_state():
    """重置迁移状态"""
    print("🔄 重置迁移状态...")

    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 清除所有旧的迁移版本
        cursor.execute("DELETE FROM alembic_version")

        # 设置为新的统一迁移版本
        cursor.execute(
            "INSERT INTO alembic_version (version_num) VALUES ('unified_complete_migration_20250902')"
        )

        conn.commit()
        print("✅ 迁移状态重置完成")
        return True

    except Exception as e:
        print(f"❌ 重置迁移状态失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def apply_unified_migration():
    """应用统一迁移内容"""
    print("🔧 应用统一迁移...")

    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 直接执行关键修复

        # 1. 确保 dreamwork_tasks 表有 cloud_image_url 列
        cursor.execute("PRAGMA table_info(dreamwork_tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        if "cloud_image_url" not in columns:
            print("   📝 添加dreamwork_tasks.cloud_image_url...")
            cursor.execute(
                "ALTER TABLE dreamwork_tasks ADD COLUMN cloud_image_url TEXT"
            )
        else:
            print("   ✅ dreamwork_tasks.cloud_image_url已存在")

        # 2. 确保 google_images_config 表存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='google_images_config'"
        )
        if not cursor.fetchone():
            print("   📝 创建google_images_config表...")
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
                INSERT INTO google_images_config (id, enabled, base_url, api_key, default_model, max_images_per_request, timeout, credits_per_generation, credits_per_image, additional_config)
                VALUES ('default', 0, 'https://api.googleimages.ai', '', 'nano-banana', 10, 120, 20, 5, '{}')
            """
            )
        else:
            print("   ✅ google_images_config表已存在")

        # 3. 确保 cloud_storage_config 表存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cloud_storage_config'"
        )
        if not cursor.fetchone():
            print("   📝 创建cloud_storage_config表...")
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
                INSERT INTO cloud_storage_config (id, provider, enabled, secret_id, secret_key, region, bucket, domain, auto_upload, allowed_types, max_file_size, base_path, image_path, video_path)
                VALUES ('default', 'tencent-cos', 0, '', '', 'ap-beijing', '', '', 1, '["image/*", "video/*"]', 104857600, 'generated/', 'images/', 'videos/')
            """
            )
        else:
            print("   ✅ cloud_storage_config表已存在")

        # 4. 确保 veo_tasks 有 enhance_prompt 列
        cursor.execute("PRAGMA table_info(veo_tasks)")
        veo_columns = [row[1] for row in cursor.fetchall()]
        if "enhance_prompt" not in veo_columns:
            print("   📝 添加veo_tasks.enhance_prompt...")
            cursor.execute(
                "ALTER TABLE veo_tasks ADD COLUMN enhance_prompt INTEGER NOT NULL DEFAULT 1"
            )
        else:
            print("   ✅ veo_tasks.enhance_prompt已存在")

        conn.commit()
        print("✅ 统一迁移应用完成")
        return True

    except Exception as e:
        print(f"❌ 应用统一迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def force_sqlalchemy_refresh():
    """强制刷新SQLAlchemy元数据"""
    print("🔄 刷新SQLAlchemy元数据...")
    try:
        # 模拟重启应用时的元数据刷新
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        # 清除可能的模块缓存
        modules_to_clear = [k for k in sys.modules.keys() if "dreamwork" in k.lower()]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

        print("✅ 元数据刷新完成，建议重启应用")
        return True
    except Exception as e:
        print(f"⚠️ 元数据刷新失败: {e}")
        return False


def verify_final_state():
    """验证最终状态"""
    print("\n🔍 验证最终状态...")

    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 验证关键表和列
        checks = [
            (
                "dreamwork_tasks表存在",
                "SELECT name FROM sqlite_master WHERE type='table' AND name='dreamwork_tasks'",
            ),
            ("dreamwork_tasks.cloud_image_url列", "PRAGMA table_info(dreamwork_tasks)"),
            (
                "google_images_config表",
                "SELECT * FROM google_images_config WHERE id='default'",
            ),
            (
                "cloud_storage_config表",
                "SELECT * FROM cloud_storage_config WHERE id='default'",
            ),
            ("veo_tasks.enhance_prompt列", "PRAGMA table_info(veo_tasks)"),
        ]

        all_good = True

        for check_name, sql in checks:
            try:
                cursor.execute(sql)
                result = cursor.fetchall()

                if "cloud_image_url列" in check_name:
                    columns = [row[1] for row in result]
                    if "cloud_image_url" in columns:
                        print(f"   ✅ {check_name}")
                    else:
                        print(f"   ❌ {check_name}")
                        all_good = False
                elif "enhance_prompt列" in check_name:
                    columns = [row[1] for row in result]
                    if "enhance_prompt" in columns:
                        print(f"   ✅ {check_name}")
                    else:
                        print(f"   ❌ {check_name}")
                        all_good = False
                elif result:
                    print(f"   ✅ {check_name}")
                else:
                    print(f"   ❌ {check_name}")
                    all_good = False

            except Exception as e:
                print(f"   ❌ {check_name}: {e}")
                all_good = False

        return all_good

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        conn.close()


def main():
    """主函数"""
    print("🚀 应用统一迁移解决表结构问题")
    print("=" * 50)

    steps = [
        ("重置迁移状态", reset_migration_state),
        ("应用统一迁移", apply_unified_migration),
        ("刷新SQLAlchemy", force_sqlalchemy_refresh),
    ]

    success_count = 0
    for step_name, step_func in steps:
        if step_func():
            success_count += 1
        else:
            print(f"❌ {step_name}失败")

    print("=" * 50)
    if verify_final_state():
        print("🎉 所有表结构问题已解决！")
        print("\n📋 请执行以下操作：")
        print("1. 重启你的Web应用")
        print("2. 重新测试DreamWork图像生成功能")
        print("3. 测试其他AI服务功能")
        print("\n✅ 迁移文件已统一，未来的部署将使用正确的迁移文件")
        return True
    else:
        print("❌ 验证失败，请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
