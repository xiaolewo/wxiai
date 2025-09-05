<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { user, showSidebar } from '$lib/stores';

	import {
		type ComfyUIWorkflow,
		type ComfyUICredits,
		getPublicComfyUIWorkflows,
		getComfyUICredits
	} from '$lib/apis/comfyui';

	const i18n = getContext('i18n');

	let workflows: ComfyUIWorkflow[] = [];
	let userCredits: ComfyUICredits | null = null;
	let loading = true;
	let selectedCategory = '';

	// 分类选项
	const categories = [
		{ value: '', label: '全部' },
		{ value: '图像处理', label: '图像处理' },
		{ value: '换脸', label: '换脸' },
		{ value: '风格转换', label: '风格转换' },
		{ value: '图像增强', label: '图像增强' },
		{ value: '创意合成', label: '创意合成' }
	];

	// 加载公开工作流
	const loadWorkflows = async () => {
		loading = true;
		try {
			workflows = await getPublicComfyUIWorkflows(selectedCategory || undefined);
		} catch (error) {
			console.error('获取工作流失败:', error);
			toast.error('获取工作流失败');
		}
		loading = false;
	};

	// 加载用户积分
	const loadUserCredits = async () => {
		if (!$user.token) return;

		try {
			userCredits = await getComfyUICredits($user.token);
		} catch (error) {
			console.error('获取用户积分失败:', error);
		}
	};

	// 分类筛选
	const filterByCategory = async (category: string) => {
		selectedCategory = category;
		await loadWorkflows();
	};

	// 使用工作流
	const useWorkflow = (workflow: ComfyUIWorkflow) => {
		goto(`/comfyui/workflow/${workflow.id}`);
	};

	onMount(() => {
		loadWorkflows();
		loadUserCredits();
	});
</script>

<svelte:head>
	<title>ComfyUI 工作流广场</title>
</svelte:head>

<div
	class="flex-1 overflow-y-auto bg-white dark:bg-gray-900 transition-all duration-300 {$showSidebar
		? 'md:max-w-[calc(100%-260px)]'
		: ''}"
