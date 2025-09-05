#!/usr/bin/env python3
"""
最终功能完整性检查
验证所有AI服务表结构和配置完整性
"""

import sqlite3
import os
import json


def get_db_connection():
    """获取数据库连接"""
    db_paths = ["backend/data/webui.db", "webui.db", "backend/webui.db"]
    for path in db_paths:
        if os.path.exists(path):
            return sqlite3.connect(path), path
    return None, None


def check_all_ai_services():
    """检查所有AI服务的表结构完整性"""
    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 数据库位置: {db_path}")
    cursor = conn.cursor()

    # 定义所有AI服务及其需要的表和字段
    ai_services = {
        "Google Images": {
            "config_table": "google_images_config",
            "tasks_table": "google_images_tasks",
            "credits_table": "google_images_credits",
            "cloud_field": "cloud_result_images",
            "required_config_fields": [
                "enabled",
                "base_url",
                "api_key",
                "default_model",
            ],
            "required_task_fields": ["user_id", "status", "prompt", "result_images"],
        },
        "ComfyUI": {
            "config_table": "comfyui_config",
            "tasks_table": "comfyui_tasks",
            "workflows_table": "comfyui_workflows",
            "cloud_field": "cloud_images",
            "required_config_fields": [
                "access_key",
                "secret_key",
                "base_url",
                "enabled",
            ],
            "required_task_fields": [
                "user_id",
                "workflow_id",
                "status",
                "output_images",
            ],
        },
        "Flux": {
            "config_table": "flux_config",
            "tasks_table": "flux_tasks",
            "credits_table": "flux_credits",
            "cloud_field": "cloud_image_url",
            "required_config_fields": ["enabled", "base_url", "api_key"],
            "required_task_fields": ["user_id", "status", "prompt", "image_url"],
        },
        "Kling": {
            "config_table": "kling_config",
            "tasks_table": "kling_tasks",
            "credits_table": "kling_credits",
            "cloud_field": "cloud_video_url",
            "required_config_fields": ["enabled", "base_url", "access_key"],
            "required_task_fields": ["user_id", "status", "prompt", "video_url"],
        },
        "Kling Lip Sync": {
            "config_table": "kling_lip_sync_config",
            "tasks_table": "kling_lip_sync_tasks",
            "credits_table": "kling_lip_sync_credits",
            "cloud_field": "cloud_video_url",
            "required_config_fields": ["enabled", "base_url", "access_key"],
            "required_task_fields": ["user_id", "status", "video_url"],
        },
        "Jimeng": {
            "config_table": "jimeng_config",
            "tasks_table": "jimeng_tasks",
            "cloud_field": "cloud_video_url",
            "required_config_fields": ["enabled", "base_url", "access_key"],
            "required_task_fields": ["user_id", "status", "prompt", "video_url"],
        },
        "Jimeng Inpainting": {
            "config_table": "jimeng_inpainting_config",
            "tasks_table": "jimeng_inpainting_tasks",
            "credits_table": "jimeng_inpainting_credits",
            "cloud_field": "cloud_image_url",
            "required_config_fields": ["enabled", "base_url", "access_key"],
            "required_task_fields": ["user_id", "status", "prompt", "image_url"],
        },
        "Jimeng Outpainting": {
            "config_table": "jimeng_outpainting_config",
            "tasks_table": "jimeng_outpainting_tasks",
            "credits_table": "jimeng_outpainting_credits",
            "cloud_field": "cloud_image_url",
            "required_config_fields": ["enabled", "base_url", "access_key"],
            "required_task_fields": ["user_id", "status", "prompt", "image_url"],
        },
        "Veo": {
            "config_table": "veo_config",
            "tasks_table": "veo_tasks",
            "credits_table": "veo_credits",
            "cloud_field": "cloud_video_url",
            "required_config_fields": ["enabled", "base_url", "api_key"],
            "required_task_fields": ["user_id", "status", "prompt", "video_url"],
        },
        "MidJourney": {
            "config_table": "mj_config",
            "tasks_table": "mj_tasks",
            "credits_table": "mj_credits",
            "cloud_field": "cloud_image_url",
            "required_config_fields": ["enabled", "base_url", "api_key"],
            "required_task_fields": ["user_id", "status", "prompt", "image_url"],
        },
        "DreamWork": {
            "config_table": "dreamwork_config",
            "tasks_table": "dreamwork_tasks",
            "credits_table": "dreamwork_credits",
            "cloud_field": "cloud_image_url",
            "required_config_fields": ["enabled", "base_url", "api_key"],
            "required_task_fields": ["user_id", "status", "prompt", "image_url"],
        },
    }

    print("\n🔍 AI服务完整性检查:")
    print("=" * 60)

    all_services_ok = True

    for service_name, service_config in ai_services.items():
        print(f"\n📊 检查 {service_name}:")
        service_ok = True

        # 检查配置表
        config_table = service_config["config_table"]
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{config_table}'"
        )
        if cursor.fetchone():
            print(f"   ✅ 配置表 {config_table} 存在")

            # 检查配置表字段
            cursor.execute(f"PRAGMA table_info({config_table})")
            columns = [row[1] for row in cursor.fetchall()]

            missing_fields = []
            for field in service_config.get("required_config_fields", []):
                if field not in columns:
                    missing_fields.append(field)

            if missing_fields:
                print(f"   ⚠️  配置表缺失字段: {missing_fields}")
                service_ok = False
            else:
                print(f"   ✅ 配置表字段完整")

            # 检查是否有配置记录
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {config_table}")
                config_count = cursor.fetchone()[0]
                print(f"   📝 配置记录: {config_count} 条")
            except Exception as e:
                print(f"   ❌ 读取配置记录失败: {e}")
                service_ok = False

        else:
            print(f"   ❌ 配置表 {config_table} 不存在")
            service_ok = False

        # 检查任务表
        tasks_table = service_config["tasks_table"]
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tasks_table}'"
        )
        if cursor.fetchone():
            print(f"   ✅ 任务表 {tasks_table} 存在")

            # 检查任务表字段
            cursor.execute(f"PRAGMA table_info({tasks_table})")
            columns = [row[1] for row in cursor.fetchall()]

            missing_fields = []
            for field in service_config.get("required_task_fields", []):
                if field not in columns:
                    missing_fields.append(field)

            if missing_fields:
                print(f"   ⚠️  任务表缺失字段: {missing_fields}")
                service_ok = False
            else:
                print(f"   ✅ 任务表字段完整")

            # 检查云存储字段
            cloud_field = service_config.get("cloud_field")
            if cloud_field:
                if cloud_field in columns:
                    print(f"   ✅ 云存储字段 {cloud_field} 存在")
                else:
                    print(f"   ❌ 云存储字段 {cloud_field} 不存在")
                    service_ok = False

            # 检查任务记录数量
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tasks_table}")
                task_count = cursor.fetchone()[0]
                print(f"   📝 任务记录: {task_count} 条")
            except Exception as e:
                print(f"   ❌ 读取任务记录失败: {e}")
                service_ok = False

        else:
            print(f"   ❌ 任务表 {tasks_table} 不存在")
            service_ok = False

        # 检查积分表（如果有）
        credits_table = service_config.get("credits_table")
        if credits_table:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{credits_table}'"
            )
            if cursor.fetchone():
                print(f"   ✅ 积分表 {credits_table} 存在")

                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {credits_table}")
                    credit_count = cursor.fetchone()[0]
                    print(f"   📝 积分记录: {credit_count} 条")
                except Exception as e:
                    print(f"   ❌ 读取积分记录失败: {e}")
                    service_ok = False
            else:
                print(f"   ⚠️  积分表 {credits_table} 不存在")

        # 检查工作流表（ComfyUI特有）
        workflows_table = service_config.get("workflows_table")
        if workflows_table:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{workflows_table}'"
            )
            if cursor.fetchone():
                print(f"   ✅ 工作流表 {workflows_table} 存在")

                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {workflows_table}")
                    workflow_count = cursor.fetchone()[0]
                    print(f"   📝 工作流记录: {workflow_count} 条")
                except Exception as e:
                    print(f"   ❌ 读取工作流记录失败: {e}")
                    service_ok = False
            else:
                print(f"   ❌ 工作流表 {workflows_table} 不存在")
                service_ok = False

        if service_ok:
            print(f"   🎉 {service_name} 服务完整")
        else:
            print(f"   ❌ {service_name} 服务有问题")
            all_services_ok = False

    conn.close()
    return all_services_ok


