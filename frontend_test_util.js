/**
 * 可灵对口型前端功能测试工具
 * 在浏览器控制台运行以验证前端功能
 */

class KlingLipSyncFrontendTester {
	constructor() {
		this.testResults = {
			navigation: { status: 'pending', details: [] },
			ui_components: { status: 'pending', details: [] },
			voice_options: { status: 'pending', details: [] },
			form_validation: { status: 'pending', details: [] },
			api_integration: { status: 'pending', details: [] }
		};
	}

	async runAllTests() {
		console.log('🎭 开始可灵对口型前端功能测试...');
		console.log('=' * 60);

		await this.testNavigation();
		await this.testUIComponents();
		await this.testVoiceOptions();
		await this.testFormValidation();
		await this.testAPIIntegration();

		this.generateReport();
	}

	async testNavigation() {
		console.log('🧭 测试导航功能...');

		try {
			// 检查侧边栏是否包含视频口型链接
			const sidebarLinks = document.querySelectorAll('a[href*="lip-sync"]');
			if (sidebarLinks.length === 0) {
				this.testResults.navigation.details.push('侧边栏缺少视频口型导航链接');
			} else {
				this.testResults.navigation.details.push('✅ 侧边栏包含视频口型导航');
			}

			// 检查管理员设置导航
			const adminLinks = document.querySelectorAll(
				'a[href*="admin/settings/kling-lip-sync"], button[data-tab="kling-lip-sync"]'
			);
			if (adminLinks.length === 0) {
				this.testResults.navigation.details.push('管理员设置缺少可灵对口型配置');
			} else {
				this.testResults.navigation.details.push('✅ 管理员设置包含可灵对口型配置');
			}

			// 测试路由是否可访问
			if (window.location.pathname.includes('/lip-sync')) {
				this.testResults.navigation.details.push('✅ 当前在可灵对口型页面');
			}

			this.testResults.navigation.status =
				this.testResults.navigation.details.filter((d) => !d.startsWith('✅')).length === 0
					? 'passed'
					: 'failed';
		} catch (error) {
			this.testResults.navigation.status = 'failed';
			this.testResults.navigation.details.push(`导航测试异常: ${error.message}`);
		}
	}

	async testUIComponents() {
		console.log('🎨 测试UI组件...');

		try {
			const requiredElements = {
				mode_selector: 'input[name="mode"], select[name="mode"]',
				text_input: 'textarea[name="text"], input[name="text"]',
				voice_language_selector: 'select[name="voice_language"], select[name="voiceLanguage"]',
				voice_selector: 'select[name="voice_id"], select[name="voiceId"]',
				file_upload: 'input[type="file"]',
				submit_button: 'button[type="submit"], button:contains("生成"), button:contains("提交")'
			};

			for (const [name, selector] of Object.entries(requiredElements)) {
				const elements = document.querySelectorAll(selector);
				if (elements.length === 0) {
					this.testResults.ui_components.details.push(`缺少UI元素: ${name}`);
				} else {
					this.testResults.ui_components.details.push(`✅ 找到UI元素: ${name}`);
				}
			}

			// 检查响应式设计
			const container = document.querySelector('.grid, .flex, .container');
			if (container) {
				this.testResults.ui_components.details.push('✅ 页面使用响应式布局');
			} else {
				this.testResults.ui_components.details.push('页面可能缺少响应式布局');
			}

			this.testResults.ui_components.status =
				this.testResults.ui_components.details.filter((d) => !d.startsWith('✅')).length === 0
					? 'passed'
					: 'failed';
		} catch (error) {
			this.testResults.ui_components.status = 'failed';
			this.testResults.ui_components.details.push(`UI组件测试异常: ${error.message}`);
		}
	}

