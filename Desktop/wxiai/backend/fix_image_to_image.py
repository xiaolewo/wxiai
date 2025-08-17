#!/usr/bin/env python3
"""
修复图生图500错误的专项工具
基于诊断结果的精准修复
"""

import asyncio
import httpx
import json
import base64
import sys
import os

# 添加项目路径
sys.path.append("/Users/liuqingliang/Desktop/openwebui/open-webui/backend")

from open_webui.models.dreamwork import DreamWorkConfig


async def test_image_formats():
    """测试不同的图片格式和大小"""
    print("🔍 测试图片格式和大小对图生图的影响")

    config = DreamWorkConfig.get_config()
    if not config:
        print("❌ 无法获取DreamWork配置")
        return

    url = f"{config.base_url}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    # 不同大小和格式的测试图片
    test_images = {
        "tiny_png": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        "small_png": "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAEklEQVR42mNk+M9QDwTDKUgAD9wGAyglAocAAAAASUVORK5CYII=",
        "jpeg_test": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wn8=",
    }

    for img_name, img_data in test_images.items():
        print(f"\n   测试 {img_name}:")

        request_data = {
            "model": "doubao-seededit-3-0-i2i-250628",
            "prompt": "enhance this image",
            "image": img_data,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=request_data, headers=headers)

                print(f"     状态码: {response.status_code}")

                if response.status_code == 200:
                    print("     ✅ 成功！")
                    result = response.json()
                    print(f"     响应: {json.dumps(result, indent=2)}")
                    return img_data  # 返回成功的图片数据
                else:
                    error_text = response.text
                    print(f"     ❌ 错误: {error_text}")

                    try:
                        error_json = response.json()
                        if "error" in error_json:
                            print(f"     错误详情: {error_json['error']}")
                        if "message" in error_json:
                            print(f"     错误消息: {error_json['message']}")
                    except:
                        pass

        except Exception as e:
            print(f"     ❌ 异常: {e}")

    return None


async def test_different_models():
    """测试不同的模型名称"""
    print("\n🔍 测试不同的图生图模型")

    config = DreamWorkConfig.get_config()
    url = f"{config.base_url}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    # 测试不同的模型名称
    models = [
        "doubao-seededit-3-0-i2i-250628",  # 当前使用的
        "doubao-seededit-3-i2i",  # 简化版本
        "doubao-i2i",  # 更简化
        "seededit-3-0-i2i",  # 无前缀
    ]

    tiny_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    for model in models:
        print(f"\n   测试模型: {model}")

        request_data = {
            "model": model,
            "prompt": "test image editing",
            "image": tiny_png,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=request_data, headers=headers)

                print(f"     状态码: {response.status_code}")

                if response.status_code == 200:
                    print("     ✅ 模型有效！")
                    return model
                elif response.status_code == 404:
                    print("     ❌ 模型不存在")
                else:
                    print(f"     ❌ 其他错误: {response.text[:100]}")

        except Exception as e:
            print(f"     ❌ 异常: {e}")

    return None


async def test_parameter_combinations():
    """测试不同的参数组合"""
    print("\n🔍 测试参数组合")

    config = DreamWorkConfig.get_config()
    url = f"{config.base_url}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    tiny_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    # 不同的参数组合
    test_configs = [
        {
            "name": "最基本参数",
            "data": {
                "model": "doubao-seededit-3-0-i2i-250628",
                "prompt": "improve image quality",
                "image": tiny_png,
            },
        },
        {
            "name": "添加size参数",
            "data": {
                "model": "doubao-seededit-3-0-i2i-250628",
                "prompt": "improve image quality",
                "image": tiny_png,
                "size": "1024x1024",
            },
        },
        {
            "name": "添加response_format",
            "data": {
                "model": "doubao-seededit-3-0-i2i-250628",
                "prompt": "improve image quality",
                "image": tiny_png,
                "response_format": "url",
            },
        },
        {
            "name": "添加guidance_scale",
            "data": {
                "model": "doubao-seededit-3-0-i2i-250628",
                "prompt": "improve image quality",
                "image": tiny_png,
                "guidance_scale": 2.5,
            },
        },
    ]

    for test_config in test_configs:
        print(f"\n   {test_config['name']}:")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url, json=test_config["data"], headers=headers
                )

                print(f"     状态码: {response.status_code}")

                if response.status_code == 200:
                    print("     ✅ 成功！")
                    return test_config["data"]
                else:
                    print(f"     ❌ 失败: {response.text[:100]}")

        except Exception as e:
            print(f"     ❌ 异常: {e}")

    return None


async def create_fixed_api_function():
    """创建修复后的API函数"""
    print("\n🛠️ 基于测试结果创建修复函数")

    # 运行所有测试
    working_image = await test_image_formats()
    working_model = await test_different_models()
    working_params = await test_parameter_combinations()

    if working_image and working_model:
        print(f"\n✅ 找到工作配置:")
        print(f"   工作的图片格式: {'PNG (tiny)' if working_image else '未知'}")
        print(f"   工作的模型: {working_model}")
        print(f"   工作的参数: {working_params}")

        # 生成修复后的函数代码
        fixed_function = f'''
async def generate_image_to_image_final_fix(config, request) -> dict:
    """基于测试结果的最终修复版图生图函数"""
    url = f"{{config.base_url}}/v1/images/generations"
    
    # 验证输入
    if not request.image:
        raise ValueError("图生图需要输入图片")
    
    # 使用测试验证的图片处理方式
    image_data = request.image.strip()
    if image_data.startswith('data:'):
        if ',' in image_data:
            image_data = image_data.split(',')[1]
    
    # 清理空白字符
    image_data = ''.join(image_data.split())
    
    # 使用测试验证的最小参数集
    request_data = {{
        "model": "{working_model}",
        "prompt": request.prompt.strip(),
        "image": image_data
    }}
    
    headers = {{
        'Authorization': f'Bearer {{config.api_key}}',
        'Content-Type': 'application/json'
    }}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=request_data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_text = response.text
            raise ValueError(f"DreamWork API错误 ({{response.status_code}}): {{error_text}}")
'''

        print(f"\n📝 生成的修复函数:")
        print(fixed_function)

        return fixed_function
    else:
        print("\n❌ 未找到工作配置，可能需要检查API状态或联系技术支持")
        return None


async def main():
    """主函数"""
    print("🚀 DreamWork 图生图500错误专项修复")
    print("=" * 50)

    result = await create_fixed_api_function()

    if result:
        print("\n🎯 修复建议:")
        print("1. 将生成的函数替换到 dreamwork_fixed.py 中")
        print("2. 重启后端服务")
        print("3. 测试图生图功能")
    else:
        print("\n🔧 进一步诊断建议:")
        print("1. 检查DreamWork服务状态")
        print("2. 验证图生图模型是否可用")
        print("3. 联系DreamWork技术支持")


if __name__ == "__main__":
    asyncio.run(main())
