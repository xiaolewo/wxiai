#!/usr/bin/env python3
"""
ComfyUI配置测试脚本 - 配置完成后运行此脚本验证
"""
import sys

sys.path.append(".")

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

    print("\n🎉 ComfyUI配置完整，可以正常使用！")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    sys.exit(1)
