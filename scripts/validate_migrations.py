#!/usr/bin/env python3
"""
数据库迁移验证脚本
用于验证迁移文件的完整性和规范性
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class MigrationFile:
    """迁移文件信息"""

    filename: str
    revision_id: str
    down_revision: str
    description: str
    file_path: Path


class MigrationValidator:
    """迁移文件验证器"""

    def __init__(self, migrations_dir: str = "backend/open_webui/migrations/versions"):
        self.migrations_dir = Path(migrations_dir)
        self.migration_files: List[MigrationFile] = []

    def scan_migration_files(self) -> List[MigrationFile]:
        """扫描所有迁移文件"""
        migration_files = []

        if not self.migrations_dir.exists():
            print(f"❌ 迁移目录不存在: {self.migrations_dir}")
            return migration_files

        for file_path in self.migrations_dir.glob("*.py"):
            if file_path.name == "__pycache__" or file_path.name.startswith("."):
                continue

            migration_info = self._parse_migration_file(file_path)
            if migration_info:
                migration_files.append(migration_info)

        self.migration_files = sorted(migration_files, key=lambda x: x.filename)
        return migration_files

    def _parse_migration_file(self, file_path: Path) -> MigrationFile:
        """解析单个迁移文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取revision信息
            revision_match = re.search(
                r'revision:\s*str\s*=\s*["\']([^"\']+)["\']', content
            )
            down_revision_match = re.search(
                r'down_revision:\s*Union\[str,\s*None\]\s*=\s*["\']([^"\']*)["\']',
                content,
            )

            # 从文件名提取描述
            filename_parts = file_path.stem.split("_", 1)
            description = filename_parts[1] if len(filename_parts) > 1 else "unknown"

            return MigrationFile(
                filename=file_path.name,
                revision_id=revision_match.group(1) if revision_match else "",
                down_revision=(
                    down_revision_match.group(1) if down_revision_match else ""
                ),
                description=description,
                file_path=file_path,
            )
        except Exception as e:
            print(f"⚠️  解析迁移文件失败 {file_path}: {e}")
            return None

    def validate_naming_convention(self) -> List[str]:
        """验证命名规范"""
        issues = []

        naming_patterns = [
            r"^[a-f0-9]{12}_[a-z][a-z0-9_]*\.py$",  # 标准格式
            r"^[0-9]{8}_[0-9]{3}_[a-z][a-z0-9_]*\.py$",  # 时间戳格式
        ]

        for migration in self.migration_files:
            filename = migration.filename

            # 检查是否符合任一命名模式
            matches_pattern = any(
                re.match(pattern, filename) for pattern in naming_patterns
            )

            if not matches_pattern:
                # 特殊文件例外
                if filename in ["merge_heads_final.py"]:
                    continue

                issues.append(f"❌ 命名不规范: {filename}")

            # 检查描述部分
            if "_" not in filename:
                issues.append(f"❌ 缺少描述: {filename}")
            else:
                description = filename.split("_", 1)[1].replace(".py", "")
                if len(description) < 3:
                    issues.append(f"❌ 描述过短: {filename}")

        return issues

    def validate_revision_consistency(self) -> List[str]:
        """验证revision一致性"""
        issues = []
        revision_map = {}

        # 建立revision映射
        for migration in self.migration_files:
            if migration.revision_id:
                if migration.revision_id in revision_map:
                    issues.append(
                        f"❌ 重复的revision ID: {migration.revision_id} 在 {migration.filename} 和 {revision_map[migration.revision_id]}"
                    )
                else:
                    revision_map[migration.revision_id] = migration.filename

        # 检查依赖关系
        for migration in self.migration_files:
            if migration.down_revision and migration.down_revision != "None":
                if (
                    migration.down_revision not in revision_map
                    and migration.down_revision
                ):
                    issues.append(
                        f"❌ 依赖的revision不存在: {migration.down_revision} 在 {migration.filename}"
                    )

        return issues

    def detect_potential_conflicts(self) -> List[str]:
        """检测潜在冲突"""
        issues = []

        # 检查同时修改相同表的迁移
        table_migrations = {}

        for migration in self.migration_files:
            # 简单的表名提取（基于描述）
            description = migration.description.lower()

            # 提取表名关键词
            table_keywords = []
            if "user" in description:
                table_keywords.append("user")
            if "chat" in description:
                table_keywords.append("chat")
            if "file" in description:
                table_keywords.append("file")
            if "midjourney" in description:
                table_keywords.append("midjourney")
            if "flux" in description:
                table_keywords.append("flux")

            for keyword in table_keywords:
                if keyword not in table_migrations:
                    table_migrations[keyword] = []
                table_migrations[keyword].append(migration.filename)

        # 检查是否有多个迁移同时修改同一表
        for table, migrations in table_migrations.items():
            if len(migrations) > 3:  # 超过3个迁移修改同一表可能有问题
                issues.append(
                    f"⚠️  表 '{table}' 被多个迁移修改: {', '.join(migrations[:3])}..."
                )

        return issues

    def check_missing_functions(self) -> List[str]:
        """检查缺失的upgrade/downgrade函数"""
        issues = []

        for migration in self.migration_files:
            try:
                with open(migration.file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if "def upgrade()" not in content:
                    issues.append(f"❌ 缺少upgrade函数: {migration.filename}")

                if "def downgrade()" not in content:
                    issues.append(f"❌ 缺少downgrade函数: {migration.filename}")

            except Exception as e:
                issues.append(f"❌ 无法读取文件 {migration.filename}: {e}")

        return issues

    def generate_migration_graph(self) -> Dict[str, List[str]]:
        """生成迁移依赖图"""
        graph = {}

        for migration in self.migration_files:
            graph[migration.revision_id] = []

        for migration in self.migration_files:
            if migration.down_revision and migration.down_revision in graph:
                graph[migration.down_revision].append(migration.revision_id)

        return graph

    def run_full_validation(self) -> Dict[str, List[str]]:
        """运行完整验证"""
        print("🔍 开始验证数据库迁移文件...")

        # 扫描文件
        migrations = self.scan_migration_files()
        print(f"📁 找到 {len(migrations)} 个迁移文件")

        results = {
            "naming_issues": self.validate_naming_convention(),
            "revision_issues": self.validate_revision_consistency(),
            "conflict_warnings": self.detect_potential_conflicts(),
            "function_issues": self.check_missing_functions(),
        }

        return results

    def print_summary(self, results: Dict[str, List[str]]):
        """打印验证摘要"""
        total_issues = sum(len(issues) for issues in results.values())

        print(f"\n📊 验证摘要:")
        print(f"总计迁移文件: {len(self.migration_files)}")
        print(f"发现问题: {total_issues}")

        if results["naming_issues"]:
            print(f"\n📝 命名规范问题 ({len(results['naming_issues'])}):")
            for issue in results["naming_issues"]:
                print(f"  {issue}")

        if results["revision_issues"]:
            print(f"\n🔗 Revision一致性问题 ({len(results['revision_issues'])}):")
            for issue in results["revision_issues"]:
                print(f"  {issue}")

        if results["function_issues"]:
            print(f"\n⚙️  函数缺失问题 ({len(results['function_issues'])}):")
            for issue in results["function_issues"]:
                print(f"  {issue}")

        if results["conflict_warnings"]:
            print(f"\n⚠️  潜在冲突警告 ({len(results['conflict_warnings'])}):")
            for issue in results["conflict_warnings"]:
                print(f"  {issue}")

        if total_issues == 0:
            print("\n✅ 所有验证通过！迁移文件状态良好。")
        else:
            print(f"\n❌ 发现 {total_issues} 个问题需要关注。")

        return total_issues == 0


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # 切换到项目根目录
    os.chdir(project_root)

    # 创建验证器
    validator = MigrationValidator()

    # 运行验证
    results = validator.run_full_validation()

    # 打印结果
    success = validator.print_summary(results)

    # 返回适当的退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