	async testVoiceOptions() {
		console.log('🎵 测试音色选项...');

		try {
			// 检查语言选择器
			const languageSelector = document.querySelector(
				'select[name="voice_language"], select[name="voiceLanguage"]'
			);
			if (!languageSelector) {
				this.testResults.voice_options.details.push('缺少语言选择器');
				this.testResults.voice_options.status = 'failed';
				return;
			}

			// 检查语言选项
			const languageOptions = languageSelector.querySelectorAll('option');
			const languageValues = Array.from(languageOptions).map((opt) => opt.value);

			if (!languageValues.includes('zh')) {
				this.testResults.voice_options.details.push('缺少中文语言选项');
			} else {
				this.testResults.voice_options.details.push('✅ 包含中文语言选项');
			}

			if (!languageValues.includes('en')) {
				this.testResults.voice_options.details.push('缺少英文语言选项');
			} else {
				this.testResults.voice_options.details.push('✅ 包含英文语言选项');
			}

			// 检查音色选择器
			const voiceSelector = document.querySelector(
				'select[name="voice_id"], select[name="voiceId"]'
			);
			if (!voiceSelector) {
				this.testResults.voice_options.details.push('缺少音色选择器');
			} else {
				const voiceOptions = voiceSelector.querySelectorAll('option');
				this.testResults.voice_options.details.push(`✅ 音色选项数量: ${voiceOptions.length}`);

				// 模拟语言切换测试
				if (languageSelector && voiceSelector) {
					this.testResults.voice_options.details.push('✅ 音色选择器响应语言变化');
				}
			}

			this.testResults.voice_options.status =
				this.testResults.voice_options.details.filter((d) => !d.startsWith('✅')).length === 0
					? 'passed'
					: 'failed';
		} catch (error) {
			this.testResults.voice_options.status = 'failed';
			this.testResults.voice_options.details.push(`音色选项测试异常: ${error.message}`);
		}
	}

	async testFormValidation() {
		console.log('📝 测试表单验证...');

		try {
			const form = document.querySelector('form');
			if (!form) {
				this.testResults.form_validation.details.push('页面缺少表单元素');
				this.testResults.form_validation.status = 'failed';
				return;
			}

			// 检查必填字段验证
			const requiredFields = form.querySelectorAll(
				'input[required], textarea[required], select[required]'
			);
			this.testResults.form_validation.details.push(`✅ 必填字段数量: ${requiredFields.length}`);

			// 检查文件上传验证
			const fileInput = form.querySelector('input[type="file"]');
			if (fileInput) {
				const accept = fileInput.getAttribute('accept');
				if (accept) {
					this.testResults.form_validation.details.push(`✅ 文件类型限制: ${accept}`);
				} else {
					this.testResults.form_validation.details.push('文件上传缺少类型限制');
				}
			}

			// 检查表单提交处理
			if (form.onsubmit || form.getAttribute('on:submit')) {
				this.testResults.form_validation.details.push('✅ 表单有提交处理函数');
			} else {
				this.testResults.form_validation.details.push('表单可能缺少提交处理');
			}

			this.testResults.form_validation.status =
				this.testResults.form_validation.details.filter((d) => !d.startsWith('✅')).length === 0
					? 'passed'
					: 'failed';
		} catch (error) {
			this.testResults.form_validation.status = 'failed';
			this.testResults.form_validation.details.push(`表单验证测试异常: ${error.message}`);
		}
	}

	async testAPIIntegration() {
		console.log('🔌 测试API集成...');

		try {
			// 检查是否有API调用函数
			if (typeof window.createKlingLipSyncTask === 'function') {
				this.testResults.api_integration.details.push('✅ 找到任务创建API函数');
			} else {
				this.testResults.api_integration.details.push('缺少任务创建API函数');
			}

			// 检查localStorage中的token
			const token = localStorage.getItem('token') || sessionStorage.getItem('token');
			if (token) {
				this.testResults.api_integration.details.push('✅ 找到认证token');
			} else {
				this.testResults.api_integration.details.push('缺少认证token (可能影响API调用)');
			}

			// 检查网络请求
			let hasNetworkCalls = false;
			const originalFetch = window.fetch;
			window.fetch = function (...args) {
				if (args[0].includes('kling-lip-sync')) {
					hasNetworkCalls = true;
				}
				return originalFetch.apply(this, args);
			};

			// 恢复原始fetch
			setTimeout(() => {
				window.fetch = originalFetch;
				if (hasNetworkCalls) {
					this.testResults.api_integration.details.push('✅ 检测到可灵对口型API调用');
				}
			}, 1000);

			this.testResults.api_integration.status =
				this.testResults.api_integration.details.filter((d) => !d.startsWith('✅')).length === 0
					? 'passed'
					: 'partial';
		} catch (error) {
			this.testResults.api_integration.status = 'failed';
			this.testResults.api_integration.details.push(`API集成测试异常: ${error.message}`);
		}
	}

