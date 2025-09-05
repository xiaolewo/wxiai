#!/usr/bin/env python3
"""
测试Veo API路由是否正常工作
"""

import requests
import json
import sys
import os


def test_veo_health():
    """测试Veo健康检查"""
    try:
        url = "http://localhost:8080/api/v1/veo/health"
        print(f"🔍 测试URL: {url}")

        response = requests.get(url, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        print(f"📊 响应头: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Veo健康检查成功:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        else:
            print(f"❌ Veo健康检查失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器 - 请确保服务正在运行在 http://localhost:8080")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def test_veo_config_user():
    """测试用户配置获取 (不需要认证)"""
    try:
        url = "http://localhost:8080/api/v1/veo/config/user"
        print(f"\n🔍 测试用户配置URL: {url}")

        response = requests.get(url, timeout=10)
        print(f"📊 状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Veo用户配置获取成功:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        elif response.status_code == 401:
            print("🔒 需要用户认证 - 这是正常的")
            return True
        else:
            print(f"❌ Veo用户配置获取失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 开始测试Veo API路由...")
    print("=" * 60)

    success = True

    # 测试健康检查
    if not test_veo_health():
        success = False

    # 测试用户配置
    if not test_veo_config_user():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！Veo API路由工作正常")
    else:
        print("❌ 部分测试失败，请检查服务配置")
        sys.exit(1)