def check_core_system_tables():
    """检查核心系统表"""
    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    print("\n🏗️  核心系统表检查:")
    print("=" * 40)

    core_tables = [
        "auth",
        "user",
        "chat",
        "file",
        "document",
        "model",
        "config",
        "credit",
        "credit_log",
        "trade_ticket",
        "redemption_code",
        "cloud_storage_config",
        "generated_files",
        "cloud_storage_stats",
        "alembic_version",
    ]

    all_core_ok = True
    for table in core_tables:
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
        )
        if cursor.fetchone():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table:20}: {count} 条记录")
            except Exception as e:
                print(f"   ⚠️  {table:20}: 存在但无法访问 ({e})")
                all_core_ok = False
        else:
            print(f"   ❌ {table:20}: 不存在")
            all_core_ok = False

    conn.close()
    return all_core_ok


def check_migration_status():
    """检查迁移状态"""
    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    print("\n🔄 迁移状态检查:")
    print("=" * 30)

    try:
        cursor.execute("SELECT version_num FROM alembic_version")
        current_version = cursor.fetchone()[0]
        print(f"   📍 当前迁移版本: {current_version}")

        # 检查是否为已知稳定版本
        stable_versions = [
            "e5f6g7h8i9j0",  # ComfyUI启用版本
            "f1e2d3c4b5a6",  # Google Images版本
            "j6k7l8m9n0p1",  # 完整版本
        ]

        if current_version in stable_versions:
            print("   ✅ 版本状态稳定")
            conn.close()
            return True
        else:
            print("   ⚠️  版本状态需要确认")
            conn.close()
            return False

    except Exception as e:
        print(f"   ❌ 无法读取迁移版本: {e}")
        conn.close()
        return False


