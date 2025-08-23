#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试COS连接"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from open_webui.models.cloud_storage import CloudStorageConfig

# 创建测试配置
config = CloudStorageConfig(
    provider="tencent-cos",
    enabled=True,
    secret_id="your_secret_id",  # 需要填入实际的
    secret_key="your_secret_key",  # 需要填入实际的
    region="ap-beijing",
    bucket="your_bucket_name",  # 需要填入实际的
    base_path="open-webui/",
    image_path="images/",
    video_path="videos/",
    max_file_size=104857600,
    domain="",
)

# 导入并初始化服务
from open_webui.utils.cloud_storage.tencent_cos import TencentCOSService

service = TencentCOSService(config)

# 测试SDK是否正确加载
import asyncio


async def test():
    print("测试COS连接...")
    result = await service.test_connection()
    print(f"结果: {result}")


# 运行测试
asyncio.run(test())
