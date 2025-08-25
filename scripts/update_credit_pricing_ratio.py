#!/usr/bin/env python3
"""
修改积分计费比例
- Token计费：从 1/1000000 改为 1/1000 (提升1000倍)
- 次数计费：从 1/1000000 改为 1/1 (提升1000000倍)
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent / "backend"))


def update_credit_usage_file():
    """更新 credit/usage.py 文件中的计费比例"""
    usage_file = (
        Path(__file__).parent.parent
        / "backend"
        / "open_webui"
        / "utils"
        / "credit"
        / "usage.py"
    )

    if not usage_file.exists():
        logger.error(f"文件不存在: {usage_file}")
        return False

    # 读取原文件内容
    with open(usage_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 备份原文件
    backup_file = usage_file.with_suffix(".py.backup")
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"已备份原文件到: {backup_file}")

    # 修改计费比例
    modifications = [
        # Token计费：从 /1000/1000 改为 /1000 (prompt价格)
        {
            "old": "return self.prompt_unit_price * self.usage.prompt_tokens / 1000 / 1000",
            "new": "return self.prompt_unit_price * self.usage.prompt_tokens / 1000",
        },
        # Token计费：从 /1000/1000 改为 /1000 (completion价格)
        {
            "old": "return self.completion_unit_price * self.usage.completion_tokens / 1000 / 1000",
            "new": "return self.completion_unit_price * self.usage.completion_tokens / 1000",
        },
        # 次数计费：从 /1000/1000 改为直接返回 (1:1比例)
        {
            "old": "return self.request_unit_price / 1000 / 1000",
            "new": "return self.request_unit_price",
        },
        # 自定义费用比例调整
        {
            "old": "return Decimal(sum(v for _, v in self.custom_fees.items())) / 1000 / 1000",
            "new": "return Decimal(sum(v for _, v in self.custom_fees.items()))",
        },
        # 缓存token价格计算调整
        {
            "old": """return (
                (
                    self.prompt_cache_unit_price * cache_tokens
                    + self.prompt_unit_price * (self.usage.prompt_tokens - cache_tokens)
                )
                / 1000
                / 1000
            )""",
            "new": """return (
                (
                    self.prompt_cache_unit_price * cache_tokens
                    + self.prompt_unit_price * (self.usage.prompt_tokens - cache_tokens)
                )
                / 1000
            )""",
        },
        # 日志记录中的比例调整
        {"old": "k: float(v / 1000 / 1000)", "new": "k: float(v)"},
    ]

    # 应用修改
    modified_content = content
    for mod in modifications:
        if mod["old"] in modified_content:
            modified_content = modified_content.replace(mod["old"], mod["new"])
            logger.info(f"✅ 已修改: {mod['old'][:50]}...")
        else:
            logger.warning(f"⚠️  未找到要修改的内容: {mod['old'][:50]}...")

    # 写入修改后的内容
    with open(usage_file, "w", encoding="utf-8") as f:
        f.write(modified_content)

    logger.info(f"✅ 已更新文件: {usage_file}")
    return True


def update_credit_utils_file():
    """更新 credit/utils.py 文件中的特征价格计费比例"""
    utils_file = (
        Path(__file__).parent.parent
        / "backend"
        / "open_webui"
        / "utils"
        / "credit"
        / "utils.py"
    )

    if not utils_file.exists():
        logger.error(f"文件不存在: {utils_file}")
        return False

    # 读取原文件内容
    with open(utils_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 备份原文件
    backup_file = utils_file.with_suffix(".py.backup")
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"已备份原文件到: {backup_file}")

    # 修改特征价格计费比例（从 /1000/1000 改为 /1000）
    modifications = [
        {
            "old": "Decimal(USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE.value) / 1000 / 1000",
            "new": "Decimal(USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE.value) / 1000",
        },
        {
            "old": "Decimal(USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE.value)\n                    / 1000\n                    / 1000",
            "new": "Decimal(USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE.value)\n                    / 1000",
        },
        {
            "old": "Decimal(USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE.value)\n                    / 1000\n                    / 1000",
            "new": "Decimal(USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE.value)\n                    / 1000",
        },
        {
            "old": "Decimal(USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE.value)\n                    / 1000\n                    / 1000",
            "new": "Decimal(USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE.value)\n                    / 1000",
        },
    ]

    # 应用修改
    modified_content = content
    for mod in modifications:
        if mod["old"] in modified_content:
            modified_content = modified_content.replace(mod["old"], mod["new"])
            logger.info(f"✅ 已修改特征价格: {mod['old'][:40]}...")
        else:
            logger.warning(f"⚠️  未找到特征价格修改内容: {mod['old'][:40]}...")

    # 写入修改后的内容
    with open(utils_file, "w", encoding="utf-8") as f:
        f.write(modified_content)

    logger.info(f"✅ 已更新文件: {utils_file}")
    return True


def update_model_descriptions():
    """更新模型价格描述，反映新的计费比例"""
    models_file = (
        Path(__file__).parent.parent / "backend" / "open_webui" / "models" / "models.py"
    )

    if not models_file.exists():
        logger.error(f"文件不存在: {models_file}")
        return False

    # 读取原文件内容
    with open(models_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 备份原文件
    backup_file = models_file.with_suffix(".py.backup")
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"已备份原文件到: {backup_file}")

    # 更新描述信息
    modifications = [
        {
            "old": 'description="prompt token price for 1m tokens"',
            "new": 'description="prompt token price for 1k tokens"',
        },
        {
            "old": 'description="prompt cache token price for 1m tokens"',
            "new": 'description="prompt cache token price for 1k tokens"',
        },
        {
            "old": 'description="completion token price for 1m tokens"',
            "new": 'description="completion token price for 1k tokens"',
        },
        {
            "old": 'description="price for 1m request"',
            "new": 'description="price for 1 request"',
        },
    ]

    # 应用修改
    modified_content = content
    for mod in modifications:
        if mod["old"] in modified_content:
            modified_content = modified_content.replace(mod["old"], mod["new"])
            logger.info(f"✅ 已更新描述: {mod['old']}")
        else:
            logger.warning(f"⚠️  未找到描述: {mod['old']}")

    # 写入修改后的内容
    with open(models_file, "w", encoding="utf-8") as f:
        f.write(modified_content)

    logger.info(f"✅ 已更新文件: {models_file}")
    return True


def update_pricing_script():
    """更新之前创建的按次计费脚本，使用新的比例"""
    script_file = Path(__file__).parent / "set_per_request_pricing.py"

    if not script_file.exists():
        logger.warning(f"按次计费脚本不存在: {script_file}")
        return True  # 不是必需的文件

    # 读取原文件内容
    with open(script_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 更新价格配置（按新比例）
    new_pricing_config = """        self.pricing_config = {
            # 不同模型类别的按次计费价格（每次1积分）
            "gpt-4": 10,         # 每次对话10积分
            "gpt-3.5": 1,        # 每次对话1积分  
            "claude": 8,         # 每次对话8积分
            "gemini": 2,         # 每次对话2积分
            "llama": 0.5,        # 每次对话0.5积分
            "default": 1         # 默认每次对话1积分
        }"""

    # 查找并替换pricing_config部分
    import re

    pattern = r"self\.pricing_config = \{[^}]+\}"
    if re.search(pattern, content, re.DOTALL):
        modified_content = re.sub(
            pattern, new_pricing_config.strip(), content, flags=re.DOTALL
        )

        # 更新相关的计算和显示逻辑
        modified_content = modified_content.replace(
            'logger.info(f"  按次价格: {request_price}/100万次 (每次{request_price/1000/1000:.6f}积分)")',
            'logger.info(f"  按次价格: {request_price}积分/次")',
        )

        modified_content = modified_content.replace(
            '"minimum_credit": request_price / 1000 / 1000  # 最小积分要求',
            '"minimum_credit": request_price  # 最小积分要求',
        )

        modified_content = modified_content.replace(
            'print(f"  {category}: {price}/100万次 (每次{price/1000/1000:.6f}积分)")',
            'print(f"  {category}: {price}积分/次")',
        )

        # 写入修改后的内容
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(modified_content)

        logger.info(f"✅ 已更新按次计费脚本: {script_file}")
    else:
        logger.warning("未找到pricing_config配置，跳过脚本更新")

    return True


def main():
    logger.info("开始更新积分计费比例...")
    logger.info("目标: Token计费 1:1000, 次数计费 1:1")
    logger.info("=" * 50)

    success_count = 0
    total_count = 4

    # 1. 更新核心计费逻辑
    logger.info("\n1. 更新核心计费逻辑文件...")
    if update_credit_usage_file():
        success_count += 1

    # 2. 更新特征价格计费
    logger.info("\n2. 更新特征价格计费...")
    if update_credit_utils_file():
        success_count += 1

    # 3. 更新模型价格描述
    logger.info("\n3. 更新模型价格描述...")
    if update_model_descriptions():
        success_count += 1

    # 4. 更新按次计费脚本
    logger.info("\n4. 更新按次计费脚本...")
    if update_pricing_script():
        success_count += 1

    # 总结
    logger.info("\n" + "=" * 50)
    logger.info(f"积分计费比例更新完成: {success_count}/{total_count}")

    if success_count == total_count:
        logger.info("✅ 所有文件更新成功！")
        logger.info("\n新的计费比例:")
        logger.info("- Token计费: 1token = 1/1000积分")
        logger.info("- 次数计费: 1次对话 = 1积分")
        logger.info("\n⚠️  请重启后端服务以使更改生效")
        logger.info("💾 备份文件已保存为 *.backup")
    else:
        logger.error("❌ 部分文件更新失败，请检查日志")

    return success_count == total_count


if __name__ == "__main__":
    main()
