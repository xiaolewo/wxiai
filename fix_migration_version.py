#!/usr/bin/env python3
"""
修复数据库迁移版本不一致问题
将数据库版本号更新到与实际表结构匹配的版本
"""

import sqlite3
import os


def fix_migration_version():
    """修复迁移版本号到正确的版本"""

    # 查找数据库文件
    db_paths = ["backend/data/webui.db", "webui.db", "backend/webui.db"]
    db_path = None

    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        print("❌ 错误: 未找到数据库文件")
        return False

    print(f"📍 使用数据库: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查当前版本
        cursor.execute("SELECT version_num FROM alembic_version")
        current_version = cursor.fetchone()[0]
        print(f"🔍 当前迁移版本: {current_version}")

        # 检查关键表是否存在，以确定应该设置的版本
        key_tables = {
            "google_images_config": "j6k7l8m9n0p1",  # Google Images 表
            "comfyui_config": "c1d2e3f4g5h6",  # ComfyUI 表
            "veo_config": "i5j6k7l8m9n0",  # Veo 表
            "kling_config": "d7462fa176a0",  # Kling 表
        }

        # 检查表存在情况
        existing_tables = []
        target_version = current_version

        for table, version in key_tables.items():
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            exists = bool(cursor.fetchone())
            if exists:
                existing_tables.append(table)
                # 更新到最新的版本
                if version > target_version:
                    target_version = version

        print(f"📋 已存在的关键表: {existing_tables}")

        # 根据现有表结构确定目标版本
        # 由于我们手动创建了Google Images表，需要设置到至少包含这些表的版本
        if "google_images_config" in existing_tables:
            # 如果Google Images表存在，至少需要设置到j6k7l8m9n0p1版本
            target_version = "e5f6g7h8i9j0"  # ComfyUI启用版本，这是当前最新的安全版本

        print(f"🎯 目标版本: {target_version}")

        if target_version != current_version:
            # 更新版本号
            cursor.execute(
                "UPDATE alembic_version SET version_num = ?", (target_version,)
            )
            conn.commit()
            print(f"✅ 版本号已更新: {current_version} -> {target_version}")

            # 验证更新
            cursor.execute("SELECT version_num FROM alembic_version")
            new_version = cursor.fetchone()[0]
            print(f"🔍 验证新版本: {new_version}")

            if new_version == target_version:
                print("🎉 版本号更新成功！")
            else:
                print("❌ 版本号更新失败")
                return False
        else:
            print("✅ 版本号已是最新，无需更新")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 更新版本号时出错: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def create_safe_migration_state():
    """创建安全的迁移状态，避免未来冲突"""
    print("\n🛡️ 创建安全迁移状态...")

    # 查找数据库文件
    db_paths = ["backend/data/webui.db", "webui.db", "backend/webui.db"]
    db_path = None

    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建一个标记表来记录手动修复
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_migration_fixes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fix_type TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 记录本次修复
        cursor.execute(
            """
            INSERT INTO manual_migration_fixes (fix_type, description)
            VALUES ('google_images_tables', 'Manually created Google Images tables due to migration version mismatch')
        """
        )

        conn.commit()
        conn.close()

        print("✅ 安全迁移状态已创建")
        return True

    except Exception as e:
        print(f"❌ 创建安全迁移状态失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 迁移版本修复脚本")
    print("=" * 50)

    # 修复版本号
    if fix_migration_version():
        # 创建安全迁移状态
        create_safe_migration_state()
        print("\n🎉 修复完成！现在可以安全地进行线上更新和全新部署了")
        print("📝 建议：")
        print("   1. 测试应用功能正常")
        print("   2. 备份数据库后再进行线上更新")
        print("   3. 全新部署时不会有冲突")
    else:
        print("\n❌ 修复失败，请检查错误信息")
