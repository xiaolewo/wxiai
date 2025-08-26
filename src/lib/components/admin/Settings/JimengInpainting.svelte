<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import Jimeng Inpainting API functions
	import {
		getJimengInpaintingConfig,
		saveJimengInpaintingConfig,
		testJimengInpaintingConnection
	} from '$lib/apis/jimeng-inpainting.js';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	// 即梦涂抹消除配置
	let jimengInpaintingConfig = {
		enabled: false,
		base_url: 'https://visual.volcengineapi.com',
		api_key: '',
		credits_cost: 30,
		edit_credits_cost: 40,
		default_steps: 30,
		default_strength: 0.8,
		default_scale: 7.0,
		default_quality: 'M'
	};

	// 质量选项
	const qualityOptions = [
		{ value: 'H', label: '高质量 (最佳效果，速度较慢)' },
		{ value: 'M', label: '中等质量 (平衡效果与速度)' },
		{ value: 'L', label: '低质量 (速度最快，效果一般)' }
	];

	onMount(async () => {
		await loadJimengInpaintingConfig();
	});

	const loadJimengInpaintingConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getJimengInpaintingConfig($user.token);
			if (config) {
				jimengInpaintingConfig = { ...jimengInpaintingConfig, ...config };
			}
		} catch (error) {
			console.error('Failed to load Jimeng Inpainting config:', error);
			toast.error('加载即梦涂抹消除配置失败');
		} finally {
			loading = false;
		}
	};

	const saveJimengInpaintingConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveJimengInpaintingConfig($user.token, jimengInpaintingConfig);
			toast.success('即梦涂抹消除配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save Jimeng Inpainting config:', error);
			toast.error('保存即梦涂抹消除配置失败');
		} finally {
			loading = false;
		}
	};

	const handleTestConnection = async () => {
		if (!jimengInpaintingConfig.base_url || !jimengInpaintingConfig.api_key) {
			toast.error('请先配置 API URL 和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const result = await testJimengInpaintingConnection($user.token);
			if (result.status === 'success') {
				toast.success('即梦涂抹消除连接测试成功');
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
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={() => {
		saveJimengInpaintingConfigData();
	}}
>
	<div class="space-y-3 overflow-y-scroll scrollbar-hidden h-full">
		<div>
			<div class="mb-2 flex w-full justify-between">
				<div class="flex items-center space-x-2">
					<div class="font-medium text-sm">🎨 即梦涂抹消除服务</div>
					<Tooltip content="即梦AI的智能涂抹消除服务，基于火山豆包API，支持去除图片中不需要的元素">
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
								d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l-.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
							/>
						</svg>
					</Tooltip>
				</div>
				<Switch bind:state={jimengInpaintingConfig.enabled} />
			</div>
		</div>

		{#if jimengInpaintingConfig.enabled}
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
										placeholder="https://visual.volcengineapi.com"
										bind:value={jimengInpaintingConfig.base_url}
										autocomplete="off"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div>
					<div class="mb-1 text-xs text-gray-500">API 密钥</div>
					<SensitiveInput
						placeholder="输入即梦API密钥..."
						bind:value={jimengInpaintingConfig.api_key}
					/>
				</div>

				<div class="flex justify-end">
					<button
						class="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition"
						type="button"
						on:click={handleTestConnection}
						disabled={loading ||
							!jimengInpaintingConfig.base_url ||
							!jimengInpaintingConfig.api_key}
					>
						{loading ? '测试中...' : '测试连接'}
					</button>
				</div>
			</div>

			<!-- 默认设置 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>默认设置</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">
							默认采样步数
							<Tooltip
								content="生成图像的精细程度，越大效果可能更好，但相应的耗时会增加。范围：10-50"
							>
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
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l-.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="10"
							max="50"
							bind:value={jimengInpaintingConfig.default_steps}
						/>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							默认消除强度
							<Tooltip content="越小越接近原图，越大消除效果越明显。范围：0.1-1.0">
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
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l-.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="0.1"
							max="1.0"
							step="0.1"
							bind:value={jimengInpaintingConfig.default_strength}
						/>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							默认控制程度
							<Tooltip content="影响文本描述的程度，范围：1-20">
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
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l-.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="1"
							max="20"
							step="0.5"
							bind:value={jimengInpaintingConfig.default_scale}
						/>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">默认质量模式</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={jimengInpaintingConfig.default_quality}
						>
							{#each qualityOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							涂抹消除积分
							<Tooltip content="每次涂抹消除功能消耗的积分数量，用于去除图片中不需要的元素">
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
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l-.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="1"
							bind:value={jimengInpaintingConfig.credits_cost}
						/>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							涂抹编辑积分
							<Tooltip content="每次涂抹编辑功能消耗的积分数量，用于根据提示词生成新内容">
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
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l-.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="1"
							bind:value={jimengInpaintingConfig.edit_credits_cost}
						/>
					</div>
				</div>
			</div>

			<!-- 功能特性 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>功能特性</div>
				</div>

				<div class="grid grid-cols-1 gap-3">
					<div class="p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">核心功能</div>
						<div class="space-y-1 text-xs text-gray-600 dark:text-gray-400">
							<div>• <strong>智能涂抹消除：</strong>基于AI技术，精确去除图片中不需要的元素</div>
							<div>• <strong>无缝填补：</strong>智能重建被消除区域，保持图像自然和谐</div>
							<div>• <strong>高质量输出：</strong>支持多种质量模式，满足不同需求</div>
						</div>
					</div>

					<div class="p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">输入要求</div>
						<div class="space-y-1 text-xs text-gray-600 dark:text-gray-400">
							<div>
								• <strong>原始图片：</strong>JPG/PNG 格式，最大 5MB，分辨率 64x64 - 4096x4096
							</div>
							<div>• <strong>遮罩图片：</strong>单通道灰度图或三通道图，白色区域为待消除部分</div>
							<div>• <strong>支持格式：</strong>8bit PNG 编码，勿嵌入 ICC Profile</div>
						</div>
					</div>

					<div class="p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">应用场景</div>
						<div class="space-y-1 text-xs text-gray-600 dark:text-gray-400">
							<div>• <strong>路人消除：</strong>去除照片中的路人或背景人物</div>
							<div>• <strong>杂物清理：</strong>清除图片中的杂物、垃圾等干扰元素</div>
							<div>• <strong>水印去除：</strong>清除图片上的水印、标识等</div>
							<div>• <strong>物体替换：</strong>替换或移除特定物体，优化图像构图</div>
						</div>
					</div>

					<div class="p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">技术特点</div>
						<div class="space-y-1 text-xs text-gray-600 dark:text-gray-400">
							<div>• <strong>即时处理：</strong>API直接返回结果，无需轮询</div>
							<div>• <strong>云端存储：</strong>自动保存到云存储，便于管理和分享</div>
							<div>• <strong>参数可调：</strong>支持自定义采样步数、消除强度等参数</div>
							<div>• <strong>质量保证：</strong>多重质量检测，确保输出效果</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 参数说明 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>参数说明</div>
				</div>

				<div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<div class="text-xs text-gray-600 dark:text-gray-400 space-y-2">
						<div class="font-medium">高级参数：</div>
						<div>• <strong>采样步数 (Steps)：</strong> 控制生成精度，建议 20-40</div>
						<div>• <strong>消除强度 (Strength)：</strong> 控制消除力度，建议 0.6-1.0</div>
						<div>• <strong>控制程度 (Scale)：</strong> 影响算法引导强度，建议 5-10</div>
						<div>• <strong>遮罩膨胀 (Dilate Size)：</strong> 扩大消除区域，建议 10-20</div>
						<div>• <strong>随机种子 (Seed)：</strong> 控制随机性，相同种子生成一致结果</div>
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
