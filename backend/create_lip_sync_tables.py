#!/usr/bin/env python3
"""
手动创建可灵对口型数据表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from open_webui.internal.db import engine, get_db
from open_webui.models.kling_lip_sync import Base as LipSyncBase


def create_tables():
    """创建可灵对口型相关表"""
    print("🎤 开始创建可灵对口型数据表...")

    try:
        # 创建表
        LipSyncBase.metadata.create_all(bind=engine)
        print("✅ 可灵对口型数据表创建成功!")

        # 验证表是否创建成功
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        lip_sync_tables = [t for t in tables if "lip_sync" in t]
        print(f"📊 创建的表: {lip_sync_tables}")

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False

    return True


if __name__ == "__main__":
    create_tables()
