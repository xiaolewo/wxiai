import aiohttp
import asyncio
import json
import base64
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class JimengInpaintingAPI:
    """即梦涂抹消除API客户端"""

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
            # 构建测试请求（使用即梦API的涂抹消除接口测试）
            # 如果base_url是官方地址，直接使用；如果是第三方，添加/volcv/v1路径
            if "visual.volcengineapi.com" in self.base_url:
                url = f"{self.base_url}?Action=Img2ImgInpainting&Version=2022-08-31"
            else:
                # 第三方平台格式
                url = f"{self.base_url}/volcv/v1?Action=Img2ImgInpainting&Version=2022-08-31"

            # 测试用的最小数据 - 使用空白base64图片进行测试
            # 1x1像素的透明PNG图片的base64
            tiny_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGAbrMfWgAAAABJRU5ErkJggg=="

            test_data = {
                "req_key": "i2i_inpainting",
                "binary_data_base64": [tiny_png, tiny_png],  # 使用最小测试图片
                "steps": 30,
                "strength": 0.8,
                "scale": 7,
                "seed": 0,
                "dilate_size": 15,
                "quality": "M",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=test_data,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:

                    # 对于测试连接，我们主要关心能否成功建立连接和认证
                    if response.status == 200:
                        # 连接和认证成功
                        return {"status": "success", "message": "连接成功，API配置正常"}
                    elif response.status == 401:
                        return {"status": "error", "message": "API密钥无效或已过期"}
                    elif response.status == 403:
                        return {"status": "error", "message": "API密钥权限不足"}
                    elif response.status == 400:
                        # 参数错误但连接成功，说明API配置是正确的
                        return {
                            "status": "success",
                            "message": "连接成功（参数格式正确）",
                        }
                    elif response.status == 406:
                        return {
                            "status": "error",
                            "message": "请求格式不被接受，请检查API配置",
                        }
                    else:
                        # 尝试获取响应内容以获取更多信息
                        try:
                            result = await response.json()
                            message = result.get("message", f"HTTP {response.status}")
                            return {
                                "status": "error",
                                "message": f"连接失败: {message}",
                            }
                        except:
                            return {
                                "status": "error",
                                "message": f"连接失败: HTTP {response.status}",
                            }

        except aiohttp.ClientTimeout:
            return {"status": "error", "message": "连接超时，请检查网络和API地址"}
        except Exception as e:
            logger.error(f"测试即梦涂抹消除API连接失败: {str(e)}")
            return {"status": "error", "message": f"连接异常: {str(e)}"}

    async def _download_image_to_base64(self, image_url: str) -> str:
        """从URL下载图片文件并转换为base64"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    image_url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        base64_data = base64.b64encode(image_data).decode("utf-8")
                        logger.info(
                            f"🎨 【即梦涂抹消除】图片文件下载成功，大小: {len(image_data)} bytes, base64长度: {len(base64_data)}"
                        )
                        return base64_data
                    else:
                        raise Exception(f"下载图片文件失败: HTTP {response.status}")
        except Exception as e:
            logger.error(f"🎨 【即梦涂抹消除】下载图片文件失败: {str(e)}")
            raise

    async def submit_inpainting_task(self, request_data: dict) -> Dict[str, Any]:
        """提交涂抹消除任务"""
        try:
            logger.info(f"🎨 【即梦涂抹消除API】收到request_data: {request_data}")

            # 下载图片并转换为base64
            original_base64 = await self._download_image_to_base64(
                request_data["original_image_url"]
            )
            mask_base64 = await self._download_image_to_base64(
                request_data["mask_image_url"]
            )

            # 构建请求数据，按照即梦API文档格式
            data = {
                "req_key": "i2i_inpainting",
                "binary_data_base64": [original_base64, mask_base64],
                "return_url": request_data.get("return_url", True),
                "steps": request_data.get("steps", 30),
                "strength": request_data.get("strength", 0.8),
                "scale": request_data.get("scale", 7.0),
                "seed": request_data.get("seed", 0),
                "dilate_size": request_data.get("dilate_size", 15),
                "quality": request_data.get("quality", "M"),
            }

            # 打印请求信息（隐藏base64数据）
            log_data = {
                **data,
                "binary_data_base64": [
                    f"[base64_data_{len(original_base64)}chars]",
                    f"[base64_data_{len(mask_base64)}chars]",
                ],
            }
            logger.info(
                f"🎨 【即梦涂抹消除】提交任务完整请求: {json.dumps(log_data, ensure_ascii=False)}"
            )

            # 构建API URL
            url = f"{self.base_url}/volcv/v1?Action=CVProcess&Version=2022-08-31"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60),  # 图片处理需要更长超时
                ) as response:
                    result = await response.json()

                    logger.info(
                        f"🎨 【即梦涂抹消除】API响应: {json.dumps(result, ensure_ascii=False)}"
                    )

                    if response.status == 200 and result.get("code") == 10000:
                        # 即梦API直接返回结果
                        data = result.get("data", {})
                        image_urls = data.get("image_urls", [])

                        if image_urls and len(image_urls) > 0:
                            return {
                                "success": True,
                                "result_image_url": image_urls[0],
                                "message": "涂抹消除成功",
                                "request_id": result.get("request_id"),
                            }
                        else:
                            # 没有返回图片URL
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

                        logger.error(f"🎨 【即梦涂抹消除】提交任务失败: {error_msg}")
                        return {"success": False, "message": error_msg}

        except aiohttp.ClientTimeout:
            error_msg = "请求超时，图片处理耗时较长，请稍后重试"
            logger.error(f"🎨 【即梦涂抹消除】提交任务超时")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"API调用异常: {str(e)}"
            logger.error(f"🎨 【即梦涂抹消除】提交任务异常: {error_msg}")
            return {"success": False, "message": error_msg}


class JimengInpaintingService:
    """即梦涂抹消除服务管理器"""

    def __init__(self):
        self.api_client = None
        self.config = None

    def initialize(self, config):
        """初始化服务"""
        self.config = config
        if config and config.enabled and config.api_key:
            self.api_client = JimengInpaintingAPI(config.base_url, config.api_key)
            logger.info("🎨 【即梦涂抹消除】服务初始化成功")
        else:
            self.api_client = None
            logger.warning("🎨 【即梦涂抹消除】服务未启用或配置不完整")

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
        return await self.api_client.submit_inpainting_task(request_data)

    def get_credits_cost(self) -> int:
        """获取积分消耗"""
        if self.config:
            return self.config.credits_cost
        return 30  # 默认消耗


# 全局服务实例
jimeng_inpainting_service = JimengInpaintingService()
