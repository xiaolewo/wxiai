#!/usr/bin/env python3
"""
测试Veo任务操作HTTP请求 - 模拟前端的实际HTTP调用
"""

import os
import sys
import asyncio
import logging
import httpx
import json
from pathlib import Path

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


async def test_http_action_request():
    """测试HTTP请求到Veo action endpoint"""
    try:
        print("🌐 【HTTP测试】开始测试Veo action HTTP请求...")

        # 获取一个可以取消的任务ID
        from open_webui.models.veo import VeoTask
        from open_webui.internal.db import get_db

        with get_db() as db:
            # 查找一个处理中的任务，如果没有就使用任何已有任务进行测试
            task = (
                db.query(VeoTask)
                .filter(
                    VeoTask.status.in_(
                        ["processing", "submitted", "failed", "completed"]
                    )
                )
                .first()
            )

            if not task:
                print("❌ 【HTTP测试】没有找到可测试的任务")
                return False

            print(f"📋 【HTTP测试】使用任务进行测试: {task.id} (状态: {task.status})")

            # 模拟前端请求
            base_url = "http://localhost:8080"  # 假设后端运行在8080端口
            url = f"{base_url}/api/v1/veo/action"

            # 请求数据 - 和前端一致
            request_data = {"action": "cancel", "task_id": task.id}

            # 请求头 - 模拟前端
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token-for-debugging",  # 需要有效的token
                "Accept": "application/json",
            }

            print(f"🌐 【HTTP测试】请求URL: {url}")
            print(f"🌐 【HTTP测试】请求头: {headers}")
            print(f"🌐 【HTTP测试】请求数据: {json.dumps(request_data, indent=2)}")

            # 发送HTTP请求
            print("🌐 【HTTP测试】发送POST请求...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=request_data, headers=headers)

                print(f"🌐 【HTTP测试】响应状态: {response.status_code}")
                print(f"🌐 【HTTP测试】响应头: {dict(response.headers)}")

                try:
                    response_data = response.json()
                    print(
                        f"🌐 【HTTP测试】响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}"
                    )
                except Exception as e:
                    print(f"🌐 【HTTP测试】响应文本: {response.text}")
                    print(f"🌐 【HTTP测试】JSON解析错误: {e}")

                if response.status_code == 400:
                    print("❌ 【HTTP测试】确认400错误重现")
                    return False
                elif response.is_success:
                    print("✅ 【HTTP测试】HTTP请求成功")
                    return True
                else:
                    print(f"⚠️ 【HTTP测试】其他HTTP错误: {response.status_code}")
                    return False

    except Exception as e:
        print(f"❌ 【HTTP测试】测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_direct_endpoint():
    """直接测试endpoint函数（绕过HTTP层）"""
    try:
        print("🔧 【直接测试】测试endpoint函数...")

        # 导入必要的模块
        from open_webui.routers.veo import veo_task_action
        from open_webui.models.veo import VeoTask
        from open_webui.models.users import Users
        from fastapi import Request
        from unittest.mock import Mock

        # 创建模拟请求对象
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url = "http://localhost:8080/api/v1/veo/action"
        mock_request.headers = {
            "content-type": "application/json",
            "authorization": "Bearer test-token",
        }

        # 查找一个可以取消的任务，或者创建一个测试任务
        from open_webui.internal.db import get_db

        with get_db() as db:
            # 首先尝试找一个processing或submitted的任务
            task = (
                db.query(VeoTask)
                .filter(VeoTask.status.in_(["processing", "submitted"]))
                .first()
            )

            if not task:
                print("📝 【直接测试】没有找到可取消的任务，创建测试任务...")
                # 创建一个测试任务
                import uuid
                from datetime import datetime

                task_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": "test_user_cancel_debug",
                    "status": "processing",  # 可以取消的状态
                    "prompt": "Test task for cancellation debugging",
                    "model": "veo3-pro-frames",
                    "enhance_prompt": True,
                    "credits_cost": 200,
                    "properties": {},
                }

                task = VeoTask.create_task(task_data)
                print(f"✅ 【直接测试】测试任务创建成功: {task.id}")

        # 创建模拟用户对象 - 使用任务的实际所有者
        mock_user = Mock()
        mock_user.id = task.user_id  # 使用任务实际的user_id
        mock_user.role = "user"

        print(f"📋 【直接测试】使用任务: {task.id}")

        # 测试数据
        action_data = {"action": "cancel", "task_id": task.id}

        print(f"🔧 【直接测试】调用endpoint函数...")
        result = await veo_task_action(mock_request, action_data, mock_user)

        print(f"✅ 【直接测试】endpoint函数调用成功: {result}")
        return True

    except Exception as e:
        print(f"❌ 【直接测试】直接调用失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 开始调试Veo任务操作HTTP请求...")
    print("=" * 60)

    # 测试1: 直接调用endpoint函数
    print("\n📍 测试1: 直接调用endpoint函数")
    print("-" * 40)
    direct_success = asyncio.run(test_direct_endpoint())

    # 测试2: HTTP请求（如果直接调用成功）
    if direct_success:
        print("\n📍 测试2: 发送实际HTTP请求")
        print("-" * 40)
        http_success = asyncio.run(test_http_action_request())
    else:
        print("\n⚠️ 跳过HTTP测试，因为直接调用失败")
        http_success = False

    print("=" * 60)
    print("🧪 调试测试完成")
    print(f"直接调用结果: {'✅ 成功' if direct_success else '❌ 失败'}")
    print(f"HTTP请求结果: {'✅ 成功' if http_success else '❌ 失败'}")
