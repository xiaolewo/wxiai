#!/usr/bin/env python3
"""
DreamWork API 最终测试和诊断
深度分析剩余的400错误问题
"""

import asyncio
import httpx
import json
import base64
from typing import Dict, Any


class DreamWorkFinalTester:
    """最终的DreamWork API测试器"""

    def __init__(self):
        # 模拟真实的API配置（需要从数据库读取）
        self.base_url = "https://api.linkapi.org"
        self.api_key = "YOUR_API_KEY"  # 需要真实的API Key

    async def test_api_connectivity(self):
        """测试基础API连接"""
        print("🔍 测试1: API连接性")
        url = f"{self.base_url}/v1/images/generations"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # 发送空POST请求测试端点可达性
                response = await client.post(url, json={})
                print(f"   状态码: {response.status_code}")
                print(f"   响应头: {dict(response.headers)}")

                if response.status_code in [400, 401, 422]:
                    print("   ✅ API端点可达")
                    return True
                else:
                    print(f"   ❌ 意外状态码: {response.status_code}")
                    return False
            except Exception as e:
                print(f"   ❌ 连接失败: {e}")
                return False

    async def test_auth_headers(self):
        """测试认证头格式"""
        print("\n🔍 测试2: 认证头格式")
        url = f"{self.base_url}/v1/images/generations"

        # 测试不同的认证头格式
        auth_formats = [
            {"Authorization": f"Bearer {self.api_key}"},
            {"Authorization": f"Bearer{self.api_key}"},  # 无空格
            {"Authorization": self.api_key},  # 不带Bearer
            {"X-API-Key": self.api_key},  # 不同的头名称
        ]

        for i, headers in enumerate(auth_formats):
            print(
                f"   格式{i+1}: {list(headers.keys())[0]} = {list(headers.values())[0][:20]}..."
            )

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        url,
                        json={"model": "test"},
                        headers={**headers, "Content-Type": "application/json"},
                    )

                    if response.status_code == 401:
                        print(f"   ❌ 认证失败")
                    elif response.status_code == 422:
                        print(f"   ✅ 认证通过（参数错误）")
                    else:
                        print(f"   状态码: {response.status_code}")
            except Exception as e:
                print(f"   ❌ 请求异常: {e}")

    async def test_minimal_requests(self):
        """测试最小化请求"""
        print("\n🔍 测试3: 最小化请求")
        url = f"{self.base_url}/v1/images/generations"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 创建最小的测试图片（1x1像素PNG）
        tiny_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

        test_cases = [
            {"name": "空请求", "data": {}},
            {"name": "只有model", "data": {"model": "doubao-seedream-3-0-t2i-250415"}},
            {
                "name": "文生图最小请求",
                "data": {"model": "doubao-seedream-3-0-t2i-250415", "prompt": "test"},
            },
            {
                "name": "图生图最小请求",
                "data": {
                    "model": "doubao-seededit-3-0-i2i-250628",
                    "prompt": "test",
                    "image": tiny_png_b64,
                },
            },
        ]

        for test_case in test_cases:
            print(f"   {test_case['name']}: ", end="")

            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(
                        url, json=test_case["data"], headers=headers
                    )

                    if response.status_code == 200:
                        print("✅ 成功")
                    elif response.status_code == 400:
                        try:
                            error_info = response.json()
                            if "code" in error_info and error_info["code"] == 0:
                                msg = error_info.get("msg", "未知错误")
                                print(f"❌ code:0 - {msg}")
                            else:
                                print(f"❌ 400错误 - {response.text[:100]}")
                        except:
                            print(f"❌ 400错误 - {response.text[:50]}")
                    else:
                        print(f"状态码: {response.status_code}")

            except Exception as e:
                print(f"❌ 异常: {e}")

    async def analyze_error_patterns(self):
        """分析错误模式"""
        print("\n🔍 测试4: 错误模式分析")

        # 从前面的修复文件中提取已知的错误响应
        known_errors = [
            '{"code": 0, "msg": "提交任务失败"}',
            '{"error": {"message": "Invalid request format"}}',
            '{"detail": "Validation error"}',
        ]

        for error in known_errors:
            print(f"   已知错误: {error}")
            try:
                error_json = json.loads(error)
                if "code" in error_json and error_json["code"] == 0:
                    print(f"     🎯 这是主要问题: code:0 表示API完全拒绝请求")
                    print(f"     💡 可能原因: 参数格式、认证、或服务不可用")
            except:
                pass

    def generate_ultimate_fix(self):
        """生成终极修复方案"""
        print("\n🛠️ 终极修复方案:")

        fixes = [
            "1. 验证API Key是否有效且有权限",
            "2. 确认API端点URL是否正确 (https://api.linkapi.org/v1/images/generations)",
            '3. 测试最简请求: {"model": "doubao-seedream-3-0-t2i-250415", "prompt": "test"}',
            "4. 检查base64图片数据是否完整无损",
            "5. 验证模型名称是否完全正确",
            "6. 检查请求大小限制（图片可能太大）",
            "7. 测试不同的Content-Type头",
            "8. 尝试添加User-Agent头",
            "9. 检查网络代理或防火墙设置",
            "10. 联系DreamWork技术支持确认API状态",
        ]

        for fix in fixes:
            print(f"   {fix}")

    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 DreamWork API 综合诊断测试")
        print("=" * 50)

        # 依次运行所有测试
        await self.test_api_connectivity()
        await self.test_auth_headers()
        await self.test_minimal_requests()
        await self.analyze_error_patterns()
        self.generate_ultimate_fix()

        print("\n📋 诊断完成！请检查上述结果以确定具体问题。")


async def main():
    """主函数"""
    tester = DreamWorkFinalTester()

    # 首先尝试从配置文件读取真实的API配置
    try:
        import sys

        sys.path.append("/Users/liuqingliang/Desktop/openwebui/open-webui/backend")
        from open_webui.models.dreamwork import DreamWorkConfig

        config = DreamWorkConfig.get_config()
        if config and config.api_key:
            tester.api_key = config.api_key
            tester.base_url = config.base_url.rstrip("/")
            print(f"✅ 已加载真实配置: {tester.base_url}")
        else:
            print("⚠️ 未找到配置，使用测试配置")
    except Exception as e:
        print(f"⚠️ 无法加载配置: {e}")

    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())
