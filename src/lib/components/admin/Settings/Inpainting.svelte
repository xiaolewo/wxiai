<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import API wrapper functions
	import {
		getInpaintingConfig,
		saveInpaintingConfig,
		testInpaintingConnection
	} from '$lib/apis/inpainting';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let testing = false;

	// 即梦涂抹消除配置
	let inpaintingConfig = {
		enabled: false,
		baseUrl: 'https://api.linkapi.org',
		apiKey: '',
		creditsPerTask: 50,
		maxConcurrentTasks: 3,
		taskTimeout: 300000, // 5分钟
		defaultSteps: 30,
		defaultStrength: 0.8,
		defaultScale: 7.0,
		defaultQuality: 'M',
		defaultDilateSize: 15
	};

	// 质量选项
	const qualityOptions = [
		{ value: 'L', label: '低质量 (快速)' },
		{ value: 'M', label: '中质量' },
		{ value: 'H', label: '高质量 (慢速)' }
	];

	onMount(async () => {
		await loadConfig();
	});

	const loadConfig = async () => {
		try {
			loading = true;
			inpaintingConfig = await getInpaintingConfig(localStorage.getItem('token'));
			console.log('🎨 【即梦涂抹消除管理员】配置已加载:', inpaintingConfig);
		} catch (error) {
			console.error('Load config error:', error);
			toast.error('加载配置失败');
		} finally {
			loading = false;
		}
	};

	const saveConfig = async () => {
		try {
			loading = true;
			const result = await saveInpaintingConfig(localStorage.getItem('token'), inpaintingConfig);
			if (result) {
				toast.success('配置保存成功');
				console.log('🎨 【即梦涂抹消除管理员】配置保存成功:', result);
			}
		} catch (error) {
			console.error('Save config error:', error);
			toast.error('保存配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!inpaintingConfig.apiKey.trim()) {
			toast.error('请先填写API密钥');
			return;
		}

		try {
			testing = true;
			const result = await testInpaintingConnection(localStorage.getItem('token'));
			console.log('测试连接结果:', result);
			if (result.success) {
				toast.success('连接测试成功');
			} else {
				toast.error(result.message || '连接测试失败');
			}
		} catch (error) {
			console.error('Test connection error:', error);
			toast.error('连接测试失败');
		} finally {
			testing = false;
		}
	};
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={saveConfig}
>
	<div class=" space-y-3">
		<div>
			<div class=" mb-1 text-sm font-medium">即梦涂抹消除</div>
			<div class="text-xs text-gray-400">配置即梦AI涂抹消除功能，智能去除图片中不需要的对象</div>
		</div>

		<hr class=" border-gray-700" />

		<!-- 启用开关 -->
		<div>
			<div class=" py-0.5 flex w-full justify-between">
				<div class=" self-center text-xs font-medium">启用涂抹消除</div>
				<Switch bind:state={inpaintingConfig.enabled} />
			</div>
		</div>

		{#if inpaintingConfig.enabled}
			<!-- API配置 -->
			<div class="space-y-3">
				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium">API基础URL</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="https://api.linkapi.org"
								bind:value={inpaintingConfig.baseUrl}
								required
							/>
						</div>
					</div>
				</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium">API密钥</div>
						<button
							type="button"
							class="text-xs font-medium text-blue-600 hover:text-blue-500"
							on:click={testConnection}
							disabled={testing || !inpaintingConfig.apiKey.trim()}
						>
							{#if testing}
								测试中...
							{:else}
								测试连接
							{/if}
						</button>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<SensitiveInput
								placeholder="请输入即梦API密钥"
								bind:value={inpaintingConfig.apiKey}
								required
							/>
						</div>
					</div>
				</div>
			</div>

			<hr class=" border-gray-700" />

			<!-- 积分配置 -->
			<div>
				<div class="flex w-full justify-between mb-2">
					<div class="self-center text-xs font-medium flex items-center space-x-1">
						<span>每个任务消耗积分</span>
						<Tooltip content="每次涂抹消除任务消耗的积分数量">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="w-3 h-3"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
								/>
							</svg>
						</Tooltip>
					</div>
				</div>
				<div class="flex w-full">
					<div class="flex-1">
						<input
							class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
							placeholder="50"
							type="number"
							min="1"
							max="1000"
							bind:value={inpaintingConfig.creditsPerTask}
							required
						/>
					</div>
				</div>
			</div>

			<hr class=" border-gray-700" />

			<!-- 默认参数配置 -->
			<div class="space-y-3">
				<div class="text-xs font-medium text-gray-600 dark:text-gray-400">默认参数配置</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium flex items-center space-x-1">
							<span>采样步数</span>
							<Tooltip content="生成图像的采样步数，越高质量越好但速度越慢">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
									/>
								</svg>
							</Tooltip>
						</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="30"
								type="number"
								min="10"
								max="50"
								bind:value={inpaintingConfig.defaultSteps}
								required
							/>
						</div>
					</div>
				</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium flex items-center space-x-1">
							<span>强度</span>
							<Tooltip content="涂抹强度，0.1-1.0之间，值越高修改越明显">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
									/>
								</svg>
							</Tooltip>
						</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="0.8"
								type="number"
								min="0.1"
								max="1.0"
								step="0.1"
								bind:value={inpaintingConfig.defaultStrength}
								required
							/>
						</div>
					</div>
				</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium flex items-center space-x-1">
							<span>文本描述程度</span>
							<Tooltip content="文本描述的影响程度，1-20之间">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
									/>
								</svg>
							</Tooltip>
						</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="7.0"
								type="number"
								min="1"
								max="20"
								step="0.5"
								bind:value={inpaintingConfig.defaultScale}
								required
							/>
						</div>
					</div>
				</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium">默认质量</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<select
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								bind:value={inpaintingConfig.defaultQuality}
							>
								{#each qualityOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium flex items-center space-x-1">
							<span>Mask膨胀半径</span>
							<Tooltip content="涂抹区域膨胀的像素半径，用于扩大处理范围">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
									/>
								</svg>
							</Tooltip>
						</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="15"
								type="number"
								min="0"
								max="50"
								bind:value={inpaintingConfig.defaultDilateSize}
								required
							/>
						</div>
					</div>
				</div>
			</div>

			<hr class=" border-gray-700" />

			<!-- 高级配置 -->
			<div class="space-y-3">
				<div class="text-xs font-medium text-gray-600 dark:text-gray-400">高级配置</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium flex items-center space-x-1">
							<span>最大并发任务数</span>
							<Tooltip content="同时处理的最大任务数量">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
									/>
								</svg>
							</Tooltip>
						</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="3"
								type="number"
								min="1"
								max="10"
								bind:value={inpaintingConfig.maxConcurrentTasks}
								required
							/>
						</div>
					</div>
				</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium flex items-center space-x-1">
							<span>任务超时时间 (毫秒)</span>
							<Tooltip content="单个任务的最长等待时间，超时会被标记为失败">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
									/>
								</svg>
							</Tooltip>
						</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="300000"
								type="number"
								min="60000"
								max="1800000"
								step="1000"
								bind:value={inpaintingConfig.taskTimeout}
								required
							/>
						</div>
					</div>
					<div class="text-xs text-gray-400 mt-1">推荐值: 300000ms (5分钟)</div>
				</div>
			</div>
		{/if}
	</div>

	<hr class=" border-gray-700" />

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class=" px-4 py-2 bg-blue-600 hover:bg-blue-700 text-gray-100 transition rounded-lg flex items-center space-x-2"
			type="submit"
			disabled={loading}
		>
			{#if loading}
				<svg
					class=" w-4 h-4 animate-spin"
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
				>
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					></path>
				</svg>
				<span>保存中...</span>
			{:else}
				<span>保存配置</span>
			{/if}
		</button>
	</div>

	<div class=" text-xs text-gray-400">
		配置完成后，用户将能够使用即梦涂抹消除功能去除图片中的对象。请确保API密钥有效且账户余额充足。
	</div>
</form>
