<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import MJ API functions
	import { type MJConfig, getMJConfig, saveMJConfig, testMJConnection } from '$lib/apis/midjourney';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	// MJ 配置 - 使用 MJConfig 类型
	let mjConfig: MJConfig = {
		enabled: false,
		baseUrl: '',
		apiKey: '',
		modes: {
			turbo: {
				enabled: true,
				credits: 10
			},
			fast: {
				enabled: true,
				credits: 5
			},
			relax: {
				enabled: true,
				credits: 2
			}
		},
		defaultMode: 'fast',
		maxConcurrentTasks: 5,
		taskTimeout: 300000, // 5分钟
		imageProxy: 'relay', // relay, origin, proxy
		webhookUrl: '',
		webhookSecret: '',
		enableWebhook: false
	};

	onMount(async () => {
		await loadMJConfig();
	});

	const loadMJConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getMJConfig($user.token);
			if (config) {
				mjConfig = { ...mjConfig, ...config };
			}
		} catch (error) {
			console.error('Failed to load MJ config:', error);
			toast.error('加载 Midjourney 配置失败');
		} finally {
			loading = false;
		}
	};

	const saveMJConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveMJConfig($user.token, mjConfig);
			toast.success('Midjourney 配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save MJ config:', error);
			toast.error('保存 Midjourney 配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!mjConfig.baseUrl || !mjConfig.apiKey) {
			toast.error('请先配置 API URL 和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await testMJConnection($user.token);
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
			<div class=" mb-1 text-sm font-medium">Midjourney 图像生成配置</div>
			<div class="text-xs text-gray-400 dark:text-gray-500">
				配置 Midjourney API 接入和积分消耗设置
			</div>
		</div>

		<hr class="dark:border-gray-700" />

		<!-- 启用开关 -->
		<div class="flex w-full justify-between">
			<div class="flex flex-col">
				<div class="text-sm font-medium">启用 Midjourney</div>
				<div class="text-xs text-gray-400">启用 Midjourney 图像生成功能</div>
			</div>
			<Switch bind:state={mjConfig.enabled} />
		</div>

		{#if mjConfig.enabled}
			<!-- API 配置 -->
			<div>
				<div class="mb-2 text-sm font-medium">API 配置</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">API Base URL</div>
					<input
						bind:value={mjConfig.baseUrl}
						placeholder="https://your-mj-api.com"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">API Key</div>
					<SensitiveInput placeholder="sk-your-api-key" bind:value={mjConfig.apiKey} />
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

			<!-- 模式配置 -->
			<div>
				<div class="mb-3 text-sm font-medium">生成模式配置</div>

				{#each Object.entries(mjConfig.modes) as [mode, config]}
					<div class="mb-4 p-3 border dark:border-gray-700 rounded-lg">
						<div class="flex justify-between items-center mb-2">
							<div class="text-sm font-medium capitalize">{mode} 模式</div>
							<Switch bind:state={config.enabled} />
						</div>

						{#if config.enabled}
							<div class="flex items-center gap-3">
								<div class="text-xs text-gray-400">积分消耗:</div>
								<input
									type="number"
									bind:value={config.credits}
									min="1"
									max="100"
									class="w-20 rounded py-1 px-2 text-xs bg-gray-50 dark:bg-gray-800 border dark:border-gray-700 outline-none"
								/>
								<div class="text-xs text-gray-400">积分/次</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>

			<hr class="dark:border-gray-700" />

			<!-- 高级设置 -->
			<div>
				<div class="mb-3 text-sm font-medium">高级设置</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">默认生成模式</div>
					<select
						bind:value={mjConfig.defaultMode}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					>
						<option value="turbo">Turbo (最快)</option>
						<option value="fast">Fast (快速)</option>
						<option value="relax">Relax (经济)</option>
					</select>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">最大并发任务数</div>
					<input
						type="number"
						bind:value={mjConfig.maxConcurrentTasks}
						min="1"
						max="20"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">任务超时时间 (秒)</div>
					<input
						type="number"
						bind:value={mjConfig.taskTimeout}
						min="60"
						max="1800"
						step="60"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3">
		<button
			class="px-3 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 dark:bg-white dark:hover:bg-gray-100 dark:text-black text-white transition rounded-lg"
			on:click={saveMJConfigData}
			disabled={loading}
		>
			{loading ? '保存中...' : '保存配置'}
		</button>
	</div>
</div>
