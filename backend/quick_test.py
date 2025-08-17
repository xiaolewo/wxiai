#!/usr/bin/env python3
"""快速测试修复是否生效"""

import asyncio
import sys

sys.path.append("/Users/liuqingliang/Desktop/openwebui/open-webui/backend")

from open_webui.models.dreamwork import DreamWorkConfig
from open_webui.utils.dreamwork_fixed import generate_image_to_image_fixed


# 创建测试数据
class TestRequest:
    def __init__(self):
        # 使用真实大小的测试图片 (100x100 PNG)
        from PIL import Image
        import io
        import base64

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
        self.image = f"data:image/png;base64,{base64_data}"
        self.prompt = "make this image more vibrant and beautiful"


async def test_fix():
    print("🧪 快速测试DreamWork图生图修复")

    # 获取配置
    config = DreamWorkConfig.get_config()
    if not config:
        print("❌ 无法获取配置")
        return

    # 创建测试请求
    request = TestRequest()

    try:
        print("🔄 测试修复版API...")
        result = await generate_image_to_image_fixed(config, request)
        print("✅ 修复成功! API返回:")
        print(f"   模型: {result.get('model')}")
        print(f"   图片数量: {len(result.get('data', []))}")
        if result.get("data"):
            print(f"   图片URL: {result['data'][0].get('url', 'N/A')[:50]}...")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fix())
    if success:
        print("\n🎉 修复验证成功！图生图功能应该已经可以正常使用了。")
    else:
        print("\n⚠️ 还需要进一步调试。")
