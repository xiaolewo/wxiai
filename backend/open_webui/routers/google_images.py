"""
谷歌生图 API Router
支持OpenAI DALL-E兼容格式的图像编辑和生成
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
from datetime import datetime

from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.google_images import (
    GoogleImagesConfig,
    GoogleImagesTask,
    GoogleImagesCredit,
    GoogleImagesConfigForm,
    GoogleImagesTaskForm,
    GoogleImagesGenerateRequest,
    GoogleImagesTaskResponse,
    GoogleImagesGenerateResponse,
    GoogleImagesUserConfig,
)
from open_webui.utils.google_images import (
    process_google_images_generation,
    validate_user_credits,
    get_user_credit_balance,
)

router = APIRouter(prefix="/google_images", tags=["google_images"])

# ======================== 配置管理 ========================


@router.get("/config")
async def get_google_images_config(user=Depends(get_admin_user)) -> dict:
    """获取谷歌生图配置 - 管理员专用"""
    config = GoogleImagesConfig.get_config()
    if not config:
        # 返回默认配置
        return {
            "enabled": False,
            "base_url": "",
            "api_key": "",
            "default_model": "nano-banana",
            "max_images_per_request": 10,
            "timeout": 60,
            "credits_per_generation": 20,
            "credits_per_image": 5,
        }

    return config.to_dict()


@router.post("/config")
async def save_google_images_config(
    config_data: GoogleImagesConfigForm, user=Depends(get_admin_user)
) -> dict:
    """保存谷歌生图配置 - 管理员专用"""
    try:
        # 验证必需字段
        if config_data.enabled and (
            not config_data.base_url or not config_data.api_key
        ):
            raise HTTPException(
                status_code=400, detail="启用服务时需要提供基础URL和API密钥"
            )

        # 转换为字典保存
        config_dict = config_data.dict()
        config = GoogleImagesConfig.save_config(config_dict)

        return {
            "success": True,
            "message": "谷歌生图配置保存成功",
            "config": config.to_dict(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/config/user")
async def get_google_images_user_config(
    user=Depends(get_verified_user),
) -> GoogleImagesUserConfig:
    """获取谷歌生图用户配置 - 只返回用户需要的信息"""
    config = GoogleImagesConfig.get_config()
    if not config:
        return GoogleImagesUserConfig(
            enabled=False,
            supported_models=["nano-banana"],
            max_images_per_request=10,
            default_model="nano-banana",
            credits_per_generation=20,
            credits_per_image=5,
        )

    return GoogleImagesUserConfig(
        enabled=config.enabled,
        supported_models=["nano-banana"],  # 支持的模型列表
        max_images_per_request=config.max_images_per_request,
        default_model=config.default_model,
        credits_per_generation=config.credits_per_generation,
        credits_per_image=config.credits_per_image,
    )


# ======================== 图像生成 ========================


@router.post("/v1/images/edits")
async def create_image_edit(
    request: GoogleImagesGenerateRequest, user=Depends(get_verified_user)
) -> dict:
    """创建图像编辑/生成 - 兼容OpenAI DALL-E格式"""
    try:
        # 检查服务是否启用
        config = GoogleImagesConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="谷歌生图服务未启用")

        # 验证积分
        credits_needed = config.credits_per_generation
        if request.images:
            credits_needed += len(request.images) * config.credits_per_image

        if not validate_user_credits(user.id, credits_needed):
            raise HTTPException(status_code=400, detail="积分不足")

        # 处理生成请求
        result = await process_google_images_generation(request, user.id)

        if result["success"]:
            # 返回OpenAI兼容格式
            return {
                "created": int(datetime.now().timestamp()),
                "data": [
                    (
                        {"url": url}
                        if not url.startswith("data:image/")
                        else {"b64_json": url.split(",")[1]}
                    )
                    for url in result["images"]
                ],
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")


@router.post("/generate")
async def generate_google_images(
    request: GoogleImagesGenerateRequest, user=Depends(get_verified_user)
) -> GoogleImagesGenerateResponse:
    """谷歌生图生成接口 - 自定义格式"""
    try:
        # 检查服务是否启用
        config = GoogleImagesConfig.get_config()
        if not config or not config.enabled:
            return GoogleImagesGenerateResponse(
                success=False, error="谷歌生图服务未启用"
            )

        # 验证积分
        credits_needed = config.credits_per_generation
        if request.images:
            credits_needed += len(request.images) * config.credits_per_image

        if not validate_user_credits(user.id, credits_needed):
            return GoogleImagesGenerateResponse(success=False, error="积分不足")

        # 处理生成请求
        result = await process_google_images_generation(request, user.id)

        return GoogleImagesGenerateResponse(
            success=result["success"],
            task_id=result.get("task_id"),
            credits_cost=result.get("credits_cost"),
            message=result.get("message"),
            error=result.get("error"),
        )

    except Exception as e:
        return GoogleImagesGenerateResponse(
            success=False, error=f"图像生成失败: {str(e)}"
        )


# ======================== 任务管理 ========================


@router.get("/task/{task_id}")
async def get_google_images_task(
    task_id: str, user=Depends(get_verified_user)
) -> GoogleImagesTaskResponse:
    """获取任务详情"""
    try:
        task = GoogleImagesTask.get_task_by_id(task_id)
        if not task:
            return GoogleImagesTaskResponse(success=False, error="任务不存在")

        # 验证任务所有权
        if task.user_id != user.id:
            return GoogleImagesTaskResponse(success=False, error="无权访问此任务")

        # 转换为表单模型
        task_form = GoogleImagesTaskForm(
            id=task.id,
            user_id=task.user_id,
            status=task.status,
            prompt=task.prompt,
            model=task.model,
            input_images=task.input_images,
            cloud_input_images=task.cloud_input_images,
            result_images=task.result_images,
            cloud_result_images=task.cloud_result_images,
            credits_cost=task.credits_cost,
            fail_reason=task.fail_reason,
            properties=task.properties,
            created_at=task.created_at.isoformat() if task.created_at else "",
            updated_at=task.updated_at.isoformat() if task.updated_at else None,
            finish_time=task.finish_time.isoformat() if task.finish_time else None,
        )

        return GoogleImagesTaskResponse(success=True, task_id=task.id, task=task_form)

    except Exception as e:
        return GoogleImagesTaskResponse(success=False, error=f"获取任务失败: {str(e)}")


@router.get("/tasks")
async def get_user_google_images_tasks(
    limit: int = 20, offset: int = 0, user=Depends(get_verified_user)
) -> dict:
    """获取用户任务列表"""
    try:
        tasks = GoogleImagesTask.get_tasks_by_user(user.id, limit, offset)

        task_list = []
        for task in tasks:
            task_form = GoogleImagesTaskForm(
                id=task.id,
                user_id=task.user_id,
                status=task.status,
                prompt=task.prompt,
                model=task.model,
                input_images=task.input_images,
                cloud_input_images=task.cloud_input_images,
                result_images=task.result_images,
                cloud_result_images=task.cloud_result_images,
                credits_cost=task.credits_cost,
                fail_reason=task.fail_reason,
                properties=task.properties,
                created_at=task.created_at.isoformat() if task.created_at else "",
                updated_at=task.updated_at.isoformat() if task.updated_at else None,
                finish_time=task.finish_time.isoformat() if task.finish_time else None,
            )
            task_list.append(task_form.dict())

        return {"success": True, "tasks": task_list, "total": len(task_list)}

    except Exception as e:
        return {"success": False, "error": f"获取任务列表失败: {str(e)}"}


@router.delete("/task/{task_id}")
async def delete_google_images_task(
    task_id: str, user=Depends(get_verified_user)
) -> dict:
    """删除任务"""
    try:
        task = GoogleImagesTask.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 验证任务所有权
        if task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权删除此任务")

        # 删除任务
        success = GoogleImagesTask.delete_task(task_id)
        if success:
            return {"success": True, "message": "任务删除成功"}
        else:
            raise HTTPException(status_code=500, detail="任务删除失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


# ======================== 积分管理 ========================


@router.get("/credits")
async def get_user_google_images_credits(user=Depends(get_verified_user)) -> dict:
    """获取用户积分信息"""
    try:
        balance = get_user_credit_balance(user.id)
        return {"success": True, "balance": balance}

    except Exception as e:
        return {"success": False, "error": f"获取积分信息失败: {str(e)}"}


@router.get("/credits/history")
async def get_user_google_images_credits_history(
    limit: int = 50, user=Depends(get_verified_user)
) -> dict:
    """获取用户积分使用历史"""
    try:
        credits = GoogleImagesCredit.get_credits_by_user(user.id, limit)

        credit_list = []
        for credit in credits:
            credit_list.append(
                {
                    "id": credit.id,
                    "credit_amount": credit.credit_amount,
                    "credits_before": credit.credits_before,
                    "credits_after": credit.credits_after,
                    "operation_type": credit.operation_type,
                    "model_name": credit.model_name,
                    "description": credit.description,
                    "created_at": (
                        credit.created_at.isoformat() if credit.created_at else ""
                    ),
                }
            )

        return {"success": True, "credits": credit_list, "total": len(credit_list)}

    except Exception as e:
        return {"success": False, "error": f"获取积分历史失败: {str(e)}"}


# ======================== 系统管理 ========================


@router.post("/admin/credits/add")
async def admin_add_google_images_credits(
    target_user_id: str,
    credits: int,
    reason: str = "管理员充值",
    user=Depends(get_admin_user),
) -> dict:
    """管理员给用户充值积分"""
    try:
        from open_webui.utils.google_images import add_user_credits
        import uuid

        task_id = str(uuid.uuid4())
        success = add_user_credits(target_user_id, credits, task_id, reason)

        if success:
            new_balance = get_user_credit_balance(target_user_id)
            return {
                "success": True,
                "message": f"成功为用户 {target_user_id} 充值 {credits} 积分",
                "new_balance": new_balance,
            }
        else:
            raise HTTPException(status_code=500, detail="积分充值失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"充值积分失败: {str(e)}")


@router.get("/admin/stats")
async def get_google_images_admin_stats(user=Depends(get_admin_user)) -> dict:
    """获取系统统计信息 - 管理员专用"""
    try:
        from open_webui.internal.db import get_db
        from sqlalchemy import func

        with get_db() as db:
            # 总任务数
            total_tasks = db.query(GoogleImagesTask).count()

            # 成功任务数
            completed_tasks = (
                db.query(GoogleImagesTask)
                .filter(GoogleImagesTask.status == "completed")
                .count()
            )

            # 失败任务数
            failed_tasks = (
                db.query(GoogleImagesTask)
                .filter(GoogleImagesTask.status == "failed")
                .count()
            )

            # 今日任务数
            from datetime import date

            today_tasks = (
                db.query(GoogleImagesTask)
                .filter(func.date(GoogleImagesTask.created_at) == date.today())
                .count()
            )

            # 总积分消耗
            total_credits = (
                db.query(func.sum(GoogleImagesCredit.credit_amount))
                .filter(GoogleImagesCredit.operation_type == "deduct")
                .scalar()
                or 0
            )

        return {
            "success": True,
            "stats": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "today_tasks": today_tasks,
                "total_credits_consumed": abs(total_credits),
                "success_rate": (
                    f"{(completed_tasks/total_tasks*100):.1f}%"
                    if total_tasks > 0
                    else "0%"
                ),
            },
        }

    except Exception as e:
        return {"success": False, "error": f"获取统计信息失败: {str(e)}"}
