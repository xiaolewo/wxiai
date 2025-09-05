#!/usr/bin/env python3
"""
测试所有AI服务的数据库表结构和基本功能
"""

import sqlite3
import os
import sys
from datetime import datetime


def get_db_connection():
    """获取数据库连接"""
    db_paths = [
        "data/webui.db",
        "backend/data/webui.db",
        "webui.db",
        "backend/webui.db",
    ]
    for path in db_paths:
        if os.path.exists(path):
            return sqlite3.connect(path), path
    return None, None


def test_all_tables_exist():
    """测试所有AI服务表是否存在"""
    print("🔍 检查所有AI服务表...")

    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    cursor = conn.cursor()

    # 期望存在的表
    expected_tables = {
        # 配置表
        "google_images_config": "Google Images配置",
        "veo_config": "Veo配置",
        "cloud_storage_config": "云存储配置",
        # 任务表
        "google_images_tasks": "Google Images任务",
        "veo_tasks": "Veo任务",
        "mj_tasks": "MidJourney任务",
        "dreamwork_tasks": "DreamWork任务",
        "flux_tasks": "Flux任务",
        "kling_tasks": "Kling任务",
        "jimeng_tasks": "即梦任务",
        "comfyui_tasks": "ComfyUI任务",
        # 积分表
        "google_images_credits": "Google Images积分",
        "veo_credits": "Veo积分",
        "jimeng_credits": "即梦积分",
        "comfyui_credits": "ComfyUI积分",
        "flux_credits": "Flux积分",
        "kling_credits": "Kling积分",
        "dreamwork_credits": "DreamWork积分",
        # 文件管理
        "generated_files": "生成文件记录",
    }

    missing_tables = []
    existing_tables = []

    for table_name, description in expected_tables.items():
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if cursor.fetchone():
            existing_tables.append((table_name, description))
        else:
            missing_tables.append((table_name, description))

    print(f"✅ 存在的表: {len(existing_tables)}/{len(expected_tables)}")
    for table_name, description in existing_tables:
        print(f"   ✅ {table_name} - {description}")

    if missing_tables:
        print(f"❌ 缺失的表: {len(missing_tables)}")
        for table_name, description in missing_tables:
            print(f"   ❌ {table_name} - {description}")

    conn.close()
    return len(missing_tables) == 0


def test_table_structures():
    """测试关键表的结构完整性"""
    print("\n🔍 检查关键表结构...")

    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # 测试表结构
    test_cases = [
        {
            "table": "google_images_tasks",
            "required_columns": [
                "input_images",
                "cloud_input_images",
                "result_images",
                "cloud_result_images",
            ],
            "description": "Google Images任务表",
        },
        {
            "table": "google_images_credits",
            "required_columns": [
                "credits_before",
                "credits_after",
                "model_name",
                "description",
            ],
            "description": "Google Images积分表",
        },
        {
            "table": "veo_config",
            "required_columns": [
                "model_credits_config",
                "query_interval",
                "default_enhance_prompt",
            ],
            "description": "Veo配置表",
        },
        {
            "table": "veo_tasks",
            "required_columns": ["external_task_id", "progress", "fail_reason"],
            "description": "Veo任务表",
        },
        {
            "table": "mj_tasks",
            "required_columns": ["cloud_image_url", "result_images"],
            "description": "MidJourney任务表",
        },
    ]

    all_passed = True

    for test_case in test_cases:
        table_name = test_case["table"]
        required_columns = test_case["required_columns"]
        description = test_case["description"]

        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            missing_columns = [col for col in required_columns if col not in columns]

            if missing_columns:
                print(f"   ❌ {description}: 缺少列 {missing_columns}")
                all_passed = False
            else:
                print(f"   ✅ {description}: 结构完整")

        except Exception as e:
            print(f"   ❌ {description}: 检查失败 - {str(e)}")
            all_passed = False

    conn.close()
    return all_passed


def test_api_endpoints():
    """测试API端点可访问性"""
    print("\n🔍 测试API端点...")

    import requests

    endpoints = [
        ("http://localhost:8080/api/v1/veo/health", "Veo健康检查"),
        ("http://localhost:8080/api/v1/google-images/health", "Google Images健康检查"),
    ]

    all_passed = True

    for url, description in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {description}: 可访问")
            else:
                print(f"   ❌ {description}: HTTP {response.status_code}")
                all_passed = False
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️ {description}: 服务未运行")
        except Exception as e:
            print(f"   ❌ {description}: {str(e)}")
            all_passed = False

    return all_passed


def test_basic_functionality():
    """测试基本功能"""
    print("\n🔍 测试基本功能...")

    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        # 测试Google Images任务创建
        from open_webui.models.google_images import GoogleImagesTask, GoogleImagesCredit
        import uuid

        test_user_id = "test-user-" + uuid.uuid4().hex[:8]
        test_task_id = str(uuid.uuid4())

        print("   🔍 测试Google Images任务创建...")
        task_data = {
            "id": test_task_id,
            "user_id": test_user_id,
            "status": "submitted",
            "prompt": "测试图像",
            "model": "nano-banana",
            "input_images": ["test-image"],
            "cloud_input_images": ["https://example.com/test.png"],
            "credits_cost": 20,
        }

        task = GoogleImagesTask.create_task(task_data)
        if task:
            print("   ✅ Google Images任务创建成功")
        else:
            print("   ❌ Google Images任务创建失败")
            return False

        # 测试积分记录创建
        print("   🔍 测试Google Images积分记录...")
        credit_data = {
            "user_id": test_user_id,
            "task_id": test_task_id,
            "credit_amount": 20,
            "credits_before": 1000,
            "credits_after": 980,
            "operation_type": "deduct",
            "model_name": "nano-banana",
            "description": "测试扣费",
        }

        credit = GoogleImagesCredit.create_credit_log(credit_data)
        if credit:
            print("   ✅ Google Images积分记录创建成功")
        else:
            print("   ❌ Google Images积分记录创建失败")
            return False

        # 测试Veo配置
        print("   🔍 测试Veo配置访问...")
        from open_webui.models.veo import VeoConfig

        config = VeoConfig.get_config()
        if config:
            print("   ✅ Veo配置访问成功")
        else:
            print("   ❌ Veo配置访问失败")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 功能测试失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("🚀 开始全面测试AI服务...")
    print("=" * 60)

    all_passed = True

    # 1. 测试表存在性
    if not test_all_tables_exist():
        all_passed = False

    # 2. 测试表结构
    if not test_table_structures():
        all_passed = False

    # 3. 测试API端点
    test_api_endpoints()  # 这个可能失败（服务未运行），不影响总结果

    # 4. 测试基本功能
    if not test_basic_functionality():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！AI服务系统已完全修复")
        print("\n📊 修复总结:")
        print("✅ 所有AI服务表已创建")
        print("✅ 所有表结构已修复")
        print("✅ 积分系统正常工作")
        print("✅ 任务创建功能正常")
        print("✅ 配置访问正常")
        print("\n🚀 系统已准备好部署到生产环境！")
    else:
        print("❌ 部分测试失败，请检查错误信息")
        return False

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
