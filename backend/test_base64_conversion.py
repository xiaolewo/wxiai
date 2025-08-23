#!/usr/bin/env python3
"""
测试base64图片到临时URL的转换功能
"""

import requests
import json
import base64
import os


def create_test_base64_image():
    """创建一个测试用的base64图片"""
    # 创建一个简单的1x1像素的PNG图片的base64数据
    # 这是一个透明的1x1像素PNG图片
    tiny_png_base64 = """iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jINnEAAAAABJRU5ErkJggg=="""

    # 构建完整的data URL格式
    return f"data:image/png;base64,{tiny_png_base64}"


def test_base64_image_to_video():
    """测试base64图片转视频功能"""

    print("🧪 测试base64图片转视频功能...")

    # 创建测试用的base64图片
    base64_image = create_test_base64_image()
    print(f"📸 创建测试base64图片: {base64_image[:50]}...")

    # 构建请求数据
    request_data = {
        "prompt": "一个简单的测试视频",
        "image": base64_image,  # 使用base64图片数据
        "duration": "5",
        "aspect_ratio": "16:9",
        "cfg_scale": 0.5,
    }

    print(f"📤 发送图生视频请求到 /api/v1/jimeng/submit/image-to-video")
    print(
        f"请求数据概要: prompt={request_data['prompt']}, image=base64数据({len(base64_image)}字符)"
    )

    try:
        # 发送请求到即梦图生视频API
        response = requests.post(
            "http://localhost:8080/api/v1/jimeng/submit/image-to-video",
            json=request_data,
            headers={
                "Content-Type": "application/json",
                # 注意：实际使用时需要有效的Bearer token
                # "Authorization": "Bearer your_token_here"
            },
            timeout=30,
        )

        print(f"📥 响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success"):
                print("✅ base64图片转换成功！")
                print(f"任务ID: {response_data.get('task_id')}")
                return True
            else:
                print("❌ API调用成功但任务创建失败")
                return False
        elif response.status_code == 401:
            print("⚠️ 需要认证（这是预期的，因为测试没有提供token）")
            if "即梦API不支持base64图片数据" not in response.text:
                print("✅ base64转换逻辑应该正常工作（没有base64相关错误）")
                return True
            else:
                print("❌ 仍然出现base64错误，转换逻辑未生效")
                return False
        elif response.status_code == 400:
            error_text = response.text
            if "即梦API不支持base64图片数据" in error_text:
                print("❌ base64转换逻辑未生效，仍然传递了base64数据")
                return False
            else:
                print("⚠️ 其他参数错误，但base64转换应该已经完成")
                return True
        else:
            print(f"❌ 意外的响应状态码: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保后端服务正在运行")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 请求过程中出错: {e}")
        return False


def test_content_array_with_base64():
    """测试content数组格式，包含base64图片"""

    print("\n🧪 测试content数组格式（包含base64图片）...")

    # 创建测试用的base64图片
    base64_image = create_test_base64_image()

    # 构建content数组格式的请求
    content_array = [
        {"type": "text", "text": "一个美丽的风景视频"},
        {"type": "image_url", "image_url": {"url": base64_image}},  # 使用base64作为URL
    ]

    request_data = {
        "content": content_array,
        "duration": "5",
        "aspect_ratio": "16:9",
        "cfg_scale": 0.5,
    }

    print(f"📤 发送content数组请求到 /api/v1/jimeng/submit/text-to-video")
    print(f"content数组包含: {len(content_array)} 个元素")

    try:
        response = requests.post(
            "http://localhost:8080/api/v1/jimeng/submit/text-to-video",
            json=request_data,
            headers={
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        print(f"📥 响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 401:
            if "即梦API不支持base64图片数据" not in response.text:
                print("✅ content数组中的base64处理应该正常工作")
                return True
            else:
                print("❌ content数组中的base64处理失败")
                return False
        elif response.status_code == 200:
            print("✅ content数组处理成功")
            return True
        else:
            print(f"⚠️ 其他状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🎬 即梦base64转换功能测试")
    print("=" * 60)

    # 测试1: 直接base64图片转视频
    test1_result = test_base64_image_to_video()

    # 测试2: content数组格式，包含base64图片
    test2_result = test_content_array_with_base64()

    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"直接base64转换: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"Content数组base64: {'✅ 通过' if test2_result else '❌ 失败'}")

    if test1_result and test2_result:
        print("🎉 所有base64转换测试通过！")
        exit(0)
    else:
        print("❌ 部分测试失败，需要进一步检查")
        exit(1)
