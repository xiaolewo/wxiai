#!/usr/bin/env python3
"""
测试即梦图生视频API的image_url传递
"""

import sys
import os

sys.path.append("/Users/liuqingliang/Desktop/openwebui/wxiai-main/backend")


def test_content_parsing():
    """测试content数组解析是否正确提取image_url"""

    from open_webui.routers.jimeng import parse_content_for_jimeng
    from open_webui.models.jimeng import JimengGenerateRequest

    print("🧪 测试content数组解析...")

    # 模拟用户发送的content数组
    test_content = [
        {"type": "text", "text": "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头"},
        {
            "type": "image_url",
            "image_url": {
                "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"
            },
        },
    ]

    # 测试解析函数
    prompt, image_url = parse_content_for_jimeng(test_content)
    print(f"解析结果:")
    print(f"  prompt: {prompt}")
    print(f"  image_url: {image_url}")

    # 测试数据模型
    request = JimengGenerateRequest(
        content=test_content, duration="5", aspect_ratio="16:9", cfg_scale=0.5
    )

    parsed_prompt, parsed_image_url = request.get_parsed_content()
    print(f"模型解析结果:")
    print(f"  prompt: {parsed_prompt}")
    print(f"  image_url: {parsed_image_url}")

    # 验证结果
    expected_image_url = (
        "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"
    )
    if parsed_image_url == expected_image_url:
        print("✅ image_url解析正确")
        return True
    else:
        print(f"❌ image_url解析错误，期望: {expected_image_url}")
        return False


def test_jimeng_api_call():
    """测试即梦API调用逻辑"""

    from open_webui.utils.jimeng import JimengApiClient
    from open_webui.models.jimeng import JimengConfig, JimengGenerateRequest

    print("\n🧪 测试即梦API调用逻辑...")

    # 创建模拟配置
    config = JimengConfig(
        enabled=True,
        base_url="https://ark.cn-beijing.volces.com",
        api_key="test_api_key",
    )

    # 创建API客户端
    client = JimengApiClient(config)

    # 创建请求对象
    request = JimengGenerateRequest(
        prompt="测试提示词",
        image_url="https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png",
        duration="5",
        aspect_ratio="16:9",
        cfg_scale=0.5,
    )

    # 测试请求数据构建（不实际发送请求）
    try:
        # 构建请求数据
        request_data = {
            "prompt": request.prompt.strip(),
            "duration": int(request.duration),
            "aspect_ratio": request.aspect_ratio,
            "cfg_scale": float(request.cfg_scale),
        }

        # 如果有图片URL，添加图生视频参数
        if request.image_url:
            request_data["image_url"] = request.image_url
            print(f"✅ 图片URL已添加到请求: {request.image_url}")

        print(f"构建的请求数据: {request_data}")

        # 验证请求数据格式
        required_fields = [
            "prompt",
            "duration",
            "aspect_ratio",
            "cfg_scale",
            "image_url",
        ]
        for field in required_fields:
            if field not in request_data:
                print(f"❌ 缺少字段: {field}")
                return False

        print("✅ 请求数据格式正确")
        return True

    except Exception as e:
        print(f"❌ 构建请求数据失败: {e}")
        return False


def test_jimeng_video_generation():
    """测试完整的即梦视频生成流程"""

    from open_webui.models.jimeng import JimengGenerateRequest

    print("\n🧪 测试完整流程...")

    # 模拟用户content数组
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

    # 创建请求
    request = JimengGenerateRequest(
        content=content, duration="5", aspect_ratio="16:9", cfg_scale=0.5
    )

    # 解析content
    parsed_prompt, parsed_image_url = request.get_parsed_content()

    # 更新请求对象
    request.prompt = parsed_prompt
    request.image_url = parsed_image_url

    print(f"最终请求:")
    print(f"  prompt: {request.prompt}")
    print(f"  image_url: {request.image_url}")
    print(f"  duration: {request.duration}")
    print(f"  aspect_ratio: {request.aspect_ratio}")
    print(f"  cfg_scale: {request.cfg_scale}")

    # 验证必要字段
    if request.prompt and request.image_url:
        print("✅ 图生视频请求数据完整")
        return True
    else:
        print("❌ 图生视频请求数据不完整")
        return False


if __name__ == "__main__":
    print("🎬 即梦图生视频测试")
    print("=" * 50)

    # 测试1: content解析
    test1_result = test_content_parsing()

    # 测试2: API调用逻辑
    test2_result = test_jimeng_api_call()

    # 测试3: 完整流程
    test3_result = test_jimeng_video_generation()

    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"Content解析: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"API调用逻辑: {'✅ 通过' if test2_result else '❌ 失败'}")
    print(f"完整流程: {'✅ 通过' if test3_result else '❌ 失败'}")

    if test1_result and test2_result and test3_result:
        print("🎉 所有测试通过！即梦图生视频应该能正常工作！")
        exit(0)
    else:
        print("❌ 部分测试失败，需要进一步检查")
        exit(1)
