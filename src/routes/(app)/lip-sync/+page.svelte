<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { WEBUI_NAME, showSidebar, user } from '$lib/stores';
	import {
		getKlingLipSyncUserConfig,
		submitKlingLipSyncTask,
		getKlingLipSyncTaskStatus,
		getKlingLipSyncHistory,
		deleteKlingLipSyncTask,
		getKlingLipSyncCredits,
		uploadVideoForLipSync,
		uploadAudioForLipSync,
		type KlingLipSyncRequest,
		type KlingLipSyncTask,
		type KlingLipSyncMode,
		chineseVoiceOptions,
		englishVoiceOptions,
		getVoiceOptions,
		getVoiceName
	} from '$lib/apis/kling-lip-sync';
	import { format } from 'date-fns';
	import { zhCN } from 'date-fns/locale';
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
	let currentTask: KlingLipSyncTask | null = null;
	let generatedVideo: KlingLipSyncTask | null = null;

	// 历史记录
	let taskHistory: KlingLipSyncTask[] = [];
	let historyPage = 1;
	let historyLimit = 20;
	let historyTotal = 0;
	let loadingHistory = false;

	// 表单参数
	let selectedMode: KlingLipSyncMode = 'text2video';
	let videoUrl = '';
	let videoId = '';
	let videoInputType: 'video_file' | 'video_url' | 'video_id' = 'video_file';
	let videoInput: HTMLInputElement;
	let uploadedVideoUrl = '';
	let selectedMediaVideoName = '';
	let isUploadingVideo = false;

	// 文本转视频参数
	let promptText = '';
	let voiceId = 'genshin_vindi2';
	let voiceLanguage = 'zh';
	let voiceSpeed = 1.0;

	// 音频转视频参数
	let audioFile = '';
	let audioUrl = '';
	let uploadedAudioUrl = '';
	let audioType: 'file' | 'url' = 'file';
	let audioInput: HTMLInputElement;
	let isUploadingAudio = false;

	type MediaSelectorContext = 'lip-video';

	let mediaAssetSelectorOpen = false;
	let mediaAssetSelectorContext: MediaSelectorContext | null = null;
	let mediaAssetSelectorMediaType: 'image' | 'video' | 'all' = 'video';
	let mediaAssetSelectorMultiple = false;

	// 轮询控制
	let pollingInterval: NodeJS.Timeout | null = null;
	let requiredCredits = 50;

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
			const config = await getKlingLipSyncUserConfig($user.token);
			serviceConfig = config;

			if (!config.enabled) {
				toast.error('可灵对口型服务未启用，请联系管理员');
				return;
			}

			// 设置默认值
			voiceId = config.defaultVoiceId;
			voiceLanguage = config.defaultVoiceLanguage;
			voiceSpeed = config.defaultVoiceSpeed;
			requiredCredits = config.creditsCost;
		} catch (error) {
			console.error('加载配置失败:', error);
			toast.error('加载配置失败');
		}
	};

	const loadCredits = async () => {
		if (!$user?.token) return;

		loadingCredits = true;
		try {
			const credits = await getKlingLipSyncCredits($user.token);
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
			const history = await getKlingLipSyncHistory($user.token, historyPage, historyLimit);
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

		// 验证基础参数
		if (videoInputType === 'video_file' && !uploadedVideoUrl.trim()) {
			toast.error('请先上传视频文件');
			return;
		}
		if (videoInputType === 'video_url' && !videoUrl.trim()) {
			toast.error('请输入视频URL');
			return;
		}
		if (videoInputType === 'video_id' && !videoId.trim()) {
			toast.error('请输入视频ID');
			return;
		}

		// 验证模式特定参数
		if (selectedMode === 'text2video') {
			if (!promptText.trim()) {
				toast.error('请输入对口型文本');
				return;
			}
			if (promptText.length > 120) {
				toast.error('文本长度不能超过120个字符');
				return;
			}
		} else if (selectedMode === 'audio2video') {
			if (audioType === 'file' && !uploadedAudioUrl) {
				toast.error('请先上传音频文件');
				return;
			}
			if (audioType === 'url' && !audioUrl.trim()) {
				toast.error('请输入音频URL');
				return;
			}
		}

		// 检查积分
		if (userCredits < requiredCredits) {
			toast.error(`积分不足，需要 ${requiredCredits} 积分`);
			return;
		}

		isGenerating = true;

		try {
			let videoInputValue = '';
			if (videoInputType === 'video_file') {
				videoInputValue = uploadedVideoUrl.trim();
			} else if (videoInputType === 'video_url') {
				videoInputValue = videoUrl.trim();
			} else {
				videoInputValue = videoId.trim();
			}

			const request: KlingLipSyncRequest = {
				mode: selectedMode,
				videoInput: videoInputValue,
				inputType: videoInputType === 'video_file' ? 'video_url' : videoInputType // 上传的文件使用云存储URL，所以传video_url类型
			};

			if (selectedMode === 'text2video') {
				request.text = promptText.trim();
				request.voiceId = voiceId;
				request.voiceLanguage = voiceLanguage;
				request.voiceSpeed = voiceSpeed;
			} else {
				if (audioType === 'file') {
					request.audioUrl = uploadedAudioUrl; // 使用上传后的云存储URL
					request.audioType = 'url'; // 实际上我们使用的是URL方式
				} else {
					request.audioUrl = audioUrl.trim(); // 使用用户输入的URL
					request.audioType = 'url';
				}
			}

			console.log('🎭 【可灵对口型】提交任务:', request);

			const result = await submitKlingLipSyncTask($user.token, request);

			if (result.success) {
				toast.success('任务提交成功');

				// 创建任务记录
				currentTask = {
					id: result.taskId,
					userId: $user.id,
					status: 'submitted',
					mode: selectedMode,
					videoInput: videoInputValue,
					inputType: videoInputType === 'video_file' ? 'video_url' : videoInputType,
					text: selectedMode === 'text2video' ? promptText.trim() : undefined,
					voiceId: selectedMode === 'text2video' ? voiceId : undefined,
					voiceLanguage: selectedMode === 'text2video' ? voiceLanguage : undefined,
					voiceSpeed: selectedMode === 'text2video' ? voiceSpeed : undefined,
					audioFile:
						selectedMode === 'audio2video' && audioType === 'file'
							? uploadedAudioUrl
							: selectedMode === 'audio2video' && audioType === 'url'
								? audioUrl
								: undefined,
					audioType: selectedMode === 'audio2video' ? audioType : undefined,
					creditsCost: requiredCredits,
					progress: '0%',
					createdAt: new Date().toISOString(),
					updatedAt: new Date().toISOString()
				};

				// 开始轮询
				startPolling();

				// 刷新积分和历史记录
				await loadCredits();
				await loadTaskHistory();
			} else {
				toast.error('任务提交失败');
			}
		} catch (error: any) {
			console.error('提交任务失败:', error);
			// 如果是URL验证错误，显示更详细的错误信息
			if (error.message && error.message.includes('视频URL验证失败')) {
				toast.error(error.message, { duration: 6000 });
			} else {
				toast.error(error.message || '提交任务失败');
			}
		} finally {
			if (!currentTask) {
				isGenerating = false;
			}
		}
	};

	// ======================== 任务轮询 ========================
	const startPolling = () => {
		if (pollingInterval) {
			clearInterval(pollingInterval);
		}

		pollingInterval = setInterval(async () => {
			if (!currentTask || !$user?.token) {
				stopPolling();
				return;
			}

			try {
				const task = await getKlingLipSyncTaskStatus($user.token, currentTask.id);
				currentTask = task;

				if (task.status === 'succeed') {
					generatedVideo = task;
					stopPolling();
					isGenerating = false;
					toast.success('对口型视频生成完成！');
					await loadTaskHistory();
				} else if (task.status === 'failed') {
					stopPolling();
					isGenerating = false;
					toast.error(`生成失败: ${task.failReason || '未知错误'}`);
					await loadTaskHistory();
				}
			} catch (error) {
				console.error('轮询任务状态失败:', error);
			}
		}, 3000);
	};

	const stopPolling = () => {
		if (pollingInterval) {
			clearInterval(pollingInterval);
			pollingInterval = null;
		}
	};

	// ======================== 媒体库选择 ========================

	function openMediaAssetSelector(
		context: MediaSelectorContext,
		mediaType: 'image' | 'video' | 'all' = 'video',
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
			case 'lip-video': {
				uploadedVideoUrl = url;
				selectedMediaVideoName = asset.display_name ?? asset.id;
				if (videoInput) {
					videoInput.value = '';
				}
				toast.success('已选择媒体库视频');
				break;
			}
		}

		mediaAssetSelectorContext = null;
	};

	// ======================== 文件处理 ========================

	const handleVideoUpload = async (event: Event) => {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) return;
		selectedMediaVideoName = '';

		// 检查文件类型
		if (!file.type.startsWith('video/')) {
			toast.error('请选择视频文件');
			return;
		}

		// 检查文件大小（100MB）
		if (file.size > 100 * 1024 * 1024) {
			toast.error('视频文件不能超过100MB');
			return;
		}

		isUploadingVideo = true;
		try {
			if (!$user?.token) {
				toast.error('请先登录');
				return;
			}

			const result = await uploadVideoForLipSync($user.token, file);

			if (result.success && result.video_url) {
				uploadedVideoUrl = result.video_url;
				selectedMediaVideoName = file.name;
				toast.success('视频上传成功');
				console.log('🎬 视频上传成功:', result.video_url);
			} else {
				throw new Error(result.message || '上传失败');
			}
		} catch (error: any) {
			console.error('上传视频失败:', error);
			toast.error(error.message || '上传视频失败');
		} finally {
			isUploadingVideo = false;
		}
	};

	const handleAudioUpload = async (event: Event) => {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) return;

		// 检查文件类型 - 包含常见的MIME类型和文件扩展名
		const allowedTypes = [
			'audio/mp3',
			'audio/mpeg',
			'audio/mp4', // MP3格式的不同MIME类型
			'audio/wav',
			'audio/wave',
			'audio/x-wav', // WAV格式
			'audio/m4a',
			'audio/mp4',
			'audio/x-m4a', // M4A格式
			'audio/aac',
			'audio/x-aac' // AAC格式
		];

		const fileName = file.name.toLowerCase();
		const fileExtension = fileName.split('.').pop();
		const allowedExtensions = ['mp3', 'wav', 'm4a', 'aac'];

		// 通过MIME类型或文件扩展名验证
		const isValidType =
			allowedTypes.includes(file.type.toLowerCase()) ||
			(fileExtension && allowedExtensions.includes(fileExtension));

		if (!isValidType) {
			toast.error('请选择支持的音频格式（MP3, WAV, M4A, AAC）');
			return;
		}

		// 检查文件大小（5MB，按照可灵API要求）
		if (file.size > 5 * 1024 * 1024) {
			toast.error('音频文件不能超过5MB');
			return;
		}

		// 上传到云存储
		isUploadingAudio = true;
		try {
			if (!$user?.token) {
				toast.error('请先登录');
				return;
			}

			const result = await uploadAudioForLipSync($user.token, file);

			if (result.success && result.audio_url) {
				uploadedAudioUrl = result.audio_url;
				toast.success('音频上传成功');
				console.log('🎵 音频上传成功:', result.audio_url);
			} else {
				throw new Error(result.message || '上传失败');
			}
		} catch (error: any) {
			console.error('上传音频失败:', error);
			toast.error(error.message || '上传音频失败');
		} finally {
			isUploadingAudio = false;
		}
	};

	// ======================== 历史记录操作 ========================
	const handleDeleteTask = async (taskId: string) => {
		if (!$user?.token) return;

		if (!confirm('确定要删除这个任务吗？')) return;

		try {
			const success = await deleteKlingLipSyncTask($user.token, taskId);
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
			processing: '生成中',
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

	// ======================== 响应式数据 ========================
	$: currentVoiceOptions = getVoiceOptions(voiceLanguage);

	// 当语言切换时，重置音色
	$: if (voiceLanguage) {
		const options = getVoiceOptions(voiceLanguage);
		if (!options.find((opt) => opt.value === voiceId)) {
			voiceId = options[0]?.value || 'genshin_vindi2';
		}
	}
</script>

<svelte:head>
	<title>
		可灵对口型 • {$WEBUI_NAME}
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
					<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">🎭 可灵对口型</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						为您的视频添加逼真的对口型效果
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

				<!-- 生成模式 -->
				<div>
					<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
						生成模式
					</label>
					<div class="space-y-2">
						<label
							class="flex items-start p-2 border border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 {selectedMode ===
							'text2video'
								? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
								: ''}"
						>
							<input type="radio" bind:group={selectedMode} value="text2video" class="mr-2 mt-1" />
							<div>
								<div class="text-xs font-medium text-gray-700 dark:text-gray-300">
									文本转语音对口型
								</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">输入文本生成语音对口型</div>
							</div>
						</label>
						<label
							class="flex items-start p-2 border border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 {selectedMode ===
							'audio2video'
								? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
								: ''}"
						>
							<input type="radio" bind:group={selectedMode} value="audio2video" class="mr-2 mt-1" />
							<div>
								<div class="text-xs font-medium text-gray-700 dark:text-gray-300">
									音频驱动对口型
								</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">上传音频生成对口型</div>
							</div>
						</label>
					</div>
				</div>

				<!-- 视频输入 -->
				<div>
					<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
						视频输入方式
					</label>
					<div class="space-y-3">
						<!-- 输入方式切换 -->
						<div class="flex space-x-4">
							<label class="flex items-center text-xs">
								<input type="radio" bind:group={videoInputType} value="video_file" class="mr-2" />
								上传文件
							</label>
							<label class="flex items-center text-xs">
								<input type="radio" bind:group={videoInputType} value="video_url" class="mr-2" />
								视频URL
							</label>
							<label class="flex items-center text-xs">
								<input type="radio" bind:group={videoInputType} value="video_id" class="mr-2" />
								视频ID
							</label>
						</div>

						<!-- 视频文件上传 -->
						{#if videoInputType === 'video_file'}
							<div>
								<div class="mb-2 flex items-center justify-between gap-2">
									<label class="block text-xs font-medium text-gray-700 dark:text-gray-300">
										视频文件（MP4/MOV，最大100MB）
									</label>
									<button
										type="button"
										on:click={() => openMediaAssetSelector('lip-video', 'video')}
										class="rounded-md border border-blue-200 px-2.5 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 dark:border-blue-500/40 dark:text-blue-200 dark:hover:bg-blue-900/40"
									>
										从媒体库选择
									</button>
								</div>
								<input
									type="file"
									accept="video/mp4,video/mov,video/avi,video/mkv"
									on:change={handleVideoUpload}
									bind:this={videoInput}
									disabled={isUploadingVideo}
									class="w-full text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
								/>
								{#if isUploadingVideo}
									<div class="mt-2 flex items-center text-xs text-blue-600">
										<div
											class="inline-block animate-spin rounded-full h-3 w-3 border-b border-blue-600 mr-2"
										></div>
										上传中...
									</div>
								{:else if uploadedVideoUrl}
									<div class="mt-2 text-xs text-green-600">
										✓ 已关联视频：{selectedMediaVideoName || '视频上传成功'}
									</div>
								{/if}
								<div class="text-xs text-gray-500 mt-1">
									支持格式：MP4/MOV，大小≤100MB，时长2-60秒，分辨率720p/1080p
								</div>
							</div>
						{/if}

						<!-- 视频URL输入 -->
						{#if videoInputType === 'video_url'}
							<div>
								<input
									type="url"
									bind:value={videoUrl}
									placeholder="请输入视频URL，如：https://example.com/video.mp4"
									class="w-full px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
								/>
								<div class="text-xs text-gray-500 mt-1">
									支持格式：MP4/MOV，大小≤100MB，时长2-60秒，分辨率720p/1080p<br />
									<span class="text-orange-600 dark:text-orange-400"
										>⚠️ 请使用域名URL，不支持IP地址、localhost或非标准端口</span
									>
								</div>
							</div>
						{/if}

						<!-- 视频ID输入 -->
						{#if videoInputType === 'video_id'}
							<div>
								<input
									type="text"
									bind:value={videoId}
									placeholder="请输入可灵AI生成的视频ID"
									class="w-full px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
								/>
								<div class="text-xs text-gray-500 mt-1">
									输入可灵平台生成的视频ID，仅支持30天内生成的≤60秒视频
								</div>
							</div>
						{/if}
					</div>
				</div>

				<!-- 文本转视频参数 -->
				{#if selectedMode === 'text2video'}
					<div class="space-y-3">
						<div>
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
								对口型文本（最大120字符）
							</label>
							<textarea
								bind:value={promptText}
								placeholder="请输入要生成对口型的文本内容..."
								maxlength="120"
								class="w-full px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none"
								rows="3"
							></textarea>
							<div class="text-xs text-gray-400 mt-1 text-right">
								{promptText.length}/120
							</div>
						</div>

						<div class="grid grid-cols-2 gap-2">
							<div>
								<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
									语言
								</label>
								<select
									bind:value={voiceLanguage}
									class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
								>
									<option value="zh">中文</option>
									<option value="en">English</option>
								</select>
							</div>

							<div>
								<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
									语速
								</label>
								<select
									bind:value={voiceSpeed}
									class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
								>
									<option value={0.5}>0.5x</option>
									<option value={0.8}>0.8x</option>
									<option value={1.0}>1.0x</option>
									<option value={1.2}>1.2x</option>
									<option value={1.5}>1.5x</option>
								</select>
							</div>
						</div>

						<div>
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
								音色
							</label>
							<select
								bind:value={voiceId}
								class="w-full px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
							>
								{#each currentVoiceOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
						</div>
					</div>
				{/if}

				<!-- 音频转视频参数 -->
				{#if selectedMode === 'audio2video'}
					<div class="space-y-3">
						<div>
							<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
								音频类型
							</label>
							<div class="flex space-x-4">
								<label class="flex items-center text-xs">
									<input type="radio" bind:group={audioType} value="file" class="mr-1" />
									上传文件
								</label>
								<label class="flex items-center text-xs">
									<input type="radio" bind:group={audioType} value="url" class="mr-1" />
									音频URL
								</label>
							</div>
						</div>

						{#if audioType === 'file'}
							<div>
								<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
									音频文件（MP3, WAV, M4A, AAC，最大5MB）
								</label>
								<input
									type="file"
									accept="audio/mp3,audio/wav,audio/m4a,audio/aac"
									on:change={handleAudioUpload}
									bind:this={audioInput}
									disabled={isUploadingAudio}
									class="w-full text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
								/>
								{#if isUploadingAudio}
									<div class="mt-2 flex items-center text-xs text-blue-600">
										<div
											class="inline-block animate-spin rounded-full h-3 w-3 border-b border-blue-600 mr-2"
										></div>
										上传中...
									</div>
								{:else if uploadedAudioUrl}
									<div class="mt-2 text-xs text-green-600">✓ 音频上传成功</div>
								{/if}
							</div>
						{/if}

						{#if audioType === 'url'}
							<div>
								<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
									音频URL
								</label>
								<input
									type="url"
									bind:value={audioUrl}
									placeholder="请输入音频URL，如：https://example.com/audio.mp3"
									class="w-full px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
								/>
								<div class="text-xs text-gray-500 mt-1">支持格式：MP3/WAV/M4A/AAC，大小≤5MB</div>
							</div>
						{/if}
					</div>
				{/if}

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
						生成中...
					{:else}
						🎭 生成对口型视频
					{/if}
				</button>

				<!-- 生成进度 -->
				{#if currentTask && isGenerating}
					<div class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-medium text-blue-700 dark:text-blue-300">
								{getStatusText(currentTask.status)}
							</span>
							<span class="text-xs text-blue-600 dark:text-blue-400">
								{currentTask.progress}
							</span>
						</div>
						<div class="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-1.5">
							<div
								class="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
								style="width: {currentTask.progress}"
							></div>
						</div>
					</div>
				{/if}

				<!-- 生成结果 -->
				{#if generatedVideo && generatedVideo.videoUrl}
					<div class="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
						<h4 class="text-xs font-medium text-green-700 dark:text-green-300 mb-2">
							✅ 最新生成的对口型视频
						</h4>
						<video controls class="w-full rounded-lg mb-2" src={generatedVideo.videoUrl}>
							您的浏览器不支持视频播放
						</video>
						<div class="text-xs text-green-600 dark:text-green-400">
							生成时间：{formatDate(generatedVideo.createdAt)}
							{#if generatedVideo.videoDuration}
								· 时长：{generatedVideo.videoDuration}秒
							{/if}
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
						<div class="text-4xl mb-4">🎭</div>
						<div class="text-lg font-medium mb-2">暂无任务记录</div>
						<div class="text-sm">开始创建您的第一个对口型视频吧！</div>
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
										<span class="text-xs text-gray-500 dark:text-gray-400">
											{#if task.mode === 'text2video'}
												📝 文本对口型
											{:else}
												🎵 音频对口型
											{/if}
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
									<!-- 视频预览 -->
									{#if task.videoUrl}
										<div class="w-full">
											<video
												controls
												class="w-full aspect-video rounded-lg bg-black"
												src={task.videoUrl}
												poster=""
											>
												您的浏览器不支持视频播放
											</video>
										</div>
									{:else}
										<div
											class="w-full aspect-video bg-gray-200 dark:bg-gray-600 rounded-lg flex items-center justify-center"
										>
											<div class="text-center">
												{#if task.status === 'processing'}
													<div class="text-3xl mb-2">⏳</div>
													<div class="text-sm text-gray-500">生成中...</div>
													<div class="text-xs text-gray-400 mt-1">{task.progress || '0%'}</div>
												{:else if task.status === 'failed'}
													<div class="text-3xl mb-2">❌</div>
													<div class="text-sm text-gray-500">生成失败</div>
													{#if task.failReason}
														<div class="text-xs text-gray-400 mt-1">{task.failReason}</div>
													{/if}
												{:else if task.status === 'submitted'}
													<div class="text-3xl mb-2">📤</div>
													<div class="text-sm text-gray-500">已提交</div>
												{:else}
													<div class="text-3xl mb-2">🎬</div>
													<div class="text-sm text-gray-500">等待处理</div>
												{/if}
											</div>
										</div>
									{/if}

									<!-- 任务详情 -->
									<div class="space-y-2">
										<!-- 文本内容或音色信息 -->
										{#if task.mode === 'text2video' && task.text}
											<div
												class="text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 p-2 rounded"
											>
												"{task.text}"
											</div>
										{/if}

										{#if task.voiceId && task.voiceLanguage}
											<div class="text-sm text-gray-600 dark:text-gray-400">
												🎵 音色：{getVoiceName(task.voiceLanguage, task.voiceId)}
											</div>
										{/if}

										<!-- 底部信息 -->
										<div
											class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-600"
										>
											<span>⏰ {formatDate(task.createdAt)}</span>
											<span>💰 {task.creditsCost} 积分</span>
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
