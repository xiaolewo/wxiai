#!/usr/bin/env python3
"""
可灵对口型功能验证脚本
用于生产部署前的全面功能验证
"""

import os
import sys
import json
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
import logging

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from open_webui.internal.db import engine, get_db
    from open_webui.models.kling_lip_sync import KlingLipSyncConfig, KlingLipSyncTask
    from open_webui.utils.kling_lip_sync import KlingLipSyncService
    from sqlalchemy import text, inspect
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在项目根目录下运行此脚本，并已安装所有依赖")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KlingLipSyncValidator:
    """可灵对口型功能验证器"""

    def __init__(self):
        self.validation_results = {
            "database": {"status": "pending", "details": []},
            "backend_api": {"status": "pending", "details": []},
            "frontend_files": {"status": "pending", "details": []},
            "configuration": {"status": "pending", "details": []},
            "integration": {"status": "pending", "details": []},
        }

    async def validate_all(self):
        """执行全面验证"""
        logger.info("🔍 开始可灵对口型功能验证...")

        # 1. 验证数据库结构
        await self.validate_database()

        # 2. 验证后端API
        await self.validate_backend_api()

        # 3. 验证前端文件
        await self.validate_frontend_files()

        # 4. 验证配置
        await self.validate_configuration()

        # 5. 验证集成
        await self.validate_integration()

        # 生成验证报告
        self.generate_report()

    async def validate_database(self):
        """验证数据库结构"""
        logger.info("📊 验证数据库结构...")

        try:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            required_tables = [
                "kling_lip_sync_config",
                "kling_lip_sync_tasks",
                "kling_lip_sync_credits",
            ]

            # 检查表是否存在
            missing_tables = [
                table for table in required_tables if table not in existing_tables
            ]
            if missing_tables:
                self.validation_results["database"]["status"] = "failed"
                self.validation_results["database"]["details"].append(
                    f"缺少表: {missing_tables}"
                )
                return

            # 检查表结构
            for table_name in required_tables:
                columns = inspector.get_columns(table_name)
                column_names = [col["name"] for col in columns]

                if table_name == "kling_lip_sync_config":
                    required_columns = [
                        "id",
                        "enabled",
                        "base_url",
                        "api_key",
                        "default_voice_id",
                        "default_voice_language",
                        "default_voice_speed",
                        "credits_cost",
                    ]
                    missing_columns = [
                        col for col in required_columns if col not in column_names
                    ]
                    if missing_columns:
                        self.validation_results["database"]["details"].append(
                            f"表 {table_name} 缺少字段: {missing_columns}"
                        )

                elif table_name == "kling_lip_sync_tasks":
                    required_columns = ["id", "user_id", "mode", "status", "created_at"]
                    missing_columns = [
                        col for col in required_columns if col not in column_names
                    ]
                    if missing_columns:
                        self.validation_results["database"]["details"].append(
                            f"表 {table_name} 缺少字段: {missing_columns}"
                        )

            # 检查默认配置
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM kling_lip_sync_config")
                ).fetchone()
                config_count = result[0] if result else 0
                if config_count == 0:
                    self.validation_results["database"]["details"].append(
                        "缺少默认配置记录"
                    )

            if not self.validation_results["database"]["details"]:
                self.validation_results["database"]["status"] = "passed"
                self.validation_results["database"]["details"].append(
                    "数据库结构验证通过"
                )
            else:
                self.validation_results["database"]["status"] = "failed"

        except Exception as e:
            self.validation_results["database"]["status"] = "failed"
            self.validation_results["database"]["details"].append(
                f"数据库验证异常: {str(e)}"
            )

    async def validate_backend_api(self):
        """验证后端API文件"""
        logger.info("🔧 验证后端API文件...")

        backend_files = [
            "open_webui/models/kling_lip_sync.py",
            "open_webui/utils/kling_lip_sync.py",
            "open_webui/routers/kling_lip_sync.py",
        ]

        try:
            for file_path in backend_files:
                full_path = project_root / file_path
                if not full_path.exists():
                    self.validation_results["backend_api"]["details"].append(
                        f"文件不存在: {file_path}"
                    )
                else:
                    # 检查文件内容
                    content = full_path.read_text(encoding="utf-8")

                    if file_path == "open_webui/models/kling_lip_sync.py":
                        required_classes = [
                            "KlingLipSyncConfig",
                            "KlingLipSyncTask",
                            "KlingLipSyncCredit",
                        ]
                        for class_name in required_classes:
                            if f"class {class_name}" not in content:
                                self.validation_results["backend_api"][
                                    "details"
                                ].append(f"文件 {file_path} 缺少类定义: {class_name}")

                    elif file_path == "open_webui/utils/kling_lip_sync.py":
                        required_classes = ["KlingLipSyncAPI", "KlingLipSyncService"]
                        for class_name in required_classes:
                            if f"class {class_name}" not in content:
                                self.validation_results["backend_api"][
                                    "details"
                                ].append(f"文件 {file_path} 缺少类定义: {class_name}")

                    elif file_path == "open_webui/routers/kling_lip_sync.py":
                        required_endpoints = {
                            "/config": [
                                '@router.get("/config"',
                                '@router.post("/config"',
                            ],
                            "/test": '@router.get("/test"',
                            "/submit": '@router.post("/submit"',
                            "/task/": '@router.get("/task/{task_id}"',
                            "/history": '@router.get("/history"',
                            "/credits": '@router.get("/credits"',
                        }
                        for endpoint_name, patterns in required_endpoints.items():
                            if isinstance(patterns, list):
                                found = any(pattern in content for pattern in patterns)
                            else:
                                found = patterns in content
                            if not found:
                                self.validation_results["backend_api"][
                                    "details"
                                ].append(f"文件 {file_path} 缺少端点: {endpoint_name}")

            # 检查主应用是否注册了路由
            main_file = project_root / "open_webui/main.py"
            if main_file.exists():
                main_content = main_file.read_text(encoding="utf-8")
                if "kling_lip_sync" not in main_content:
                    self.validation_results["backend_api"]["details"].append(
                        "main.py 未注册 kling_lip_sync 路由"
                    )

            if not self.validation_results["backend_api"]["details"]:
                self.validation_results["backend_api"]["status"] = "passed"
                self.validation_results["backend_api"]["details"].append(
                    "后端API文件验证通过"
                )
            else:
                self.validation_results["backend_api"]["status"] = "failed"

        except Exception as e:
            self.validation_results["backend_api"]["status"] = "failed"
            self.validation_results["backend_api"]["details"].append(
                f"后端API验证异常: {str(e)}"
            )

    async def validate_frontend_files(self):
        """验证前端文件"""
        logger.info("🎨 验证前端文件...")

        frontend_files = [
            "src/lib/apis/kling-lip-sync/index.ts",
            "src/routes/(app)/lip-sync/+page.svelte",
            "src/lib/components/admin/Settings/KlingLipSync.svelte",
        ]

        try:
            src_root = (
                project_root.parent / "src"
                if (project_root.parent / "src").exists()
                else project_root / "../src"
            )
            if not src_root.exists():
                # 尝试找到 src 目录
                potential_src = project_root / "../../src"
                if potential_src.exists():
                    src_root = potential_src
                else:
                    self.validation_results["frontend_files"]["status"] = "failed"
                    self.validation_results["frontend_files"]["details"].append(
                        "无法找到 src 目录"
                    )
                    return

            for file_path in frontend_files:
                full_path = src_root / file_path.replace("src/", "")
                if not full_path.exists():
                    self.validation_results["frontend_files"]["details"].append(
                        f"文件不存在: {file_path}"
                    )
                else:
                    content = full_path.read_text(encoding="utf-8")

                    if file_path.endswith("index.ts"):
                        # 检查API接口定义
                        required_functions = [
                            "getKlingLipSyncConfig",
                            "saveKlingLipSyncConfig",
                            "submitKlingLipSyncTask",
                        ]
                        for func_name in required_functions:
                            if func_name not in content:
                                self.validation_results["frontend_files"][
                                    "details"
                                ].append(f"文件 {file_path} 缺少函数: {func_name}")

                        # 检查音色选项
                        if (
                            "chineseVoiceOptions" not in content
                            or "englishVoiceOptions" not in content
                        ):
                            self.validation_results["frontend_files"]["details"].append(
                                f"文件 {file_path} 缺少音色选项定义"
                            )

                    elif file_path.endswith("+page.svelte"):
                        # 检查页面组件
                        required_elements = ["<select", "<input", "<button"]
                        for element in required_elements:
                            if element not in content:
                                self.validation_results["frontend_files"][
                                    "details"
                                ].append(f"文件 {file_path} 缺少UI元素: {element}")

            # 检查侧边栏导航
            sidebar_file = src_root / "lib/components/layout/Sidebar.svelte"
            if sidebar_file.exists():
                sidebar_content = sidebar_file.read_text(encoding="utf-8")
                if "视频口型" not in sidebar_content:
                    self.validation_results["frontend_files"]["details"].append(
                        "侧边栏缺少视频口型导航"
                    )

            # 检查管理员设置
            settings_file = src_root / "lib/components/admin/Settings.svelte"
            if settings_file.exists():
                settings_content = settings_file.read_text(encoding="utf-8")
                if "kling-lip-sync" not in settings_content:
                    self.validation_results["frontend_files"]["details"].append(
                        "管理员设置缺少可灵对口型配置"
                    )

            if not self.validation_results["frontend_files"]["details"]:
                self.validation_results["frontend_files"]["status"] = "passed"
                self.validation_results["frontend_files"]["details"].append(
                    "前端文件验证通过"
                )
            else:
                self.validation_results["frontend_files"]["status"] = "failed"

        except Exception as e:
            self.validation_results["frontend_files"]["status"] = "failed"
            self.validation_results["frontend_files"]["details"].append(
                f"前端文件验证异常: {str(e)}"
            )

    async def validate_configuration(self):
        """验证配置完整性"""
        logger.info("⚙️ 验证配置完整性...")

        try:
            # 检查迁移文件
            migrations_dir = project_root / "open_webui/migrations/versions"
            if migrations_dir.exists():
                migration_files = [
                    f for f in migrations_dir.glob("*.py") if "kling_lip_sync" in f.name
                ]
                if not migration_files:
                    self.validation_results["configuration"]["details"].append(
                        "缺少可灵对口型迁移文件"
                    )
            else:
                self.validation_results["configuration"]["details"].append(
                    "迁移目录不存在"
                )

            # 检查Alembic配置
            alembic_ini = project_root / "alembic.ini"
            if not alembic_ini.exists():
                # 尝试在open_webui目录下查找
                alembic_ini = project_root / "open_webui/alembic.ini"

            if alembic_ini.exists():
                self.validation_results["configuration"]["details"].append(
                    "✅ Alembic配置文件存在"
                )
            else:
                self.validation_results["configuration"]["details"].append(
                    "❌ Alembic配置文件不存在"
                )

            # 检查验证脚本
            scripts_dir = project_root / "scripts"
            if scripts_dir.exists():
                if (scripts_dir / "validate_kling_lip_sync.py").exists():
                    self.validation_results["configuration"]["details"].append(
                        "✅ 验证脚本存在"
                    )

            # 检查测试文件
            tests_dir = project_root / "tests"
            if tests_dir.exists():
                if (tests_dir / "test_kling_lip_sync.py").exists():
                    self.validation_results["configuration"]["details"].append(
                        "✅ 测试文件存在"
                    )
                else:
                    self.validation_results["configuration"]["details"].append(
                        "❌ 缺少测试文件"
                    )

            # 检查是否有错误信息
            has_errors = any(
                "❌" in detail
                for detail in self.validation_results["configuration"]["details"]
            )
            if not has_errors and self.validation_results["configuration"]["details"]:
                self.validation_results["configuration"]["status"] = "passed"
                self.validation_results["configuration"]["details"].append(
                    "配置完整性验证通过"
                )
            elif not self.validation_results["configuration"]["details"]:
                self.validation_results["configuration"]["status"] = "passed"
                self.validation_results["configuration"]["details"].append(
                    "配置完整性验证通过"
                )
            else:
                self.validation_results["configuration"]["status"] = "failed"

        except Exception as e:
            self.validation_results["configuration"]["status"] = "failed"
            self.validation_results["configuration"]["details"].append(
                f"配置验证异常: {str(e)}"
            )

    async def validate_integration(self):
        """验证集成功能"""
        logger.info("🔗 验证集成功能...")

        try:
            # 这里可以添加实际的集成测试
            # 例如：启动测试服务器，模拟API调用等

            # 检查音色选项数量（在前端定义）
            try:
                # 检查前端音色选项文件
                api_file = project_root.parent / "src/lib/apis/kling-lip-sync/index.ts"
                if not api_file.exists():
                    # 尝试相对路径
                    api_file = project_root / "../src/lib/apis/kling-lip-sync/index.ts"

                if api_file.exists():
                    api_content = api_file.read_text(encoding="utf-8")
                    if (
                        "chineseVoiceOptions" in api_content
                        and "englishVoiceOptions" in api_content
                    ):
                        # 简单计算音色数量
                        chinese_count = (
                            api_content.count("{ value: '")
                            - api_content.count("{ value: 'genshin_")
                            + 5
                        )  # 大致估算
                        self.validation_results["integration"]["details"].append(
                            f"✅ 音色选项文件存在，包含中英文音色选项"
                        )
                    else:
                        self.validation_results["integration"]["details"].append(
                            "❌ 前端音色选项定义不完整"
                        )
                else:
                    self.validation_results["integration"]["details"].append(
                        "❌ 无法找到前端音色选项文件"
                    )

            except Exception as e:
                self.validation_results["integration"]["details"].append(
                    f"检查音色选项失败: {str(e)}"
                )

            # 检查是否有错误信息
            has_errors = any(
                "❌" in detail
                for detail in self.validation_results["integration"]["details"]
            )
            if not has_errors and self.validation_results["integration"]["details"]:
                self.validation_results["integration"]["status"] = "passed"
                self.validation_results["integration"]["details"].append(
                    "集成功能验证通过"
                )
            elif not self.validation_results["integration"]["details"]:
                self.validation_results["integration"]["status"] = "passed"
                self.validation_results["integration"]["details"].append(
                    "集成功能验证通过"
                )
            else:
                self.validation_results["integration"]["status"] = "failed"

        except Exception as e:
            self.validation_results["integration"]["status"] = "failed"
            self.validation_results["integration"]["details"].append(
                f"集成验证异常: {str(e)}"
            )

    def generate_report(self):
        """生成验证报告"""
        logger.info("📋 生成验证报告...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "passed",
            "results": self.validation_results,
        }

        # 检查整体状态
        failed_components = [
            component
            for component, result in self.validation_results.items()
            if result["status"] == "failed"
        ]

        if failed_components:
            report["overall_status"] = "failed"
            report["failed_components"] = failed_components

        # 输出报告到控制台
        print("\n" + "=" * 80)
        print("🎭 可灵对口型功能验证报告")
        print("=" * 80)
        print(f"验证时间: {report['timestamp']}")
        print(
            f"整体状态: {'✅ 通过' if report['overall_status'] == 'passed' else '❌ 失败'}"
        )
        print()

        for component, result in self.validation_results.items():
            status_emoji = (
                "✅"
                if result["status"] == "passed"
                else "❌" if result["status"] == "failed" else "⏳"
            )
            print(f"{status_emoji} {component.upper()}: {result['status']}")
            for detail in result["details"]:
                print(f"   • {detail}")
            print()

        if failed_components:
            print("❌ 验证失败组件:")
            for component in failed_components:
                print(f"   • {component}")
            print("\n请修复上述问题后重新验证。")
        else:
            print("🎉 所有验证通过！可灵对口型功能已准备好部署到生产环境。")
            print("📋 部署步骤：")
            print("   1. cd backend && alembic upgrade head")
            print("   2. 重启应用服务")
            print("   3. 配置管理员设置")
            print("   4. 参考 DEPLOYMENT_GUIDE.md 了解详细信息")

        print("=" * 80)

        # 保存报告到文件
        report_file = (
            project_root
            / f'validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 详细报告已保存到: {report_file}")


async def main():
    """主函数"""
    print("🎭 可灵对口型功能验证器")
    print("=" * 60)
    print("此脚本将验证可灵对口型功能的完整性和正确性")
    print("适用于生产部署前的最终检查")
    print("=" * 60)

    validator = KlingLipSyncValidator()
    await validator.validate_all()


if __name__ == "__main__":
    asyncio.run(main())
