"""
Midjourney API Router
实现完整的Midjourney绘画功能，包括任务提交、查询、动作执行等
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import json
import asyncio
from datetime import datetime, timedelta
import uuid

from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.config import CACHE_DIR
from open_webui.internal.db import get_db
from open_webui.models.midjourney import (
    MJConfig,
    MJTask,
    MJConfigForm,
    MJTaskForm,
    MJGenerateRequest,
    MJActionRequest,
    MJModalRequest,
)
from open_webui.utils.midjourney import (
    MJApiClient,
    deduct_user_credits,
    add_user_credits,
    get_user_credit_balance,
    validate_user_credits,
)
from open_webui.services.file_manager import get_file_manager

router = APIRouter(prefix="/midjourney", tags=["midjourney"])

# 全局变量存储MJ配置
mj_config = None
mj_client = None


def get_mj_client():
    """获取MJ API客户端"""
    global mj_client, mj_config
    if not mj_client or not mj_config:
        config = MJConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(
                status_code=400, detail="Midjourney service not configured or disabled"
            )
        mj_client = MJApiClient(config)
        mj_config = config
    return mj_client


# ======================== 配置管理 ========================


@router.get("/config")
async def get_mj_config(user=Depends(get_admin_user)):
    """获取MJ配置 - 管理员专用"""
    config = MJConfig.get_config()
    if not config:
        # 返回默认配置
        return {
            "enabled": False,
            "base_url": "",
            "api_key": "",
            "modes": {
                "turbo": {"enabled": True, "credits": 10},
                "fast": {"enabled": True, "credits": 5},
                "relax": {"enabled": True, "credits": 2},
            },
            "default_mode": "fast",
            "max_concurrent_tasks": 5,
            "task_timeout": 300000,
        }
    return config.to_dict()


@router.get("/config/user")
async def get_mj_user_config(user=Depends(get_verified_user)):
    """获取MJ用户配置 - 只返回用户需要的配置信息（不包含敏感信息）"""
    config = MJConfig.get_config()
    if not config:
        # 返回默认用户配置
        return {
            "enabled": False,
            "modes": {
                "turbo": {"enabled": True, "credits": 10},
                "fast": {"enabled": True, "credits": 5},
                "relax": {"enabled": True, "credits": 2},
            },
            "default_mode": "fast",
            "stream_enabled": False,  # 服务未配置时禁用流式
            "stream_url": "/api/v1/midjourney/stream/user",  # 流式端点URL
        }

    # 只返回用户需要的配置，不包含敏感信息
    return {
        "enabled": config.enabled,
        "modes": config.modes,
        "default_mode": config.default_mode,
        "stream_enabled": True,  # 指示流式功能已启用
        "stream_url": "/api/v1/midjourney/stream/user",  # 流式端点URL
    }


@router.post("/config")
async def save_mj_config(config_data: dict, user=Depends(get_admin_user)):
    """保存MJ配置 - 管理员专用"""
    global mj_client, mj_config

    try:
        # 验证必需字段
        enabled = config_data.get("enabled", False)
        if enabled and (
            not config_data.get("base_url") or not config_data.get("api_key")
        ):
            raise HTTPException(
                status_code=400, detail="Base URL and API Key are required when enabled"
            )

        # 确保modes字段存在且格式正确
        if "modes" not in config_data:
            config_data["modes"] = {
                "turbo": {"enabled": True, "credits": 10},
                "fast": {"enabled": True, "credits": 5},
                "relax": {"enabled": True, "credits": 2},
            }

        # 设置默认值
        config_data.setdefault("default_mode", "fast")
        config_data.setdefault("max_concurrent_tasks", 5)
        config_data.setdefault("task_timeout", 300000)

        # 保存配置
        config = MJConfig.save_config(config_data)

        # 重置客户端
        mj_client = None
        mj_config = None

        return {
            "message": "Configuration saved successfully",
            "config": config.to_dict(),
        }
    except Exception as e:
        import traceback

        print(f"Error saving MJ config: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to save configuration: {str(e)}"
        )


@router.get("/test")
async def test_mj_connection(user=Depends(get_admin_user)):
    """测试MJ连接 - 管理员专用"""
    try:
        # 检查配置是否存在
        config = MJConfig.get_config()
        if not config:
            raise HTTPException(
                status_code=400, detail="Midjourney service not configured"
            )

        if not config.enabled:
            raise HTTPException(
                status_code=400, detail="Midjourney service is disabled"
            )

        if not config.base_url or not config.api_key:
            raise HTTPException(
                status_code=400, detail="Base URL and API Key are required"
            )

        # 创建客户端并测试连接
        client = MJApiClient(config)

        # 简单测试 - 检查API可达性
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            try:
                response = await http_client.get(
                    f"{config.base_url.rstrip('/')}/mj",
                    headers={"Authorization": f"Bearer {config.api_key}"},
                )
                # 如果API返回任何响应（即使是错误），说明连接成功
                return {
                    "message": "Connection test successful",
                    "status_code": response.status_code,
                }
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=400, detail="Cannot connect to Midjourney API server"
                )
            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=400, detail="Connection to Midjourney API timed out"
                )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


# ======================== 任务提交 ========================


@router.post("/submit/imagine")
async def submit_imagine_task(
    request: MJGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """提交文生图任务"""
    try:
        client = get_mj_client()

        # 获取最新配置并验证用户积分
        config = MJConfig.get_config()
        if not config or not config.modes:
            raise HTTPException(
                status_code=400, detail="Midjourney configuration not found"
            )

        mode_credits = config.modes.get(request.mode, {}).get("credits", 5)
        if not validate_user_credits(user.id, mode_credits):
            raise HTTPException(status_code=400, detail="Insufficient credits")

        # 扣除积分
        deduct_user_credits(user.id, mode_credits, f"MJ-{request.mode}-imagine")

        # 构建完整prompt
        final_prompt = client.build_prompt(request)

        # 🔥 准备参考图片数据 - 支持不同类型和权重
        imagine_data = {"prompt": final_prompt, "mode": request.mode}

        # 如果有参考图片，添加到请求中
        if request.reference_images:
            print(f"🖼️ 【后端调试】准备发送 {len(request.reference_images)} 张参考图片")

            # 检查每张图片的数据
            for i, img in enumerate(request.reference_images):
                base64_preview = (
                    img.base64[:50] + "..." if len(img.base64) > 50 else img.base64
                )
                print(
                    f"🖼️ 【后端调试】图片{i+1}: 类型={img.type}, 权重={img.weight}, Base64={base64_preview}"
                )

            # 方式1: 标准base64Array（兼容性最好）
            imagine_data["base64Array"] = [
                img.base64 for img in request.reference_images
            ]

            # 方式2: 详细的图片信息（如果API支持）
            imagine_data["referenceImages"] = [
                {"base64": img.base64, "weight": img.weight, "type": img.type}
                for img in request.reference_images
            ]

            # 方式3: 权重数组（某些API支持）
            weights = [img.weight for img in request.reference_images]
            if any(w != 1.0 for w in weights):  # 只有在有非默认权重时才添加
                imagine_data["imageWeights"] = weights

            print(
                f"🖼️ 【后端调试】发送数据: base64Array={len(imagine_data['base64Array'])}, imageWeights={imagine_data.get('imageWeights')}"
            )
            print(f"🖼️ 【后端调试】最终请求数据keys: {list(imagine_data.keys())}")

        # 提交任务
        mj_response = await client.submit_imagine(imagine_data)

        if mj_response["code"] == 1:
            # 创建本地任务记录
            task = MJTask.create_task(
                id=mj_response["result"],
                user_id=user.id,
                action="IMAGINE",
                prompt=request.prompt,
                mode=request.mode,
                credits_cost=mode_credits,
                mj_response=mj_response,
            )

            # 后台轮询任务状态
            background_tasks.add_task(poll_task_status, mj_response["result"], user.id)

            return mj_response
        else:
            # 任务提交失败，退还积分
            add_user_credits(user.id, mode_credits, f"MJ-{request.mode}-imagine-refund")
            return mj_response

    except HTTPException:
        raise
    except Exception as e:
        # 发生错误时退还积分
        mode_credits = mj_config.modes.get(request.mode, {}).get("credits", 5)
        add_user_credits(
            user.id, mode_credits, f"MJ-{request.mode}-imagine-error-refund"
        )
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.post("/submit/blend")
async def submit_blend_task(
    request: dict, background_tasks: BackgroundTasks, user=Depends(get_verified_user)
):
    """提交图片混合任务"""
    try:
        client = get_mj_client()

        # 获取最新配置，默认使用fast模式的积分
        config = MJConfig.get_config()
        if not config or not config.modes:
            raise HTTPException(
                status_code=400, detail="Midjourney configuration not found"
            )

        mode_credits = config.modes.get("fast", {}).get("credits", 5)
        if not validate_user_credits(user.id, mode_credits):
            raise HTTPException(status_code=400, detail="Insufficient credits")

        deduct_user_credits(user.id, mode_credits, "MJ-blend")

        mj_response = await client.submit_blend(request)

        if mj_response["code"] == 1:
            task = MJTask.create_task(
                id=mj_response["result"],
                user_id=user.id,
                action="BLEND",
                prompt="Blend images",
                mode="fast",
                credits_cost=mode_credits,
                mj_response=mj_response,
            )

            background_tasks.add_task(poll_task_status, mj_response["result"], user.id)
            return mj_response
        else:
            add_user_credits(user.id, mode_credits, "MJ-blend-refund")
            return mj_response

    except HTTPException:
        raise
    except Exception as e:
        add_user_credits(user.id, mode_credits, "MJ-blend-error-refund")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit blend task: {str(e)}"
        )


@router.post("/submit/describe")
async def submit_describe_task(
    request: dict, background_tasks: BackgroundTasks, user=Depends(get_verified_user)
):
    """提交图生文任务"""
    try:
        client = get_mj_client()

        # 获取最新配置，图生文使用固定积分（可配置）
        config = MJConfig.get_config()
        mode_credits = 1  # describe固定使用1积分
        if not validate_user_credits(user.id, mode_credits):
            raise HTTPException(status_code=400, detail="Insufficient credits")

        deduct_user_credits(user.id, mode_credits, "MJ-describe")

        mj_response = await client.submit_describe(request)

        if mj_response["code"] == 1:
            task = MJTask.create_task(
                id=mj_response["result"],
                user_id=user.id,
                action="DESCRIBE",
                prompt="Describe image",
                mode="fast",
                credits_cost=mode_credits,
                mj_response=mj_response,
            )

            background_tasks.add_task(poll_task_status, mj_response["result"], user.id)
            return mj_response
        else:
            add_user_credits(user.id, mode_credits, "MJ-describe-refund")
            return mj_response

    except HTTPException:
        raise
    except Exception as e:
        add_user_credits(user.id, mode_credits, "MJ-describe-error-refund")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit describe task: {str(e)}"
        )


# ======================== 任务操作 ========================


@router.post("/submit/action")
async def submit_action_task(
    request: MJActionRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """执行任务动作（U1-U4, V1-V4等）"""
    try:
        client = get_mj_client()

        # 验证任务所有权
        task = MJTask.get_task_by_id(request.task_id)
        if not task or task.user_id != user.id:
            raise HTTPException(
                status_code=404, detail="Task not found or access denied"
            )

        # 动作通常不额外收费，但可以根据需要调整
        mode_credits = 0

        mj_response = await client.submit_action(
            {"taskId": request.task_id, "customId": request.custom_id}
        )

        if mj_response["code"] == 1:
            # 创建新的子任务记录
            new_task = MJTask.create_task(
                id=mj_response["result"],
                user_id=user.id,
                action="ACTION",
                prompt=f"Action on {request.task_id}",
                mode=task.mode,
                credits_cost=mode_credits,
                mj_response=mj_response,
                parent_task_id=request.task_id,
            )

            background_tasks.add_task(poll_task_status, mj_response["result"], user.id)
            return mj_response
        else:
            return mj_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit action: {str(e)}"
        )


@router.post("/submit/modal")
async def submit_modal_task(
    request: MJModalRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """提交Modal确认任务"""
    try:
        client = get_mj_client()

        # 验证任务所有权
        task = MJTask.get_task_by_id(request.task_id)
        if not task or task.user_id != user.id:
            raise HTTPException(
                status_code=404, detail="Task not found or access denied"
            )

        mj_response = await client.submit_modal(
            {
                "taskId": request.task_id,
                "prompt": request.prompt or "",
                "maskBase64": request.mask_base64 or "",
            }
        )

        if mj_response["code"] == 1:
            # 更新原任务状态
            task.update_status("IN_PROGRESS")
            background_tasks.add_task(poll_task_status, mj_response["result"], user.id)
            return mj_response
        else:
            return mj_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit modal: {str(e)}")


# ======================== 任务查询 ========================


@router.get("/task/{task_id}")
async def get_task_status(task_id: str, user=Depends(get_verified_user)):
    """获取任务状态 - 修复版本"""
    try:
        print(
            f"🔍 【API修复版】获取任务状态: {task_id}, 用户: {user.id if user else 'None'}"
        )

        # 先查本地数据库
        task = MJTask.get_task_by_id(task_id)
        print(
            f"🔍 【API修复版】本地任务: {task.id if task else 'None'}, 状态: {task.status if task else 'None'}"
        )

        # 🔥 强制返回本地数据（如果存在且正确）
        if task and task.image_url and task.status == "SUCCESS":
            print(f"🔥 【API修复版】直接返回本地完成任务: {task.id}")
            result = task.to_dict()
            print(
                f"🔥 【API修复版】返回数据: status={result.get('status')}, imageUrl={bool(result.get('imageUrl'))}, progress={result.get('progress')}"
            )
            return result

        # 查询远程最新状态
        try:
            client = get_mj_client()
            mj_task = await client.get_task_status(task_id)
            print(
                f"🔍 【API修复版】远程状态: {mj_task.get('status') if mj_task else 'None'}, 图片: {bool(mj_task.get('imageUrl')) if mj_task else False}"
            )
        except Exception as e:
            print(f"⚠️ 【API修复版】远程查询失败: {e}")
            mj_task = None

        if mj_task:
            # 🔥 强制更新本地记录
            if task:
                print(f"🔥 【API修复版】强制更新数据库 - 任务ID: {task.id}")
                # 如果有图片URL，强制设置为SUCCESS
                image_url = mj_task.get("imageUrl", "")
                status = mj_task.get("status", "UNKNOWN")
                if image_url:
                    print(f"🖼️ 【API修复版】发现图片URL，强制完成: {image_url[:50]}...")
                    mj_task_copy = mj_task.copy()
                    mj_task_copy["status"] = "SUCCESS"
                    mj_task_copy["progress"] = "100%"
                    task.update_from_mj_response(mj_task_copy)
                else:
                    task.update_from_mj_response(mj_task)
                result = task.to_dict()
                print(
                    f"🔥 【API修复版】数据库已更新: status={result.get('status')}, imageUrl={bool(result.get('imageUrl'))}, progress={result.get('progress')}"
                )
                return result
            else:
                # 🔥 如果本地没有任务，创建一个新的任务记录
                print(f"🔥 【API修复版】本地没有任务记录，创建新的任务: {task_id}")
                image_url = (
                    mj_task.get("imageUrl")
                    or mj_task.get("image_url")
                    or mj_task.get("url")
                )
                status = mj_task.get("status", "UNKNOWN")
                progress = mj_task.get("progress", "0%")

                # 如果有图片URL，强制设置为SUCCESS
                if image_url:
                    print(f"🖼️ 【API修复版】远程有图片，强制设置为SUCCESS")
                    status = "SUCCESS"
                    progress = "100%"

                # 🔥 创建新的任务记录到数据库
                try:
                    new_task = MJTask.create_task(
                        id=task_id,
                        user_id=user.id,
                        action="IMAGINE",
                        prompt=mj_task.get("prompt", ""),
                        mode="fast",
                        credits_cost=0,
                        mj_response=mj_task,
                    )
                    print(f"🔥 【API修复版】已创建新任务记录: {new_task.id}")
                    # 再次更新以确保状态正确
                    if image_url:
                        final_data = {
                            "status": "SUCCESS",
                            "progress": "100%",
                            "imageUrl": image_url,
                            "failReason": mj_task.get("failReason"),
                            "properties": mj_task.get("properties", {}),
                            "buttons": mj_task.get("buttons", []),
                        }
                        new_task.update_from_mj_response(final_data)
                    return new_task.to_dict()
                except Exception as e:
                    print(f"🔥 【API修复版】创建任务记录失败: {e}")

                # 如果创建失败，返回标准化数据
                standardized = {
                    "id": mj_task.get("id", task_id),
                    "status": status,
                    "progress": progress,
                    "imageUrl": image_url,
                    "prompt": mj_task.get("prompt", ""),
                    "failReason": mj_task.get("failReason")
                    or mj_task.get("fail_reason"),
                    "properties": mj_task.get("properties", {}),
                    "buttons": mj_task.get("buttons", []),
                }
                print(f"🔄 【API修复版】返回标准化数据: {standardized}")
                return standardized
        else:
            # 如果远程也没有，返回本地记录
            if task:
                print(f"🔄 【API修复版】返回本地记录: {task.id}")
                return task.to_dict()
            else:
                print(f"❌ 【API修复版】任务不存在: {task_id}")
                raise HTTPException(status_code=404, detail="Task not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【API修复版】获取任务状态失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/task/{task_id}/image-seed")
async def get_task_image_seed(task_id: str, user=Depends(get_verified_user)):
    """获取任务图片的seed"""
    try:
        # 验证任务所有权
        task = MJTask.get_task_by_id(task_id)
        if not task or task.user_id != user.id:
            raise HTTPException(
                status_code=404, detail="Task not found or access denied"
            )

        client = get_mj_client()
        result = await client.get_image_seed(task_id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get image seed: {str(e)}"
        )


# ======================== 用户功能 ========================


@router.get("/history")
async def get_user_task_history(
    page: int = 1, limit: int = 20, user=Depends(get_verified_user)
):
    """获取用户任务历史"""
    try:
        tasks = MJTask.get_user_tasks(user.id, page, limit)
        total = MJTask.get_user_task_count(user.id)

        return {
            "data": [task.to_dict() for task in tasks],
            "total": total,
            "page": page,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task history: {str(e)}"
        )


@router.get("/credits")
async def get_user_credits(user=Depends(get_verified_user)):
    """获取用户积分余额"""
    try:
        balance = get_user_credit_balance(user.id)
        return {"balance": balance}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get credits: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_task(task_id: str, user=Depends(get_verified_user)):
    """删除用户任务"""
    try:
        # 验证任务所有权
        task = MJTask.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 删除任务记录
        with get_db() as db:
            db.delete(task)
            db.commit()

        return {"message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


@router.post("/fix-tasks")
async def fix_task_states(user=Depends(get_verified_user)):
    """修复用户的任务状态 - 强制修复版本"""
    try:
        fixed_count = 0
        remote_checked = 0
        tasks = MJTask.get_user_tasks(user.id, 1, 100)  # 获取最近100个任务

        print(
            f"🔧 【强制修复版】开始修复用户 {user.id} 的任务状态，共 {len(tasks)} 个任务"
        )

        for task in tasks:
            needs_fix = False
            old_status = task.status
            old_progress = task.progress
            old_image_url = task.image_url

            print(
                f"🔧 【强制修复版】检查任务 {task.id}: 状态={task.status}, 进度={task.progress}, 图片={bool(task.image_url)}"
            )

            # 🔥 对于所有非失败的任务，都查询一次远程状态
            if (
                task.status not in ["SUCCESS", "FAILURE", "FAILED"]
                or not task.image_url
            ):
                try:
                    print(f"🔧 【强制修复版】查询远程状态: {task.id}")
                    client = get_mj_client()
                    mj_task = await client.get_task_status(task.id)
                    remote_checked += 1

                    if mj_task:
                        remote_image = mj_task.get("imageUrl")
                        remote_status = mj_task.get("status", "UNKNOWN")

                        print(
                            f"🔧 【强制修复版】远程状态: {task.id} - 状态={remote_status}, 图片={bool(remote_image)}"
                        )

                        # 如果远程有图片，直接修复
                        if remote_image:
                            needs_fix = True
                            task.image_url = remote_image
                            print(f"🔧 【强制修复版】发现远程图片: {task.id}")
                        # 如果远程状态更新了，也修复
                        elif remote_status in ["SUCCESS", "FAILURE", "FAILED"]:
                            needs_fix = True
                            print(
                                f"🔧 【强制修复版】远程状态已完成: {task.id} -> {remote_status}"
                            )

                except Exception as e:
                    print(f"🔧 【强制修复版】查询远程状态失败: {task.id} - {e}")

            # 条件1: 有图片URL但状态不是完成状态
            if task.image_url and task.status not in ["SUCCESS", "FAILURE", "FAILED"]:
                needs_fix = True
                print(
                    f"🔧 【强制修复版】发现异常: 任务 {task.id} 有图片但状态为 {task.status}"
                )

            # 条件2: 有图片但进度不是100%
            elif task.image_url and task.progress != "100%":
                needs_fix = True
                print(
                    f"🔧 【强制修复版】发现异常: 任务 {task.id} 有图片但进度为 {task.progress}"
                )

            if needs_fix:
                try:
                    with get_db() as db:
                        # 🔥 强制修复
                        if task.image_url:
                            task.status = "SUCCESS"
                            task.progress = "100%"
                        else:
                            # 没有图片的任务，检查是否应该标记为失败
                            task.status = "FAILURE"
                            task.fail_reason = "No image generated"
                            task.progress = "0%"

                        if not task.finish_time:
                            task.finish_time = datetime.utcnow()
                        task.updated_at = datetime.utcnow()

                        db.add(task)
                        db.commit()
                        db.refresh(task)

                    print(f"🔧 【强制修复版】修复完成: {task.id}")
                    print(f"   状态: {old_status} -> {task.status}")
                    print(f"   进度: {old_progress} -> {task.progress}")
                    print(f"   图片: {bool(old_image_url)} -> {bool(task.image_url)}")
                    fixed_count += 1

                except Exception as e:
                    print(f"🔧 【强制修复版】修复任务失败: {task.id} - {e}")

        print(
            f"🔧 【强制修复版】修复完成，共修复 {fixed_count} 个任务，查询了 {remote_checked} 个远程状态"
        )

        return {
            "message": f"Task states fixed successfully",
            "fixed_count": fixed_count,
            "remote_checked": remote_checked,
        }

    except Exception as e:
        print(f"🔧 【强制修复版】修复任务状态失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to fix task states: {str(e)}"
        )


# ======================== 实时更新 ========================


@router.get("/stream/user")
async def stream_user_tasks(user=Depends(get_verified_user)):
    """用户任务状态实时流 - 修复版本"""

    async def generate():
        try:
            print(f"🔄 【流媒体修复版】开始用户 {user.id} 的任务流")

            # 检查MJ服务是否配置
            config = MJConfig.get_config()
            if not config or not config.enabled:
                yield f"data: {json.dumps({'type': 'info', 'message': 'Midjourney service not configured or disabled'})}\n\n"
                yield f"data: {json.dumps({'type': 'stream_end', 'message': 'Stream completed'})}\n\n"
                return

            sent_completed_tasks = set()  # 记录已发送的完成任务，避免重复
            max_iterations = 200  # 最多运行200次 (约10分钟)
            iteration = 0

            while iteration < max_iterations:
                try:
                    # 获取用户最新任务状态 - 只获取最近更新的未完成任务
                    recent_tasks = MJTask.get_user_recent_tasks(user.id, limit=5)

                    active_tasks_found = False

                    for task in recent_tasks:
                        # 🔥 只推送真正需要更新的任务
                        should_send = False

                        # 1. 未完成的任务 - 总是发送
                        if task.status not in ["SUCCESS", "FAILURE", "FAILED"]:
                            should_send = True
                            active_tasks_found = True
                            print(
                                f"🔄 【流媒体修复版】发送进行中任务: {task.id}, 状态: {task.status}"
                            )

                        # 2. 刚完成的任务 - 只发送一次
                        elif task.status in ["SUCCESS", "FAILURE", "FAILED"]:
                            if task.id not in sent_completed_tasks:
                                should_send = True
                                sent_completed_tasks.add(task.id)
                                print(
                                    f"🔄 【流媒体修复版】发送完成任务(首次): {task.id}, 状态: {task.status}"
                                )
                            else:
                                print(
                                    f"🔄 【流媒体修复版】跳过已发送的完成任务: {task.id}"
                                )

                        # 3. 最近更新的任务 (5秒内)
                        elif task.updated_at > datetime.utcnow() - timedelta(seconds=5):
                            should_send = True
                            print(f"🔄 【流媒体修复版】发送最近更新任务: {task.id}")

                        if should_send:
                            task_data = task.to_dict()
                            yield f"data: {json.dumps(task_data)}\n\n"

                    # 🔥 如果没有活跃任务且已经发送了所有完成任务，则停止流
                    if not active_tasks_found and len(sent_completed_tasks) > 0:
                        print(f"🔄 【流媒体修复版】没有活跃任务，停止流媒体")
                        break

                    await asyncio.sleep(2)  # 每2秒检查一次
                    iteration += 1

                except Exception as e:
                    print(f"🔄 【流媒体修复版】流媒体错误: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    break

            print(
                f"🔄 【流媒体修复版】用户 {user.id} 的任务流结束，共 {iteration} 次迭代"
            )
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'stream_end', 'message': 'Stream completed'})}\n\n"

        except Exception as e:
            print(f"🔄 【流媒体修复版】生成器错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ======================== 后台任务 ========================


async def poll_task_status(task_id: str, user_id: str):
    """后台轮询任务状态 - 修复版本"""
    max_attempts = 300  # 增加到300次 (约10分钟)
    attempt = 0

    print(f"🚀 【修复版】开始后台轮询任务 {task_id}")

    while attempt < max_attempts:
        try:
            client = get_mj_client()
            mj_task = await client.get_task_status(task_id)

            if mj_task:
                status = mj_task.get("status", "UNKNOWN")
                progress = mj_task.get("progress", "0%")
                image_url = mj_task.get("imageUrl", "")

                print(
                    f"📊 【修复版】任务 {task_id} - 状态: {status}, 进度: {progress}, 有图片: {bool(image_url)}"
                )

                # 🔥 强制更新数据库 - 每次轮询都更新
                task = MJTask.get_task_by_id(task_id)
                if task:
                    print(f"💾 【修复版】强制更新数据库: {task_id}")

                    # 如果有图片URL，无论什么状态都设置为SUCCESS
                    if image_url:
                        print(f"🖼️ 【修复版】发现图片，强制完成: {image_url}")
                        forced_data = {
                            "status": "SUCCESS",
                            "progress": "100%",
                            "imageUrl": image_url,
                            "failReason": mj_task.get("failReason"),
                            "properties": mj_task.get("properties", {}),
                            "buttons": mj_task.get("buttons", []),
                        }
                        task.update_from_mj_response(forced_data)
                        print(f"✅ 【修复版】任务 {task_id} 已强制完成")

                        # 🔥 自动上传到云存储
                        try:
                            from open_webui.internal.db import get_db

                            file_manager = get_file_manager()
                            success, message, file_record = (
                                await file_manager.save_generated_content(
                                    user_id=user_id,
                                    file_url=image_url,
                                    filename=f"midjourney_{task_id}.jpg",
                                    file_type="image",
                                    source_type="midjourney",
                                    source_task_id=task_id,
                                    metadata={
                                        "prompt": task.prompt,
                                        "mode": task.mode,
                                        "original_url": image_url,
                                    },
                                )
                            )
                            if success and file_record and file_record.cloud_url:
                                # 重新获取task对象并在新的session中更新云存储URL
                                with get_db() as update_db:
                                    update_task = (
                                        update_db.query(MJTask)
                                        .filter(MJTask.id == task_id)
                                        .first()
                                    )
                                    if update_task:
                                        update_task.cloud_image_url = (
                                            file_record.cloud_url
                                        )
                                        update_db.commit()
                                        print(
                                            f"☁️ 【云存储】Midjourney图片上传成功，已更新URL: {task_id}"
                                        )
                                    else:
                                        print(f"☁️ 【云存储】找不到任务记录: {task_id}")
                            else:
                                print(
                                    f"☁️ 【云存储】Midjourney图片上传失败: {task_id} - {message}"
                                )
                        except Exception as upload_error:
                            print(
                                f"☁️ 【云存储【Midjourney自动上传异常: {task_id} - {upload_error}"
                            )

                        break
                    else:
                        # 没有图片时正常更新
                        task.update_from_mj_response(mj_task)

                # 检查任务是否完成
                if status in ["SUCCESS", "FAILURE", "FAILED"]:
                    print(f"✅ 【修复版】任务 {task_id} 正常完成，最终状态: {status}")
                    break

            else:
                print(f"⚠️ 【修复版】任务 {task_id} 返回空响应")

            await asyncio.sleep(2)  # 固定2秒间隔
            attempt += 1

        except Exception as e:
            print(f"❌ 【修复版】轮询任务 {task_id} 出错: {e}")
            import traceback

            traceback.print_exc()
            await asyncio.sleep(3)
            attempt += 1

    print(f"🏁 【修复版】任务 {task_id} 轮询结束，共 {attempt} 次")

    # 🔥 最终检查 - 如果还没完成，再查一次远程状态
    try:
        print(f"🔍 【修复版】最终检查任务状态: {task_id}")
        client = get_mj_client()
        final_task = await client.get_task_status(task_id)
        if final_task and final_task.get("imageUrl"):
            task = MJTask.get_task_by_id(task_id)
            if task:
                print(f"🔥 【修复版】最终强制完成: {task_id}")
                final_data = {
                    "status": "SUCCESS",
                    "progress": "100%",
                    "imageUrl": final_task.get("imageUrl"),
                    "failReason": final_task.get("failReason"),
                    "properties": final_task.get("properties", {}),
                    "buttons": final_task.get("buttons", []),
                }
                task.update_from_mj_response(final_data)

                # 🔥 最终检查时也自动上传到云存储
                try:
                    from open_webui.internal.db import get_db

                    file_manager = get_file_manager()
                    success, message, file_record = (
                        await file_manager.save_generated_content(
                            user_id=user_id,
                            file_url=final_task.get("imageUrl"),
                            filename=f"midjourney_{task_id}.jpg",
                            file_type="image",
                            source_type="midjourney",
                            source_task_id=task_id,
                            metadata={
                                "prompt": task.prompt,
                                "mode": task.mode,
                                "original_url": final_task.get("imageUrl"),
                            },
                        )
                    )
                    if success and file_record and file_record.cloud_url:
                        # 重新获取task对象并在新的session中更新云存储URL
                        with get_db() as update_db:
                            update_task = (
                                update_db.query(MJTask)
                                .filter(MJTask.id == task_id)
                                .first()
                            )
                            if update_task:
                                update_task.cloud_image_url = file_record.cloud_url
                                update_db.commit()
                                print(
                                    f"☁️ 【云存储】Midjourney最终检查图片上传成功，已更新URL: {task_id}"
                                )
                            else:
                                print(f"☁️ 【云存储】找不到任务记录: {task_id}")
                    else:
                        print(
                            f"☁️ 【云存储】Midjourney最终检查图片上传失败: {task_id} - {message}"
                        )
                except Exception as upload_error:
                    print(
                        f"☁️ 【云存储】Midjourney最终检查自动上传异常: {task_id} - {upload_error}"
                    )
    except Exception as e:
        print(f"❌ 【修复版】最终检查失败: {e}")
