/**
 * 测试 Midjourney 参数格式修复
 * 验证参数是否使用正确的简写格式
 */

// 模拟参数构建逻辑
function buildPrompt(prompt, params) {
	let finalPrompt = prompt;

	// 添加高级参数到prompt
	if (params) {
		if (params.aspectRatio && params.aspectRatio !== 'custom') {
			finalPrompt += ` --ar ${params.aspectRatio}`;
		} else if (params.customAspectRatio) {
			finalPrompt += ` --ar ${params.customAspectRatio.width}:${params.customAspectRatio.height}`;
		}

		if (params.chaos !== undefined) {
			finalPrompt += ` --chaos ${params.chaos}`;
		}

		if (params.stylize !== undefined) {
			finalPrompt += ` --stylize ${params.stylize}`;
		}

		if (params.seed !== undefined) {
			finalPrompt += ` --seed ${params.seed}`;
		}

		if (params.weird !== undefined) {
			finalPrompt += ` --weird ${params.weird}`;
		}

		if (params.quality !== undefined) {
			finalPrompt += ` --q ${params.quality}`; // 修复: 使用 --q 而不是 --quality
		}

		if (params.version) {
			// 去掉 'v' 前缀，因为 --v 参数不需要 'v' 前缀
			const versionNumber = params.version.replace('v', '');
			finalPrompt += ` --v ${versionNumber}`; // 修复: 使用 --v 而不是 --version
		}

		if (params.tile) {
			finalPrompt += ` --tile`;
		}
	}

	return finalPrompt;
}

// 测试用例
function testParameterFormats() {
	console.log('🧪 Testing MJ Parameter Formats...\n');

	const testCases = [
		{
			name: '基础测试 - quality 和 version',
			prompt: 'dog',
			params: {
				aspectRatio: '1:1',
				quality: 1,
				version: 'v6.1'
			},
			expected: 'dog --ar 1:1 --q 1 --v 6.1'
		},
		{
			name: '完整参数测试',
			prompt: 'beautiful landscape',
			params: {
				aspectRatio: '16:9',
				chaos: 50,
				stylize: 100,
				seed: 12345,
				weird: 250,
				quality: 2,
				version: 'v7',
				tile: true
			},
			expected:
				'beautiful landscape --ar 16:9 --chaos 50 --stylize 100 --seed 12345 --weird 250 --q 2 --v 7 --tile'
		},
		{
			name: '自定义比例测试',
			prompt: 'portrait',
			params: {
				customAspectRatio: { width: 3, height: 4 },
				quality: 0.5,
				version: 'v5.2'
			},
			expected: 'portrait --ar 3:4 --q 0.5 --v 5.2'
		}
	];

	let passed = 0;
	let total = testCases.length;

	testCases.forEach((testCase, index) => {
		const result = buildPrompt(testCase.prompt, testCase.params);
		const success = result === testCase.expected;

		console.log(`📋 Test ${index + 1}: ${testCase.name}`);
		console.log(`Input: "${testCase.prompt}" + params`);
		console.log(`Expected: "${testCase.expected}"`);
		console.log(`Got:      "${result}"`);
		console.log(`Result: ${success ? '✅ PASS' : '❌ FAIL'}\n`);

		if (success) passed++;
	});

	console.log('📊 Summary:');
	console.log(`✅ Passed: ${passed}/${total}`);
	console.log(`❌ Failed: ${total - passed}/${total}`);

	if (passed === total) {
		console.log('\n🎉 All parameter format tests passed!');
		console.log('\n📋 Key Fixes:');
		console.log('  ✅ --quality → --q');
		console.log('  ✅ --version v6.1 → --v 6.1');
		console.log('  ✅ 自动去除版本号中的 "v" 前缀');
		console.log('  ✅ 保持其他参数格式不变');
	} else {
		console.log('\n⚠️ Some tests failed!');
	}

	return passed === total;
}

// 运行测试
testParameterFormats();
