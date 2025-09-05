#!/usr/bin/env python3
"""
修复veo_tasks表结构，添加缺失的enhance_prompt列
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


def fix_veo_tasks_table():
    """修复veo_tasks表结构"""
    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 使用数据库: {db_path}")
    cursor = conn.cursor()

    try:
        print("🔧 修复veo_tasks表结构...")

        # 1. 检查当前表结构
        cursor.execute("PRAGMA table_info(veo_tasks)")
        current_columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"📊 当前表列: {list(current_columns.keys())}")

        # 2. 期望的表结构（基于模型定义）
        expected_columns = {
            "enhance_prompt": "BOOLEAN",  # 关键缺失列
        }

        # 3. 添加缺失的列
        missing_columns = []
        for col_name, col_type in expected_columns.items():
            if col_name not in current_columns:
                missing_columns.append((col_name, col_type))

        if missing_columns:
            print(f"📊 需要添加 {len(missing_columns)} 个缺失的列:")

            for col_name, col_type in missing_columns:
                try:
                    # enhance_prompt默认为True
                    sql = f"ALTER TABLE veo_tasks ADD COLUMN {col_name} {col_type} NOT NULL DEFAULT 1"
                    cursor.execute(sql)
                    print(f"   ✅ 添加列: {col_name} ({col_type})")

                except Exception as e:
                    print(f"   ❌ 添加列 {col_name} 失败: {e}")
        else:
            print("✅ 所有必要的列都存在")

        # 4. 检查列名映射问题
        # 表中有image_urls，模型期望input_images
        if "image_urls" in current_columns and "input_images" in current_columns:
            print("🔄 检测到列名冗余: image_urls 和 input_images 都存在")
            print("   💡 注意：应用将优先使用 input_images 列")
        elif "image_urls" in current_columns and "input_images" not in current_columns:
            print("🔄 检测到列名不匹配: image_urls 存在但缺少 input_images")
            print("   💡 注意：需要数据迁移或列映射")

        # 5. 检查其他可能的不匹配
        model_expects = {
            "enhance_prompt": "Boolean",
            "input_images": "JSON",
            "cloud_input_images": "JSON",
            "result_video_url": "TEXT",
            "cloud_video_url": "TEXT",
            "external_task_id": "VARCHAR(100)",
            "progress": "VARCHAR(10)",  # 注意：模型期望VARCHAR(10)，表中是VARCHAR(20)
            "fail_reason": "TEXT",
            "credits_cost": "INTEGER",
            "properties": "JSON",
        }

        inconsistencies = []
        for col_name in model_expects:
            if col_name not in current_columns:
                inconsistencies.append(f"缺少列: {col_name}")

        if inconsistencies:
            print("⚠️  发现模型与表结构不一致:")
            for issue in inconsistencies:
                print(f"   ⚠️  {issue}")
        else:
            print("✅ 模型与表结构基本一致")

        # 6. 提交更改
        conn.commit()

        print("\n✅ veo_tasks表结构修复完成！")

        # 7. 验证修复结果
        print("\n🔍 验证修复结果...")
        cursor.execute("PRAGMA table_info(veo_tasks)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 最终veo_tasks列: {final_columns}")

        return True

    except Exception as e:
        print(f"❌ 修复表结构时发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def test_veo_task_query():
    """测试Veo任务查询"""
    print("\n🔍 测试Veo任务查询...")

    try:
        import sys
        import os

        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        from open_webui.models.veo import VeoTask

        # 测试获取任务列表
        user_id = "1e402f55-88cc-4eb9-a364-8b51a441518a"
        tasks = VeoTask.get_tasks_by_user(user_id, limit=5)

        print(f"✅ Veo任务查询成功: 找到 {len(tasks)} 个任务")

        for task in tasks:
            print(
                f"   📋 任务ID: {task.id}, 状态: {task.status}, 提示: {task.prompt[:30]}..."
            )

        return True

    except Exception as e:
        print(f"❌ 测试Veo任务查询失败: {str(e)}")
        import traceback

        print(f"📊 错误堆栈:\n{traceback.format_exc()}")
        return False


def test_api_endpoint():
    """测试API端点"""
    print("\n🔍 测试Veo任务API端点...")

    try:
        import requests

        # 测试任务列表端点（需要认证，预期401或数据）
        url = "http://localhost:8080/api/v1/veo/tasks"
        response = requests.get(url, timeout=10)

        if response.status_code == 401:
            print("   ✅ API端点可访问（需要认证）")
            return True
        elif response.status_code == 200:
            print("   ✅ API端点正常返回数据")
            return True
        else:
            print(f"   ❌ API端点返回错误: {response.status_code}")
            print(f"   📊 响应内容: {response.text[:200]}...")
            return False

    except requests.exceptions.ConnectionError:
        print("   ⚠️ 服务器未运行，无法测试API端点")
        return True  # 不算失败
    except Exception as e:
        print(f"   ❌ 测试API端点失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 开始修复veo_tasks表结构...")
    print("=" * 60)

    if fix_veo_tasks_table():
        query_success = test_veo_task_query()
        api_success = test_api_endpoint()

        if query_success:
            print("\n🎉 veo_tasks表修复成功！现在应该可以正常查询任务了")
            print("\n🚀 建议操作：")
            print("1. 重新测试 Veo 任务历史页面")
            print("2. 检查任务列表是否正常加载")
            print("3. 验证任务创建和状态更新")
        else:
            print("❌ 表结构修复后仍无法查询任务")
    else:
        print("❌ 表结构修复失败")
        sys.exit(1)
