#!/usr/bin/env python3
"""
修复ComfyUI配置问题 - 检查并提供配置指引
"""

import os
import sys
import sqlite3


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


def check_and_show_comfyui_config():
    """检查并显示ComfyUI配置状态"""
    print("🔍 检查ComfyUI配置状态...")

    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='comfyui_config'"
        )
        if not cursor.fetchone():
            print("❌ comfyui_config表不存在")
            return False

        # 获取表结构
        cursor.execute("PRAGMA table_info(comfyui_config)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 表结构: {columns}")

        # 检查配置记录
        cursor.execute("SELECT * FROM comfyui_config")
        configs = cursor.fetchall()

        if not configs:
            print("📋 ComfyUI配置表为空")
            return False

        print(f"📋 找到 {len(configs)} 条配置记录:")

        for i, config in enumerate(configs):
            config_dict = dict(zip(columns, config))
            print(f"\n配置记录 {i+1}:")
            print(f"   🆔 ID: {config_dict.get('id', 'N/A')}")
            print(
                f"   🔑 Access Key: {'已配置' if config_dict.get('access_key') else '❌ 为空'}"
            )
            print(
                f"   🗝️ Secret Key: {'已配置' if config_dict.get('secret_key') else '❌ 为空'}"
            )
            print(f"   🌐 Base URL: {config_dict.get('base_url', 'N/A')}")
            print(f"   ⚡ Enabled: {config_dict.get('enabled', False)}")
            print(f"   ⏰ Created: {config_dict.get('created_at', 'N/A')}")
            print(f"   🔄 Updated: {config_dict.get('updated_at', 'N/A')}")

        return (
            len(
                [
                    c
                    for c in configs
                    if dict(zip(columns, c)).get("access_key")
                    and dict(zip(columns, c)).get("secret_key")
                ]
            )
            > 0
        )

    except Exception as e:
        print(f"❌ 检查配置时发生错误: {e}")
        return False
    finally:
        conn.close()


def provide_configuration_guide():
    """提供配置指引"""
    print("\n" + "=" * 60)
    print("🛠️ ComfyUI配置修复指引")
    print("=" * 60)

    print("\n📋 问题原因：")
    print("   ComfyUI的access_key和secret_key未配置，导致签名验证失败")

    print("\n🔧 解决方案：")
    print("1. 启动Web应用")
    print("2. 使用管理员账号登录")
    print("3. 进入管理界面 → AI服务配置 → ComfyUI设置")
    print("4. 配置以下参数：")
    print("   • Access Key: 从哩布官网获取")
    print("   • Secret Key: 从哩布官网获取")
    print("   • Base URL: https://openapi.liblibai.cloud (默认)")
    print("   • 启用状态: 开启")

    print("\n🌐 获取哩布API密钥：")
    print("1. 访问哩布官网: https://www.liblibai.com/")
    print("2. 注册/登录账号")
    print("3. 进入API管理页面")
    print("4. 获取access_key和secret_key")

    print("\n⚠️  注意事项：")
    print("• 确保API密钥有效且未过期")
    print("• 检查账户是否有足够的API调用额度")
    print("• 确保网络能够访问哩布API服务器")


def create_test_config_script():
    """创建配置测试脚本"""
    test_script = """#!/usr/bin/env python3
'''
ComfyUI配置测试脚本 - 配置完成后运行此脚本验证
'''
import sys
sys.path.append('.')

try:
    from open_webui.models.comfyui import get_comfyui_config
    from open_webui.utils.comfyui_api import ComfyUISignatureAuth
    
    config = get_comfyui_config()
    if not config:
        print("❌ 无法获取配置")
        sys.exit(1)
    
    if not config.access_key or not config.secret_key:
        print("❌ API密钥未配置")
        sys.exit(1)
    
    print("✅ 配置检查通过")
    print(f"Access Key: {config.access_key[:8]}...")
    print(f"Secret Key: {config.secret_key[:8]}...")
    print(f"Enabled: {config.enabled}")
    
    # 测试签名生成
    auth = ComfyUISignatureAuth(config.access_key, config.secret_key)
    signature = auth.generate_signature("/api/generate/comfyui/app")
    print(f"✅ 签名生成成功: {signature['Signature'][:20]}...")
    
    print("\\n🎉 ComfyUI配置完整，可以正常使用！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    sys.exit(1)
"""

    with open("test_comfyui_after_config.py", "w", encoding="utf-8") as f:
        f.write(test_script)

    print(f"\n📝 已创建配置测试脚本: test_comfyui_after_config.py")
    print("   配置完成后运行: python test_comfyui_after_config.py")


if __name__ == "__main__":
    print("🚀 ComfyUI配置问题诊断...")
    print("=" * 60)

    has_valid_config = check_and_show_comfyui_config()

    if not has_valid_config:
        provide_configuration_guide()
        create_test_config_script()

        print("\n" + "=" * 60)
        print("🎯 总结：")
        print("❌ ComfyUI配置不完整，需要手动配置API密钥")
        print("🔧 请按照上述指引完成配置")
        print("✅ 配置完成后，签名验证失败问题将自动解决")
    else:
        print("\n✅ ComfyUI配置完整，签名验证失败可能由其他原因导致")
        print("💡 建议检查API密钥是否过期或网络连接问题")
