#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试腾讯云COS SDK实际可用的方法"""

from qcloud_cos import CosConfig, CosS3Client

# 创建一个假的配置来初始化客户端
config = CosConfig(Region="ap-beijing", SecretId="test", SecretKey="test")

client = CosS3Client(config)

# 测试各种可能的方法
methods_to_test = [
    "bucket_exists",
    "head_bucket",
    "list_objects",
    "list_objects_v2",
    "get_bucket",
    "head_object",
    "put_object",
    "delete_object",
]

print("检查CosS3Client实际可用的方法：\n")
for method in methods_to_test:
    if hasattr(client, method):
        print(f"✓ {method} - 存在")
    else:
        print(f"✗ {method} - 不存在")

print("\n实际可用的所有方法（不包括私有方法）：")
all_methods = [m for m in dir(client) if not m.startswith("_")]
for i, method in enumerate(sorted(all_methods), 1):
    print(f"{i:3}. {method}")
