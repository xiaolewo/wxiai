#!/usr/bin/env python3
"""
测试ComfyUI API端点访问
"""

import requests
import json


def test_comfyui_endpoints():
    """测试ComfyUI API端点"""
    print("🔗 测试ComfyUI API端点...")

    base_url = "http://localhost:8080/api/v1/comfyui"

    endpoints = [
        ("/admin/config", "GET", "获取配置"),
        ("/admin/config", "POST", "保存配置"),
        ("/workflows", "GET", "获取工作流"),
        ("/health", "GET", "健康检查"),
    ]

    for endpoint, method, description in endpoints:
        url = base_url + endpoint
        print(f"\n🔍 测试 {method} {url} - {description}")

        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                # 测试POST配置保存
                test_config = {
                    "access_key": "test_key_from_api",
                    "secret_key": "test_secret_from_api",
                    "base_url": "https://openapi.liblibai.cloud",
                    "enabled": True,
                    "timeout": 300,
                    "max_concurrent_tasks": 5,
                }
                response = requests.post(url, json=test_config, timeout=5)

            print(f"   📊 状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ 响应成功: {type(data)}")
                    if isinstance(data, dict):
                        print(f"   📋 响应键: {list(data.keys())}")
                except:
                    print(f"   📄 响应文本: {response.text[:100]}...")
            elif response.status_code == 401:
                print("   🔐 需要认证 (正常，需要管理员权限)")
            elif response.status_code == 422:
                print("   ⚠️  请求参数错误")
                try:
                    error = response.json()
                    print(f"   📋 错误详情: {error}")
                except:
                    pass
            else:
                print(f"   ❌ 请求失败: {response.text[:200]}")

        except requests.exceptions.ConnectionError:
            print("   ❌ 连接失败 - 服务器可能未运行")
        except requests.exceptions.Timeout:
            print("   ⏰ 请求超时")
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")


def test_direct_config_api():
    """直接测试配置API"""
    print("\n🎯 直接测试配置API...")

    url = "http://localhost:8080/api/v1/comfyui/admin/config"

    # 测试数据
    config_data = {
        "access_key": "real_access_key_test",
        "secret_key": "real_secret_key_test",
        "base_url": "https://openapi.liblibai.cloud",
        "enabled": True,
        "timeout": 300,
        "max_concurrent_tasks": 5,
    }

    print(f"📝 尝试POST配置到: {url}")
    print(f"📋 配置数据: {json.dumps(config_data, indent=2)}")

    try:
        response = requests.post(
            url,
            json=config_data,
            headers={
                "Content-Type": "application/json",
                # 注意：这里没有认证头，所以预期会返回401
            },
            timeout=10,
        )

        print(f"📊 响应状态: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")

        if response.text:
            print(f"📋 响应内容: {response.text}")

            try:
                response_data = response.json()
                print(f"📊 JSON响应: {json.dumps(response_data, indent=2)}")
            except:
                print("📄 响应不是JSON格式")

        if response.status_code == 401:
            print("✅ API端点存在且需要认证（正常）")
            return True
        elif response.status_code == 422:
            print("✅ API端点存在，参数验证正常")
            return True
        elif response.status_code == 200:
            print("⚠️  API端点存在但没有验证认证（可能有问题）")
            return True
        else:
            print(f"❌ API端点响应异常: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 测试配置API失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 开始测试ComfyUI API端点...")
    print("=" * 60)

    test_comfyui_endpoints()
    test_direct_config_api()

    print("\n" + "=" * 60)
    print("💡 如果API端点正常但Web界面无法保存配置，问题可能在于:")
    print("1. 前端表单提交逻辑")
    print("2. 认证/权限问题")
    print("3. CORS或网络配置问题")
    print("4. 前后端数据格式不匹配")
