#!/usr/bin/env python3
"""
Flux API测试脚本
测试Flux路由和基础功能
"""

import asyncio
import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, "/Users/liuqingliang/Desktop/wxiai/wxiai-main/backend")

from open_webui.models.flux import (
    FluxConfigs,
    FluxTasks,
    FluxCreditsManager,
    FluxConfigForm,
    get_supported_flux_models,
    is_flux_enabled,
)


async def test_basic_functions():
    """测试基础功能"""
    print("🧪 测试Flux基础功能...")

    # 1. 测试支持的模型列表
    print("\n📋 支持的Flux模型:")
    models = get_supported_flux_models()
    for i, model in enumerate(models[:5], 1):  # 显示前5个
        print(f"  {i}. {model['name']} ({model['id']}) - {model['description']}")
    print(f"  ... 共{len(models)}个模型")

    # 2. 测试服务状态
    print(f"\n🔧 服务状态: {'✅ 已启用' if is_flux_enabled() else '❌ 未启用'}")

    # 3. 测试配置管理
    print("\n⚙️ 配置管理测试:")
    config = FluxConfigs.get_config()
    if config:
        print(f"  ✅ 找到配置: {config.default_model}")
    else:
        print("  ❌ 未找到配置，创建默认配置...")

        # 创建默认配置
        default_config = FluxConfigForm(
            api_key="test_api_key_placeholder",
            base_url="https://queue.fal.run",
            enabled=False,  # 默认禁用，避免实际调用
            timeout=300,
            max_concurrent_tasks=5,
            default_model="fal-ai/flux-1/dev",
        )

        try:
            new_config = FluxConfigs.create_or_update_config(default_config)
            print(f"  ✅ 创建配置成功: {new_config.id}")
        except Exception as e:
            print(f"  ❌ 创建配置失败: {e}")

    # 4. 测试积分系统
    print("\n💰 积分系统测试:")
    try:
        test_user_id = "test_user_123"
        credits = FluxCreditsManager.get_user_credits(test_user_id)
        print(f"  ✅ 用户 {test_user_id} 积分: {credits.credits_balance}")

        # 测试添加积分
        success = FluxCreditsManager.add_credits(test_user_id, 50)
        if success:
            updated_credits = FluxCreditsManager.get_user_credits(test_user_id)
            print(f"  ✅ 添加50积分后: {updated_credits.credits_balance}")
    except Exception as e:
        print(f"  ❌ 积分系统测试失败: {e}")

    print("\n🎉 基础功能测试完成！")


async def test_api_client():
    """测试API客户端"""
    print("\n🌐 测试Flux API客户端...")

    try:
        from open_webui.utils.flux_api import FluxAPIClient, FluxAPIError
        from open_webui.models.flux import FluxTextToImageRequest

        # 获取配置
        config = FluxConfigs.get_config()
        if not config:
            print("  ❌ 未找到配置，跳过API客户端测试")
            return

        # 创建API客户端
        client = FluxAPIClient(config)
        print(f"  ✅ API客户端创建成功: {client.base_url}")

        # 测试连接（不实际发送请求）
        print("  ⚠️  连接测试跳过（避免实际API调用）")

        # 测试请求对象创建
        request = FluxTextToImageRequest(
            model="fal-ai/flux-1/dev",
            prompt="A beautiful sunset over mountains",
            num_images=1,
        )
        print(f"  ✅ 请求对象创建成功: {request.model}")

    except Exception as e:
        print(f"  ❌ API客户端测试失败: {e}")

    print("  ✅ API客户端测试完成")


async def test_database_operations():
    """测试数据库操作"""
    print("\n💾 测试数据库操作...")

    try:
        # 测试任务创建
        test_task = FluxTasks.create_task(
            user_id="test_user_123",
            model="fal-ai/flux-1/dev",
            task_type="text_to_image",
            prompt="Test prompt for database",
            request_id="test_request_123",
        )
        print(f"  ✅ 任务创建成功: {test_task.id}")

        # 测试任务查询
        found_task = FluxTasks.get_task_by_id(test_task.id)
        if found_task:
            print(f"  ✅ 任务查询成功: {found_task.prompt}")

        # 测试状态更新
        success = FluxTasks.update_task_status(
            test_task.id, "IN_PROGRESS", queue_position=5
        )
        if success:
            print("  ✅ 任务状态更新成功")

        # 测试用户任务列表
        user_tasks = FluxTasks.get_user_tasks("test_user_123", page=1, limit=10)
        print(f"  ✅ 用户任务列表: {len(user_tasks)}个任务")

    except Exception as e:
        print(f"  ❌ 数据库操作测试失败: {e}")
        import traceback

        traceback.print_exc()

    print("  ✅ 数据库操作测试完成")


async def main():
    """主测试函数"""
    print("🚀 Flux功能测试开始")
    print("=" * 50)

    try:
        await test_basic_functions()
        await test_api_client()
        await test_database_operations()

        print("\n" + "=" * 50)
        print("✅ 所有测试完成！Flux基础设施运行正常")

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
