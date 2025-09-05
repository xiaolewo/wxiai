#!/usr/bin/env python3
"""
测试ComfyUI配置保存功能
"""

import os
import sys


def test_config_save():
    """测试配置保存"""
    print("🔧 测试ComfyUI配置保存功能...")

    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        from open_webui.models.comfyui import ComfyUIConfigs, ComfyUIConfigForm

        # 模拟配置数据（使用测试密钥）
        test_form = ComfyUIConfigForm(
            access_key="test_access_key_123",
            secret_key="test_secret_key_456",
            base_url="https://openapi.liblibai.cloud",
            enabled=True,
            timeout=300,
            max_concurrent_tasks=5,
        )

        print("📝 尝试保存测试配置...")
        print(f"   Access Key: {test_form.access_key}")
        print(f"   Secret Key: {test_form.secret_key}")
        print(f"   Base URL: {test_form.base_url}")
        print(f"   Enabled: {test_form.enabled}")

        # 保存配置
        saved_config = ComfyUIConfigs.create_or_update_config(test_form)

        if saved_config:
            print(f"✅ 配置保存成功!")
            print(f"   保存后的Access Key: {saved_config.access_key}")
            print(f"   保存后的Secret Key: {saved_config.secret_key}")
            print(f"   保存后的ID: {saved_config.id}")
        else:
            print("❌ 配置保存失败")
            return False

        # 验证保存结果
        print("\n🔍 验证保存结果...")
        retrieved_config = ComfyUIConfigs.get_config()

        if retrieved_config:
            print(f"✅ 配置读取成功:")
            print(f"   读取的Access Key: {retrieved_config.access_key}")
            print(f"   读取的Secret Key: {retrieved_config.secret_key}")
            print(f"   读取的Base URL: {retrieved_config.base_url}")
            print(f"   读取的Enabled: {retrieved_config.enabled}")

            # 检查是否匹配
            if (
                retrieved_config.access_key == test_form.access_key
                and retrieved_config.secret_key == test_form.secret_key
            ):
                print("✅ 配置保存和读取完全正确!")
                return True
            else:
                print("❌ 配置保存后读取不匹配")
                return False
        else:
            print("❌ 无法读取保存的配置")
            return False

    except Exception as e:
        print(f"❌ 测试配置保存失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def check_database_direct():
    """直接检查数据库"""
    print("\n🔍 直接检查数据库...")

    import sqlite3

    db_paths = [
        "data/webui.db",
        "backend/data/webui.db",
        "webui.db",
        "backend/webui.db",
    ]
    conn = None

    for path in db_paths:
        if os.path.exists(path):
            conn = sqlite3.connect(path)
            break

    if not conn:
        print("❌ 无法连接数据库")
        return

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, access_key, secret_key, base_url, enabled FROM comfyui_config"
        )
        rows = cursor.fetchall()

        print(f"📊 数据库中的配置记录 ({len(rows)} 条):")
        for row in rows:
            print(f"   ID: {row[0]}")
            print(f"   Access Key: {row[1] or '(空)'}")
            print(f"   Secret Key: {row[2] or '(空)'}")
            print(f"   Base URL: {row[3]}")
            print(f"   Enabled: {row[4]}")
            print()

    except Exception as e:
        print(f"❌ 查询数据库失败: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 开始测试ComfyUI配置保存...")
    print("=" * 60)

    # 首先检查当前数据库状态
    check_database_direct()

    # 测试配置保存
    if test_config_save():
        print("\n🎉 配置保存功能正常!")
        print("💡 如果Web界面无法保存配置，可能是:")
        print("   1. 前端表单数据未正确发送")
        print("   2. API路由权限问题")
        print("   3. 网络请求失败")

        # 再次检查数据库
        check_database_direct()
    else:
        print("\n❌ 配置保存功能存在问题")
