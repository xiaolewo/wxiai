"""
DreamWork 修复版 API 客户端
专门用于替换原有的图生图函数
"""

import httpx
import json
import base64
from typing import Dict, Any


async def generate_image_to_image_fixed(config, request) -> dict:
    """
    修复版图生图函数
    解决 API 需要完整 data URL 格式的问题
    """
    url = f"{config.base_url}/v1/images/generations"

    # 验证输入数据
    if not request.image:
        raise ValueError("图生图模式需要输入图片")

    # 验证和清理图片数据
    image_data = request.image.strip()
    print(f"🎨 【DreamWork修复版】原始图片数据长度: {len(image_data)}字符")

    # 确保是完整的data URL格式
    if image_data.startswith("data:"):
        print(f"🎨 【DreamWork修复版】检测到data URL格式")
        # 保持完整的data URL格式
        data_url = image_data
    else:
        # 如果只是base64数据，需要添加data URL前缀
        print(f"🎨 【DreamWork修复版】检测到纯base64，添加data URL前缀")

        # 清理空白字符
        clean_image_data = "".join(image_data.split())

        # 验证base64并检测图片格式
        try:
            decoded = base64.b64decode(clean_image_data)
            if len(decoded) < 100:
                raise ValueError(f"图片数据太小: {len(decoded)} bytes")
            print(
                f"🎨 【DreamWork修复版】base64验证通过，解码后大小: {len(decoded)} bytes"
            )

            # 检测图片格式
            image_format = "png"  # 默认
            if decoded[:4] == b"\x89PNG":
                image_format = "png"
            elif decoded[:2] == b"\xff\xd8":
                image_format = "jpeg"
            elif decoded[:6] in [b"GIF87a", b"GIF89a"]:
                image_format = "gif"
            elif decoded[:4] == b"RIFF" and decoded[8:12] == b"WEBP":
                image_format = "webp"

            # 构建完整的data URL
            data_url = f"data:image/{image_format};base64,{clean_image_data}"
            print(
                f"🎨 【DreamWork修复版】构建data URL: data:image/{image_format};base64,[{len(clean_image_data)}字符]"
            )

        except Exception as e:
            raise ValueError(f"无效的base64数据: {e}")

    # 使用正确的请求格式
    request_data = {
        "model": "doubao-seededit-3-0-i2i-250628",  # 硬编码图生图模型
        "prompt": request.prompt.strip(),
        "image": data_url,  # 使用完整的data URL
    }

    # 只在非默认值时添加size参数
    if hasattr(request, "size") and request.size and request.size != "1024x1024":
        request_data["size"] = request.size

    print(f"🎨 【DreamWork修复版】最简化请求参数:")
    for key, value in request_data.items():
        if key == "image":
            print(f"  - {key}: [base64 data, {len(value)} chars]")
        else:
            print(f"  - {key}: {value}")

    # 最简单的headers
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"🎨 【DreamWork修复版】发送请求到: {url}")
            response = await client.post(url, json=request_data, headers=headers)
            print(f"🎨 【DreamWork修复版】响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"🎨 【DreamWork修复版】请求成功!")
                return result
            else:
                error_text = response.text
                print(f"🎨 【DreamWork修复版】错误响应: {error_text}")

                # 专门处理code: 0的错误
                try:
                    error_json = response.json()
                    if "code" in error_json and error_json["code"] == 0:
                        error_msg = error_json.get(
                            "msg", error_json.get("message", "未知错误")
                        )
                        raise ValueError(f"DreamWork API返回错误: {error_msg}")
                    elif "error" in error_json:
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
        print(f"🎨 【DreamWork修复版】请求异常: {e}")
        raise ValueError(f"DreamWork API请求失败: {e}")


# 应用到原有的类中
def monkey_patch_dreamwork_client():
    """猴子补丁：替换原有的图生图函数"""
    from open_webui.utils.dreamwork import DreamWorkApiClient

    # 将修复版函数绑定到类上
    DreamWorkApiClient.generate_image_to_image = generate_image_to_image_fixed
