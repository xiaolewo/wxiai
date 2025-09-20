<script lang="ts">
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';

	import {
		type Jimeng4Config,
		getJimeng4Config,
		saveJimeng4Config,
		testJimeng4Connection
	} from '$lib/apis/jimeng4';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	let jimeng4Config: Jimeng4Config = {
		enabled: false,
		baseUrl: '',
		apiKey: '',
		defaultModel: 'doubao-seedream-4-0-250828',
		defaultSize: '2K',
		defaultWatermark: true,
		defaultSequentialMode: 'auto',
		defaultN: 1,
		creditsPerImage: 30,
		maxConcurrentTasks: 5,
		taskTimeout: 300000
	};

	onMount(async () => {
		await loadConfig();
	});

	const loadConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getJimeng4Config($user.token);
			if (config) {
				jimeng4Config = { ...jimeng4Config, ...config };
			}
		} catch (error) {
			console.error('Failed to load Jimeng4 config:', error);
			toast.error('加载即梦4配置失败');
		} finally {
			loading = false;
		}
	};

	const saveConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveJimeng4Config($user.token, jimeng4Config);
			toast.success('即梦4配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save Jimeng4 config:', error);
			toast.error('保存即梦4配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!jimeng4Config.baseUrl || !jimeng4Config.apiKey) {
			toast.error('请先配置 API 地址和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await testJimeng4Connection($user.token);
			toast.success('连接测试成功');
		} catch (error) {
			console.error('Jimeng4 connection test failed:', error);
			toast.error('连接测试失败');
		} finally {
			loading = false;
		}
	};
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class="space-y-3 pr-1.5">
		<div>
			<div class="mb-1 text-sm font-medium">即梦4 (Seedream v4) 图像生成配置</div>
			<div class="text-xs text-gray-400 dark:text-gray-500">
				配置即梦4图像 API，支持多图参考、连续生成等高级特性
			</div>
		</div>

		<hr class="dark:border-gray-700" />

		<div class="flex w-full justify-between">
			<div class="flex flex-col">
				<div class="text-sm font-medium">启用即梦4</div>
				<div class="text-xs text-gray-400">开启 Seedream v4 图像服务</div>
			</div>
			<Switch bind:state={jimeng4Config.enabled} />
		</div>

		{#if jimeng4Config.enabled}
			<div>
				<div class="mb-2 text-sm font-medium">API 配置</div>
				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">API Base URL</div>
					<input
						bind:value={jimeng4Config.baseUrl}
						placeholder="https://ark.cn-beijing.volces.com"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>
				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">API Key</div>
					<SensitiveInput placeholder="your-seedream4-api-key" bind:value={jimeng4Config.apiKey} />
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

			<div class="grid grid-cols-2 gap-3">
				<div>
					<div class="text-xs text-gray-400 mb-1">默认模型</div>
					<input
						bind:value={jimeng4Config.defaultModel}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>
				<div>
					<div class="text-xs text-gray-400 mb-1">默认尺寸</div>
					<select
						bind:value={jimeng4Config.defaultSize}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					>
						<option value="1K">1K</option>
						<option value="2K">2K</option>
						<option value="4K">4K</option>
						<option value="custom">自定义</option>
					</select>
				</div>
				<div>
					<div class="text-xs text-gray-400 mb-1">连续生成模式</div>
					<select
						bind:value={jimeng4Config.defaultSequentialMode}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					>
						<option value="auto">自动</option>
						<option value="fast">快速</option>
						<option value="balanced">均衡</option>
					</select>
				</div>
				<div>
					<div class="text-xs text-gray-400 mb-1">默认生成张数</div>
					<input
						type="number"
						min="1"
						max="10"
						bind:value={jimeng4Config.defaultN}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>
			</div>

			<hr class="dark:border-gray-700" />

			<div class="grid grid-cols-2 gap-3">
				<div>
					<div class="text-xs text-gray-400 mb-1">单张图片积分</div>
					<input
						type="number"
						min="1"
						bind:value={jimeng4Config.creditsPerImage}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>
				<div>
					<div class="text-xs text-gray-400 mb-1">最大并发任务</div>
					<input
						type="number"
						min="1"
						bind:value={jimeng4Config.maxConcurrentTasks}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>
				<div>
					<div class="text-xs text-gray-400 mb-1">任务超时（毫秒）</div>
					<input
						type="number"
						min="60000"
						step="60000"
						bind:value={jimeng4Config.taskTimeout}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
					<div class="text-xs text-gray-500 mt-1">默认5分钟，单位毫秒</div>
				</div>
				<div class="flex items-center gap-2 mt-6">
					<input
						type="checkbox"
						bind:checked={jimeng4Config.defaultWatermark}
						class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
					/>
					<span class="text-sm text-gray-600 dark:text-gray-300">默认启用水印</span>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end mt-4 gap-2">
		<button
			class="px-3 py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-lg"
			on:click={loadConfig}
			disabled={loading}
		>
			重新加载
		</button>
		<button
			class="px-4 py-1.5 text-xs font-medium bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition"
			on:click={saveConfig}
			disabled={loading}
		>
			{loading ? '保存中...' : $i18n.t('Save')}
		</button>
	</div>
</div>
