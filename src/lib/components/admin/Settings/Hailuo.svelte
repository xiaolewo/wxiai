<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';
	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import { type HailuoConfig, getHailuoConfig, updateHailuoConfig } from '$lib/apis/hailuo';

	const dispatch = createEventDispatcher();
	let loading = false;

	let cfg: HailuoConfig = {
		enabled: false,
		base_url: 'https://api.minimaxi.com',
		api_key: '',
		default_model: 'MiniMax-Hailuo-02',
		default_duration: 6,
		default_resolution: '768P',
		prompt_optimizer: true,
		max_concurrent_tasks: 3,
		task_timeout_ms: 900000,
		query_interval_ms: 10000,
		model_credits_config: {
			first_last_multiplier: 1.3,
			'MiniMax-Hailuo-02': { '768P': { '6': 80, '10': 120 }, '1080P': { '6': 120 } }
		}
	};

	onMount(async () => {
		await load();
	});

	const load = async () => {
		if (!$user?.token) return;
		loading = true;
		try {
			const data = await getHailuoConfig($user.token);
			if (data)
				cfg = {
					...cfg,
					...data,
					model_credits_config: {
						...(cfg.model_credits_config || {}),
						...(data.model_credits_config || {})
					}
				} as any;
		} catch (e) {
			console.error(e);
			toast.error('加载海螺配置失败');
		} finally {
			loading = false;
		}
	};

	const save = async () => {
		if (!$user?.token) return;
		loading = true;
		try {
			const ok = await updateHailuoConfig($user.token, cfg);
			if (ok) {
				toast.success('海螺配置已保存');
				dispatch('save');
			} else toast.error('保存失败');
		} catch (e) {
			console.error(e);
			toast.error('保存失败');
		} finally {
			loading = false;
		}
	};
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={save}
>
	<div class="space-y-3 overflow-y-scroll scrollbar-hidden h-full">
		<div class="mb-2 flex w-full justify-between">
			<div class="flex items-center space-x-2">
				<div class="font-medium text-sm">🐚 海螺视频（MiniMax Hailuo）</div>
				<Tooltip content="MiniMax 海螺视频生成服务，支持文生/图生/首尾帧">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="currentColor"
						class="w-4 h-4"
						><path
							d="M12 2a10 10 0 100 20 10 10 0 000-20Zm.75 5a.75.75 0 00-1.5 0v5.25c0 .414.336.75.75.75H16a.75.75 0 000-1.5h-3.25V7Z"
						/></svg
					>
				</Tooltip>
			</div>
			<Switch bind:state={cfg.enabled} />
		</div>

		{#if cfg.enabled}
			<div class="space-y-3">
				<div class="text-xs font-medium text-gray-500">API 配置</div>
				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">API URL</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.base_url}
							placeholder="https://api.minimaxi.com"
						/>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">API 密钥</div>
						<SensitiveInput placeholder="Bearer token" bind:value={cfg.api_key} />
					</div>
				</div>
			</div>

			<div class="space-y-3">
				<div class="text-xs font-medium text-gray-500">默认参数</div>
				<div class="grid grid-cols-3 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">默认模型</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.default_model}
						/>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">默认分辨率</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.default_resolution}
						>
							<option value="768P">768P</option>
							<option value="1080P">1080P</option>
						</select>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">默认时长 (秒)</div>
						<input
							type="number"
							min="1"
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.default_duration}
						/>
					</div>
				</div>
				<div class="flex items-center space-x-3">
					<div class="text-xs text-gray-500">优化提示词</div>
					<Switch bind:state={cfg.prompt_optimizer} />
				</div>
			</div>

			<div class="space-y-3">
				<div class="text-xs font-medium text-gray-500">系统参数</div>
				<div class="grid grid-cols-3 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">最大并发</div>
						<input
							type="number"
							min="1"
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.max_concurrent_tasks}
						/>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">任务超时(ms)</div>
						<input
							type="number"
							min="1000"
							step="1000"
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.task_timeout_ms}
						/>
					</div>
					<div>
						<div class="mb-1 text-xs text-gray-500">查询间隔(ms)</div>
						<input
							type="number"
							min="1000"
							step="1000"
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={cfg.query_interval_ms}
						/>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end gap-2">
		<button
			type="submit"
			class="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg"
			disabled={loading}
		>
			{loading ? '保存中...' : '保存设置'}
		</button>
	</div>
</form>
