#!/usr/bin/env python3
"""
DreamWork API 400错误专项修复
针对"code: 0"错误的具体解决方案
"""

import httpx
import json
import base64
import asyncio
from typing import Dict, Any


class DreamWorkApiFixer:
    """专门用于修复DreamWork API调用的类"""

    def __init__(self, api_key: str, base_url: str = "https://api.linkapi.org"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def test_minimal_request(self):
        """测试最小化的API请求"""
        url = f"{self.base_url}/v1/images/generations"

        # 最简单的文生图请求
        minimal_data = {
            "model": "doubao-seedream-3-0-t2i-250415",
            "prompt": "a simple test image",
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        print(f"📝 测试最小化文生图请求:")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(minimal_data, indent=2)}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=minimal_data, headers=headers)
                print(f"状态码: {response.status_code}")
                print(f"响应: {response.text}")
                return response.status_code == 200
            except Exception as e:
                print(f"请求异常: {e}")
                return False

    async def test_image_to_image_formats(self):
        """测试不同的图生图请求格式"""
        url = f"{self.base_url}/v1/images/generations"

        # 创建一个最小的PNG图片base64
        tiny_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

        # 测试不同的参数组合
        test_cases = [
            {
                "name": "最小图生图请求",
                "data": {
                    "model": "doubao-seededit-3-0-i2i-250628",
                    "prompt": "enhance this image",
                    "image": tiny_png,
                },
            },
            {
                "name": "带size参数",
                "data": {
                    "model": "doubao-seededit-3-0-i2i-250628",
                    "prompt": "enhance this image",
                    "image": tiny_png,
                    "size": "1024x1024",
                },
            },
            {
                "name": "带response_format参数",
                "data": {
                    "model": "doubao-seededit-3-0-i2i-250628",
                    "prompt": "enhance this image",
                    "image": tiny_png,
                    "response_format": "url",
                },
            },
            {
                "name": "完整参数",
                "data": {
                    "model": "doubao-seededit-3-0-i2i-250628",
                    "prompt": "enhance this image",
                    "image": tiny_png,
                    "size": "1024x1024",
                    "response_format": "url",
                    "guidance_scale": 2.5,
                    "watermark": True,
                },
            },
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        results = {}

        for test_case in test_cases:
            print(f"\n📝 测试: {test_case['name']}")
            print(f"参数: {list(test_case['data'].keys())}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(
                        url, json=test_case["data"], headers=headers
                    )
                    response_data = response.text

                    print(f"状态码: {response.status_code}")
                    if response.status_code != 200:
                        print(f"错误响应: {response_data}")

                        # 解析错误信息
                        try:
                            error_json = response.json()
                            if "code" in error_json:
                                print(f"错误代码: {error_json.get('code')}")
                            if "msg" in error_json:
                                print(f"错误消息: {error_json.get('msg')}")
                            if "message" in error_json:
                                print(f"错误描述: {error_json.get('message')}")
                        except:
                            print("无法解析错误响应为JSON")
                    else:
                        print("✅ 请求成功!")

                    results[test_case["name"]] = response.status_code == 200

                except Exception as e:
                    print(f"请求异常: {e}")
                    results[test_case["name"]] = False

        return results

    def generate_fixed_api_client_code(self):
        """生成修复后的API客户端代码"""
        code = '''
async def generate_image_to_image_fixed(self, request: DreamWorkGenerateRequest) -> dict:
    """修复版图生图API调用"""
    url = f"{self.base_url}/v1/images/generations"
    
    # 验证和清理图片数据
    if not request.image:
        raise ValueError("图生图模式需要输入图片")
        
    image_data = request.image.strip()
    
    # 处理data URL格式
    if image_data.startswith('data:'):
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        else:
            raise ValueError("无效的data URL格式")
    
    # 清理空白字符
    image_data = ''.join(image_data.split())
    
    # 验证base64
    try:
        decoded = base64.b64decode(image_data)
        if len(decoded) < 100:
            raise ValueError(f"图片数据太小: {len(decoded)} bytes")
    except Exception as e:
        raise ValueError(f"无效的base64数据: {e}")
    
    # 使用最简单的请求格式
    request_data = {
        "model": "doubao-seededit-3-0-i2i-250628",
        "prompt": request.prompt.strip(),
        "image": image_data
    }
    
    # 只添加必要参数
    if request.size and request.size != "1024x1024":
        request_data["size"] = request.size
    
    headers = {
        'Authorization': f'Bearer {self.api_key}',
        'Content-Type': 'application/json'
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=request_data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_text = response.text
            try:
                error_json = response.json()
                if 'code' in error_json and error_json['code'] == 0:
                    error_msg = error_json.get('msg', '未知错误')
                    raise ValueError(f"DreamWork API返回错误: {error_msg}")
                elif 'error' in error_json:
                    raise ValueError(f"DreamWork API错误: {error_json['error']}")
                else:
                    raise ValueError(f"DreamWork API错误: {error_text}")
            except json.JSONDecodeError:
                raise ValueError(f"DreamWork API返回非JSON响应: {error_text}")
'''
        return code


async def main():
    """主测试函数"""
    print("🔧 DreamWork API 400错误专项修复测试")
    print("=" * 50)

    # 这里需要真实的API key来测试
    # api_key = "your_actual_api_key_here"
    # fixer = DreamWorkApiFixer(api_key)

    # 因为没有真实API key，我们展示修复后的代码
    fixer = DreamWorkApiFixer("test_key")

    print("\n📋 修复后的API客户端代码:")
    print(fixer.generate_fixed_api_client_code())

    print("\n🎯 关键修复点:")
    fixes = [
        "1. 使用最简化的请求参数（只包含必需字段）",
        "2. 改进图片数据清理（移除所有空白字符）",
        "3. 增强base64验证（检查解码后数据大小）",
        "4. 优化错误处理（专门处理code: 0的情况）",
        "5. 简化请求头（只保留必需的Authorization和Content-Type）",
    ]

    for fix in fixes:
        print(f"   {fix}")

    print("\n💡 建议:")
    suggestions = [
        "• 确保API key有效且有足够权限",
        "• 测试图片数据确保是有效的base64编码",
        "• 使用最小参数集避免参数冲突",
        "• 检查网络连接和DNS解析",
        "• 验证模型名称是否正确",
    ]

    for suggestion in suggestions:
        print(f"   {suggestion}")


if __name__ == "__main__":
    asyncio.run(main())
