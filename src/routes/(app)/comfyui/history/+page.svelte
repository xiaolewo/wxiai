<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { user, showSidebar } from '$lib/stores';
	import { getComfyUIHistory, type ComfyUIHistoryItem } from '$lib/apis/comfyui';

	const i18n = getContext('i18n');

	let loading = true;
	let historyItems: ComfyUIHistoryItem[] = [];
	let currentPage = 1;
	let totalPages = 1;
	let pageSize = 20;

	// 图片模态框
	let showImageModal = false;
	let modalImageUrl = '';

	// 加载历史记录
	const loadHistory = async (page = 1) => {
		if (!$user.token) {
			goto('/auth');
			return;
		}

		loading = true;
		try {
			const response = await getComfyUIHistory($user.token, page, pageSize);
			historyItems = response.history;
			currentPage = page;
			totalPages = Math.ceil(response.total / pageSize) || 1;
		} catch (error) {
			console.error('获取历史记录失败:', error);
			toast.error('获取历史记录失败');
		}
		loading = false;
	};

	// 格式化时间
	const formatDateTime = (dateStr: string) => {
		try {
			const date = new Date(dateStr);
			return date.toLocaleString('zh-CN', {
				year: 'numeric',
				month: '2-digit',
				day: '2-digit',
				hour: '2-digit',
				minute: '2-digit'
			});
		} catch {
			return '未知时间';
		}
	};

	// 格式化生成时间
	const formatGenerationTime = (seconds?: number) => {
		if (!seconds) return '-';
		if (seconds < 60) return `${Math.round(seconds)}秒`;
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = Math.round(seconds % 60);
		return `${minutes}分${remainingSeconds}秒`;
	};

	// 页面切换
	const changePage = (page: number) => {
		if (page >= 1 && page <= totalPages && page !== currentPage) {
			loadHistory(page);
		}
	};

	// 打开图片模态框
	const openImageModal = (imageUrl: string) => {
		modalImageUrl = imageUrl;
		showImageModal = true;
	};

	// 关闭图片模态框
	const closeImageModal = () => {
		showImageModal = false;
		modalImageUrl = '';
	};

	onMount(() => {
		loadHistory();
	});
</script>

<svelte:head>
	<title>ComfyUI 历史记录</title>
</svelte:head>

<div
	class="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900 transition-all duration-300 {$showSidebar
		? 'md:max-w-[calc(100%-260px)]'
		: ''}"
