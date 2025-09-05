#!/usr/bin/env python3
"""
修复veo_config表结构，使其与模型期望的列结构匹配
"""

import sqlite3
import os
import sys
import json
from datetime import datetime


def get_db_connection():
    """获取数据库连接"""
    db_paths = [
        "data/webui.db",
        "backend/data/webui.db",
        "webui.db",
        "backend/webui.db",
    ]
    for path in db_paths:
        if os.path.exists(path):
            return sqlite3.connect(path), path
    return None, None


def fix_veo_table_structure():
    """修复veo相关表的结构"""
    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 使用数据库: {db_path}")
    cursor = conn.cursor()

    try:
        print("🔧 修复veo_config表结构...")

        # 1. 检查当前表结构
        cursor.execute("PRAGMA table_info(veo_config)")
        current_columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"📊 当前表列: {list(current_columns.keys())}")

        # 2. 期望的表结构（基于模型定义）
        expected_columns = {
            "id": "INTEGER",
            "enabled": "BOOLEAN",
            "base_url": "VARCHAR(500)",
            "api_key": "TEXT",
            "model_credits_config": "JSON",  # 缺失的关键列
            "default_model": "VARCHAR(50)",
            "default_enhance_prompt": "BOOLEAN",
            "max_concurrent_tasks": "INTEGER",
            "task_timeout": "INTEGER",
            "query_interval": "INTEGER",  # 缺失的关键列
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
        }

        # 3. 添加缺失的列
        missing_columns = []
        for col_name, col_type in expected_columns.items():
            if col_name not in current_columns:
                missing_columns.append((col_name, col_type))

        if missing_columns:
            print(f"📊 需要添加 {len(missing_columns)} 个缺失的列:")

            for col_name, col_type in missing_columns:
                try:
                    # 添加列的SQL
                    if col_type == "JSON":
                        sql = f"ALTER TABLE veo_config ADD COLUMN {col_name} JSON"
                    elif col_type == "BOOLEAN":
                        if col_name == "default_enhance_prompt":
                            sql = f"ALTER TABLE veo_config ADD COLUMN {col_name} BOOLEAN NOT NULL DEFAULT 1"
                        else:
                            sql = f"ALTER TABLE veo_config ADD COLUMN {col_name} BOOLEAN NOT NULL DEFAULT 0"
                    elif col_type == "INTEGER":
                        if col_name == "query_interval":
                            sql = f"ALTER TABLE veo_config ADD COLUMN {col_name} INTEGER NOT NULL DEFAULT 15000"
                        else:
                            sql = (
                                f"ALTER TABLE veo_config ADD COLUMN {col_name} INTEGER"
                            )
                    elif col_type == "VARCHAR(50)":
                        if col_name == "default_model":
                            sql = f"ALTER TABLE veo_config ADD COLUMN {col_name} VARCHAR(50) NOT NULL DEFAULT 'veo3'"
                        else:
                            sql = f"ALTER TABLE veo_config ADD COLUMN {col_name} VARCHAR(50)"
                    else:
                        sql = f"ALTER TABLE veo_config ADD COLUMN {col_name} {col_type}"

                    cursor.execute(sql)
                    print(f"   ✅ 添加列: {col_name} ({col_type})")

                except Exception as e:
                    print(f"   ❌ 添加列 {col_name} 失败: {e}")
        else:
            print("✅ 所有必要的列都存在")

        # 4. 检查是否已有配置记录
        cursor.execute("SELECT COUNT(*) FROM veo_config WHERE id = 1")
        count = cursor.fetchone()[0]

        if count == 0:
            print("📊 插入默认配置...")
            default_model_credits = {
                "veo3": 100,
                "veo3-fast": 80,
                "veo3-pro": 150,
                "veo3-pro-frames": 200,
                "veo2": 90,
                "veo2-fast": 70,
                "veo2-fast-frames": 120,
                "veo2-fast-components": 160,
                "veo2-pro": 140,
                "veo3-fast-frames": 90,
            }

            cursor.execute(
                """
                INSERT INTO veo_config 
                (id, enabled, base_url, api_key, model_credits_config, default_model, 
                 default_enhance_prompt, max_concurrent_tasks, task_timeout, query_interval,
                 created_at) 
                VALUES 
                (1, 0, 'https://api.veoai.com', '', ?, 'veo3', 1, 3, 900000, 15000, ?)
            """,
                (json.dumps(default_model_credits), datetime.now()),
            )
            print("   ✅ 默认配置插入成功")
        else:
            # 5. 更新现有记录，确保有model_credits_config数据
            cursor.execute("SELECT model_credits_config FROM veo_config WHERE id = 1")
            result = cursor.fetchone()
            if not result or not result[0]:
                print("📊 更新model_credits_config...")
                default_model_credits = {
                    "veo3": 100,
                    "veo3-fast": 80,
                    "veo3-pro": 150,
                    "veo3-pro-frames": 200,
                    "veo2": 90,
                    "veo2-fast": 70,
                    "veo2-fast-frames": 120,
                    "veo2-fast-components": 160,
                    "veo2-pro": 140,
                    "veo3-fast-frames": 90,
                }
                cursor.execute(
                    "UPDATE veo_config SET model_credits_config = ? WHERE id = 1",
                    (json.dumps(default_model_credits),),
                )
                print("   ✅ model_credits_config更新成功")

            print("✅ 配置记录已存在")

        # 6. 修复其他veo表结构 - veo_tasks表需要正确的列
        print("\n🔧 检查veo_tasks表结构...")
        cursor.execute("PRAGMA table_info(veo_tasks)")
        task_columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"📊 veo_tasks当前列: {list(task_columns.keys())}")

        # 期望的veo_tasks列（基于模型）
        expected_task_columns = {
            "external_task_id": "VARCHAR(100)",
            "progress": "VARCHAR(10)",
            "fail_reason": "TEXT",
        }

        for col_name, col_type in expected_task_columns.items():
            if col_name not in task_columns:
                try:
                    if col_name == "progress":
                        sql = f"ALTER TABLE veo_tasks ADD COLUMN {col_name} VARCHAR(10) DEFAULT '0%'"
                    else:
                        sql = f"ALTER TABLE veo_tasks ADD COLUMN {col_name} {col_type}"

                    cursor.execute(sql)
                    print(f"   ✅ 添加veo_tasks列: {col_name}")
                except Exception as e:
                    print(f"   ❌ 添加列 {col_name} 失败: {e}")

        # 7. 提交更改
        conn.commit()

        print("\n✅ veo表结构修复完成！")

        # 8. 验证修复结果
        print("\n🔍 验证修复结果...")
        cursor.execute("PRAGMA table_info(veo_config)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 最终veo_config列: {final_columns}")

        cursor.execute(
            "SELECT id, enabled, model_credits_config FROM veo_config WHERE id = 1"
        )
        config_result = cursor.fetchone()
        if config_result:
            print(
                f"📊 配置记录: id={config_result[0]}, enabled={config_result[1]}, model_credits_config存在={config_result[2] is not None}"
            )

        return True

    except Exception as e:
        print(f"❌ 修复表结构时发生错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def test_veo_config_access():
    """测试veo配置是否能正常访问"""
    conn, db_path = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        print("\n🔍 测试配置访问...")
        # 模拟模型查询
        cursor.execute(
            """
            SELECT id, enabled, base_url, api_key, model_credits_config, 
                   default_model, default_enhance_prompt, max_concurrent_tasks, 
                   task_timeout, query_interval, created_at, updated_at 
            FROM veo_config 
            WHERE id = ? LIMIT ? OFFSET ?
        """,
            (1, 1, 0),
        )

        result = cursor.fetchone()
        if result:
            print("✅ veo_config查询成功")
            return True
        else:
            print("❌ veo_config查询返回空结果")
            return False

    except Exception as e:
        print(f"❌ 测试配置访问失败: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 开始修复veo表结构...")
    print("=" * 60)

    if fix_veo_table_structure():
        if test_veo_config_access():
            print("\n🎉 veo表结构修复成功！现在应该可以正常访问Veo配置了")
            print("\n🚀 建议操作：")
            print("1. 重新测试 Veo API 路由")
            print("2. 检查管理员配置页面")
            print("3. 测试 Veo 用户配置获取")
        else:
            print("❌ 表结构修复后仍无法访问配置")
    else:
        print("❌ 表结构修复失败")
        sys.exit(1)
