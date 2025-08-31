"""
谷歌生图业务逻辑工具类
包含API客户端、积分管理、任务处理、云存储等工具
支持OpenAI DALL-E兼容格式
"""

import httpx
import asyncio
import json
import base64
import uuid
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from open_webui.models.google_images import (
    GoogleImagesConfig,
    GoogleImagesTask,
    GoogleImagesCredit,
    GoogleImagesGenerateRequest
)
from open_webui.models.credits import Credits
from open_webui.services.file_manager import get_file_manager

logger = logging.getLogger(__name__)

# ======================== API客户端 ========================

class GoogleImagesApiClient:
    """谷歌生图API客户端 - 兼容OpenAI DALL-E格式"""

    def __init__(self, config: GoogleImagesConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/") if config.base_url else ""
        self.api_key = config.api_key
        self.timeout = httpx.Timeout(float(config.timeout))

    async def generate_image(self, request: GoogleImagesGenerateRequest) -> dict:
        """生成图像 - 支持multipart/form-data格式"""
        url = f"{self.base_url}/v1/images/edits"
        
        logger.info(f"🎨 【谷歌生图】发起图像生成请求: {request.model}")
        logger.info(f"🎨 【谷歌生图】请求URL: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 准备multipart/form-data
                files = []
                data = {
                    "model": request.model,
                    "prompt": request.prompt
                }
                
                # 添加可选参数
                if request.size:
                    data["size"] = request.size
                if request.n:
                    data["n"] = str(request.n)
                if request.quality:
                    data["quality"] = request.quality
                if request.style:
                    data["style"] = request.style
                
                # 处理图片文件
                if request.images:
                    for i, image_data in enumerate(request.images):
                        if image_data.startswith('data:image/'):
                            # Base64格式图片
                            header, encoded_data = image_data.split(',', 1)
                            image_content = base64.b64decode(encoded_data)
                            
                            # 确定文件扩展名
                            if 'png' in header:
                                filename = f"image_{i}.png"
                                content_type = "image/png"
                            else:
                                filename = f"image_{i}.jpg"
                                content_type = "image/jpeg"
                            
                            files.append(
                                ("image", (filename, image_content, content_type))
                            )
                        elif image_data.startswith('http'):
                            # URL格式图片，需要下载
                            try:
                                img_response = await client.get(image_data)
                                if img_response.is_success:
                                    content_type = img_response.headers.get('content-type', 'image/jpeg')
                                    ext = 'png' if 'png' in content_type else 'jpg'
                                    filename = f"image_{i}.{ext}"
                                    
                                    files.append(
                                        ("image", (filename, img_response.content, content_type))
                                    )
                                else:
                                    logger.warning(f"🎨 【谷歌生图】无法下载图片: {image_data}")
                            except Exception as e:
                                logger.error(f"🎨 【谷歌生图】下载图片失败: {str(e)}")
                
                # 设置请求头
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                logger.info(f"🎨 【谷歌生图】准备发送请求，数据字段: {list(data.keys())}, 文件数量: {len(files)}")
                
                # 发送请求 - 强制使用multipart/form-data格式
                if not files:
                    # 即使没有文件也要使用multipart格式，添加一个空文件占位符
                    files = [("placeholder", ("", b"", "text/plain"))]
                
                response = await client.post(
                    url, 
                    data=data,
                    files=files,
                    headers=headers
                )
                
                logger.info(f"🎨 【谷歌生图】收到响应: status_code={response.status_code}")
                
                # 检查响应状态
                if not response.is_success:
                    error_text = response.text
                    logger.error(f"🎨 【谷歌生图】HTTP错误 {response.status_code}: {error_text}")
                    return {
                        "success": False, 
                        "error": f"HTTP错误 {response.status_code}: {error_text}"
                    }
                
                # 解析响应
                try:
                    result = response.json()
                    logger.info(f"🎨 【谷歌生图】API响应解析成功")
                    
                    # 检查响应格式
                    if "data" in result:
                        # OpenAI格式响应
                        images = []
                        for item in result["data"]:
                            if "url" in item:
                                images.append(item["url"])
                            elif "b64_json" in item:
                                images.append(f"data:image/png;base64,{item['b64_json']}")
                        
                        if images:
                            return {
                                "success": True,
                                "images": images,
                                "message": "图像生成成功"
                            }
                        else:
                            return {
                                "success": False,
                                "error": "响应中未找到有效的图像数据"
                            }
                    else:
                        # 其他格式响应
                        return {
                            "success": True,
                            "raw_response": result,
                            "message": "请求成功"
                        }
                        
                except json.JSONDecodeError as e:
                    logger.error(f"🎨 【谷歌生图】JSON解析错误: {str(e)}")
                    return {
                        "success": False,
                        "error": "响应格式错误，无法解析JSON数据"
                    }
                    
        except httpx.ConnectError as e:
            error_msg = f"无法连接到谷歌生图API服务器，请检查网络连接或服务器状态"
            logger.error(f"🎨 【谷歌生图】连接错误: {error_msg}")
            return {"success": False, "error": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"请求超时，谷歌生图API服务器响应时间过长"
            logger.error(f"🎨 【谷歌生图】请求超时: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"调用谷歌生图API时发生未知错误: {str(e)}"
            logger.error(f"🎨 【谷歌生图】未知异常: {error_msg}")
            logger.exception("🎨 【谷歌生图】异常堆栈:")
            return {"success": False, "error": error_msg}

# ======================== 积分管理 ========================

def validate_user_credits(user_id: str, required_credits: int) -> bool:
    """验证用户积分是否足够"""
    try:
        user_credits = Credits.get_user_credits(user_id)
        current_balance = int(user_credits.credit) if user_credits else 0
        
        logger.info(f"💰 【谷歌生图积分】用户 {user_id} 当前积分: {current_balance}, 需要积分: {required_credits}")
        
        return current_balance >= required_credits
    except Exception as e:
        logger.error(f"💰 【谷歌生图积分】验证积分时出错: {str(e)}")
        return False

def deduct_user_credits(user_id: str, credits: int, task_id: str, model_name: str = None) -> bool:
    """扣除用户积分"""
    try:
        user_credits = Credits.get_user_credits(user_id)
        if not user_credits:
            logger.error(f"💰 【谷歌生图积分】用户 {user_id} 积分记录不存在")
            return False
        
        credits_before = int(user_credits.credit)
        credits_after = credits_before - credits
        
        # 更新用户积分
        success = Credits.update_user_credits(user_id, credits_after)
        
        if success:
            # 记录积分变动
            GoogleImagesCredit.create_credit_log({
                "user_id": user_id,
                "task_id": task_id,
                "credit_amount": credits,
                "credits_before": credits_before,
                "credits_after": credits_after,
                "operation_type": "deduct",
                "model_name": model_name,
                "description": f"谷歌生图生成消费 - 模型: {model_name}"
            })
            
            logger.info(f"💰 【谷歌生图积分】用户 {user_id} 扣除积分 {credits}，余额: {credits_before} -> {credits_after}")
            return True
        else:
            logger.error(f"💰 【谷歌生图积分】扣除用户 {user_id} 积分失败")
            return False
    except Exception as e:
        logger.error(f"💰 【谷歌生图积分】扣除积分时出错: {str(e)}")
        return False

def add_user_credits(user_id: str, credits: int, task_id: str, reason: str = "退费") -> bool:
    """返还用户积分"""
    try:
        user_credits = Credits.get_user_credits(user_id)
        if not user_credits:
            logger.error(f"💰 【谷歌生图积分】用户 {user_id} 积分记录不存在")
            return False
        
        credits_before = int(user_credits.credit)
        credits_after = credits_before + credits
        
        # 更新用户积分
        success = Credits.update_user_credits(user_id, credits_after)
        
        if success:
            # 记录积分变动
            GoogleImagesCredit.create_credit_log({
                "user_id": user_id,
                "task_id": task_id,
                "credit_amount": credits,
                "credits_before": credits_before,
                "credits_after": credits_after,
                "operation_type": "refund",
                "description": f"谷歌生图退费 - {reason}"
            })
            
            logger.info(f"💰 【谷歌生图积分】用户 {user_id} 返还积分 {credits}，余额: {credits_before} -> {credits_after}")
            return True
        else:
            logger.error(f"💰 【谷歌生图积分】返还用户 {user_id} 积分失败")
            return False
    except Exception as e:
        logger.error(f"💰 【谷歌生图积分】返还积分时出错: {str(e)}")
        return False

def get_user_credit_balance(user_id: str) -> int:
    """获取用户积分余额"""
    try:
        user_credits = Credits.get_user_credits(user_id)
        return int(user_credits.credit) if user_credits else 0
    except Exception as e:
        logger.error(f"💰 【谷歌生图积分】获取用户 {user_id} 积分余额失败: {str(e)}")
        return 0

# ======================== 云存储处理 ========================

async def upload_image_to_cloud(image_data: str, user_id: str, task_id: str, index: int = 0) -> Optional[str]:
    """上传图片到云存储"""
    try:
        file_manager = get_file_manager()
        
        # 生成文件名
        timestamp = int(datetime.now().timestamp())
        filename = f"google_images_{task_id}_{index}_{timestamp}"
        
        if image_data.startswith('http'):
            # URL图片
            success, message, file_record = await file_manager.save_generated_content(
                user_id=user_id,
                file_url=image_data,
                filename=filename,
                file_type="image",
                source_type="google_images",
                source_task_id=task_id,
                metadata={"input_type": "image", "from_url": True, "index": index}
            )
            
            if success and file_record and file_record.cloud_url:
                logger.info(f"📁 【谷歌生图云存储】图片上传成功: {file_record.cloud_url}")
                return file_record.cloud_url
            else:
                logger.warning(f"📁 【谷歌生图云存储】图片上传失败: {message}")
                return image_data  # 返回原始URL
        
        elif image_data.startswith('data:image/'):
            # Base64图片
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
                source_type="google_images",
                source_task_id=task_id,
                metadata={"input_type": "image", "from_base64": True, "index": index}
            )
            
            if success and file_record and file_record.cloud_url:
                logger.info(f"📁 【谷歌生图云存储】图片上传成功: {file_record.cloud_url}")
                return file_record.cloud_url
            else:
                logger.warning(f"📁 【谷歌生图云存储】图片上传失败: {message}")
                return None
        else:
            logger.error("📁 【谷歌生图云存储】不支持的图片格式")
            return None
        
    except Exception as e:
        logger.error(f"📁 【谷歌生图云存储】图片上传失败: {str(e)}")
        return None

# ======================== 任务处理 ========================

async def process_google_images_generation(request: GoogleImagesGenerateRequest, user_id: str) -> dict:
    """处理谷歌生图生成请求"""
    task_id = str(uuid.uuid4())
    
    try:
        logger.info(f"🎨 【谷歌生图处理】开始处理用户 {user_id} 的生成请求，task_id: {task_id}")
        
        # 获取配置
        config = GoogleImagesConfig.get_config()
        if not config or not config.enabled:
            logger.error("🎨 【谷歌生图处理】服务未启用")
            return {"success": False, "error": "谷歌生图服务未启用"}
        
        # 计算积分消耗
        credits_cost = config.credits_per_generation
        if request.images:
            credits_cost += len(request.images) * config.credits_per_image
        
        logger.info(f"🎨 【谷歌生图处理】积分消耗: {credits_cost}")
        
        # 验证和扣除积分
        if not validate_user_credits(user_id, credits_cost):
            return {"success": False, "error": "积分不足"}
        
        if not deduct_user_credits(user_id, credits_cost, task_id, request.model):
            return {"success": False, "error": "积分扣除失败"}
        
        # 处理输入图片（上传到云存储）
        cloud_input_images = []
        if request.images:
            logger.info(f"🎨 【谷歌生图处理】开始处理 {len(request.images)} 张输入图片...")
            for i, image in enumerate(request.images):
                cloud_url = await upload_image_to_cloud(image, user_id, task_id, i)
                if cloud_url:
                    cloud_input_images.append(cloud_url)
                else:
                    cloud_input_images.append(image)  # 使用原始数据
        
        # 创建任务记录
        task_data = {
            "id": task_id,
            "user_id": user_id,
            "status": "processing",
            "prompt": request.prompt,
            "model": request.model,
            "size": request.size,
            "quality": request.quality,
            "style": request.style,
            "input_images": request.images,
            "cloud_input_images": cloud_input_images,
            "credits_cost": credits_cost,
            "properties": {
                "original_request": request.dict()
            }
        }
        
        task = GoogleImagesTask.create_task(task_data)
        logger.info(f"🎨 【谷歌生图处理】任务记录创建成功: {task.id}")
        
        # 调用API
        api_client = GoogleImagesApiClient(config)
        
        # 使用云存储的图片URL进行API调用
        api_request = GoogleImagesGenerateRequest(
            model=request.model,
            prompt=request.prompt,
            images=cloud_input_images if cloud_input_images else None,
            size=request.size,
            quality=request.quality,
            style=request.style,
            n=request.n
        )
        
        api_result = await api_client.generate_image(api_request)
        
        if api_result["success"]:
            # 处理结果图片（上传到云存储）
            result_images = api_result.get("images", [])
            cloud_result_images = []
            
            if result_images:
                logger.info(f"🎨 【谷歌生图处理】开始处理 {len(result_images)} 张结果图片...")
                for i, image in enumerate(result_images):
                    cloud_url = await upload_image_to_cloud(image, user_id, task_id, f"result_{i}")
                    if cloud_url:
                        cloud_result_images.append(cloud_url)
                    else:
                        cloud_result_images.append(image)
            
            # 更新任务状态
            GoogleImagesTask.update_task_status(task_id, {
                "status": "completed",
                "result_images": result_images,
                "cloud_result_images": cloud_result_images,
                "progress": "100%",
                "finish_time": datetime.now()
            })
            
            return {
                "success": True,
                "task_id": task_id,
                "credits_cost": credits_cost,
                "message": "图像生成成功",
                "images": cloud_result_images or result_images
            }
        else:
            # API调用失败，退还积分
            add_user_credits(user_id, credits_cost, task_id, "API调用失败")
            GoogleImagesTask.update_task_status(task_id, {
                "status": "failed",
                "fail_reason": api_result["error"],
                "finish_time": datetime.now()
            })
            
            return {
                "success": False,
                "error": api_result["error"],
                "task_id": task_id
            }
            
    except Exception as e:
        error_msg = f"处理谷歌生图请求时出错: {str(e)}"
        logger.error(f"🎨 【谷歌生图处理】{error_msg}")
        logger.exception("🎨 【谷歌生图处理】异常堆栈:")
        
        # 尝试退还积分
        try:
            add_user_credits(user_id, credits_cost, task_id, "处理异常")
        except Exception as refund_error:
            logger.error(f"🎨 【谷歌生图处理】退还积分失败: {str(refund_error)}")
            
        return {"success": False, "error": error_msg}