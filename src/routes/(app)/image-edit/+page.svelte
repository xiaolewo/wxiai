<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, showSidebar, user, mobile, config } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import InpaintingModal from '$lib/components/common/InpaintingModal.svelte';

	// Import API wrapper functions
	import {
		getInpaintingUserConfig,
		uploadInpaintingImage,
		submitInpaintingTask,
		getInpaintingUserTaskHistory,
		getInpaintingUserCredits,
		deleteInpaintingTask
	} from '$lib/apis/inpainting';

	const i18n = getContext('i18n');

	let loaded = false;
	let isGenerating = false;
	let currentTask = null;
	let generatedResult = null;
	let taskHistory = [];
	let userCredits = 0;
	let loadingData = false;
	let inpaintingConfig = null;

	// Modal related
	let showInpaintingModal = false;
	let selectedImageFile: File | null = null;

	// Image viewer modal
	let showImageModal = false;
	let selectedImageUrl = '';
	let selectedImageAlt = '';
	let imageLoading = false;

	onMount(async () => {
		if ($user) {
			await loadUserData();
			loaded = true;
		}
	});

	const loadUserData = async () => {
		if (!$user?.token) {
			console.error('🎨 【图像编辑】没有token，无法加载数据');
			return;
		}

		try {
			loadingData = true;

			// Load configuration using API wrapper
			try {
				inpaintingConfig = await getInpaintingUserConfig($user.token);
				console.log('🎨 【图像编辑】配置已加载:', inpaintingConfig);

				// 配置已加载 - 默认参数在模态框中设置
			} catch (error) {
				console.error('🎨 【图像编辑】加载配置失败:', error);
			}

			// Load user credits using API wrapper
			try {
				const creditsData = await getInpaintingUserCredits($user.token);
				if (creditsData && creditsData.success) {
					userCredits = creditsData.balance || 0;
					console.log('🎨 【图像编辑】系统积分余额:', userCredits);
				}
			} catch (error) {
				console.error('🎨 【图像编辑】加载系统积分失败:', error);
			}

			// Load task history using API wrapper
			try {
				const historyData = await getInpaintingUserTaskHistory($user.token, 1, 20);
				if (historyData && historyData.data) {
					taskHistory = historyData.data;
					console.log('🎨 【图像编辑】加载历史记录:', taskHistory.length, '个任务');
				}
			} catch (error) {
				console.error('🎨 【图像编辑】加载历史失败:', error);
			}
		} catch (error) {
			console.error('🎨 【图像编辑】加载用户数据失败:', error);
			toast.error('加载数据失败');
		} finally {
			loadingData = false;
		}
	};

	const handleImageUpload = async (event) => {
		const file = event.target.files[0];
		if (!file) return;

		if (!file.type.startsWith('image/')) {
			toast.error('请上传图片文件');
			return;
		}

		// 降低文件大小限制，提升处理速度
		if (file.size > 2 * 1024 * 1024) {
			toast.error('图片文件不能超过2MB，请使用更小的图片以避免超时');
			return;
		}

		try {
			// 预先检查图片尺寸
			const img = new Image();
			const canvas = document.createElement('canvas');
			const ctx = canvas.getContext('2d');

			img.onload = () => {
				// 检查图片尺寸
				if (img.width > 2048 || img.height > 2048) {
					toast.error('图片尺寸过大，请使用小于2048x2048像素的图片');
					return;
				}

				// 如果图片尺寸合理，继续处理
				selectedImageFile = file;
				showInpaintingModal = true;
				toast.success(
					'图片已选择，请在弹窗中涂抹需要消除的区域（为避免超时，请使用较小的涂抹区域）'
				);
				console.log('🎨 【图像编辑】图片已选择:', file.name, `尺寸: ${img.width}x${img.height}`);
			};

			img.onerror = () => {
				toast.error('图片加载失败，请选择有效的图片文件');
			};

			// 读取图片
			const reader = new FileReader();
			reader.onload = (e) => {
				img.src = e.target.result;
			};
			reader.readAsDataURL(file);
		} catch (error) {
			console.error('🎨 【图像编辑】图片处理失败:', error);
			toast.error('图片处理失败');
		}
	};

	const handleInpaintingSubmit = async (event) => {
		const { scaledInputImageBase64, maskImageBase64, parameters } = event.detail;

		if (!selectedImageFile) {
			toast.error('图片选择失败，请重新选择');
			return;
		}

		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		try {
			isGenerating = true;

			console.log('🎨 【图像编辑前端】提交涂抹消除任务(使用缩放后图片):', {
				scaledInputImageBase64: `${scaledInputImageBase64.length} 字符`,
				maskImageBase64: `${maskImageBase64.length} 字符`,
				scaledInputPreview: scaledInputImageBase64.substring(0, 50) + '...',
				maskImagePreview: maskImageBase64.substring(0, 50) + '...',
				...parameters
			});

			const result = await submitInpaintingTask(
				$user.token,
				scaledInputImageBase64,
				maskImageBase64,
				parameters
			);

			if (result && result.success) {
				generatedResult = {
					id: result.task_id,
					result_image_url: result.result_image_url,
					status: 'completed'
				};

				// 关闭弹窗
				showInpaintingModal = false;

				toast.success('图像涂抹消除完成');

				// 刷新用户数据
				await loadUserData();
			} else {
				toast.error(result?.message || '任务提交失败');
			}
		} catch (error) {
			console.error('🎨 【图像编辑】提交任务失败:', error);
			toast.error('提交任务失败');
		} finally {
			isGenerating = false;
		}
	};

	const handleModalClose = () => {
		showInpaintingModal = false;
		selectedImageFile = null;
	};

	const handleDeleteTask = async (taskId: string) => {
		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		try {
			const confirmed = confirm('确定要删除此涂抹消除任务吗？');
			if (!confirmed) return;

			console.log('🗑️ 删除涂抹消除任务:', taskId);

			const result = await deleteInpaintingTask($user.token, taskId);

			if (result && result.success) {
				// 从历史记录中移除任务
				taskHistory = taskHistory.filter((t) => t.id !== taskId);

				// 如果删除的是最新生成结果，清空显示
				if (generatedResult?.id === taskId) {
					generatedResult = null;
				}

				toast.success('任务删除成功');
				await loadUserData(); // 刷新数据
			} else {
				toast.error(result?.message || '删除失败');
			}
		} catch (error) {
			console.error('🎨 【图像编辑】删除任务失败:', error);
			toast.error('删除失败');
		}
	};

	const formatDate = (dateString) => {
		if (!dateString) return '-';
		try {
			const date = new Date(dateString);
			// 检查日期是否有效
			if (isNaN(date.getTime())) return '-';

			return date.toLocaleString('zh-CN', {
				year: 'numeric',
				month: '2-digit',
				day: '2-digit',
				hour: '2-digit',
				minute: '2-digit',
				second: '2-digit'
			});
		} catch (error) {
			console.error('日期格式化错误:', error);
			return '-';
		}
	};

	// 图片放大功能
	const handleImageClick = (imageUrl, alt = '生成结果') => {
		if (imageUrl) {
			selectedImageUrl = imageUrl;
			selectedImageAlt = alt;
			imageLoading = true;
			showImageModal = true;
		}
	};

	const closeImageModal = () => {
		showImageModal = false;
		selectedImageUrl = '';
		selectedImageAlt = '';
		imageLoading = false;
	};

	const handleImageLoad = () => {
		imageLoading = false;
	};

	const handleImageError = () => {
		imageLoading = false;
		toast.error('图片加载失败');
	};

	const getStatusText = (status) => {
		const statusMap = {
			submitted: '已提交',
			processing: '处理中',
			completed: '已完成',
			failed: '失败'
		};
		return statusMap[status] || status;
	};

	const getStatusColor = (status) => {
		const colorMap = {
			submitted: 'text-yellow-600',
			processing: 'text-blue-600',
			completed: 'text-green-600',
			failed: 'text-red-600'
		};
		return colorMap[status] || 'text-gray-600';
	};
