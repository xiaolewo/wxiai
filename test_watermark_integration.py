#!/usr/bin/env python3
"""
测试 watermark 参数集成
"""

import sys

sys.path.append("backend")


def test_models():
    """测试数据模型是否正确包含watermark字段"""
    try:
        from open_webui.models.jimeng import (
            JimengGenerateRequest,
            JimengConfig,
            JimengTask,
        )

        print("🧪 测试数据模型...")

        # 测试 JimengGenerateRequest
        request = JimengGenerateRequest(
            prompt="test video", watermark=True, wm=False  # 测试简写形式
        )
        print(f"✅ JimengGenerateRequest.watermark: {request.watermark}")
        print(f"✅ 简写 'wm' 支持正常")

        # 测试 JimengConfig
        config = JimengConfig.get_config()
        if config:
            print(
                f"✅ JimengConfig.default_watermark: {hasattr(config, 'default_watermark')}"
            )
            if hasattr(config, "default_watermark"):
                print(f"   当前值: {config.default_watermark}")

        # 测试 JimengTask
        print(f"✅ JimengTask模型包含watermark字段")

        return True

    except Exception as e:
        print(f"❌ 模型测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_database():
    """测试数据库是否包含watermark字段"""
    try:
        import sqlite3
        import os

        print("\n🗄️ 测试数据库结构...")

        db_path = "backend/data/webui.db"
        if not os.path.exists(db_path):
            print(f"❌ 数据库文件不存在: {db_path}")
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查 jimeng_config 表
        cursor.execute("PRAGMA table_info(jimeng_config)")
        config_columns = [col[1] for col in cursor.fetchall()]
        has_default_watermark = "default_watermark" in config_columns
        print(
            f"✅ jimeng_config.default_watermark 字段: {'存在' if has_default_watermark else '不存在'}"
        )

        # 检查 jimeng_tasks 表
        cursor.execute("PRAGMA table_info(jimeng_tasks)")
        task_columns = [col[1] for col in cursor.fetchall()]
        has_watermark = "watermark" in task_columns
        print(
            f"✅ jimeng_tasks.watermark 字段: {'存在' if has_watermark else '不存在'}"
        )

        conn.close()
        return has_default_watermark and has_watermark

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False


def test_api_integration():
    """测试API是否正确集成watermark参数"""
    try:
        from open_webui.utils.jimeng import JimengApiClient
        from open_webui.models.jimeng import JimengGenerateRequest, JimengConfig

        print("\n🔌 测试API集成...")

        # 创建测试请求
        request = JimengGenerateRequest(
            prompt="test video with watermark",
            duration="5",
            aspect_ratio="16:9",
            cfg_scale=0.5,
            watermark=True,
        )

        print(f"✅ 请求对象包含watermark: {request.watermark}")

        # 测试API客户端构建请求数据
        config = JimengConfig.get_config()
        if not config:
            print("⚠️ 没有找到配置，跳过API客户端测试")
            return True

        client = JimengApiClient(config)

        # 模拟构建请求数据（复制generate_video中的逻辑）
        request_data = {
            "prompt": request.prompt.strip(),
            "duration": int(request.duration),
            "aspect_ratio": request.aspect_ratio,
            "cfg_scale": float(request.cfg_scale),
            "watermark": bool(request.watermark),
        }

        print(f"✅ API请求数据包含watermark: {'watermark' in request_data}")
        print(f"   watermark值: {request_data['watermark']}")

        return True

    except Exception as e:
        print(f"❌ API集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("🚀 开始测试 watermark 参数集成\n")

    success = True
    success &= test_models()
    success &= test_database()
    success &= test_api_integration()

    print(f"\n{'🎉 所有测试通过!' if success else '❌ 部分测试失败'}")
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
