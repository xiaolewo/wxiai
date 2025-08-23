#!/usr/bin/env python3
"""
发送真实的即梦API请求进行测试
"""

import requests
import json


def test_real_jimeng_request():
    """发送真实的即梦API请求"""

    print("🧪 发送真实的即梦API请求...")

    # 用户提供的实际content格式
    content = [
        {
            "type": "text",
            "text": "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动 --wm true --dur 5",
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"
            },
        },
    ]

    # 构建请求数据
    request_data = {
        "content": content,
        "duration": "5",
        "aspect_ratio": "16:9",
        "cfg_scale": 0.5,
    }

    print(f"📤 发送请求到: http://localhost:8080/api/v1/jimeng/submit/text-to-video")
    print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

    try:
        # 发送请求
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

        return response.status_code, response.text

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None, str(e)


def test_direct_image_to_video():
    """直接测试图生视频API"""

    print("\n🧪 直接测试图生视频API...")

    # 直接使用图生视频格式
    request_data = {
        "prompt": "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头",
        "image_url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png",
        "duration": "5",
        "aspect_ratio": "16:9",
        "cfg_scale": 0.5,
    }

    print(f"📤 发送请求到: http://localhost:8080/api/v1/jimeng/submit/image-to-video")
    print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

    try:
        response = requests.post(
            "http://localhost:8080/api/v1/jimeng/submit/image-to-video",
            json=request_data,
            headers={
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        print(f"📥 响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        return response.status_code, response.text

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None, str(e)


if __name__ == "__main__":
    print("🎬 即梦真实API请求测试")
    print("=" * 60)

    # 测试1: content数组格式
    status1, response1 = test_real_jimeng_request()

    # 测试2: 直接图生视频格式
    status2, response2 = test_direct_image_to_video()

    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"Content数组请求: 状态码={status1}")
    print(f"直接图生视频请求: 状态码={status2}")

    # 检查是否到达了路由处理
    if status1 == 401 or status2 == 401:
        print("✅ 请求到达了后端路由（401表示需要认证）")
    elif status1 is not None or status2 is not None:
        print("⚠️ 请求到达了后端，但可能有其他问题")
    else:
        print("❌ 请求未能到达后端")
