#!/usr/bin/env python3
"""测试MJ API的脚本 - 带认证"""
import requests
import json
import jwt
from datetime import datetime, timedelta


def create_test_token():
    """创建测试用的JWT token"""
    # 这些值需要与后端配置一致
    SECRET_KEY = "t0p-s3cr3t"  # 默认密钥，生产环境应该更改

    payload = {
        "id": "55821824-1d51-4f2f-8e0b-cd73dbb04b93",  # 用户ID
        "email": "admin@163.com",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def test_task_status_with_auth():
    # 从数据库获取任务ID
    import sqlite3

    db_path = "/Users/liuqingliang/Desktop/openwebui/open-webui/backend/data/webui.db"

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT id, status, progress, image_url FROM mj_tasks ORDER BY created_at DESC LIMIT 1"
        )
        task = cursor.fetchone()

        if task:
            task_id, status, progress, image_url = task
            print(f"📊 数据库中的任务:")
            print(f"   ID: {task_id}")
            print(f"   状态: {status}")
            print(f"   进度: {progress}")
            print(f"   图片: {bool(image_url)}")

            # 创建认证token
            try:
                token = create_test_token()
                print(f"\n🔑 生成测试token: {token[:50]}...")

                # 测试API调用
                url = f"http://localhost:8080/api/v1/midjourney/task/{task_id}"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }

                print(f"\n🔍 测试API调用...")
                response = requests.get(url, headers=headers)

                print(f"API状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ API返回数据:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(f"❌ API错误: {response.text}")

            except Exception as e:
                print(f"❌ 测试失败: {e}")
                import traceback

                traceback.print_exc()
        else:
            print("❌ 数据库中没有任务")


if __name__ == "__main__":
    test_task_status_with_auth()
