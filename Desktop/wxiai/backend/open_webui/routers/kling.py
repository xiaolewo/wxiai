"""
可灵视频生成 API 路由
实现完整的可灵视频生成功能，包括文生视频、图生视频等
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
from open_webui.models.kling import (
    KlingConfig,
    KlingTask,
    KlingConfigForm,
    KlingTaskForm,
    KlingGenerateRequest,
)
from open_webui.utils.kling import (
    KlingApiClient,
    deduct_user_credits,
    add_user_credits,
    get_user_credit_balance,
    validate_user_credits,
    process_kling_generation,
)

router = APIRouter(prefix="/kling", tags=["kling"])

# 全局变量存储可灵配置
kling_config = None
kling_client = None


def get_kling_client():
    """获取可灵API客户端"""
    global kling_client, kling_config
    if not kling_client or not kling_config:
        config = KlingConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="可灵服务未配置或已禁用")
        kling_client = KlingApiClient(config)
        kling_config = config
    return kling_client


# ======================== 配置管理 ========================


@router.get("/config")
async def get_kling_config(user=Depends(get_admin_user)):
    """获取可灵配置 - 管理员专用"""
    config = KlingConfig.get_config()
    if not config:
        # 返回默认配置
        default_config = KlingConfig()
        return {
            "enabled": False,
            "base_url": "https://api.klingai.com",
            "api_key": "",
            "text_to_video_model": "kling-v1",
            "image_to_video_model": "kling-v1",
            "default_mode": "std",
            "default_duration": "5",
            "default_aspect_ratio": "16:9",
            "default_cfg_scale": 0.5,
            "credits_per_std_5s": 50,
            "credits_per_std_10s": 100,
            "credits_per_pro_5s": 100,
            "credits_per_pro_10s": 200,
            "model_credits_config": default_config._get_default_model_credits(),
            "max_concurrent_tasks": 3,
            "task_timeout": 600000,
        }
    return config.to_dict()


@router.get("/config/user")
async def get_kling_user_config(user=Depends(get_verified_user)):
    """获取可灵用户配置 - 只返回用户需要的配置信息（不包含敏感信息）"""
    config = KlingConfig.get_config()
    if not config:
        # 返回默认用户配置
        default_config = KlingConfig()
        return {
            "enabled": False,
            "text_to_video_model": "kling-v1",
            "image_to_video_model": "kling-v1",
            "default_mode": "std",
            "default_duration": "5",
            "default_aspect_ratio": "16:9",
            "default_cfg_scale": 0.5,
            "credits_per_std_5s": 50,
            "credits_per_std_10s": 100,
            "credits_per_pro_5s": 100,
            "credits_per_pro_10s": 200,
            "model_credits_config": default_config._get_default_model_credits(),
        }

    # 只返回用户需要的配置，不包含敏感信息
    return {
        "enabled": config.enabled,
        "text_to_video_model": config.text_to_video_model,
        "image_to_video_model": config.image_to_video_model,
        "default_mode": config.default_mode,
        "default_duration": config.default_duration,
        "default_aspect_ratio": config.default_aspect_ratio,
        "default_cfg_scale": config.default_cfg_scale,
        "credits_per_std_5s": config.credits_per_std_5s,
        "credits_per_std_10s": config.credits_per_std_10s,
        "credits_per_pro_5s": config.credits_per_pro_5s,
        "credits_per_pro_10s": config.credits_per_pro_10s,
        "model_credits_config": config.model_credits_config
        or config._get_default_model_credits(),
    }


@router.post("/config")
async def save_kling_config(config_data: dict, user=Depends(get_admin_user)):
    """保存可灵配置 - 管理员专用"""
    global kling_client, kling_config

    try:
        # 验证必需字段
        enabled = config_data.get("enabled", False)
        if enabled and (
            not config_data.get("base_url") or not config_data.get("api_key")
        ):
            raise HTTPException(
                status_code=400, detail="启用时需要提供Base URL和API Key"
            )

        # 设置默认值
        config_data.setdefault("text_to_video_model", "kling-v1")
        config_data.setdefault("image_to_video_model", "kling-v1")
        config_data.setdefault("default_mode", "std")
        config_data.setdefault("default_duration", "5")
        config_data.setdefault("default_aspect_ratio", "16:9")
        config_data.setdefault("default_cfg_scale", 0.5)
        config_data.setdefault("credits_per_std_5s", 50)
        config_data.setdefault("credits_per_std_10s", 100)
        config_data.setdefault("credits_per_pro_5s", 100)
        config_data.setdefault("credits_per_pro_10s", 200)
        config_data.setdefault("max_concurrent_tasks", 3)
        config_data.setdefault("task_timeout", 600000)

        # 保存配置
        config = KlingConfig.save_config(config_data)

        # 重置客户端
        kling_client = None
        kling_config = None

        return {"message": "配置保存成功", "config": config.to_dict()}
    except Exception as e:
        import traceback

        print(f"Error saving Kling config: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/test/simple")
async def test_kling_simple(user=Depends(get_admin_user)):
    """简单测试可灵配置 - 不需要真实API"""
    try:
        config = KlingConfig.get_config()
        if not config:
            return {"status": "error", "message": "可灵服务未配置"}

        return {
            "status": "success",
            "message": "可灵配置检查完成",
            "config": {
                "enabled": config.enabled,
                "base_url": config.base_url,
                "has_api_key": bool(config.api_key),
                "text_to_video_model": config.text_to_video_model,
                "image_to_video_model": config.image_to_video_model,
            },
        }
    except Exception as e:
        return {"status": "error", "message": f"错误: {str(e)}"}


@router.get("/test")
async def test_kling_connection(user=Depends(get_admin_user)):
    """测试可灵连接 - 管理员专用，智能检测API路径"""
    try:
        # 检查配置是否存在
        config = KlingConfig.get_config()
        if not config:
            raise HTTPException(status_code=400, detail="可灵服务未配置")

        print(
            f"🎬 【可灵测试】配置检查: enabled={config.enabled}, base_url={config.base_url}, api_key={'***' if config.api_key else 'None'}"
        )

        if not config.enabled:
            raise HTTPException(status_code=400, detail="可灵服务已禁用")

        if not config.base_url or not config.api_key:
            raise HTTPException(status_code=400, detail="需要提供Base URL和API Key")

        # 智能路径检测 - 尝试多种常见的API路径模式
        base_url = config.base_url.rstrip("/")
        possible_paths = [
            "/kling/v1/videos/text2video",  # 第三方平台路径 (如代理服务)
            "/v1/videos/text2video",  # 官方API路径
            "/api/kling/v1/videos/text2video",  # 另一种第三方平台路径
            "/api/v1/videos/text2video",  # 简化的API路径
            "/videos/text2video",  # 最简路径
            "/text2video",  # 直接端点
        ]

        test_payload = {
            "model_name": config.text_to_video_model,
            "prompt": "test connection",
            "mode": "std",
            "duration": "5",
        }

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        successful_path = None
        test_results = []

        print(
            f"🎬 【可灵测试】开始智能路径检测，测试 {len(possible_paths)} 种路径模式..."
        )

        async with httpx.AsyncClient(timeout=15.0) as http_client:
            for i, path in enumerate(possible_paths):
                test_url = f"{base_url}{path}"
                print(
                    f"🎬 【可灵测试】测试路径 {i+1}/{len(possible_paths)}: {test_url}"
                )

                try:
                    response = await http_client.post(
                        test_url, headers=headers, json=test_payload, timeout=10.0
                    )

                    print(f"🎬 【可灵测试】路径 {i+1} 响应: {response.status_code}")

                    test_results.append(
                        {
                            "path": path,
                            "url": test_url,
                            "status_code": response.status_code,
                            "response_preview": (
                                response.text[:100] if response.text else "无内容"
                            ),
                        }
                    )

                    # 检查是否找到了有效的路径
                    if response.status_code in [
                        200,
                        400,
                        422,
                    ]:  # 200=成功, 400/422=参数错误但端点存在
                        successful_path = path
                        print(
                            f"✅ 【可灵测试】找到有效路径: {test_url} (状态: {response.status_code})"
                        )

                        # 分析状态码含义
                        if response.status_code == 200:
                            message = "连接测试成功，API正常工作"
                            status = "success"
                        else:
                            message = (
                                "连接成功，但参数有误 - 这是正常的，说明API端点可达"
                            )
                            status = "success"

                        # 保存检测到的路径到配置中
                        try:
                            config.detected_api_path = path
                            config.updated_at = datetime.now()
                            with get_db() as db:
                                db.merge(config)
                                db.commit()
                            print(f"✅ 【可灵测试】已保存检测到的API路径: {path}")
                        except Exception as save_error:
                            print(f"⚠️ 【可灵测试】保存API路径失败: {save_error}")

                        return {
                            "status": status,
                            "message": message,
                            "detected_path": path,
                            "full_url": test_url,
                            "status_code": response.status_code,
                            "response_preview": (
                                response.text[:200] if response.text else "无内容"
                            ),
                            "note": "已自动检测到正确的API路径并保存，服务可以正常使用",
                            "test_results": test_results,
                        }

                    elif response.status_code == 401:
                        print(f"🔑 【可灵测试】路径 {i+1} API密钥问题")
                        # 401表示路径正确但密钥有问题，也算找到了路径
                        return {
                            "status": "error",
                            "message": "API密钥无效 - 请检查API Key",
                            "detected_path": path,
                            "full_url": test_url,
                            "status_code": response.status_code,
                            "response_preview": (
                                response.text[:100] if response.text else "无内容"
                            ),
                            "note": "已找到正确的API路径，但API密钥验证失败",
                            "suggestion": "请确认API密钥格式正确且有效",
                            "test_results": test_results,
                        }

                    elif response.status_code == 403:
                        print(f"🚫 【可灵测试】路径 {i+1} 权限问题")
                        # 403也表示路径正确但权限不足
                        return {
                            "status": "warning",
                            "message": "API访问被拒绝 - 可能是配额不足或权限问题",
                            "detected_path": path,
                            "full_url": test_url,
                            "status_code": response.status_code,
                            "response_preview": (
                                response.text[:100] if response.text else "无内容"
                            ),
                            "note": "已找到正确的API路径，但访问权限不足",
                            "test_results": test_results,
                        }

                except httpx.ConnectError as e:
                    print(f"❌ 【可灵测试】路径 {i+1} 连接错误: {e}")
                    test_results.append(
                        {"path": path, "url": test_url, "error": f"连接错误: {str(e)}"}
                    )
                    continue

                except httpx.TimeoutException as e:
                    print(f"⏱️ 【可灵测试】路径 {i+1} 超时: {e}")
                    test_results.append(
                        {"path": path, "url": test_url, "error": f"请求超时: {str(e)}"}
                    )
                    continue

                except Exception as e:
                    print(f"❓ 【可灵测试】路径 {i+1} 其他错误: {e}")
                    test_results.append(
                        {"path": path, "url": test_url, "error": f"请求错误: {str(e)}"}
                    )
                    continue

        # 如果所有路径都失败了
        print(f"❌ 【可灵测试】所有路径测试完毕，未找到有效路径")

        return {
            "status": "error",
            "message": "无法找到有效的API路径 - 请检查Base URL配置",
            "status_code": 404,
            "debug_info": {
                "base_url": base_url,
                "tested_paths": [result["path"] for result in test_results],
                "suggestions": [
                    "请确认Base URL是否正确 (如: https://api.klingai.com)",
                    "检查您的服务提供商使用的API路径格式",
                    "确认API服务是否正常运行",
                    "验证网络连接是否正常",
                ],
            },
            "test_results": test_results,
            "note": "已尝试多种常见的API路径模式，但都无法连通",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【可灵测试】系统错误: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"连接测试失败: {str(e)}")


# ======================== 任务提交 ========================


@router.post("/submit/text-to-video")
async def submit_text_to_video_task(
    request: KlingGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """提交文生视频任务"""
    try:
        print(f"🎬 【可灵后端】收到文生视频请求: 用户={user.id}")
        print(
            f"🎬 【可灵后端】请求参数: model={request.model_name}, prompt={request.prompt[:50]}..., mode={request.mode}, duration={request.duration}"
        )
        print(
            f"🎬 【可灵后端】其他参数: aspect_ratio={request.aspect_ratio}, cfg_scale={request.cfg_scale}"
        )

        # 使用工具函数处理任务
        print(f"🎬 【可灵后端】开始处理文生视频任务...")
        task = await process_kling_generation(
            user_id=user.id, request=request, action="TEXT_TO_VIDEO"
        )

        print(f"🎬 【可灵后端】任务创建成功: {task.id}")
        return {"success": True, "task_id": task.id, "message": "文生视频任务提交成功"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【可灵后端】文生视频任务提交失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"提交文生视频任务失败: {str(e)}")


@router.post("/submit/image-to-video")
async def submit_image_to_video_task(
    request: KlingGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """提交图生视频任务"""
    try:
        print(f"🎬 【可灵后端】收到图生视频请求: 用户={user.id}")
        print(
            f"🎬 【可灵后端】请求参数: model={request.model_name}, prompt={request.prompt[:50]}..., mode={request.mode}, duration={request.duration}"
        )
        print(
            f"🎬 【可灵后端】输入图片: {len(request.image) if request.image else 0}字符"
        )
        if request.dynamic_masks:
            print(f"🎬 【可灵后端】动态笔刷: {len(request.dynamic_masks)}组")

        # 验证输入图片
        if not request.image:
            print("❌ 【可灵后端】缺少输入图片")
            raise HTTPException(status_code=400, detail="图生视频需要输入图片")

        # 验证图片数据基本格式
        image_data = request.image.strip()
        if len(image_data) < 100:
            print(f"❌ 【可灵后端】图片数据太短: {len(image_data)}字符")
            raise HTTPException(
                status_code=400, detail=f"图片数据太短: {len(image_data)}字符"
            )

        # 记录图片数据前缀用于调试
        prefix = image_data[:50] if len(image_data) > 50 else image_data
        print(f"🎬 【可灵后端】图片数据前缀: {prefix}...")

        # 使用工具函数处理任务
        print(f"🎬 【可灵后端】开始处理图生视频任务...")
        task = await process_kling_generation(
            user_id=user.id, request=request, action="IMAGE_TO_VIDEO"
        )

        print(f"🎬 【可灵后端】任务创建成功: {task.id}")
        return {"success": True, "task_id": task.id, "message": "图生视频任务提交成功"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【可灵后端】图生视频任务提交失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"提交图生视频任务失败: {str(e)}")


# ======================== 任务查询 ========================


@router.get("/task/{task_id}")
async def get_kling_task_status(task_id: str, user=Depends(get_verified_user)):
    """获取任务状态"""
    try:
        print(f"🎬 【可灵API】获取任务状态: {task_id}, 用户: {user.id}")

        # 先查本地数据库
        task = KlingTask.get_task_by_id(task_id)
        print(
            f"🎬 【可灵API】本地任务: {task.id if task else 'None'}, 状态: {task.status if task else 'None'}"
        )

        # 验证任务所有权
        if not task:
            print(f"❌ 【可灵API】任务不存在: {task_id}")
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.user_id != user.id:
            print(
                f"❌ 【可灵API】无权访问任务: 任务用户={task.user_id}, 请求用户={user.id}"
            )
            raise HTTPException(status_code=404, detail="无权访问此任务")

        # 如果任务已完成，直接返回
        if task.status in ["succeed", "failed"]:
            print(f"🎬 【可灵API】任务已完成: {task.id}")
            return task.to_dict()

        # 如果任务还在进行中，可以选择查询远程状态
        # 注意：可灵API查询需要external_task_id
        if task.external_task_id is not None and task.external_task_id != "":
            try:
                print(f"🔍 【可灵API】查询远程状态: {task.external_task_id}")
                client = get_kling_client()
                remote_status = await client.query_task(task.external_task_id)
                print(f"📡 【可灵API】远程响应: {str(remote_status)[:200]}...")
                task.update_from_api_response(remote_status)
                print(f"🎬 【可灵API】更新远程状态成功: {task.status}")
            except Exception as e:
                print(f"⚠️ 【可灵API】查询远程状态失败: {e}")
                import traceback

                traceback.print_exc()
                # 查询失败不影响返回本地状态

        print(f"📤 【可灵API】准备返回任务状态")
        result = task.to_dict()
        print(f"✅ 【可灵API】任务状态序列化成功，包含 {len(result)} 个字段")
        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【可灵API】获取任务状态失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


# ======================== 用户功能 ========================


@router.get("/history")
async def get_user_kling_history(
    page: int = 1, limit: int = 20, user=Depends(get_verified_user)
):
    """获取用户任务历史"""
    try:
        tasks = KlingTask.get_user_tasks(user.id, page, limit)
        total = KlingTask.get_user_task_count(user.id)

        return {
            "data": [task.to_dict() for task in tasks],
            "total": total,
            "page": page,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务历史失败: {str(e)}")


@router.get("/credits")
async def get_user_kling_credits(user=Depends(get_verified_user)):
    """获取用户积分余额"""
    try:
        balance = get_user_credit_balance(user.id)
        return {"balance": balance}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取积分失败: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_kling_task(task_id: str, user=Depends(get_verified_user)):
    """删除用户任务"""
    try:
        # 验证任务所有权
        task = KlingTask.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问")

        # 删除任务记录
        with get_db() as db:
            db.delete(task)
            db.commit()

        return {"message": "任务删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


# ======================== 统计功能 ========================


@router.get("/stats/system")
async def get_kling_system_stats(user=Depends(get_admin_user)):
    """获取系统可灵统计 - 管理员专用"""
    try:
        from open_webui.utils.kling import get_system_kling_stats

        stats = get_system_kling_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")


@router.get("/stats/user")
async def get_kling_user_stats(user=Depends(get_verified_user)):
    """获取用户可灵统计"""
    try:
        from open_webui.utils.kling import get_user_kling_stats

        stats = get_user_kling_stats(user.id)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户统计失败: {str(e)}")


# ======================== 管理员功能 ========================


@router.post("/admin/credits/add")
async def admin_add_kling_credits(
    target_user_id: str, amount: int, reason: str = "", user=Depends(get_admin_user)
):
    """管理员给用户充值积分"""
    try:
        from open_webui.utils.kling import admin_add_credits_to_user

        new_balance = admin_add_credits_to_user(user.id, target_user_id, amount, reason)
        return {
            "message": f"给用户 {target_user_id} 充值 {amount} 积分",
            "new_balance": new_balance,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"充值积分失败: {str(e)}")


@router.post("/admin/credits/deduct")
async def admin_deduct_kling_credits(
    target_user_id: str, amount: int, reason: str = "", user=Depends(get_admin_user)
):
    """管理员扣除用户积分"""
    try:
        from open_webui.utils.kling import admin_deduct_credits_from_user

        new_balance = admin_deduct_credits_from_user(
            user.id, target_user_id, amount, reason
        )
        return {
            "message": f"从用户 {target_user_id} 扣除 {amount} 积分",
            "new_balance": new_balance,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扣除积分失败: {str(e)}")


@router.post("/admin/cleanup")
async def admin_cleanup_old_tasks(days: int = 30, user=Depends(get_admin_user)):
    """管理员清理旧任务记录"""
    try:
        from open_webui.utils.kling import cleanup_old_tasks

        deleted_count = cleanup_old_tasks(days)
        return {"message": f"清理了 {deleted_count} 个旧任务（超过 {days} 天）"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理任务失败: {str(e)}")
