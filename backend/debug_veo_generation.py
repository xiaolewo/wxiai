#!/usr/bin/env python3
"""
调试Veo生成API - 模拟前端请求
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))

# 设置环境变量
os.environ.setdefault('OPENAI_API_KEY', 'sk-test')

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_veo_generation():
    """测试Veo视频生成"""
    try:
        print("🔧 正在导入Veo模块...")
        from open_webui.models.veo import VeoConfig, VeoGenerateRequest
        from open_webui.utils.veo import process_veo_generation
        from open_webui.models.credits import Credits
        print("✅ 模块导入成功")
        
        # 创建测试配置
        print("📋 创建测试配置...")
        config_data = {
            'enabled': True,
            'base_url': 'https://api.veoai.com',
            'api_key': 'test-api-key-for-debugging',
            'default_model': 'veo3-pro-frames',
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
        
        config = VeoConfig.save_config(config_data)
        print(f"✅ 配置创建成功: enabled={config.enabled}, default_model={config.default_model}")
        
        # 创建测试用户和积分
        test_user_id = "test_user_debug_001"
        print(f"💰 为测试用户 {test_user_id} 设置积分...")
        
        # 确保用户有足够的积分
        Credits.update_user_credits(test_user_id, 1000)
        user_credits = Credits.get_user_credits(test_user_id)
        print(f"💰 用户积分设置完成: {user_credits.credit if user_credits else 0}")
        
        # 创建图生视频测试请求
        print("🖼️ 创建图生视频测试请求...")
        test_images = [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="  # 1x1像素透明PNG
        ]
        
        request = VeoGenerateRequest(
            prompt="A beautiful sunset over the ocean with gentle waves",
            model="veo3-pro-frames",
            enhance_prompt=True,
            images=test_images
        )
        
        print(f"📝 测试请求创建完成:")
        print(f"   模型: {request.model}")
        print(f"   提示词: {request.prompt}")
        print(f"   图片数量: {len(request.images)}")
        print(f"   提示词优化: {request.enhance_prompt}")
        
        # 执行生成请求
        print("\n🎬 开始执行Veo生成请求...")
        print("=" * 60)
        
        result = await process_veo_generation(request, test_user_id)
        
        print("=" * 60)
        print(f"🎬 Veo生成请求完成")
        
        # 输出结果
        print(f"\n📊 结果分析:")
        print(f"   成功: {result.get('success')}")
        if result.get('success'):
            print(f"   任务ID: {result.get('task_id')}")
            print(f"   外部任务ID: {result.get('external_task_id')}")
            print(f"   积分消耗: {result.get('credits_cost')}")
            print(f"   消息: {result.get('message')}")
        else:
            print(f"   错误: {result.get('error')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始调试Veo生成API...")
    print("🔍 这将显示详细的执行日志，帮助定位400错误的原因")
    print("=" * 60)
    
    success = asyncio.run(test_veo_generation())
    
    print("=" * 60)
    if success:
        print("✅ Veo生成API调试完成 - 执行成功")
    else:
        print("❌ Veo生成API调试完成 - 执行失败")
        print("📋 请查看上方的详细日志来定位问题")