</script>

<svelte:head>
	<title>图像编辑 - {$WEBUI_NAME}</title>
</svelte:head>

{#if loaded}
	<div
		class="relative flex w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
			? 'md:max-w-[calc(100%-260px)]'
			: ''} max-w-full"
	>
		<!-- 主体内容 - 左右分栏：左侧操作栏，右侧历史记录栏 -->
		<div class="flex w-full h-full">
			<!-- 左侧操作栏 -->
			<div
				class="w-80 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-600 overflow-y-auto scrollbar-hide"
			>
				<div class="p-4 space-y-4">
					<!-- 服务选择和状态 -->
					<div>
						<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							🎨 图像编辑服务
						</h3>
						<div class="rounded-lg p-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
							<div class="flex items-center justify-between">
								<div>
									<div class="font-medium">即梦涂抹消除</div>
									<div class="text-xs opacity-75">
										{inpaintingConfig?.enabled ? '已启用' : '未配置'}
									</div>
								</div>
								<div class="text-xl">🎨</div>
							</div>
						</div>
					</div>

					<!-- 积分余额 -->
					<div class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
						<div>当前服务: 即梦涂抹消除</div>
						<div>消耗积分: {inpaintingConfig?.credits_per_task || 50}积分/次</div>
						<div class="flex justify-between items-center">
							<div class="text-green-600 dark:text-green-400">余额: {userCredits}积分</div>
							<button
								class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded transition-colors"
								on:click={async () => {
									await loadUserData();
									toast.success('配置和积分已刷新');
								}}
								disabled={loadingData}
								title="刷新积分和配置"
							>
								{loadingData ? '刷新中...' : '刷新'}
							</button>
						</div>
					</div>

					{#if !inpaintingConfig || !inpaintingConfig.enabled}
						<div
							class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3"
						>
							<div class="text-sm font-medium text-red-700 dark:text-red-300 mb-1">服务未启用</div>
							<div class="text-xs text-red-600 dark:text-red-400">
								请联系管理员配置即梦涂抹消除服务
							</div>
						</div>
					{:else}
						<!-- 图片上传 -->
						<div class="text-center">
							<h3 class="text-lg font-medium text-gray-700 dark:text-gray-300 mb-4">
								上传图片开始编辑
							</h3>

							<div
								class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
							>
								<input
									type="file"
									accept="image/*"
									on:change={handleImageUpload}
									class="hidden"
									id="image-upload"
								/>
								<label for="image-upload" class="cursor-pointer flex flex-col items-center">
									<svg
										class="w-12 h-12 text-gray-400 mb-4"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
										></path>
									</svg>
									<div class="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
										点击上传图片
									</div>
									<div class="text-sm text-gray-500 dark:text-gray-400">
										支持 JPG、PNG 格式，最大 5MB
									</div>
								</label>
							</div>

							{#if selectedImageFile}
								<div
									class="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
								>
									<div class="text-sm text-green-700 dark:text-green-300">
										✅ {selectedImageFile.name} ({Math.round(
											(selectedImageFile.size / 1024 / 1024) * 100
										) / 100} MB)
									</div>
								</div>
							{/if}
						</div>

						<!-- 使用说明 -->
						<div
							class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4"
						>
							<h4 class="font-medium text-blue-700 dark:text-blue-300 mb-2">使用说明</h4>
							<ol class="text-sm text-blue-600 dark:text-blue-400 space-y-1">
								<li>1. 上传需要编辑的图片（建议小于2MB）</li>
								<li>2. 在弹窗中用鼠标涂抹需要消除的区域</li>
								<li>3. 调整参数后点击"开始消除"</li>
								<li>4. 等待处理完成，查看结果</li>
							</ol>
						</div>

						<!-- 优化建议 -->
						<div
							class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4"
						>
							<h4 class="font-medium text-amber-700 dark:text-amber-300 mb-2">💡 避免超时建议</h4>
							<ul class="text-sm text-amber-600 dark:text-amber-400 space-y-1">
								<li>• 使用较小的图片（推荐512px以内）</li>
								<li>• 涂抹区域不要过大</li>
								<li>• 选择"低质量"模式获得更快速度</li>
								<li>• 减少处理步数（10-15步）</li>
							</ul>
						</div>

						<!-- 最新生成结果 -->
						{#if generatedResult && generatedResult.status === 'completed'}
							<div
								class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3"
							>
								<div class="text-sm font-medium text-green-700 dark:text-green-300 mb-2">
									✅ 消除完成
								</div>
								{#if generatedResult.result_image_url}
									<div class="relative group">
										<img
											src={generatedResult.result_image_url}
											alt="最新消除结果"
											class="w-full rounded-lg cursor-pointer hover:opacity-80 transition-opacity"
											on:click={() =>
												handleImageClick(generatedResult.result_image_url, '最新消除结果')}
											title="点击查看大图"
										/>
										<!-- 放大图标提示 -->
										<div
											class="absolute top-2 right-2 bg-black/50 text-white rounded-full p-2 opacity-0 group-hover:opacity-100 transition-opacity"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
												></path>
											</svg>
										</div>
									</div>
								{/if}
							</div>
						{/if}
					{/if}
				</div>
			</div>

			<!-- 右侧历史记录栏 -->
			<div class="flex-1 flex flex-col bg-white dark:bg-gray-800">
				<!-- 搜索栏 -->
				<div class="p-4 border-b border-gray-200 dark:border-gray-600">
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-3">
							<h2 class="text-xl font-semibold">任务历史</h2>
							<span
								class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700 dark:from-purple-900/30 dark:to-blue-900/30 dark:text-purple-300"
							>
								🎨 即梦涂抹消除
							</span>
						</div>
						<button
							on:click={loadUserData}
							class="text-blue-600 hover:text-blue-700 text-sm"
							disabled={loadingData}
						>
							{#if loadingData}
								<Spinner className="size-4" />
							{:else}
								刷新
							{/if}
						</button>
					</div>
				</div>

				<!-- 历史记录列表 -->
				<div class="flex-1 p-4 overflow-y-auto scrollbar-hide">
					{#if taskHistory.length === 0}
						<div class="text-center text-gray-500 py-8">
							<div class="text-lg mb-2">暂无历史记录</div>
							<div class="text-sm">开始你的第一个图像涂抹消除任务吧</div>
						</div>
					{:else}
						<div class="space-y-3">
							{#each taskHistory as task}
								<div class="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
									<!-- 任务头部：状态、标签、时间 -->
									<div class="flex items-center justify-between mb-3">
										<div class="flex items-center gap-2">
											<!-- 功能标签 -->
											<span
												class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700 dark:from-purple-900/30 dark:to-blue-900/30 dark:text-purple-300"
											>
												🎨 涂抹消除
											</span>
											<!-- 状态标签 -->
											<div class="text-sm {getStatusColor(task.status)} font-medium">
												{getStatusText(task.status)}
											</div>
										</div>
										<div class="text-xs text-gray-500">
											{formatDate(task.createdAt || task.created_at)}
										</div>
									</div>

									<!-- 任务参数信息 -->
									{#if task.steps || task.quality}
										<div class="flex flex-wrap gap-2 mb-2">
											{#if task.steps}
												<span
													class="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300"
												>
													步数: {task.steps}
												</span>
											{/if}
											{#if task.quality}
												<span
													class="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300"
												>
													质量: {task.quality}
												</span>
											{/if}
											{#if task.strength}
												<span
													class="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300"
												>
													强度: {task.strength}
												</span>
											{/if}
										</div>
									{/if}

									{#if task.status === 'completed' && task.result_image_url}
										<div class="mt-3 relative group">
											<img
												src={task.result_image_url}
												alt="涂抹消除结果"
												class="w-full rounded-lg cursor-pointer hover:opacity-80 transition-opacity"
												style="max-height: 200px; object-fit: contain;"
												on:click={() => handleImageClick(task.result_image_url, '涂抹消除结果')}
												title="点击查看大图"
											/>
											<!-- 放大图标提示 -->
											<div
												class="absolute top-2 right-2 bg-black/50 text-white rounded-full p-2 opacity-0 group-hover:opacity-100 transition-opacity"
											>
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path
														stroke-linecap="round"
														stroke-linejoin="round"
														stroke-width="2"
														d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
													></path>
												</svg>
											</div>
										</div>
									{/if}

									{#if task.status === 'failed' && task.fail_reason}
										<div class="mt-2 text-sm text-red-600 dark:text-red-400">
											失败原因: {task.fail_reason}
										</div>
									{/if}

									{#if task.status === 'completed' || task.status === 'failed'}
										<div class="mt-3 flex justify-between items-center">
											<!-- 任务ID -->
											<div class="text-xs text-gray-400 font-mono">
												ID: {task.id?.substring(0, 8)}...
											</div>
											<!-- 删除按钮 -->
											<button
												on:click={() => handleDeleteTask(task.id)}
												class="inline-flex items-center px-3 py-1 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
											>
												🗑️ 删除
											</button>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- 涂抹弹窗 -->
<InpaintingModal
	bind:show={showInpaintingModal}
	imageFile={selectedImageFile}
	isProcessing={isGenerating}
	on:submit={handleInpaintingSubmit}
	on:close={handleModalClose}
/>

<!-- 图片放大模态框 -->
{#if showImageModal}
	<!-- 遮罩层 -->
	<div
		class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
		on:click={closeImageModal}
		on:keydown={(e) => e.key === 'Escape' && closeImageModal()}
		tabindex="-1"
		role="dialog"
		aria-label="图片预览"
	>
		<!-- 模态框内容 -->
		<div
			class="relative max-w-7xl max-h-full w-full h-full flex items-center justify-center"
			on:click|stopPropagation
		>
			<!-- 关闭按钮 -->
			<button
				class="absolute top-4 right-4 z-10 bg-black/50 hover:bg-black/70 text-white rounded-full p-2 transition-colors"
				on:click={closeImageModal}
				title="关闭 (ESC)"
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					></path>
				</svg>
			</button>

			<!-- 加载状态 -->
			{#if imageLoading}
				<div class="flex items-center justify-center">
					<div class="flex items-center space-x-2 text-white">
						<Spinner className="size-8" />
						<span>加载中...</span>
					</div>
				</div>
			{/if}

			<!-- 图片 -->
			<img
				src={selectedImageUrl}
				alt={selectedImageAlt}
				class="max-w-full max-h-full object-contain rounded-lg shadow-2xl {imageLoading
					? 'opacity-0'
					: 'opacity-100'}"
				style="min-width: 200px; min-height: 200px;"
				on:load={handleImageLoad}
				on:error={handleImageError}
			/>

			<!-- 图片信息 -->
			<div class="absolute bottom-4 left-4 bg-black/50 text-white px-3 py-1 rounded-lg text-sm">
				{selectedImageAlt} - 点击空白处或按ESC关闭
			</div>
		</div>
	</div>
{/if}

<style>
	/* Custom styles for canvas */
	canvas {
		border: 1px solid #d1d5db;
	}

	.dark canvas {
		border-color: #4b5563;
	}
</style>
