#!/usr/bin/env python3
"""
检查云存储配置状态
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from open_webui.internal.db import get_db
from open_webui.models.cloud_storage import CloudStorageConfig, GeneratedFile


def check_cloud_storage_config():
    """检查云存储配置"""
    print("\n🔍 检查云存储配置状态...")
    print("-" * 50)

    with get_db() as db:
        # 检查cloud_storage_config表
        config = db.query(CloudStorageConfig).first()

        if not config:
            print("❌ 云存储配置不存在（cloud_storage_config表为空）")
            print("   需要在管理员面板配置腾讯云COS")
            return False

        print(f"✅ 找到云存储配置:")
        print(f"   - Provider: {config.provider}")
        print(f"   - Enabled: {config.enabled}")
        print(f"   - Region: {config.region}")
        print(f"   - Bucket: {config.bucket}")
        print(
            f"   - SecretId: {'***' + config.secret_id[-4:] if config.secret_id else 'None'}"
        )
        print(f"   - Domain: {config.domain or '默认域名'}")

        if not config.enabled:
            print("\n⚠️ 云存储未启用！需要在管理员面板开启")
            return False

        if not all([config.secret_id, config.secret_key, config.region, config.bucket]):
            print("\n⚠️ 云存储配置不完整！缺少必要参数")
            return False

        # 检查generated_files表
        print("\n📊 文件上传统计:")
        total_files = db.query(GeneratedFile).count()
        uploaded_files = (
            db.query(GeneratedFile).filter(GeneratedFile.status == "uploaded").count()
        )
        failed_files = (
            db.query(GeneratedFile).filter(GeneratedFile.status == "failed").count()
        )
        pending_files = (
            db.query(GeneratedFile).filter(GeneratedFile.status == "pending").count()
        )

        print(f"   - 总文件数: {total_files}")
        print(f"   - 已上传: {uploaded_files}")
        print(f"   - 失败: {failed_files}")
        print(f"   - 待处理: {pending_files}")

        # 查看最近的失败记录
        if failed_files > 0:
            recent_failures = (
                db.query(GeneratedFile)
                .filter(GeneratedFile.status == "failed")
                .order_by(GeneratedFile.created_at.desc())
                .limit(3)
                .all()
            )

            print("\n❌ 最近失败的上传:")
            for f in recent_failures:
                print(f"   - {f.filename}: {f.error_message}")

        return config.enabled


if __name__ == "__main__":
    try:
        is_enabled = check_cloud_storage_config()

        if is_enabled:
            print("\n✅ 云存储配置正常")
            print("\n💡 如果图片仍未上传，可能原因：")
            print("   1. 后端服务需要重启以应用代码修改")
            print("   2. 腾讯云COS SDK未正确安装")
            print("   3. 腾讯云认证信息错误")
            print("   4. 网络连接问题")
        else:
            print("\n❌ 云存储未配置或未启用")
            print("\n📝 解决方案：")
            print("   1. 登录管理员面板")
            print("   2. 进入 Settings -> 云存储")
            print("   3. 配置腾讯云COS参数")
            print("   4. 启用云存储功能")

    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback

        traceback.print_exc()
