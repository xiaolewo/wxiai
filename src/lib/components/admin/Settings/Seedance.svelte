<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import {
		getSeedanceConfig,
		saveSeedanceConfig,
		testSeedanceConnection,
		type SeedanceConfig
	} from '$lib/apis/seedance';

	const dispatch = createEventDispatcher();

	let loading = false;
	let testing = false;

	const modelOptions = [
		{ value: 'doubao-seedance-1-0-pro-250528', label: 'Seedance 1.0 Pro（文/图生）' },
		{ value: 'doubao-seedance-1-0-lite-t2v-250428', label: 'Seedance 1.0 Lite 文生' },
		{ value: 'doubao-seedance-1-0-lite-i2v-250428', label: 'Seedance 1.0 Lite 图生' }
	];

	const resolutionOptions = [
		{ value: '480p', label: '480p' },
		{ value: '720p', label: '720p' },
		{ value: '1080p', label: '1080p' }
	];

	const ratioOptions = [
		'21:9',
		'16:9',
		'4:3',
		'1:1',
		'3:4',
		'9:16',
		'9:21',
		'keep_ratio',
		'adaptive'
	];

	let cfg: SeedanceConfig = {
		enabled: false,
		baseUrl: 'https://ark.cn-beijing.volces.com',
		apiKey: '',
		defaultModel: 'doubao-seedance-1-0-pro-250528',
		defaultDuration: '5',
		defaultResolution: '720p',
		defaultRatio: '16:9',
		defaultWatermark: false,
		defaultCameraFixed: false,
		defaultReturnLastFrame: false,
		creditsPer5s: 40,
		creditsPer10s: 80,
		queryInterval: 10000,
		maxConcurrentTasks: 5,
		taskTimeout: 600000,
		modelCreditsConfig: {}
	};

	onMount(async () => {
		await load();
	});

	const load = async () => {
		if (!$user?.token) return;
		loading = true;
		try {
			const data = await getSeedanceConfig($user.token);
			if (data) {
				cfg = {
					...cfg,
					...data,
					creditsPer5s: Number(data.creditsPer5s ?? cfg.creditsPer5s),
					creditsPer10s: Number(data.creditsPer10s ?? cfg.creditsPer10s),
					queryInterval: Number(data.queryInterval ?? cfg.queryInterval),
					maxConcurrentTasks: Number(data.maxConcurrentTasks ?? cfg.maxConcurrentTasks),
					taskTimeout: Number(data.taskTimeout ?? cfg.taskTimeout)
				};
			}
		} catch (error) {
			console.error(error);
			toast.error('加载 Seedance 配置失败');
		} finally {
			loading = false;
		}
	};

	const buildPayload = () => ({
		enabled: cfg.enabled,
		base_url: cfg.baseUrl?.trim() || 'https://ark.cn-beijing.volces.com',
		api_key: cfg.apiKey?.trim() ?? '',
		default_model: cfg.defaultModel,
		default_duration: cfg.defaultDuration || '5',
		default_resolution: cfg.defaultResolution,
		default_ratio: cfg.defaultRatio,
		default_watermark: cfg.defaultWatermark,
		default_camera_fixed: cfg.defaultCameraFixed,
		default_return_last_frame: cfg.defaultReturnLastFrame,
		credits_per_5s: Number(cfg.creditsPer5s) || 0,
		credits_per_10s: Number(cfg.creditsPer10s) || 0,
		max_concurrent_tasks: Number(cfg.maxConcurrentTasks) || 5,
		task_timeout: Number(cfg.taskTimeout) || 600000,
		query_interval: Number(cfg.queryInterval) || 10000,
		model_credits_config: cfg.modelCreditsConfig ?? {}
	});

	const save = async () => {
		if (!$user?.token) return;
		loading = true;
		try {
			await saveSeedanceConfig($user.token, buildPayload());
			toast.success('Seedance 配置已保存');
			dispatch('save');
		} catch (error) {
			console.error(error);
			toast.error(error instanceof Error ? error.message : '保存 Seedance 配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!$user?.token) return;
		if (!cfg.enabled) {
			toast.error('请先启用 Seedance 服务后再测试连通性');
			return;
		}
		testing = true;
		try {
			const result = await testSeedanceConnection($user.token);
			toast.success(result?.message || '连接测试成功');
		} catch (error) {
			console.error(error);
			toast.error(error instanceof Error ? error.message : '连接测试失败');
		} finally {
			testing = false;
		}
	};
</script>

<form
	class="flex h-full flex-col justify-between space-y-3 text-sm"
	on:submit|preventDefault={save}
>
	<div class="space-y-4 overflow-y-auto scrollbar-hidden">
		<div class="flex items-start justify-between gap-4">
			<div class="space-y-1">
				<div class="flex items-center gap-2 text-sm font-medium">
					<span>🎞️ Seedance 新即梦视频服务</span>
					<Tooltip content="Seedance 新即梦视频生成，支持文生与首帧/首尾帧图生流程">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 24 24"
							fill="currentColor"
							class="h-4 w-4"
						>
							<path
								d="M12 2a10 10 0 100 20 10 10 0 000-20Zm-.75 5a.75.75 0 011.5 0v4.69l2.28 2.28a.75.75 0 01-1.06 1.06l-2.5-2.5A.75.75 0 0111.25 12V7Z"
							/>
						</svg>
					</Tooltip>
				</div>
				<p class="text-xs text-gray-500 dark:text-gray-400">
					配置 Seedance (新即梦) 文生 / 图生视频生成所需的 API 接入、默认参数与积分策略。
				</p>
			</div>
			<Switch bind:state={cfg.enabled} />
		</div>

		<div class="flex flex-wrap gap-2">
			<button
				type="button"
				class="rounded-lg border border-gray-200 px-3 py-1 text-xs hover:bg-gray-100 dark:border-gray-600 dark:hover:bg-gray-700"
				on:click={load}
				disabled={loading}
			>
				{loading ? '刷新中...' : '重新加载配置'}
			</button>
			<button
				type="button"
				class="rounded-lg border border-amber-200 px-3 py-1 text-xs text-amber-600 hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-amber-500/40 dark:text-amber-300 dark:hover:bg-amber-900/30"
				on:click={testConnection}
				disabled={testing || loading || !cfg.enabled}
			>
				{testing ? '测试中...' : '连通性测试'}
			</button>
		</div>

		<div class="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
			<div class="text-xs font-medium text-gray-500">API 配置</div>
			<div class="grid gap-3 md:grid-cols-2">
				<div>
					<div class="mb-1 text-xs text-gray-500">Base URL</div>
					<input
						class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
						placeholder="https://ark.cn-beijing.volces.com"
						bind:value={cfg.baseUrl}
					/>
				</div>
				<div>
					<div class="mb-1 text-xs text-gray-500">API Key</div>
					<SensitiveInput placeholder="Bearer xxx" bind:value={cfg.apiKey} />
				</div>
			</div>
		</div>

		{#if cfg.enabled}
			<div class="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
				<div class="text-xs font-medium text-gray-500">默认生成参数</div>
				<div class="grid gap-3 md:grid-cols-2">
					<div>
						<div class="mb-1 text-xs text-gray-500">默认模型</div>
						<select
							class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.defaultModel}
						>
							{#each modelOptions as opt}
								<option value={opt.value}>{opt.label}</option>
							{/each}
						</select>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">默认时长 (秒)</div>
						<select
							class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.defaultDuration}
						>
							<option value="5">5 秒</option>
							<option value="10">10 秒</option>
						</select>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">默认分辨率</div>
						<select
							class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.defaultResolution}
						>
							{#each resolutionOptions as opt}
								<option value={opt.value}>{opt.label}</option>
							{/each}
						</select>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">默认画面比例</div>
						<select
							class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.defaultRatio}
						>
							{#each ratioOptions as ratio}
								<option value={ratio}>{ratio}</option>
							{/each}
						</select>
					</div>
				</div>

				<div class="grid gap-3 md:grid-cols-3">
					<label
						class="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2 text-xs dark:border-gray-700"
					>
						<span>生成结果添加水印</span>
						<Switch bind:state={cfg.defaultWatermark} />
					</label>
					<label
						class="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2 text-xs dark:border-gray-700"
					>
						<span>固定摄像头 (camera_fixed)</span>
						<Switch bind:state={cfg.defaultCameraFixed} />
					</label>
					<label
						class="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2 text-xs dark:border-gray-700"
					>
						<span>返回尾帧 (return_last_frame)</span>
						<Switch bind:state={cfg.defaultReturnLastFrame} />
					</label>
				</div>
			</div>

			<div class="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
				<div class="text-xs font-medium text-gray-500">积分与轮询设置</div>
				<div class="grid gap-3 md:grid-cols-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">5 秒视频积分</div>
						<input
							type="number"
							min="0"
							class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.creditsPer5s}
						/>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">10 秒视频积分</div>
						<input
							type="number"
							min="0"
							class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.creditsPer10s}
						/>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">轮询间隔 (ms)</div>
						<input
							type="number"
							min="1000"
							step="1000"
							class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.queryInterval}
						/>
					</div>
				</div>

				<div class="grid gap-3 md:grid-cols-2">
					<div>
						<div class="mb-1 text-xs text-gray-500">最大并发任务数</div>
						<input
							type="number"
							min="1"
							class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.maxConcurrentTasks}
						/>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">任务超时 (ms)</div>
						<input
							type="number"
							min="60000"
							step="1000"
							class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.taskTimeout}
						/>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end gap-2">
		<button
			type="submit"
			class="rounded-lg bg-amber-500 px-4 py-1.5 text-xs text-white hover:bg-amber-600 disabled:cursor-not-allowed disabled:bg-gray-400"
			disabled={loading}
		>
			{loading ? '保存中...' : '保存设置'}
		</button>
	</div>
</form>
