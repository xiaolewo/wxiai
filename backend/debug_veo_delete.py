#!/usr/bin/env python3
"""
测试Veo任务删除功能 - 验证delete操作
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
os.environ.setdefault('OPENAI_API_KEY', 'sk-test')

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_veo_delete():
    """测试Veo任务删除功能"""
    try:
        print("🗑️ 开始测试Veo任务删除功能...")
        
        from open_webui.models.veo import VeoTask
        from open_webui.routers.veo import veo_task_action
        from fastapi import Request
        from unittest.mock import Mock
        from datetime import datetime
        
        # 1. 创建一个测试任务（失败状态）
        print("\n📝 步骤1: 创建测试任务...")
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "user_id": "test_user_delete",
            "status": "failed",  # 失败状态，按之前的逻辑不能取消，但应该可以删除
            "prompt": "Test task for deletion - failed task",
            "model": "veo3-pro-frames",
            "enhance_prompt": True,
            "credits_cost": 200,
            "fail_reason": "测试用的失败任务",
            "properties": {}
        }
        
        task = VeoTask.create_task(task_data)
        print(f"✅ 测试任务创建成功: {task.id}")
        print(f"📊 任务状态: {task.status}")
        
        # 2. 验证任务存在
        print("\n🔍 步骤2: 验证任务存在...")
        retrieved_task = VeoTask.get_task_by_id(task_id)
        if retrieved_task:
            print(f"✅ 任务存在: {retrieved_task.id}, 状态: {retrieved_task.status}")
        else:
            print("❌ 任务不存在")
            return False
        
        # 3. 测试取消操作（应该失败，因为是failed状态）
        print("\n🚫 步骤3: 测试取消操作（应该失败）...")
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url = "http://localhost:8080/api/v1/veo/action"
        mock_request.headers = {"content-type": "application/json"}
        
        mock_user = Mock()
        mock_user.id = "test_user_delete"
        mock_user.role = "user"
        
        cancel_data = {
            "action": "cancel",
            "task_id": task_id
        }
        
        try:
            result = await veo_task_action(mock_request, cancel_data, mock_user)
            print(f"❌ 取消操作意外成功: {result}")
        except Exception as e:
            print(f"✅ 取消操作正确失败: {str(e)}")
            
        # 4. 测试删除操作（应该成功）
        print("\n🗑️ 步骤4: 测试删除操作（应该成功）...")
        delete_data = {
            "action": "delete",
            "task_id": task_id
        }
        
        try:
            result = await veo_task_action(mock_request, delete_data, mock_user)
            print(f"✅ 删除操作成功: {result}")
            
            # 5. 验证任务已被删除
            print("\n🔍 步骤5: 验证任务已被删除...")
            deleted_task = VeoTask.get_task_by_id(task_id)
            if deleted_task is None:
                print("✅ 任务已成功删除")
                return True
            else:
                print(f"❌ 任务仍然存在: {deleted_task.id}")
                return False
                
        except Exception as e:
            print(f"❌ 删除操作失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_delete_multiple_statuses():
    """测试删除不同状态的任务"""
    try:
        print("\n🧪 测试删除不同状态的任务...")
        
        from open_webui.models.veo import VeoTask
        
        test_statuses = ["failed", "completed", "cancelled", "submitted", "processing"]
        results = {}
        
        for status in test_statuses:
            print(f"\n📋 测试删除状态为 '{status}' 的任务...")
            
            # 创建测试任务
            task_id = str(uuid.uuid4())
            task_data = {
                "id": task_id,
                "user_id": "test_user_delete_multi",
                "status": status,
                "prompt": f"Test task for deletion - {status} status",
                "model": "veo3",
                "enhance_prompt": False,
                "credits_cost": 100,
                "properties": {}
            }
            
            task = VeoTask.create_task(task_data)
            print(f"✅ 创建 {status} 任务: {task.id}")
            
            # 直接测试删除方法
            success = VeoTask.delete_task(task_id)
            if success:
                print(f"✅ {status} 任务删除成功")
                results[status] = True
            else:
                print(f"❌ {status} 任务删除失败")
                results[status] = False
        
        print("\n📊 删除结果汇总:")
        for status, success in results.items():
            icon = "✅" if success else "❌"
            print(f"  {icon} {status}: {'成功' if success else '失败'}")
            
        return all(results.values())
        
    except Exception as e:
        print(f"❌ 多状态删除测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始测试Veo任务删除功能...")
    print("=" * 60)
    
    # 测试1: 基本删除功能
    print("\n📍 测试1: 基本删除功能")
    print("-" * 40)
    basic_success = asyncio.run(test_veo_delete())
    
    # 测试2: 多状态删除
    print("\n📍 测试2: 删除不同状态的任务")
    print("-" * 40)
    multi_success = asyncio.run(test_delete_multiple_statuses())
    
    print("=" * 60)
    print("🧪 Veo任务删除功能测试完成")
    print(f"基本删除功能: {'✅ 成功' if basic_success else '❌ 失败'}")
    print(f"多状态删除测试: {'✅ 成功' if multi_success else '❌ 失败'}")
    
    if basic_success and multi_success:
        print("🎉 所有删除功能测试通过！")
    else:
        print("⚠️ 部分测试失败，需要检查实现")