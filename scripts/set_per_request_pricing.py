#!/usr/bin/env python3
"""
批量设置模型为按次计费模式
将现有模型从token计费切换到按次计费
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from open_webui.models.models import Models, ModelForm, ModelPriceForm
from open_webui.models.users import Users


class RequestPricingUpdater:
    """按次计费模式配置器"""

    def __init__(self):
        self.pricing_config = {
            # 不同模型类别的按次计费价格（每次1积分）
            "gpt-4": 10,  # 每次对话10积分
            "gpt-3.5": 1,  # 每次对话1积分
            "claude": 8,  # 每次对话8积分
            "gemini": 2,  # 每次对话2积分
            "llama": 0.5,  # 每次对话0.5积分
            "default": 1,  # 默认每次对话1积分
        }

    def get_model_category(self, model_id: str) -> str:
        """根据模型ID判断模型类别"""
        model_lower = model_id.lower()

        if "gpt-4" in model_lower:
            return "gpt-4"
        elif "gpt-3.5" in model_lower or "gpt3.5" in model_lower:
            return "gpt-3.5"
        elif "claude" in model_lower:
            return "claude"
        elif "gemini" in model_lower:
            return "gemini"
        elif "llama" in model_lower:
            return "llama"
        else:
            return "default"

    def get_request_price(self, model_id: str) -> int:
        """获取模型的按次计费价格"""
        category = self.get_model_category(model_id)
        return self.pricing_config.get(category, self.pricing_config["default"])

    def update_model_pricing(self, model_id: str, dry_run: bool = True) -> bool:
        """更新单个模型的计费方式"""
        try:
            model = Models.get_model_by_id(model_id)
            if not model:
                logger.warning(f"模型 {model_id} 不存在")
                return False

            # 计算按次价格
            request_price = self.get_request_price(model_id)

            # 构建新的价格配置
            new_price = {
                "prompt_price": 0,  # 禁用token计费
                "completion_price": 0,  # 禁用token计费
                "prompt_cache_price": 0,  # 禁用缓存token计费
                "request_price": request_price,  # 启用按次计费
                "minimum_credit": request_price,  # 最小积分要求
            }

            logger.info(f"模型 {model_id} 计费方式更新:")
            logger.info(f"  类别: {self.get_model_category(model_id)}")
            logger.info(f"  按次价格: {request_price}积分/次")

            if dry_run:
                logger.info("  [预览模式] 不会实际更新数据库")
                return True

            # 更新模型配置
            form_data = ModelForm(
                id=model.id,
                base_model_id=model.base_model_id,
                name=model.name,
                meta=model.meta,
                params=model.params,
                access_control=model.access_control,
                price=ModelPriceForm(**new_price),
                is_active=model.is_active,
            )

            # 获取管理员用户作为更新者
            admin_user = Users.get_user_by_role("admin")
            if not admin_user:
                logger.error("未找到管理员用户")
                return False

            updated_model = Models.update_model_by_id(
                model_id, form_data, admin_user[0].id
            )
            if updated_model:
                logger.info(f"  ✅ 模型 {model_id} 更新成功")
                return True
            else:
                logger.error(f"  ❌ 模型 {model_id} 更新失败")
                return False

        except Exception as e:
            logger.error(f"更新模型 {model_id} 时出错: {e}")
            return False

    def update_all_models(self, dry_run: bool = True) -> Dict[str, Any]:
        """批量更新所有模型的计费方式"""
        logger.info("开始批量更新模型计费方式...")

        # 获取所有模型
        models = Models.get_all_models()

        result = {"total": len(models), "success": 0, "failed": 0, "failed_models": []}

        for model in models:
            logger.info(f"\n处理模型: {model.id}")

            if self.update_model_pricing(model.id, dry_run):
                result["success"] += 1
            else:
                result["failed"] += 1
                result["failed_models"].append(model.id)

        # 输出结果统计
        logger.info("\n" + "=" * 50)
        logger.info("批量更新完成统计:")
        logger.info(f"总模型数: {result['total']}")
        logger.info(f"成功更新: {result['success']}")
        logger.info(f"失败数量: {result['failed']}")

        if result["failed_models"]:
            logger.info(f"失败模型: {', '.join(result['failed_models'])}")

        if dry_run:
            logger.info("\n⚠️  这是预览模式，未实际修改数据库")
            logger.info("要实际执行更新，请使用 --execute 参数")

        return result

    def update_specific_models(
        self, model_ids: List[str], dry_run: bool = True
    ) -> Dict[str, Any]:
        """更新指定的模型列表"""
        logger.info(f"开始更新指定模型: {', '.join(model_ids)}")

        result = {
            "total": len(model_ids),
            "success": 0,
            "failed": 0,
            "failed_models": [],
        }

        for model_id in model_ids:
            logger.info(f"\n处理模型: {model_id}")

            if self.update_model_pricing(model_id, dry_run):
                result["success"] += 1
            else:
                result["failed"] += 1
                result["failed_models"].append(model_id)

        return result

    def show_current_pricing(self):
        """显示当前所有模型的计费配置"""
        logger.info("当前模型计费配置:")
        logger.info("=" * 80)

        models = Models.get_all_models()

        for model in models:
            price_info = model.price or {}
            request_price = price_info.get("request_price", 0)
            prompt_price = price_info.get("prompt_price", 0)
            completion_price = price_info.get("completion_price", 0)

            pricing_mode = "按次计费" if request_price > 0 else "Token计费"

            logger.info(f"模型: {model.id}")
            logger.info(f"  计费模式: {pricing_mode}")

            if request_price > 0:
                logger.info(f"  按次价格: {request_price}积分/次")
            else:
                logger.info(f"  输入Token价格: {prompt_price}/100万token")
                logger.info(f"  输出Token价格: {completion_price}/100万token")

            logger.info("")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="模型计费方式管理工具")
    parser.add_argument(
        "--execute", action="store_true", help="实际执行更新（默认为预览模式）"
    )
    parser.add_argument("--all", action="store_true", help="更新所有模型")
    parser.add_argument("--models", nargs="+", help="更新指定模型ID列表")
    parser.add_argument(
        "--show", action="store_true", help="显示当前所有模型的计费配置"
    )
    parser.add_argument("--config", help="自定义价格配置文件(JSON格式)")

    args = parser.parse_args()

    updater = RequestPricingUpdater()

    # 加载自定义配置
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                custom_config = json.load(f)
            updater.pricing_config.update(custom_config)
            logger.info(f"已加载自定义配置: {args.config}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return

    # 显示当前配置
    if args.show:
        updater.show_current_pricing()
        return

    dry_run = not args.execute

    # 更新所有模型
    if args.all:
        updater.update_all_models(dry_run=dry_run)
    # 更新指定模型
    elif args.models:
        updater.update_specific_models(args.models, dry_run=dry_run)
    else:
        # 显示帮助和当前配置
        parser.print_help()
        print("\n当前价格配置:")
        for category, price in updater.pricing_config.items():
            print(f"  {category}: {price}积分/次")


if __name__ == "__main__":
    main()
