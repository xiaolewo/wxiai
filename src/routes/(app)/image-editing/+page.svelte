<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { WEBUI_NAME, showSidebar, user } from '$lib/stores';
	import {
		getJimengInpaintingUserConfig,
		submitJimengInpaintingTask,
		getJimengInpaintingTaskStatus,
		getJimengInpaintingHistory,
		deleteJimengInpaintingTask,
		getJimengInpaintingCredits,
		uploadImageForInpainting,
		type JimengInpaintingRequest,
		type JimengInpaintingTask
	} from '$lib/apis/jimeng-inpainting.js';
	import { format } from 'date-fns';
	import { zhCN } from 'date-fns/locale';

	// 导入新组件
	import InpaintingModal from '$lib/components/image-editing/InpaintingModal.svelte';
	import MaskPreview from '$lib/components/image-editing/MaskPreview.svelte';
	import MediaAssetSelector from '$lib/components/media-library/MediaAssetSelector.svelte';
	import { type MediaAsset } from '$lib/apis/media-library';

	const i18n = getContext('i18n');

	// ======================== 状态管理 ========================
	let isLoading = false;
	let serviceConfig: any = null;

	// 用户积分
	let userCredits = 0;
	let loadingCredits = false;

	// 任务状态
	let isGenerating = false;
	let currentTask: JimengInpaintingTask | null = null;
	let generatedImage: JimengInpaintingTask | null = null;

	// 历史记录
	let taskHistory: JimengInpaintingTask[] = [];
	let historyPage = 1;
	let historyLimit = 20;
	let historyTotal = 0;
	let loadingHistory = false;

	// 表单参数
	let uploadedOriginalImageUrl = '';
	let uploadedMaskImageUrl = '';
	let originalImageInput: HTMLInputElement;
	let isUploadingOriginal = false;
	let selectedOriginalImageName = '';

	// 弹窗涂抹相关
	let showInpaintingModal = false;
	let hasMask = false;
	let maskBlob: Blob | null = null;

	// 图片查看相关
	let showImageModal = false;
	let currentImageUrl = '';
	let currentImageTask: JimengInpaintingTask | null = null;

	// 图像处理参数
	let steps = 30;
	let strength = 0.8;
	let scale = 7.0;
	let seed = 0;
	let dilateSize = 15;
	let quality = 'M';

	// 模式和提示词
	let mode = 'remove'; // 'remove' 或 'edit'
	let customPrompt = '';

	let requiredCredits = 30;
	let editCredits = 40;

	type MediaSelectorContext = 'inpainting-original';

	let mediaAssetSelectorOpen = false;
	let mediaAssetSelectorContext: MediaSelectorContext | null = null;
	let mediaAssetSelectorMediaType: 'image' | 'video' | 'all' = 'image';
	let mediaAssetSelectorMultiple = false;

	// 计算当前所需积分
	$: currentRequiredCredits = mode === 'edit' ? editCredits : requiredCredits;

	// ======================== 生命周期 ========================
	onMount(async () => {
		if (!$user) {
			toast.error('请先登录');
			return;
		}

		await loadConfig();
		await loadCredits();
		await loadTaskHistory();
	});

	// ======================== 配置和数据加载 ========================
	const loadConfig = async () => {
		if (!$user?.token) return;

		try {
			const config = await getJimengInpaintingUserConfig($user.token);
			serviceConfig = config;

			if (!config.enabled) {
				toast.error('即梦图像编辑服务未启用，请联系管理员');
				return;
			}

			// 设置默认值
			steps = config.default_steps;
			strength = config.default_strength;
			scale = config.default_scale;
			quality = config.default_quality;
			requiredCredits = config.credits_cost;
			editCredits = config.edit_credits_cost || 40;
		} catch (error) {
			console.error('加载配置失败:', error);
			toast.error('加载配置失败');
		}
	};

	const loadCredits = async () => {
		if (!$user?.token) return;

		loadingCredits = true;
		try {
			const credits = await getJimengInpaintingCredits($user.token);
			userCredits = credits.balance;
		} catch (error) {
			console.error('获取积分失败:', error);
		} finally {
			loadingCredits = false;
		}
	};

	const loadTaskHistory = async () => {
		if (!$user?.token) return;

		loadingHistory = true;
		try {
			const history = await getJimengInpaintingHistory($user.token, historyPage, historyLimit);
			taskHistory = history.data;
			historyTotal = history.total;
		} catch (error) {
			console.error('加载历史记录失败:', error);
		} finally {
			loadingHistory = false;
		}
	};

	// ======================== 任务提交 ========================
	const handleGenerate = async () => {
		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		if (!serviceConfig?.enabled) {
			toast.error('服务未启用');
			return;
		}

		// 验证图片和遮罩
		if (!uploadedOriginalImageUrl.trim()) {
			toast.error('请先上传原始图片');
			return;
		}
		// 先生成遮罩
		if (!uploadedMaskImageUrl.trim()) {
			await generateMask();
			if (!uploadedMaskImageUrl.trim()) {
				toast.error('请先在图片上涂抹需要消除的区域');
				return;
			}
		}

		// 验证编辑模式的提示词
		if (mode === 'edit' && !customPrompt.trim()) {
			toast.error('编辑模式需要输入提示词');
			return;
		}

		// 检查积分
		if (userCredits < currentRequiredCredits) {
			toast.error(`积分不足，需要 ${currentRequiredCredits} 积分`);
			return;
		}

		isGenerating = true;

		try {
			const request: JimengInpaintingRequest = {
				original_image_url: uploadedOriginalImageUrl.trim(),
				mask_image_url: uploadedMaskImageUrl.trim(),
				mode: mode,
				custom_prompt: mode === 'edit' ? customPrompt.trim() : undefined,
				steps: steps,
				strength: strength,
				scale: scale,
				seed: seed,
				dilate_size: dilateSize,
				quality: quality,
				return_url: true
			};

			console.log(`🎨 【即梦${mode === 'edit' ? '涂抹编辑' : '涂抹消除'}】提交任务:`, request);

			const result = await submitJimengInpaintingTask($user.token, request);

			if (result.success) {
				toast.success('任务提交成功，正在处理中...');

				// 即梦API直接返回结果，获取任务状态
				try {
					const task = await getJimengInpaintingTaskStatus($user.token, result.task_id);
					generatedImage = task;

					if (task.status === 'succeed') {
						toast.success('图像编辑完成！');
					} else if (task.status === 'failed') {
						toast.error(`处理失败: ${task.fail_reason || '未知错误'}`);
					}

					// 刷新积分和历史记录
					await loadCredits();
					await loadTaskHistory();
				} catch (statusError) {
					console.error('获取任务状态失败:', statusError);
					toast.error('任务状态获取失败，请查看历史记录');
				}
			} else {
				toast.error('任务提交失败');
			}
		} catch (error: any) {
			console.error('提交任务失败:', error);
			toast.error(error.message || '提交任务失败');
		} finally {
			isGenerating = false;
		}
	};

	// ======================== 弹窗涂抹功能 ========================

	const handleStartInpainting = () => {
		if (!uploadedOriginalImageUrl) {
			toast.error('请先上传原始图片');
			return;
		}
		showInpaintingModal = true;
	};

	const handleInpaintingModalConfirm = async (event: CustomEvent) => {
		const { maskBlob } = event.detail;

		if (!maskBlob || !$user?.token) {
			showInpaintingModal = false;
			return;
		}

		try {
			// 蒙版blob已通过事件参数获得，直接使用

			// 上传蒙版到服务器
			const file = new File([maskBlob], 'mask.png', { type: 'image/png' });
			const result = await uploadImageForInpainting($user.token, file);

			if (result.success && result.image_url) {
				uploadedMaskImageUrl = result.image_url;
				hasMask = true;
				toast.success('蒙版创建成功');
				console.log('🎨 蒙版生成并上传成功:', result.image_url);
			} else {
				throw new Error(result.message || '上传失败');
			}
		} catch (error: any) {
			console.error('生成蒙版失败:', error);
			toast.error(error.message || '生成蒙版失败');
		}

		showInpaintingModal = false;
	};

	const handleInpaintingModalClose = () => {
		showInpaintingModal = false;
	};

	const handleEditMask = () => {
		// 重新打开涂抹弹窗编辑蒙版
		showInpaintingModal = true;
	};

	const handleClearMask = () => {
		// 清除蒙版相关数据
		hasMask = false;
		maskBlob = null;
		uploadedMaskImageUrl = '';
		toast.success('蒙版已清除');
	};

	const generateMask = async () => {
		// 这个函数现在由弹窗涂抹流程处理，保留用于兼容性
		if (!hasMask || !uploadedMaskImageUrl) {
			toast.error('请先创建蒙版');
			return;
		}
		// 蒙版已经在弹窗确认时上传，无需重复操作
	};

	// ======================== 媒体库选择 ========================

	function openMediaAssetSelector(
		context: MediaSelectorContext,
		mediaType: 'image' | 'video' | 'all' = 'image',
		multiple = false
	) {
		if (!$user?.token) {
			toast.error('请先登录后再选择媒体资源');
			return;
		}
		mediaAssetSelectorContext = context;
		mediaAssetSelectorMediaType = mediaType;
		mediaAssetSelectorMultiple = multiple;
		mediaAssetSelectorOpen = true;
	}

	const handleMediaAssetSelection = (assets: MediaAsset[]) => {
		mediaAssetSelectorOpen = false;
		if (!assets?.length || !mediaAssetSelectorContext) {
			mediaAssetSelectorContext = null;
			return;
		}

		const asset = assets[0];
		const url = asset.file?.cloud_url;
		if (!url) {
			toast.error('所选素材缺少可用链接');
			mediaAssetSelectorContext = null;
			return;
		}

		switch (mediaAssetSelectorContext) {
			case 'inpainting-original': {
				uploadedOriginalImageUrl = url;
				selectedOriginalImageName = asset.display_name ?? asset.id;
				if (originalImageInput) {
					originalImageInput.value = '';
				}
				hasMask = false;
				maskBlob = null;
				uploadedMaskImageUrl = '';
				toast.success('已选择媒体库图片');
				break;
			}
		}

		mediaAssetSelectorContext = null;
	};

	// ======================== 文件处理 ========================

	const handleOriginalImageUpload = async (event: Event) => {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) return;
		selectedOriginalImageName = '';

		// 检查文件类型
		if (!file.type.startsWith('image/')) {
			toast.error('请选择图片文件');
			return;
		}

		// 检查文件大小（5MB）
		if (file.size > 5 * 1024 * 1024) {
			toast.error('图片文件不能超过5MB');
			return;
		}

		isUploadingOriginal = true;
		try {
			if (!$user?.token) {
				toast.error('请先登录');
				return;
			}

			const result = await uploadImageForInpainting($user.token, file);

			if (result.success && result.image_url) {
				uploadedOriginalImageUrl = result.image_url;
				selectedOriginalImageName = file.name;
				hasMask = false;
				maskBlob = null;
				uploadedMaskImageUrl = '';
				toast.success('原始图片上传成功');
				console.log('🎨 原始图片上传成功:', result.image_url);
			} else {
				throw new Error(result.message || '上传失败');
			}
		} catch (error: any) {
			console.error('上传原始图片失败:', error);
			toast.error(error.message || '上传原始图片失败');
		} finally {
			isUploadingOriginal = false;
		}
	};

	// ======================== 历史记录操作 ========================
	const handleDeleteTask = async (taskId: string) => {
		if (!$user?.token) return;

		if (!confirm('确定要删除这个任务吗？')) return;

		try {
			const success = await deleteJimengInpaintingTask($user.token, taskId);
			if (success) {
				toast.success('任务已删除');
				await loadTaskHistory();
			} else {
				toast.error('删除失败');
			}
		} catch (error) {
			console.error('删除任务失败:', error);
			toast.error('删除任务失败');
		}
	};

	const handleViewImage = (task: JimengInpaintingTask) => {
		if (task.cloud_image_url || task.result_image_url) {
			currentImageUrl = task.cloud_image_url || task.result_image_url;
			currentImageTask = task;
			showImageModal = true;
		}
	};

	const handleDownloadImage = async (task: JimengInpaintingTask) => {
		const imageUrl = task.cloud_image_url || task.result_image_url;
		if (!imageUrl) {
			toast.error('没有可下载的图片');
			return;
		}

		try {
			// 创建一个临时的a标签来触发下载
			const link = document.createElement('a');
			link.href = imageUrl;
			link.download = `jimeng-inpainting-${task.id}-${formatDate(task.created_at).replace(/[:\s]/g, '-')}.jpg`;
			link.target = '_blank';

			// 对于跨域图片，我们需要先下载到blob再下载
			const response = await fetch(imageUrl);
			if (response.ok) {
				const blob = await response.blob();
				const blobUrl = URL.createObjectURL(blob);
				link.href = blobUrl;
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
				URL.revokeObjectURL(blobUrl);
				toast.success('图片下载已开始');
			} else {
				// 如果fetch失败，尝试直接下载
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
			}
		} catch (error) {
			console.error('下载图片失败:', error);
			// 降级处理：在新标签页打开图片
			window.open(imageUrl, '_blank');
			toast.info('已在新标签页打开图片，可右键保存');
		}
	};

	const handleCloseImageModal = () => {
		showImageModal = false;
		currentImageUrl = '';
		currentImageTask = null;
	};

	// ======================== 工具函数 ========================
	const formatDate = (dateString: string) => {
		try {
			return format(new Date(dateString), 'MM-dd HH:mm', { locale: zhCN });
		} catch {
			return dateString;
		}
	};

	const getStatusText = (status: string) => {
		const statusMap = {
			submitted: '已提交',
			processing: '处理中',
			succeed: '已完成',
			failed: '失败'
		};
		return statusMap[status as keyof typeof statusMap] || status;
	};

	const getStatusColor = (status: string) => {
		const colorMap = {
			submitted: 'text-blue-600 bg-blue-50',
			processing: 'text-yellow-600 bg-yellow-50',
			succeed: 'text-green-600 bg-green-50',
			failed: 'text-red-600 bg-red-50'
		};
		return colorMap[status as keyof typeof colorMap] || 'text-gray-600 bg-gray-50';
	};
