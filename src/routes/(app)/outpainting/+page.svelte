<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { WEBUI_NAME, showSidebar, user } from '$lib/stores';
	import {
		getJimengOutpaintingUserConfig,
		submitJimengOutpaintingTask,
		getJimengOutpaintingTaskStatus,
		getJimengOutpaintingHistory,
		deleteJimengOutpaintingTask,
		getJimengOutpaintingCredits,
		uploadImageForOutpainting,
		type JimengOutpaintingRequest,
		type JimengOutpaintingTask
	} from '$lib/apis/jimeng-outpainting.js';
	import { format } from 'date-fns';
	import { zhCN } from 'date-fns/locale';

	// 导入组件
	import OutpaintingPreview from '$lib/components/outpainting/OutpaintingPreview.svelte';
	import CanvasEditor from '$lib/components/outpainting/CanvasEditor.svelte';

	const i18n = getContext('i18n');

	// ======================== 状态管理 ========================
	let isLoading = false;
	let serviceConfig: any = null;

	// 用户积分
	let userCredits = 0;
	let loadingCredits = false;

	// 任务状态
	let isGenerating = false;
	let currentTask: JimengOutpaintingTask | null = null;
	let generatedImage: JimengOutpaintingTask | null = null;

	// 历史记录
	let taskHistory: JimengOutpaintingTask[] = [];
	let historyPage = 1;
	let historyLimit = 20;
	let historyTotal = 0;
	let loadingHistory = false;

	// 表单参数
	let uploadedImageUrl = '';
	let originalImageInput: HTMLInputElement;
	let isUploadingImage = false;

	// 扩图模式和参数
	let expansionMode = 'equal'; // equal/aspect/custom/canvas
	let customPrompt = '';

	// 扩展参数
	let top = 0.1;
	let bottom = 0.1;
	let left = 0.1;
	let right = 0.1;

	// 预设比例
	let aspectRatio = '16:9'; // 1:1, 4:3, 16:9, 9:16

	// 生成参数
	let steps = 30;
	let strength = 0.8;
	let scale = 7.0;
	let seed = 0;
	let quality = 'M';
	let maxWidth = 1920;
	let maxHeight = 1920;

	// Canvas编辑器相关
	let showCanvasEditor = false;
	let canvasImageUrl = '';
	let canvasData: any = null;

	// 图片查看相关
	let showImageModal = false;
	let currentImageUrl = '';
	let currentImageTask: JimengOutpaintingTask | null = null;

	let requiredCredits = 25;

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
			const config = await getJimengOutpaintingUserConfig($user.token);
			serviceConfig = config;

			if (!config.enabled) {
				toast.error('即梦智能扩图服务未启用，请联系管理员');
				return;
			}

			// 设置默认值
			steps = config.default_steps;
			strength = config.default_strength;
			scale = config.default_scale;
			quality = config.default_quality;
			maxWidth = config.default_max_width;
			maxHeight = config.default_max_height;
			requiredCredits = config.credits_cost;
		} catch (error) {
			console.error('加载配置失败:', error);
			toast.error('加载配置失败');
		}
	};

	const loadCredits = async () => {
		if (!$user?.token) return;

		loadingCredits = true;
		try {
			const credits = await getJimengOutpaintingCredits($user.token);
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
			const history = await getJimengOutpaintingHistory($user.token, historyPage, historyLimit);
			taskHistory = history.data;
			historyTotal = history.total;
		} catch (error) {
			console.error('加载历史记录失败:', error);
		} finally {
			loadingHistory = false;
		}
	};

	// ======================== 扩展模式处理 ========================
	const handleModeChange = () => {
		if (expansionMode === 'equal') {
			// 等比扩展 - 四边相同比例
			const ratio = 0.2;
			top = bottom = left = right = ratio;
		} else if (expansionMode === 'aspect') {
			// 画幅扩展 - 根据预设比例计算
			calculateAspectRatio();
		} else if (expansionMode === 'custom') {
			// 自定义扩展 - 保持当前值
		} else if (expansionMode === 'canvas') {
			// 画布模式 - 打开画布编辑器
			if (uploadedImageUrl) {
				openCanvasEditor();
			} else {
				toast.error('请先上传图片');
				expansionMode = 'equal';
			}
		}
	};

	const calculateAspectRatio = () => {
		// 根据选择的画幅比例计算扩展参数
		const ratios = {
			'1:1': { w: 1, h: 1 },
			'4:3': { w: 4, h: 3 },
			'16:9': { w: 16, h: 9 },
			'9:16': { w: 9, h: 16 }
		};

		const ratio = ratios[aspectRatio];
		if (!ratio) return;

		// 假设原图为正方形，计算需要的扩展
		// 简化处理：主要在宽度或高度方向扩展
		if (ratio.w > ratio.h) {
			// 横图，主要扩展左右
			left = right = 0.3;
			top = bottom = 0.1;
		} else if (ratio.w < ratio.h) {
			// 竖图，主要扩展上下
			top = bottom = 0.3;
			left = right = 0.1;
		} else {
			// 正方形
			top = bottom = left = right = 0.1;
		}
	};

	// ======================== 画布编辑器 ========================
	const openCanvasEditor = () => {
		canvasImageUrl = uploadedImageUrl;
		showCanvasEditor = true;
	};

	const handleCanvasConfirm = (event: CustomEvent) => {
		canvasData = event.detail;
		showCanvasEditor = false;
		toast.success('画布设置已保存');
	};

	const handleCanvasClose = () => {
		showCanvasEditor = false;
		if (expansionMode === 'canvas') {
			expansionMode = 'equal'; // 取消时回到等比模式
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

		if (!uploadedImageUrl.trim()) {
			toast.error('请先上传原始图片');
			return;
		}

		// 检查积分
		if (userCredits < requiredCredits) {
			toast.error(`积分不足，需要 ${requiredCredits} 积分`);
			return;
		}

		isGenerating = true;

		try {
			const request: JimengOutpaintingRequest = {
				original_image_url: uploadedImageUrl.trim(),
				expansion_mode: expansionMode,
				custom_prompt: customPrompt.trim() || '蓝色的海洋',
				top: top,
				bottom: bottom,
				left: left,
				right: right,
				steps: steps,
				strength: strength,
				scale: scale,
				seed: seed,
				quality: quality,
				max_width: maxWidth,
				max_height: maxHeight,
				return_url: true
			};

			// 画布模式需要额外参数
			if (expansionMode === 'canvas' && canvasData) {
				request.mask_image_url = canvasData.maskImageUrl;
			}

			console.log('🎨 【即梦智能扩图】提交任务:', request);

			const result = await submitJimengOutpaintingTask($user.token, request);

			if (result.success) {
				toast.success('任务提交成功，正在处理中...');

				// 获取任务状态
				try {
					const task = await getJimengOutpaintingTaskStatus($user.token, result.task_id);
					generatedImage = task;

					if (task.status === 'succeed') {
						toast.success('智能扩图完成！');
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

	// ======================== 文件处理 ========================
	const handleImageUpload = async (event: Event) => {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) return;

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

		isUploadingImage = true;
		try {
			if (!$user?.token) {
				toast.error('请先登录');
				return;
			}

			const result = await uploadImageForOutpainting($user.token, file);

			if (result.success && result.image_url) {
				uploadedImageUrl = result.image_url;
				toast.success('图片上传成功');
				console.log('🎨 图片上传成功:', result.image_url);
			} else {
				throw new Error(result.message || '上传失败');
			}
		} catch (error: any) {
			console.error('上传图片失败:', error);
			toast.error(error.message || '上传图片失败');
		} finally {
			isUploadingImage = false;
		}
	};

	// ======================== 历史记录操作 ========================
	const handleDeleteTask = async (taskId: string) => {
		if (!$user?.token) return;

		if (!confirm('确定要删除这个任务吗？')) return;

		try {
			const success = await deleteJimengOutpaintingTask($user.token, taskId);
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

	const handleViewImage = (task: JimengOutpaintingTask) => {
		if (task.cloud_image_url || task.result_image_url) {
			currentImageUrl = task.cloud_image_url || task.result_image_url;
			currentImageTask = task;
			showImageModal = true;
		}
	};

	const handleDownloadImage = async (task: JimengOutpaintingTask) => {
		const imageUrl = task.cloud_image_url || task.result_image_url;
		if (!imageUrl) {
			toast.error('没有可下载的图片');
			return;
		}

		try {
			const response = await fetch(imageUrl);
			if (response.ok) {
				const blob = await response.blob();
				const blobUrl = URL.createObjectURL(blob);
				const link = document.createElement('a');
				link.href = blobUrl;
				link.download = `jimeng-outpainting-${task.id}-${formatDate(task.created_at).replace(/[:\s]/g, '-')}.jpg`;
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
				URL.revokeObjectURL(blobUrl);
				toast.success('图片下载已开始');
			} else {
				window.open(imageUrl, '_blank');
			}
		} catch (error) {
			console.error('下载图片失败:', error);
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

	const getModeText = (mode: string) => {
		const modeMap = {
			equal: '🔄 等比扩展',
			aspect: '📐 画幅扩展',
			custom: '🎯 四边扩展',
			canvas: '🎨 画布扩展'
		};
		return modeMap[mode as keyof typeof modeMap] || mode;
	};
</script>

<svelte:head>
	<title>
		智能扩图 • {$WEBUI_NAME}
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
					<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">🎨 智能扩图</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						AI智能扩展图片尺寸，支持多种扩展模式
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
								{requiredCredits}
							</span>
						</div>
					</div>
				{/if}

				<!-- 扩展模式选择 -->
				<div
					class="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-600"
				>
					<div class="mb-2">
						<span class="text-xs font-medium text-gray-700 dark:text-gray-300"> 扩展模式 </span>
					</div>
					<div class="space-y-2">
						<label class="flex items-center cursor-pointer">
							<input
								type="radio"
								bind:group={expansionMode}
								value="equal"
								on:change={handleModeChange}
								class="mr-2 text-blue-600"
							/>
							<div class="flex-1">
								<div class="text-sm font-medium text-gray-700 dark:text-gray-300">🔄 等比扩展</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">以图片中心等比扩展四边</div>
							</div>
						</label>
						<label class="flex items-center cursor-pointer">
							<input
								type="radio"
								bind:group={expansionMode}
								value="aspect"
								on:change={handleModeChange}
								class="mr-2 text-blue-600"
							/>
							<div class="flex-1">
								<div class="text-sm font-medium text-gray-700 dark:text-gray-300">📐 画幅扩展</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">扩展为指定画幅比例</div>
							</div>
						</label>
						<label class="flex items-center cursor-pointer">
							<input
								type="radio"
								bind:group={expansionMode}
								value="custom"
								on:change={handleModeChange}
								class="mr-2 text-blue-600"
							/>
							<div class="flex-1">
								<div class="text-sm font-medium text-gray-700 dark:text-gray-300">🎯 四边扩展</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">自定义设置各边扩展比例</div>
							</div>
						</label>
						<label class="flex items-center cursor-pointer">
							<input
								type="radio"
								bind:group={expansionMode}
								value="canvas"
								on:change={handleModeChange}
								class="mr-2 text-blue-600"
							/>
							<div class="flex-1">
								<div class="text-sm font-medium text-gray-700 dark:text-gray-300">🎨 画布扩展</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">在画布中自定义图片位置</div>
							</div>
						</label>
					</div>

					<!-- 画幅比例选择 -->
					{#if expansionMode === 'aspect'}
						<div class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
								目标画幅
							</label>
							<select
								bind:value={aspectRatio}
								on:change={calculateAspectRatio}
								class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
							>
								<option value="1:1">1:1 正方形</option>
								<option value="4:3">4:3 传统</option>
								<option value="16:9">16:9 宽屏</option>
								<option value="9:16">9:16 竖屏</option>
							</select>
						</div>
					{/if}
				</div>

				<!-- 图片上传区域 -->
				<div class="space-y-4">
					<div>
						<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
							原始图片（JPG/PNG，最大5MB）
						</label>
						<input
							type="file"
							accept="image/jpeg,image/jpg,image/png"
							on:change={handleImageUpload}
							bind:this={originalImageInput}
							disabled={isUploadingImage}
							class="w-full text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
						/>
						{#if isUploadingImage}
							<div class="mt-2 flex items-center text-xs text-blue-600">
								<div
									class="inline-block animate-spin rounded-full h-3 w-3 border-b border-blue-600 mr-2"
								></div>
								上传中...
							</div>
						{:else if uploadedImageUrl}
							<div class="mt-2 text-xs text-green-600">✓ 图片上传成功</div>
							<div class="mt-2">
								<img
									src={uploadedImageUrl}
									alt="原始图片"
									class="w-full h-32 object-cover rounded-lg border border-gray-200 dark:border-gray-600"
								/>
							</div>
						{/if}
					</div>

					<!-- 扩展参数预览 -->
					{#if uploadedImageUrl}
						<OutpaintingPreview
							originalImageUrl={uploadedImageUrl}
							{expansionMode}
							{top}
							{bottom}
							{left}
							{right}
						/>
					{/if}
				</div>

				<!-- 扩展参数调节 -->
				{#if expansionMode === 'custom'}
					<div class="space-y-3">
						<div class="grid grid-cols-2 gap-2">
							<div>
								<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
									向上扩展
								</label>
								<input
									type="number"
									bind:value={top}
									min="0"
									max="1"
									step="0.1"
									class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
								/>
							</div>
							<div>
								<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
									向下扩展
								</label>
								<input
									type="number"
									bind:value={bottom}
									min="0"
									max="1"
									step="0.1"
									class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
								/>
							</div>
						</div>
						<div class="grid grid-cols-2 gap-2">
							<div>
								<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
									向左扩展
								</label>
								<input
									type="number"
									bind:value={left}
									min="0"
									max="1"
									step="0.1"
									class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
								/>
							</div>
							<div>
								<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
									向右扩展
								</label>
								<input
									type="number"
									bind:value={right}
									min="0"
									max="1"
									step="0.1"
									class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
								/>
							</div>
						</div>
					</div>
				{/if}

				<!-- 提示词 -->
				<div>
					<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
						扩展内容描述（可选）
					</label>
					<textarea
						bind:value={customPrompt}
						placeholder="描述您希望在扩展区域生成的内容，例如：蓝色的海洋、绿色的森林等..."
						class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						rows="3"
					></textarea>
					<div class="text-xs text-gray-500 mt-1">留空将使用默认描述</div>
				</div>

				<!-- 高级参数 -->
				<details
					class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600"
				>
					<summary
						class="px-3 py-2 text-xs font-medium text-gray-700 dark:text-gray-300 cursor-pointer"
					>
						高级参数
					</summary>
					<div class="px-3 pb-3 space-y-3">
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
									扩展强度
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
					</div>
				</details>

				<!-- 生成按钮 -->
				<button
					on:click={handleGenerate}
					disabled={isGenerating || !serviceConfig?.enabled || !uploadedImageUrl}
					class="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white text-sm font-medium rounded-lg transition-colors duration-200 disabled:cursor-not-allowed flex items-center justify-center"
				>
					{#if isGenerating}
						<div
							class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"
						></div>
						处理中...
					{:else}
						🎨 开始智能扩图
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
						<div class="text-sm">开始您的第一个智能扩图任务吧！</div>
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
												class="px-2 py-1 rounded-full font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
											>
												{getModeText(task.expansion_mode)}
											</span>
										</div>

										<!-- 提示词显示 -->
										{#if task.custom_prompt}
											<div
												class="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-600 rounded p-2"
											>
												<div class="font-medium mb-1">提示词:</div>
												<div class="italic">"{task.custom_prompt}"</div>
											</div>
										{/if}

										<!-- 扩展参数 -->
										{#if task.expansion_mode === 'custom'}
											<div class="text-xs text-gray-600 dark:text-gray-400">
												<div>扩展: ↑{task.top} ↓{task.bottom} ←{task.left} →{task.right}</div>
											</div>
										{/if}

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

<!-- 画布编辑器弹窗 -->
{#if showCanvasEditor}
	<CanvasEditor
		bind:show={showCanvasEditor}
		originalImageUrl={canvasImageUrl}
		on:confirm={handleCanvasConfirm}
		on:close={handleCanvasClose}
	/>
{/if}

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
							<span class="font-medium">模式:</span>
							{getModeText(currentImageTask.expansion_mode)}
						</div>
						<div>
							<span class="font-medium">步数:</span>
							{currentImageTask.steps}
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
