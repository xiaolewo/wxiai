#!/usr/bin/env python3
"""
即梦涂抹消除功能部署脚本

此脚本用于安全部署即梦涂抹消除功能到生产环境
包含完整的验证、备份、迁移和测试流程

运行方式：
python deploy_jimeng_inpainting.py --mode=check     # 只检查不部署
python deploy_jimeng_inpainting.py --mode=deploy    # 执行完整部署
python deploy_jimeng_inpainting.py --mode=rollback  # 回滚到部署前状态
"""

import os
import sys
import shutil
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目路径到sys.path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))

import logging
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("deploy_jimeng_inpainting.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class JimengInpaintingDeployer:
    def __init__(self):
        self.db_path = current_dir / "data" / "webui.db"
        self.backup_path = (
            current_dir
            / "data"
            / f"webui.db.jimeng_deploy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.alembic_cfg_path = current_dir / "open_webui" / "alembic.ini"
        self.expected_migration_id = "f2g3h4i5j6k7"

    def log_step(self, step: str, status: str = "进行中"):
        """记录部署步骤"""
        logger.info(f"🔸 [{step}] {status}")

    def check_prerequisites(self) -> bool:
        """检查部署前置条件"""
        self.log_step("检查前置条件", "开始")

        # 1. 检查数据库文件存在
        if not self.db_path.exists():
            logger.error(f"❌ 数据库文件不存在: {self.db_path}")
            return False
        self.log_step("数据库文件", "✅ 存在")

        # 2. 检查迁移文件存在
        migration_file = (
            current_dir
            / "open_webui"
            / "migrations"
            / "versions"
            / f"{self.expected_migration_id}_add_jimeng_inpainting_tables.py"
        )
        if not migration_file.exists():
            logger.error(f"❌ 迁移文件不存在: {migration_file}")
            return False
        self.log_step("迁移文件", "✅ 存在")

        # 3. 检查alembic配置
        if not self.alembic_cfg_path.exists():
            logger.error(f"❌ Alembic配置文件不存在: {self.alembic_cfg_path}")
            return False
        self.log_step("Alembic配置", "✅ 存在")

        # 4. 检查数据库连接
        try:
            engine = create_engine(f"sqlite:///{self.db_path}")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.log_step("数据库连接", "✅ 正常")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

        self.log_step("前置条件检查", "✅ 完成")
        return True

    def backup_database(self) -> bool:
        """备份数据库"""
        self.log_step("数据库备份", "开始")

        try:
            shutil.copy2(self.db_path, self.backup_path)

            # 验证备份文件
            if self.backup_path.exists() and self.backup_path.stat().st_size > 0:
                logger.info(f"✅ 数据库已备份到: {self.backup_path}")
                return True
            else:
                logger.error("❌ 备份文件创建失败或为空")
                return False

        except Exception as e:
            logger.error(f"❌ 数据库备份失败: {e}")
            return False

    def check_migration_status(self) -> tuple[bool, str]:
        """检查迁移状态"""
        self.log_step("检查迁移状态", "开始")

        try:
            # 设置Alembic配置
            alembic_cfg = Config(str(self.alembic_cfg_path))
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{self.db_path}")

            # 获取当前数据库版本
            script = ScriptDirectory.from_config(alembic_cfg)

            def get_current_revision():
                engine = create_engine(f"sqlite:///{self.db_path}")
                with engine.connect() as connection:
                    context = EnvironmentContext(config=alembic_cfg, script=script)
                    context.configure(connection=connection)
                    return context.get_current_revision()

            current_rev = get_current_revision()
            head_rev = script.get_current_head()

            logger.info(f"📊 当前数据库版本: {current_rev}")
            logger.info(f"📊 最新迁移版本: {head_rev}")

            # 检查是否已经应用了即梦涂抹消除迁移
            if current_rev == self.expected_migration_id:
                return True, "即梦涂抹消除迁移已应用"
            elif (
                current_rev
                and script.get_revision(current_rev)
                and self.expected_migration_id
                in [r.revision for r in script.walk_revisions()]
            ):
                # 检查是否在迁移历史中
                revisions = list(script.walk_revisions(current_rev, "base"))
                applied_revs = [r.revision for r in revisions]
                if self.expected_migration_id in applied_revs:
                    return True, "即梦涂抹消除迁移已在历史中"

            return False, "需要应用即梦涂抹消除迁移"

        except Exception as e:
            logger.error(f"❌ 检查迁移状态失败: {e}")
            return False, f"检查失败: {e}"

    def verify_table_structure(self) -> bool:
        """验证表结构"""
        self.log_step("验证表结构", "开始")

        expected_tables = {
            "jimeng_inpainting_config": [
                "id",
                "enabled",
                "base_url",
                "api_key",
                "credits_cost",
                "default_steps",
                "default_strength",
                "default_scale",
                "default_quality",
                "created_at",
                "updated_at",
            ],
            "jimeng_inpainting_tasks": [
                "id",
                "user_id",
                "status",
                "progress",
                "original_image_url",
                "mask_image_url",
                "steps",
                "strength",
                "scale",
                "seed",
                "dilate_size",
                "quality",
                "result_image_url",
                "cloud_image_url",
                "credits_cost",
                "fail_reason",
                "properties",
                "created_at",
                "updated_at",
                "finish_time",
            ],
            "jimeng_inpainting_credits": [
                "id",
                "user_id",
                "task_id",
                "credit_amount",
                "operation_type",
                "created_at",
            ],
        }

        try:
            engine = create_engine(f"sqlite:///{self.db_path}")

            for table_name, expected_columns in expected_tables.items():
                with engine.connect() as conn:
                    # 检查表是否存在
                    result = conn.execute(
                        text(
                            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                        )
                    )
                    if not result.fetchone():
                        logger.error(f"❌ 表不存在: {table_name}")
                        return False

                    # 检查列是否存在
                    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                    existing_columns = [row[1] for row in result.fetchall()]

                    for expected_col in expected_columns:
                        if expected_col not in existing_columns:
                            logger.error(f"❌ 表 {table_name} 缺少列: {expected_col}")
                            return False

                    logger.info(f"✅ 表 {table_name} 结构正确")

            self.log_step("表结构验证", "✅ 完成")
            return True

        except Exception as e:
            logger.error(f"❌ 验证表结构失败: {e}")
            return False

    def apply_migration(self) -> bool:
        """应用迁移"""
        self.log_step("应用迁移", "开始")

        try:
            # 设置Alembic配置
            alembic_cfg = Config(str(self.alembic_cfg_path))
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{self.db_path}")

            # 应用迁移到head
            command.upgrade(alembic_cfg, "head")

            self.log_step("迁移应用", "✅ 完成")
            return True

        except Exception as e:
            logger.error(f"❌ 应用迁移失败: {e}")
            return False

    def verify_default_data(self) -> bool:
        """验证默认数据"""
        self.log_step("验证默认数据", "开始")

        try:
            engine = create_engine(f"sqlite:///{self.db_path}")

            with engine.connect() as conn:
                # 检查默认配置是否存在
                result = conn.execute(
                    text("SELECT COUNT(*) FROM jimeng_inpainting_config")
                )
                config_count = result.fetchone()[0]

                if config_count == 0:
                    logger.error("❌ 没有找到默认配置记录")
                    return False
                elif config_count > 1:
                    logger.warning(f"⚠️  发现多条配置记录: {config_count}")
                else:
                    logger.info("✅ 默认配置存在")

                # 验证默认配置内容
                result = conn.execute(
                    text(
                        "SELECT base_url, credits_cost, default_steps FROM jimeng_inpainting_config LIMIT 1"
                    )
                )
                config = result.fetchone()

                if config:
                    base_url, credits_cost, default_steps = config
                    logger.info(
                        f"📊 默认配置: base_url={base_url}, credits_cost={credits_cost}, default_steps={default_steps}"
                    )

                    if not base_url or credits_cost != 30 or default_steps != 30:
                        logger.warning("⚠️  默认配置值可能不正确")

            self.log_step("默认数据验证", "✅ 完成")
            return True

        except Exception as e:
            logger.error(f"❌ 验证默认数据失败: {e}")
            return False

    def check_indexes(self) -> bool:
        """检查索引"""
        self.log_step("检查索引", "开始")

        expected_indexes = [
            "idx_jimeng_inpainting_user_id",
            "idx_jimeng_inpainting_status",
            "idx_jimeng_inpainting_created",
            "idx_jimeng_inpainting_credit_user",
            "idx_jimeng_inpainting_credit_task",
        ]

        try:
            engine = create_engine(f"sqlite:///{self.db_path}")

            with engine.connect() as conn:
                for index_name in expected_indexes:
                    result = conn.execute(
                        text(
                            f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"
                        )
                    )
                    if result.fetchone():
                        logger.info(f"✅ 索引存在: {index_name}")
                    else:
                        logger.warning(f"⚠️  索引不存在: {index_name}")

            self.log_step("索引检查", "✅ 完成")
            return True

        except Exception as e:
            logger.error(f"❌ 检查索引失败: {e}")
            return False

    def run_deployment_test(self) -> bool:
        """运行部署测试"""
        self.log_step("部署测试", "开始")

        try:
            # 测试基本CRUD操作
            from open_webui.models.jimeng_inpainting import JimengInpaintingTable

            table = JimengInpaintingTable()

            # 测试获取配置
            config = table.get_config()
            if not config:
                logger.error("❌ 无法获取配置")
                return False
            logger.info(f"✅ 配置获取测试通过: enabled={config.enabled}")

            # 测试创建任务（模拟数据）
            test_task_data = {
                "user_id": "test_user_deploy",
                "original_image_url": "https://example.com/test.jpg",
                "mask_image_url": "https://example.com/mask.jpg",
                "steps": 30,
                "strength": 0.8,
                "scale": 7.0,
                "seed": 0,
                "dilate_size": 15,
                "quality": "M",
                "credits_cost": 30,
            }

            task = table.create_task(test_task_data)
            if not task:
                logger.error("❌ 测试任务创建失败")
                return False
            logger.info(f"✅ 任务创建测试通过: {task.id}")

            # 测试获取任务
            retrieved_task = table.get_task_by_id(task.id)
            if not retrieved_task or retrieved_task.user_id != "test_user_deploy":
                logger.error("❌ 测试任务获取失败")
                return False
            logger.info("✅ 任务获取测试通过")

            # 清理测试数据
            table.delete_task(task.id, "test_user_deploy")
            logger.info("✅ 测试数据已清理")

            self.log_step("部署测试", "✅ 完成")
            return True

        except Exception as e:
            logger.error(f"❌ 部署测试失败: {e}")
            return False

    def rollback_database(self) -> bool:
        """回滚数据库"""
        self.log_step("数据库回滚", "开始")

        if not self.backup_path.exists():
            logger.error(f"❌ 备份文件不存在: {self.backup_path}")
            return False

        try:
            # 停止可能的数据库连接（如果有）
            # 替换数据库文件
            shutil.copy2(self.backup_path, self.db_path)

            logger.info(f"✅ 数据库已回滚到: {self.backup_path}")
            self.log_step("数据库回滚", "✅ 完成")
            return True

        except Exception as e:
            logger.error(f"❌ 数据库回滚失败: {e}")
            return False

    def generate_report(self, success: bool, operations: list) -> dict:
        """生成部署报告"""
        report = {
            "deployment_time": datetime.now().isoformat(),
            "success": success,
            "database_path": str(self.db_path),
            "backup_path": str(self.backup_path) if self.backup_path.exists() else None,
            "operations": operations,
            "migration_id": self.expected_migration_id,
        }

        report_file = (
            current_dir
            / f"jimeng_inpainting_deploy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        try:
            import json

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"📊 部署报告已生成: {report_file}")
        except Exception as e:
            logger.error(f"❌ 生成部署报告失败: {e}")

        return report


def main():
    parser = argparse.ArgumentParser(description="即梦涂抹消除功能部署脚本")
    parser.add_argument(
        "--mode",
        choices=["check", "deploy", "rollback"],
        default="check",
        help="运行模式",
    )
    parser.add_argument("--backup-path", help="回滚时指定备份文件路径")

    args = parser.parse_args()

    deployer = JimengInpaintingDeployer()

    if args.backup_path and args.mode == "rollback":
        deployer.backup_path = Path(args.backup_path)

    operations = []
    success = False

    try:
        if args.mode == "check":
            logger.info("🔍 === 即梦涂抹消除功能部署检查 ===")

            operations.append("前置条件检查")
            if not deployer.check_prerequisites():
                raise Exception("前置条件检查失败")

            operations.append("迁移状态检查")
            migration_applied, migration_msg = deployer.check_migration_status()
            logger.info(f"📊 迁移状态: {migration_msg}")

            if migration_applied:
                operations.append("表结构验证")
                if not deployer.verify_table_structure():
                    raise Exception("表结构验证失败")

                operations.append("默认数据验证")
                if not deployer.verify_default_data():
                    raise Exception("默认数据验证失败")

                operations.append("索引检查")
                deployer.check_indexes()

                operations.append("部署测试")
                if not deployer.run_deployment_test():
                    raise Exception("部署测试失败")

                logger.info("✅ === 检查完成，系统已就绪 ===")
            else:
                logger.info("⚠️  === 需要执行部署 ===")
                logger.info("💡 运行: python deploy_jimeng_inpainting.py --mode=deploy")

            success = True

        elif args.mode == "deploy":
            logger.info("🚀 === 即梦涂抹消除功能部署开始 ===")

            operations.append("前置条件检查")
            if not deployer.check_prerequisites():
                raise Exception("前置条件检查失败")

            operations.append("数据库备份")
            if not deployer.backup_database():
                raise Exception("数据库备份失败")

            operations.append("迁移检查")
            migration_applied, migration_msg = deployer.check_migration_status()

            if not migration_applied:
                operations.append("应用迁移")
                if not deployer.apply_migration():
                    raise Exception("应用迁移失败")
            else:
                logger.info(f"ℹ️  {migration_msg}")

            operations.append("表结构验证")
            if not deployer.verify_table_structure():
                raise Exception("表结构验证失败")

            operations.append("默认数据验证")
            if not deployer.verify_default_data():
                raise Exception("默认数据验证失败")

            operations.append("索引检查")
            deployer.check_indexes()

            operations.append("部署测试")
            if not deployer.run_deployment_test():
                raise Exception("部署测试失败")

            logger.info("🎉 === 部署成功完成 ===")
            logger.info(f"💾 数据库备份: {deployer.backup_path}")
            logger.info(
                "🔄 如需回滚: python deploy_jimeng_inpainting.py --mode=rollback"
            )

            success = True

        elif args.mode == "rollback":
            logger.info("↩️  === 即梦涂抹消除功能回滚开始 ===")

            operations.append("数据库回滚")
            if not deployer.rollback_database():
                raise Exception("数据库回滚失败")

            logger.info("✅ === 回滚成功完成 ===")
            success = True

    except Exception as e:
        logger.error(f"❌ 操作失败: {e}")
        success = False

        if args.mode == "deploy" and "backup_database" in operations:
            logger.info("🔄 自动回滚...")
            try:
                deployer.rollback_database()
                logger.info("✅ 自动回滚完成")
            except Exception as rollback_error:
                logger.error(f"❌ 自动回滚失败: {rollback_error}")

    finally:
        # 生成部署报告
        report = deployer.generate_report(success, operations)

        if success:
            logger.info("🎯 === 操作成功完成 ===")
        else:
            logger.error("💥 === 操作失败 ===")
            sys.exit(1)


if __name__ == "__main__":
    main()