</script>

<svelte:head>
	<title>
		图像编辑 • {$WEBUI_NAME}
	</title>
</svelte:head>

<div
	class="relative flex w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-260px)]'
		: ''} max-w-full bg-gray-50 dark:bg-gray-900"
>
	<!-- 主体内容 - 左右分栏：左侧操作栏，右侧历史记录栏 -->
	<div class="flex w-full h-full">
		<!-- 左侧操作栏 -->
		<div
			class="w-80 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-600 overflow-y-auto scrollbar-hide"
		>
			<div class="p-4 space-y-4">
				<!-- 标题 -->
				<div>
					<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">🎨 图像编辑</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						AI智能图像编辑，支持涂抹消除和创意编辑
					</p>
				</div>

				<!-- 积分显示 -->
				{#if loadingCredits}
					<div class="text-center py-2">
						<div
							class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"
						></div>
					</div>
				{:else}
					<div
						class="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-600"
					>
						<div class="flex items-center justify-between">
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400"> 当前积分 </span>
							<span class="text-sm font-bold text-blue-600 dark:text-blue-400">
								{userCredits}
							</span>
						</div>
						<div class="flex items-center justify-between mt-1">
							<span class="text-xs text-gray-400"> 消耗积分 </span>
							<span class="text-xs text-gray-600 dark:text-gray-400">
								{currentRequiredCredits}
							</span>
						</div>
					</div>
				{/if}

				<!-- 模式选择 -->
				<div
					class="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-600"
				>
					<div class="mb-2">
						<span class="text-xs font-medium text-gray-700 dark:text-gray-300"> 功能模式 </span>
					</div>
					<div class="space-y-2">
						<label class="flex items-center cursor-pointer">
							<input type="radio" bind:group={mode} value="remove" class="mr-2 text-blue-600" />
							<div class="flex-1">
								<div class="text-sm font-medium text-gray-700 dark:text-gray-300">🧹 涂抹消除</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">
									去除图片中的不需要元素（{requiredCredits} 积分）
								</div>
							</div>
						</label>
						<label class="flex items-center cursor-pointer">
							<input type="radio" bind:group={mode} value="edit" class="mr-2 text-blue-600" />
							<div class="flex-1">
								<div class="text-sm font-medium text-gray-700 dark:text-gray-300">✨ 涂抹编辑</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">
									根据提示词生成新内容（{editCredits} 积分）
								</div>
							</div>
						</label>
					</div>

					<!-- 提示词输入框 - 仅在编辑模式下显示 -->
					{#if mode === 'edit'}
						<div class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
								提示词 <span class="text-red-500">*</span>
							</label>
							<textarea
								bind:value={customPrompt}
								placeholder="描述您想要生成的内容，例如：一只小狗、美丽的花朵、蓝天白云等..."
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
								rows="3"
							></textarea>
							<div class="text-xs text-gray-500 mt-1">建议控制在100字以内，内容简洁准确</div>
						</div>
					{/if}
				</div>

				<!-- 图片上传区域 -->
				<div class="space-y-4">
					<!-- 原始图片上传 -->
					<div>
						<div class="mb-2 flex items-center justify-between gap-2">
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300">
								原始图片（JPG/PNG，最大5MB）
							</label>
							<button
								type="button"
								on:click={() => openMediaAssetSelector('inpainting-original', 'image')}
								class="rounded-md border border-blue-200 px-2.5 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 dark:border-blue-500/40 dark:text-blue-200 dark:hover:bg-blue-900/40"
							>
								从媒体库选择
							</button>
						</div>
						<input
							type="file"
							accept="image/jpeg,image/jpg,image/png"
							on:change={handleOriginalImageUpload}
							bind:this={originalImageInput}
							disabled={isUploadingOriginal}
							class="w-full text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
						/>
						{#if isUploadingOriginal}
							<div class="mt-2 flex items-center text-xs text-blue-600">
								<div
									class="inline-block animate-spin rounded-full h-3 w-3 border-b border-blue-600 mr-2"
								></div>
								上传中...
							</div>
						{:else if uploadedOriginalImageUrl}
							<div class="mt-2 text-xs text-green-600">
								✓ 已关联图片：{selectedOriginalImageName || '原始图片上传成功'}
							</div>
							<div class="mt-2">
								<img
									src={uploadedOriginalImageUrl}
									alt="原始图片"
									class="w-full h-32 object-cover rounded-lg border border-gray-200 dark:border-gray-600"
								/>
							</div>
						{/if}
					</div>

					<!-- 蒙版预览区域 -->
					{#if uploadedOriginalImageUrl}
						<MaskPreview
							originalImageUrl={uploadedOriginalImageUrl}
							maskImageUrl={uploadedMaskImageUrl}
							{hasMask}
							on:edit-mask={handleStartInpainting}
							on:clear-mask={handleClearMask}
						/>
					{/if}
				</div>

				<!-- 参数调节 -->
				<div class="space-y-3">
					<div class="grid grid-cols-2 gap-2">
						<div>
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
								采样步数
							</label>
							<input
								type="number"
								bind:value={steps}
								min="10"
								max="50"
								class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
							/>
						</div>

						<div>
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
								消除强度
							</label>
							<input
								type="number"
								bind:value={strength}
								min="0.1"
								max="1.0"
								step="0.1"
								class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
							/>
						</div>
					</div>

					<div class="grid grid-cols-2 gap-2">
						<div>
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
								控制程度
							</label>
							<input
								type="number"
								bind:value={scale}
								min="1"
								max="20"
								step="0.5"
								class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
							/>
						</div>

						<div>
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
								质量
							</label>
							<select
								bind:value={quality}
								class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
							>
								<option value="H">高质量</option>
								<option value="M">中等</option>
								<option value="L">快速</option>
							</select>
						</div>
					</div>

					<div>
						<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
							遮罩膨胀半径
						</label>
						<input
							type="number"
							bind:value={dilateSize}
							min="0"
							max="50"
							class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
						/>
						<div class="text-xs text-gray-500 mt-1">增加遮罩范围，确保完全消除目标物体</div>
					</div>

					<div>
						<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
							随机种子 (-1表示随机)
						</label>
						<input
							type="number"
							bind:value={seed}
							min="-1"
							class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
						/>
					</div>
				</div>

				<!-- 生成按钮 -->
				<button
					on:click={handleGenerate}
					disabled={isGenerating || !serviceConfig?.enabled}
					class="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white text-sm font-medium rounded-lg transition-colors duration-200 disabled:cursor-not-allowed flex items-center justify-center"
				>
					{#if isGenerating}
						<div
							class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"
						></div>
						处理中...
					{:else}
						{mode === 'edit' ? '✨ 开始涂抹编辑' : '🧹 开始涂抹消除'}
					{/if}
				</button>

				<!-- 生成结果 -->
				{#if generatedImage && generatedImage.result_image_url}
					<div class="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
						<h4 class="text-xs font-medium text-green-700 dark:text-green-300 mb-2">
							✅ 最新处理结果
						</h4>
						<img
							src={generatedImage.cloud_image_url || generatedImage.result_image_url}
							alt="处理结果"
							class="w-full rounded-lg mb-2"
						/>
						<div class="text-xs text-green-600 dark:text-green-400">
							处理时间：{formatDate(generatedImage.created_at)}
						</div>
					</div>
				{/if}
			</div>
		</div>

		<!-- 右侧历史记录栏 -->
		<div class="flex-1 flex flex-col bg-white dark:bg-gray-800">
			<!-- 搜索栏 -->
			<div class="p-4 border-b border-gray-200 dark:border-gray-600">
				<div class="flex items-center justify-between">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">历史记录</h2>
					<div class="text-sm text-gray-500 dark:text-gray-400">
						共 {historyTotal} 个任务
					</div>
				</div>
			</div>

			<!-- 历史记录列表 -->
			<div class="flex-1 overflow-y-auto">
				{#if loadingHistory && taskHistory.length === 0}
					<div class="p-4 text-center text-gray-500">
						<div
							class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"
						></div>
						<div class="mt-2">加载中...</div>
					</div>
				{:else if taskHistory.length === 0}
					<div class="p-8 text-center text-gray-500">
						<div class="text-4xl mb-4">🎨</div>
						<div class="text-lg font-medium mb-2">暂无任务记录</div>
						<div class="text-sm">开始您的第一个图像编辑任务吧！</div>
					</div>
				{:else}
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
						{#each taskHistory as task}
							<div
								class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
							>
								<!-- 任务头部 -->
								<div class="flex items-center justify-between mb-2">
									<div class="flex items-center space-x-2">
										<span
											class={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(task.status)}`}
										>
											{getStatusText(task.status)}
										</span>
									</div>
									<button
										on:click={() => handleDeleteTask(task.id)}
										class="text-gray-400 hover:text-red-500 text-sm p-1"
										title="删除任务"
									>
										🗑️
									</button>
								</div>

								<!-- 任务内容区域 -->
								<div class="space-y-3">
									<!-- 图片预览 -->
									{#if task.result_image_url || task.cloud_image_url}
										<div class="w-full relative group">
											<img
												src={task.cloud_image_url || task.result_image_url}
												alt="处理结果"
												class="w-full aspect-square rounded-lg bg-black object-cover cursor-pointer transition-all duration-200 group-hover:brightness-75"
												on:click={() => handleViewImage(task)}
											/>
											<!-- 悬浮操作按钮 -->
											<div
												class="absolute inset-0 flex items-center justify-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded-lg"
											>
												<button
													on:click|stopPropagation={() => handleViewImage(task)}
													class="p-2 bg-white/90 hover:bg-white text-gray-700 rounded-full shadow-lg transition-all duration-200 hover:scale-110"
													title="查看大图"
												>
													<svg
														class="w-5 h-5"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
														/>
													</svg>
												</button>
												<button
													on:click|stopPropagation={() => handleDownloadImage(task)}
													class="p-2 bg-white/90 hover:bg-white text-gray-700 rounded-full shadow-lg transition-all duration-200 hover:scale-110"
													title="下载图片"
												>
													<svg
														class="w-5 h-5"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z"
														/>
													</svg>
												</button>
											</div>
										</div>
									{:else}
										<div
											class="w-full aspect-square bg-gray-200 dark:bg-gray-600 rounded-lg flex items-center justify-center"
										>
											<div class="text-center">
												{#if task.status === 'processing'}
													<div class="text-3xl mb-2">⏳</div>
													<div class="text-sm text-gray-500">处理中...</div>
													<div class="text-xs text-gray-400 mt-1">{task.progress || '0%'}</div>
												{:else if task.status === 'failed'}
													<div class="text-3xl mb-2">❌</div>
													<div class="text-sm text-gray-500">处理失败</div>
													{#if task.fail_reason}
														<div class="text-xs text-gray-400 mt-1">{task.fail_reason}</div>
													{/if}
												{:else if task.status === 'submitted'}
													<div class="text-3xl mb-2">📤</div>
													<div class="text-sm text-gray-500">已提交</div>
												{:else}
													<div class="text-3xl mb-2">🎨</div>
													<div class="text-sm text-gray-500">等待处理</div>
												{/if}
											</div>
										</div>
									{/if}

									<!-- 任务详情 -->
									<div class="space-y-2">
										<!-- 模式显示 -->
										<div class="text-xs">
											<span
												class={`px-2 py-1 rounded-full font-medium ${task.mode === 'edit' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'}`}
											>
												{task.mode === 'edit' ? '✨ 涂抹编辑' : '🧹 涂抹消除'}
											</span>
										</div>

										<!-- 提示词显示 -->
										{#if task.mode === 'edit' && task.custom_prompt}
											<div
												class="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-600 rounded p-2"
											>
												<div class="font-medium mb-1">提示词:</div>
												<div class="italic">"{task.custom_prompt}"</div>
											</div>
										{/if}

										<!-- 参数信息 -->
										<div class="text-sm text-gray-600 dark:text-gray-400">
											<div>步数: {task.steps} | 强度: {task.strength}</div>
											<div>质量: {task.quality} | 膨胀: {task.dilate_size}</div>
										</div>

										<!-- 底部信息 -->
										<div
											class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-600"
										>
											<span>⏰ {formatDate(task.created_at)}</span>
											<span>💰 {task.credits_cost} 积分</span>
										</div>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<!-- 涂抹弹窗 -->
<InpaintingModal
	bind:show={showInpaintingModal}
	originalImageUrl={uploadedOriginalImageUrl}
	on:confirm={handleInpaintingModalConfirm}
	on:close={handleInpaintingModalClose}
/>

<!-- 图片查看弹窗 -->
{#if showImageModal && currentImageUrl}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
		on:click={handleCloseImageModal}
	>
		<div
			class="relative max-w-[95vw] max-h-[95vh] flex flex-col bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden"
		>
			<!-- 弹窗头部 -->
			<div
				class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700"
			>
				<div>
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white">查看大图</h3>
					{#if currentImageTask}
						<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
							任务ID: {currentImageTask.id} | {formatDate(currentImageTask.created_at)}
						</p>
					{/if}
				</div>
				<div class="flex items-center gap-2">
					{#if currentImageTask}
						<button
							on:click|stopPropagation={() => handleDownloadImage(currentImageTask)}
							class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition"
							title="下载图片"
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z"
								/>
							</svg>
						</button>
					{/if}
					<button
						on:click={handleCloseImageModal}
						class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg text-xl transition"
					>
						×
					</button>
				</div>
			</div>

			<!-- 图片显示区域 -->
			<div class="flex-1 p-6 flex items-center justify-center min-h-0 bg-gray-100 dark:bg-gray-900">
				<img
					src={currentImageUrl}
					alt="处理结果大图"
					class="max-w-full max-h-[calc(95vh-190px)] object-contain rounded-lg shadow-lg"
					on:click|stopPropagation
					crossorigin="anonymous"
				/>
			</div>

			<!-- 图片信息 -->
			{#if currentImageTask}
				<div
					class="px-6 py-4 border-t border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700"
				>
					<div
						class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 dark:text-gray-400"
					>
						<div>
							<span class="font-medium">步数:</span>
							{currentImageTask.steps}
						</div>
						<div>
							<span class="font-medium">强度:</span>
							{currentImageTask.strength}
						</div>
						<div>
							<span class="font-medium">质量:</span>
							{currentImageTask.quality}
						</div>
						<div>
							<span class="font-medium">积分:</span>
							{currentImageTask.credits_cost}
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}

<MediaAssetSelector
	token={$user?.token ?? ''}
	open={mediaAssetSelectorOpen}
	mediaType={mediaAssetSelectorMediaType}
	multiple={mediaAssetSelectorMultiple}
	on:close={() => {
		mediaAssetSelectorOpen = false;
		mediaAssetSelectorContext = null;
	}}
	on:confirm={({ detail }) => handleMediaAssetSelection(detail)}
/>
