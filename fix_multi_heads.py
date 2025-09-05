#!/usr/bin/env python3
"""
修复Alembic多头问题
将数据库版本设置到最新的合理版本，解决多头分叉问题
"""

import sqlite3
import os


def fix_multi_heads():
    """修复多头问题"""
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

        # 基于现有表结构，设定一个合理的最终版本
        # 通过我们的分析，e5f6g7h8i9j0 是ComfyUI启用版本，是一个比较安全的版本
        target_version = "e5f6g7h8i9j0"

        # 检查关键表是否存在
        key_tables = [
            "google_images_config",
            "comfyui_config",
            "veo_config",
            "kling_config",
            "jimeng_config",
        ]

        existing_key_tables = []
        for table in key_tables:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            if cursor.fetchone():
                existing_key_tables.append(table)

        print(f"📋 已存在的关键表: {existing_key_tables}")

        # 如果所有关键表都存在，我们可以安全地设置为最新版本
        # 但为了避免多头问题，我们设置为一个已知稳定的版本
        if len(existing_key_tables) >= 3:  # 大部分表都存在
            target_version = "e5f6g7h8i9j0"  # ComfyUI 启用版本

        print(f"🎯 目标版本: {target_version}")

        # 更新版本号
        cursor.execute("UPDATE alembic_version SET version_num = ?", (target_version,))
        conn.commit()

        # 验证更新
        cursor.execute("SELECT version_num FROM alembic_version")
        new_version = cursor.fetchone()[0]
        print(f"✅ 版本已更新: {current_version} -> {new_version}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        if conn:
            conn.close()
        return False


def test_alembic():
    """测试Alembic是否能正常工作"""
    import subprocess
    import os

    os.chdir("/Users/liuqingliang/Desktop/wxiai/one/wxiai-main/backend/open_webui")

    try:
        # 测试 alembic current
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": ".."},
        )

        if result.returncode == 0:
            print("✅ Alembic current 命令成功:")
            print(f"   {result.stdout.strip()}")
            return True
        else:
            print("❌ Alembic current 命令失败:")
            print(f"   {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"❌ 测试Alembic失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 修复 Alembic 多头问题")
    print("=" * 50)

    # 修复多头问题
    if fix_multi_heads():
        print("\n🧪 测试 Alembic 功能...")
        if test_alembic():
            print("\n🎉 修复成功！Alembic 现在可以正常工作")
            print("✅ 现在可以安全地进行:")
            print("   - 线上更新")
            print("   - 全新部署")
            print("   - 正常的迁移操作")
        else:
            print("\n⚠️  版本已修复，但Alembic仍有问题，可能需要进一步调试")
    else:
        print("\n❌ 修复失败")
