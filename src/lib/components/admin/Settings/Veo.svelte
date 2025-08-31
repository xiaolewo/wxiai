<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import Veo API functions
	import {
		type VeoConfig,
		getVeoConfig,
		updateVeoConfig,
		getVeoHealth
	} from '$lib/apis/veo';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	// Veo配置
	let veoConfig = {
		enabled: false,
		base_url: 'https://api.veoai.com',
		api_key: '',
		model_credits_config: {
			'veo3': 100,
			'veo3-fast': 80,
			'veo3-pro': 150,
			'veo3-pro-frames': 200,
			'veo2': 90,
			'veo2-fast': 70,
			'veo2-fast-frames': 120,
			'veo2-fast-components': 160,
			'veo2-pro': 140,
			'veo3-fast-frames': 90
		},
		default_model: 'veo3',
		default_enhance_prompt: true,
		max_concurrent_tasks: 3,
		task_timeout: 900000, // 15分钟
		query_interval: 15000 // 15秒
	};

	// 模型选项
	const modelOptions = [
		{ value: 'veo3', label: 'Veo 3 (最新)', type: 'text' },
		{ value: 'veo3-fast', label: 'Veo 3 Fast', type: 'text' },
		{ value: 'veo3-pro', label: 'Veo 3 Pro', type: 'text' },
		{ value: 'veo3-pro-frames', label: 'Veo 3 Pro Frames', type: 'image' },
		{ value: 'veo2', label: 'Veo 2', type: 'text' },
		{ value: 'veo2-fast', label: 'Veo 2 Fast', type: 'text' },
		{ value: 'veo2-fast-frames', label: 'Veo 2 Fast Frames', type: 'image' },
		{ value: 'veo2-fast-components', label: 'Veo 2 Fast Components', type: 'image' },
		{ value: 'veo2-pro', label: 'Veo 2 Pro', type: 'text' },
		{ value: 'veo3-fast-frames', label: 'Veo 3 Fast Frames', type: 'image' }
	];

	onMount(async () => {
		await loadVeoConfig();
	});

	const loadVeoConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getVeoConfig($user.token);
			if (config) {
				// 保持完整的模型列表，只更新已存在的配置
				veoConfig = { 
					...veoConfig, 
					...config, 
					model_credits_config: { 
						...veoConfig.model_credits_config, 
						...(config.model_credits_config || {}) 
					} 
				};
			}
		} catch (error) {
			console.error('Failed to load Veo config:', error);
			toast.error('加载Veo配置失败');
		} finally {
			loading = false;
		}
	};

	const saveVeoConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const success = await updateVeoConfig($user.token, veoConfig);
			if (success) {
				toast.success('Veo配置已保存');
				dispatch('save');
			} else {
				toast.error('保存Veo配置失败');
			}
		} catch (error) {
			console.error('Failed to save Veo config:', error);
			toast.error('保存Veo配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!veoConfig.base_url || !veoConfig.api_key) {
			toast.error('请先配置 API URL 和密钥');
			return;
		}

		loading = true;
		try {
			const result = await getVeoHealth();
			if (result && result.enabled) {
				toast.success('Veo连接测试成功');
			} else {
				toast.error(`连接测试失败: ${result?.status || '服务不可用'}`);
			}
		} catch (error) {
			console.error('Connection test failed:', error);
			toast.error('连接测试失败');
		} finally {
			loading = false;
		}
	};

	// 获取模型类型标识
	const getModelTypeBadge = (modelValue: string) => {
		const model = modelOptions.find(opt => opt.value === modelValue);
		if (model?.type === 'image') {
			return '图';
		}
		return '文';
	};
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={() => {
		saveVeoConfigData();
	}}
>
	<div class="space-y-3 overflow-y-scroll scrollbar-hidden h-full">
		<div>
			<div class="mb-2 flex w-full justify-between">
				<div class="flex items-center space-x-2">
					<div class="font-medium text-sm">🎯 Veo AI视频生成服务</div>
					<Tooltip content="Google Veo AI的视频生成服务，支持文生视频和图生视频">
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
				<Switch bind:state={veoConfig.enabled} />
			</div>
		</div>

		{#if veoConfig.enabled}
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
										placeholder="https://api.veoai.com"
										bind:value={veoConfig.base_url}
										autocomplete="off"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div>
					<div class="mb-1 text-xs text-gray-500">API 密钥</div>
					<SensitiveInput placeholder="Bearer token..." bind:value={veoConfig.api_key} />
				</div>

				<div class="flex justify-end">
					<button
						class="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition"
						type="button"
						on:click={testConnection}
						disabled={loading || !veoConfig.base_url || !veoConfig.api_key}
					>
						{loading ? '测试中...' : '测试连接'}
					</button>
				</div>
			</div>

			<!-- 默认参数 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>默认参数</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">默认模型</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={veoConfig.default_model}
						>
							{#each modelOptions as option}
								<option value={option.value}>
									{option.label} [{getModelTypeBadge(option.value)}]
								</option>
							{/each}
						</select>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							默认优化提示词
							<Tooltip content="是否默认启用AI提示词优化">
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
						<Switch bind:state={veoConfig.default_enhance_prompt} />
					</div>
				</div>
			</div>

			<!-- 模型积分配置 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>模型积分配置</div>
				</div>

				<div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
					{#each Object.entries(veoConfig.model_credits_config) as [modelName, credits]}
						<div class="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
							<div class="flex-1">
								<div class="text-xs text-gray-500 mb-1">
									{modelName}
									<span class="ml-2 px-1 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded text-xs">
										{getModelTypeBadge(modelName)}
									</span>
								</div>
								<input
									class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-700"
									type="number"
									min="1"
									bind:value={veoConfig.model_credits_config[modelName]}
								/>
							</div>
						</div>
					{/each}
				</div>
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
							bind:value={veoConfig.max_concurrent_tasks}
						/>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							任务超时时间 (毫秒)
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
							min="60000"
							step="60000"
							bind:value={veoConfig.task_timeout}
						/>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							查询间隔 (毫秒)
							<Tooltip content="轮询任务状态的时间间隔">
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
							min="5000"
							step="1000"
							bind:value={veoConfig.query_interval}
						/>
					</div>
				</div>
			</div>

			<!-- 使用说明 -->
			<div class="space-y-2">
				<div class="text-xs font-medium text-gray-500">使用说明</div>
				<div class="text-xs text-gray-600 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg space-y-1">
					<div>• 支持多种Veo模型：文生视频、图生视频等</div>
					<div>• 带有"frames"或"components"的模型支持图片输入</div>
					<div>• 可以自定义每个模型的积分消耗</div>
					<div>• 建议查询间隔不少于15秒，避免API限制</div>
					<div>• 任务超时建议设置为15分钟(900000毫秒)或更长</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3">
		<button
			class="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-gray-100 transition rounded-lg text-sm"
			type="submit"
			disabled={loading}
		>
			{loading ? '保存中...' : '保存'}
		</button>
	</div>
</form>