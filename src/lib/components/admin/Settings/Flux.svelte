<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import Flux API functions
	import {
		type FluxConfig,
		getFluxConfig,
		saveFluxConfig,
		testFluxConnection
	} from '$lib/apis/flux';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	// Flux 配置
	let fluxConfig = {
		enabled: false,
		baseUrl: 'https://api.linkapi.org',
		apiKey: '',
		defaultModel: 'fal-ai/flux-1/schnell',
		creditsPerGeneration: 5,
		maxConcurrentTasks: 5,
		taskTimeout: 300000, // 5分钟
		// 各模型积分配置
		modelCredits: {
			'fal-ai/flux-1/schnell': 5,
			'fal-ai/flux-1/dev': 10,
			'fal-ai/flux-pro': 20,
			'fal-ai/flux-pro/kontext': 25,
			'fal-ai/flux-pro/kontext/multi': 30,
			'fal-ai/flux-pro/max': 35
		}
	};

	// 支持的Flux模型选项
	const modelOptions = [
		{ value: 'fal-ai/flux-1/schnell', label: 'FLUX.1 [Schnell] - 快速模型', category: 'basic' },
		{ value: 'fal-ai/flux-1/dev', label: 'FLUX.1 [Dev] - 标准模型', category: 'basic' },
		{ value: 'fal-ai/flux-1/dev/image-to-image', label: 'FLUX.1 [Dev] 图生图', category: 'basic' },
		{ value: 'fal-ai/flux-pro', label: 'FLUX.1 [Pro] - 专业模型', category: 'pro' },
		{ value: 'fal-ai/flux-pro/kontext', label: 'FLUX.1 Kontext [Pro]', category: 'pro' },
		{
			value: 'fal-ai/flux-pro/kontext/multi',
			label: 'FLUX.1 Kontext [Multi] - 多图编辑',
			category: 'pro'
		},
		{
			value: 'fal-ai/flux-pro/max',
			label: 'FLUX.1 Kontext [Max Multi] - 高级多图',
			category: 'pro'
		}
	];

	onMount(async () => {
		await loadFluxConfig();
	});

	const loadFluxConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getFluxConfig($user.token);
			if (config) {
				fluxConfig = { ...fluxConfig, ...config };
			}
		} catch (error) {
			console.error('Failed to load Flux config:', error);
			toast.error('加载Flux配置失败');
		} finally {
			loading = false;
		}
	};

	const saveFluxConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveFluxConfig($user.token, fluxConfig);
			toast.success('Flux配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save Flux config:', error);
			toast.error('保存Flux配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!fluxConfig.baseUrl || !fluxConfig.apiKey) {
			toast.error('请先配置 API URL 和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const result = await testFluxConnection($user.token, {
				baseUrl: fluxConfig.baseUrl,
				apiKey: fluxConfig.apiKey
			});

			if (result.success) {
				toast.success('Flux连接测试成功');
			} else {
				toast.error(`连接测试失败: ${result.error || '未知错误'}`);
			}
		} catch (error) {
			console.error('Failed to test Flux connection:', error);
			toast.error('连接测试失败');
		} finally {
			loading = false;
		}
	};

	// 更新模型积分
	const updateModelCredit = (modelId: string, credits: number) => {
		fluxConfig.modelCredits = {
			...fluxConfig.modelCredits,
			[modelId]: credits
		};
	};
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm">
	<div class="space-y-3 pr-1.5 overflow-y-scroll scrollbar-hidden h-full">
		<div>
			<div class=" mb-2 text-sm font-medium">Flux AI 图像生成服务</div>
			<div class="text-xs text-gray-400">配置 Flux AI 图像生成服务，支持多种模型和参数选项</div>
		</div>

		<hr class=" dark:border-gray-700" />

		<!-- 启用开关 -->
		<div class="space-y-3">
			<div class="flex justify-between items-center">
				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">启用 Flux AI</div>
						<Tooltip content="启用后用户可以使用Flux AI进行图像生成">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<div class="text-xs text-gray-500">开启Flux AI图像生成功能</div>
				</div>
				<Switch bind:state={fluxConfig.enabled} />
			</div>
		</div>

		<hr class=" dark:border-gray-700" />

		<!-- API配置 -->
		{#if fluxConfig.enabled}
			<div class="space-y-3">
				<div class="text-sm font-medium">API 配置</div>

				<!-- API URL -->
				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">API URL</div>
						<Tooltip content="Flux AI API 服务地址">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<input
						class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-600"
						placeholder="https://api.linkapi.org"
						bind:value={fluxConfig.baseUrl}
						required
					/>
				</div>

				<!-- API Key -->
				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">API Key</div>
						<Tooltip content="Flux AI API 密钥">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<SensitiveInput
						placeholder="输入你的 Flux API Key"
						bind:value={fluxConfig.apiKey}
						required
					/>
				</div>

				<!-- 连接测试按钮 -->
				<div class="flex justify-end">
					<button
						class="px-3 py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-200 transition duration-200 rounded-lg"
						on:click={testConnection}
						disabled={loading || !fluxConfig.baseUrl || !fluxConfig.apiKey}
					>
						{loading ? '测试中...' : '测试连接'}
					</button>
				</div>
			</div>

			<hr class=" dark:border-gray-700" />

			<!-- 默认模型 -->
			<div class="space-y-3">
				<div class="text-sm font-medium">默认模型配置</div>

				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">默认模型</div>
						<Tooltip content="用户首次使用时的默认模型">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<select
						class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-600"
						bind:value={fluxConfig.defaultModel}
					>
						{#each modelOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</div>
			</div>

			<hr class=" dark:border-gray-700" />

			<!-- 模型积分配置 -->
			<div class="space-y-3">
				<div class="text-sm font-medium">模型积分配置</div>
				<div class="text-xs text-gray-500 mb-3">设置每个模型生成一张图片消耗的积分数量</div>

				<!-- 基础模型 -->
				<div class="space-y-2">
					<div class="text-sm font-medium text-blue-600 dark:text-blue-400">基础模型</div>
					{#each modelOptions.filter((m) => m.category === 'basic') as model}
						<div
							class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
						>
							<div class="text-sm">{model.label}</div>
							<div class="flex items-center space-x-2">
								<input
									type="number"
									min="1"
									max="100"
									class="w-16 rounded-lg py-1 px-2 text-sm dark:text-gray-300 dark:bg-gray-700 outline-none border border-gray-200 dark:border-gray-600"
									value={fluxConfig.modelCredits[model.value] || 5}
									on:input={(e) => updateModelCredit(model.value, parseInt(e.target.value) || 5)}
								/>
								<span class="text-xs text-gray-500">积分</span>
							</div>
						</div>
					{/each}
				</div>

				<!-- 专业模型 -->
				<div class="space-y-2">
					<div class="text-sm font-medium text-purple-600 dark:text-purple-400">专业模型</div>
					{#each modelOptions.filter((m) => m.category === 'pro') as model}
						<div
							class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
						>
							<div class="text-sm">{model.label}</div>
							<div class="flex items-center space-x-2">
								<input
									type="number"
									min="1"
									max="100"
									class="w-16 rounded-lg py-1 px-2 text-sm dark:text-gray-300 dark:bg-gray-700 outline-none border border-gray-200 dark:border-gray-600"
									value={fluxConfig.modelCredits[model.value] || 20}
									on:input={(e) => updateModelCredit(model.value, parseInt(e.target.value) || 20)}
								/>
								<span class="text-xs text-gray-500">积分</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<hr class=" dark:border-gray-700" />

			<!-- 任务设置 -->
			<div class="space-y-3">
				<div class="text-sm font-medium">任务设置</div>

				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">最大并发任务</div>
						<Tooltip content="同时处理的最大任务数量">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<input
						type="number"
						min="1"
						max="20"
						class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-600"
						bind:value={fluxConfig.maxConcurrentTasks}
					/>
				</div>

				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">任务超时时间 (秒)</div>
						<Tooltip content="任务超时时间，超时后会标记为失败">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<input
						type="number"
						min="60"
						max="1800"
						class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-600"
						value={fluxConfig.taskTimeout / 1000}
						on:input={(e) => (fluxConfig.taskTimeout = parseInt(e.target.value) * 1000)}
					/>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-gray-50 transition rounded-lg"
			disabled={loading}
			on:click={saveFluxConfigData}
		>
			{loading ? '保存中...' : '保存配置'}
		</button>
	</div>
</div>
