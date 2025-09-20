#!/usr/bin/env python3
"""
验证数据库迁移相关文件是否正确创建
"""

import os
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"

print(f"项目根目录: {PROJECT_ROOT}")
print(f"后端目录: {BACKEND_DIR}")
print(f"脚本目录: {SCRIPTS_DIR}")

# 需要验证的文件列表
REQUIRED_FILES = [
    # 配置文件
    PROJECT_ROOT / ".env.mysql",
    # 脚本文件
    SCRIPTS_DIR / "init_mysql_db.py",
    SCRIPTS_DIR / "cleanup_sqlite.py",
    SCRIPTS_DIR / "migrate_data_sqlite_to_mysql.py",
    SCRIPTS_DIR / "test_mysql_connection.py",
    # 启动脚本
    BACKEND_DIR / "start_mysql.sh",
    # 文档文件
    PROJECT_ROOT / "MYSQL_CONFIGURATION.md",
    PROJECT_ROOT / "MIGRATION_TO_MYSQL.md",
    PROJECT_ROOT / "DATABASE_MIGRATION_GUIDE.md",
    # Docker配置
    PROJECT_ROOT / "docker-compose.mysql.yaml",
    PROJECT_ROOT / "mysql" / "conf.d" / "mysql.cnf",
]


def check_files():
    """检查所有必需的文件是否存在"""
    missing_files = []
    existing_files = []

    for file_path in REQUIRED_FILES:
        if file_path.exists():
            existing_files.append(str(file_path.relative_to(PROJECT_ROOT)))
            print(f"✅ {file_path.relative_to(PROJECT_ROOT)}")
        else:
            missing_files.append(str(file_path.relative_to(PROJECT_ROOT)))
            print(f"❌ {file_path.relative_to(PROJECT_ROOT)}")

    print(f"\n总共检查 {len(REQUIRED_FILES)} 个文件")
    print(f"存在 {len(existing_files)} 个文件")
    print(f"缺失 {len(missing_files)} 个文件")

    if missing_files:
        print("\n缺失的文件:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("\n🎉 所有文件都已正确创建!")
        return True


def check_permissions():
    """检查脚本文件是否有执行权限"""
    script_files = [
        SCRIPTS_DIR / "init_mysql_db.py",
        SCRIPTS_DIR / "cleanup_sqlite.py",
        SCRIPTS_DIR / "migrate_data_sqlite_to_mysql.py",
        SCRIPTS_DIR / "test_mysql_connection.py",
        BACKEND_DIR / "start_mysql.sh",
    ]

    no_permission_files = []

    for file_path in script_files:
        if file_path.exists():
            if os.access(file_path, os.X_OK):
                print(f"✅ {file_path.relative_to(PROJECT_ROOT)} (可执行)")
            else:
                print(f"❌ {file_path.relative_to(PROJECT_ROOT)} (无执行权限)")
                no_permission_files.append(str(file_path.relative_to(PROJECT_ROOT)))

    if no_permission_files:
        print(f"\n以下文件无执行权限:")
        for file in no_permission_files:
            print(f"  - {file}")
        return False
    else:
        print(f"\n🎉 所有脚本文件都有执行权限!")
        return True


def main():
    """主函数"""
    print("🚀 验证数据库迁移相关文件...")
    print("=" * 50)

    files_ok = check_files()
    print("\n" + "=" * 50)

    permissions_ok = check_permissions()
    print("\n" + "=" * 50)

    if files_ok and permissions_ok:
        print("\n🎉 所有验证通过!")
        return 0
    else:
        print("\n❌ 部分验证失败!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
