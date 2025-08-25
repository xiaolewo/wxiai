#!/usr/bin/env python3
"""
更新前端积分显示代码为整数格式
"""

import os
import sys
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_credit_display_files():
    """更新前端积分显示相关文件"""

    # 需要更新的文件列表和对应的修改规则
    files_to_update = [
        {
            "file": "src/lib/components/chat/Settings/Credit.svelte",
            "updates": [
                {
                    "old": r"<div>{credit}</div>",
                    "new": r"<div>{Math.round(credit)}</div>",
                    "description": "主积分显示为整数",
                },
                {
                    "old": r"{parseFloat\(log\.credit\)\.toFixed\(6\)}",
                    "new": r"{Math.round(parseFloat(log.credit))}",
                    "description": "积分日志显示为整数",
                },
                {
                    "old": r"Math\.round\(usage\.total_price \* 1e6\) / 1e6",
                    "new": r"Math.round(usage.total_price)",
                    "description": "使用量价格显示为整数",
                },
                {
                    "old": r"usage\.request_unit_price / 1e6",
                    "new": r"Math.round(usage.request_unit_price)",
                    "description": "请求单价显示为整数",
                },
                {
                    "old": r"Math\.round\(usage\.prompt_tokens \* usage\.prompt_unit_price \+ usage\.completion_tokens \* usage\.completion_unit_price\) / 1e6",
                    "new": r"Math.round(usage.prompt_tokens * usage.prompt_unit_price + usage.completion_tokens * usage.completion_unit_price)",
                    "description": "Token价格计算显示为整数",
                },
            ],
        },
        {
            "file": "src/lib/components/admin/Users/Credit.svelte",
            "updates": [
                {
                    "old": r"{statsData\.total_payment \?\? 0}",
                    "new": r"{Math.round(statsData.total_payment ?? 0)}",
                    "description": "总支付金额显示为整数",
                },
                {
                    "old": r"{statsData\.total_credit \?\? 0}",
                    "new": r"{Math.round(statsData.total_credit ?? 0)}",
                    "description": "总积分消费显示为整数",
                },
                {
                    "old": r"{statsData\.total_tokens \?\? 0}",
                    "new": r"{Math.round(statsData.total_tokens ?? 0)}",
                    "description": "总Token消费显示为整数",
                },
            ],
        },
        {
            "file": "src/lib/components/admin/Users/UserList.svelte",
            "updates": [
                {
                    "old": r"<td class=\" px-3 py-1\"> {user\.credit} </td>",
                    "new": r'<td class=" px-3 py-1"> {Math.round(user.credit ?? 0)} </td>',
                    "description": "用户列表积分显示为整数",
                }
            ],
        },
    ]

    project_root = Path(__file__).parent.parent
    updated_files = []

    for file_info in files_to_update:
        file_path = project_root / file_info["file"]

        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            continue

        # 读取原文件
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 备份原文件
        backup_path = file_path.with_suffix(file_path.suffix + ".credit_backup")
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 应用更新
        updated = False
        for update in file_info["updates"]:
            if re.search(update["old"], content):
                content = re.sub(update["old"], update["new"], content)
                logger.info(f"✅ {file_path.name}: {update['description']}")
                updated = True
            else:
                logger.warning(f"⚠️  {file_path.name}: 未找到 {update['old']}")

        if updated:
            # 写入更新后的内容
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            updated_files.append(str(file_path))
            logger.info(f"已备份到: {backup_path}")

    return updated_files


