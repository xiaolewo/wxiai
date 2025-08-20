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

            # 上传文件
            response = self.client.put_object(
                Bucket=self.config.bucket,
                Body=file_data,
                Key=object_key,
                ContentType=content_type,
                StorageClass="STANDARD",  # 存储类型
            )

            # 生成访问URL
            public_url = self._get_public_url(object_key)

            logger.info(f"文件上传成功: {object_key}")

            return {
                "success": True,
                "message": "文件上传成功",
                "cloud_path": object_key,
                "cloud_url": public_url,
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
        try:
            # 下载文件
            logger.info(f"正在从URL下载文件: {file_url}")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(file_url, headers=headers, timeout=30)
            response.raise_for_status()

            file_data = response.content
            content_type = response.headers.get("content-type")

            # 如果没有提供文件名，从URL中提取
            if not filename:
                parsed_url = urlparse(file_url)
                filename = (
                    os.path.basename(parsed_url.path)
                    or f"downloaded_{uuid.uuid4().hex[:8]}"
                )

            logger.info(f"文件下载完成，大小: {len(file_data)} bytes")

            # 上传到COS
            return await self.upload_file_from_bytes(
                file_data=file_data,
                filename=filename,
                file_type=file_type,
                user_id=user_id,
                content_type=content_type,
            )

        except requests.exceptions.RequestException as e:
            error_msg = f"下载文件失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"处理URL文件失败: {str(e)}"
            logger.error(error_msg)
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

    def get_file_url(self, object_key: str) -> str:
        """获取文件的访问URL

        Args:
            object_key: COS对象键

        Returns:
            str: 文件访问URL
        """
        return self._get_public_url(object_key)
