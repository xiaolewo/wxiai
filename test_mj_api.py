#!/usr/bin/env python3
"""测试MJ API的脚本"""
import requests
import json


# 测试API响应
def test_task_status():
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
            print(f"   图片URL: {image_url[:50] if image_url else 'None'}")

            # 测试API调用
            try:
                print(f"\n🔍 测试API调用...")
                url = f"http://localhost:8080/api/v1/midjourney/task/{task_id}"
                response = requests.get(url)

                print(f"API状态码: {response.status_code}")

                if response.status_code == 401:
                    print("❌ 需要认证，这就是问题所在！")
                    print("前端需要传递正确的认证token")
                elif response.status_code == 200:
                    data = response.json()
                    print(f"✅ API返回数据:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(f"❌ API错误: {response.text}")

            except Exception as e:
                print(f"❌ API调用失败: {e}")
        else:
            print("❌ 数据库中没有任务")


if __name__ == "__main__":
    test_task_status()
