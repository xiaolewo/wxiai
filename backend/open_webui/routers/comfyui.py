"""
ComfyUI API路由
提供ComfyUI工作流管理、任务执行、积分管理等接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import asyncio

from open_webui.models.users import Users
from open_webui.utils.auth import get_current_user, get_admin_user
from open_webui.models.comfyui import (
    ComfyUIConfig,
    ComfyUIWorkflow,
    ComfyUITask,
    ComfyUIConfigForm,
    ComfyUIConfigResponse,
    ComfyUIWorkflowForm,
    ComfyUIWorkflowResponse,
    ComfyUITaskRequest,
    ComfyUITaskResponse,
    ComfyUIConfigs,
    ComfyUIWorkflows,
    ComfyUITasks,
    is_comfyui_enabled,
    calculate_workflow_credits,
)
from open_webui.models.credits import Credits
from open_webui.utils.comfyui_api import (
    submit_comfyui_task,
    check_comfyui_task_status,
    ComfyUIWorkflowImporter,
)

router = APIRouter(prefix="/comfyui", tags=["ComfyUI"])
logger = logging.getLogger(__name__)


# ======================== 辅助函数 ========================


def check_comfyui_enabled_dependency():
    """检查ComfyUI是否启用"""
    if not is_comfyui_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ComfyUI服务未启用"
        )


# ======================== 管理员配置接口 ========================


@router.get("/admin/config", response_model=ComfyUIConfigResponse)
async def get_comfyui_config(admin_user=Depends(get_admin_user)):
    """获取ComfyUI配置"""
    try:
        config = ComfyUIConfigs.get_config()
        if not config:
            # 返回默认配置
            return ComfyUIConfigResponse(
                id="default",
                base_url="https://openapi.liblibai.cloud",
                enabled=False,
                timeout=300,
                max_concurrent_tasks=5,
            )

        return ComfyUIConfigResponse(**config.to_dict())

    except Exception as e:
        logger.error(f"获取ComfyUI配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}",
        )


@router.post("/admin/config", response_model=ComfyUIConfigResponse)
async def save_comfyui_config(
    config_form: ComfyUIConfigForm, admin_user=Depends(get_admin_user)
):
    """保存ComfyUI配置"""
    try:
        config = ComfyUIConfigs.create_or_update_config(config_form)
        return ComfyUIConfigResponse(**config.to_dict())

    except Exception as e:
        logger.error(f"保存ComfyUI配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置失败: {str(e)}",
        )


# ======================== 工作流管理接口 ========================


@router.get("/admin/workflows", response_model=List[ComfyUIWorkflowResponse])
async def get_all_workflows(admin_user=Depends(get_admin_user)):
    """获取所有工作流（管理员）"""
    try:
        workflows = ComfyUIWorkflows.get_all_workflows()
        return [ComfyUIWorkflowResponse(**workflow.to_dict()) for workflow in workflows]

    except Exception as e:
        logger.error(f"获取工作流列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流列表失败: {str(e)}",
        )


@router.post("/admin/workflows", response_model=ComfyUIWorkflowResponse)
async def create_workflow(
    workflow_form: ComfyUIWorkflowForm, admin_user=Depends(get_admin_user)
):
    """创建工作流"""
    try:
        # 处理封面图片上传
        if workflow_form.preview_image and workflow_form.preview_image.startswith(
            "data:image/"
        ):
            try:
                from open_webui.services.file_manager import get_file_manager

                file_manager = get_file_manager()

                # 生成文件名
                import uuid
                from datetime import datetime

                timestamp = int(datetime.now().timestamp())
                filename = (
                    f"comfyui_workflow_cover_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
                )

                # 上传图片到云存储
                success, message, file_record = (
                    await file_manager.save_generated_content(
                        user_id=admin_user.id,
                        file_data=None,
                        file_url=None,
                        filename=filename,
                        file_type="image",
                        source_type="comfyui_workflow",
                        source_task_id=None,
                        metadata={"workflow_name": workflow_form.name},
                    )
                )

                # 处理base64图片
                if workflow_form.preview_image.startswith("data:image/"):
                    import base64

                    header, encoded_data = workflow_form.preview_image.split(",", 1)
                    image_content = base64.b64decode(encoded_data)

                    success, message, file_record = (
                        await file_manager.save_generated_content(
                            user_id=admin_user.id,
                            file_data=image_content,
                            filename=filename,
                            file_type="image",
                            source_type="comfyui_workflow",
                            source_task_id=None,
                            metadata={"workflow_name": workflow_form.name},
                        )
                    )

                if success and file_record and file_record.cloud_url:
                    workflow_form.preview_image = file_record.cloud_url
                    logger.info(f"工作流封面图片上传成功: {file_record.cloud_url}")
                else:
                    logger.warning(f"工作流封面图片上传失败: {message}")

            except Exception as upload_error:
                logger.error(f"上传工作流封面图片时出错: {upload_error}")
                # 上传失败不阻止工作流创建，只记录警告

        workflow = ComfyUIWorkflows.create_workflow(workflow_form)
        return ComfyUIWorkflowResponse(**workflow.to_dict())

    except Exception as e:
        logger.error(f"创建工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建工作流失败: {str(e)}",
        )


@router.put("/admin/workflows/{workflow_id}", response_model=ComfyUIWorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_form: ComfyUIWorkflowForm,
    admin_user=Depends(get_admin_user),
):
    """更新工作流"""
    try:
        # 处理封面图片上传
        if workflow_form.preview_image and workflow_form.preview_image.startswith(
            "data:image/"
        ):
            try:
                from open_webui.services.file_manager import get_file_manager

                file_manager = get_file_manager()

                # 生成文件名
                import uuid
                from datetime import datetime

                timestamp = int(datetime.now().timestamp())
                filename = f"comfyui_workflow_cover_{workflow_id}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"

                # 处理base64图片
                import base64

                header, encoded_data = workflow_form.preview_image.split(",", 1)
                image_content = base64.b64decode(encoded_data)

                success, message, file_record = (
                    await file_manager.save_generated_content(
                        user_id=admin_user.id,
                        file_data=image_content,
                        filename=filename,
                        file_type="image",
                        source_type="comfyui_workflow",
                        source_task_id=workflow_id,
                        metadata={
                            "workflow_name": workflow_form.name,
                            "workflow_id": workflow_id,
                        },
                    )
                )

                if success and file_record and file_record.cloud_url:
                    workflow_form.preview_image = file_record.cloud_url
                    logger.info(f"工作流封面图片更新成功: {file_record.cloud_url}")
                else:
                    logger.warning(f"工作流封面图片更新失败: {message}")

            except Exception as upload_error:
                logger.error(f"更新工作流封面图片时出错: {upload_error}")
                # 上传失败不阻止工作流更新，只记录警告

        workflow = ComfyUIWorkflows.update_workflow(workflow_id, workflow_form)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="工作流不存在"
            )

        return ComfyUIWorkflowResponse(**workflow.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新工作流失败: {str(e)}",
        )


@router.delete("/admin/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, admin_user=Depends(get_admin_user)):
    """删除工作流"""
    try:
        success = ComfyUIWorkflows.delete_workflow(workflow_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="工作流不存在"
            )

        return {"success": True, "message": "工作流删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除工作流失败: {str(e)}",
        )


@router.post("/admin/workflows/import-samples")
async def import_sample_workflows(admin_user=Depends(get_admin_user)):
    """导入示例工作流"""
    try:
        workflows = ComfyUIWorkflowImporter.create_sample_workflows()
        return {
            "success": True,
            "message": f"成功导入 {len(workflows)} 个示例工作流",
            "workflows": [workflow.to_dict() for workflow in workflows],
        }

    except Exception as e:
        logger.error(f"导入示例工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入示例工作流失败: {str(e)}",
        )


# ======================== 用户工作流接口 ========================


@router.get("/workflows/public", response_model=List[ComfyUIWorkflowResponse])
async def get_public_workflows(category: Optional[str] = None):
    """获取公开工作流列表"""
    try:
        workflows = ComfyUIWorkflows.get_public_workflows(category)
        return [ComfyUIWorkflowResponse(**workflow.to_dict()) for workflow in workflows]

    except Exception as e:
        logger.error(f"获取公开工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公开工作流失败: {str(e)}",
        )


@router.get("/workflows/{workflow_id}/schema")
async def get_workflow_schema(workflow_id: str):
    """获取工作流参数结构"""
    try:
        workflow = ComfyUIWorkflows.get_workflow_by_id(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="工作流不存在"
            )

        if not workflow.is_public and not workflow.enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="工作流未公开"
            )

        return {
            "workflow": workflow.to_dict(),
            "parameter_schema": workflow.parameter_schema,
            "default_params": workflow.default_params,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流参数结构失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流参数结构失败: {str(e)}",
        )


# ======================== 任务管理接口 ========================


@router.post("/tasks", response_model=ComfyUITaskResponse)
async def submit_task(
    task_request: ComfyUITaskRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    """提交ComfyUI任务"""
    check_comfyui_enabled_dependency()

    try:
        # 获取工作流信息
        workflow = ComfyUIWorkflows.get_workflow_by_id(task_request.workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="工作流不存在"
            )

        if not workflow.enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="工作流已禁用"
            )

        # 计算积分消耗
        credits_needed = calculate_workflow_credits(workflow, task_request.input_params)

        # 检查用户积分
        user_credits = Credits.get_credit_by_user_id(user.id)
        if not user_credits or user_credits.credit < credits_needed:
            current_balance = user_credits.credit if user_credits else 0
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"积分不足，需要 {credits_needed} 积分，当前余额 {current_balance} 积分",
            )

        # 扣除积分
        from open_webui.models.credits import AddCreditForm, SetCreditFormDetail
        from decimal import Decimal

        deduct_form = AddCreditForm(
            user_id=user.id,
            amount=Decimal(-credits_needed),
            detail=SetCreditFormDetail(
                desc=f"ComfyUI工作流执行: {workflow.name}",
                api_path="/api/v1/comfyui/tasks",
                api_params={"workflow_id": task_request.workflow_id},
                usage={"credits_cost": credits_needed},
            ),
        )

        updated_credits = Credits.add_credit_by_user_id(deduct_form)
        if not updated_credits:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="扣除积分失败"
            )

        # 创建任务
        task = ComfyUITasks.create_task(
            user.id, task_request.workflow_id, task_request.input_params
        )

        # 更新积分消耗
        ComfyUITasks.update_task_status(task.id, "PENDING", credits_cost=credits_needed)

        # 后台提交任务到哩布API
        background_tasks.add_task(submit_task_to_liblib, task.id)

        # 重新获取任务信息
        task = ComfyUITasks.get_task_by_id(task.id)
        return ComfyUITaskResponse(**task.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交任务失败: {str(e)}",
        )


@router.get("/tasks/{task_id}", response_model=ComfyUITaskResponse)
async def get_task_status(task_id: str, user=Depends(get_current_user)):
    """获取任务状态"""
    try:
        task = ComfyUITasks.get_task_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 验证用户权限
        if task.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此任务"
            )

        # 如果任务正在进行中，检查最新状态
        if task.status in ["PENDING", "IN_PROGRESS", "PROCESSING"]:
            check_comfyui_task_status(task_id)
            # 重新获取任务信息
            task = ComfyUITasks.get_task_by_id(task_id)

        # 对于已完成的任务，检查是否需要补充云存储上传
        if (
            task
            and task.status == "SUCCESS"
            and not task.cloud_images
            and not task.cloud_videos
        ):
            if task.output_images or task.output_videos:
                logger.info(
                    f"🎯 检测到已完成任务 {task_id} 缺少云存储记录，触发云存储上传"
                )
                # 异步触发云存储上传，不阻塞API响应
                import asyncio

                asyncio.create_task(upload_results_to_cloud_storage(task))

        return ComfyUITaskResponse(**task.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态失败: {str(e)}",
        )


@router.get("/tasks", response_model=List[ComfyUITaskResponse])
async def get_user_tasks(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    user=Depends(get_current_user),
):
    """获取用户任务历史"""
    try:
        tasks = ComfyUITasks.get_user_tasks(user.id, page, limit, status)
        return [ComfyUITaskResponse(**task.to_dict()) for task in tasks]

    except Exception as e:
        logger.error(f"获取用户任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户任务失败: {str(e)}",
        )


@router.get("/history")
async def get_user_history(
    page: int = 1, limit: int = 20, user=Depends(get_current_user)
):
    """获取用户个人历史记录（只返回成功完成的任务）"""
    try:
        # 只获取成功完成的任务
        tasks = ComfyUITasks.get_user_tasks(user.id, page, limit, "SUCCESS")

        history_items = []
        for task in tasks:
            # 获取工作流信息
            workflow = ComfyUIWorkflows.get_workflow_by_id(task.workflow_id)
            workflow_name = workflow.name if workflow else "未知工作流"

            # 构建历史记录项
            history_item = {
                "id": task.id,
                "workflow_id": task.workflow_id,
                "workflow_name": workflow_name,
                "status": task.status,
                "credits_cost": task.credits_cost or 0,
                "generation_time": task.generation_time,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
                # 云存储结果（优先显示云存储，否则显示原始）
                "results": {
                    "images": (
                        task.cloud_images
                        if task.cloud_images
                        else (
                            [
                                {
                                    "cloud_url": img.get("imageUrl"),
                                    "original_url": img.get("imageUrl"),
                                }
                                for img in task.output_images
                            ]
                            if task.output_images
                            else []
                        )
                    ),
                    "videos": (
                        task.cloud_videos
                        if task.cloud_videos
                        else (
                            [
                                {
                                    "cloud_url": vid.get("videoUrl"),
                                    "cover_url": vid.get("coverPath"),
                                    "original_url": vid.get("videoUrl"),
                                }
                                for vid in task.output_videos
                            ]
                            if task.output_videos
                            else []
                        )
                    ),
                },
                # 输入参数摘要（用于显示）
                "input_summary": _get_input_summary(task.input_params),
            }

            history_items.append(history_item)

        return {
            "history": history_items,
            "page": page,
            "limit": limit,
            "total": len(history_items),
        }

    except Exception as e:
        logger.error(f"获取用户历史记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户历史记录失败: {str(e)}",
        )


def _get_input_summary(input_params: dict) -> str:
    """生成输入参数的简要摘要"""
    if not input_params:
        return ""

    summary_parts = []
    for key, value in input_params.items():
        if isinstance(value, str):
            if value.startswith("data:image/"):
                summary_parts.append(f"{key}: [图片]")
            elif len(value) > 50:
                summary_parts.append(f"{key}: {value[:50]}...")
            else:
                summary_parts.append(f"{key}: {value}")
        else:
            summary_parts.append(f"{key}: {value}")

    return " | ".join(summary_parts)


# ======================== 积分管理接口 ========================


@router.get("/credits")
async def get_user_credits(user=Depends(get_current_user)):
    """获取用户积分信息"""
    try:
        credits = Credits.get_credit_by_user_id(user.id)
        if not credits:
            credits = Credits.init_credit_by_user_id(user.id)

        return {
            "user_id": user.id,
            "credits_balance": int(credits.credit),
            "total_used": 0,  # 可以从日志计算或者不返回此字段
            "created_at": credits.created_at,
            "updated_at": credits.updated_at,
        }

    except Exception as e:
        logger.error(f"获取用户积分失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户积分失败: {str(e)}",
        )


@router.post("/admin/credits/add")
async def add_user_credits(
    user_id: str, amount: int, admin_user=Depends(get_admin_user)
):
    """给用户增加积分（管理员）"""
    try:
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="积分数量必须大于0"
            )

        from open_webui.models.credits import AddCreditForm, SetCreditFormDetail
        from decimal import Decimal

        add_form = AddCreditForm(
            user_id=user_id,
            amount=Decimal(amount),
            detail=SetCreditFormDetail(
                desc=f"管理员增加ComfyUI积分",
                api_path="/api/v1/comfyui/admin/credits/add",
                api_params={"admin_action": "add_credits"},
                usage={"credits_added": amount},
            ),
        )

        updated_credits = Credits.add_credit_by_user_id(add_form)
        if not updated_credits:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="增加积分失败"
            )

        return {
            "success": True,
            "message": f"成功给用户 {user_id} 增加 {amount} 积分",
            "credits": {
                "user_id": user_id,
                "credits_balance": int(updated_credits.credit),
                "updated_at": updated_credits.updated_at,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"增加用户积分失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"增加用户积分失败: {str(e)}",
        )


# ======================== 后台任务 ========================


async def submit_task_to_liblib(task_id: str):
    """后台任务：提交任务到哩布API"""
    logger.info(f"🚀 开始后台提交任务 {task_id} 到哩布API")
    try:
        success, message = await submit_comfyui_task(task_id)
        if not success:
            # 更新任务状态为失败
            ComfyUITasks.update_task_status(task_id, "FAILED", error_message=message)
            logger.error(f"❌ 任务 {task_id} 提交失败: {message}")

            # 提交失败时退还积分
            task = ComfyUITasks.get_task_by_id(task_id)
            if task and task.credits_cost:
                try:
                    from open_webui.models.credits import (
                        AddCreditForm,
                        SetCreditFormDetail,
                    )
                    from decimal import Decimal

                    add_form = AddCreditForm(
                        user_id=task.user_id,
                        amount=Decimal(task.credits_cost),
                        detail=SetCreditFormDetail(
                            desc=f"ComfyUI任务提交失败退还积分: {message}",
                            api_path="/api/v1/comfyui/tasks",
                            api_params={"task_id": task_id, "action": "refund"},
                            usage={"credits_refunded": task.credits_cost},
                        ),
                    )

                    updated_credits = Credits.add_credit_by_user_id(add_form)
                    if updated_credits:
                        logger.info(
                            f"💰 任务 {task_id} 提交失败，已退还 {task.credits_cost} 积分给用户 {task.user_id}"
                        )
                    else:
                        logger.error(f"💰 任务 {task_id} 提交失败，退还积分失败")
                except Exception as refund_error:
                    logger.error(
                        f"💰 任务 {task_id} 提交失败，退还积分时出错: {refund_error}"
                    )
        else:
            logger.info(f"✅ 任务 {task_id} 提交成功: {message}")

            # 开始监控任务状态
            logger.info(f"🔍 启动任务 {task_id} 状态监控")
            asyncio.create_task(monitor_task_status(task_id))

    except Exception as e:
        logger.error(f"❌ 后台提交任务 {task_id} 失败: {e}")
        import traceback

        logger.error(f"❌ 提交任务异常堆栈: {traceback.format_exc()}")
        ComfyUITasks.update_task_status(task_id, "FAILED", error_message=str(e))

        # 异常时退还积分
        task = ComfyUITasks.get_task_by_id(task_id)
        if task and task.credits_cost:
            try:
                from open_webui.models.credits import AddCreditForm, SetCreditFormDetail
                from decimal import Decimal

                add_form = AddCreditForm(
                    user_id=task.user_id,
                    amount=Decimal(task.credits_cost),
                    detail=SetCreditFormDetail(
                        desc=f"ComfyUI任务异常退还积分: {str(e)[:100]}",
                        api_path="/api/v1/comfyui/tasks",
                        api_params={"task_id": task_id, "action": "refund"},
                        usage={"credits_refunded": task.credits_cost},
                    ),
                )

                updated_credits = Credits.add_credit_by_user_id(add_form)
                if updated_credits:
                    logger.info(
                        f"💰 任务 {task_id} 异常，已退还 {task.credits_cost} 积分给用户 {task.user_id}"
                    )
                else:
                    logger.error(f"💰 任务 {task_id} 异常，退还积分失败")
            except Exception as refund_error:
                logger.error(f"💰 任务 {task_id} 异常，退还积分时出错: {refund_error}")


async def monitor_task_status(task_id: str):
    """后台任务：监控任务状态"""
    max_attempts = 60  # 最大检查次数
    check_interval = 10  # 检查间隔（秒）

    logger.info(
        f"🔍 开始监控任务 {task_id}，最大尝试次数: {max_attempts}，检查间隔: {check_interval}秒"
    )

    for attempt in range(max_attempts):
        try:
            await asyncio.sleep(check_interval)

            task = ComfyUITasks.get_task_by_id(task_id)
            if not task or task.status in ["SUCCESS", "FAILED", "CANCELLED"]:
                break

            # 检查任务状态
            check_comfyui_task_status(task_id)

            # 重新获取任务状态
            task = ComfyUITasks.get_task_by_id(task_id)
            if task and task.status == "SUCCESS":
                logger.info(f"✅ 任务 {task_id} 完成，开始上传到云存储")
                logger.info(
                    f"📊 任务状态详情: output_images={len(task.output_images) if task.output_images else 0}, output_videos={len(task.output_videos) if task.output_videos else 0}"
                )

                # 上传结果到云存储
                try:
                    await upload_results_to_cloud_storage(task)
                    logger.info(f"🌥️ 任务 {task_id} 云存储上传处理完成")
                except Exception as e:
                    logger.error(f"❌ 任务 {task_id} 云存储上传失败: {e}")
                break

        except Exception as e:
            logger.error(f"监控任务 {task_id} 状态失败: {e}")

    # 如果超时仍未完成，标记为失败
    task = ComfyUITasks.get_task_by_id(task_id)
    if task and task.status not in ["SUCCESS", "FAILED", "CANCELLED"]:
        ComfyUITasks.update_task_status(task_id, "FAILED", error_message="任务执行超时")
        logger.warning(f"任务 {task_id} 执行超时")

        # 超时时退还积分
        if task.credits_cost:
            try:
                from open_webui.models.credits import AddCreditForm, SetCreditFormDetail
                from decimal import Decimal

                add_form = AddCreditForm(
                    user_id=task.user_id,
                    amount=Decimal(task.credits_cost),
                    detail=SetCreditFormDetail(
                        desc="ComfyUI任务超时退还积分",
                        api_path="/api/v1/comfyui/tasks",
                        api_params={"task_id": task_id, "action": "refund"},
                        usage={"credits_refunded": task.credits_cost},
                    ),
                )

                updated_credits = Credits.add_credit_by_user_id(add_form)
                if updated_credits:
                    logger.info(
                        f"💰 任务 {task_id} 超时，已退还 {task.credits_cost} 积分给用户 {task.user_id}"
                    )
                else:
                    logger.error(f"💰 任务 {task_id} 超时，退还积分失败")
            except Exception as refund_error:
                logger.error(f"💰 任务 {task_id} 超时，退还积分时出错: {refund_error}")


async def upload_image_to_comfyui_cloud(
    image_data: str, user_id: str, task_id: str
) -> Optional[str]:
    """上传ComfyUI图片到云存储"""
    try:
        from open_webui.services.file_manager import get_file_manager
        import uuid
        from datetime import datetime

        file_manager = get_file_manager()

        # 生成文件名
        timestamp = int(datetime.now().timestamp())
        filename = f"comfyui_{task_id}_{timestamp}_{uuid.uuid4().hex[:8]}"

        if image_data.startswith("http"):
            # URL图片，使用文件管理器的save_generated_content方法
            success, message, file_record = await file_manager.save_generated_content(
                user_id=user_id,
                file_url=image_data,
                filename=filename,
                file_type="image",
                source_type="comfyui",
                source_task_id=task_id,
                metadata={"input_type": "image", "from_url": True},
            )

            if success and file_record and file_record.cloud_url:
                logger.info(f"📁 ComfyUI图片上传成功: {file_record.cloud_url}")
                return file_record.cloud_url
            else:
                logger.warning(f"📁 ComfyUI图片上传失败: {message}")
                return image_data  # 返回原始URL

        elif image_data.startswith("data:image/"):
            # Base64图片，先解码再上传
            import base64

            header, encoded_data = image_data.split(",", 1)
            image_content = base64.b64decode(encoded_data)

            # 从header确定文件扩展名
            if "png" in header:
                filename += ".png"
            else:
                filename += ".jpg"

            success, message, file_record = await file_manager.save_generated_content(
                user_id=user_id,
                file_data=image_content,
                filename=filename,
                file_type="image",
                source_type="comfyui",
                source_task_id=task_id,
                metadata={"input_type": "image", "from_base64": True},
            )

            if success and file_record and file_record.cloud_url:
                logger.info(f"📁 ComfyUI图片上传成功: {file_record.cloud_url}")
                return file_record.cloud_url
            else:
                logger.warning(f"📁 ComfyUI图片上传失败: {message}")
                return None
        else:
            logger.error("📁 ComfyUI不支持的图片格式")
            return None

    except Exception as e:
        logger.error(f"📁 ComfyUI图片上传失败: {str(e)}")
        return None


async def upload_results_to_cloud_storage(task):
    """上传任务结果到云存储"""
    try:

        logger.info(f"🔄 开始为任务 {task.id} 执行云存储上传")
        logger.info(
            f"🔄 任务输出图片数量: {len(task.output_images) if task.output_images else 0}"
        )
        logger.info(
            f"🔄 任务输出视频数量: {len(task.output_videos) if task.output_videos else 0}"
        )

        # 直接打印任务的输出图片内容，用于调试
        if task.output_images:
            logger.info(
                f"🔄 输出图片数据预览: {task.output_images[:1]}"
            )  # 只显示第一个
        if task.output_videos:
            logger.info(
                f"🔄 输出视频数据预览: {task.output_videos[:1]}"
            )  # 只显示第一个

        cloud_images = []
        cloud_videos = []

        # 上传图片到云存储
        if task.output_images:
            logger.info(f"📸 开始上传任务 {task.id} 的图片结果到云存储")
            for i, image_data in enumerate(task.output_images):
                if isinstance(image_data, dict) and "imageUrl" in image_data:
                    try:
                        # 从哩布下载图片然后上传到我们的云存储
                        import requests
                        import base64

                        logger.info(f"📥 开始下载图片 {i}: {image_data['imageUrl']}")
                        response = requests.get(image_data["imageUrl"], timeout=30)
                        if response.status_code == 200:
                            logger.info(
                                f"📥 图片 {i} 下载成功，大小: {len(response.content)} bytes"
                            )

                            # 转换为base64格式
                            image_base64 = base64.b64encode(response.content).decode()
                            mime_type = response.headers.get(
                                "content-type", "image/png"
                            )
                            data_url = f"data:{mime_type};base64,{image_base64}"

                            # 上传到我们的云存储
                            logger.info(f"☁️ 开始上传图片 {i} 到云存储")
                            cloud_url = await upload_image_to_comfyui_cloud(
                                data_url, task.user_id, f"{task.id}_img_{i}"
                            )

                            if cloud_url:
                                cloud_images.append(
                                    {
                                        "original_url": image_data["imageUrl"],
                                        "cloud_url": cloud_url,
                                        "node_id": image_data.get("nodeId"),
                                        "output_name": image_data.get("outputName"),
                                        "audit_status": image_data.get("auditStatus"),
                                    }
                                )
                                logger.info(f"✅ 图片 {i} 上传云存储成功: {cloud_url}")
                            else:
                                logger.warning(
                                    f"❌ 图片 {i} 上传云存储失败，使用原始URL"
                                )
                                # 如果云存储上传失败，至少保存原始URL
                                cloud_images.append(
                                    {
                                        "original_url": image_data["imageUrl"],
                                        "cloud_url": image_data["imageUrl"],
                                        "node_id": image_data.get("nodeId"),
                                        "output_name": image_data.get("outputName"),
                                        "audit_status": image_data.get("auditStatus"),
                                    }
                                )
                        else:
                            logger.error(
                                f"❌ 下载图片 {i} 失败，HTTP状态码: {response.status_code}"
                            )
                    except Exception as e:
                        logger.error(f"❌ 处理图片 {i} 失败: {e}")
                        # 即使处理失败，也保存原始URL作为备份
                        cloud_images.append(
                            {
                                "original_url": image_data["imageUrl"],
                                "cloud_url": image_data["imageUrl"],
                                "node_id": image_data.get("nodeId"),
                                "output_name": image_data.get("outputName"),
                                "audit_status": image_data.get("auditStatus"),
                            }
                        )

        # 上传视频到云存储
        if task.output_videos:
            logger.info(f"🎬 开始处理任务 {task.id} 的视频结果")
            for i, video_data in enumerate(task.output_videos):
                if isinstance(video_data, dict) and "videoUrl" in video_data:
                    try:
                        # TODO: 实现真正的视频下载和云存储上传
                        # 视频文件比较大，暂时直接保存原始URL
                        # 后续可以实现异步视频下载和上传逻辑

                        logger.info(f"🎬 处理视频 {i}: {video_data['videoUrl']}")
                        cloud_videos.append(
                            {
                                "original_url": video_data["videoUrl"],
                                "cloud_url": video_data[
                                    "videoUrl"
                                ],  # 暂时使用原始URL，后续实现真正的云存储
                                "cover_url": video_data.get("coverPath"),
                                "node_id": video_data.get("nodeId"),
                                "output_name": video_data.get("outputName"),
                                "audit_status": video_data.get("auditStatus"),
                            }
                        )
                        logger.info(f"✅ 视频 {i} 记录保存成功")
                    except Exception as e:
                        logger.error(f"❌ 处理视频 {i} 失败: {e}")
                        # 保存原始URL作为备份
                        cloud_videos.append(
                            {
                                "original_url": video_data["videoUrl"],
                                "cloud_url": video_data["videoUrl"],
                                "cover_url": video_data.get("coverPath"),
                                "node_id": video_data.get("nodeId"),
                                "output_name": video_data.get("outputName"),
                                "audit_status": video_data.get("auditStatus"),
                            }
                        )

        # 更新任务的云存储字段
        if cloud_images or cloud_videos:
            logger.info(
                f"📝 准备更新数据库，cloud_images数量: {len(cloud_images)}, cloud_videos数量: {len(cloud_videos)}"
            )
            success = ComfyUITasks.update_task_status(
                task.id,
                task.status,
                cloud_images=cloud_images if cloud_images else None,
                cloud_videos=cloud_videos if cloud_videos else None,
            )
            if success:
                logger.info(
                    f"✅ 任务 {task.id} 云存储记录更新成功: {len(cloud_images)} 图片, {len(cloud_videos)} 视频"
                )
            else:
                logger.error(f"❌ 任务 {task.id} 云存储记录更新失败")
        else:
            logger.warning(f"⚠️ 任务 {task.id} 没有云存储内容需要更新")

    except Exception as e:
        logger.error(f"❌ 上传任务 {task.id} 结果到云存储失败: {e}")
        import traceback

        logger.error(f"❌ 云存储上传异常堆栈: {traceback.format_exc()}")


# ======================== 工具接口 ========================


@router.post("/tasks/{task_id}/upload-to-cloud")
async def manual_upload_to_cloud(task_id: str, user=Depends(get_current_user)):
    """手动触发任务结果上传到云存储"""
    try:
        task = ComfyUITasks.get_task_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 验证用户权限
        if task.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此任务"
            )

        # 检查任务状态
        if task.status != "SUCCESS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能为已完成的任务上传云存储",
            )

        if not task.output_images and not task.output_videos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="任务没有生成结果"
            )

        logger.info(f"🔧 手动触发任务 {task_id} 云存储上传")

        # 异步触发云存储上传
        import asyncio

        asyncio.create_task(upload_results_to_cloud_storage(task))

        return {"success": True, "message": "云存储上传已启动", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动触发云存储上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"云存储上传失败: {str(e)}",
        )


@router.get("/status")
async def get_comfyui_status():
    """获取ComfyUI服务状态"""
    try:
        config = ComfyUIConfigs.get_config()
        return {
            "enabled": config.enabled if config else False,
            "configured": config is not None,
            "api_available": is_comfyui_enabled(),
        }

    except Exception as e:
        logger.error(f"获取ComfyUI状态失败: {e}")
        return {
            "enabled": False,
            "configured": False,
            "api_available": False,
            "error": str(e),
        }
