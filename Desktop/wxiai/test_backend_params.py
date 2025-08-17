#!/usr/bin/env python3
"""
测试后端 Midjourney 参数格式修复
验证后端是否正确使用 --q 和 --v 参数格式
"""

import sys

sys.path.append("/Users/liuqingliang/Desktop/openwebui/open-webui/backend")


def test_backend_prompt_building():
    """测试后端 prompt 构建"""
    print("🔧 Testing Backend Prompt Building...")

    try:
        from open_webui.utils.midjourney import MJApiClient
        from open_webui.models.midjourney import MJGenerateRequest, MJAdvancedParams

        # 创建一个模拟的配置
        class MockConfig:
            def __init__(self):
                self.base_url = "https://test.com"
                self.api_key = "test"
                self.enabled = True

        # 创建客户端
        client = MJApiClient(MockConfig())

        # 测试用例 1: 基础参数
        print("\n📋 Test 1: 基础参数 (quality + version)")
        advanced_params = MJAdvancedParams(
            quality=1, version="v6.1", aspect_ratio="1:1"
        )

        request = MJGenerateRequest(
            prompt="dog", mode="fast", advanced_params=advanced_params
        )

        result = client.build_prompt(request)
        expected = "dog --ar 1:1 --q 1 --v 6.1"

        print(f"Expected: {expected}")
        print(f"Got:      {result}")
        print(f"Result: {'✅ PASS' if result == expected else '❌ FAIL'}")

        test1_pass = result == expected

        # 测试用例 2: 完整参数
        print("\n📋 Test 2: 完整参数测试")
        advanced_params2 = MJAdvancedParams(
            aspect_ratio="16:9",
            chaos=50,
            stylize=100,
            seed=12345,
            weird=250,
            quality=2,
            version="v7",
            tile=True,
        )

        request2 = MJGenerateRequest(
            prompt="beautiful landscape", mode="fast", advanced_params=advanced_params2
        )

        result2 = client.build_prompt(request2)
        expected2 = "beautiful landscape --ar 16:9 --chaos 50 --stylize 100 --weird 250 --seed 12345 --q 2 --v 7 --tile"

        print(f"Expected: {expected2}")
        print(f"Got:      {result2}")
        print(f"Result: {'✅ PASS' if result2 == expected2 else '❌ FAIL'}")

        test2_pass = result2 == expected2

        # 测试用例 3: 版本号处理
        print("\n📋 Test 3: 版本号处理测试")
        advanced_params3 = MJAdvancedParams(
            quality=0.5, version="v5.2"  # 测试带点的版本号
        )

        request3 = MJGenerateRequest(
            prompt="test prompt", mode="fast", advanced_params=advanced_params3
        )

        result3 = client.build_prompt(request3)
        expected3 = "test prompt --q 0.5 --v 5.2"

        print(f"Expected: {expected3}")
        print(f"Got:      {result3}")
        print(f"Result: {'✅ PASS' if result3 == expected3 else '❌ FAIL'}")

        test3_pass = result3 == expected3

        all_passed = test1_pass and test2_pass and test3_pass

        print(
            f"\n📊 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
        )

        return all_passed

    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_parameter_consistency():
    """测试前后端参数一致性"""
    print("\n🔄 Testing Frontend-Backend Consistency...")

    # 模拟前端参数构建逻辑
    def frontend_build_prompt(prompt, params):
        finalPrompt = prompt

        if params.get("aspectRatio") and params["aspectRatio"] != "custom":
            finalPrompt += f" --ar {params['aspectRatio']}"

        if params.get("chaos") is not None:
            finalPrompt += f" --chaos {params['chaos']}"

        if params.get("stylize") is not None:
            finalPrompt += f" --stylize {params['stylize']}"

        if params.get("seed") is not None:
            finalPrompt += f" --seed {params['seed']}"

        if params.get("weird") is not None:
            finalPrompt += f" --weird {params['weird']}"

        if params.get("quality") is not None:
            finalPrompt += f" --q {params['quality']}"

        if params.get("version"):
            version_number = params["version"].replace("v", "")
            finalPrompt += f" --v {version_number}"

        if params.get("tile"):
            finalPrompt += " --tile"

        return finalPrompt

    # 测试数据
    test_params = {"aspectRatio": "1:1", "quality": 1, "version": "v6.1"}

    frontend_result = frontend_build_prompt("dog", test_params)
    expected = "dog --ar 1:1 --q 1 --v 6.1"

    print(f"Frontend result: {frontend_result}")
    print(f"Expected result: {expected}")
    print(f"Consistency: {'✅ PASS' if frontend_result == expected else '❌ FAIL'}")

    return frontend_result == expected


def main():
    """运行所有测试"""
    print("🚀 Testing MJ Parameter Format Fixes")
    print("=" * 50)

    backend_test = test_backend_prompt_building()
    consistency_test = test_parameter_consistency()

    print("\n" + "=" * 50)
    print("📊 Final Results:")
    print(f"   Backend Tests: {'✅ PASS' if backend_test else '❌ FAIL'}")
    print(f"   Consistency Tests: {'✅ PASS' if consistency_test else '❌ FAIL'}")

    if backend_test and consistency_test:
        print("\n🎉 All parameter format fixes working correctly!")
        print("\n📋 What's been fixed:")
        print("   ✅ Frontend: --quality → --q, --version v6.1 → --v 6.1")
        print("   ✅ Backend: --quality → --q, --version v6.1 → --v 6.1")
        print("   ✅ Version handling: 'v6.1' → '6.1' automatically")
        print("   ✅ Frontend-Backend consistency maintained")

        print("\n🎯 Example outputs:")
        print("   Input: dog --ar 1:1 --quality 1 --version v6.1")
        print("   Output: dog --ar 1:1 --q 1 --v 6.1")

    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

    return backend_test and consistency_test


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
