import aiohttp
import asyncio
import json
import base64
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class JimengOutpaintingAPI:
    """即梦智能扩图API客户端"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        try:
            # 使用第三方平台正确的API格式进行连接测试
            url = f"{self.base_url}/volcv/v1?Action=CVProcess&Version=2022-08-31"

            # 测试用的最小数据 - 1x1像素透明PNG图片
            tiny_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGAbrMfWgAAAABJRU5ErkJggg=="

            test_data = {
                "req_key": "i2i_outpainting",
                "custom_prompt": "蓝色的海洋",
                "binary_data_base64": [tiny_png],
                "scale": 7,
                "seed": -1,
                "steps": 30,
                "strength": 0.8,
                "top": 0.1,
                "bottom": 0.1,
                "left": 1,
                "right": 1,
                "max_height": 1920,
                "max_width": 1920,
                "return_url": True,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=test_data,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:

                    if response.status == 200:
                        try:
                            result = await response.json()
                            if result.get("code") == 10000:
                                return {
                                    "status": "success",
                                    "message": "连接成功，API配置正常",
                                }
                            else:
                                return {
                                    "status": "success",
                                    "message": f"连接成功，返回码: {result.get('code')}",
                                }
                        except:
                            return {"status": "success", "message": "连接成功"}
                    elif response.status == 401:
                        return {"status": "error", "message": "API密钥无效或已过期"}
                    elif response.status == 403:
                        return {"status": "error", "message": "API密钥权限不足"}
                    elif response.status == 400:
                        try:
                            result = await response.json()
                            message = result.get("message", "参数错误")
                            return {
                                "status": "success",
                                "message": f"连接成功，但参数有误: {message}",
                            }
                        except:
                            return {
                                "status": "success",
                                "message": "连接成功，但参数需要调整",
                            }
                    elif response.status == 406:
                        return {
                            "status": "error",
                            "message": "请求格式不被接受，请检查API配置",
                        }
                    else:
                        try:
                            result = await response.json()
                            message = result.get("message", f"HTTP {response.status}")
                            return {
                                "status": "error",
                                "message": f"连接失败: {message}",
                            }
                        except Exception:
                            return {
                                "status": "error",
                                "message": f"连接失败: HTTP {response.status}",
                            }

        except aiohttp.ClientTimeout:
            return {"status": "error", "message": "连接超时，请检查网络和API地址"}
        except Exception as e:
            logger.error(f"测试即梦智能扩图API连接失败: {str(e)}")
            return {"status": "error", "message": f"连接异常: {str(e)}"}

    async def _download_image_to_base64(self, image_url: str) -> str:
        """从URL下载图片文件并转换为base64"""
        logger.info(f"🎨 【即梦智能扩图】开始下载图片: {image_url[:100]}...")
        try:
            # 检查是否是data URL
            if image_url.startswith("data:image"):
                logger.info(f"🎨 【即梦智能扩图】检测到data URL，直接提取base64数据")
                # 提取base64部分 data:image/png;base64,xxxxx
                if "," in image_url:
                    base64_data = image_url.split(",")[1]
                    logger.info(
                        f"🎨 【即梦智能扩图】data URL处理成功，base64长度: {len(base64_data)}"
                    )
                    return base64_data
                else:
                    raise Exception("无效的data URL格式")

            # 检查是否是blob URL或其他不支持的URL
            if image_url.startswith("blob:") or not image_url.startswith("http"):
                raise Exception(f"不支持的URL格式: {image_url[:50]}...")

            import ssl

            # 创建SSL上下文，禁用证书验证
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # 创建连接器
            connector = aiohttp.TCPConnector(ssl=ssl_context)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    image_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        base64_data = base64.b64encode(image_data).decode("utf-8")
                        logger.info(
                            f"🎨 【即梦智能扩图】图片下载成功，大小: {len(image_data)} bytes, base64长度: {len(base64_data)}"
                        )
                        return base64_data
                    else:
                        raise Exception(f"下载图片失败: HTTP {response.status}")

        except Exception as e:
            logger.error(f"🎨 【即梦智能扩图】下载图片失败: {str(e)}")
            raise e

    async def submit_outpainting_task(self, request_data: dict) -> Dict[str, Any]:
        """提交智能扩图任务"""
        try:
            expansion_mode = request_data.get("expansion_mode", "equal")
            logger.info(f"🎨 【即梦智能扩图】收到请求: {expansion_mode}模式")

            # 下载原始图片并转换为base64
            original_base64 = await self._download_image_to_base64(
                request_data["original_image_url"]
            )

            # 构建请求数据
            if expansion_mode == "canvas" and request_data.get("mask_image_url"):
                # 画布模式 - 需要扩展图和遮罩
                try:
                    mask_base64 = await self._download_image_to_base64(
                        request_data["mask_image_url"]
                    )
                except Exception as e:
                    logger.error(f"🎨 【即梦智能扩图】下载mask图片失败: {str(e)}")
                    return {"success": False, "message": f"下载mask图片失败: {str(e)}"}
                data = {
                    "req_key": "i2i_outpainting",
                    "custom_prompt": request_data.get("custom_prompt", "蓝色的海洋"),
                    "binary_data_base64": [original_base64, mask_base64],
                    "scale": request_data.get("scale", 7),
                    "seed": request_data.get("seed", -1),
                    "steps": request_data.get("steps", 30),
                    "strength": request_data.get("strength", 0.8),
                    "max_height": request_data.get("max_height", 1920),
                    "max_width": request_data.get("max_width", 1920),
                    "return_url": request_data.get("return_url", True),
                }
            else:
                # 比例模式 - 使用扩展比例参数
                data = {
                    "req_key": "i2i_outpainting",
                    "custom_prompt": request_data.get("custom_prompt", "蓝色的海洋"),
                    "binary_data_base64": [original_base64],
                    "scale": request_data.get("scale", 7),
                    "seed": request_data.get("seed", -1),
                    "steps": request_data.get("steps", 30),
                    "strength": request_data.get("strength", 0.8),
                    "top": request_data.get("top", 0.1),
                    "bottom": request_data.get("bottom", 0.1),
                    "left": request_data.get("left", 0.1),
                    "right": request_data.get("right", 0.1),
                    "max_height": request_data.get("max_height", 1920),
                    "max_width": request_data.get("max_width", 1920),
                    "return_url": request_data.get("return_url", True),
                }

            # 打印请求信息（隐藏base64数据）
            log_data = {
                **data,
                "binary_data_base64": [
                    f"[base64_data_{len(d)}chars]" for d in data["binary_data_base64"]
                ],
            }
            logger.info(
                f"🎨 【即梦智能扩图】提交任务请求: {json.dumps(log_data, ensure_ascii=False)}"
            )

            # 使用第三方平台格式构建API URL
            url = f"{self.base_url}/volcv/v1?Action=CVProcess&Version=2022-08-31"

            logger.info(f"🎨 【即梦智能扩图】API请求URL: {url}")
            logger.info(
                f"🎨 【即梦智能扩图】扩展模式: {expansion_mode}, 提示词: {data.get('custom_prompt', 'N/A')}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    result = await response.json()

                    logger.info(f"🎨 【即梦智能扩图】HTTP状态码: {response.status}")
                    logger.info(
                        f"🎨 【即梦智能扩图】API响应: {json.dumps(result, ensure_ascii=False)}"
                    )

                    if result.get("code") != 10000:
                        logger.error(
                            f"🎨 【即梦智能扩图】API返回错误码: {result.get('code')}, 消息: {result.get('message', 'Unknown error')}"
                        )

                    # 检查是否有image_urls
                    data_section = result.get("data", {})
                    image_urls = data_section.get("image_urls", [])
                    logger.info(f"🎨 【即梦智能扩图】返回图片数量: {len(image_urls)}")

                    if response.status == 200 and result.get("code") == 10000:
                        # API直接返回结果
                        data = result.get("data", {})
                        image_urls = data.get("image_urls", [])

                        if image_urls and len(image_urls) > 0:
                            return {
                                "success": True,
                                "result_image_url": image_urls[0],
                                "message": "智能扩图成功",
                                "request_id": result.get("request_id"),
                            }
                        else:
                            return {
                                "success": False,
                                "message": "API响应中没有找到结果图片",
                            }
                    else:
                        error_msg = result.get("message", f"HTTP {response.status}")

                        # 检查特定错误码
                        if result.get("code") == 50411:
                            error_msg = "输入图片前审核未通过，请更换图片"
                        elif result.get("code") == 50511:
                            error_msg = "输出图片后审核未通过，请调整参数重试"

                        logger.error(f"🎨 【即梦智能扩图】提交任务失败: {error_msg}")
                        return {"success": False, "message": error_msg}

        except aiohttp.ClientTimeout:
            error_msg = "请求超时，图片处理耗时较长，请稍后重试"
            logger.error(f"🎨 【即梦智能扩图】提交任务超时")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"API调用异常: {str(e)}"
            logger.error(f"🎨 【即梦智能扩图】提交任务异常: {error_msg}")
            return {"success": False, "message": error_msg}


class JimengOutpaintingService:
    """即梦智能扩图服务管理器"""

    def __init__(self):
        self.api_client = None
        self.config = None

    def initialize(self, config):
        """初始化服务"""
        self.config = config
        if config and config.enabled and config.api_key:
            self.api_client = JimengOutpaintingAPI(config.base_url, config.api_key)
            logger.info("🎨 【即梦智能扩图】服务初始化成功")
        else:
            self.api_client = None
            logger.warning("🎨 【即梦智能扩图】服务未启用或配置不完整")

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.api_client is not None

    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        if not self.api_client:
            return {"status": "error", "message": "服务未初始化或未启用"}
        return await self.api_client.test_connection()

    async def submit_task(self, request_data: dict) -> Dict[str, Any]:
        """提交任务"""
        if not self.api_client:
            return {"success": False, "message": "服务未初始化或未启用"}
        return await self.api_client.submit_outpainting_task(request_data)

    def get_credits_cost(self) -> int:
        """获取积分消耗"""
        if self.config:
            return self.config.credits_cost
        return 25  # 默认消耗


# 全局服务实例
jimeng_outpainting_service = JimengOutpaintingService()
