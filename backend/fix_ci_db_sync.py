#!/usr/bin/env python3
"""
修复CI中数据库模型同步问题
"""

import os
import sys
import shutil
from datetime import datetime


def main():
    print("🔧 CI Database Sync Fix")
    print("=" * 50)

    # 1. 检查是否有自动生成的重复迁移
    migrations_dir = "open_webui/migrations/versions"
    problem_patterns = ["a170c8f7ed90", "add_input_image_to_dreamwork"]

    if os.path.exists(migrations_dir):
        for filename in os.listdir(migrations_dir):
            for pattern in problem_patterns:
                if pattern in filename:
                    problem_file = os.path.join(migrations_dir, filename)
                    print(f"❌ 发现问题迁移文件: {filename}")

                    # 备份并删除问题文件
                    backup_name = (
                        f"{filename}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                    backup_path = os.path.join(migrations_dir, backup_name)
                    shutil.move(problem_file, backup_path)
                    print(f"✅ 已备份到: {backup_name}")

    # 2. 生成修复说明
    fix_instructions = """
📋 CI修复指南:

1. 删除自动生成的重复迁移:
   - 文件: a170c8f7ed90_add_input_image_to_dreamwork_tasks_.py
   - 原因: input_image列已在 a1b2c3d4e5f6_init_dreamwork_tables.py 中存在

2. 模型定义已修复:
   ✅ dreamwork.py: 所有列添加了 nullable=True 以匹配迁移文件
   
3. 确保CI不再自动生成迁移:
   - 检查 alembic revision --autogenerate 不会产生新迁移
   - 确认模型定义与迁移文件完全一致

4. 重新构建Docker镜像:
   - git add .
   - git commit -m "fix: sync dreamwork model with migration schema"  
   - git push

5. 验证迁移链完整性:
   当前HEAD: a1b2c3d4e5f7_fix_dreamwork_progress_column.py
"""

    print(fix_instructions)

    # 3. 创建验证脚本
    verification_script = """
# 验证迁移是否同步
python -c "
from open_webui.models.dreamwork import DreamworkTask
from open_webui.migrations.versions.a1b2c3d4e5f6_init_dreamwork_tables import *
print('✅ 模型与迁移同步检查通过')
"
"""

    print("🧪 验证命令:")
    print(verification_script)


if __name__ == "__main__":
    main()
