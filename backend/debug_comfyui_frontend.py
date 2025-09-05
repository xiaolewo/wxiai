#!/usr/bin/env python3
"""
ComfyUI前端配置保存问题调试工具
模拟前端请求，调试认证和数据保存流程
"""

import requests
import json
import os
import sys


def get_admin_token():
    """获取管理员token（模拟登录过程）"""
    print("🔑 获取管理员认证token...")

    # 这里需要你提供管理员的用户名和密码
    admin_email = input("请输入管理员邮箱: ").strip()
    admin_password = input("请输入管理员密码: ").strip()

    if not admin_email or not admin_password:
        print("❌ 邮箱和密码不能为空")
        return None

    try:
        # 尝试登录获取token
        login_url = "http://localhost:8080/api/v1/auths/signin"
        login_data = {"email": admin_email, "password": admin_password}

        response = requests.post(login_url, json=login_data, timeout=10)

        print(f"📊 登录响应状态: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            token = result.get("token")
            if token:
                print(f"✅ 登录成功，获得token: {token[:20]}...")
                return token
            else:
                print("❌ 登录响应中没有token")
                print(f"响应内容: {result}")
                return None
        else:
            print(f"❌ 登录失败: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None


def test_get_config(token):
    """测试获取配置API"""
    print("\n🔍 测试获取配置API...")

    try:
        url = "http://localhost:8080/api/v1/comfyui/admin/config"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        response = requests.get(url, headers=headers, timeout=10)

        print(f"📊 GET响应状态: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")

        if response.status_code == 200:
            config = response.json()
            print(f"✅ 获取配置成功:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            return config
        else:
            print(f"❌ 获取配置失败: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 获取配置请求异常: {e}")
        return None


def test_save_config(token):
    """测试保存配置API"""
    print("\n💾 测试保存配置API...")

    # 模拟前端发送的配置数据
    config_data = {
        "access_key": input("请输入Access Key: ").strip(),
        "secret_key": input("请输入Secret Key: ").strip(),
        "base_url": "https://openapi.liblibai.cloud",
        "enabled": True,
        "timeout": 300,
        "max_concurrent_tasks": 5,
    }

    if not config_data["access_key"] or not config_data["secret_key"]:
        print("❌ Access Key和Secret Key不能为空")
        return False

    try:
        url = "http://localhost:8080/api/v1/comfyui/admin/config"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        print(f"🔗 请求URL: {url}")
        print(f"📋 请求头: {headers}")
        print(f"📦 请求数据: {json.dumps(config_data, indent=2)}")

        response = requests.post(url, headers=headers, json=config_data, timeout=10)

        print(f"\n📊 POST响应状态: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 保存配置成功:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ 保存配置失败:")
            print(f"响应文本: {response.text}")
            try:
                error = response.json()
                print(f"错误详情: {json.dumps(error, indent=2, ensure_ascii=False)}")
            except:
                pass
            return False

    except Exception as e:
        print(f"❌ 保存配置请求异常: {e}")
        return False


def verify_database_save():
    """验证数据库中的保存结果"""
    print("\n🔍 验证数据库保存结果...")

    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from open_webui.models.comfyui import ComfyUIConfigs

        config = ComfyUIConfigs.get_config()
        if config:
            print(f"✅ 数据库中的配置:")
            print(f"   Access Key: {'已设置' if config.access_key else '❌ 为空'}")
            print(f"   Secret Key: {'已设置' if config.secret_key else '❌ 为空'}")
            print(f"   Base URL: {config.base_url}")
            print(f"   Enabled: {config.enabled}")
            print(f"   Timeout: {config.timeout}")
            print(f"   Max Tasks: {config.max_concurrent_tasks}")

            if config.access_key and config.secret_key:
                print("✅ 配置保存到数据库成功！")
                return True
            else:
                print("❌ 配置保存不完整")
                return False
        else:
            print("❌ 数据库中没有配置")
            return False

    except Exception as e:
        print(f"❌ 验证数据库失败: {e}")
        return False


def main():
    print("🚀 ComfyUI前端配置保存调试工具")
    print("=" * 60)
    print("此工具将模拟前端请求流程，帮助诊断配置保存问题")
    print()

    # 步骤1：获取管理员token
    token = get_admin_token()
    if not token:
        print("❌ 无法获得管理员认证，退出")
        return

    # 步骤2：测试获取配置
    current_config = test_get_config(token)

    # 步骤3：测试保存配置
    save_success = test_save_config(token)

    # 步骤4：验证数据库保存结果
    if save_success:
        db_save_success = verify_database_save()

        if db_save_success:
            print("\n🎉 完整流程测试成功！")
            print("✅ 前端API调用正常")
            print("✅ 后端处理正常")
            print("✅ 数据库保存正常")
            print("\n💡 如果Web界面仍然不能保存，可能是:")
            print("1. 浏览器缓存问题")
            print("2. 前端JavaScript错误")
            print("3. 网络连接问题")
        else:
            print("\n❌ API调用成功但数据库保存失败")
            print("可能是后端数据处理或数据库写入问题")
    else:
        print("\n❌ API调用失败")
        print("请检查认证、权限或网络问题")


if __name__ == "__main__":
    main()
