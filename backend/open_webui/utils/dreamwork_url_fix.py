"""
DreamWork API URL格式修复
解决图生图API期望URL而不是base64的问题
"""

import httpx
import json
import base64
import tempfile
import os
from typing import Dict, Any


async def generate_image_to_image_url_fix(config, request) -> dict:
    """
    修复版图生图函数 - 使用URL格式
    解决API期望image URL而不是base64数据的问题
    """
    url = f"{config.base_url}/v1/images/generations"

    # 验证输入数据
    if not request.image:
        raise ValueError("图生图模式需要输入图片")

    # 验证和清理图片数据
    image_data = request.image.strip()
    print(f"🎨 【DreamWork URL修复】原始图片数据长度: {len(image_data)}字符")

    # 处理data URL格式
    if image_data.startswith("data:"):
        if "," in image_data:
            header, image_data = image_data.split(",", 1)
            print(f"🎨 【DreamWork URL修复】移除data URL前缀: {header}")
        else:
            raise ValueError("无效的data URL格式")

    # 清理空白字符
    image_data = "".join(image_data.split())

    # 验证base64
    try:
        decoded_data = base64.b64decode(image_data)
        if len(decoded_data) < 100:
            raise ValueError(f"图片数据太小: {len(decoded_data)} bytes")
        print(
            f"🎨 【DreamWork URL修复】base64验证通过，解码后大小: {len(decoded_data)} bytes"
        )
    except Exception as e:
        raise ValueError(f"无效的base64数据: {e}")

    # 方案1: 使用data URL格式（尝试正确的data URL格式）
    # 检测图片格式
    image_format = "png"  # 默认
    if decoded_data[:4] == b"\x89PNG":
        image_format = "png"
    elif decoded_data[:2] == b"\xff\xd8":
        image_format = "jpeg"
    elif decoded_data[:6] in [b"GIF87a", b"GIF89a"]:
        image_format = "gif"
    elif decoded_data[:4] == b"RIFF" and decoded_data[8:12] == b"WEBP":
        image_format = "webp"

    # 构建正确的data URL
    data_url = f"data:image/{image_format};base64,{image_data}"
    print(
        f"🎨 【DreamWork URL修复】构建data URL: data:image/{image_format};base64,[{len(image_data)}字符]"
    )

    # 使用最简单的请求格式
    request_data = {
        "model": "doubao-seededit-3-0-i2i-250628",
        "prompt": request.prompt.strip(),
        "image": data_url,  # 使用完整的data URL
    }

    print(f"🎨 【DreamWork URL修复】请求参数:")
    for key, value in request_data.items():
        if key == "image":
            print(
                f"  - {key}: data:image/{image_format};base64,[{len(image_data)} chars]"
            )
        else:
            print(f"  - {key}: {value}")

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"🎨 【DreamWork URL修复】发送请求到: {url}")
            response = await client.post(url, json=request_data, headers=headers)
            print(f"🎨 【DreamWork URL修复】响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"🎨 【DreamWork URL修复】请求成功!")
                return result
            else:
                error_text = response.text
                print(f"🎨 【DreamWork URL修复】错误响应: {error_text}")

                # 如果data URL还是不行，尝试方案2
                if (
                    "unsupported protocol scheme" in error_text
                    or "invalid image url" in error_text
                ):
                    print(
                        f"🎨 【DreamWork URL修复】data URL失败，尝试临时文件上传方案..."
                    )
                    return await _try_temp_file_upload(
                        config, request, decoded_data, image_format
                    )

                # 处理其他错误
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_info = error_json["error"]
                        if isinstance(error_info, dict):
                            error_msg = error_info.get("message", str(error_info))
                        else:
                            error_msg = str(error_info)
                        raise ValueError(f"DreamWork API错误: {error_msg}")
                    else:
                        raise ValueError(f"DreamWork API错误: {error_text}")
                except json.JSONDecodeError:
                    raise ValueError(f"DreamWork API返回非JSON响应: {error_text}")

    except httpx.TimeoutException:
        raise ValueError("DreamWork API请求超时")
    except httpx.ConnectError as e:
        raise ValueError(f"无法连接到DreamWork API: {e}")
    except Exception as e:
        if "DreamWork API" in str(e):
            raise
        print(f"🎨 【DreamWork URL修复】请求异常: {e}")
        raise ValueError(f"DreamWork API请求失败: {e}")


async def _try_temp_file_upload(config, request, decoded_data, image_format):
    """
    尝试通过临时文件和可访问的URL来处理图片
    这是备用方案，如果data URL不被支持
    """
    print(f"🎨 【DreamWork URL修复】尝试备用方案...")

    # 注意：这个方案需要一个可以公开访问的临时文件服务
    # 由于没有这样的服务，我们直接返回错误说明
    raise ValueError(
        """
DreamWork API要求图片必须是可访问的URL，不支持base64数据。
解决方案：
1. 设置图片临时存储服务（如AWS S3, 阿里云OSS等）
2. 将base64图片上传到临时存储
3. 使用临时URL调用DreamWork API
4. 或者联系DreamWork技术支持确认正确的图片格式
"""
    )


# 测试函数
async def test_url_fix():
    """测试URL修复方案"""
    import sys

    sys.path.append("/Users/liuqingliang/Desktop/openwebui/open-webui/backend")
    from open_webui.models.dreamwork import DreamWorkConfig

    config = DreamWorkConfig.get_config()
    if not config:
        print("❌ 无法获取DreamWork配置")
        return

    # 创建模拟请求
    class MockRequest:
        def __init__(self):
            self.image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            self.prompt = "enhance this image"

    request = MockRequest()

    try:
        result = await generate_image_to_image_url_fix(config, request)
        print("✅ 修复成功!")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ 修复测试失败: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_url_fix())
