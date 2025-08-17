<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import Jimeng API functions
	import {
		type JimengConfig,
		getJimengConfig,
		saveJimengConfig,
		testJimengConnection
	} from '$lib/apis/jimeng';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	// 即梦配置
	let jimengConfig = {
		enabled: false,
		baseUrl: 'https://ark.cn-beijing.volces.com',
		apiKey: '',
		defaultDuration: '5',
		defaultAspectRatio: '16:9',
		defaultCfgScale: 0.5,
		creditsPer5s: 30,
		creditsPer10s: 60,
		maxConcurrentTasks: 5,
		taskTimeout: 600000, // 10分钟
		queryInterval: 10000 // 10秒
	};

	// 视频时长选项
	const durationOptions = [
		{ value: '5', label: '5秒' },
		{ value: '10', label: '10秒' }
	];

	// 画面比例选项
	const aspectRatioOptions = [
		{ value: '1:1', label: '1:1 (正方形)' },
		{ value: '21:9', label: '21:9 (超宽屏)' },
		{ value: '16:9', label: '16:9 (横向)' },
		{ value: '9:16', label: '9:16 (竖向)' },
		{ value: '4:3', label: '4:3 (传统)' },
		{ value: '3:4', label: '3:4 (竖向传统)' }
	];

	onMount(async () => {
		await loadJimengConfig();
	});

	const loadJimengConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getJimengConfig($user.token);
			if (config) {
				jimengConfig = { ...jimengConfig, ...config };
			}
		} catch (error) {
			console.error('Failed to load Jimeng config:', error);
			toast.error('加载即梦配置失败');
		} finally {
			loading = false;
		}
	};

	const saveJimengConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveJimengConfig($user.token, jimengConfig);
			toast.success('即梦配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save Jimeng config:', error);
			toast.error('保存即梦配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!jimengConfig.baseUrl || !jimengConfig.apiKey) {
			toast.error('请先配置 API URL 和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const result = await testJimengConnection($user.token);
			if (result.status === 'success') {
				toast.success('即梦连接测试成功');
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

	// 计算积分消耗预览
	const getCreditsEstimate = (duration: string) => {
		if (duration === '5') return jimengConfig.creditsPer5s;
		if (duration === '10') return jimengConfig.creditsPer10s;
		return 0;
	};
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={() => {
		saveJimengConfigData();
	}}
>
	<div class="space-y-3 overflow-y-scroll scrollbar-hidden h-full">
		<div>
			<div class="mb-2 flex w-full justify-between">
				<div class="flex items-center space-x-2">
					<div class="font-medium text-sm">🌟 即梦视频生成服务</div>
					<Tooltip content="即梦AI的视频生成服务，支持文生视频和图生视频">
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
				<Switch bind:state={jimengConfig.enabled} />
			</div>
		</div>

		{#if jimengConfig.enabled}
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
										placeholder="https://ark.cn-beijing.volces.com"
										bind:value={jimengConfig.baseUrl}
										autocomplete="off"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div>
					<div class="mb-1 text-xs text-gray-500">API 密钥</div>
					<SensitiveInput placeholder="Bearer token..." bind:value={jimengConfig.apiKey} />
				</div>

				<div class="flex justify-end">
					<button
						class="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition"
						type="button"
						on:click={testConnection}
						disabled={loading || !jimengConfig.baseUrl || !jimengConfig.apiKey}
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
						<div class="mb-1 text-xs text-gray-500">默认时长</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={jimengConfig.defaultDuration}
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
							bind:value={jimengConfig.defaultAspectRatio}
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
							bind:value={jimengConfig.defaultCfgScale}
						/>
					</div>
				</div>
			</div>

			<!-- 积分配置 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>积分配置</div>
					<Tooltip content="不同时长的积分消耗设置">
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

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">5秒视频</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="1"
							bind:value={jimengConfig.creditsPer5s}
						/>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">10秒视频</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="1"
							bind:value={jimengConfig.creditsPer10s}
						/>
					</div>
				</div>

				<!-- 积分预览 -->
				<div class="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<div class="text-xs text-gray-500 mb-2">积分消耗预览:</div>
					<div class="grid grid-cols-2 gap-2 text-xs">
						<div>5秒视频: {getCreditsEstimate('5')} 积分</div>
						<div>10秒视频: {getCreditsEstimate('10')} 积分</div>
					</div>
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
							bind:value={jimengConfig.maxConcurrentTasks}
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
							bind:value={jimengConfig.taskTimeout}
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
							bind:value={jimengConfig.queryInterval}
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
