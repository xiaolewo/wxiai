#!/usr/bin/env python3
"""
修复缺失的表字段
根据功能检查结果，添加所有缺失的字段
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


def add_missing_fields():
    """添加所有缺失的字段"""
    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 使用数据库: {db_path}")
    cursor = conn.cursor()

    try:
        print("🔧 修复缺失字段...")

        # 1. 修复Kling配置表 - 添加access_key字段
        print("\n📊 修复 Kling 配置表...")
        try:
            cursor.execute("PRAGMA table_info(kling_config)")
            columns = [row[1] for row in cursor.fetchall()]
            if "access_key" not in columns:
                cursor.execute("ALTER TABLE kling_config ADD COLUMN access_key TEXT")
                print("   ✅ 添加 kling_config.access_key 字段")
            else:
                print("   ✅ kling_config.access_key 字段已存在")
        except Exception as e:
            print(f"   ❌ 修复 kling_config 失败: {e}")

        # 2. 修复Kling Lip Sync配置表 - 添加access_key字段
        print("\n📊 修复 Kling Lip Sync 配置表...")
        try:
            cursor.execute("PRAGMA table_info(kling_lip_sync_config)")
            columns = [row[1] for row in cursor.fetchall()]
            if "access_key" not in columns:
                cursor.execute(
                    "ALTER TABLE kling_lip_sync_config ADD COLUMN access_key TEXT"
                )
                print("   ✅ 添加 kling_lip_sync_config.access_key 字段")
            else:
                print("   ✅ kling_lip_sync_config.access_key 字段已存在")
        except Exception as e:
            print(f"   ❌ 修复 kling_lip_sync_config 失败: {e}")

        # 3. 修复Jimeng配置表 - 添加access_key字段
        print("\n📊 修复 Jimeng 配置表...")
        try:
            cursor.execute("PRAGMA table_info(jimeng_config)")
            columns = [row[1] for row in cursor.fetchall()]
            if "access_key" not in columns:
                cursor.execute("ALTER TABLE jimeng_config ADD COLUMN access_key TEXT")
                print("   ✅ 添加 jimeng_config.access_key 字段")
            else:
                print("   ✅ jimeng_config.access_key 字段已存在")
        except Exception as e:
            print(f"   ❌ 修复 jimeng_config 失败: {e}")

        # 4. 修复Jimeng Inpainting配置表 - 添加access_key字段
        print("\n📊 修复 Jimeng Inpainting 配置表...")
        try:
            cursor.execute("PRAGMA table_info(jimeng_inpainting_config)")
            columns = [row[1] for row in cursor.fetchall()]
            if "access_key" not in columns:
                cursor.execute(
                    "ALTER TABLE jimeng_inpainting_config ADD COLUMN access_key TEXT"
                )
                print("   ✅ 添加 jimeng_inpainting_config.access_key 字段")
            else:
                print("   ✅ jimeng_inpainting_config.access_key 字段已存在")
        except Exception as e:
            print(f"   ❌ 修复 jimeng_inpainting_config 失败: {e}")

        # 5. 修复Jimeng Inpainting任务表 - 添加prompt和image_url字段
        print("\n📊 修复 Jimeng Inpainting 任务表...")
        try:
            cursor.execute("PRAGMA table_info(jimeng_inpainting_tasks)")
            columns = [row[1] for row in cursor.fetchall()]

            if "prompt" not in columns:
                cursor.execute(
                    "ALTER TABLE jimeng_inpainting_tasks ADD COLUMN prompt TEXT"
                )
                print("   ✅ 添加 jimeng_inpainting_tasks.prompt 字段")
            else:
                print("   ✅ jimeng_inpainting_tasks.prompt 字段已存在")

            if "image_url" not in columns:
                cursor.execute(
                    "ALTER TABLE jimeng_inpainting_tasks ADD COLUMN image_url TEXT"
                )
                print("   ✅ 添加 jimeng_inpainting_tasks.image_url 字段")
            else:
                print("   ✅ jimeng_inpainting_tasks.image_url 字段已存在")
        except Exception as e:
            print(f"   ❌ 修复 jimeng_inpainting_tasks 失败: {e}")

        # 6. 修复Jimeng Outpainting配置表 - 添加access_key字段
        print("\n📊 修复 Jimeng Outpainting 配置表...")
        try:
            cursor.execute("PRAGMA table_info(jimeng_outpainting_config)")
            columns = [row[1] for row in cursor.fetchall()]
            if "access_key" not in columns:
                cursor.execute(
                    "ALTER TABLE jimeng_outpainting_config ADD COLUMN access_key TEXT"
                )
                print("   ✅ 添加 jimeng_outpainting_config.access_key 字段")
            else:
                print("   ✅ jimeng_outpainting_config.access_key 字段已存在")
        except Exception as e:
            print(f"   ❌ 修复 jimeng_outpainting_config 失败: {e}")

        # 7. 修复Jimeng Outpainting任务表 - 添加prompt和image_url字段
        print("\n📊 修复 Jimeng Outpainting 任务表...")
        try:
            cursor.execute("PRAGMA table_info(jimeng_outpainting_tasks)")
            columns = [row[1] for row in cursor.fetchall()]

            if "prompt" not in columns:
                cursor.execute(
                    "ALTER TABLE jimeng_outpainting_tasks ADD COLUMN prompt TEXT"
                )
                print("   ✅ 添加 jimeng_outpainting_tasks.prompt 字段")
            else:
                print("   ✅ jimeng_outpainting_tasks.prompt 字段已存在")

            if "image_url" not in columns:
                cursor.execute(
                    "ALTER TABLE jimeng_outpainting_tasks ADD COLUMN image_url TEXT"
                )
                print("   ✅ 添加 jimeng_outpainting_tasks.image_url 字段")
            else:
                print("   ✅ jimeng_outpainting_tasks.image_url 字段已存在")
        except Exception as e:
            print(f"   ❌ 修复 jimeng_outpainting_tasks 失败: {e}")

        # 8. 修复Veo任务表 - 添加video_url字段
        print("\n📊 修复 Veo 任务表...")
        try:
            cursor.execute("PRAGMA table_info(veo_tasks)")
            columns = [row[1] for row in cursor.fetchall()]

            if "video_url" not in columns:
                cursor.execute("ALTER TABLE veo_tasks ADD COLUMN video_url TEXT")
                print("   ✅ 添加 veo_tasks.video_url 字段")
            else:
                print("   ✅ veo_tasks.video_url 字段已存在")
        except Exception as e:
            print(f"   ❌ 修复 veo_tasks 失败: {e}")

        conn.commit()
        conn.close()
        print("\n✅ 所有缺失字段修复完成！")
        return True

    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        conn.rollback()
        conn.close()
        return False


def add_default_configurations():
    """为缺少配置记录的服务添加默认配置"""
    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        print("\n🔧 添加默认配置记录...")

        # 检查并添加Kling配置
        cursor.execute("SELECT COUNT(*) FROM kling_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO kling_config (enabled, base_url, access_key, timeout, credits_per_generation)
                VALUES (0, 'https://api.kling.kuaishou.com', '', 300, 50)
            """
            )
            print("   ✅ 添加 Kling 默认配置")

        # 检查并添加Jimeng配置
        cursor.execute("SELECT COUNT(*) FROM jimeng_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO jimeng_config (enabled, base_url, access_key, timeout, credits_per_generation)
                VALUES (0, 'https://api.jimeng.ai', '', 300, 30)
            """
            )
            print("   ✅ 添加 Jimeng 默认配置")

        # 检查并添加Jimeng Outpainting配置
        cursor.execute("SELECT COUNT(*) FROM jimeng_outpainting_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO jimeng_outpainting_config (enabled, base_url, access_key, timeout, credits_per_generation)
                VALUES (0, 'https://api.jimeng.ai', '', 300, 20)
            """
            )
            print("   ✅ 添加 Jimeng Outpainting 默认配置")

        # 检查并添加Veo配置
        cursor.execute("SELECT COUNT(*) FROM veo_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO veo_config (enabled, base_url, api_key, timeout, credits_per_generation)
                VALUES (0, 'https://api.veo.com', '', 300, 80)
            """
            )
            print("   ✅ 添加 Veo 默认配置")

        # 检查并添加MidJourney配置
        cursor.execute("SELECT COUNT(*) FROM mj_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO mj_config (enabled, base_url, api_key, timeout, credits_per_generation)
                VALUES (0, 'https://api.midjourney.com', '', 300, 25)
            """
            )
            print("   ✅ 添加 MidJourney 默认配置")

        # 检查并添加DreamWork配置
        cursor.execute("SELECT COUNT(*) FROM dreamwork_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO dreamwork_config (enabled, base_url, api_key, timeout, credits_per_generation)
                VALUES (0, 'https://api.dreamwork.com', '', 300, 15)
            """
            )
            print("   ✅ 添加 DreamWork 默认配置")

        conn.commit()
        conn.close()
        print("✅ 默认配置添加完成！")
        return True

    except Exception as e:
        print(f"❌ 添加默认配置失败: {e}")
        conn.rollback()
        conn.close()
        return False


def main():
    """主函数"""
    print("🚀 修复缺失字段和配置")
    print("=" * 50)

    # 1. 添加缺失字段
    print("第一步：添加缺失字段")
    if not add_missing_fields():
        print("❌ 字段修复失败")
        return

    # 2. 添加默认配置
    print("\n第二步：添加默认配置")
    add_default_configurations()

    print("\n" + "=" * 50)
    print("🎉 修复完成！")
    print("✅ 现在所有AI服务都应该有完整的表结构和字段")
    print("建议重新运行功能检查脚本来验证修复结果")


if __name__ == "__main__":
    main()
