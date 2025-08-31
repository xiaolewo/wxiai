"""
Veo视频生成工具类
包含API客户端、积分管理、任务处理、云存储等工具
"""

import httpx
import asyncio
import json
import base64
import uuid
import os
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import logging

from open_webui.models.veo import VeoConfig, VeoTask, VeoCredit, VeoGenerateRequest
from open_webui.models.credits import Credits
from open_webui.services.file_manager import get_file_manager
from open_webui.config import CACHE_DIR
import aiofiles

logger = logging.getLogger(__name__)

# ======================== API客户端 ========================


class VeoApiClient:
    """Veo API客户端"""

    def __init__(self, config: VeoConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.timeout = httpx.Timeout(60.0)

    async def generate_video(self, request: VeoGenerateRequest) -> dict:
        """生成视频 - 统一接口支持文生视频和图生视频"""
        url = f"{self.base_url}/google/v1/models/veo/videos"
        
        # 构建请求数据
        payload = {
            "prompt": request.prompt.strip(),
            "model": request.model,
            "enhance_prompt": request.enhance_prompt
        }
        
        # 如果有图片输入，添加images字段
        if request.images:
            payload["images"] = request.images
        
        logger.info(f"🎬 【Veo客户端】发起视频生成请求: {request.model}")
        logger.info(f"🎬 【Veo客户端】请求URL: {url}")
        logger.info(f"🎬 【Veo客户端】请求头数量: {len(self.headers)}")
        logger.debug(f"🎬 【Veo客户端】请求payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            logger.info("🎬 【Veo客户端】创建HTTP客户端...")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("🎬 【Veo客户端】发送POST请求...")
                response = await client.post(url, json=payload, headers=self.headers)
                
                logger.info(f"🎬 【Veo客户端】收到响应: status_code={response.status_code}")
                
                # 检查响应状态
                if not response.is_success:
                    error_text = response.text
                    logger.error(f"🎬 【Veo客户端】HTTP错误 {response.status_code}: {error_text}")
                    return {"success": False, "error": f"HTTP错误 {response.status_code}: {error_text}"}
                
                logger.info("🎬 【Veo客户端】解析JSON响应...")
                result = response.json()
                logger.info(f"🎬 【Veo客户端】API响应解析成功: code={result.get('code')}, message={result.get('message', '')}")
                
                if result.get("code") == "success":
                    logger.info(f"🎬 【Veo客户端】API调用成功: task_id={result.get('data')}")
                    return {
                        "success": True,
                        "task_id": result.get("data"),
                        "message": result.get("message", "")
                    }
                else:
                    logger.error(f"🎬 【Veo客户端】API返回失败: {result.get('message', '生成失败')}")
                    return {
                        "success": False,
                        "error": result.get("message", "生成失败")
                    }
                    
        except httpx.ConnectError as e:
            error_msg = f"无法连接到Veo API服务器 ({self.base_url})，请检查网络连接或服务器状态"
            logger.error(f"🎬 【Veo客户端】连接错误: {error_msg}")
            logger.error(f"🎬 【Veo客户端】连接详情: {str(e)}")
            return {"success": False, "error": error_msg}
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"🎬 【Veo客户端】HTTP状态错误: {error_msg}")
            return {"success": False, "error": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"请求超时，Veo API服务器响应时间过长"
            logger.error(f"🎬 【Veo客户端】请求超时: {error_msg}")
            logger.error(f"🎬 【Veo客户端】超时详情: {str(e)}")
            return {"success": False, "error": error_msg}
        except json.JSONDecodeError as e:
            error_msg = f"Veo API返回的响应格式错误，无法解析JSON数据"
            logger.error(f"🎬 【Veo客户端】JSON解析错误: {error_msg}")
            logger.error(f"🎬 【Veo客户端】解析详情: {str(e)}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"调用Veo API时发生未知错误: {str(e)}"
            logger.error(f"🎬 【Veo客户端】未知异常: {error_msg}")
            logger.exception("🎬 【Veo客户端】异常堆栈:")
            return {"success": False, "error": error_msg}

    async def query_task(self, task_id: str) -> dict:
        """查询任务状态"""
        url = f"{self.base_url}/google/v1/tasks/{task_id}"
        
        logger.debug(f"🎬 【Veo客户端】查询任务状态: {task_id}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                result = response.json()
                logger.debug(f"🎬 【Veo客户端】任务状态响应: {result}")
                
                if result.get("code") == "success":
                    task_data = result.get("data", {})
                    return {
                        "success": True,
                        "status": task_data.get("status", "UNKNOWN"),
                        "progress": task_data.get("progress", "0%"),
                        "fail_reason": task_data.get("fail_reason", ""),
                        "video_url": task_data.get("data", {}).get("video_url"),
                        "finish_time": task_data.get("finish_time"),
                        "raw_data": task_data
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("message", "查询失败")
                    }
                    
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(f"🎬 【Veo客户端】查询HTTP错误: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"查询失败: {str(e)}"
            logger.error(f"🎬 【Veo客户端】查询异常: {error_msg}")
            return {"success": False, "error": error_msg}


# ======================== 积分管理 ========================


def validate_user_credits(user_id: str, required_credits: int) -> bool:
    """验证用户积分是否足够"""
    try:
        user_credits = Credits.get_user_credits(user_id)
        current_balance = int(user_credits.credit) if user_credits else 0
        
        logger.info(f"💰 【Veo积分】用户 {user_id} 当前积分: {current_balance}, 需要积分: {required_credits}")
        
        if current_balance >= required_credits:
            return True
        else:
            logger.warning(f"💰 【Veo积分】用户 {user_id} 积分不足")
            return False
            
    except Exception as e:
        logger.error(f"💰 【Veo积分】验证积分时出错: {str(e)}")
        return False


def deduct_user_credits(user_id: str, credits: int, task_id: str, model_name: str = None) -> bool:
    """扣除用户积分"""
    try:
        user_credits = Credits.get_user_credits(user_id)
        if not user_credits:
            logger.error(f"💰 【Veo积分】用户 {user_id} 积分记录不存在")
            return False
        
        credits_before = int(user_credits.credit)
        credits_after = credits_before - credits
        
        # 更新用户积分
        success = Credits.update_user_credits(user_id, credits_after)
        
        if success:
            # 记录积分变动
            VeoCredit.create_credit_log({
                "user_id": user_id,
                "task_id": task_id,
                "credit_amount": credits,
                "credits_before": credits_before,
                "credits_after": credits_after,
                "operation_type": "deduct",
                "model_name": model_name,
                "description": f"Veo视频生成消费 - 模型: {model_name}"
            })
            
            logger.info(f"💰 【Veo积分】用户 {user_id} 扣除积分 {credits}，余额: {credits_before} -> {credits_after}")
            return True
        else:
            logger.error(f"💰 【Veo积分】扣除用户 {user_id} 积分失败")
            return False
            
    except Exception as e:
        logger.error(f"💰 【Veo积分】扣除积分时出错: {str(e)}")
        return False


def add_user_credits(user_id: str, credits: int, task_id: str, reason: str = "退费") -> bool:
    """返还用户积分"""
    try:
        user_credits = Credits.get_user_credits(user_id)
        if not user_credits:
            logger.error(f"💰 【Veo积分】用户 {user_id} 积分记录不存在")
            return False
        
        credits_before = int(user_credits.credit)
        credits_after = credits_before + credits
        
        # 更新用户积分
        success = Credits.update_user_credits(user_id, credits_after)
        
        if success:
            # 记录积分变动
            VeoCredit.create_credit_log({
                "user_id": user_id,
                "task_id": task_id,
                "credit_amount": credits,
                "credits_before": credits_before,
                "credits_after": credits_after,
                "operation_type": "refund",
                "description": f"Veo视频生成退费 - {reason}"
            })
            
            logger.info(f"💰 【Veo积分】用户 {user_id} 返还积分 {credits}，余额: {credits_before} -> {credits_after}")
            return True
        else:
            logger.error(f"💰 【Veo积分】返还用户 {user_id} 积分失败")
            return False
            
    except Exception as e:
        logger.error(f"💰 【Veo积分】返还积分时出错: {str(e)}")
        return False


def get_user_credit_balance(user_id: str) -> int:
    """获取用户积分余额"""
    try:
        user_credits = Credits.get_user_credits(user_id)
        return int(user_credits.credit) if user_credits else 0
    except Exception as e:
        logger.error(f"💰 【Veo积分】获取用户 {user_id} 积分余额失败: {str(e)}")
        return 0


# ======================== 云存储处理 ========================


async def upload_image_to_cloud(image_data: str, user_id: str, task_id: str) -> Optional[str]:
    """上传图片到云存储"""
    try:
        file_manager = get_file_manager()
        
        # 生成文件名
        timestamp = int(datetime.now().timestamp())
        filename = f"{task_id}_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        if image_data.startswith('http'):
            # URL图片，使用文件管理器的save_generated_content方法
            success, message, file_record = await file_manager.save_generated_content(
                user_id=user_id,
                file_url=image_data,
                filename=filename,
                file_type="image",
                source_type="veo",
                source_task_id=task_id,
                metadata={"input_type": "image", "from_url": True}
            )
            
            if success and file_record and file_record.cloud_url:
                logger.info(f"📁 【Veo云存储】图片上传成功: {file_record.cloud_url}")
                return file_record.cloud_url
            else:
                logger.warning(f"📁 【Veo云存储】图片上传失败: {message}")
                return image_data  # 返回原始URL
        
        elif image_data.startswith('data:image/'):
            # Base64图片，先解码再上传
            header, encoded_data = image_data.split(',', 1)
            image_content = base64.b64decode(encoded_data)
            
            # 从header确定文件扩展名
            if 'png' in header:
                filename += '.png'
            else:
                filename += '.jpg'
            
            success, message, file_record = await file_manager.save_generated_content(
                user_id=user_id,
                file_data=image_content,
                filename=filename,
                file_type="image",
                source_type="veo",
                source_task_id=task_id,
                metadata={"input_type": "image", "from_base64": True}
            )
            
            if success and file_record and file_record.cloud_url:
                logger.info(f"📁 【Veo云存储】图片上传成功: {file_record.cloud_url}")
                return file_record.cloud_url
            else:
                logger.warning(f"📁 【Veo云存储】图片上传失败: {message}")
                return None
        else:
            logger.error("📁 【Veo云存储】不支持的图片格式")
            return None
        
    except Exception as e:
        logger.error(f"📁 【Veo云存储】图片上传失败: {str(e)}")
        return None


async def upload_video_to_cloud(video_url: str, task_id: str) -> Optional[str]:
    """下载视频并上传到云存储"""
    try:
        # 从task_id获取用户信息
        task = VeoTask.get_task_by_id(task_id)
        if not task:
            logger.error(f"📁 【Veo云存储】任务 {task_id} 不存在")
            return video_url
            
        file_manager = get_file_manager()
        
        # 生成文件名
        timestamp = int(datetime.now().timestamp())
        filename = f"{task_id}_{timestamp}.mp4"
        
        success, message, file_record = await file_manager.save_generated_content(
            user_id=task.user_id,
            file_url=video_url,
            filename=filename,
            file_type="video",
            source_type="veo",
            source_task_id=task_id,
            metadata={"output_type": "video", "model": task.model}
        )
        
        if success and file_record and file_record.cloud_url:
            logger.info(f"📁 【Veo云存储】视频上传成功: {file_record.cloud_url}")
            return file_record.cloud_url
        else:
            logger.warning(f"📁 【Veo云存储】视频上传失败: {message}")
            return video_url  # 返回原始URL
        
    except Exception as e:
        logger.error(f"📁 【Veo云存储】视频上传失败: {str(e)}")
        return video_url


# ======================== 任务处理 ========================


async def process_veo_generation(request: VeoGenerateRequest, user_id: str) -> dict:
    """处理Veo视频生成请求"""
    task_id = str(uuid.uuid4())
    
    try:
        logger.info(f"🎬 【Veo处理】开始处理用户 {user_id} 的生成请求，task_id: {task_id}")
        logger.info(f"🎬 【Veo处理】请求参数: model={request.model}, prompt='{request.prompt[:100]}...', enhance_prompt={request.enhance_prompt}")
        
        # 获取配置
        logger.info("🎬 【Veo处理】获取配置...")
        config = VeoConfig.get_config()
        if not config or not config.enabled:
            logger.error("🎬 【Veo处理】Veo服务未启用")
            return {"success": False, "error": "Veo服务未启用"}
        
        logger.info(f"🎬 【Veo处理】配置获取成功: enabled={config.enabled}, base_url={config.base_url}")
        
        # 计算积分消耗
        logger.info(f"🎬 【Veo处理】计算模型 {request.model} 的积分消耗...")
        credits_cost = config.get_credits_cost(request.model)
        logger.info(f"🎬 【Veo处理】积分消耗: {credits_cost}")
        
        # 验证和扣除积分
        logger.info(f"🎬 【Veo处理】验证用户积分: 需要 {credits_cost} 积分")
        if not validate_user_credits(user_id, credits_cost):
            logger.error(f"🎬 【Veo处理】用户 {user_id} 积分不足")
            return {"success": False, "error": "积分不足"}
        
        logger.info(f"🎬 【Veo处理】扣除用户积分...")
        if not deduct_user_credits(user_id, credits_cost, task_id, request.model):
            logger.error(f"🎬 【Veo处理】用户 {user_id} 积分扣除失败")
            return {"success": False, "error": "积分扣除失败"}
        
        logger.info(f"🎬 【Veo处理】积分扣除成功")
        
        # 处理输入图片（如果有）
        cloud_input_images = []
        if request.images:
            logger.info(f"🎬 【Veo处理】开始处理 {len(request.images)} 张输入图片...")
            for i, image in enumerate(request.images):
                logger.info(f"🎬 【Veo处理】上传第 {i+1} 张图片到云存储...")
                cloud_url = await upload_image_to_cloud(image, user_id, f"{task_id}_{i}")
                if cloud_url:
                    logger.info(f"🎬 【Veo处理】图片 {i+1} 上传成功: {cloud_url[:50]}...")
                    cloud_input_images.append(cloud_url)
                else:
                    logger.warning(f"🎬 【Veo处理】图片 {i+1} 上传失败，使用原始数据")
                    # 图片上传失败，使用原始数据
                    cloud_input_images.append(image)
        else:
            logger.info("🎬 【Veo处理】无输入图片，跳过图片处理")
        
        # 创建任务记录
        logger.info("🎬 【Veo处理】创建任务记录...")
        task_data = {
            "id": task_id,
            "user_id": user_id,
            "status": "submitted",
            "prompt": request.prompt,
            "model": request.model,
            "enhance_prompt": request.enhance_prompt,
            "input_images": request.images,
            "cloud_input_images": cloud_input_images,
            "credits_cost": credits_cost,
            "properties": {
                "original_request": request.dict()
            }
        }
        
        logger.info(f"🎬 【Veo处理】任务数据准备完成: {len(task_data)} 个字段")
        task = VeoTask.create_task(task_data)
        logger.info(f"🎬 【Veo处理】任务记录创建成功: {task.id}")
        
        # 创建API客户端并发起请求
        logger.info("🎬 【Veo处理】创建API客户端...")
        api_client = VeoApiClient(config)
        
        # 使用云存储的图片URL进行API调用
        logger.info("🎬 【Veo处理】准备API请求...")
        api_request = VeoGenerateRequest(
            prompt=request.prompt,
            model=request.model,
            enhance_prompt=request.enhance_prompt,
            images=cloud_input_images if cloud_input_images else None
        )
        
        logger.info(f"🎬 【Veo处理】API请求准备完成: images_count={len(cloud_input_images) if cloud_input_images else 0}")
        
        # 调用API
        logger.info("🎬 【Veo处理】开始调用Veo API...")
        api_result = await api_client.generate_video(api_request)
        logger.info(f"🎬 【Veo处理】Veo API返回结果: success={api_result.get('success')}, message='{api_result.get('message', '')}'")
        
        if 'error' in api_result:
            logger.error(f"🎬 【Veo处理】Veo API返回错误: {api_result['error']}")
        
        if api_result["success"]:
            logger.info(f"🎬 【Veo处理】API调用成功，external_task_id: {api_result['task_id']}")
            # 更新任务状态
            logger.info("🎬 【Veo处理】更新任务状态为processing...")
            VeoTask.update_task_status(task_id, {
                "external_task_id": api_result["task_id"],
                "status": "processing",
                "progress": "5%"
            })
            
            # 启动后台任务监控
            logger.info("🎬 【Veo处理】启动后台任务监控...")
            asyncio.create_task(monitor_veo_task(task_id, config))
            
            logger.info(f"🎬 【Veo处理】任务提交完成，返回成功结果")
            return {
                "success": True,
                "task_id": task_id,
                "external_task_id": api_result["task_id"],
                "credits_cost": credits_cost,
                "message": "任务已提交，正在处理中"
            }
        else:
            logger.error(f"🎬 【Veo处理】API调用失败: {api_result['error']}")
            # API调用失败，退还积分
            logger.info("🎬 【Veo处理】退还积分...")
            add_user_credits(user_id, credits_cost, task_id, "API调用失败")
            logger.info("🎬 【Veo处理】更新任务状态为失败...")
            VeoTask.update_task_status(task_id, {
                "status": "failed",
                "fail_reason": api_result["error"]
            })
            
            logger.info(f"🎬 【Veo处理】返回失败结果: {api_result['error']}")
            return {
                "success": False,
                "error": api_result["error"],
                "task_id": task_id
            }
            
    except Exception as e:
        error_msg = f"处理Veo生成请求时出错: {str(e)}"
        logger.error(f"🎬 【Veo处理】{error_msg}")
        logger.exception("🎬 【Veo处理】异常堆栈:")
        
        # 尝试退还积分
        try:
            logger.info("🎬 【Veo处理】异常处理：尝试退还积分...")
            add_user_credits(user_id, credits_cost, task_id, "处理异常")
        except Exception as refund_error:
            logger.error(f"🎬 【Veo处理】退还积分失败: {str(refund_error)}")
            
        return {"success": False, "error": error_msg}


async def monitor_veo_task(task_id: str, config: VeoConfig):
    """监控Veo任务状态"""
    api_client = VeoApiClient(config)
    max_attempts = 60  # 最多监控15分钟 (60 * 15s)
    attempt = 0
    
    logger.info(f"🔍 【Veo监控】开始监控任务: {task_id}")
    
    while attempt < max_attempts:
        try:
            await asyncio.sleep(config.query_interval / 1000)  # 转换为秒
            
            task = VeoTask.get_task_by_id(task_id)
            if not task or not task.external_task_id:
                logger.warning(f"🔍 【Veo监控】任务 {task_id} 不存在或缺少外部任务ID")
                break
            
            # 查询任务状态
            result = await api_client.query_task(task.external_task_id)
            
            if not result["success"]:
                logger.error(f"🔍 【Veo监控】查询任务 {task_id} 失败: {result['error']}")
                VeoTask.update_task_status(task_id, {
                    "status": "failed",
                    "fail_reason": result["error"]
                })
                break
            
            status = result["status"]
            progress = result["progress"]
            
            logger.debug(f"🔍 【Veo监控】任务 {task_id} 状态: {status}, 进度: {progress}")
            
            # 更新任务状态
            update_data = {
                "progress": progress,
                "updated_at": datetime.now()
            }
            
            if status == "SUCCESS":
                video_url = result["video_url"]
                if video_url:
                    # 下载视频并上传到云存储
                    cloud_video_url = await upload_video_to_cloud(video_url, task_id)
                    
                    update_data.update({
                        "status": "completed",
                        "result_video_url": video_url,
                        "cloud_video_url": cloud_video_url,
                        "progress": "100%",
                        "finish_time": datetime.now()
                    })
                    
                    VeoTask.update_task_status(task_id, update_data)
                    logger.info(f"🎬 【Veo监控】任务 {task_id} 完成")
                    break
                else:
                    update_data.update({
                        "status": "failed",
                        "fail_reason": "未获取到视频结果"
                    })
                    VeoTask.update_task_status(task_id, update_data)
                    break
                    
            elif status == "FAILURE":
                update_data.update({
                    "status": "failed",
                    "fail_reason": result["fail_reason"] or "生成失败"
                })
                VeoTask.update_task_status(task_id, update_data)
                
                # 生成失败，退还积分
                if task:
                    add_user_credits(
                        task.user_id, 
                        task.credits_cost, 
                        task_id, 
                        "生成失败"
                    )
                logger.warning(f"🎬 【Veo监控】任务 {task_id} 生成失败")
                break
                
            elif status in ["IN_PROGRESS", "SUBMITTED", "NOT_START"]:
                # 任务进行中，更新状态
                update_data["status"] = "processing"
                VeoTask.update_task_status(task_id, update_data)
                
            attempt += 1
            
        except Exception as e:
            logger.error(f"🔍 【Veo监控】监控任务 {task_id} 时出错: {str(e)}")
            attempt += 1
    
    # 监控超时处理
    if attempt >= max_attempts:
        logger.warning(f"🔍 【Veo监控】任务 {task_id} 监控超时")
        VeoTask.update_task_status(task_id, {
            "status": "timeout",
            "fail_reason": "任务监控超时"
        })
        
        # 超时退还积分
        task = VeoTask.get_task_by_id(task_id)
        if task and task.credits_cost:
            add_user_credits(task.user_id, task.credits_cost, task_id, "任务超时")