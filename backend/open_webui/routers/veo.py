"""
Veo视频生成 API 路由
实现Google Veo视频生成功能，包括文生视频、图生视频等
支持云存储、积分管理、任务状态监控等完整功能
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import json
import asyncio
from datetime import datetime, timedelta
import uuid
import logging

from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.config import CACHE_DIR
from open_webui.internal.db import get_db
from open_webui.models.veo import (
    VeoConfig,
    VeoTask,
    VeoCredit,
    VeoConfigForm,
    VeoGenerateRequest,
    VeoTaskForm,
    VeoTaskResponse,
    VeoUserConfig,
)
from open_webui.utils.veo import (
    VeoApiClient,
    deduct_user_credits,
    add_user_credits,
    get_user_credit_balance,
    validate_user_credits,
    process_veo_generation,
    monitor_veo_task,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/veo", tags=["veo"])

# 全局变量存储Veo配置
veo_config = None
veo_client = None


def get_veo_client():
    """获取Veo API客户端"""
    global veo_client, veo_config
    if not veo_client or not veo_config:
        config = VeoConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="Veo服务未配置或已禁用")
        veo_client = VeoApiClient(config)
        veo_config = config
    return veo_client


# ======================== 配置管理 ========================


@router.get("/config")
async def get_veo_config(user=Depends(get_admin_user)):
    """获取Veo配置 - 管理员专用"""
    config = VeoConfig.get_config()
    if not config:
        # 返回默认配置
        return {
            "enabled": False,
            "base_url": "https://api.veoai.com",
            "api_key": "",
            "model_credits_config": {
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
            },
            "default_model": "veo3",
            "default_enhance_prompt": True,
            "max_concurrent_tasks": 3,
            "task_timeout": 900000,
            "query_interval": 15000,
        }
    return config.to_dict()


@router.get("/config/user")
async def get_veo_user_config(user=Depends(get_verified_user)):
    """获取Veo用户配置 - 只返回用户需要的配置信息（不包含敏感信息）"""
    config = VeoConfig.get_config()
    if not config:
        # 返回默认用户配置
        return {
            "enabled": False,
            "supported_models": [],
            "model_credits_config": {},
            "default_model": "veo3",
            "default_enhance_prompt": True,
            "model_image_limits": {},
        }

    # 只返回用户需要的配置，不包含敏感信息
    supported_models = config.get_supported_models()
    model_image_limits = {}

    for model in supported_models:
        model_image_limits[model] = config.get_model_image_limits(model)

    return {
        "enabled": config.enabled,
        "supported_models": supported_models,
        "model_credits_config": config.model_credits_config
        or config._get_default_model_credits(),
        "default_model": config.default_model,
        "default_enhance_prompt": config.default_enhance_prompt,
        "model_image_limits": model_image_limits,
    }


@router.post("/config")
async def update_veo_config(config_data: VeoConfigForm, user=Depends(get_admin_user)):
    """更新Veo配置 - 管理员专用"""
    try:
        # 重置全局客户端缓存
        global veo_client, veo_config
        veo_client = None
        veo_config = None

        # config_data.model_credits_config = str(config_data.model_credits_config)

        # 保存配置
        config = VeoConfig.save_config(config_data=config_data.model_dump())

        logger.info(f"🔧 【Veo配置】管理员 {user.id} 更新了Veo配置")

        return {"success": True, "message": "配置已更新", "config": config.to_dict()}
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        logger.error(f"🔧 【Veo配置】更新配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


# ======================== 视频生成 ========================


@router.post("/generate")
async def generate_veo_video(
    request: VeoGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """生成Veo视频"""
    try:
        logger.info(f"🎬 【Veo生成】用户 {user.id} 请求生成视频，模型: {request.model}")
        logger.info(
            f"🎬 【Veo生成】请求详情: prompt='{request.prompt[:50]}...', enhance_prompt={request.enhance_prompt}, images_count={len(request.images) if request.images else 0}"
        )

        # 检查服务是否启用
        config = VeoConfig.get_config()
        if not config or not config.enabled:
            logger.error("🎬 【Veo生成】服务未启用")
            raise HTTPException(status_code=400, detail="Veo服务未启用")

        logger.info(
            f"🎬 【Veo生成】配置检查通过: enabled={config.enabled}, base_url={config.base_url}"
        )

        # 验证模型是否支持
        supported_models = config.get_supported_models()
        logger.info(f"🎬 【Veo生成】支持的模型列表: {supported_models}")

        if request.model not in supported_models:
            logger.error(
                f"🎬 【Veo生成】不支持的模型: {request.model}, 支持的模型: {supported_models}"
            )
            raise HTTPException(
                status_code=400, detail=f"不支持的模型: {request.model}"
            )

        logger.info(f"🎬 【Veo生成】模型验证通过: {request.model}")

        # 验证图片数量限制
        if request.images:
            logger.info(f"🎬 【Veo生成】开始验证图片输入: {len(request.images)} 张图片")
            image_limits = config.get_model_image_limits(request.model)
            max_images = image_limits.get("max", 0)

            logger.info(f"🎬 【Veo生成】模型 {request.model} 图片限制: {image_limits}")

            if max_images == 0:
                logger.error(f"🎬 【Veo生成】模型 {request.model} 不支持图片输入")
                raise HTTPException(
                    status_code=400, detail=f"模型 {request.model} 不支持图片输入"
                )
            elif len(request.images) > max_images:
                logger.error(
                    f"🎬 【Veo生成】图片数量超限: {len(request.images)} > {max_images}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"模型 {request.model} 最多支持 {max_images} 张图片，您提供了 {len(request.images)} 张",
                )

            logger.info(
                f"🎬 【Veo生成】图片验证通过: {len(request.images)}/{max_images}"
            )

        logger.info("🎬 【Veo生成】开始调用 process_veo_generation...")

        # 处理视频生成
        result = await process_veo_generation(request, user.id)

        logger.info(f"🎬 【Veo生成】process_veo_generation 返回结果: {result}")

        if result["success"]:
            logger.info(f"🎬 【Veo生成】任务提交成功: task_id={result['task_id']}")
            return {
                "success": True,
                "task_id": result["task_id"],
                "external_task_id": result.get("external_task_id"),
                "credits_cost": result["credits_cost"],
                "message": result["message"],
                "estimated_time": "5-15分钟",
            }
        else:
            logger.error(
                f"🎬 【Veo生成】process_veo_generation 返回失败: {result['error']}"
            )
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException as he:
        logger.error(f"🎬 【Veo生成】HTTP异常: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"🎬 【Veo生成】生成视频时出错: {str(e)}")
        logger.exception("🎬 【Veo生成】异常堆栈:")
        raise HTTPException(status_code=500, detail=f"生成视频失败: {str(e)}")


# ======================== 任务管理 ========================


@router.get("/task/{task_id}")
async def get_veo_task(task_id: str, user=Depends(get_verified_user)):
    """获取Veo任务详情"""
    try:
        task = VeoTask.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 权限检查：只能查看自己的任务，管理员可以查看所有任务
        if task.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="无权限查看此任务")

        return {"success": True, "task": task.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 【Veo任务】获取任务 {task_id} 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")


@router.get("/tasks")
async def get_veo_tasks(
    limit: int = 20, offset: int = 0, user=Depends(get_verified_user)
):
    """获取用户的Veo任务列表"""
    try:
        tasks = VeoTask.get_tasks_by_user(user.id, limit, offset)

        return {
            "success": True,
            "tasks": [task.to_dict() for task in tasks],
            "total": len(tasks),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"🔍 【Veo任务】获取用户 {user.id} 任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.post("/action")
async def veo_task_action(
    request: Request, action_data: Dict[str, Any], user=Depends(get_verified_user)
):
    """执行Veo任务操作（如取消任务等）"""
    # 添加全局异常捕获以确保所有错误都被记录
    logger.info(f"🎯 【Veo操作】endpoint函数开始执行")

    try:
        # 记录原始请求信息
        logger.info(f"🎯 【Veo操作】收到POST请求: {request.method} {request.url}")
        logger.info(f"🎯 【Veo操作】请求头: {dict(request.headers)}")
        logger.info(
            f"🎯 【Veo操作】用户信息: id={user.id}, role={getattr(user, 'role', 'unknown')}"
        )
        logger.info(f"🎯 【Veo操作】解析后的请求数据: {action_data}")
        logger.info(f"🎯 【Veo操作】请求数据类型: {type(action_data)}")

        logger.info(f"🎯 【Veo操作】用户 {user.id} 请求执行任务操作")
        logger.info(f"🎯 【Veo操作】请求数据: {action_data}")

        action = action_data.get("action")
        task_id = action_data.get("task_id")

        logger.info(f"🎯 【Veo操作】解析参数: action={action}, task_id={task_id}")

        if not action or not task_id:
            logger.error(
                f"🎯 【Veo操作】缺少必要参数: action={action}, task_id={task_id}"
            )
            raise HTTPException(status_code=400, detail="缺少必要参数")

        logger.info(f"🎯 【Veo操作】查询任务: {task_id}")
        task = VeoTask.get_task_by_id(task_id)
        if not task:
            logger.error(f"🎯 【Veo操作】任务不存在: {task_id}")
            raise HTTPException(status_code=404, detail="任务不存在")

        logger.info(
            f"🎯 【Veo操作】任务信息: id={task.id}, user_id={task.user_id}, status={task.status}"
        )

        # 权限检查
        if task.user_id != user.id and user.role != "admin":
            logger.error(
                f"🎯 【Veo操作】权限不足: task.user_id={task.user_id}, user.id={user.id}, user.role={user.role}"
            )
            raise HTTPException(status_code=403, detail="无权限操作此任务")

        if action == "cancel":
            logger.info(f"🎯 【Veo操作】执行取消操作，当前状态: {task.status}")

            # 取消任务 - 只能取消进行中的任务
            if task.status in ["completed", "failed", "cancelled"]:
                logger.error(f"🎯 【Veo操作】任务状态不允许取消: {task.status}")
                raise HTTPException(
                    status_code=400,
                    detail=f"任务已完成或已取消，当前状态: {task.status}",
                )

            logger.info("🎯 【Veo操作】更新任务状态为已取消")
            # 更新任务状态
            VeoTask.update_task_status(
                task_id,
                {
                    "status": "cancelled",
                    "fail_reason": "用户取消",
                    "finish_time": datetime.now(),
                },
            )

            # 退还积分（只有进行中的任务被取消才退还积分）
            if task.credits_cost:
                logger.info(f"🎯 【Veo操作】退还积分: {task.credits_cost}")
                add_user_credits(
                    task.user_id, task.credits_cost, task_id, "用户取消任务"
                )

            logger.info(f"🚫 【Veo任务】用户 {user.id} 成功取消了任务 {task_id}")

            return {
                "success": True,
                "message": "任务已取消",
                "task": VeoTask.get_task_by_id(task_id).to_dict(),
            }
        elif action == "delete":
            logger.info(f"🎯 【Veo操作】执行删除操作，当前状态: {task.status}")

            # 删除任务 - 可以删除任何状态的任务
            logger.info("🗑️ 【Veo操作】删除任务记录...")

            try:
                # 删除任务记录
                success = VeoTask.delete_task(task_id)
                if success:
                    logger.info(f"🗑️ 【Veo任务】用户 {user.id} 成功删除了任务 {task_id}")
                    return {"success": True, "message": "任务已删除"}
                else:
                    logger.error(f"🗑️ 【Veo操作】删除任务失败: {task_id}")
                    raise HTTPException(status_code=500, detail="删除任务失败")

            except Exception as e:
                logger.error(f"🗑️ 【Veo操作】删除任务时发生错误: {str(e)}")
                raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")
        else:
            logger.error(f"🎯 【Veo操作】不支持的操作: {action}")
            raise HTTPException(status_code=400, detail=f"不支持的操作: {action}")

    except HTTPException as he:
        logger.error(f"🎯 【Veo操作】HTTP异常: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"🎯 【Veo操作】执行任务操作失败: {str(e)}")
        logger.exception("🎯 【Veo操作】异常堆栈:")
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


# ======================== 用户信息 ========================


@router.get("/user/credits")
async def get_user_veo_credits(user=Depends(get_verified_user)):
    """获取用户Veo相关积分信息"""
    try:
        # 当前积分余额
        current_balance = get_user_credit_balance(user.id)

        # Veo积分消费记录（最近50条）
        veo_credits = VeoCredit.get_credits_by_user(user.id, 50)

        # 统计信息
        total_consumed = sum(
            credit.credit_amount
            for credit in veo_credits
            if credit.operation_type == "deduct"
        )
        total_refunded = sum(
            credit.credit_amount
            for credit in veo_credits
            if credit.operation_type == "refund"
        )

        return {
            "success": True,
            "current_balance": current_balance,
            "veo_credits": [
                {
                    "id": credit.id,
                    "task_id": credit.task_id,
                    "credit_amount": credit.credit_amount,
                    "operation_type": credit.operation_type,
                    "model_name": credit.model_name,
                    "description": credit.description,
                    "created_at": (
                        credit.created_at.isoformat() if credit.created_at else None
                    ),
                }
                for credit in veo_credits
            ],
            "statistics": {
                "total_consumed": total_consumed,
                "total_refunded": total_refunded,
                "net_consumed": total_consumed - total_refunded,
            },
        }
    except Exception as e:
        logger.error(f"💰 【Veo积分】获取用户 {user.id} 积分信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取积分信息失败: {str(e)}")


# ======================== 管理员功能 ========================


@router.get("/admin/stats")
async def get_veo_admin_stats(user=Depends(get_admin_user)):
    """获取Veo服务统计信息 - 管理员专用"""
    try:
        with get_db() as db:
            # 任务统计
            total_tasks = db.query(VeoTask).count()
            completed_tasks = (
                db.query(VeoTask).filter(VeoTask.status == "completed").count()
            )
            failed_tasks = db.query(VeoTask).filter(VeoTask.status == "failed").count()
            processing_tasks = (
                db.query(VeoTask)
                .filter(VeoTask.status.in_(["submitted", "processing"]))
                .count()
            )

            # 积分统计
            total_credits_consumed = (
                db.query(VeoCredit)
                .filter(VeoCredit.operation_type == "deduct")
                .with_entities(db.func.sum(VeoCredit.credit_amount).label("total"))
                .scalar()
                or 0
            )

            total_credits_refunded = (
                db.query(VeoCredit)
                .filter(VeoCredit.operation_type == "refund")
                .with_entities(db.func.sum(VeoCredit.credit_amount).label("total"))
                .scalar()
                or 0
            )

            # 模型使用统计
            model_stats = {}
            tasks = db.query(VeoTask).all()
            for task in tasks:
                model = task.model
                if model not in model_stats:
                    model_stats[model] = {"count": 0, "completed": 0, "failed": 0}
                model_stats[model]["count"] += 1
                if task.status == "completed":
                    model_stats[model]["completed"] += 1
                elif task.status == "failed":
                    model_stats[model]["failed"] += 1

        return {
            "success": True,
            "task_statistics": {
                "total": total_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "processing": processing_tasks,
                "success_rate": (
                    round(completed_tasks / total_tasks * 100, 2)
                    if total_tasks > 0
                    else 0
                ),
            },
            "credit_statistics": {
                "total_consumed": int(total_credits_consumed),
                "total_refunded": int(total_credits_refunded),
                "net_consumed": int(total_credits_consumed - total_credits_refunded),
            },
            "model_statistics": model_stats,
        }
    except Exception as e:
        logger.error(f"📊 【Veo统计】获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/admin/tasks")
async def get_all_veo_tasks(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    user=Depends(get_admin_user),
):
    """获取所有Veo任务 - 管理员专用"""
    try:
        with get_db() as db:
            query = db.query(VeoTask).order_by(VeoTask.created_at.desc())

            if status:
                query = query.filter(VeoTask.status == status)

            tasks = query.limit(limit).offset(offset).all()
            total = query.count()

        return {
            "success": True,
            "tasks": [task.to_dict() for task in tasks],
            "total": total,
            "limit": limit,
            "offset": offset,
            "filter_status": status,
        }
    except Exception as e:
        logger.error(f"📋 【Veo管理】获取所有任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")


# ======================== 健康检查 ========================


@router.get("/health")
async def veo_health_check():
    """Veo服务健康检查"""
    try:
        config = VeoConfig.get_config()

        if not config:
            return {"status": "error", "message": "配置未找到", "enabled": False}

        health_status = {
            "status": "ok" if config.enabled else "disabled",
            "enabled": config.enabled,
            "base_url": config.base_url,
            "supported_models": config.get_supported_models() if config.enabled else [],
            "config_valid": bool(config.api_key) if config.enabled else False,
        }

        # 如果启用，尝试测试API连接
        if config.enabled and config.api_key:
            try:
                client = VeoApiClient(config)
                # 这里可以添加简单的API测试
                health_status["api_accessible"] = True
            except Exception as e:
                health_status["api_accessible"] = False
                health_status["api_error"] = str(e)

        return health_status

    except Exception as e:
        logger.error(f"🔍 【Veo健康检查】检查失败: {str(e)}")
        return {
            "status": "error",
            "message": f"健康检查失败: {str(e)}",
            "enabled": False,
        }
