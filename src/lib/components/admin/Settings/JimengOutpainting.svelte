<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import Jimeng Outpainting API functions
	import {
		getJimengOutpaintingConfig,
		saveJimengOutpaintingConfig,
		testJimengOutpaintingConnection
	} from '$lib/apis/jimeng-outpainting.js';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let testing = false;

	// 即梦智能扩图配置
	let jimengOutpaintingConfig = {
		enabled: false,
		base_url: '',
		api_key: '',
		credits_cost: 25,
		default_steps: 30,
		default_strength: 0.8,
		default_scale: 7.0,
		default_quality: 'M',
		default_max_width: 1920,
		default_max_height: 1920
	};

	// 质量选项
	const qualityOptions = [
		{ value: 'H', label: '高质量 (最佳效果，速度较慢)' },
		{ value: 'M', label: '中等质量 (平衡效果与速度)' },
		{ value: 'L', label: '低质量 (速度最快，效果一般)' }
	];

	onMount(async () => {
		await loadJimengOutpaintingConfig();
	});

	const loadJimengOutpaintingConfig = async () => {
		if (!$user?.token || $user?.role !== 'admin') {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getJimengOutpaintingConfig($user.token);
			if (config) {
				jimengOutpaintingConfig = { ...jimengOutpaintingConfig, ...config };
				console.log('📋 加载即梦智能扩图配置:', config);
			}
		} catch (error) {
			console.error('❌ 加载即梦智能扩图配置失败:', error);
			toast.error(`加载配置失败: ${error}`);
		} finally {
			loading = false;
		}
	};

	const saveJimengOutpaintingConfigData = async () => {
		if (!$user?.token || $user?.role !== 'admin') {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveJimengOutpaintingConfig($user.token, jimengOutpaintingConfig);
			toast.success('✅ 即梦智能扩图配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('❌ 保存即梦智能扩图配置失败:', error);
			toast.error(`保存配置失败: ${error}`);
		} finally {
			loading = false;
		}
	};

	const handleTestConnection = async () => {
		if (!jimengOutpaintingConfig.base_url || !jimengOutpaintingConfig.api_key) {
			toast.error('请先填写API地址和密钥');
			return;
		}

		if (!$user?.token || $user?.role !== 'admin') {
			toast.error('需要管理员权限');
			return;
		}

		testing = true;
		try {
			const result = await testJimengOutpaintingConnection($user.token);
			if (result.status === 'success') {
				toast.success('🎉 即梦智能扩图连接测试成功');
			} else {
				toast.error(`连接测试失败: ${result.message}`);
			}
		} catch (error) {
			console.error('❌ 连接测试失败:', error);
			toast.error(`连接测试失败: ${error}`);
		} finally {
			testing = false;
		}
	};
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm">
	<div class="space-y-3">
		<div>
			<div class="mb-2 flex w-full justify-between">
				<div class="flex items-center space-x-2">
					<div class="flex self-center">🎨 即梦智能扩图配置</div>
				</div>
				<div class="flex items-center space-x-2">
					<Switch bind:state={jimengOutpaintingConfig.enabled} />
				</div>
			</div>
			<div class="text-xs text-gray-500 dark:text-gray-400">
				配置即梦智能扩图服务，支持四种扩展模式：等比扩展、画幅扩展、四边扩展、画布扩展
			</div>
		</div>

		<hr class="dark:border-gray-700" />

		<div class="space-y-3">
			<!-- API 基础配置 -->
			<div class="space-y-2">
				<div class="text-sm font-medium text-gray-700 dark:text-gray-300">API 基础配置</div>

				<div>
					<div class="mb-1 flex items-center space-x-2">
						<label class="text-xs font-medium text-gray-700 dark:text-gray-300" for="base_url">
							API 基础地址 *
						</label>
						<Tooltip
							content="即梦智能扩图API的基础地址，例如：https://visual.volcengineapi.com 或第三方代理地址"
						>
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
									d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z"
								/>
							</svg>
						</Tooltip>
					</div>
					<input
						id="base_url"
						class="w-full rounded-lg py-2.5 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
						placeholder="https://visual.volcengineapi.com"
						bind:value={jimengOutpaintingConfig.base_url}
						autocomplete="off"
					/>
				</div>

				<div>
					<div class="mb-1 flex items-center space-x-2">
						<label class="text-xs font-medium text-gray-700 dark:text-gray-300" for="api_key">
							API 密钥 *
						</label>
						<Tooltip content="即梦API的访问密钥，请从即梦平台获取">
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
									d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z"
								/>
							</svg>
						</Tooltip>
					</div>
					<SensitiveInput
						id="api_key"
						placeholder="请输入即梦API密钥"
						bind:value={jimengOutpaintingConfig.api_key}
						autocomplete="off"
					/>
				</div>

				<div class="flex space-x-2">
					<button
						class="flex-1 px-3 py-2 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors disabled:opacity-50"
						on:click={handleTestConnection}
						disabled={testing ||
							!jimengOutpaintingConfig.base_url ||
							!jimengOutpaintingConfig.api_key}
					>
						{#if testing}
							<div
								class="inline-block animate-spin rounded-full h-3 w-3 border-b border-blue-700 mr-1"
							></div>
							测试中...
						{:else}
							🔌 测试连接
						{/if}
					</button>
				</div>
			</div>

			<!-- 积分配置 -->
			<div class="space-y-2">
				<div class="text-sm font-medium text-gray-700 dark:text-gray-300">积分配置</div>

				<div>
					<div class="mb-1 flex items-center space-x-2">
						<label class="text-xs font-medium text-gray-700 dark:text-gray-300" for="credits_cost">
							每次扩图消耗积分
						</label>
						<Tooltip content="用户每次使用智能扩图功能消耗的积分数量">
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
									d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z"
								/>
							</svg>
						</Tooltip>
					</div>
					<input
						id="credits_cost"
						class="w-full rounded-lg py-2.5 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
						type="number"
						min="1"
						max="1000"
						placeholder="25"
						bind:value={jimengOutpaintingConfig.credits_cost}
					/>
				</div>
			</div>

			<!-- 默认参数配置 -->
			<div class="space-y-2">
				<div class="text-sm font-medium text-gray-700 dark:text-gray-300">默认参数配置</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1">
							<label
								class="text-xs font-medium text-gray-700 dark:text-gray-300"
								for="default_steps"
							>
								默认采样步数
							</label>
						</div>
						<input
							id="default_steps"
							class="w-full rounded-lg py-2.5 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
							type="number"
							min="10"
							max="50"
							bind:value={jimengOutpaintingConfig.default_steps}
						/>
					</div>

					<div>
						<div class="mb-1">
							<label
								class="text-xs font-medium text-gray-700 dark:text-gray-300"
								for="default_strength"
							>
								默认扩展强度
							</label>
						</div>
						<input
							id="default_strength"
							class="w-full rounded-lg py-2.5 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
							type="number"
							min="0.1"
							max="1.0"
							step="0.1"
							bind:value={jimengOutpaintingConfig.default_strength}
						/>
					</div>

					<div>
						<div class="mb-1">
							<label
								class="text-xs font-medium text-gray-700 dark:text-gray-300"
								for="default_scale"
							>
								默认控制程度
							</label>
						</div>
						<input
							id="default_scale"
							class="w-full rounded-lg py-2.5 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
							type="number"
							min="1"
							max="20"
							step="0.5"
							bind:value={jimengOutpaintingConfig.default_scale}
						/>
					</div>

					<div>
						<div class="mb-1">
							<label
								class="text-xs font-medium text-gray-700 dark:text-gray-300"
								for="default_quality"
							>
								默认质量等级
							</label>
						</div>
						<select
							id="default_quality"
							class="w-full rounded-lg py-2.5 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
							bind:value={jimengOutpaintingConfig.default_quality}
						>
							{#each qualityOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1">
							<label
								class="text-xs font-medium text-gray-700 dark:text-gray-300"
								for="default_max_width"
							>
								默认最大宽度 (px)
							</label>
						</div>
						<input
							id="default_max_width"
							class="w-full rounded-lg py-2.5 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
							type="number"
							min="512"
							max="4096"
							step="64"
							bind:value={jimengOutpaintingConfig.default_max_width}
						/>
					</div>

					<div>
						<div class="mb-1">
							<label
								class="text-xs font-medium text-gray-700 dark:text-gray-300"
								for="default_max_height"
							>
								默认最大高度 (px)
							</label>
						</div>
						<input
							id="default_max_height"
							class="w-full rounded-lg py-2.5 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
							type="number"
							min="512"
							max="4096"
							step="64"
							bind:value={jimengOutpaintingConfig.default_max_height}
						/>
					</div>
				</div>
			</div>

			<!-- 使用说明 -->
			<div class="space-y-2">
				<div class="text-sm font-medium text-gray-700 dark:text-gray-300">使用说明</div>
				<div class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
					<div>• <strong>等比扩展：</strong>四边相同比例扩展</div>
					<div>• <strong>画幅扩展：</strong>扩展为指定画幅比例（1:1, 4:3, 16:9, 9:16）</div>
					<div>• <strong>四边扩展：</strong>自定义各边扩展比例</div>
					<div>• <strong>画布扩展：</strong>在画布中自定义图片位置和大小</div>
					<div>• 用户可以上传图片并选择扩展模式，系统会自动扣除相应积分</div>
				</div>
			</div>
		</div>
	</div>

	<div class="flex justify-end pt-3">
		<button
			class="px-3.5 py-1.5 text-xs font-medium bg-black hover:bg-gray-900 dark:bg-white dark:hover:bg-gray-100 text-white dark:text-black transition rounded-lg disabled:opacity-50"
			on:click={saveJimengOutpaintingConfigData}
			disabled={loading}
		>
			{#if loading}
				<div
					class="inline-block animate-spin rounded-full h-3 w-3 border-b border-white dark:border-black mr-1"
				></div>
				保存中...
			{:else}
				💾 保存配置
			{/if}
		</button>
	</div>
</div>
