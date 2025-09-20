<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	import { type BananaConfig, getBananaConfig, saveBananaConfig } from '$lib/apis/banana';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let saving = false;

	const modelOptions = [
		{ value: 'nano-banana', label: 'Nano Banana（标准）' },
		{ value: 'nano-banana-hd', label: 'Nano Banana HD（4K）' }
	];

	const aspectRatioOptions = ['1:1', '3:4', '4:3', '16:9', '9:16', '2:3', '3:2', '21:9'];
	const outputFormatOptions = [
		{ value: 'url', label: 'URL（返回可访问链接）' },
		{ value: 'b64_json', label: 'Base64 JSON' }
	];

	let configState: BananaConfig = {
		enabled: false,
		baseUrl: '',
		apiKey: '',
		defaultModel: 'nano-banana',
		defaultOutputFormat: 'url',
		defaultAspectRatio: '1:1',
		creditsPerGeneration: 10,
		creditsPerEdit: 10,
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
			const fetched = await getBananaConfig($user.token);
			if (fetched) {
				configState = { ...configState, ...fetched };
			}
		} catch (error) {
			console.error('Failed to load Banana config:', error);
			toast.error('加载 Banana 配置失败');
		} finally {
			loading = false;
		}
	};

	const saveConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		if (configState.enabled) {
			if (!configState.baseUrl) {
				toast.error('请填写 API 地址');
				return;
			}
			if (!configState.apiKey) {
				toast.error('请填写 API 密钥');
				return;
			}
		}

		saving = true;
		try {
			await saveBananaConfig($user.token, configState);
			toast.success('Banana 配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save Banana config:', error);
			toast.error('保存配置失败');
		} finally {
			saving = false;
		}
	};
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm">
	<div class="space-y-3 pr-1.5 overflow-y-auto scrollbar-hidden h-full">
		<div>
			<div class="mb-2 text-sm font-medium">Banana 图像生成服务</div>
			<div class="text-xs text-gray-500">
				配置 Banana Nano 系列图像生成模型，支持文生图与图生图（多参考图）
			</div>
		</div>

		<hr class="dark:border-gray-700" />

		<div class="space-y-3">
			<div class="flex justify-between items-center">
				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">启用 Banana 服务</div>
					</div>
					<div class="text-xs text-gray-500">开启后用户可在图像生成页选择 Banana 模型</div>
				</div>
				<Switch bind:state={configState.enabled} />
			</div>
		</div>

		{#if loading}
			<div class="flex items-center gap-2 text-sm text-gray-500">
				<Spinner className="size-4" />
				正在加载配置...
			</div>
		{:else if configState.enabled}
			<div class="space-y-3">
				<div>
					<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
						>API 地址</label
					>
					<input
						bind:value={configState.baseUrl}
						type="text"
						placeholder="例如：https://api.linkapi.org"
						class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
					/>
				</div>

				<div>
					<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
						>API 密钥</label
					>
					<SensitiveInput
						bind:value={configState.apiKey}
						placeholder="填写 Banana 提供的 API Key"
					/>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>默认模型</label
						>
						<select
							bind:value={configState.defaultModel}
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
						>
							{#each modelOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>默认输出格式</label
						>
						<select
							bind:value={configState.defaultOutputFormat}
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
						>
							{#each outputFormatOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>默认图片比例</label
						>
						<select
							bind:value={configState.defaultAspectRatio}
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
						>
							{#each aspectRatioOptions as ratio}
								<option value={ratio}>{ratio}</option>
							{/each}
						</select>
					</div>
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>文生图积分</label
						>
						<input
							bind:value={configState.creditsPerGeneration}
							type="number"
							min="0"
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
						/>
					</div>
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>图生图积分</label
						>
						<input
							bind:value={configState.creditsPerEdit}
							type="number"
							min="0"
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
						/>
					</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>最大并发任务</label
						>
						<input
							bind:value={configState.maxConcurrentTasks}
							type="number"
							min="1"
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
						/>
					</div>
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>任务超时（毫秒）</label
						>
						<input
							bind:value={configState.taskTimeout}
							type="number"
							min="60000"
							step="1000"
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
						/>
						<div class="text-xs text-gray-500 mt-1">默认 300000 ms（5 分钟）</div>
					</div>
				</div>
			</div>
		{:else}
			<div
				class="p-4 bg-gray-50 dark:bg-gray-900/40 rounded text-xs text-gray-500 dark:text-gray-400"
			>
				服务未启用。启用后可配置 API 信息、默认模型及积分策略。
			</div>
		{/if}
	</div>

	<div class="flex justify-end gap-2">
		<button
			class="px-4 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
			on:click={loadConfig}
			disabled={loading || saving}
		>
			刷新
		</button>
		<button
			on:click={saveConfig}
			disabled={saving || loading}
			class="px-4 py-2 text-sm rounded bg-blue-500 hover:bg-blue-600 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
		>
			{saving ? '保存中…' : $i18n.t('Save')}
		</button>
	</div>
</div>
