#!/usr/bin/env python3
"""
检查ComfyUI配置和签名验证
"""

import os
import sys


def get_db_connection():
    """获取数据库连接"""
    import sqlite3

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


def check_comfyui_config():
    """检查ComfyUI配置"""
    print("🔍 检查ComfyUI配置...")

    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    cursor = conn.cursor()

    try:
        # 检查comfyui_config表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='comfyui_config'"
        )
        if not cursor.fetchone():
            print("❌ comfyui_config表不存在")
            return False

        # 检查配置记录
        cursor.execute("SELECT * FROM comfyui_config LIMIT 1")
        config = cursor.fetchone()

        if not config:
            print("❌ ComfyUI配置为空，请先在管理界面配置哩布API密钥")
            print("   💡 提示：需要配置access_key和secret_key")
            return False

        # 获取列名
        cursor.execute("PRAGMA table_info(comfyui_config)")
        columns = [row[1] for row in cursor.fetchall()]
        config_dict = dict(zip(columns, config))

        print(f"✅ 找到ComfyUI配置记录:")
        print(
            f"   🔑 Access Key: {'已配置' if config_dict.get('access_key') else '❌ 未配置'}"
        )
        print(
            f"   🗝️ Secret Key: {'已配置' if config_dict.get('secret_key') else '❌ 未配置'}"
        )
        print(f"   🌐 Base URL: {config_dict.get('base_url', 'N/A')}")
        print(f"   ⚡ Enabled: {config_dict.get('enabled', False)}")

        # 检查关键配置
        if not config_dict.get("access_key") or not config_dict.get("secret_key"):
            print("❌ 关键配置缺失：access_key或secret_key为空")
            return False

        if not config_dict.get("enabled"):
            print("⚠️ ComfyUI功能未启用")
            return False

        print("✅ ComfyUI配置完整")
        return True

    except Exception as e:
        print(f"❌ 检查配置时发生错误: {e}")
        return False
    finally:
        conn.close()


def test_signature_generation():
    """测试签名生成"""
    print("\n🔍 测试签名生成功能...")

    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        from open_webui.models.comfyui import get_comfyui_config
        from open_webui.utils.comfyui_api import ComfyUISignatureAuth

        config = get_comfyui_config()
        if not config:
            print("❌ 无法获取ComfyUI配置")
            return False

        print(f"✅ 配置加载成功")
        print(f"   🔑 Access Key: {config.access_key[:8]}...")
        print(f"   🗝️ Secret Key: {config.secret_key[:8]}...")
        print(f"   🌐 Base URL: {config.base_url}")
        print(f"   ⚡ Enabled: {config.enabled}")

        # 测试签名生成
        auth = ComfyUISignatureAuth(config.access_key, config.secret_key)
        test_uri = "/api/generate/comfyui/app"
        signature_params = auth.generate_signature(test_uri)

        print(f"✅ 签名生成成功:")
        print(f"   📝 Signature: {signature_params['Signature'][:20]}...")
        print(f"   ⏰ Timestamp: {signature_params['Timestamp']}")
        print(f"   🎲 Nonce: {signature_params['SignatureNonce'][:20]}...")

        # 生成完整URL
        signed_url = auth.get_signed_url(config.base_url, test_uri)
        print(f"✅ 签名URL生成成功: {signed_url[:100]}...")

        return True

    except Exception as e:
        print(f"❌ 签名测试失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_api_connectivity():
    """测试API连通性"""
    print("\n🔍 测试哩布API连通性...")

    try:
        import requests
        from open_webui.models.comfyui import get_comfyui_config
        from open_webui.utils.comfyui_api import ComfyUISignatureAuth

        config = get_comfyui_config()
        if not config:
            print("❌ 无法获取ComfyUI配置")
            return False

        # 测试基本连通性 - 使用一个简单的状态查询
        auth = ComfyUISignatureAuth(config.access_key, config.secret_key)
        test_uri = "/api/generate/comfy/status"
        signed_url = auth.get_signed_url(config.base_url, test_uri)

        # 使用假的generateUuid进行测试（预期会返回错误，但不是签名错误）
        test_payload = {"generateUuid": "test-uuid-for-connectivity"}

        print(f"🔗 测试URL: {signed_url[:50]}...")

        response = requests.post(
            signed_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        print(f"📊 API响应状态: {response.status_code}")

        try:
            result = response.json()
            print(f"📋 响应内容: {result}")

            # 检查是否是签名错误
            if result.get("code") == 401 and "签名验证失败" in result.get("msg", ""):
                print("❌ 签名验证失败！请检查access_key和secret_key是否正确")
                return False
            else:
                print("✅ 签名验证通过（API响应正常，非签名错误）")
                return True

        except ValueError:
            print(f"⚠️ 响应不是JSON格式: {response.text[:200]}")
            # 非JSON响应通常意味着签名通过了
            if response.status_code != 401:
                print("✅ 签名验证通过（服务器响应非JSON，但状态非401）")
                return True

        return True

    except requests.exceptions.ConnectionError:
        print("❌ 网络连接失败，请检查网络设置")
        return False
    except Exception as e:
        print(f"❌ API测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 开始ComfyUI配置诊断...")
    print("=" * 60)

    success = True

    # 1. 检查数据库配置
    if not check_comfyui_config():
        success = False

    # 2. 测试签名生成
    if success and not test_signature_generation():
        success = False

    # 3. 测试API连通性
    if success and not test_api_connectivity():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 ComfyUI配置诊断完成！")
        print("✅ 配置正常，签名验证应该可以工作")
        print("\n💡 如果仍然遇到签名验证失败，请检查：")
        print("1. 哩布API密钥是否已更新或过期")
        print("2. 服务器时间是否准确")
        print("3. 网络连接是否稳定")
    else:
        print("❌ ComfyUI配置存在问题！")
        print("\n🛠️ 请按以下步骤修复：")
        print("1. 登录管理界面，重新配置ComfyUI设置")
        print("2. 确认access_key和secret_key正确")
        print("3. 启用ComfyUI功能")
        print("4. 测试API连接")

        sys.exit(1)
