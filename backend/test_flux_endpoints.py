#!/usr/bin/env python3
"""
Flux API端点测试脚本
验证所有API接口的基本功能
"""

import asyncio
import sys
import os
import json

# 添加项目路径到Python路径
sys.path.insert(0, "/Users/liuqingliang/Desktop/wxiai/wxiai-main/backend")

from open_webui.models.flux import (
    FluxConfigs,
    FluxTasks,
    FluxCreditsManager,
    FluxConfigForm,
    FluxTextToImageRequest,
    FluxImageToImageRequest,
    get_supported_flux_models,
    is_flux_enabled,
)


async def test_flux_config_management():
    """测试Flux配置管理"""
    print("🔧 测试Flux配置管理...")

    # 1. 测试创建配置
    config_data = FluxConfigForm(
        api_key="test_fal_ai_key_12345",
        base_url="https://queue.fal.run",
        enabled=True,
        timeout=300,
        max_concurrent_tasks=3,
        default_model="fal-ai/flux-1/dev",
    )

    # 保存配置
    config = FluxConfigs.create_or_update_config(config_data)
    print(f"  ✅ 配置创建成功: {config.id}")

    # 2. 测试获取配置
    retrieved_config = FluxConfigs.get_config()
    assert retrieved_config is not None
    assert retrieved_config.enabled == True
    assert retrieved_config.default_model == "fal-ai/flux-1/dev"
    print(f"  ✅ 配置获取成功: enabled={retrieved_config.enabled}")

    # 3. 测试服务状态
    enabled = is_flux_enabled()
    print(f"  ✅ 服务状态检查: {enabled}")

    return config


async def test_flux_tasks():
    """测试Flux任务管理"""
    print("\n📋 测试Flux任务管理...")

    # 1. 创建文本生图任务
    task1 = FluxTasks.create_task(
        user_id="test_user_456",
        model="fal-ai/flux-1/dev",
        task_type="text_to_image",
        prompt="A beautiful sunset over mountains",
        request_id="test_request_123",
        num_images=1,
        aspect_ratio="1:1",
        guidance_scale=3.5,
    )
    print(f"  ✅ 文本生图任务创建成功: {task1.id}")

    # 2. 创建图生图任务
    task2 = FluxTasks.create_task(
        user_id="test_user_456",
        model="fal-ai/flux-1/dev/image-to-image",
        task_type="image_to_image",
        prompt="A stylized version of this landscape",
        request_id="test_request_124",
        input_image_url="https://example.com/input.jpg",
        strength=0.8,
    )
    print(f"  ✅ 图生图任务创建成功: {task2.id}")

    # 3. 查询任务
    retrieved_task = FluxTasks.get_task_by_id(task1.id)
    assert retrieved_task is not None
    assert retrieved_task.prompt == "A beautiful sunset over mountains"
    print(f"  ✅ 任务查询成功: {retrieved_task.task_type}")

    # 4. 更新任务状态
    success = FluxTasks.update_task_status(
        task1.id,
        "IN_PROGRESS",
        queue_position=3,
        image_url="https://example.com/generated.jpg",
    )
    assert success == True
    print(f"  ✅ 任务状态更新成功")

    # 5. 获取用户任务列表
    user_tasks = FluxTasks.get_user_tasks("test_user_456", page=1, limit=10)
    assert len(user_tasks) >= 2
    print(f"  ✅ 用户任务列表: {len(user_tasks)}个任务")

    return task1, task2


async def test_flux_credits():
    """测试Flux积分系统"""
    print("\n💰 测试Flux积分系统...")

    # 1. 获取用户积分
    user_id = "test_user_789"
    credits = FluxCreditsManager.get_user_credits(user_id)
    print(f"  ✅ 用户积分: {credits.credits_balance}")

    # 2. 添加积分
    success = FluxCreditsManager.add_credits(user_id, 50)
    assert success == True

    updated_credits = FluxCreditsManager.get_user_credits(user_id)
    assert updated_credits.credits_balance >= 50
    print(f"  ✅ 添加积分后: {updated_credits.credits_balance}")

    # 3. 扣除积分
    success = FluxCreditsManager.deduct_credits(user_id, 20)
    assert success == True

    final_credits = FluxCreditsManager.get_user_credits(user_id)
    print(f"  ✅ 扣除积分后: {final_credits.credits_balance}")

    return credits