def create_credit_utils():
    """创建前端积分工具函数"""
    utils_file = Path(__file__).parent.parent / "src" / "lib" / "utils" / "credit.js"

    # 确保目录存在
    utils_file.parent.mkdir(parents=True, exist_ok=True)

    utils_content = """/**
 * 积分相关工具函数
 * 统一处理积分的格式化和显示
 */

/**
 * 格式化积分为整数显示
 * @param {number|string} credit - 积分值
 * @returns {number} 格式化后的整数积分
 */
export function formatCredit(credit) {
    const num = parseFloat(credit);
    if (isNaN(num)) return 0;
    return Math.round(num);
}

/**
 * 格式化积分价格为整数
 * @param {number} price - 价格值
 * @returns {number} 格式化后的整数价格
 */
export function formatCreditPrice(price) {
    const num = parseFloat(price);
    if (isNaN(num)) return 0;
    return Math.round(num);
}

/**
 * 检查积分是否足够
 * @param {number} current - 当前积分
 * @param {number} required - 需要积分
 * @returns {boolean} 是否足够
 */
export function hasEnoughCredit(current, required) {
    return formatCredit(current) >= formatCredit(required);
}

/**
 * 计算积分差值
 * @param {number} current - 当前积分
 * @param {number} required - 需要积分
 * @returns {number} 积分差值（正数表示不足）
 */
export function getCreditDifference(current, required) {
    return Math.max(0, formatCredit(required) - formatCredit(current));
}

/**
 * 格式化积分显示文本
 * @param {number} credit - 积分值
 * @param {string} unit - 单位（默认"积分"）
 * @returns {string} 格式化后的显示文本
 */
export function formatCreditText(credit, unit = "积分") {
    return `${formatCredit(credit)} ${unit}`;
}
"""

    with open(utils_file, "w", encoding="utf-8") as f:
        f.write(utils_content)

    logger.info(f"✅ 已创建积分工具函数: {utils_file}")
    return str(utils_file)


def update_stores_credit():
    """更新stores中的积分处理"""
    stores_file = Path(__file__).parent.parent / "src" / "lib" / "stores" / "index.ts"

    if not stores_file.exists():
        logger.warning(f"stores文件不存在: {stores_file}")
        return False

    with open(stores_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 备份原文件
    backup_file = stores_file.with_suffix(".ts.credit_backup")
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)

    # 检查是否需要添加积分格式化函数
    if "formatCredit" not in content:
        # 在文件末尾添加积分格式化相关代码
        additional_code = """

// 积分格式化函数
export const formatCredit = (credit: number | string): number => {
    const num = parseFloat(String(credit));
    if (isNaN(num)) return 0;
    return Math.round(num);
};
"""
        content += additional_code

        with open(stores_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ 已更新 {stores_file}")
        logger.info(f"已备份到: {backup_file}")
        return True
    else:
        logger.info(f"stores中已有积分格式化函数")
        return True


def main():
    logger.info("开始更新前端积分显示为整数...")
    logger.info("=" * 50)

    success_count = 0
    total_count = 3

    # 1. 更新积分显示文件
    logger.info("\n1. 更新前端积分显示文件...")
    try:
        updated_files = update_credit_display_files()
        if updated_files:
            logger.info(f"已更新 {len(updated_files)} 个文件:")
            for file in updated_files:
                logger.info(f"  - {file}")
            success_count += 1
        else:
            logger.warning("没有文件被更新")
    except Exception as e:
        logger.error(f"更新积分显示文件失败: {e}")

    # 2. 创建积分工具函数
    logger.info("\n2. 创建积分工具函数...")
    try:
        utils_file = create_credit_utils()
        logger.info(f"积分工具函数创建完成: {utils_file}")
        success_count += 1
    except Exception as e:
        logger.error(f"创建积分工具函数失败: {e}")

    # 3. 更新stores
    logger.info("\n3. 更新stores积分处理...")
    try:
        if update_stores_credit():
            success_count += 1
    except Exception as e:
        logger.error(f"更新stores失败: {e}")

    # 总结
    logger.info("\n" + "=" * 50)
    logger.info(f"前端积分整数化完成: {success_count}/{total_count}")

    if success_count == total_count:
        logger.info("✅ 前端积分显示更新完成！")
        logger.info("\n更新内容:")
        logger.info("- 所有积分显示改为整数（Math.round）")
        logger.info("- 创建了积分工具函数 credit.js")
        logger.info("- 更新了 stores 中的积分处理")
        logger.info("- 备份文件保存为 *.credit_backup")

        logger.info("\n使用建议:")
        logger.info(
            "- 导入积分工具: import { formatCredit } from '$lib/utils/credit.js'"
        )
        logger.info("- 格式化显示: {formatCredit(credit)}")
        logger.info("- 检查余额: hasEnoughCredit(current, required)")
    else:
        logger.error("❌ 部分更新失败，请检查日志")

    return success_count == total_count


if __name__ == "__main__":
    main()
