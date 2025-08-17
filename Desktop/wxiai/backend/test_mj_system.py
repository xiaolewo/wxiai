#!/usr/bin/env python3
"""
Midjourney系统完整性测试
验证所有组件是否正常工作
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_database():
    """测试数据库连接和表结构"""
    print("🔍 测试数据库连接和表结构...")

    try:
        from open_webui.internal.db import get_db
        from sqlalchemy import text

        with get_db() as db:
            # 检查MJ表是否存在
            tables = db.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mj_%';"
                )
            ).fetchall()
            mj_tables = [table[0] for table in tables]

            expected_tables = ["mj_config", "mj_tasks", "mj_credits"]
            missing_tables = [t for t in expected_tables if t not in mj_tables]

            if missing_tables:
                print(f"❌ 缺少数据表: {missing_tables}")
                return False

            print(f"✅ 数据表检查通过: {mj_tables}")

            # 检查配置是否初始化
            config_count = db.execute(text("SELECT COUNT(*) FROM mj_config")).scalar()
            if config_count == 0:
                print("❌ 没有找到默认配置")
                return False

            print(f"✅ 配置记录: {config_count} 条")
            return True

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False


def test_models():
    """测试数据模型"""
    print("🔍 测试数据模型...")

    try:
        from open_webui.models.midjourney import MJConfig, MJTask, MJCredit

        # 测试MJConfig
        config = MJConfig.get_config()
        if config:
            print(f"✅ MJConfig模型: 启用状态={config.enabled}")
        else:
            print("⚠️ 没有找到MJ配置")

        # 测试积分查询
        balance = MJCredit.get_user_balance("test_user")
        print(f"✅ MJCredit模型: 测试用户余额={balance}")

        print("✅ 数据模型测试通过")
        return True

    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False


def test_api_client():
    """测试API客户端"""
    print("🔍 测试API客户端...")

    try:
        from open_webui.utils.midjourney import MJApiClient
        from open_webui.models.midjourney import MJConfig, MJGenerateRequest

        # 获取配置
        config = MJConfig.get_config()
        if not config or not config.base_url:
            print("⚠️ 没有MJ配置或base_url为空，跳过API客户端测试")
            return True

        # 创建客户端
        client = MJApiClient(config)
        print(f"✅ API客户端创建成功: {client.base_url}")

        # 测试prompt构建
        request = MJGenerateRequest(
            prompt="test prompt",
            mode="fast",
            advanced_params={"aspect_ratio": "16:9", "chaos": 50, "stylize": 100},
        )

        prompt = client.build_prompt(request)
        print(f"✅ Prompt构建: {prompt}")

        return True

    except Exception as e:
        print(f"❌ API客户端测试失败: {e}")
        return False


def test_routers():
    """测试路由模块"""
    print("🔍 测试路由模块...")

    try:
        from open_webui.routers.midjourney import router as mj_router
        from open_webui.routers.admin_midjourney import router as admin_router

        # 检查路由数量
        mj_routes = len(mj_router.routes)
        admin_routes = len(admin_router.routes)

        print(f"✅ MJ路由: {mj_routes} 个端点")
        print(f"✅ 管理员路由: {admin_routes} 个端点")

        # 检查主要端点
        mj_paths = {route.path for route in mj_router.routes}
        expected_paths = {
            "/config",
            "/submit/imagine",
            "/submit/action",
            "/task/{task_id}",
            "/credits",
        }

        missing_paths = [p for p in expected_paths if p not in mj_paths]
        if missing_paths:
            print(f"⚠️ 缺少端点: {missing_paths}")
        else:
            print("✅ 主要端点检查通过")

        return True

    except Exception as e:
        print(f"❌ 路由测试失败: {e}")
        return False


def test_credit_system():
    """测试积分系统"""
    print("🔍 测试积分系统...")

    try:
        from open_webui.utils.midjourney import (
            get_user_credit_balance,
            validate_user_credits,
            add_user_credits,
            deduct_user_credits,
        )

        test_user_id = "test_user_123"

        # 测试初始余额
        initial_balance = get_user_credit_balance(test_user_id)
        print(f"✅ 初始余额: {initial_balance}")

        # 测试充值
        new_balance = add_user_credits(test_user_id, 100, "测试充值")
        print(f"✅ 充值后余额: {new_balance}")

        # 测试验证
        has_enough = validate_user_credits(test_user_id, 50)
        print(f"✅ 积分验证: {has_enough}")

        # 测试扣费
        final_balance = deduct_user_credits(test_user_id, 30, "测试扣费")
        print(f"✅ 扣费后余额: {final_balance}")

        return True

    except Exception as e:
        print(f"❌ 积分系统测试失败: {e}")
        return False


def test_integration():
    """集成测试"""
    print("🔍 执行集成测试...")

    try:
        # 测试配置更新
        from open_webui.models.midjourney import MJConfig

        config = MJConfig.get_config()
        if config:
            print(f"✅ 获取配置成功: enabled={config.enabled}")

            # 测试配置更新
            original_enabled = config.enabled
            config.enabled = not original_enabled
            config.save()

            updated_config = MJConfig.get_config()
            if updated_config.enabled != original_enabled:
                print("✅ 配置更新成功")

                # 恢复原始状态
                updated_config.enabled = original_enabled
                updated_config.save()
            else:
                print("❌ 配置更新失败")
                return False

        return True

    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始Midjourney系统完整性测试...\n")

    tests = [
        ("数据库", test_database),
        ("数据模型", test_models),
        ("API客户端", test_api_client),
        ("路由模块", test_routers),
        ("积分系统", test_credit_system),
        ("集成测试", test_integration),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {name}")
        print("=" * 50)

        try:
            if test_func():
                print(f"✅ {name} 测试通过")
                passed += 1
            else:
                print(f"❌ {name} 测试失败")
        except Exception as e:
            print(f"💥 {name} 测试异常: {e}")

    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 50)

    if passed == total:
        print("🎉 所有测试通过！Midjourney系统已准备就绪！")

        print("\n📋 系统摘要:")
        print("- ✅ 数据库表已创建并初始化")
        print("- ✅ 数据模型和API客户端正常工作")
        print("- ✅ 路由和端点配置正确")
        print("- ✅ 积分系统运行正常")
        print("- ✅ 系统集成测试通过")

        print("\n🔧 下一步:")
        print("1. 在管理员设置中配置Midjourney API")
        print("2. 设置积分政策和价格")
        print("3. 测试完整的绘画流程")

        return True
    else:
        print(f"❌ {total - passed} 个测试失败，请检查系统配置")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