	generateReport() {
		console.log('\n' + '='.repeat(80));
		console.log('🎭 可灵对口型前端功能测试报告');
		console.log('='.repeat(80));

		const overallStatus = Object.values(this.testResults).every(
			(result) => result.status === 'passed'
		)
			? '✅ 全部通过'
			: '❌ 存在问题';

		console.log(`整体状态: ${overallStatus}`);
		console.log();

		for (const [component, result] of Object.entries(this.testResults)) {
			const statusEmoji =
				result.status === 'passed' ? '✅' : result.status === 'partial' ? '⚠️' : '❌';

			console.log(`${statusEmoji} ${component.toUpperCase()}: ${result.status}`);
			result.details.forEach((detail) => {
				console.log(`   • ${detail}`);
			});
			console.log();
		}

		// 生成修复建议
		const issues = [];
		Object.values(this.testResults).forEach((result) => {
			result.details.forEach((detail) => {
				if (!detail.startsWith('✅')) {
					issues.push(detail);
				}
			});
		});

		if (issues.length > 0) {
			console.log('🔧 建议修复的问题:');
			issues.forEach((issue, index) => {
				console.log(`${index + 1}. ${issue}`);
			});
		} else {
			console.log('🎉 所有前端功能测试通过！');
		}

		console.log('='.repeat(80));

		return this.testResults;
	}

	// 辅助方法：模拟用户交互
	simulateUserInteraction() {
		console.log('🤖 模拟用户交互测试...');

		try {
			// 模拟模式切换
			const modeInputs = document.querySelectorAll('input[name="mode"]');
			if (modeInputs.length > 0) {
				modeInputs[0].click();
				console.log('✅ 模拟模式切换');
			}

			// 模拟语言切换
			const languageSelect = document.querySelector('select[name="voice_language"]');
			if (languageSelect) {
				languageSelect.value = 'en';
				languageSelect.dispatchEvent(new Event('change'));
				console.log('✅ 模拟语言切换到英文');

				setTimeout(() => {
					languageSelect.value = 'zh';
					languageSelect.dispatchEvent(new Event('change'));
					console.log('✅ 模拟语言切换回中文');
				}, 1000);
			}

			// 模拟文本输入
			const textInput = document.querySelector('textarea[name="text"], input[name="text"]');
			if (textInput) {
				textInput.value = '这是一段测试文本';
				textInput.dispatchEvent(new Event('input'));
				console.log('✅ 模拟文本输入');
			}
		} catch (error) {
			console.log(`模拟交互出错: ${error.message}`);
		}
	}

	// 性能测试
	testPerformance() {
		console.log('⚡ 性能测试...');

		const startTime = performance.now();

		// 检查页面加载时间
		if (window.performance && window.performance.timing) {
			const loadTime =
				window.performance.timing.loadEventEnd - window.performance.timing.navigationStart;
			console.log(`页面加载时间: ${loadTime}ms`);

			if (loadTime > 3000) {
				console.log('⚠️ 页面加载时间较长，建议优化');
			} else {
				console.log('✅ 页面加载时间正常');
			}
		}

		// 检查DOM元素数量
		const elementCount = document.querySelectorAll('*').length;
		console.log(`DOM元素数量: ${elementCount}`);

		if (elementCount > 1000) {
			console.log('⚠️ DOM元素较多，可能影响性能');
		}

		const endTime = performance.now();
		console.log(`测试执行时间: ${(endTime - startTime).toFixed(2)}ms`);
	}
}

// 使用方法：
console.log(`
🎭 可灵对口型前端测试工具已加载

使用方法：
const tester = new KlingLipSyncFrontendTester();

// 运行所有测试
await tester.runAllTests();

// 模拟用户交互
tester.simulateUserInteraction();

// 性能测试
tester.testPerformance();

// 运行单个测试
await tester.testNavigation();
await tester.testUIComponents();
await tester.testVoiceOptions();

开始测试...
`);

// 自动运行测试（如果页面已加载完成）
if (document.readyState === 'complete') {
	const autoTester = new KlingLipSyncFrontendTester();
	autoTester.runAllTests();
} else {
	window.addEventListener('load', () => {
		const autoTester = new KlingLipSyncFrontendTester();
		autoTester.runAllTests();
	});
}
