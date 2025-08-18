#!/usr/bin/env python3
"""
直接测试即梦content解析功能，不通过HTTP请求
"""

import sys
import os

sys.path.append("/Users/liuqingliang/Desktop/openwebui/wxiai-main/backend")


def test_content_parsing_directly():
    """直接测试content解析功能"""

    print("🧪 直接测试即梦content解析功能...")

    from open_webui.routers.jimeng import parse_content_for_jimeng

    # 测试1: 普通图片URL
    print("\n📝 测试1: 普通图片URL")
    content1 = [
        {"type": "text", "text": "一个美丽的风景视频"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
    ]

    prompt1, image_url1 = parse_content_for_jimeng(content1)
    print(f"解析结果: prompt='{prompt1}', image_url='{image_url1}'")

    # 测试2: base64图片URL
    print("\n📝 测试2: base64图片URL")
    base64_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jINnEAAAAABJRU5ErkJggg=="

    content2 = [
        {"type": "text", "text": "基于上传图片的视频"},
        {"type": "image_url", "image_url": {"url": base64_data}},
    ]

    print(f"输入base64数据长度: {len(base64_data)} 字符")

    try:
        prompt2, image_url2 = parse_content_for_jimeng(content2)
        print(f"解析结果: prompt='{prompt2}', image_url='{image_url2[:50]}...'")

        # 验证转换结果
        if image_url2.startswith("http://localhost:8080/api/v1/jimeng/temp-image/"):
            print("✅ base64成功转换为临时URL")
            return True
        elif image_url2.startswith("data:image/"):
            print("❌ base64未被转换，仍然是原始数据")
            return False
        else:
            print(f"⚠️ 意外的URL格式: {image_url2}")
            return False

    except Exception as e:
        print(f"❌ 解析过程中出错: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_temp_file_service():
    """测试临时文件创建和访问"""

    print("\n🧪 测试临时文件创建...")

    from open_webui.utils.jimeng import save_base64_to_temp_file
    import requests

    base64_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jINnEAAAAABJRU5ErkJggg=="

    try:
        # 创建临时文件
        temp_relative_path = save_base64_to_temp_file(base64_data)
        temp_url = f"http://localhost:8080/{temp_relative_path}"

        print(f"临时文件路径: {temp_relative_path}")
        print(f"临时文件URL: {temp_url}")

        # 测试访问临时文件
        print("测试访问临时文件...")
        response = requests.get(temp_url, timeout=5)

        if response.status_code == 200:
            print(f"✅ 临时文件可访问，内容长度: {len(response.content)} 字节")
            return True
        else:
            print(f"❌ 临时文件访问失败，状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 临时文件创建或访问失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🎬 即梦content解析功能测试")
    print("=" * 60)

    # 测试1: 直接解析功能
    test1_result = test_content_parsing_directly()

    # 测试2: 临时文件服务
    test2_result = test_temp_file_service()

    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"直接content解析: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"临时文件服务: {'✅ 通过' if test2_result else '❌ 失败'}")

    if test1_result and test2_result:
        print("🎉 所有content解析测试通过！")
        exit(0)
    else:
        print("❌ 部分测试失败，需要进一步检查")
        exit(1)
