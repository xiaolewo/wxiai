#!/usr/bin/env python3
"""
可灵对口型功能简洁测试执行器
运行验证脚本并提供快速反馈
"""

import subprocess
import sys
from pathlib import Path


def main():
    """主函数"""
    print("🎭 可灵对口型功能 - 快速测试")
    print("=" * 50)

    project_root = Path(__file__).parent

    # 运行验证脚本
    print("🔍 运行功能验证...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "backend/scripts/validate_kling_lip_sync.py"),
            ],
            capture_output=False,
        )

        if result.returncode == 0:
            print("\n✅ 验证完成")
        else:
            print("\n❌ 验证发现问题，请检查上面的输出")

    except FileNotFoundError:
        print("❌ 验证脚本不存在")
        print("请确保文件存在: backend/scripts/validate_kling_lip_sync.py")

    print("\n💡 快速部署步骤:")
    print("1. cd backend && alembic upgrade head")
    print("2. 重启应用服务")
    print("3. 访问 /admin/settings/kling-lip-sync 配置")
    print("4. 访问 /lip-sync 测试功能")


if __name__ == "__main__":
    main()
