#!/usr/bin/env python3
"""
创建一个有效的测试图片
"""

from PIL import Image
import io


def create_valid_png():
    """创建一个有效的小PNG图片"""
    # 创建一个16x16的RGB图片
    img = Image.new("RGB", (16, 16), color="red")

    # 保存到字节流
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return img_bytes.getvalue()


def create_test_jpg():
    """创建一个有效的小JPG图片"""
    # 创建一个16x16的RGB图片
    img = Image.new("RGB", (16, 16), color="blue")

    # 保存到字节流
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    return img_bytes.getvalue()


if __name__ == "__main__":
    try:
        png_data = create_valid_png()
        jpg_data = create_test_jpg()

        print(f"PNG大小: {len(png_data)} bytes")
        print(f"JPG大小: {len(jpg_data)} bytes")

        # 保存到文件以供测试
        with open("test_image.png", "wb") as f:
            f.write(png_data)

        with open("test_image.jpg", "wb") as f:
            f.write(jpg_data)

        print("测试图片已创建: test_image.png, test_image.jpg")

    except ImportError:
        print("❌ 需要安装Pillow: pip install Pillow")
    except Exception as e:
        print(f"❌ 创建图片失败: {e}")
