#!/usr/bin/env python3
"""
敏感配置备份和恢复脚本
"""

import sqlite3
import json
import os
from datetime import datetime


def backup_sensitive_configs():
    """备份敏感配置"""
    print("🔐 备份敏感配置...")

    db_paths = [
        "data/webui.db",
        "backend/data/webui.db",
        "webui.db",
        "backend/webui.db",
    ]
    conn = None

    for path in db_paths:
        if os.path.exists(path):
            conn = sqlite3.connect(path)
            break

    if not conn:
        print("❌ 无法连接到数据库")
        return None

    cursor = conn.cursor()
    backup_data = {}

    # 备份各种配置表
    config_tables = [
        "comfyui_config",
        "google_images_config",
        "veo_config",
        "cloud_storage_config",
    ]

    for table in config_tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()

            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]

            table_data = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                table_data.append(row_dict)

            backup_data[table] = table_data
            print(f"   ✅ 备份 {table}: {len(table_data)} 条记录")

        except Exception as e:
            print(f"   ⚠️ 跳过 {table}: {e}")

    conn.close()

    # 保存备份文件
    backup_filename = (
        f"sensitive_configs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(backup_filename, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    print(f"✅ 配置备份已保存: {backup_filename}")
    return backup_filename


def restore_sensitive_configs(backup_file):
    """恢复敏感配置"""
    print(f"🔄 从 {backup_file} 恢复配置...")

    if not os.path.exists(backup_file):
        print(f"❌ 备份文件不存在: {backup_file}")
        return False

    with open(backup_file, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    db_paths = [
        "data/webui.db",
        "backend/data/webui.db",
        "webui.db",
        "backend/webui.db",
    ]
    conn = None

    for path in db_paths:
        if os.path.exists(path):
            conn = sqlite3.connect(path)
            break

    if not conn:
        print("❌ 无法连接到数据库")
        return False

    cursor = conn.cursor()

    for table_name, table_data in backup_data.items():
        try:
            # 检查表是否存在
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if not cursor.fetchone():
                print(f"   ⚠️ 表 {table_name} 不存在，跳过")
                continue

            # 清空现有数据
            cursor.execute(f"DELETE FROM {table_name}")

            # 插入备份数据
            for row_data in table_data:
                columns = list(row_data.keys())
                values = list(row_data.values())
                placeholders = ",".join(["?" for _ in values])

                sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                cursor.execute(sql, values)

            print(f"   ✅ 恢复 {table_name}: {len(table_data)} 条记录")

        except Exception as e:
            print(f"   ❌ 恢复 {table_name} 失败: {e}")

    conn.commit()
    conn.close()
    print("✅ 配置恢复完成")
    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        if len(sys.argv) > 2:
            restore_sensitive_configs(sys.argv[2])
        else:
            print("❌ 请指定备份文件: python config_backup.py restore backup_file.json")
    else:
        backup_sensitive_configs()
