import os
import io
import logging
import uuid
import hashlib
import mimetypes
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
import requests

try:
    from qcloud_cos import CosConfig
    from qcloud_cos import CosS3Client
    from qcloud_cos.cos_exception import CosClientError, CosServiceError
except ImportError:
    # 如果没有安装SDK，提供一个模拟类
    class CosConfig:
        def __init__(self, *args, **kwargs):
            pass

    class CosS3Client:
        def __init__(self, *args, **kwargs):
            pass

        def put_object(self, *args, **kwargs):
            raise Exception(
                "腾讯云COS SDK未安装，请运行: pip install cos-python-sdk-v5"
            )

        def list_objects(self, *args, **kwargs):
            raise Exception(
                "腾讯云COS SDK未安装，请运行: pip install cos-python-sdk-v5"
            )

        def delete_object(self, *args, **kwargs):
            raise Exception(
                "腾讯云COS SDK未安装，请运行: pip install cos-python-sdk-v5"
            )

        def head_object(self, *args, **kwargs):
            raise Exception(
                "腾讯云COS SDK未安装，请运行: pip install cos-python-sdk-v5"
            )

        def bucket_exists(self, *args, **kwargs):
            raise Exception(
                "腾讯云COS SDK未安装，请运行: pip install cos-python-sdk-v5"
            )

        def head_bucket(self, *args, **kwargs):
            raise Exception(
                "腾讯云COS SDK未安装，请运行: pip install cos-python-sdk-v5"
            )

    class CosClientError(Exception):
        pass

    class CosServiceError(Exception):
        pass


from open_webui.models.cloud_storage import CloudStorageConfig


logger = logging.getLogger(__name__)


