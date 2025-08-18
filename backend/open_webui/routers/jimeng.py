"""
即梦视频生成 API 路由
实现完整的即梦视频生成功能，包括文生视频、图生视频等
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, FileResponse
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
import os
from open_webui.internal.db import get_db
from open_webui.models.jimeng import (
    JimengConfig,
    JimengTask,
    JimengConfigForm,
    JimengTaskForm,
    JimengGenerateRequest,
)
from open_webui.utils.jimeng import (
    JimengApiClient,
    deduct_user_credits,
    add_user_credits,
    get_user_credit_balance,
    validate_user_credits,
    process_jimeng_generation,
)

router = APIRouter(prefix="/jimeng", tags=["jimeng"])

# 全局变量存储即梦配置
jimeng_config = None
jimeng_client = None


def get_jimeng_client():
    """获取即梦API客户端"""
    global jimeng_client, jimeng_config
    if not jimeng_client or not jimeng_config:
        config = JimengConfig.get_config()
        if not config or not config.enabled:
            raise HTTPException(status_code=400, detail="即梦服务未配置或已禁用")
        jimeng_client = JimengApiClient(config)
        jimeng_config = config
    return jimeng_client


# ======================== 配置管理 ========================


@router.get("/config")
async def get_jimeng_config(user=Depends(get_admin_user)):
    """获取即梦配置 - 管理员专用"""
    config = JimengConfig.get_config()
    if not config:
        # 返回默认配置
        return {
            "enabled": False,
            "base_url": "https://ark.cn-beijing.volces.com",
            "api_key": "",
            "default_duration": "5",
            "default_aspect_ratio": "16:9",
            "default_cfg_scale": 0.5,
            "credits_per_5s": 30,
            "credits_per_10s": 60,
            "max_concurrent_tasks": 5,
            "task_timeout": 600000,
            "query_interval": 10000,
        }
    return config.to_dict()


@router.get("/config/user")
async def get_jimeng_user_config(user=Depends(get_verified_user)):
    """获取即梦用户配置 - 只返回用户需要的配置信息（不包含敏感信息）"""
    config = JimengConfig.get_config()
    if not config:
        # 返回默认用户配置
        return {
            "enabled": False,
            "default_duration": "5",
            "default_aspect_ratio": "16:9",
            "default_cfg_scale": 0.5,
            "credits_per_5s": 30,
            "credits_per_10s": 60,
        }

    # 只返回用户需要的配置，不包含敏感信息
    return {
        "enabled": config.enabled,
        "default_duration": config.default_duration,
        "default_aspect_ratio": config.default_aspect_ratio,
        "default_cfg_scale": config.default_cfg_scale,
        "credits_per_5s": config.credits_per_5s,
        "credits_per_10s": config.credits_per_10s,
    }


@router.post("/config")
async def save_jimeng_config(config_data: dict, user=Depends(get_admin_user)):
    """保存即梦配置 - 管理员专用"""
    global jimeng_client, jimeng_config

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
        config_data.setdefault("default_duration", "5")
        config_data.setdefault("default_aspect_ratio", "16:9")
        config_data.setdefault("default_cfg_scale", 0.5)
        config_data.setdefault("credits_per_5s", 30)
        config_data.setdefault("credits_per_10s", 60)
        config_data.setdefault("max_concurrent_tasks", 5)
        config_data.setdefault("task_timeout", 600000)
        config_data.setdefault("query_interval", 10000)

        # 保存配置
        config = JimengConfig.save_config(config_data)

        # 重置客户端
        jimeng_client = None
        jimeng_config = None

        return {"message": "配置保存成功", "config": config.to_dict()}
    except Exception as e:
        import traceback

        print(f"Error saving Jimeng config: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/test/simple")
async def test_jimeng_simple(user=Depends(get_admin_user)):
    """简单测试即梦配置 - 不需要真实API"""
    try:
        config = JimengConfig.get_config()
        if not config:
            return {"status": "error", "message": "即梦服务未配置"}

        return {
            "status": "success",
            "message": "即梦配置检查完成",
            "config": {
                "enabled": config.enabled,
                "base_url": config.base_url,
                "has_api_key": bool(config.api_key),
                "default_duration": config.default_duration,
                "default_aspect_ratio": config.default_aspect_ratio,
            },
        }
    except Exception as e:
        return {"status": "error", "message": f"错误: {str(e)}"}


@router.get("/test")
async def test_jimeng_connection(user=Depends(get_admin_user)):
    """测试即梦连接 - 管理员专用，智能检测API路径"""
    try:
        # 检查配置是否存在
        config = JimengConfig.get_config()
        if not config:
            raise HTTPException(status_code=400, detail="即梦服务未配置")

        print(
            f"🎬 【即梦测试】配置检查: enabled={config.enabled}, base_url={config.base_url}, api_key={'***' if config.api_key else 'None'}"
        )

        if not config.enabled:
            raise HTTPException(status_code=400, detail="即梦服务已禁用")

        if not config.base_url or not config.api_key:
            raise HTTPException(status_code=400, detail="需要提供Base URL和API Key")

        # 智能路径检测 - 尝试多种常见的API路径模式
        base_url = config.base_url.rstrip("/")
        possible_paths = [
            "/jimeng/submit/videos",  # 标准即梦路径
            "/BASE_URL/jimeng/submit/videos",  # 带BASE_URL前缀
            "/api/jimeng/submit/videos",  # 带api前缀
            "/v1/jimeng/submit/videos",  # 带版本号
            "/submit/videos",  # 简化路径
            "/videos/submit",  # 替代路径
        ]

        test_payload = {
            "prompt": "test connection",
            "duration": 5,
            "aspect_ratio": "16:9",
            "cfg_scale": 0.5,
        }

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        successful_path = None
        test_results = []

        print(
            f"🎬 【即梦测试】开始智能路径检测，测试 {len(possible_paths)} 种路径模式..."
        )

        async with httpx.AsyncClient(timeout=15.0) as http_client:
            for i, path in enumerate(possible_paths):
                test_url = f"{base_url}{path}"
                print(
                    f"🎬 【即梦测试】测试路径 {i+1}/{len(possible_paths)}: {test_url}"
                )

                try:
                    response = await http_client.post(
                        test_url, headers=headers, json=test_payload, timeout=10.0
                    )

                    print(f"🎬 【即梦测试】路径 {i+1} 响应: {response.status_code}")

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
                            f"✅ 【即梦测试】找到有效路径: {test_url} (状态: {response.status_code})"
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
                            print(f"✅ 【即梦测试】已保存检测到的API路径: {path}")
                        except Exception as save_error:
                            print(f"⚠️ 【即梦测试】保存API路径失败: {save_error}")

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
                        print(f"🔑 【即梦测试】路径 {i+1} API密钥问题")
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
                        print(f"🚫 【即梦测试】路径 {i+1} 权限问题")
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
                    print(f"❌ 【即梦测试】路径 {i+1} 连接错误: {e}")
                    test_results.append(
                        {"path": path, "url": test_url, "error": f"连接错误: {str(e)}"}
                    )
                    continue

                except httpx.TimeoutException as e:
                    print(f"⏱️ 【即梦测试】路径 {i+1} 超时: {e}")
                    test_results.append(
                        {"path": path, "url": test_url, "error": f"请求超时: {str(e)}"}
                    )
                    continue

                except Exception as e:
                    print(f"❓ 【即梦测试】路径 {i+1} 其他错误: {e}")
                    test_results.append(
                        {"path": path, "url": test_url, "error": f"请求错误: {str(e)}"}
                    )
                    continue

        # 如果所有路径都失败了
        print(f"❌ 【即梦测试】所有路径测试完毕，未找到有效路径")

        return {
            "status": "error",
            "message": "无法找到有效的API路径 - 请检查Base URL配置",
            "status_code": 404,
            "debug_info": {
                "base_url": base_url,
                "tested_paths": [result["path"] for result in test_results],
                "suggestions": [
                    "请确认Base URL是否正确 (如: https://ark.cn-beijing.volces.com)",
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
        print(f"❌ 【即梦测试】系统错误: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"连接测试失败: {str(e)}")


# ======================== 任务提交 ========================


def parse_content_for_jimeng(content, http_request=None) -> tuple[str, str]:
    """
    解析content数组，提取文本prompt和图片URL
    支持OpenAI格式的content数组: [{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {"url": "..."}}]
    支持base64图片自动转换为临时URL

    Returns:
        tuple: (prompt, image_url)
    """
    prompt = ""
    image_url = ""

    if isinstance(content, str):
        # 如果content是字符串，直接作为prompt
        prompt = content
    elif isinstance(content, list):
        # 如果content是数组，解析每个元素
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_content = item.get("text", "")
                    if text_content:
                        prompt += text_content
                elif item.get("type") == "image_url":
                    img_data = item.get("image_url", {})
                    img_url = img_data.get("url", "")
                    if img_url and not image_url:  # 只取第一个图片
                        # 检查是否是base64数据URL
                        if img_url.startswith("data:image/"):
                            print(
                                f"🎬 【即梦content解析】检测到base64图片数据，转换为临时URL..."
                            )
                            try:
                                from open_webui.utils.jimeng import (
                                    save_base64_to_temp_file,
                                )

                                # 将base64转换为临时文件URL
                                temp_relative_path = save_base64_to_temp_file(img_url)
                                # 构建完整的URL - 使用当前请求的域名
                                if http_request:
                                    request_url_base = str(
                                        http_request.base_url
                                    ).rstrip("/")
                                else:
                                    request_url_base = (
                                        "http://localhost:8080"  # 回退到默认值
                                    )
                                image_url = f"{request_url_base}/{temp_relative_path}"
                                print(
                                    f"✅ 【即梦content解析】base64转换成功，URL: {image_url}"
                                )
                            except Exception as convert_error:
                                print(
                                    f"❌ 【即梦content解析】base64转换失败: {convert_error}"
                                )
                                # 转换失败时，保持原始URL，后续处理会报错
                                image_url = img_url
                        else:
                            # 普通图片URL，直接使用
                            image_url = img_url

    return prompt.strip(), image_url.strip()


@router.post("/submit/text-to-video")
async def submit_text_to_video_task(
    request: JimengGenerateRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    user=Depends(get_verified_user),
):
    """提交文生视频任务"""
    try:
        print(f"🎬 【即梦后端】收到文生视频请求: 用户={user.id}")

        # 解析content数组或使用现有prompt
        parsed_prompt, parsed_image_url = request.get_parsed_content(http_request)
        print(
            f"🎬 【即梦后端】解析后的内容: prompt={parsed_prompt[:50]}..., image_url={parsed_image_url}"
        )

        # 如果解析到了图片URL，这实际上是图生视频任务
        if parsed_image_url:
            print(f"🎬 【即梦后端】检测到图片URL，转为图生视频任务")
            # 更新请求对象
            request.prompt = parsed_prompt
            request.image_url = parsed_image_url

            # 调用图生视频处理逻辑
            task = await process_jimeng_generation(
                user_id=user.id, request=request, action="IMAGE_TO_VIDEO"
            )

            print(f"🎬 【即梦后端】图生视频任务创建成功: {task.id}")
            return {
                "success": True,
                "task_id": task.id,
                "message": "图生视频任务提交成功",
            }
        # 如果有base64图片数据但没有图片URL，转换base64为临时URL
        elif request.image and not request.image_url:
            from open_webui.utils.jimeng import save_base64_to_temp_file

            print(f"🎬 【即梦后端】检测到base64图片数据，转为图生视频任务...")
            try:
                # 将base64转换为临时文件URL
                temp_relative_path = save_base64_to_temp_file(request.image)
                # 构建完整的URL - 使用当前请求的域名
                base_url = str(http_request.base_url).rstrip("/")
                request.image_url = f"{base_url}/{temp_relative_path}"
                request.prompt = parsed_prompt
                print(f"✅ 【即梦后端】base64转换成功，URL: {request.image_url}")

                # 清除base64数据，避免重复处理
                request.image = None

                # 调用图生视频处理逻辑
                task = await process_jimeng_generation(
                    user_id=user.id, request=request, action="IMAGE_TO_VIDEO"
                )

                print(f"🎬 【即梦后端】图生视频任务创建成功: {task.id}")
                return {
                    "success": True,
                    "task_id": task.id,
                    "message": "图生视频任务提交成功",
                }

            except Exception as convert_error:
                print(f"❌ 【即梦后端】base64转换失败: {convert_error}")
                raise HTTPException(
                    status_code=400, detail=f"图片数据处理失败: {str(convert_error)}"
                )
        else:
            # 纯文生视频任务
            request.prompt = parsed_prompt
            print(
                f"🎬 【即梦后端】文生视频任务参数: prompt={request.prompt[:50]}..., duration={request.duration}"
            )

            # 使用工具函数处理任务
            print(f"🎬 【即梦后端】开始处理文生视频任务...")
            task = await process_jimeng_generation(
                user_id=user.id, request=request, action="TEXT_TO_VIDEO"
            )

            print(f"🎬 【即梦后端】任务创建成功: {task.id}")
            return {
                "success": True,
                "task_id": task.id,
                "message": "文生视频任务提交成功",
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【即梦后端】文生视频任务提交失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"提交文生视频任务失败: {str(e)}")


@router.post("/submit/image-to-video")
async def submit_image_to_video_task(
    request: JimengGenerateRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    user=Depends(get_verified_user),
):
    """提交图生视频任务"""
    try:
        print(f"🎬 【即梦后端】收到图生视频请求: 用户={user.id}")

        # 解析content数组或使用现有prompt和image_url
        parsed_prompt, parsed_image_url = request.get_parsed_content(http_request)
        print(
            f"🎬 【即梦后端】解析后的内容: prompt={parsed_prompt[:50]}..., image_url={parsed_image_url}"
        )

        # 更新请求对象
        if parsed_prompt:
            request.prompt = parsed_prompt
        if parsed_image_url:
            request.image_url = parsed_image_url

        print(
            f"🎬 【即梦后端】请求参数: prompt={request.prompt[:50] if request.prompt else ''}..., duration={request.duration}"
        )

        # 验证图生视频必需参数
        if not request.image_url and not request.image:
            print("❌ 【即梦后端】缺少输入图片")
            raise HTTPException(
                status_code=400, detail="图生视频需要输入图片URL或图片数据"
            )

        # 如果提供的是base64图片数据，转换为临时URL
        if request.image and not request.image_url:
            from open_webui.utils.jimeng import save_base64_to_temp_file

            print(f"🎬 【即梦后端】检测到base64图片数据，转换为临时URL...")
            try:
                # 将base64转换为临时文件URL
                temp_relative_path = save_base64_to_temp_file(request.image)
                # 构建完整的URL - 使用当前请求的域名
                base_url = str(http_request.base_url).rstrip("/")
                request.image_url = f"{base_url}/{temp_relative_path}"
                print(f"✅ 【即梦后端】base64转换成功，URL: {request.image_url}")

                # 清除base64数据，避免重复处理
                request.image = None

            except Exception as convert_error:
                print(f"❌ 【即梦后端】base64转换失败: {convert_error}")
                raise HTTPException(
                    status_code=400, detail=f"图片数据处理失败: {str(convert_error)}"
                )

        # 使用工具函数处理任务
        print(f"🎬 【即梦后端】开始处理图生视频任务...")
        task = await process_jimeng_generation(
            user_id=user.id, request=request, action="IMAGE_TO_VIDEO"
        )

        print(f"🎬 【即梦后端】任务创建成功: {task.id}")
        return {"success": True, "task_id": task.id, "message": "图生视频任务提交成功"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【即梦后端】图生视频任务提交失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"提交图生视频任务失败: {str(e)}")


# ======================== 任务查询 ========================


@router.get("/task/{task_id}")
async def get_jimeng_task_status(task_id: str, user=Depends(get_verified_user)):
    """获取任务状态"""
    try:
        print(f"🎬 【即梦API】获取任务状态: {task_id}, 用户: {user.id}")

        # 先查本地数据库
        task = JimengTask.get_task_by_id(task_id)
        print(
            f"🎬 【即梦API】本地任务: {task.id if task else 'None'}, 状态: {task.status if task else 'None'}"
        )

        # 验证任务所有权
        if not task:
            print(f"❌ 【即梦API】任务不存在: {task_id}")
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.user_id != user.id:
            print(
                f"❌ 【即梦API】无权访问任务: 任务用户={task.user_id}, 请求用户={user.id}"
            )
            raise HTTPException(status_code=404, detail="无权访问此任务")

        # 如果任务已完成，直接返回
        if task.status in ["succeed", "failed"]:
            print(f"🎬 【即梦API】任务已完成: {task.id}")
            return task.to_dict()

        # 如果任务未完成且有external_task_id，查询即梦API获取最新状态
        if task.external_task_id and task.status not in ["succeed", "failed"]:
            try:
                print(f"🎬 【即梦API】查询即梦API获取最新状态: {task.external_task_id}")

                # 获取即梦客户端
                client = get_jimeng_client()

                # 查询远程任务状态
                api_result = await client.query_task(task.external_task_id)
                print(f"🎬 【即梦API】API查询结果: {api_result}")

                if api_result.get("code") == "success":
                    api_data = api_result.get("data", {})
                    new_status = api_data.get("status", task.status)
                    new_progress = api_data.get("progress", task.progress)
                    video_url = api_data.get("video_url")
                    fail_reason = api_data.get("fail_reason")

                    # 更新本地任务状态
                    with get_db() as db:
                        db_task = (
                            db.query(JimengTask)
                            .filter(JimengTask.id == task.id)
                            .first()
                        )
                        if db_task:
                            db_task.status = new_status
                            db_task.progress = new_progress

                            if video_url:
                                db_task.video_url = video_url
                                print(f"✅ 【即梦API】更新视频URL: {video_url}")

                            if fail_reason:
                                db_task.fail_reason = fail_reason

                            if new_status in ["succeed", "failed"]:
                                db_task.complete_time = datetime.utcnow()

                            db_task.updated_at = datetime.utcnow()
                            db.commit()
                            db.refresh(db_task)

                            # 返回更新后的任务
                            return db_task.to_dict()
                else:
                    print(
                        f"⚠️ 【即梦API】API查询失败: {api_result.get('message', '未知错误')}"
                    )

            except Exception as e:
                print(f"❌ 【即梦API】查询API状态失败: {e}")
                # 即使查询失败，也返回本地状态

        # 返回当前本地状态
        print(f"🎬 【即梦API】返回本地任务状态")
        return task.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【即梦API】获取任务状态失败: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


# ======================== 用户功能 ========================


@router.get("/history")
async def get_user_jimeng_history(
    page: int = 1, limit: int = 20, user=Depends(get_verified_user)
):
    """获取用户任务历史"""
    try:
        tasks = JimengTask.get_user_tasks(user.id, page, limit)
        total = JimengTask.get_user_task_count(user.id)

        return {
            "data": [task.to_dict() for task in tasks],
            "total": total,
            "page": page,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务历史失败: {str(e)}")


@router.get("/credits")
async def get_user_jimeng_credits(user=Depends(get_verified_user)):
    """获取用户积分余额"""
    try:
        balance = get_user_credit_balance(user.id)
        return {"balance": balance}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取积分失败: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_jimeng_task(task_id: str, user=Depends(get_verified_user)):
    """删除用户任务"""
    try:
        # 验证任务所有权
        task = JimengTask.get_task_by_id(task_id)
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
async def get_jimeng_system_stats(user=Depends(get_admin_user)):
    """获取系统即梦统计 - 管理员专用"""
    try:
        from open_webui.utils.jimeng import get_system_jimeng_stats

        stats = get_system_jimeng_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")


@router.get("/stats/user")
async def get_jimeng_user_stats(user=Depends(get_verified_user)):
    """获取用户即梦统计"""
    try:
        from open_webui.utils.jimeng import get_user_jimeng_stats

        stats = get_user_jimeng_stats(user.id)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户统计失败: {str(e)}")


# ======================== 管理员功能 ========================


@router.post("/admin/credits/add")
async def admin_add_jimeng_credits(
    target_user_id: str, amount: int, reason: str = "", user=Depends(get_admin_user)
):
    """管理员给用户充值积分"""
    try:
        from open_webui.utils.jimeng import admin_add_credits_to_user

        new_balance = admin_add_credits_to_user(user.id, target_user_id, amount, reason)
        return {
            "message": f"给用户 {target_user_id} 充值 {amount} 积分",
            "new_balance": new_balance,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"充值积分失败: {str(e)}")


@router.post("/admin/credits/deduct")
async def admin_deduct_jimeng_credits(
    target_user_id: str, amount: int, reason: str = "", user=Depends(get_admin_user)
):
    """管理员扣除用户积分"""
    try:
        from open_webui.utils.jimeng import admin_deduct_credits_from_user

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
        from open_webui.utils.jimeng import cleanup_old_tasks

        deleted_count = cleanup_old_tasks(days)
        return {"message": f"清理了 {deleted_count} 个旧任务（超过 {days} 天）"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理任务失败: {str(e)}")


# ======================== 临时文件服务 ========================


@router.get("/temp-image/{filename}")
async def serve_temp_image(filename: str):
    """提供临时图片文件 - 无需认证，供即梦API访问"""
    try:
        # 安全检查：只允许访问即梦临时图片目录
        if not filename.startswith("jimeng_temp_"):
            raise HTTPException(status_code=404, detail="File not found")

        # 构建文件路径
        temp_dir = os.path.join(CACHE_DIR, "jimeng_temp_images")
        file_path = os.path.abspath(os.path.join(temp_dir, filename))

        # 防止路径遍历攻击
        if not file_path.startswith(os.path.abspath(temp_dir)):
            raise HTTPException(status_code=404, detail="File not found")

        # 检查文件是否存在
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        print(f"🎬 【即梦临时文件】提供文件: {file_path}")
        return FileResponse(file_path)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 【即梦临时文件】服务文件失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve file")