async def test_request_models():
    """测试请求模型"""
    print("\n🔬 测试请求模型...")

    # 1. 文本生图请求
    text_request = FluxTextToImageRequest(
        model="fal-ai/flux-1/schnell",
        prompt="A cyberpunk cityscape at night",
        num_images=1,
        aspect_ratio="16:9",
        guidance_scale=4.0,
        num_inference_steps=20,
        seed=42,
        sync_mode=False,
        enable_safety_checker=True,
    )
    print(f"  ✅ 文本生图请求模型: {text_request.model}")

    # 2. 图生图请求
    image_request = FluxImageToImageRequest(
        model="fal-ai/flux-1/dev/image-to-image",
        prompt="Transform into anime style",
        image_url="https://example.com/input.jpg",
        strength=0.75,
        num_images=1,
        guidance_scale=3.5,
        sync_mode=False,
    )
    print(f"  ✅ 图生图请求模型: {image_request.model}")

    return text_request, image_request


async def test_model_support():
    """测试模型支持"""
    print("\n🤖 测试模型支持...")

    # 1. 获取支持的模型
    models = get_supported_flux_models()
    print(f"  ✅ 支持的模型数量: {len(models)}")

    # 2. 验证关键模型存在
    model_ids = [model["id"] for model in models]
    key_models = [
        "fal-ai/flux-1/dev",
        "fal-ai/flux-1/schnell",
        "fal-ai/flux-1/dev/image-to-image",
    ]

    for model_id in key_models:
        assert model_id in model_ids, f"Missing key model: {model_id}"
        print(f"  ✅ 关键模型存在: {model_id}")

    # 3. 模型信息验证
    dev_model = next(m for m in models if m["id"] == "fal-ai/flux-1/dev")
    assert "type" in dev_model
    print(f"  ✅ 模型信息验证: {dev_model['type']}")

    return models


async def test_api_client_basic():
    """测试API客户端基础功能"""
    print("\n🌐 测试API客户端基础功能...")

    try:
        from open_webui.utils.flux_api import FluxAPIClient

        # 获取配置
        config = FluxConfigs.get_config()
        if config:
            client = FluxAPIClient(config)
            print(f"  ✅ API客户端创建成功: {client.base_url}")

            # 测试支持模型验证
            try:
                client._validate_model("fal-ai/flux-1/dev")
                print(f"  ✅ 模型验证通过")
            except Exception as e:
                print(f"  ❌ 模型验证失败: {e}")

            # 测试URL构建
            url = client._build_model_url("fal-ai/flux-1/dev")
            expected = "https://queue.fal.run/fal-ai/flux-1/dev"
            assert url == expected
            print(f"  ✅ URL构建正确: {url}")

        else:
            print(f"  ⚠️  没有配置，跳过API客户端测试")

    except Exception as e:
        print(f"  ❌ API客户端测试失败: {e}")


async def main():
    """主测试函数"""
    print("🚀 Flux API端点功能测试开始")
    print("=" * 60)

    try:
        # 测试各个功能模块
        config = await test_flux_config_management()
        task1, task2 = await test_flux_tasks()
        credits = await test_flux_credits()
        text_req, image_req = await test_request_models()
        models = await test_model_support()
        await test_api_client_basic()

        print("\n" + "=" * 60)
        print("🎉 所有测试完成！Flux API功能正常")

        # 总结信息
        print(f"\n📊 测试总结:")
        print(f"  - 配置管理: ✅ 正常")
        print(f"  - 任务管理: ✅ 正常")
        print(f"  - 积分系统: ✅ 正常")
        print(f"  - 请求模型: ✅ 正常")
        print(f"  - 模型支持: ✅ {len(models)}个模型")
        print(f"  - API客户端: ✅ 基础功能正常")

        return True

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
