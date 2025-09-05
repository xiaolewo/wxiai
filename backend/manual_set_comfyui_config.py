#!/usr/bin/env python3
"""
手动设置ComfyUI配置 - 绕过Web界面直接设置
"""

import os
import sys


def manual_set_config():
    """手动设置ComfyUI配置"""
    print("🔧 手动设置ComfyUI配置...")

    # 请在这里填入你的真实API密钥
    ACCESS_KEY = input("请输入哩布API Access Key: ").strip()
    SECRET_KEY = input("请输入哩布API Secret Key: ").strip()

    if not ACCESS_KEY or not SECRET_KEY:
        print("❌ Access Key和Secret Key不能为空")
        return False

    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        from open_webui.models.comfyui import ComfyUIConfigs, ComfyUIConfigForm

        # 创建配置表单
        config_form = ComfyUIConfigForm(
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            base_url="https://openapi.liblibai.cloud",
            enabled=True,
            timeout=300,
            max_concurrent_tasks=5,
        )

        print("📝 保存配置到数据库...")
        saved_config = ComfyUIConfigs.create_or_update_config(config_form)

        if saved_config:
            print("✅ 配置保存成功!")
            print(f"   Access Key: {saved_config.access_key[:8]}...")
            print(f"   Secret Key: {saved_config.secret_key[:8]}...")
            print(f"   Base URL: {saved_config.base_url}")
            print(f"   Enabled: {saved_config.enabled}")

            # 测试签名生成
            print("\n🔍 测试签名生成...")
            from open_webui.utils.comfyui_api import ComfyUISignatureAuth

            auth = ComfyUISignatureAuth(
                saved_config.access_key, saved_config.secret_key
            )
            signature_params = auth.generate_signature("/api/generate/comfyui/app")

            print(f"✅ 签名生成成功: {signature_params['Signature'][:20]}...")
            print("\n🎉 ComfyUI配置设置完成，现在可以正常使用了!")
            return True
        else:
            print("❌ 配置保存失败")
            return False

    except Exception as e:
        print(f"❌ 设置配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 ComfyUI配置手动设置工具")
    print("=" * 60)
    print("⚠️  注意：此工具会直接写入数据库，绕过Web界面")
    print("🔑 请确保你有正确的哩布API密钥")
    print()

    if manual_set_config():
        print("\n✅ 配置设置完成!")
        print("💡 现在可以尝试使用ComfyUI功能了")
        print("🔧 如果仍有问题，请检查API密钥是否正确")
    else:
        print("\n❌ 配置设置失败")
        print("🛠️  请检查输入的API密钥是否正确")