>
	<!-- 页面头部 -->
	<div class="bg-gray-50 dark:bg-gray-800">
		<div class="px-4 py-8 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-3xl font-bold mb-2 text-gray-900 dark:text-white">ComfyUI 工作流广场</h1>
					<p class="text-gray-600 dark:text-gray-400">
						发现和使用强大的 ComfyUI 工作流，让 AI 创作更简单
					</p>
				</div>
				<div class="flex items-center space-x-4">
					<!-- 历史记录按钮 -->
					<button
						class="flex items-center px-4 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
						on:click={() => goto('/comfyui/history')}
					>
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
						<span class="text-sm">我的历史</span>
					</button>

					{#if userCredits}
						<div
							class="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-4 py-2"
						>
							<div class="text-sm text-gray-600 dark:text-gray-400">我的积分</div>
							<div class="text-2xl font-bold text-gray-900 dark:text-white">
								{userCredits.credits_balance}
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>

	<div class="px-4 py-8 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-800">
		<!-- 分类筛选 -->
		<div class="mb-8">
			<div class="flex flex-wrap gap-2">
				{#each categories as category}
					<button
						class="px-4 py-2 rounded-full transition-all duration-200 {selectedCategory ===
						category.value
							? 'bg-blue-600 text-white shadow-lg'
							: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}"
						on:click={() => filterByCategory(category.value)}
					>
						{category.label}
					</button>
				{/each}
			</div>
		</div>

		{#if loading}
			<!-- 加载状态 -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
				{#each Array(8) as _}
					<div
						class="bg-white dark:bg-gray-800 rounded-lg p-4 animate-pulse border dark:border-gray-700"
					>
						<div class="w-full h-48 bg-gray-200 dark:bg-gray-700 rounded-lg mb-4"></div>
						<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
						<div class="h-3 bg-gray-200 dark:bg-gray-700 rounded mb-4 w-3/4"></div>
						<div class="flex justify-between items-center">
							<div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
							<div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
						</div>
					</div>
				{/each}
			</div>
		{:else if workflows.length === 0}
			<!-- 空状态 -->
			<div class="text-center py-16">
				<div class="w-24 h-24 mx-auto mb-4 text-gray-300 dark:text-gray-600">
					<svg fill="currentColor" viewBox="0 0 24 24">
						<path
							fill-rule="evenodd"
							d="M3 6a3 3 0 013-3h2.25a3 3 0 013 3v2.25a3 3 0 01-3 3H6a3 3 0 01-3-3V6zm9.75 0a3 3 0 013-3H18a3 3 0 013 3v2.25a3 3 0 01-3 3h-2.25a3 3 0 01-3-3V6zM3 15.75a3 3 0 013-3h2.25a3 3 0 013 3V18a3 3 0 01-3 3H6a3 3 0 01-3-3v-2.25zm9.75 0a3 3 0 013-3H18a3 3 0 013 3V18a3 3 0 01-3 3h-2.25a3 3 0 01-3-3v-2.25z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
				<h3 class="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">暂无工作流</h3>
				<p class="text-gray-500 dark:text-gray-400">
					{selectedCategory ? '该分类下' : ''}暂时没有可用的工作流，请稍后再试
				</p>
			</div>
		{:else}
			<!-- 工作流卡片网格 -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
				{#each workflows as workflow}
					<div
						class="bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 border dark:border-gray-700 overflow-hidden"
					>
						<!-- 预览图 -->
						<div
							class="w-full h-48 bg-gradient-to-br from-blue-500 to-purple-600 relative overflow-hidden"
						>
							{#if workflow.preview_image}
								<img
									src={workflow.preview_image}
									alt={workflow.name}
									class="w-full h-full object-cover"
								/>
							{:else}
								<div class="w-full h-full flex items-center justify-center text-white">
									<svg class="w-16 h-16 opacity-70" fill="currentColor" viewBox="0 0 24 24">
										<path
											fill-rule="evenodd"
											d="M3 6a3 3 0 013-3h2.25a3 3 0 013 3v2.25a3 3 0 01-3 3H6a3 3 0 01-3-3V6zm9.75 0a3 3 0 013-3H18a3 3 0 013 3v2.25a3 3 0 01-3 3h-2.25a3 3 0 01-3-3V6zM3 15.75a3 3 0 013-3h2.25a3 3 0 013 3V18a3 3 0 01-3 3H6a3 3 0 01-3-3v-2.25zm9.75 0a3 3 0 013-3H18a3 3 0 013 3V18a3 3 0 01-3 3h-2.25a3 3 0 01-3-3v-2.25z"
											clip-rule="evenodd"
										/>
									</svg>
								</div>
							{/if}

							<!-- 分类标签 -->
							{#if workflow.category}
								<div class="absolute top-2 left-2">
									<span
										class="px-2 py-1 text-xs bg-black/50 text-white rounded-full backdrop-blur-sm"
									>
										{workflow.category}
									</span>
								</div>
							{/if}
						</div>

						<!-- 卡片内容 -->
						<div class="p-4">
							<h3 class="font-semibold text-gray-900 dark:text-white mb-2 text-lg leading-tight">
								{workflow.name}
							</h3>

							{#if workflow.description}
								<p class="text-gray-600 dark:text-gray-300 text-sm mb-3 line-clamp-2">
									{workflow.description}
								</p>
							{/if}

							<!-- 积分和操作 -->
							<div class="flex items-center justify-between">
								<div class="flex items-center space-x-2">
									<div class="flex items-center text-amber-500">
										<svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24">
											<path
												d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
											/>
										</svg>
										<span class="text-sm font-medium">{workflow.base_credits}</span>
									</div>
									{#if workflow.complexity_multiplier !== 1.0}
										<span class="text-xs text-gray-500 dark:text-gray-400">
											×{workflow.complexity_multiplier}
										</span>
									{/if}
								</div>

								<button
									class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors duration-200 font-medium"
									on:click={() => useWorkflow(workflow)}
								>
									使用
								</button>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
