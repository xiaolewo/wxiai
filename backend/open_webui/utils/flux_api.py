"""
Flux API客户端 - 与Fal.ai API通信
支持文本生图、图生图等功能
"""

import aiohttp
import asyncio
import json
import uuid
from typing import Dict, Optional, Any, List
from datetime import datetime
import logging

from open_webui.models.flux import (
    FluxConfig,
    FluxConfigs,
    FluxTextToImageRequest,
    FluxImageToImageRequest,
    FluxMultiImageRequest,
    get_supported_flux_models,
)

logger = logging.getLogger(__name__)


class FluxAPIError(Exception):
    """Flux API异常"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class FluxAPIClient:
    """Flux API客户端"""

    def __init__(self, config: Optional[FluxConfig] = None):
        """初始化客户端"""
        if config is None:
            config = FluxConfigs.get_config()

        if not config:
            raise FluxAPIError("Flux configuration not found")

        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.timeout = config.timeout

        # 支持的模型映射
        self.supported_models = {
            model["id"]: model for model in get_supported_flux_models()
        }

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """发起HTTP请求"""
        if headers is None:
            headers = {}

        # 根据用户反馈，不管什么域名都使用Bearer格式
        auth_format = "Bearer"
        headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

        logger.debug(f"Using {auth_format} authentication for URL: {url}")

        request_timeout = timeout or self.timeout

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=request_timeout)
            ) as session:
                logger.debug(f"Making {method} request to {url}")
                logger.debug(f"Headers: {headers}")
                logger.debug(f"Data: {json_data}")

                async with session.request(
                    method=method, url=url, headers=headers, json=json_data
                ) as response:
                    response_text = await response.text()
                    logger.debug(f"Response status: {response.status}")
                    logger.debug(f"Response text: {response_text}")

                    try:
                        response_data = (
                            json.loads(response_text) if response_text else {}
                        )
                    except json.JSONDecodeError:
                        response_data = {"raw_response": response_text}

                    if response.status >= 400:
                        error_msg = response_data.get(
                            "detail", f"HTTP {response.status}: {response_text}"
                        )
                        raise FluxAPIError(
                            message=error_msg,
                            status_code=response.status,
                            response_data=response_data,
                        )

                    return response_data

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise FluxAPIError(f"HTTP client error: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Request timeout after {request_timeout}s")
            raise FluxAPIError(f"Request timeout after {request_timeout}s")

    def _validate_model(self, model: str) -> None:
        """验证模型是否支持"""
        if model not in self.supported_models:
            available_models = list(self.supported_models.keys())
            # 提供更详细的错误信息
            model_types = {}
            for m, info in self.supported_models.items():
                model_type = info.get("type", "unknown")
                if model_type not in model_types:
                    model_types[model_type] = []
                model_types[model_type].append(m)

            error_msg = f"不支持的模型: {model}\n可用模型按类型分组:\n"
            for mtype, models in model_types.items():
                error_msg += f"  {mtype}: {models}\n"

            raise FluxAPIError(error_msg.strip())

    def _build_model_url(self, model: str) -> str:
        """构建模型API URL"""
        # Fal.ai的API URL格式: https://queue.fal.run/fal-ai/flux-1/dev
        return f"{self.base_url}/{model}"

    def get_model_capabilities(self, model: str) -> Dict[str, Any]:
        """获取模型能力和限制信息 - 根据用户反馈提供更详细的参数支持"""
        capabilities = {
            "name": "Unknown Model",
            "type": "text_to_image",
            "max_images": 4,
            "default_steps": 28,
            "max_steps": 50,
            "supports_image_size": False,
            "supports_aspect_ratio": False,
            "supports_safety_tolerance": False,
        }

        # FLUX.1 Dev版本的能力参数
        if "dev" in model and "kontext" not in model:
            if "image-to-image" in model:
                capabilities.update(
                    {
                        "name": "FLUX.1 Dev Image-to-Image",
                        "type": "image_to_image",
                        "max_images": 4,
                        "default_steps": 40,
                        "supports_image_size": True,
                        "description": "基于输入图片生成，支持图片尺寸设置",
                    }
                )
            else:
                capabilities.update(
                    {
                        "name": "FLUX.1 Dev",
                        "max_images": 4,
                        "default_steps": 28,
                        "supports_image_size": True,
                        "description": "开发版本，支持图片尺寸设置，适合测试",
                    }
                )

        # FLUX.1 Schnell版本的能力参数（快速生成）
        elif "schnell" in model and "kontext" not in model:
            capabilities.update(
                {
                    "name": "FLUX.1 Schnell",
                    "max_images": 4,
                    "default_steps": 4,
                    "max_steps": 4,  # Schnell版本推荐1-4步
                    "supports_image_size": True,
                    "description": "快速生成版本，1-4推理步数，适合快速原型",
                }
            )

        # FLUX.1 Pro版本的能力参数
        elif "kontext" in model:
            if "max" in model:
                capabilities.update(
                    {
                        "name": "FLUX.1 Pro Max",
                        "max_images": 8,  # Pro Max支持更多图片
                        "supports_aspect_ratio": True,
                        "supports_safety_tolerance": True,
                        "description": "最高质量版本，支持最多8张图片生成",
                    }
                )
            else:
                capabilities.update(
                    {
                        "name": "FLUX.1 Pro",
                        "max_images": 6,  # Pro支持6张
                        "supports_aspect_ratio": True,
                        "supports_safety_tolerance": True,
                        "description": "专业版本，支持最多6张图片生成",
                    }
                )

        return capabilities

    async def submit_text_to_image(
        self, request: FluxTextToImageRequest
    ) -> Dict[str, Any]:
        """提交文本生图任务 - 根据模型版本自适应参数"""
        self._validate_model(request.model)

        # 基本参数
        request_data = {
            "prompt": request.prompt,
            "num_images": request.num_images,
            "guidance_scale": request.guidance_scale,
            "sync_mode": request.sync_mode,
        }

        # 根据模型版本处理参数
        model_info = self.supported_models.get(request.model, {})
        model_type = model_info.get("type", "text_to_image")

        # 根据模型版本处理参数 - 更详细的版本检测
        if "dev" in request.model and "kontext" not in request.model:
            # FLUX.1 [Dev] 版本参数
            if request.image_size:
                request_data["image_size"] = request.image_size
            else:
                request_data["image_size"] = "landscape_4_3"  # Dev版本默认值

            request_data["num_inference_steps"] = (
                request.num_inference_steps or 28
            )  # Dev版本默认28步
            request_data["enable_safety_checker"] = request.enable_safety_checker

            # Dev版本支持的额外参数
            if request.seed is not None:
                request_data["seed"] = request.seed

        # Schnell版本（快速生成）
        elif "schnell" in request.model and "kontext" not in request.model:
            # FLUX.1 Schnell 版本参数（快速模式）
            if request.image_size:
                request_data["image_size"] = request.image_size
            else:
                request_data["image_size"] = "landscape_4_3"  # Schnell版本默认值

            # Schnell版本优化的推理步数（1-4步）
            steps = request.num_inference_steps or 4
            if steps > 4:
                logger.warning(f"Schnell模型推荐使用1-4推理步数，当前设置: {steps}")
            request_data["num_inference_steps"] = min(steps, 4)  # Schnell最多4步
            request_data["enable_safety_checker"] = request.enable_safety_checker

            # Schnell版本支持的额外参数
            if request.seed is not None:
                request_data["seed"] = request.seed

        # Pro/Max版本使用aspect_ratio
        elif "kontext" in request.model:
            # FLUX.1 Kontext [Pro/Max] 版本参数
            if request.aspect_ratio:
                request_data["aspect_ratio"] = request.aspect_ratio
            else:
                request_data["aspect_ratio"] = "1:1"  # Pro版本默认值

            # Pro版本不使用num_inference_steps，而是使用其他参数
            # 添加Pro版本特有的参数
            if request.safety_tolerance:
                request_data["safety_tolerance"] = int(request.safety_tolerance)
            if request.output_format:
                request_data["output_format"] = request.output_format

            # Pro/Max版本支持的额外参数
            if request.seed is not None:
                request_data["seed"] = request.seed

            # 如果是Pro Max版本，支持更多图片数量
            if "max" in request.model and request.num_images > 6:
                logger.info(
                    f"Pro Max版本支持最多8张图片，当前请求: {request.num_images}"
                )

        else:
            # 未知版本，使用通用参数
            logger.warning(f"未识别的Flux模型版本: {request.model}，使用通用参数")
            if request.aspect_ratio:
                request_data["aspect_ratio"] = request.aspect_ratio
            else:
                request_data["aspect_ratio"] = "1:1"

        # 记录使用的模型和参数配置
        logger.info(f"模型 {request.model} 配置参数: {list(request_data.keys())}")
        logger.debug(f"完整参数: {request_data}")

        # 发起请求
        url = self._build_model_url(request.model)

        logger.info(f"提交文本生图任务到 {url}")
        logger.info(f"模型: {request.model}, 图片数量: {request.num_images}")
        logger.debug(f"配置的基础URL: {self.base_url}")
        logger.debug(f"请求参数数量: {len(request_data)} 个")

        response = await self._make_request("POST", url, json_data=request_data)

        logger.info(
            f"文本生图任务提交成功，请求ID: {response.get('request_id', 'unknown')}"
        )
        if "queue_position" in response:
            logger.info(f"队列位置: {response['queue_position']}")

        return response

    async def submit_image_to_image(
        self, request: FluxImageToImageRequest
    ) -> Dict[str, Any]:
        """提交图生图任务 - 根据模型版本自适应参数"""
        self._validate_model(request.model)

        # 基本参数
        request_data = {
            "prompt": request.prompt,
            "image_url": request.image_url,
            "num_images": request.num_images,
            "guidance_scale": request.guidance_scale,
            "sync_mode": request.sync_mode,
        }

        # 根据具体的图生图模型版本设置参数
        if "dev" in request.model and "image-to-image" in request.model:
            # FLUX.1 [Dev] 图生图版本
            request_data["strength"] = request.strength or 0.95  # Dev图生图默认强度
            request_data["num_inference_steps"] = (
                request.num_inference_steps or 40
            )  # Dev图生图默认步数
            request_data["enable_safety_checker"] = request.enable_safety_checker

            logger.info(
                f"使用Dev图生图模式: strength={request_data['strength']}, steps={request_data['num_inference_steps']}"
            )

        elif "redux" in request.model:
            # FLUX.1 Redux 版本（图片风格转换）
            if request.image_size:
                request_data["image_size"] = request.image_size
            else:
                request_data["image_size"] = "landscape_4_3"  # Redux默认尺寸

            # Redux版本根据基础模型调整步数
            if "schnell" in request.model:
                steps = request.num_inference_steps or 4  # Schnell Redux默认4步
                request_data["num_inference_steps"] = min(steps, 4)  # 限制最大步数
                logger.info(
                    f"使用Schnell Redux模式: steps={request_data['num_inference_steps']}"
                )
            else:
                request_data["num_inference_steps"] = (
                    request.num_inference_steps or 28
                )  # Dev Redux默认28步
                logger.info(
                    f"使用Dev Redux模式: steps={request_data['num_inference_steps']}"
                )

            request_data["enable_safety_checker"] = request.enable_safety_checker

        else:
            # 其他图生图模型版本
            logger.warning(f"未识别的图生图模型: {request.model}，使用默认参数")
            request_data["strength"] = request.strength or 0.95
            request_data["num_inference_steps"] = request.num_inference_steps or 28

        # 通用可选参数
        if request.seed is not None:
            request_data["seed"] = request.seed

        # 记录图生图配置
        logger.info(f"图生图模型 {request.model} 配置完成: {list(request_data.keys())}")
        logger.debug(f"图生图完整参数: {request_data}")

        # 发起请求
        url = self._build_model_url(request.model)

        logger.info(f"提交图生图任务到 {url}")
        logger.info(f"模型: {request.model}, 图片数量: {request.num_images}")

        response = await self._make_request("POST", url, json_data=request_data)

        logger.info(
            f"图生图任务提交成功，请求ID: {response.get('request_id', 'unknown')}"
        )
        if "queue_position" in response:
            logger.info(f"队列位置: {response['queue_position']}")

        return response

    async def submit_multi_image_edit(
        self, request: FluxMultiImageRequest
    ) -> Dict[str, Any]:
        """提交多图片编辑任务（实验性功能）"""
        self._validate_model(request.model)

        # 验证模型类型
        model_info = self.supported_models.get(request.model)
        if not model_info or model_info.get("type") != "multi_image":
            raise FluxAPIError(
                f"Model {request.model} does not support multi-image editing"
            )

        # 构建请求数据
        request_data = {
            "prompt": request.prompt,
            "image_urls": request.image_urls,
            "num_images": request.num_images,
            "guidance_scale": request.guidance_scale,
            "sync_mode": request.sync_mode,
        }

        # 添加可选参数
        if request.aspect_ratio:
            request_data["aspect_ratio"] = request.aspect_ratio

        if request.seed is not None:
            request_data["seed"] = request.seed

        if request.safety_tolerance:
            request_data["safety_tolerance"] = int(request.safety_tolerance)

        if request.output_format:
            request_data["output_format"] = request.output_format

        # 发起请求
        url = self._build_model_url(request.model)

        logger.info(f"提交多图编辑任务到 {url}，输入图片: {len(request.image_urls)} 张")
        logger.info(f"模型: {request.model}, 输出图片数量: {request.num_images}")

        response = await self._make_request("POST", url, json_data=request_data)

        logger.info(
            f"多图编辑任务提交成功，请求ID: {response.get('request_id', 'unknown')}"
        )
        if "queue_position" in response:
            logger.info(f"队列位置: {response['queue_position']}")

        return response

    async def get_task_status(self, model: str, request_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        self._validate_model(model)

        # 根据文档，有两种方式查询状态：
        # 1. 使用status端点: /fal-ai/flux-1/requests/{request_id}/status
        # 2. 使用结果端点: /fal-ai/{model}/requests/{request_id}
        # 先尝试status端点，如果失败再尝试结果端点

        if self.base_url == "https://api.linkapi.org":
            # 使用linkapi.org代理，通过配置的base_url访问
            status_url = f"{self.base_url}/fal-ai/flux-1/requests/{request_id}/status"
            result_url = f"{self.base_url}/fal-ai/{model}/requests/{request_id}"
        else:
            # 直接使用fal.ai，构建queue.fal.run URL
            status_url = (
                f"https://queue.fal.run/fal-ai/flux-1/requests/{request_id}/status"
            )
            result_url = f"https://queue.fal.run/fal-ai/{model}/requests/{request_id}"

        # 先尝试status端点
        url = status_url

        logger.info(f"Checking task status for {request_id}")
        logger.debug(f"Base URL configured: {self.base_url}, Model: {model}")
        logger.debug(
            f"API Key prefix: {self.api_key[:10]}..." if self.api_key else "No API key"
        )

        try:
            # 首先尝试status端点
            response = await self._make_request("GET", url)
            logger.debug(
                f"Task status for {request_id}: {response.get('status', 'unknown')}"
            )

            # **关键修复**: 如果status端点返回 COMPLETED 但没有 images，必须获取结果
            if response.get("status") == "COMPLETED" and "images" not in response:
                logger.info(f"任务 {request_id} 已完成，正在获取结果图片")
                try:
                    result_response = await self.get_task_result(model, request_id)

                    # 合并status和result响应
                    merged_response = response.copy()
                    merged_response.update(result_response)
                    logger.info(
                        f"任务 {request_id} 结果合并成功，包含 {len(merged_response.get('images', []))} 张图片"
                    )
                    return merged_response
                except Exception as e:
                    logger.warning(f"获取任务 {request_id} 结果失败，返回状态信息: {e}")
                    return response

            # 如果已经有images或其他状态，直接返回
            return response

        except Exception as status_error:
            logger.warning(f"Status endpoint failed for {request_id}: {status_error}")

            # 如果status端点失败，尝试结果端点
            try:
                response = await self._make_request("GET", result_url)
                logger.debug(
                    f"Task result for {request_id}: status={response.get('status', 'unknown')}"
                )
                return response

            except Exception as result_error:
                logger.error(f"Both endpoints failed for {request_id}")
                logger.error(f"Status endpoint error: {status_error}")
                logger.error(f"Result endpoint error: {result_error}")
                raise status_error  # 抛出原始的status错误

        return response

    async def get_task_result(self, model: str, request_id: str) -> Dict[str, Any]:
        """获取任务结果"""
        self._validate_model(model)

        # 根据配置的base_url构建结果获取URL
        if self.base_url == "https://api.linkapi.org":
            # 使用linkapi.org代理，通过配置的base_url访问
            url = f"{self.base_url}/fal-ai/flux-1/requests/{request_id}"
        else:
            # 直接使用fal.ai，构建queue.fal.run URL
            url = f"https://queue.fal.run/fal-ai/flux-1/requests/{request_id}"

        logger.info(f"Getting task result for {request_id}, URL: {url}")
        logger.debug(f"Base URL configured: {self.base_url}, Model: {model}")

        response = await self._make_request("GET", url)

        logger.debug(
            f"Task result for {request_id}: status={response.get('status', 'unknown')}"
        )

        return response

    async def cancel_task(self, model: str, request_id: str) -> Dict[str, Any]:
        """取消任务"""
        self._validate_model(model)

        # 根据配置的base_url构建取消任务URL
        if self.base_url == "https://api.linkapi.org":
            # 使用linkapi.org代理，通过配置的base_url访问
            url = f"{self.base_url}/fal-ai/flux-1/requests/{request_id}/cancel"
        else:
            # 直接使用fal.ai，构建queue.fal.run URL
            url = f"https://queue.fal.run/fal-ai/flux-1/requests/{request_id}/cancel"

        logger.info(f"Cancelling task: {request_id}, URL: {url}")
        logger.debug(f"Base URL configured: {self.base_url}, Model: {model}")

        response = await self._make_request("PUT", url)

        logger.info(f"Task cancelled: {request_id}")

        return response

    async def poll_task_until_completion(
        self,
        model: str,
        request_id: str,
        max_attempts: int = 300,
        poll_interval: int = 5,
    ) -> Dict[str, Any]:
        """轮询任务直到完成

        Args:
            model: 模型名称
            request_id: 请求ID
            max_attempts: 最大轮询次数
            poll_interval: 轮询间隔（秒）

        Returns:
            最终的任务结果
        """
        logger.info(
            f"Starting to poll task {request_id}, max_attempts={max_attempts}, interval={poll_interval}s"
        )

        for attempt in range(max_attempts):
            try:
                result = await self.get_task_status(model, request_id)
                status = result.get("status", "").upper()

                logger.debug(
                    f"Poll attempt {attempt + 1}/{max_attempts}: status={status}"
                )

                # 检查完成状态
                if status == "COMPLETED":
                    # 获取最终结果
                    final_result = await self.get_task_result(model, request_id)
                    logger.info(f"Task {request_id} completed successfully")
                    return final_result

                # 检查失败状态
                elif status in ["FAILED", "CANCELLED"]:
                    error_msg = result.get("error", "Task failed")
                    logger.error(f"Task {request_id} failed: {error_msg}")
                    raise FluxAPIError(f"Task failed: {error_msg}")

                # 如果还在进行中，等待下次轮询
                elif status in ["PENDING", "IN_PROGRESS", "IN_QUEUE"]:
                    if attempt < max_attempts - 1:  # 不是最后一次尝试
                        await asyncio.sleep(poll_interval)
                        continue

                # 未知状态
                else:
                    logger.warning(f"Unknown task status: {status}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(poll_interval)
                        continue

            except FluxAPIError:
                raise
            except Exception as e:
                logger.error(f"Error polling task {request_id}: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(poll_interval)
                    continue
                else:
                    raise FluxAPIError(f"Polling failed: {e}")

        # 超过最大尝试次数
        logger.error(f"Task {request_id} polling timeout after {max_attempts} attempts")
        raise FluxAPIError(f"Task polling timeout after {max_attempts} attempts")

    def _parse_aspect_ratio(self, aspect_ratio: str) -> tuple[int, int]:
        """解析宽高比字符串为具体尺寸

        Args:
            aspect_ratio: 格式如 "1:1", "16:9", "4:3" 等

        Returns:
            (width, height) 元组
        """
        try:
            if ":" in aspect_ratio:
                width_ratio, height_ratio = map(float, aspect_ratio.split(":"))
            else:
                # 如果没有冒号，假设是正方形
                width_ratio = height_ratio = 1.0

            # 基于1024为基准计算实际尺寸
            base_size = 1024

            if width_ratio >= height_ratio:
                width = base_size
                height = int(base_size * height_ratio / width_ratio)
            else:
                height = base_size
                width = int(base_size * width_ratio / height_ratio)

            # 确保尺寸为8的倍数（常见的生成模型要求）
            width = (width // 8) * 8
            height = (height // 8) * 8

            # 最小尺寸限制
            width = max(width, 512)
            height = max(height, 512)

            return width, height

        except (ValueError, ZeroDivisionError):
            logger.warning(f"Invalid aspect ratio: {aspect_ratio}, using 1:1")
            return 1024, 1024

    async def test_connection(self) -> bool:
        """测试API连接"""
        try:
            # 使用最简单的模型进行测试
            test_model = "fal-ai/flux-1/schnell"
            if test_model not in self.supported_models:
                test_model = list(self.supported_models.keys())[0]

            # 构建测试用URL
            url = self._build_model_url(test_model)

            # 发送一个最小的POST请求来测试连接
            # 使用无效参数，期望得到400错误而不是404，证明API可达
            test_data = {"prompt": "__CONNECTION_TEST__", "num_images": 1}

            try:
                await self._make_request("POST", url, json_data=test_data, timeout=10)
                # 如果请求成功，说明连接正常
                return True
            except FluxAPIError as e:
                # 如果是400错误（参数问题），说明API可达，连接正常
                if e.status_code == 400:
                    logger.info("API connection test successful (400 error expected)")
                    return True
                # 如果是401错误（认证问题），说明API可达但密钥问题
                elif e.status_code == 401:
                    logger.error(
                        "API connection test failed: Authentication error (invalid API key)"
                    )
                    return False
                # 如果是404错误，说明URL不正确或API不可达
                elif e.status_code == 404:
                    logger.error(f"API connection test failed: URL not found - {url}")
                    return False
                else:
                    # 其他错误，记录但认为连接正常
                    logger.info(
                        f"API connection test: received expected error {e.status_code}"
                    )
                    return True

        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False


# 工具函数


def get_flux_client(config: Optional[FluxConfig] = None) -> FluxAPIClient:
    """获取Flux API客户端实例"""
    return FluxAPIClient(config)


async def submit_flux_text_to_image(
    model: str, prompt: str, **kwargs
) -> Dict[str, Any]:
    """便捷函数：提交文本生图任务"""
    request = FluxTextToImageRequest(model=model, prompt=prompt, **kwargs)

    client = get_flux_client()
    return await client.submit_text_to_image(request)


async def submit_flux_image_to_image(
    model: str, prompt: str, image_url: str, **kwargs
) -> Dict[str, Any]:
    """便捷函数：提交图生图任务"""
    request = FluxImageToImageRequest(
        model=model, prompt=prompt, image_url=image_url, **kwargs
    )

    client = get_flux_client()
    return await client.submit_image_to_image(request)


async def get_flux_task_status(model: str, request_id: str) -> Dict[str, Any]:
    """便捷函数：获取任务状态"""
    client = get_flux_client()
    return await client.get_task_status(model, request_id)


async def get_flux_task_result(model: str, request_id: str) -> Dict[str, Any]:
    """便捷函数：获取任务结果"""
    client = get_flux_client()
    return await client.get_task_result(model, request_id)