class TencentCOSService:
    """腾讯云COS存储服务"""

    def __init__(self, config: CloudStorageConfig):
        """初始化腾讯云COS服务

        Args:
            config: 云存储配置对象
        """
        self.config = config
        self.client = None

        if not config.enabled:
            logger.warning("腾讯云COS存储未启用")
            return

        if not all([config.secret_id, config.secret_key, config.region, config.bucket]):
            logger.error("腾讯云COS配置信息不完整")
            return

        try:
            # 初始化COS配置
            cos_config = CosConfig(
                Region=config.region,
                SecretId=config.secret_id,
                SecretKey=config.secret_key,
                Token=None,  # 如果使用永久密钥不需要填入token，如果使用临时密钥需要填入
                Scheme="https",  # 指定使用 http/https 协议来访问 COS，默认为 https
            )

            # 初始化客户端
            self.client = CosS3Client(cos_config)
            logger.info(
                f"腾讯云COS客户端初始化成功 - Region: {config.region}, Bucket: {config.bucket}"
            )

        except Exception as e:
            logger.error(f"腾讯云COS客户端初始化失败: {str(e)}")
            self.client = None

    def is_available(self) -> bool:
        """检查COS服务是否可用"""
        return self.client is not None and self.config.enabled

    async def test_connection(self) -> Dict[str, Any]:
        """测试COS连接

        Returns:
            Dict: 测试结果
        """
        if not self.is_available():
            return {"success": False, "message": "COS服务未初始化或未启用"}

        try:
            # 使用bucket_exists方法测试连接
            exists = self.client.bucket_exists(Bucket=self.config.bucket)

            if not exists:
                return {
                    "success": False,
                    "message": f"Bucket '{self.config.bucket}' 不存在",
                }

            return {
                "success": True,
                "message": "连接测试成功",
                "bucket_info": {
                    "bucket": self.config.bucket,
                    "region": self.config.region,
                    "status": "accessible",
                },
            }

        except CosServiceError as e:
            error_msg = f"COS服务错误: {e.get_error_msg()}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except CosClientError as e:
            error_msg = f"COS客户端错误: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    def _generate_file_path(self, filename: str, file_type: str, user_id: str) -> str:
        """生成文件存储路径

        Args:
            filename: 文件名
            file_type: 文件类型 ('image', 'video')
            user_id: 用户ID

        Returns:
            str: 完整的存储路径
        """
        # 获取当前日期
        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")

        # 根据文件类型选择路径
        if file_type == "image":
            type_path = self.config.image_path
        elif file_type == "video":
            type_path = self.config.video_path
        else:
            type_path = "others/"

        # 生成唯一文件名（避免重复）
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{user_id}_{uuid.uuid4().hex[:8]}_{filename}"

        # 组合完整路径
        full_path = f"{self.config.base_path}{type_path}{date_path}/{unique_filename}"

        return full_path

    def _get_public_url(self, object_key: str) -> str:
        """获取文件的公开访问URL

        Args:
            object_key: COS对象键

        Returns:
            str: 公开访问URL
        """
        if self.config.domain:
            # 使用自定义域名
            domain = self.config.domain.rstrip("/")
            return f"{domain}/{object_key}"
        else:
            # 使用默认域名
            return f"https://{self.config.bucket}.cos.{self.config.region}.myqcloud.com/{object_key}"

    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> str:
        """获取预签名URL，用于临时访问私有文件

        Args:
            object_key: COS对象键
            expires_in: URL过期时间（秒），默认1小时

        Returns:
            str: 预签名URL
        """
        try:
            if not self.is_available():
                return self._get_public_url(object_key)

            # 使用腾讯云COS SDK的预签名方法
            presigned_url = self.client.get_presigned_download_url(
                Bucket=self.config.bucket,
                Key=object_key,
                Expired=expires_in,  # 腾讯云COS使用Expired参数
            )

            logger.info(f"生成预签名URL成功: {object_key}")
            logger.info(f"预签名URL: {presigned_url}")

            # 简单验证URL格式
            if not presigned_url.startswith(("http://", "https://")):
                logger.error(f"预签名URL格式不正确: {presigned_url}")
                return self._get_public_url(object_key)

            return presigned_url

        except Exception as e:
            logger.warning(f"生成预签名URL失败: {str(e)}，回退到公共URL")
            return self._get_public_url(object_key)

    async def upload_file_from_bytes(
        self,
        file_data: bytes,
        filename: str,
        file_type: str,
        user_id: str,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """从字节数据上传文件到COS

        Args:
            file_data: 文件字节数据
            filename: 文件名
            file_type: 文件类型 ('image', 'video')
            user_id: 用户ID
            content_type: MIME类型

        Returns:
            Dict: 上传结果
        """
        if not self.is_available():
            return {"success": False, "message": "COS服务未初始化或未启用"}

        # 检查文件大小
        file_size = len(file_data)
        if file_size > self.config.max_file_size:
            return {
                "success": False,
                "message": f"文件大小 {file_size} 超过限制 {self.config.max_file_size}",
            }

        try:
            # 生成存储路径
            object_key = self._generate_file_path(filename, file_type, user_id)

            # 自动检测MIME类型
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = "application/octet-stream"

            # 上传文件并设置为公共读取
            response = self.client.put_object(
                Bucket=self.config.bucket,
                Body=file_data,
                Key=object_key,
                ContentType=content_type,
                StorageClass="STANDARD",  # 存储类型
                ACL="public-read",  # 设置为公共读取
            )

            # 生成公共访问URL
            public_url = self._get_public_url(object_key)

            # 既然设置了ACL为公共读取，直接使用公共URL
            logger.info(f"文件上传成功: {object_key}")
            logger.info(f"公共访问URL: {public_url}")

            return {
                "success": True,
                "message": "文件上传成功",
                "cloud_path": object_key,
                "cloud_url": public_url,  # 使用公共URL，因为已设置为ACL公共读取
                "public_url": public_url,  # 公共URL
                "file_size": file_size,
                "content_type": content_type,
                "etag": response.get("ETag", ""),
            }

        except CosServiceError as e:
            error_msg = f"COS服务错误: {e.get_error_msg()}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except CosClientError as e:
            error_msg = f"COS客户端错误: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"上传失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    async def upload_file_from_url(
        self, file_url: str, filename: str, file_type: str, user_id: str
    ) -> Dict[str, Any]:
        """从URL下载文件并上传到COS

        Args:
            file_url: 文件URL
            filename: 保存的文件名
            file_type: 文件类型 ('image', 'video')
            user_id: 用户ID

        Returns:
            Dict: 上传结果
        """
        # 重试下载最多3次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 下载文件
                logger.info(
                    f"正在从URL下载文件 (尝试 {attempt + 1}/{max_retries}): {file_url}"
                )

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Sec-Fetch-Dest": "image",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "cross-site",
                    "Referer": "https://google.datas.systems/",
                }

                # 增加超时时间，对于大文件下载
                timeout = 60 if attempt > 0 else 30
                logger.info(f"发起HTTP请求: timeout={timeout}s")
                logger.debug(f"请求头详情: {headers}")

                # 先尝试HEAD请求检查URL是否可访问
                if attempt == 0:
                    logger.info(f"先进行HEAD请求检查URL可访问性: {file_url}")
                    try:
                        with requests.Session() as session:
                            session.headers.update(headers)
                            head_response = session.head(
                                file_url, timeout=10, allow_redirects=True
                            )
                            logger.info(
                                f"HEAD响应: status_code={head_response.status_code}"
                            )
                            logger.debug(f"HEAD响应头: {dict(head_response.headers)}")

                            if head_response.status_code == 404:
                                logger.error(f"HEAD请求确认URL不存在: {file_url}")
                                return {
                                    "success": False,
                                    "message": f"图片URL不存在: {file_url}",
                                }
                            elif head_response.status_code >= 400:
                                logger.warning(
                                    f"HEAD请求返回错误状态: {head_response.status_code}"
                                )
                                # 但继续尝试GET请求，因为有些服务器不支持HEAD
                    except Exception as head_error:
                        logger.warning(
                            f"HEAD请求失败，但继续尝试GET请求: {str(head_error)}"
                        )

                # 主要下载请求 - 使用session保持连接
                with requests.Session() as session:
                    # 设置session的默认headers
                    session.headers.update(headers)

                    response = session.get(
                        file_url, timeout=timeout, stream=True, allow_redirects=True
                    )

                logger.info(
                    f"GET响应: status_code={response.status_code}, content-type={response.headers.get('content-type', 'unknown')}"
                )
                logger.info(
                    f"GET响应头: {dict(list(response.headers.items())[:10])}"
                )  # 打印前10个响应头

                # 检查响应状态
                if response.status_code == 404:
                    logger.warning(f"图片URL返回404，可能已过期: {file_url}")
                    if attempt < max_retries - 1:
                        logger.info(f"等待 {(attempt + 1) * 2} 秒后重试...")
                        import time

                        time.sleep((attempt + 1) * 2)
                        continue
                    else:
                        return {
                            "success": False,
                            "message": f"图片URL已失效，尝试{max_retries}次均返回404: {file_url}",
                        }
                elif response.status_code == 403:
                    logger.warning(f"图片URL返回403，访问被拒绝: {file_url}")
                    if attempt < max_retries - 1:
                        logger.info(f"等待 {(attempt + 1) * 3} 秒后重试...")
                        import time

                        time.sleep((attempt + 1) * 3)
                        continue
                    else:
                        return {
                            "success": False,
                            "message": f"图片URL访问被拒绝，尝试{max_retries}次均返回403: {file_url}",
                        }
                elif response.status_code >= 500:
                    logger.warning(
                        f"图片URL返回服务器错误 {response.status_code}: {file_url}"
                    )
                    if attempt < max_retries - 1:
                        logger.info(f"服务器错误，等待 {(attempt + 1) * 5} 秒后重试...")
                        import time

                        time.sleep((attempt + 1) * 5)
                        continue
                    else:
                        return {
                            "success": False,
                            "message": f"服务器持续错误，尝试{max_retries}次均返回{response.status_code}: {file_url}",
                        }

                response.raise_for_status()

                # 分块下载以处理大文件
                logger.info(
                    f"开始下载文件内容，Content-Length: {response.headers.get('content-length', 'unknown')}"
                )
                file_data = b""
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file_data += chunk
                        downloaded_size += len(chunk)
                        if downloaded_size % 50000 == 0:  # 每50KB记录一次
                            logger.debug(f"已下载: {downloaded_size} bytes")

                logger.info(f"文件下载完成，总大小: {len(file_data)} bytes")

                content_type = response.headers.get("content-type", "image/png")

                # 如果没有提供文件名，从URL中提取
                if not filename:
                    parsed_url = urlparse(file_url)
                    filename = (
                        os.path.basename(parsed_url.path)
                        or f"downloaded_{uuid.uuid4().hex[:8]}"
                    )

                # 确保文件扩展名正确
                if not os.path.splitext(filename)[1] and content_type:
                    if "png" in content_type:
                        filename += ".png"
                    elif "jpeg" in content_type or "jpg" in content_type:
                        filename += ".jpg"
                    elif "webp" in content_type:
                        filename += ".webp"

                logger.info(
                    f"文件下载完成，大小: {len(file_data)} bytes, 类型: {content_type}"
                )

                # 验证下载的文件是否为有效图片
                if len(file_data) < 100:
                    logger.warning(
                        f"下载的文件过小，可能不是有效图片: {len(file_data)} bytes"
                    )
                    if attempt < max_retries - 1:
                        logger.info(f"文件过小，等待 {(attempt + 1) * 2} 秒后重试...")
                        import time

                        time.sleep((attempt + 1) * 2)
                        continue

                # 验证文件头是否为图片格式
                if not self._is_valid_image_data(file_data):
                    logger.warning(f"下载的数据不是有效的图片格式")
                    if attempt < max_retries - 1:
                        logger.info(
                            f"数据格式无效，等待 {(attempt + 1) * 2} 秒后重试..."
                        )
                        import time

                        time.sleep((attempt + 1) * 2)
                        continue

                # 上传到COS
                result = await self.upload_file_from_bytes(
                    file_data=file_data,
                    filename=filename,
                    file_type=file_type,
                    user_id=user_id,
                    content_type=content_type,
                )

                # 如果上传成功，确保返回的URL是预签名URL
                if result.get("success") and result.get("cloud_path"):
                    # 文件已设置为公共读取，直接使用公共URL
                    logger.info(f"上传成功，使用公共URL: {result.get('cloud_url')}")

                return result

            except requests.exceptions.Timeout as e:
                logger.warning(f"下载超时 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {(attempt + 1) * 2} 秒后重试...")
                    import time

                    time.sleep((attempt + 1) * 2)
                    continue
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"网络请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    logger.info(f"等待 {(attempt + 1) * 2} 秒后重试...")
                    import time

                    time.sleep((attempt + 1) * 2)
                    continue
            except Exception as e:
                logger.warning(
                    f"下载过程中出现错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    continue

        # 如果所有重试都失败了，返回最后的错误
        error_msg = f"下载文件失败，已重试{max_retries}次: URL={file_url} - 所有重试均失败，可能的原因：1)图片URL已过期 2)防爬虫限制 3)网络连接问题"
        logger.error(error_msg)
        logger.error(f"最后尝试的请求头: {headers}")
        return {"success": False, "message": error_msg}

    async def delete_file(self, object_key: str) -> Dict[str, Any]:
        """删除COS中的文件

        Args:
            object_key: COS对象键

        Returns:
            Dict: 删除结果
        """
        if not self.is_available():
            return {"success": False, "message": "COS服务未初始化或未启用"}

        try:
            response = self.client.delete_object(
                Bucket=self.config.bucket, Key=object_key
            )

            logger.info(f"文件删除成功: {object_key}")

            return {"success": True, "message": "文件删除成功"}

        except CosServiceError as e:
            error_msg = f"COS服务错误: {e.get_error_msg()}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except CosClientError as e:
            error_msg = f"COS客户端错误: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"删除失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    async def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """获取文件信息

        Args:
            object_key: COS对象键

        Returns:
            Dict: 文件信息
        """
        if not self.is_available():
            return {"success": False, "message": "COS服务未初始化或未启用"}

        try:
            response = self.client.head_object(
                Bucket=self.config.bucket, Key=object_key
            )

            return {
                "success": True,
                "file_info": {
                    "size": int(response.get("Content-Length", 0)),
                    "content_type": response.get("Content-Type"),
                    "last_modified": response.get("Last-Modified"),
                    "etag": response.get("ETag", "").strip('"'),
                    "storage_class": response.get("x-cos-storage-class", "STANDARD"),
                },
            }

        except CosServiceError as e:
            if e.get_error_code() == "NoSuchKey":
                return {"success": False, "message": "文件不存在"}
            error_msg = f"COS服务错误: {e.get_error_msg()}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"获取文件信息失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    def _is_valid_image_data(self, data: bytes) -> bool:
        """验证数据是否为有效的图片格式

        Args:
            data: 文件数据

        Returns:
            bool: 是否为有效图片
        """
        if len(data) < 8:
            return False

        # 检查常见图片格式的文件头
        # JPEG: FF D8 FF
        if data.startswith(b"\xff\xd8\xff"):
            return True
        # PNG: 89 50 4E 47 0D 0A 1A 0A
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return True
        # GIF: 47 49 46 38
        if data.startswith(b"GIF8"):
            return True
        # WebP: RIFF...WEBP
        if data.startswith(b"RIFF") and b"WEBP" in data[:12]:
            return True
        # BMP: 42 4D
        if data.startswith(b"BM"):
            return True

        return False

    def get_file_url(self, object_key: str) -> str:
        """获取文件的访问URL

        Args:
            object_key: COS对象键

        Returns:
            str: 文件访问URL
        """
        return self._get_public_url(object_key)
