#!/usr/bin/env python3
"""
测试Veo用户配置API
检查用户端配置是否包含正确的模型信息和默认模型
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))

# 设置环境变量（如果没有的话）
os.environ.setdefault('OPENAI_API_KEY', 'sk-test')

def test_veo_user_config():
    """测试Veo用户配置API"""
    try:
        print("🔧 正在导入Veo模块...")
        from open_webui.models.veo import VeoConfig
        print("✅ 模块导入成功")
        
        # 获取配置
        print("\n📋 测试配置获取...")
        config = VeoConfig.get_config()
        
        if not config:
            print("⚠️  没有找到配置，创建默认配置...")
            default_config_data = {
                'enabled': True,
                'base_url': 'https://api.veoai.com',
                'api_key': 'test-api-key',
                'default_model': 'veo3',
                'default_enhance_prompt': True,
                'max_concurrent_tasks': 3,
                'task_timeout': 900000,
                'query_interval': 15000,
                'model_credits_config': {
                    "veo3": 100,
                    "veo3-fast": 80,
                    "veo3-pro": 150,
                    "veo3-pro-frames": 200,
                    "veo2": 90,
                    "veo2-fast": 70,
                    "veo2-fast-frames": 120,
                    "veo2-fast-components": 160,
                    "veo2-pro": 140,
                    "veo3-fast-frames": 90
                }
            }
            config = VeoConfig.save_config(default_config_data)
            print("✅ 默认配置创建成功")
        
        print(f"📊 当前配置: enabled={config.enabled}, default_model={config.default_model}")
        
        # 测试支持的模型列表
        print("\n🎯 测试支持的模型列表...")
        supported_models = config.get_supported_models()
        print(f"支持的模型数量: {len(supported_models)}")
        for model in supported_models:
            print(f"  - {model}")
        
        if not supported_models:
            print("❌ 支持的模型列表为空！这会导致用户端没有可选模型。")
            return False
        
        # 测试默认模型积分配置
        print("\n💰 测试模型积分配置...")
        model_credits = config.model_credits_config or config._get_default_model_credits()
        print(f"模型积分配置数量: {len(model_credits)}")
        for model, credits in model_credits.items():
            print(f"  - {model}: {credits} 积分")
        
        # 测试模型图片限制配置
        print("\n🖼️ 测试模型图片限制配置...")
        for model in supported_models:
            limits = config.get_model_image_limits(model)
            max_images = limits.get("max", 0)
            description = limits.get("description", "")
            print(f"  - {model}: 最多 {max_images} 张图片 - {description}")
        
        # 模拟用户配置API调用
        print("\n🌐 模拟用户配置API调用...")
        
        # 模拟API响应构建
        model_image_limits = {}
        for model in supported_models:
            model_image_limits[model] = config.get_model_image_limits(model)
        
        user_config = {
            "enabled": config.enabled,
            "supported_models": supported_models,
            "model_credits_config": model_credits,
            "default_model": config.default_model,
            "default_enhance_prompt": config.default_enhance_prompt,
            "model_image_limits": model_image_limits,
        }
        
        print("📋 用户配置API响应:")
        print(f"  enabled: {user_config['enabled']}")
        print(f"  default_model: {user_config['default_model']}")
        print(f"  default_enhance_prompt: {user_config['default_enhance_prompt']}")
        print(f"  supported_models: {len(user_config['supported_models'])} 个")
        print(f"  model_credits_config: {len(user_config['model_credits_config'])} 个")
        print(f"  model_image_limits: {len(user_config['model_image_limits'])} 个")
        
        # 验证关键字段
        critical_checks = [
            ("enabled", user_config['enabled'] is not None),
            ("default_model", user_config['default_model'] is not None and user_config['default_model'] != ""),
            ("supported_models", len(user_config['supported_models']) > 0),
            ("model_credits_config", len(user_config['model_credits_config']) > 0),
            ("default_model_in_supported", user_config['default_model'] in user_config['supported_models']),
            ("default_model_has_credits", user_config['default_model'] in user_config['model_credits_config']),
        ]
        
        print("\n✅ 关键字段验证:")
        all_passed = True
        for check_name, result in critical_checks:
            if result:
                print(f"  ✅ {check_name}: 通过")
            else:
                print(f"  ❌ {check_name}: 失败")
                all_passed = False
        
        if not all_passed:
            return False
        
        # 检查默认模型是否存在于支持列表中
        if user_config['default_model'] not in user_config['supported_models']:
            print(f"❌ 默认模型 '{user_config['default_model']}' 不在支持的模型列表中！")
            print(f"支持的模型: {user_config['supported_models']}")
            return False
        
        # 输出完整的用户配置（供调试）
        print("\n📄 完整用户配置JSON:")
        import json
        print(json.dumps(user_config, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始测试Veo用户配置API...")
    print("=" * 60)
    
    success = test_veo_user_config()
    
    print("=" * 60)
    if success:
        print("✅ Veo用户配置API测试通过！")
        print("📝 配置包含正确的模型信息和默认模型。")
    else:
        print("❌ Veo用户配置API测试失败！")
        print("🔧 请检查配置或API实现。")
        sys.exit(1)