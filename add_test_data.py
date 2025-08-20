#!/usr/bin/env python3
"""
添加测试数据到generated_files表
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from datetime import datetime, timedelta
import random
import uuid
from open_webui.internal.db import get_db
from open_webui.models.cloud_storage import GeneratedFile


def add_test_data():
    """添加测试数据"""
    print("\n🔧 添加测试数据到generated_files表...")

    with get_db() as db:
        # 生成一些测试数据
        sources = ["midjourney", "dreamwork", "kling", "jimeng"]
        types = ["image", "video"]
        users = ["user_001", "user_002", "user_003", "admin"]

        count = 0
        for i in range(20):
            # 随机生成数据
            source = random.choice(sources)
            file_type = (
                "video" if source in ["kling", "jimeng"] else random.choice(types)
            )
            user_id = random.choice(users)
            status = random.choices(
                ["uploaded", "failed", "pending"], weights=[70, 10, 20]
            )[0]

            # 随机日期（最近7天内）
            days_ago = random.randint(0, 7)
            created_at = datetime.now() - timedelta(
                days=days_ago, hours=random.randint(0, 23)
            )

            # 随机文件大小
            if file_type == "video":
                file_size = random.randint(10_000_000, 100_000_000)  # 10MB-100MB
            else:
                file_size = random.randint(100_000, 5_000_000)  # 100KB-5MB

            # 创建记录
            file = GeneratedFile(
                id=str(uuid.uuid4()),
                user_id=user_id,
                filename=f"test_{source}_{i}.{'mp4' if file_type == 'video' else 'jpg'}",
                original_filename=f"original_{i}.{'mp4' if file_type == 'video' else 'jpg'}",
                file_type=file_type,
                mime_type=f"{file_type}/{'mp4' if file_type == 'video' else 'jpeg'}",
                file_size=file_size if status == "uploaded" else None,
                storage_provider="tencent-cos",
                cloud_url=(
                    f"https://test-cos.myqcloud.com/test/{uuid.uuid4()}.{'mp4' if file_type == 'video' else 'jpg'}"
                    if status == "uploaded"
                    else None
                ),
                cloud_path=(
                    f"generated/{file_type}s/{created_at.strftime('%Y/%m/%d')}/test_{uuid.uuid4()}"
                    if status == "uploaded"
                    else None
                ),
                source_type=source,
                source_task_id=f"task_{uuid.uuid4()}",
                status=status,
                error_message="测试错误: 网络连接失败" if status == "failed" else None,
                created_at=created_at,
                updated_at=created_at,
            )

            db.add(file)
            count += 1

        db.commit()
        print(f"✅ 成功添加 {count} 条测试数据")


if __name__ == "__main__":
    try:
        add_test_data()
    except Exception as e:
        print(f"❌ 添加测试数据失败: {e}")
        import traceback

        traceback.print_exc()
