#!/usr/bin/env python3
"""
调试Google Images积分扣除失败问题
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from open_webui.models.credits import Credits
from open_webui.models.google_images import GoogleImagesCredit
import uuid


def test_user_credits():
    """测试用户积分查询"""
    print("🔍 测试用户积分查询...")

    try:
        # 获取最新用户
        user_id = "1e402f55-88cc-4eb9-a364-8b51a441518a"
        print(f"📊 测试用户ID: {user_id}")

        user_credits = Credits.get_user_credits(user_id)
        if user_credits:
            print(f"✅ 用户积分记录存在:")
            print(f"   用户ID: {user_credits.user_id}")
            print(f"   积分余额: {user_credits.credit}")
            print(f"   类型: {type(user_credits.credit)}")
            return user_credits
        else:
            print("❌ 用户积分记录不存在")
            return None

    except Exception as e:
        print(f"❌ 查询用户积分失败: {str(e)}")
        return None


def test_credits_update():
    """测试积分更新"""
    print("\n🔄 测试积分更新...")

    try:
        user_id = "1e402f55-88cc-4eb9-a364-8b51a441518a"
        user_credits = Credits.get_user_credits(user_id)

        if not user_credits:
            print("❌ 没有用户积分记录，无法测试更新")
            return False

        original_credit = int(user_credits.credit)
        test_credit = original_credit - 20  # 扣除20积分

        print(f"📊 原始积分: {original_credit}")
        print(f"📊 目标积分: {test_credit}")

        # 尝试更新积分
        success = Credits.update_user_credits(user_id, test_credit)

        if success:
            print("✅ 积分更新成功")
            # 恢复原始积分
            Credits.update_user_credits(user_id, original_credit)
            print("🔄 积分已恢复到原始值")
            return True
        else:
            print("❌ 积分更新失败")
            return False

    except Exception as e:
        print(f"❌ 测试积分更新失败: {str(e)}")
        return False


def test_credit_log_creation():
    """测试积分记录创建"""
    print("\n📝 测试积分记录创建...")

    try:
        user_id = "1e402f55-88cc-4eb9-a364-8b51a441518a"
        task_id = f"test_{uuid.uuid4().hex[:8]}"

        log_data = {
            "user_id": user_id,
            "task_id": task_id,
            "credit_amount": 20,
            "credits_before": 9960,
            "credits_after": 9940,
            "operation_type": "deduct",
            "model_name": "nano-banana",
            "description": "测试积分扣除",
        }

        print(f"📊 测试积分记录数据: {log_data}")

        # 尝试创建积分记录
        credit_log = GoogleImagesCredit.create_credit_log(log_data)

        if credit_log:
            print(f"✅ 积分记录创建成功: ID={credit_log.id}")
            return True
        else:
            print("❌ 积分记录创建失败")
            return False

    except Exception as e:
        print(f"❌ 测试积分记录创建失败: {str(e)}")
        print(f"📊 错误类型: {type(e).__name__}")
        import traceback

        print(f"📊 错误堆栈:\n{traceback.format_exc()}")
        return False


def test_complete_deduction():
    """测试完整的积分扣除流程"""
    print("\n🎯 测试完整的积分扣除流程...")

    try:
        from open_webui.utils.google_images import deduct_user_credits

        user_id = "1e402f55-88cc-4eb9-a364-8b51a441518a"
        task_id = f"test_{uuid.uuid4().hex[:8]}"
        credits = 20
        model_name = "nano-banana"

        print(f"📊 扣除参数:")
        print(f"   用户ID: {user_id}")
        print(f"   任务ID: {task_id}")
        print(f"   扣除积分: {credits}")
        print(f"   模型名称: {model_name}")

        # 执行积分扣除
        result = deduct_user_credits(user_id, credits, task_id, model_name)

        if result:
            print("✅ 完整积分扣除流程成功")
            # 尝试返还积分
            from open_webui.utils.google_images import add_user_credits

            refund_result = add_user_credits(user_id, credits, task_id, "测试回退")
            if refund_result:
                print("🔄 积分已成功返还")
            return True
        else:
            print("❌ 完整积分扣除流程失败")
            return False

    except Exception as e:
        print(f"❌ 测试完整积分扣除流程失败: {str(e)}")
        import traceback

        print(f"📊 错误堆栈:\n{traceback.format_exc()}")
        return False


if __name__ == "__main__":
    print("🚀 开始调试Google Images积分扣除问题...")
    print("=" * 60)

    # 1. 测试用户积分查询
    user_credits = test_user_credits()

    if user_credits:
        # 2. 测试积分更新
        if test_credits_update():
            # 3. 测试积分记录创建
            if test_credit_log_creation():
                # 4. 测试完整流程
                test_complete_deduction()
            else:
                print("\n❌ 积分记录创建失败，这可能是主要问题")
        else:
            print("\n❌ 积分更新失败")
    else:
        print("\n❌ 无法获取用户积分")

    print("\n" + "=" * 60)
    print("🎯 调试完成")