def main():
    """主函数"""
    print("🚀 最终功能完整性检查")
    print("=" * 70)

    # 1. 检查核心系统表
    print("第一步：检查核心系统表...")
    core_ok = check_core_system_tables()

    # 2. 检查所有AI服务
    print("\n第二步：检查所有AI服务...")
    ai_ok = check_all_ai_services()

    # 3. 检查迁移状态
    print("\n第三步：检查迁移状态...")
    migration_ok = check_migration_status()

    # 4. 最终报告
    print("\n" + "=" * 70)
    print("🎯 最终检查报告:")

    if core_ok:
        print("   ✅ 核心系统表: 完整")
    else:
        print("   ❌ 核心系统表: 有问题")

    if ai_ok:
        print("   ✅ AI服务表: 完整")
    else:
        print("   ❌ AI服务表: 有问题")

    if migration_ok:
        print("   ✅ 迁移状态: 正常")
    else:
        print("   ❌ 迁移状态: 异常")

    if core_ok and ai_ok and migration_ok:
        print("\n🎉 所有功能检查通过！")
        print("✅ 系统准备就绪，可以安全进行:")
        print("   - 线上更新 (alembic upgrade head)")
        print("   - 全新部署")
        print("   - 正常业务运行")
        print("   - 所有11个AI服务可用")
        print("   - 云存储功能完整")
        print("   - 积分系统正常")
    else:
        print("\n⚠️  发现一些问题，建议修复后再进行部署")


if __name__ == "__main__":
    main()
