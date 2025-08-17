<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import Kling API functions
	import {
		type KlingConfig,
		getKlingConfig,
		saveKlingConfig,
		testKlingConnection
	} from '$lib/apis/kling';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	// 可灵配置
	let klingConfig = {
		enabled: false,
		baseUrl: 'https://api.klingai.com',
		apiKey: '',
		textToVideoModel: 'kling-v1',
		imageToVideoModel: 'kling-v1',
		defaultMode: 'std',
		defaultDuration: '5',
		defaultAspectRatio: '16:9',
		defaultCfgScale: 0.5,
		modelCreditsConfig: {},
		maxConcurrentTasks: 3,
		taskTimeout: 600000 // 10分钟
	};

	// 支持的模型选项
	const modelOptions = [
		{ value: 'kling-v1', label: 'Kling V1' },
		{ value: 'kling-v1-6', label: 'Kling V1.6' },
		{ value: 'kling-v2-master', label: 'Kling V2 Master' },
		{ value: 'kling-v2-1-master', label: 'Kling V2.1 Master' }
	];

	// 视频模式选项
	const modeOptions = [
		{ value: 'std', label: '标准模式 (Standard)' },
		{ value: 'pro', label: '专家模式 (Pro)' }
	];

	// 视频时长选项
	const durationOptions = [
		{ value: '5', label: '5秒' },
		{ value: '10', label: '10秒' }
	];

	// 画面比例选项
	const aspectRatioOptions = [
		{ value: '16:9', label: '16:9 (横向)' },
		{ value: '9:16', label: '9:16 (竖向)' },
		{ value: '1:1', label: '1:1 (正方形)' }
	];

	onMount(async () => {
		await loadKlingConfig();
	});

	const loadKlingConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getKlingConfig($user.token);
			if (config) {
				klingConfig = { ...klingConfig, ...config };
			}
			// 初始化模型积分配置
			initializeModelCreditsConfig();
		} catch (error) {
			console.error('Failed to load Kling config:', error);
			toast.error('加载可灵配置失败');
		} finally {
			loading = false;
		}
	};

	const saveKlingConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveKlingConfig($user.token, klingConfig);
			toast.success('可灵配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save Kling config:', error);
			toast.error('保存可灵配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!klingConfig.baseUrl || !klingConfig.apiKey) {
			toast.error('请先配置 API URL 和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const result = await testKlingConnection($user.token);
			if (result.status === 'success') {
				toast.success('可灵连接测试成功');
			} else {
				toast.error(`连接测试失败: ${result.message}`);
			}
		} catch (error) {
			console.error('Connection test failed:', error);
			toast.error('连接测试失败');
		} finally {
			loading = false;
		}
	};

	// 确保模型配置结构存在
	const ensureModelConfig = (modelName: string) => {
		if (!klingConfig.modelCreditsConfig) {
			klingConfig.modelCreditsConfig = {};
		}

		if (!klingConfig.modelCreditsConfig[modelName]) {
			klingConfig.modelCreditsConfig[modelName] = {
				std: { '5': 50, '10': 100 },
				pro: { '5': 100, '10': 200 }
			};
		}

		if (!klingConfig.modelCreditsConfig[modelName].std) {
			klingConfig.modelCreditsConfig[modelName].std = { '5': 50, '10': 100 };
		}

		if (!klingConfig.modelCreditsConfig[modelName].pro) {
			klingConfig.modelCreditsConfig[modelName].pro = { '5': 100, '10': 200 };
		}

		// 确保具体的时长配置存在
		if (!klingConfig.modelCreditsConfig[modelName].std['5']) {
			klingConfig.modelCreditsConfig[modelName].std['5'] = 50;
		}
		if (!klingConfig.modelCreditsConfig[modelName].std['10']) {
			klingConfig.modelCreditsConfig[modelName].std['10'] = 100;
		}
		if (!klingConfig.modelCreditsConfig[modelName].pro['5']) {
			klingConfig.modelCreditsConfig[modelName].pro['5'] = 100;
		}
		if (!klingConfig.modelCreditsConfig[modelName].pro['10']) {
			klingConfig.modelCreditsConfig[modelName].pro['10'] = 200;
		}

		// 触发响应式更新
		klingConfig = { ...klingConfig };
	};

	// 初始化模型配置
	const initializeModelCreditsConfig = () => {
		if (!klingConfig.modelCreditsConfig) {
			klingConfig.modelCreditsConfig = {};
		}

		// 为每个模型初始化默认配置
		modelOptions.forEach((model) => {
			ensureModelConfig(model.value);
		});
	};
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={() => {
		saveKlingConfigData();
	}}
