#!/usr/bin/env python3
"""
测试文件上传功能
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from open_webui.services.file_manager import get_file_manager


async def test_file_upload():
    """测试文件上传服务"""
    try:
        print("🔧 测试文件管理器...")

        file_manager = get_file_manager()
        print(f"✅ 文件管理器初始化成功: {type(file_manager).__name__}")

        # 创建一个测试文件内容
        test_content = b"test image content"
        test_filename = "test_image.jpg"

        print("📤 测试保存文件...")

        success, message, file_record = await file_manager.save_generated_content(
            user_id="test_user",
            file_data=test_content,
            filename=test_filename,
            file_type="image",
            source_type="flux_test",
            metadata={
                "test": True,
                "original_filename": test_filename,
                "content_type": "image/jpeg",
                "file_size": len(test_content),
            },
        )

        if success:
            print(f"✅ 文件保存成功: {message}")
            if file_record:
                print(f"📁 文件记录ID: {file_record.id}")
                print(f"🌐 云存储URL: {file_record.cloud_url}")
            else:
                print("⚠️ 文件记录为空")
        else:
            print(f"❌ 文件保存失败: {message}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 开始文件上传测试...")
    asyncio.run(test_file_upload())
    print("🏁 测试完成")
