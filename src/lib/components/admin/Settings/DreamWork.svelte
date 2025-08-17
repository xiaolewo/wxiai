<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import DreamWork API functions
	import {
		type DreamWorkConfig,
		getDreamWorkConfig,
		saveDreamWorkConfig,
		testDreamWorkConnection
	} from '$lib/apis/dreamwork';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	// DreamWork 配置
	let dreamWorkConfig = {
		enabled: false,
		baseUrl: '',
		apiKey: '',
		textToImageModel: 'doubao-seedream-3-0-t2i-250415',
		imageToImageModel: 'doubao-seededit-3-0-i2i-250628',
		defaultSize: '1024x1024',
		defaultGuidanceScale: 2.5,
		watermarkEnabled: true,
		creditsPerGeneration: 10,
		maxConcurrentTasks: 5,
		taskTimeout: 300000 // 5分钟
	};

	// 支持的图片尺寸选项
	const sizeOptions = [
		{ value: '1024x1024', label: '1024×1024 (正方形)' },
		{ value: '1024x768', label: '1024×768 (4:3)' },
		{ value: '768x1024', label: '768×1024 (3:4)' },
		{ value: '1216x832', label: '1216×832 (3:2)' },
		{ value: '832x1216', label: '832×1216 (2:3)' },
		{ value: 'adaptive', label: '自适应' }
	];

	onMount(async () => {
		await loadDreamWorkConfig();
	});

	const loadDreamWorkConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getDreamWorkConfig($user.token);
			if (config) {
				dreamWorkConfig = { ...dreamWorkConfig, ...config };
			}
		} catch (error) {
			console.error('Failed to load DreamWork config:', error);
			toast.error('加载即梦配置失败');
		} finally {
			loading = false;
		}
	};

	const saveDreamWorkConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveDreamWorkConfig($user.token, dreamWorkConfig);
			toast.success('即梦配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save DreamWork config:', error);
			toast.error('保存即梦配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!dreamWorkConfig.baseUrl || !dreamWorkConfig.apiKey) {
			toast.error('请先配置 API URL 和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await testDreamWorkConnection($user.token);
			toast.success('连接测试成功');
		} catch (error) {
			console.error('Connection test failed:', error);
			toast.error('连接测试失败');
		} finally {
			loading = false;
		}
	};
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class=" space-y-3 pr-1.5">
		<div>
			<div class=" mb-1 text-sm font-medium">即梦 (DreamWork) 图像生成配置</div>
			<div class="text-xs text-gray-400 dark:text-gray-500">
				配置即梦API接入和积分消耗设置，支持文生图和图生图功能
			</div>
		</div>

		<hr class="dark:border-gray-700" />

		<!-- 启用开关 -->
		<div class="flex w-full justify-between">
			<div class="flex flex-col">
				<div class="text-sm font-medium">启用即梦</div>
				<div class="text-xs text-gray-400">启用即梦图像生成功能</div>
			</div>
			<Switch bind:state={dreamWorkConfig.enabled} />
		</div>

		{#if dreamWorkConfig.enabled}
			<!-- API 配置 -->
			<div>
				<div class="mb-2 text-sm font-medium">API 配置</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">API Base URL</div>
					<input
						bind:value={dreamWorkConfig.baseUrl}
						placeholder="https://ark.cn-beijing.volces.com"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">API Key</div>
					<SensitiveInput
						placeholder="your-dreamwork-api-key"
						bind:value={dreamWorkConfig.apiKey}
					/>
				</div>

				<button
					class="px-3 py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-lg"
					on:click={testConnection}
					disabled={loading}
				>
					{loading ? '测试中...' : '测试连接'}
				</button>
			</div>

			<hr class="dark:border-gray-700" />

			<!-- 模型配置 -->
			<div>
				<div class="mb-3 text-sm font-medium">模型配置</div>

				<div class="mb-4 p-3 border dark:border-gray-700 rounded-lg">
					<div class="mb-2 text-sm font-medium">文生图模型</div>
					<input
						bind:value={dreamWorkConfig.textToImageModel}
						placeholder="doubao-seedream-3-0-t2i-250415"
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="mb-4 p-3 border dark:border-gray-700 rounded-lg">
					<div class="mb-2 text-sm font-medium">图生图模型</div>
					<input
						bind:value={dreamWorkConfig.imageToImageModel}
						placeholder="doubao-seededit-3-0-i2i-250628"
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>
			</div>

			<hr class="dark:border-gray-700" />

			<!-- 生成参数 -->
			<div>
				<div class="mb-3 text-sm font-medium">默认生成参数</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">默认图片尺寸</div>
					<select
						bind:value={dreamWorkConfig.defaultSize}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					>
						{#each sizeOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">默认引导尺度 (Guidance Scale)</div>
					<input
						type="number"
						bind:value={dreamWorkConfig.defaultGuidanceScale}
						min="1"
						max="20"
						step="0.5"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
					<div class="text-xs text-gray-500 mt-1">推荐值: 2.5-7.5，数值越高与提示词匹配度越高</div>
				</div>

				<div class="flex w-full justify-between">
					<div class="flex flex-col">
						<div class="text-sm font-medium">默认启用水印</div>
						<div class="text-xs text-gray-400">生成的图片是否包含水印</div>
					</div>
					<Switch bind:state={dreamWorkConfig.watermarkEnabled} />
				</div>
			</div>

			<hr class="dark:border-gray-700" />

			<!-- 积分和限制 -->
			<div>
				<div class="mb-3 text-sm font-medium">积分和限制设置</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">每次生成消耗积分</div>
					<input
						type="number"
						bind:value={dreamWorkConfig.creditsPerGeneration}
						min="1"
						max="100"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">最大并发任务数</div>
					<input
						type="number"
						bind:value={dreamWorkConfig.maxConcurrentTasks}
						min="1"
						max="20"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">任务超时时间 (秒)</div>
					<input
						type="number"
						bind:value={dreamWorkConfig.taskTimeout}
						min="60"
						max="1800"
						step="60"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>
			</div>

			<hr class="dark:border-gray-700" />

			<!-- 使用说明 -->
			<div>
				<div class="mb-2 text-sm font-medium">使用说明</div>
				<div class="text-xs text-gray-500 space-y-1">
					<div>• 文生图：根据文本描述生成图像</div>
					<div>• 图生图：基于输入图片和文本描述生成新图像</div>
					<div>• 引导尺度：控制生成图像与提示词的匹配程度</div>
					<div>• 种子值：用于控制生成结果的随机性，相同种子产生相似结果</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3">
		<button
			class="px-3 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 dark:bg-white dark:hover:bg-gray-100 dark:text-black text-white transition rounded-lg"
			on:click={saveDreamWorkConfigData}
			disabled={loading}
		>
			{loading ? '保存中...' : '保存配置'}
		</button>
	</div>
</div>