>
	<div class="space-y-3 overflow-y-scroll scrollbar-hidden h-full">
		<div>
			<div class="mb-2 flex w-full justify-between">
				<div class="flex items-center space-x-2">
					<div class="font-medium text-sm">🎬 可灵视频生成服务</div>
					<Tooltip content="可灵AI的视频生成服务，支持文生视频和图生视频">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="w-4 h-4"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
							/>
						</svg>
					</Tooltip>
				</div>
				<Switch bind:state={klingConfig.enabled} />
			</div>
		</div>

		{#if klingConfig.enabled}
			<!-- API 配置 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>API 配置</div>
				</div>

				<div>
					<div class="flex w-full">
						<div class="flex-1 mr-2">
							<div class="mb-1 text-xs text-gray-500">API URL</div>
							<div class="flex w-full">
								<div class="flex-1">
									<input
										class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
										placeholder="https://api.klingai.com"
										bind:value={klingConfig.baseUrl}
										autocomplete="off"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div>
					<div class="mb-1 text-xs text-gray-500">API 密钥</div>
					<SensitiveInput placeholder="sk-..." bind:value={klingConfig.apiKey} />
				</div>

				<div class="flex justify-end">
					<button
						class="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition"
						type="button"
						on:click={testConnection}
						disabled={loading || !klingConfig.baseUrl || !klingConfig.apiKey}
					>
						{loading ? '测试中...' : '测试连接'}
					</button>
				</div>
			</div>

			<!-- 模型配置 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>模型配置</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">文生视频模型</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={klingConfig.textToVideoModel}
						>
							{#each modelOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">图生视频模型</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={klingConfig.imageToVideoModel}
						>
							{#each modelOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
				</div>
			</div>

			<!-- 默认参数 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>默认参数</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">默认模式</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={klingConfig.defaultMode}
						>
							{#each modeOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">默认时长</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={klingConfig.defaultDuration}
						>
							{#each durationOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">默认画面比例</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={klingConfig.defaultAspectRatio}
						>
							{#each aspectRatioOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							CFG Scale
							<Tooltip content="生成自由度，值越大越符合提示词 (0-1)">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3 inline ml-1"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="0"
							max="1"
							step="0.1"
							bind:value={klingConfig.defaultCfgScale}
						/>
					</div>
				</div>
			</div>

			<!-- 模型版本积分配置 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>模型版本积分配置</div>
					<Tooltip content="为不同模型版本设置独立的积分消耗，支持差异化定价">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="w-4 h-4"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
							/>
						</svg>
					</Tooltip>
				</div>

				{#each modelOptions as model}
					<div class="p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
							{model.label}
						</div>

						<div class="grid grid-cols-2 gap-3">
							<!-- 标准模式 -->
							<div class="space-y-2">
								<div class="text-xs text-gray-500 font-medium">标准模式 (STD)</div>
								<div class="space-y-2">
									<div class="flex items-center gap-2">
										<span class="text-xs text-gray-400 w-8">5秒:</span>
										<input
											class="flex-1 rounded py-1 px-2 text-xs border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
											type="number"
											min="1"
											value={klingConfig.modelCreditsConfig[model.value]?.std?.['5'] || 50}
											on:input={(e) => {
												ensureModelConfig(model.value);
												klingConfig.modelCreditsConfig[model.value].std['5'] =
													parseInt(e.target.value) || 50;
											}}
										/>
									</div>
									<div class="flex items-center gap-2">
										<span class="text-xs text-gray-400 w-8">10秒:</span>
										<input
											class="flex-1 rounded py-1 px-2 text-xs border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
											type="number"
											min="1"
											value={klingConfig.modelCreditsConfig[model.value]?.std?.['10'] || 100}
											on:input={(e) => {
												ensureModelConfig(model.value);
												klingConfig.modelCreditsConfig[model.value].std['10'] =
													parseInt(e.target.value) || 100;
											}}
										/>
									</div>
								</div>
							</div>

							<!-- 专家模式 -->
							<div class="space-y-2">
								<div class="text-xs text-gray-500 font-medium">专家模式 (PRO)</div>
								<div class="space-y-2">
									<div class="flex items-center gap-2">
										<span class="text-xs text-gray-400 w-8">5秒:</span>
										<input
											class="flex-1 rounded py-1 px-2 text-xs border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
											type="number"
											min="1"
											value={klingConfig.modelCreditsConfig[model.value]?.pro?.['5'] || 100}
											on:input={(e) => {
												ensureModelConfig(model.value);
												klingConfig.modelCreditsConfig[model.value].pro['5'] =
													parseInt(e.target.value) || 100;
											}}
										/>
									</div>
									<div class="flex items-center gap-2">
										<span class="text-xs text-gray-400 w-8">10秒:</span>
										<input
											class="flex-1 rounded py-1 px-2 text-xs border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
											type="number"
											min="1"
											value={klingConfig.modelCreditsConfig[model.value]?.pro?.['10'] || 200}
											on:input={(e) => {
												ensureModelConfig(model.value);
												klingConfig.modelCreditsConfig[model.value].pro['10'] =
													parseInt(e.target.value) || 200;
											}}
										/>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/each}
			</div>

			<!-- 系统配置 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>系统配置</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">
							最大并发任务
							<Tooltip content="同时处理的最大视频生成任务数">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3 inline ml-1"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="1"
							max="10"
							bind:value={klingConfig.maxConcurrentTasks}
						/>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							任务超时时间 (秒)
							<Tooltip content="视频生成任务的最大等待时间">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3 inline ml-1"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="60"
							step="60"
							bind:value={klingConfig.taskTimeout}
						/>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3">
		<button
			class="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-gray-100 transition rounded-lg text-sm"
			type="submit"
			disabled={loading}
		>
			{loading ? '保存中...' : '保存'}
		</button>
	</div>
</form>
