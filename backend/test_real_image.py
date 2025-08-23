#!/usr/bin/env python3
"""
测试真实图片的DreamWork API调用
"""

import asyncio
import sys
import base64
from PIL import Image
import io

sys.path.append("/Users/liuqingliang/Desktop/openwebui/open-webui/backend")

from open_webui.models.dreamwork import DreamWorkConfig
from open_webui.utils.dreamwork_url_fix import generate_image_to_image_url_fix


def create_test_image():
    """创建一个真实大小的测试图片"""
    # 创建一个100x100的彩色测试图片
    img = Image.new("RGB", (100, 100), color="red")

    # 添加一些图案
    for x in range(100):
        for y in range(100):
            if (x + y) % 20 < 10:
                img.putpixel((x, y), (0, 255, 0))  # 绿色

    # 转换为base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_data = buffer.getvalue()

    base64_data = base64.b64encode(img_data).decode("utf-8")
    print(f"✅ 创建测试图片: {len(img_data)} bytes, base64: {len(base64_data)} chars")

    return f"data:image/png;base64,{base64_data}"


class TestRequest:
    def __init__(self, image_data):
        self.image = image_data
        self.prompt = "make this image more colorful and vibrant"


async def test_with_real_image():
    """使用真实图片测试DreamWork API"""
    print("🎨 使用真实图片测试DreamWork图生图API")
    print("=" * 50)

    # 获取配置
    config = DreamWorkConfig.get_config()
    if not config:
        print("❌ 无法获取DreamWork配置")
        return

    # 创建测试图片
    test_image = create_test_image()
    request = TestRequest(test_image)

    try:
        print("\n🔄 开始测试API调用...")
        result = await generate_image_to_image_url_fix(config, request)
        print("✅ API调用成功!")
        print(f"结果: {result}")

    except Exception as e:
        print(f"❌ API调用失败: {e}")

        # 分析具体错误
        error_str = str(e)
        if "unsupported protocol scheme" in error_str:
            print("\n💡 分析: DreamWork API确实不支持data URL格式")
            print("   需要实现图片上传到可访问的URL服务")
        elif "invalid image url" in error_str:
            print("\n💡 分析: API期望的是HTTP/HTTPS URL")
            print("   建议实现临时图片托管服务")
        else:
            print(f"\n💡 其他错误: {error_str}")


if __name__ == "__main__":
    asyncio.run(test_with_real_image())
