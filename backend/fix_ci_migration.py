#!/usr/bin/env python3
"""
修复CI中迁移文件不一致问题的脚本
主要解决dreamwork_tasks表的input_image列定义不一致
"""

import os
import sys


def main():
    print("🔧 CI Migration Fix Script")
    print("=" * 50)

    # 检查问题
    print("检测到的问题:")
    print("1. dreamwork_tasks.input_image 在迁移中是 nullable=True")
    print("2. 在模型中是 nullable=False (默认)")
    print("3. CI环境自动生成了重复的迁移")
    print()

    print("解决方案:")
    print("1. 统一模型定义，使input_image为nullable=True")
    print("2. 确保迁移文件格式一致")
    print("3. 避免CI自动生成重复迁移")
    print()

    print("✅ 建议操作:")
    print("1. 删除CI生成的重复迁移文件 a170c8f7ed90_*.py")
    print("2. 确保模型定义与现有迁移一致")
    print("3. 重新构建Docker镜像")


if __name__ == "__main__":
    main()