>
	<div class="px-4 py-8 sm:px-6 lg:px-8">
		<div class="max-w-6xl mx-auto">
			<!-- 页面标题 -->
			<div class="flex items-center justify-between mb-6">
				<div class="flex items-center space-x-4">
					<button
						class="flex items-center text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
						on:click={() => goto('/comfyui')}
					>
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 19l-7-7 7-7"
							/>
						</svg>
						返回工作流广场
					</button>
				</div>
				<h1 class="text-2xl font-bold text-gray-900 dark:text-white">我的生成历史</h1>
			</div>

			{#if loading}
				<!-- 加载状态 -->
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-8">
					<div class="flex items-center justify-center">
						<div
							class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"
						></div>
						<span class="ml-3 text-gray-600 dark:text-gray-300">加载中...</span>
					</div>
				</div>
			{:else if historyItems.length === 0}
				<!-- 空状态 -->
				<div
					class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-12 text-center"
				>
					<div class="mx-auto w-24 h-24 mb-4 text-gray-300">
						<svg fill="currentColor" viewBox="0 0 24 24">
							<path
								d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"
							/>
						</svg>
					</div>
					<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">暂无生成记录</h3>
					<p class="text-gray-500 dark:text-gray-400 mb-4">你还没有完成过任何ComfyUI生成任务</p>
					<button
						class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
						on:click={() => goto('/comfyui')}
					>
						开始创作
					</button>
				</div>
			{:else}
				<!-- 历史记录列表 -->
				<div class="space-y-4">
					{#each historyItems as item (item.id)}
						<div
							class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6"
						>
							<!-- 记录头部 -->
							<div class="flex items-start justify-between mb-4">
								<div class="flex-1">
									<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
										{item.workflow_name}
									</h3>
									<div class="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
										<span class="flex items-center">
											<svg
												class="w-4 h-4 mr-1"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M12 8c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3-1.343-3-3-3z"
												/>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.745 3.745 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.745 3.745 0 013.296-1.043A3.745 3.745 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.745 3.745 0 013.296 1.043 3.745 3.745 0 011.043 3.296A3.745 3.745 0 0121 12z"
												/>
											</svg>
											{item.credits_cost} 积分
										</span>
										<span class="flex items-center">
											<svg
												class="w-4 h-4 mr-1"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
												/>
											</svg>
											{formatGenerationTime(item.generation_time)}
										</span>
										<span class="flex items-center">
											<svg
												class="w-4 h-4 mr-1"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
												/>
											</svg>
											{formatDateTime(item.created_at)}
										</span>
									</div>
								</div>
								<span
									class="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full text-sm"
								>
									已完成
								</span>
							</div>

							<!-- 输入参数摘要 -->
							{#if item.input_summary}
								<div class="mb-4 p-3 bg-gray-50 dark:bg-gray-750 rounded-lg">
									<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
										输入参数
									</h4>
									<p class="text-sm text-gray-600 dark:text-gray-400">{item.input_summary}</p>
								</div>
							{/if}

							<!-- 生成结果 -->
							<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
								<!-- 图片结果 -->
								{#if item.results.images && item.results.images.length > 0}
									<div>
										<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
											生成图片
										</h4>
										<div class="grid grid-cols-2 gap-2">
											{#each item.results.images as image}
												{@const imageUrl = image.cloud_url || image.original_url}
												<div class="relative group">
													<img
														src={imageUrl}
														alt="生成结果"
														class="w-full h-32 object-cover rounded-lg border dark:border-gray-600 cursor-pointer"
														loading="lazy"
														on:error={(e) => {
															// 如果云存储URL失败，尝试原始URL
															if (e.target.src === image.cloud_url && image.original_url) {
																e.target.src = image.original_url;
															}
														}}
														on:click={() => openImageModal(imageUrl)}
													/>
													<div
														class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all rounded-lg flex items-center justify-center"
													>
														<button
															class="opacity-0 group-hover:opacity-100 px-3 py-1 bg-white text-gray-800 rounded text-sm transition-opacity hover:bg-gray-100"
															on:click={() => openImageModal(imageUrl)}
														>
															查看大图
														</button>
													</div>
												</div>
											{/each}
										</div>
									</div>
								{/if}

								<!-- 视频结果 -->
								{#if item.results.videos && item.results.videos.length > 0}
									<div>
										<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
											生成视频
										</h4>
										<div class="space-y-2">
											{#each item.results.videos as video}
												<div class="relative">
													<video
														src={video.cloud_url}
														controls
														class="w-full h-48 rounded-lg border dark:border-gray-600"
														preload="metadata"
													>
														您的浏览器不支持视频播放。
													</video>
													{#if video.cover_url}
														<div class="absolute top-2 right-2">
															<img
																src={video.cover_url}
																alt="封面"
																class="w-12 h-12 rounded border bg-white"
															/>
														</div>
													{/if}
												</div>
											{/each}
										</div>
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>

				<!-- 分页导航 -->
				{#if totalPages > 1}
					<div class="flex items-center justify-center mt-8 space-x-2">
						<button
							class="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 disabled:opacity-50"
							disabled={currentPage === 1}
							on:click={() => changePage(currentPage - 1)}
						>
							上一页
						</button>

						{#each Array(totalPages) as _, i}
							<button
								class="px-3 py-2 text-sm rounded {currentPage === i + 1
									? 'bg-blue-600 text-white'
									: 'text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700'}"
								on:click={() => changePage(i + 1)}
							>
								{i + 1}
							</button>
						{/each}

						<button
							class="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 disabled:opacity-50"
							disabled={currentPage === totalPages}
							on:click={() => changePage(currentPage + 1)}
						>
							下一页
						</button>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>

<!-- 图片模态框 -->
{#if showImageModal}
	<div
		class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
		on:click={closeImageModal}
	>
		<div class="relative max-w-4xl max-h-full">
			<button
				class="absolute top-4 right-4 text-white hover:text-gray-300 text-2xl z-10"
				on:click={closeImageModal}
			>
				×
			</button>
			<img
				src={modalImageUrl}
				alt="查看大图"
				class="max-w-full max-h-full object-contain rounded-lg"
				on:click|stopPropagation
			/>
		</div>
	</div>
{/if}
