"""
可灵对口型功能路由器
提供配置管理、任务提交、历史记录等API接口
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from open_webui.models.kling_lip_sync import (
    KlingLipSyncConfigs,
    KlingLipSyncTasks,
    KlingLipSyncConfigForm,
    KlingLipSyncRequest,
    KlingLipSyncTaskForm,
)
from open_webui.models.credits import Credits
from open_webui.utils.kling_lip_sync_api import (
    get_kling_lip_sync_client,
    get_kling_lip_sync_processor,
    KlingLipSyncAPIError,
)
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_access, has_permission

logger = logging.getLogger(__name__)

router = APIRouter()

# ======================== 管理员配置接口 ========================


@router.get("/config")
async def get_kling_lip_sync_config(user=Depends(get_admin_user)):
    """获取可灵对口型配置（管理员）"""
    try:
        config = KlingLipSyncConfigs.get_config()
        if config:
            config_dict = config.to_dict()
            # 隐藏敏感信息
            if config_dict.get("api_key"):
                config_dict["api_key"] = "***" + config_dict["api_key"][-4:]
            return config_dict
        else:
            return {
                "enabled": False,
                "base_url": "https://api.klingai.com",
                "api_key": "",
                "credits_per_task": 50,
                "max_concurrent_tasks": 3,
                "task_timeout": 300000,
                "default_mode": "text2video",
                "default_voice_id": "girlfriend_1_speech02",
                "default_voice_language": "zh",
            }
    except Exception as e:
        logger.error(f"获取可灵对口型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/config")
async def save_kling_lip_sync_config(
    config_form: KlingLipSyncConfigForm, user=Depends(get_admin_user)
):
    """保存可灵对口型配置（管理员）"""
    try:
        config_data = config_form.dict()
        config = KlingLipSyncConfigs.save_config(config_data)

        return {
            "success": True,
            "message": "配置保存成功",
            "config": config.to_dict(),
        }
    except Exception as e:
        logger.error(f"保存可灵对口型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/config/user")
async def get_user_kling_lip_sync_config(user=Depends(get_verified_user)):
    """获取用户可见的可灵对口型配置"""
    try:
        config = KlingLipSyncConfigs.get_config()
        if config and config.enabled:
            return {
                "enabled": True,
                "default_mode": config.default_mode,
                "default_voice_id": config.default_voice_id,
                "default_voice_language": config.default_voice_language,
                "credits_per_task": config.credits_per_task,
                "max_concurrent_tasks": config.max_concurrent_tasks,
            }
        else:
            return {"enabled": False}
    except Exception as e:
        logger.error(f"获取用户配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/test-connection")
async def test_kling_lip_sync_connection(user=Depends(get_admin_user)):
    """测试可灵对口型API连接（管理员）"""
    try:
        client = get_kling_lip_sync_client()
        result = await client.test_connection()
        return result
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        return {
            "success": False,
            "message": f"测试连接失败: {str(e)}",
            "error": str(e),
        }


# ======================== 音色和语言配置 ========================


@router.get("/voices")
async def get_available_voices(user=Depends(get_verified_user)):
    """获取可用音色列表"""
    return {
        "voices": [
            # 中文音色
            {
                "id": "genshin_vindi2",
                "name": "阳光少年",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "zhinen_xuesheng",
                "name": "懂事小弟",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "tiyuxi_xuedi",
                "name": "运动少年",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "ai_shatang",
                "name": "青春少女",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "genshin_klee2",
                "name": "温柔小妹",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "genshin_kirara",
                "name": "元气少女",
                "language": "zh",
                "gender": "female",
            },
            {"id": "ai_kaiya", "name": "阳光男生", "language": "zh", "gender": "male"},
            {
                "id": "tiexin_nanyou",
                "name": "幽默小哥",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "ai_chenjiahao_712",
                "name": "文艺小哥",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "girlfriend_1_speech02",
                "name": "甜美邻家",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "chat1_female_new-3",
                "name": "温柔姐姐",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "girlfriend_2_speech02",
                "name": "职场女青",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "cartoon-boy-07",
                "name": "活泼男童",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "cartoon-girl-01",
                "name": "俏皮女童",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "ai_huangyaoshi_712",
                "name": "稳重老爸",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "you_pingjing",
                "name": "温柔妈妈",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "ai_laoguowang_712",
                "name": "严肃上司",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "chengshu_jiejie",
                "name": "优雅贵妇",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "zhuxi_speech02",
                "name": "慈祥爷爷",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "uk_oldman3",
                "name": "唠叨爷爷",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "laopopo_speech02",
                "name": "唠叨奶奶",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "heainainai_speech02",
                "name": "和蔼奶奶",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "dongbeilaotie_speech02",
                "name": "东北老铁",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "chongqingxiaohuo_speech02",
                "name": "重庆小伙",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "chuanmeizi_speech02",
                "name": "四川妹子",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "chaoshandashu_speech02",
                "name": "潮汕大叔",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "ai_taiwan_man2_speech02",
                "name": "台湾男生",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "xianzhanggui_speech02",
                "name": "西安掌柜",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "tianjinjiejie_speech02",
                "name": "天津姐姐",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "diyinnansang_DB_CN_M_04-v2",
                "name": "新闻播报男",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "yizhipiannan-v1",
                "name": "译制片男",
                "language": "zh",
                "gender": "male",
            },
            {
                "id": "guanxiaofang-v2",
                "name": "元气少女",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "tianmeixuemei-v1",
                "name": "撒娇女友",
                "language": "zh",
                "gender": "female",
            },
            {
                "id": "daopianyansang-v1",
                "name": "刀片烟嗓",
                "language": "zh",
                "gender": "male",
            },
            {"id": "mengwa-v1", "name": "乖巧正太", "language": "zh", "gender": "male"},
            # 英文音色
            {
                "id": "genshin_vindi2",
                "name": "Sunny",
                "language": "en",
                "gender": "male",
            },
            {
                "id": "zhinen_xuesheng",
                "name": "Sage",
                "language": "en",
                "gender": "male",
            },
            {"id": "AOT", "name": "Ace", "language": "en", "gender": "male"},
            {
                "id": "ai_shatang",
                "name": "Blossom",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "genshin_klee2",
                "name": "Peppy",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "genshin_kirara",
                "name": "Dove",
                "language": "en",
                "gender": "female",
            },
            {"id": "ai_kaiya", "name": "Shine", "language": "en", "gender": "male"},
            {
                "id": "oversea_male1",
                "name": "Anchor",
                "language": "en",
                "gender": "male",
            },
            {
                "id": "ai_chenjiahao_712",
                "name": "Lyric",
                "language": "en",
                "gender": "male",
            },
            {
                "id": "girlfriend_4_speech02",
                "name": "Melody",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "chat1_female_new-3",
                "name": "Tender",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "chat_0407_5-1",
                "name": "Siren",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "cartoon-boy-07",
                "name": "Zippy",
                "language": "en",
                "gender": "male",
            },
            {"id": "uk_boy1", "name": "Bud", "language": "en", "gender": "male"},
            {
                "id": "cartoon-girl-01",
                "name": "Sprite",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "PeppaPig_platform",
                "name": "Candy",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "ai_huangzhong_712",
                "name": "Beacon",
                "language": "en",
                "gender": "male",
            },
            {
                "id": "ai_huangyaoshi_712",
                "name": "Rock",
                "language": "en",
                "gender": "male",
            },
            {
                "id": "ai_laoguowang_712",
                "name": "Titan",
                "language": "en",
                "gender": "male",
            },
            {
                "id": "chengshu_jiejie",
                "name": "Grace",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "you_pingjing",
                "name": "Helen",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "calm_story1",
                "name": "Lore",
                "language": "en",
                "gender": "neutral",
            },
            {"id": "uk_man2", "name": "Crag", "language": "en", "gender": "male"},
            {
                "id": "laopopo_speech02",
                "name": "Prattle",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "heainainai_speech02",
                "name": "Hearth",
                "language": "en",
                "gender": "female",
            },
            {
                "id": "reader_en_m-v1",
                "name": "The Reader",
                "language": "en",
                "gender": "male",
            },
            {
                "id": "commercial_lady_en_f-v1",
                "name": "Commercial Lady",
                "language": "en",
                "gender": "female",
            },
        ]
    }


@router.get("/languages")
async def get_supported_languages(user=Depends(get_verified_user)):
    """获取支持的语言列表"""
    return {
        "languages": [
            {"code": "zh", "name": "中文"},
            {"code": "en", "name": "English"},
        ]
    }


# ======================== 任务管理接口 ========================


@router.post("/lip-sync")
async def create_lip_sync_task(
    task_form: KlingLipSyncTaskForm, user=Depends(get_verified_user)
):
    """创建对口型任务"""
    try:
        # 检查功能是否启用
        if not KlingLipSyncConfigs.is_enabled():
            raise HTTPException(status_code=400, detail="可灵对口型功能未启用")

        # 验证输入参数
        request = task_form.request
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="对口型文本不能为空")

        if not request.video_id and not request.video_url:
            raise HTTPException(
                status_code=400, detail="video_id 和 video_url 必须提供其中一个"
            )

        # 检查系统积分是否足够（任务处理器会负责实际扣除）
        config = KlingLipSyncConfigs.get_config()
        credits_required = config.credits_per_task if config else 50

        user_credits = Credits.get_credit_by_user_id(user.id)
        if not user_credits or float(user_credits.credit) < credits_required:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"积分不足，需要 {credits_required} 积分",
                    "required_credits": credits_required,
                    "current_credits": (
                        float(user_credits.credit) if user_credits else 0
                    ),
                },
            )

        # 提交任务
        processor = get_kling_lip_sync_processor()
        task_data = {
            "task_id": f"lip_sync_{user.id}_{int(time.time() * 1000)}",
            "video_id": request.video_id,
            "video_url": request.video_url,
            "mode": request.mode,
            "text": request.text,
            "voice_id": request.voice_id,
            "voice_language": request.voice_language,
        }

        result = await processor.submit_lip_sync_task(user.id, task_data)

        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result["message"],
                    "task_id": result["task_id"],
                    "external_task_id": result.get("external_task_id"),
                    "credits_consumed": result.get(
                        "credits_consumed", credits_required
                    ),
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result["message"],
                    "error": result.get("error"),
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建对口型任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/task/{task_id}")
async def get_lip_sync_task(task_id: str, user=Depends(get_verified_user)):
    """获取对口型任务详情"""
    try:
        task = KlingLipSyncTasks.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 权限检查：只能查看自己的任务
        if task.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="无权访问此任务")

        return task.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")


@router.get("/tasks")
async def get_user_lip_sync_tasks(
    limit: int = 50, offset: int = 0, user=Depends(get_verified_user)
):
    """获取用户对口型任务列表"""
    try:
        tasks = KlingLipSyncTasks.get_user_tasks(user.id, limit, offset)

        return {
            "tasks": [task.to_dict() for task in tasks],
            "total": len(tasks),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/history")
async def get_user_lip_sync_history(
    page: int = 1, limit: int = 20, user=Depends(get_verified_user)
):
    """获取用户对口型任务历史记录"""
    try:
        offset = (page - 1) * limit
        tasks = KlingLipSyncTasks.get_user_tasks(user.id, limit, offset)

        return {
            "success": True,
            "data": [task.to_dict() for task in tasks],
            "total": len(tasks),
            "page": page,
            "limit": limit,
            "has_more": len(tasks) == limit,
        }

    except Exception as e:
        logger.error(f"获取任务历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务历史失败: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_lip_sync_task(task_id: str, user=Depends(get_verified_user)):
    """删除对口型任务"""
    try:
        task = KlingLipSyncTasks.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 权限检查
        if task.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="无权删除此任务")

        # 只能删除已完成或失败的任务
        if task.status in ["submitted", "processing"]:
            raise HTTPException(status_code=400, detail="无法删除进行中的任务")

        success = KlingLipSyncTasks.delete_task(task_id)
        if success:
            return {"success": True, "message": "任务删除成功"}
        else:
            raise HTTPException(status_code=500, detail="任务删除失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


# ======================== 视频上传接口 ========================


@router.post("/upload-video")
async def upload_video_for_lip_sync(
    file: UploadFile = File(...), user=Depends(get_verified_user)
):
    """上传视频用于对口型"""
    try:
        # 检查文件类型
        if not file.content_type or not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="请上传视频文件")

        # 检查文件大小 (限制100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        file_size = 0
        content = bytearray()

        while True:
            chunk = await file.read(8192)  # 8KB chunks
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > max_size:
                raise HTTPException(status_code=413, detail="文件大小不能超过100MB")
            content.extend(chunk)

        # 上传到云存储
        try:
            from open_webui.services.file_manager import get_file_manager

            file_manager = get_file_manager()

            # 生成文件名
            file_ext = file.filename.split(".")[-1] if "." in file.filename else "mp4"
            cloud_filename = f"lip_sync_input/{user.id}/{uuid.uuid4().hex}.{file_ext}"

            # 上传文件
            upload_result = await file_manager.upload_file_content(
                content=bytes(content),
                filename=cloud_filename,
                content_type=file.content_type,
                metadata={
                    "user_id": user.id,
                    "original_filename": file.filename,
                    "file_size": file_size,
                    "upload_type": "lip_sync_input",
                    "created_at": datetime.now().isoformat(),
                },
            )

            if upload_result["success"]:
                return {
                    "success": True,
                    "message": "视频上传成功",
                    "video_url": upload_result["url"],
                    "filename": cloud_filename,
                    "file_size": file_size,
                    "content_type": file.content_type,
                }
            else:
                raise HTTPException(
                    status_code=500, detail=f"上传失败: {upload_result['message']}"
                )

        except ImportError:
            raise HTTPException(status_code=500, detail="云存储服务不可用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"视频上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"视频上传失败: {str(e)}")


# ======================== 积分管理接口 ========================


@router.get("/credits")
async def get_user_lip_sync_credits(user=Depends(get_verified_user)):
    """获取用户系统积分"""
    try:
        credits = Credits.get_credit_by_user_id(user.id)
        return {
            "success": True,
            "balance": float(credits.credit) if credits else 0.0,
            "user_id": user.id,
        }

    except Exception as e:
        logger.error(f"获取用户积分失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取积分失败: {str(e)}")


# 积分管理使用系统统一的积分系统，不再需要独立的积分增加接口


# ======================== 健康检查 ========================


@router.get("/health")
async def kling_lip_sync_health_check():
    """健康检查"""
    try:
        config = KlingLipSyncConfigs.get_config()
        return {
            "status": "healthy",
            "enabled": config.enabled if config else False,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
