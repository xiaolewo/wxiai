"""
即梦涂抹消除API客户端
基于即梦涂抹消除API规范的完整API客户端实现
"""

import asyncio
import json
import logging
import time
import uuid
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from urllib.parse import quote
import httpx

from open_webui.models.inpainting import InpaintingConfigs, InpaintingTasks
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)


class InpaintingAPIError(Exception):
    """涂抹消除API错误"""

    def __init__(self, message: str, code: int = None, response: Dict = None):
        self.message = message
        self.code = code
        self.response = response
        super().__init__(self.message)


class InpaintingAPIClient:
    """即梦涂抹消除API客户端"""

    def __init__(self):
        """初始化API客户端"""
        self.config = None
        self.client = None
        self._load_config()

    def _load_config(self):
        """加载配置"""
        self.config = InpaintingConfigs.get_config()
        if not self.config:
            raise InpaintingAPIError("涂抹消除配置不存在，请先在管理员面板配置")

        if not self.config.enabled:
            raise InpaintingAPIError("涂抹消除功能未启用")

        if not self.config.api_key:
            raise InpaintingAPIError("API密钥未配置")

    def _generate_volcengine_signature(
        self,
        method: str,
        path: str,
        query_params: str,
        headers: Dict[str, str],
        body: str,
    ) -> Dict[str, str]:
        """生成火山引擎API签名"""
        # 假设API密钥格式为 "access_key:secret_key"
        if ":" in self.config.api_key:
            access_key, secret_key = self.config.api_key.split(":", 1)
        else:
            # 如果API密钥不包含分隔符，直接使用作为access key
            access_key = self.config.api_key
            secret_key = self.config.api_key

        # 构建签名字符串
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        date = timestamp[:8]

        # 构建canonical request
        canonical_headers = []
        signed_headers = []
        for key, value in sorted(headers.items()):
            if key.lower().startswith("x-"):
                canonical_headers.append(f"{key.lower()}:{value}")
                signed_headers.append(key.lower())

        canonical_headers_str = "\n".join(canonical_headers)
        signed_headers_str = ";".join(signed_headers)

        canonical_request = f"{method}\n{path}\n{query_params}\n{canonical_headers_str}\n\n{signed_headers_str}\n{hashlib.sha256(body.encode()).hexdigest()}"

        # 构建string to sign
        algorithm = "HMAC-SHA256"
        credential_scope = f"{date}/cn-north-1/cv/request"
        string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"

        # 计算签名
        signing_key = hmac.new(
            f"HMAC-SHA256{secret_key}".encode(), date.encode(), hashlib.sha256
        ).digest()
        signing_key = hmac.new(
            signing_key, "cn-north-1".encode(), hashlib.sha256
        ).digest()
        signing_key = hmac.new(signing_key, "cv".encode(), hashlib.sha256).digest()
        signing_key = hmac.new(signing_key, "request".encode(), hashlib.sha256).digest()
        signature = hmac.new(
            signing_key, string_to_sign.encode(), hashlib.sha256
        ).hexdigest()

        # 构建Authorization头
        authorization = f"{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers_str}, Signature={signature}"

        return {"X-Date": timestamp, "Authorization": authorization}

    def _get_headers(
        self,
        method: str = "POST",
        path: str = "/",
        query_params: str = "",
        body: str = "",
    ) -> Dict[str, str]:
        """获取请求头 - 使用代理服务的简单Bearer认证"""
        return {
            "Content-Type": "application/json",
            "User-Agent": "wxiai-inpainting-client/1.0.0",
            "Authorization": f"Bearer {self.config.api_key}",
        }

    def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if not self.client:
            # 增加超时时间配置，解决请求超时问题
            timeout_seconds = max(60.0, self.config.task_timeout / 1000.0)  # 至少60秒
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=30.0,  # 连接超时30秒
                    read=timeout_seconds,  # 读取超时
                    write=30.0,  # 写入超时30秒
                    pool=5.0,  # 连接池超时5秒
                )
            )
        return self.client

    def _optimize_image_base64(
        self, base64_str: str, max_size: int = 512, quality: int = 75
    ) -> str:
        """激进优化图片大小和质量"""
        try:
            # 解码base64
            img_data = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(img_data))

            # 记录原始尺寸
            original_size = img.size
            original_mode = img.mode
            original_base64_size = len(base64_str)

            # 激进缩放策略：限制最大尺寸为512px
            if max(img.width, img.height) > max_size:
                # 计算缩放比例
                ratio = min(max_size / img.width, max_size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"🔧 图片已激进缩放: {original_size} -> {img.size}")

            # 确保最小尺寸（避免过小导致错误）
            min_size = 64
            if img.width < min_size or img.height < min_size:
                # 放大到最小尺寸
                ratio = max(min_size / img.width, min_size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"🔧 图片已放大到最小尺寸: {img.size}")

            # 转换格式和压缩
            if img.mode in ("RGBA", "P", "LA"):
                # 转换为RGB格式
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode in ("RGBA", "LA"):
                    if img.mode == "LA":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1])
                else:  # P模式
                    img = img.convert("RGBA")
                    background.paste(
                        img, mask=img.split()[-1] if len(img.split()) > 3 else None
                    )
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # 重新编码为base64，使用更低质量
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            optimized_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # 如果仍然过大，进一步降低质量
            if len(optimized_base64) > 500000:  # 500KB limit
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=60, optimize=True)
                optimized_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                logger.info(f"🔧 进一步压缩质量到60%")

            # 记录优化结果
            reduction = (1 - len(optimized_base64) / original_base64_size) * 100
            logger.info(f"🔧 图片激进优化完成: {original_mode} -> RGB")
            logger.info(f"🔧 尺寸变化: {original_size} -> {img.size}")
            logger.info(
                f"🔧 大小变化: {original_base64_size} -> {len(optimized_base64)} (减少{reduction:.1f}%)"
            )

            return optimized_base64

        except Exception as e:
            logger.error(f"图片优化失败，使用原图: {e}")
            return base64_str

    async def create_inpainting_task(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建涂抹消除任务

        Args:
            request_data: 请求数据

        Returns:
            API响应数据

        Raises:
            InpaintingAPIError: API调用失败
        """
        try:
            self._load_config()  # 重新加载配置确保最新

            # 构建API URL (通过代理使用即梦涂抹消除API)
            api_url = f"{self.config.base_url.rstrip('/')}/volcv/v1?Action=Img2ImgInpainting&Version=2022-08-31"

            # 优化图片大小和质量
            input_image_b64 = request_data.get("input_image_base64")
            mask_image_b64 = request_data.get("mask_image_base64")

            if input_image_b64:
                input_image_b64 = self._optimize_image_base64(
                    input_image_b64, max_size=512, quality=75
                )
                logger.info(
                    f"🎨 输入图片已激进优化，Base64长度: {len(input_image_b64)}"
                )

            if mask_image_b64:
                mask_image_b64 = self._optimize_image_base64(
                    mask_image_b64, max_size=512, quality=85
                )
                logger.info(f"🎨 Mask图片已激进优化，Base64长度: {len(mask_image_b64)}")

            # 构建请求体 (使用最激进的快速设置)
            payload = {
                "req_key": "i2i_inpainting",
                "binary_data_base64": [input_image_b64, mask_image_b64],
                "return_url": True,  # 返回URL链接
                "steps": min(request_data.get("steps", 15), 15),  # 强制限制最大15步
                "strength": min(request_data.get("strength", 0.7), 0.8),  # 限制强度
                "scale": min(request_data.get("scale", 5.0), 7.0),  # 限制scale
                "quality": "L",  # 强制使用最快质量
                "dilate_size": min(
                    request_data.get("dilate_size", 10), 15
                ),  # 限制膨胀尺寸
                "seed": request_data.get("seed", 0),
            }

            # 移除空值
            payload = {k: v for k, v in payload.items() if v is not None}

            logger.info(f"调用即梦涂抹消除API: {api_url}")
            logger.info(f"🎨 使用req_key: {payload['req_key']}")
            logger.info(
                f"🎨 参数: steps={payload.get('steps')}, strength={payload.get('strength')}, scale={payload.get('scale')}"
            )
            logger.info(
                f"🎨 其他参数: quality={payload.get('quality')}, dilate_size={payload.get('dilate_size')}, seed={payload.get('seed')}"
            )

            logger.debug(
                f"请求数据: {json.dumps({**payload, 'binary_data_base64': ['<input_image_data>', '<mask_image_data>']}, ensure_ascii=False)}"
            )

            # 准备请求参数
            from urllib.parse import urlparse, parse_qs

            parsed_url = urlparse(api_url)
            path = parsed_url.path or "/"
            query_params = parsed_url.query or ""
            body = json.dumps(payload, separators=(",", ":"))

            # 生成请求头（包含签名）
            headers = self._get_headers("POST", path, query_params, body)

            client = self._get_client()

            # 添加重试机制处理超时和服务器错误
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 API调用尝试 {attempt + 1}/{max_retries}")
                    response = await client.post(api_url, json=payload, headers=headers)
                    break  # 成功则跳出循环
                except httpx.TimeoutException as e:
                    if attempt == max_retries - 1:
                        raise InpaintingAPIError(
                            f"API请求超时（已重试{max_retries}次）: {str(e)}"
                        )
                    logger.warning(f"⏰ API请求超时，{2 * (attempt + 1)}秒后重试...")
                    await asyncio.sleep(2 * (attempt + 1))  # 递增延迟重试
                except httpx.RequestError as e:
                    if attempt == max_retries - 1:
                        raise InpaintingAPIError(
                            f"API请求异常（已重试{max_retries}次）: {str(e)}"
                        )
                    logger.warning(
                        f"🔌 API请求异常，{2 * (attempt + 1)}秒后重试: {str(e)}"
                    )
                    await asyncio.sleep(2 * (attempt + 1))

            # 记录响应状态
            logger.info(f"API响应状态: {response.status_code}")

            if response.status_code != 200:
                error_text = await response.aread()
                error_content = error_text.decode("utf-8", errors="ignore")
                logger.error(f"API请求失败: {response.status_code} - {error_content}")

                # 特殊处理406错误和上游服务错误
                if response.status_code == 406:
                    try:
                        error_data = json.loads(error_content)
                        upstream_message = error_data.get("upsream_message", "")

                        # 检查是否是超时错误
                        if (
                            "request timeout" in upstream_message
                            or "20002639us" in upstream_message
                        ):
                            raise InpaintingAPIError(
                                "即梦服务超时，请尝试使用更小的图片或减少处理步数",
                                code=response.status_code,
                                response=error_data,
                            )
                        elif "Internal Error" in upstream_message:
                            raise InpaintingAPIError(
                                "即梦服务内部错误，请稍后重试",
                                code=response.status_code,
                                response=error_data,
                            )
                    except json.JSONDecodeError:
                        pass

                raise InpaintingAPIError(
                    f"API请求失败: HTTP {response.status_code}",
                    code=response.status_code,
                    response={
                        "status_code": response.status_code,
                        "text": error_content,
                    },
                )

            # 解析响应
            response_data = response.json()
            logger.info(f"🎨 即梦API响应成功")
            logger.debug(
                f"API响应数据: {json.dumps(response_data, ensure_ascii=False)}"
            )

            # 检查响应格式 (即梦涂抹消除API格式)
            if response_data.get("code") != 10000:
                error_msg = response_data.get("message", "未知错误")
                logger.error(
                    f"API业务错误: code={response_data.get('code')}, message={error_msg}"
                )
                raise InpaintingAPIError(
                    f"API业务错误: {error_msg}",
                    code=response_data.get("code"),
                    response=response_data,
                )

            # 检查是否有生成的图片数据
            data = response_data.get("data", {})
            if not data:
                error_msg = "API响应数据为空"
                logger.error(f"API响应异常: {error_msg}")
                raise InpaintingAPIError(
                    f"API响应异常: {error_msg}", response=response_data
                )

            return response_data

        except httpx.TimeoutException:
            logger.error("API请求超时")
            raise InpaintingAPIError("API请求超时")
        except httpx.RequestError as e:
            logger.error(f"API请求异常: {e}")
            raise InpaintingAPIError(f"API请求异常: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"API响应解析失败: {e}")
            raise InpaintingAPIError(f"API响应解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"API调用未知错误: {e}")
            raise InpaintingAPIError(f"API调用未知错误: {str(e)}")

    async def query_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态数据

        Note:
            即梦涂抹消除API是同步接口，这里通过数据库查询任务状态
        """
        try:
            task = InpaintingTasks.get_task_by_id(task_id)
            if not task:
                raise InpaintingAPIError(f"任务不存在: {task_id}")

            return {
                "task_id": task.id,
                "status": task.status,
                "task_status_msg": task.task_status_msg,
                "progress": task.progress,
                "result_image_url": task.result_image_url,
                "cloud_result_url": task.cloud_result_url,
                "fail_reason": task.fail_reason,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }

        except Exception as e:
            logger.error(f"查询任务状态失败: {e}")
            raise InpaintingAPIError(f"查询任务状态失败: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """测试API连接

        Returns:
            连接测试结果
        """
        try:
            self._load_config()

            # 构建测试API URL
            base_url = self.config.base_url.rstrip("/")
            test_url = f"{base_url}/volcv/v1"

            logger.info(f"🔗 测试连接到: {test_url}")

            # 创建HTTP客户端进行测试
            async with httpx.AsyncClient(timeout=10.0) as test_client:
                # 发送GET请求测试连接
                try:
                    response = await test_client.get(
                        test_url,
                        headers={
                            "Authorization": f"Bearer {self.config.api_key}",
                            "User-Agent": "wxiai-inpainting-test/1.0.0",
                        },
                    )

                    logger.info(f"✅ 连接测试响应: {response.status_code}")

                    # 即使是404或其他状态码，只要能连接到服务器就算成功
                    if response.status_code in [200, 400, 401, 403, 404]:
                        return {
                            "success": True,
                            "message": f"连接测试成功 (HTTP {response.status_code})",
                            "api_url": test_url,
                            "status_code": response.status_code,
                            "api_key_configured": bool(self.config.api_key),
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"服务器响应异常 (HTTP {response.status_code})",
                            "api_url": test_url,
                            "status_code": response.status_code,
                            "error": f"HTTP {response.status_code}",
                        }

                except httpx.TimeoutException:
                    return {
                        "success": False,
                        "message": "连接超时，请检查网络或API地址",
                        "api_url": test_url,
                        "error": "Connection timeout",
                    }
                except httpx.ConnectError as e:
                    return {
                        "success": False,
                        "message": f"无法连接到服务器: {str(e)}",
                        "api_url": test_url,
                        "error": f"Connection error: {str(e)}",
                    }
                except httpx.RequestError as e:
                    return {
                        "success": False,
                        "message": f"请求错误: {str(e)}",
                        "api_url": test_url,
                        "error": f"Request error: {str(e)}",
                    }

        except InpaintingAPIError as e:
            return {
                "success": False,
                "message": f"配置错误: {e.message}",
                "error": e.message,
            }
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return {
                "success": False,
                "message": f"连接测试失败: {str(e)}",
                "error": str(e),
            }

    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.aclose()
            self.client = None


class InpaintingTaskProcessor:
    """涂抹消除任务处理器"""

    def __init__(self):
        self.api_client = InpaintingAPIClient()

    async def submit_inpainting_task(
        self, user_id: str, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提交涂抹消除任务

        Args:
            user_id: 用户ID
            task_data: 任务数据

        Returns:
            任务提交结果
        """
        try:
            # 检查用户积分 - 使用统一积分系统
            from open_webui.models.credits import Credits

            config = InpaintingConfigs.get_config()
            credits_cost = config.credits_per_task if config else 50

            # 获取用户积分
            user_credits = Credits.get_credit_by_user_id(user_id)
            if not user_credits or float(user_credits.credit) < credits_cost:
                return {
                    "success": False,
                    "message": "积分不足",
                    "required_credits": credits_cost,
                    "current_credits": (
                        float(user_credits.credit) if user_credits else 0
                    ),
                }

            # 扣除积分
            try:
                from decimal import Decimal
                from open_webui.models.credits import AddCreditForm, SetCreditFormDetail

                Credits.add_credit_by_user_id(
                    AddCreditForm(
                        user_id=user_id,
                        amount=Decimal(-credits_cost),  # 负数表示扣除积分
                        detail=SetCreditFormDetail(
                            desc="即梦涂抹消除任务",
                            api_params={
                                "task_id": task_data.get("task_id"),
                                "service": "inpainting",
                            },
                        ),
                    )
                )
            except Exception as e:
                logger.error(f"扣除积分失败: {e}")
                return {"success": False, "message": "扣除积分失败", "error": str(e)}

            # 创建数据库任务记录
            task_id = task_data.get("task_id") or f"inpainting_{int(time.time())}"
            db_task_data = {
                "task_id": task_id,
                "input_image_url": task_data.get("input_image_url"),
                "mask_image_url": task_data.get("mask_image_url"),
                "uploaded_input_url": task_data.get("uploaded_input_url"),
                "uploaded_mask_url": task_data.get("uploaded_mask_url"),
                "steps": task_data.get("steps", 30),
                "strength": task_data.get("strength", 0.8),
                "scale": task_data.get("scale", 7.0),
                "quality": task_data.get("quality", "M"),
                "dilate_size": task_data.get("dilate_size", 15),
                "seed": task_data.get("seed", 0),
                "credits_cost": credits_cost,
                "status": "submitted",
                "submit_time": datetime.now(),  # 使用datetime对象
                "request_data": json.dumps(task_data, ensure_ascii=False),
            }

            db_task = InpaintingTasks.create_task(user_id, db_task_data)

            # 调用API (即梦涂抹消除是同步API，直接处理结果)
            try:
                api_response = await self.api_client.create_inpainting_task(
                    {
                        "input_image_base64": task_data.get("input_image_base64"),
                        "mask_image_base64": task_data.get("mask_image_base64"),
                        "steps": task_data.get("steps"),
                        "strength": task_data.get("strength"),
                        "scale": task_data.get("scale"),
                        "quality": task_data.get("quality"),
                        "dilate_size": task_data.get("dilate_size"),
                        "seed": task_data.get("seed"),
                    }
                )

                # 处理API响应 (即梦涂抹消除API格式)
                if api_response.get("data"):
                    data = api_response["data"]
                    result_image_url = None

                    # 获取结果图片URL (即梦涂抹消除API格式)
                    if data.get("image_urls") and len(data["image_urls"]) > 0:
                        result_image_url = data["image_urls"][0]
                    elif (
                        data.get("binary_data_base64")
                        and len(data["binary_data_base64"]) > 0
                    ):
                        # 如果只有base64，转换为data URL格式
                        result_image_url = (
                            f"data:image/jpeg;base64,{data['binary_data_base64'][0]}"
                        )

                    if not result_image_url:
                        raise InpaintingAPIError("API未返回有效的图片URL")

                    # 可选：上传到云存储
                    cloud_result_url = result_image_url  # 默认使用原URL
                    try:
                        from open_webui.services.file_manager import get_file_manager

                        file_manager = get_file_manager()

                        # 下载并上传到云存储
                        import httpx

                        async with httpx.AsyncClient() as client:
                            img_response = await client.get(result_image_url)
                            if img_response.status_code == 200:
                                cloud_filename = f"inpainting_result/{user_id}/{uuid.uuid4().hex}.jpg"
                                upload_result = await file_manager.upload_file_content(
                                    content=img_response.content,
                                    filename=cloud_filename,
                                    content_type="image/jpeg",
                                    metadata={
                                        "user_id": user_id,
                                        "task_id": db_task.id,
                                        "service": "inpainting",
                                        "created_at": datetime.now().isoformat(),
                                    },
                                )
                                if upload_result["success"]:
                                    cloud_result_url = upload_result["url"]
                                    logger.info(
                                        f"✅ 结果图片已上传到云存储: {cloud_result_url}"
                                    )
                    except Exception as e:
                        logger.warning(f"上传结果图片到云存储失败: {e}")

                    # 更新任务完成状态
                    update_data = {
                        "status": "completed",
                        "result_image_url": result_image_url,
                        "cloud_result_url": cloud_result_url,
                        "progress": "100%",
                        "finish_time": datetime.now(),  # 使用datetime对象
                        "response_data": json.dumps(api_response, ensure_ascii=False),
                    }

                    InpaintingTasks.update_task(db_task.id, update_data)

                    return {
                        "success": True,
                        "message": "涂抹消除任务完成",
                        "task_id": db_task.id,
                        "result_image_url": cloud_result_url,  # 返回云存储URL
                        "credits_consumed": credits_cost,
                    }
                else:
                    raise InpaintingAPIError("API响应数据格式错误")

            except InpaintingAPIError as api_error:
                # API调用失败，回退积分
                try:
                    Credits.add_credit_by_user_id(
                        AddCreditForm(
                            user_id=user_id,
                            amount=Decimal(credits_cost),  # 正数表示退还积分
                            detail=SetCreditFormDetail(
                                desc="即梦涂抹消除任务失败，退还积分",
                                api_params={
                                    "task_id": task_data.get("task_id"),
                                    "service": "inpainting",
                                    "reason": "api_error",
                                },
                            ),
                        )
                    )
                except Exception as e:
                    logger.error(f"退还积分失败: {e}")

                # 更新任务失败状态
                InpaintingTasks.update_task(
                    db_task.id,
                    {
                        "status": "failed",
                        "fail_reason": api_error.message,
                        "finish_time": datetime.now(),  # 使用datetime对象
                    },
                )

                return {
                    "success": False,
                    "message": f"任务提交失败: {api_error.message}",
                    "task_id": db_task.id,
                    "error": api_error.message,
                }

        except Exception as e:
            logger.error(f"提交涂抹消除任务失败: {e}")
            return {
                "success": False,
                "message": f"提交任务失败: {str(e)}",
                "error": str(e),
            }

    async def close(self):
        """关闭处理器"""
        await self.api_client.close()


# 全局实例
_global_client = None
_global_processor = None


def get_inpainting_client() -> InpaintingAPIClient:
    """获取全局API客户端"""
    global _global_client
    if not _global_client:
        _global_client = InpaintingAPIClient()
    return _global_client


def get_inpainting_processor() -> InpaintingTaskProcessor:
    """获取全局任务处理器"""
    global _global_processor
    if not _global_processor:
        _global_processor = InpaintingTaskProcessor()
    return _global_processor


async def cleanup_clients():
    """清理全局客户端"""
    global _global_client, _global_processor
    if _global_client:
        await _global_client.close()
        _global_client = None
    if _global_processor:
        await _global_processor.close()
        _global_processor = None
