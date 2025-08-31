#!/usr/bin/env python3
"""
调试Veo任务操作API - 测试取消任务功能
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
import uuid

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))

# 设置环境变量
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

# 设置日志级别
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_veo_action():
    """测试Veo任务操作"""
    try:
        print("🔧 正在导入Veo模块...")
        from open_webui.models.veo import VeoConfig, VeoTask
        from open_webui.models.credits import Credits

        print("✅ 模块导入成功")

        # 创建测试配置
        print("📋 创建测试配置...")
        config_data = {
            "enabled": True,
            "base_url": "https://api.veoai.com",
            "api_key": "test-api-key-for-debugging",
            "default_model": "veo3-pro-frames",
            "default_enhance_prompt": True,
            "max_concurrent_tasks": 3,
            "task_timeout": 900000,
            "query_interval": 15000,
            "model_credits_config": {
                "veo3": 100,
                "veo3-fast": 80,
                "veo3-pro": 150,
                "veo3-pro-frames": 200,
            },
        }

        config = VeoConfig.save_config(config_data)
        print(f"✅ 配置创建成功")

        # 创建测试用户和积分
        test_user_id = "test_user_action_001"
        print(f"💰 为测试用户 {test_user_id} 设置积分...")
        Credits.update_user_credits(test_user_id, 1000)
        print(f"💰 用户积分设置完成")

        # 创建测试任务
        print("📝 创建测试任务...")
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "user_id": test_user_id,
            "status": "processing",  # 设置为可以取消的状态
            "prompt": "A test video for cancellation",
            "model": "veo3-pro-frames",
            "enhance_prompt": True,
            "credits_cost": 200,
            "properties": {},
        }

        task = VeoTask.create_task(task_data)
        print(f"✅ 测试任务创建成功: {task.id}")
        print(f"📊 任务信息: user_id={task.user_id}, status={task.status}")

        # 测试任务操作API的逻辑
        print("\n🎯 开始测试任务操作逻辑...")
        print("=" * 60)

        # 模拟API调用
        action_data = {"action": "cancel", "task_id": task_id}

        print(f"📋 操作请求数据: {action_data}")

        # 检查参数
        action = action_data.get("action")
        task_id_param = action_data.get("task_id")

        print(f"🔍 解析参数: action={action}, task_id={task_id_param}")

        if not action or not task_id_param:
            print("❌ 缺少必要参数")
            return False

        # 查询任务
        print(f"🔍 查询任务: {task_id_param}")
        retrieved_task = VeoTask.get_task_by_id(task_id_param)
        if not retrieved_task:
            print("❌ 任务不存在")
            return False

        print(f"✅ 找到任务: id={retrieved_task.id}, status={retrieved_task.status}")

        # 检查任务状态
        if retrieved_task.status in ["completed", "failed", "cancelled"]:
            print(f"❌ 任务状态不允许取消: {retrieved_task.status}")
            return False

        print(f"✅ 任务状态允许取消: {retrieved_task.status}")

        # 更新任务状态
        print("🔄 更新任务状态为已取消...")
        from datetime import datetime

        VeoTask.update_task_status(
            task_id_param,
            {
                "status": "cancelled",
                "fail_reason": "测试取消",
                "finish_time": datetime.now(),
            },
        )

        # 验证更新
        updated_task = VeoTask.get_task_by_id(task_id_param)
        print(f"✅ 任务状态已更新: {updated_task.status}")

        # 退还积分测试
        if retrieved_task.credits_cost:
            print(f"💰 退还积分: {retrieved_task.credits_cost}")
            from open_webui.utils.veo import add_user_credits

            add_user_credits(
                retrieved_task.user_id,
                retrieved_task.credits_cost,
                task_id_param,
                "测试取消任务",
            )
            print("✅ 积分退还完成")

        print("=" * 60)
        print("✅ Veo任务操作测试完成 - 所有步骤成功")
        return True

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 开始调试Veo任务操作API...")
    print("🔍 这将测试取消任务的完整流程")
    print("=" * 60)

    success = asyncio.run(test_veo_action())

    print("=" * 60)
    if success:
        print("✅ Veo任务操作API调试完成 - 执行成功")
    else:
        print("❌ Veo任务操作API调试完成 - 执行失败")
        print("📋 请查看上方的详细日志来定位问题")
