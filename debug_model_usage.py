#!/usr/bin/env python3
"""
Debug script to find where juggernautXL_v8Rundiffusion_V8 model is being used
"""

import json
import sys
from pathlib import Path


def search_in_dict(data, search_term, path=""):
    """递归搜索字典中的值"""
    results = []

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, str) and search_term.lower() in value.lower():
                results.append(f"Found '{search_term}' at {current_path}: {value}")
            elif isinstance(value, (dict, list)):
                results.extend(search_in_dict(value, search_term, current_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]" if path else f"[{i}]"
            if isinstance(item, str) and search_term.lower() in item.lower():
                results.append(f"Found '{search_term}' at {current_path}: {item}")
            elif isinstance(item, (dict, list)):
                results.extend(search_in_dict(item, search_term, current_path))

    return results


def main():
    search_term = "juggernaut"

    # 搜索工作流配置
    print("=== 搜索工作流配置中的模型引用 ===")

    # 检查你提供的配置
    your_config = {
        "parameter_schema": {
            "fields": [
                {
                    "name": "image",
                    "displayName": "图像",
                    "type": "IMAGE",
                    "id": "image",
                    "parentId": 2,
                    "image_upload": True,
                    "isMaskImage": False,
                },
                {
                    "name": "sdxl_model",
                    "displayName": "SDXL模型",
                    "type": "MODEL",
                    "id": "sdxl_model",
                    "parentId": 15,
                },
                {
                    "name": "steps",
                    "displayName": "步数",
                    "type": "INT",
                    "id": "steps",
                    "parentId": 15,
                    "defaultValue": 45,
                    "min": 3,
                    "max": 4096,
                    "step": 1,
                },
            ]
        },
        "default_params": {
            "templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
            "generateParams": {
                "2": {
                    "class_type": "LoadImage",
                    "inputs": {
                        "image": "https://liblibai-tmp-image.liblib.cloud/img/84cd9ecbef5b4333afb1125200e50242/2b04302c9011b28337a6c992faa62c9447d64de71f41ea6a19e741d9873e1d4d.png"
                    },
                },
                "15": {
                    "class_type": "SUPIR_Upscale",
                    "inputs": {
                        "sdxl_model": "e18fe70ddebd42a8b0fc9351c6469948",
                        "steps": 45,
                    },
                },
                "workflowUuid": "3e54edc7d52b4fa49644bfa92ad06c13",
            },
        },
    }

    # 搜索配置
    results = search_in_dict(your_config, search_term)
    if results:
        print("在你的配置中发现:")
        for result in results:
            print(f"  {result}")
    else:
        print("❌ 在你的配置中没有找到 'juggernaut' 相关内容")

    print("\n=== 可能的来源分析 ===")
    print("1. 检查Template UUID: 4df2efa0f18d46dc9758803e478eb51c")
    print("   这个模板本身可能包含不可商用模型")

    print("\n2. 检查工作流默认参数中是否有隐藏节点:")
    default_params = your_config["default_params"]["generateParams"]
    print(f"   当前节点: {list(default_params.keys())}")

    print("\n3. 检查SUPIR_Upscale节点参数:")
    supir_node = default_params.get("15", {})
    if "inputs" in supir_node:
        print(f"   SUPIR节点参数: {supir_node['inputs']}")
        # 检查sdxl_model参数
        sdxl_model = supir_node["inputs"].get("sdxl_model", "")
        print(f"   SDXL模型ID: {sdxl_model}")

    print("\n=== 建议解决方案 ===")
    print("1. 检查哩布官方文档，找到可商用的模型列表")
    print("2. 将 sdxl_model 参数改为可商用模型ID")
    print("3. 或者换一个不使用限制模型的Template UUID")


if __name__ == "__main__":
    main()
