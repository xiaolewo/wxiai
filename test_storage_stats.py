#!/usr/bin/env python3
"""
测试增强的云存储统计功能
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import asyncio
from open_webui.services.file_manager import get_file_manager


async def test_storage_stats():
    """测试存储统计功能"""
    print("\n📊 测试增强的云存储统计功能...")
    print("=" * 80)

    file_manager = get_file_manager()
    stats = await file_manager.get_storage_stats()

    # 美化输出
    print("\n" + json.dumps(stats, indent=2, ensure_ascii=False))

    # 验证数据结构
    print("\n✅ 数据结构验证:")
    required_fields = [
        "summary",
        "type_distribution",
        "source_distribution",
        "top_users",
        "daily_trend",
        "recent_failures",
    ]

    for field in required_fields:
        if field in stats:
            print(f"  ✓ {field}: 存在")
        else:
            print(f"  ✗ {field}: 缺失")

    # 显示摘要
    if "summary" in stats:
        summary = stats["summary"]
        print(f"\n📈 存储摘要:")
        print(f"  - 总文件数: {summary['total_files']}")
        print(f"  - 已上传: {summary['uploaded_files']}")
        print(f"  - 待处理: {summary['pending_files']}")
        print(f"  - 失败: {summary['failed_files']}")
        print(f"  - 总大小: {summary['total_size_formatted']}")
        print(f"  - 成功率: {summary['success_rate']}%")

    # 显示分布
    if "source_distribution" in stats and stats["source_distribution"]:
        print(f"\n🎯 按来源分布:")
        for source, data in stats["source_distribution"].items():
            print(f"  - {source}: {data['count']} 个文件, {data['size_formatted']}")

    if "type_distribution" in stats and stats["type_distribution"]:
        print(f"\n📁 按类型分布:")
        for file_type, data in stats["type_distribution"].items():
            print(f"  - {file_type}: {data['count']} 个文件, {data['size_formatted']}")

    # 显示TOP用户
    if "top_users" in stats and stats["top_users"]:
        print(f"\n👥 TOP用户:")
        for i, user in enumerate(stats["top_users"][:5], 1):
            print(
                f"  {i}. {user['user_id']}: {user['count']} 个文件, {user['size_formatted']}"
            )

    # 显示趋势
    if "daily_trend" in stats and stats["daily_trend"]:
        print(f"\n📅 最近7天趋势:")
        for day in stats["daily_trend"]:
            print(f"  - {day['date']}: {day['count']} 个文件, {day['size_formatted']}")

    # 显示失败记录
    if "recent_failures" in stats and stats["recent_failures"]:
        print(f"\n❌ 最近失败:")
        for failure in stats["recent_failures"]:
            print(
                f"  - {failure['filename']} ({failure['source_type']}): {failure['error']}"
            )
            print(f"    时间: {failure['created_at']}")


if __name__ == "__main__":
    try:
        asyncio.run(test_storage_stats())
        print("\n✅ 测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
