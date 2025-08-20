<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, showSidebar, user, mobile, config } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	// Import MJ API functions
	import {
		type MJTask,
		type MJMode,
		type MJVersion,
		type MJAspectRatio,
		type MJQuality,
		type MJReferenceImage,
		type MJAdvancedParams,
		type MJGenerateRequest,
		type MJConfig,
		submitImagineTask,
		submitActionTask,
		submitModalTask,
		getTaskStatus,
		getUserTaskHistory,
		getUserCredits,
		getMJUserConfig,
		deleteTask,
		fixTaskStates
	} from '$lib/apis/midjourney';

	// Import DreamWork API functions
	import {
		type DreamWorkTask,
		type DreamWorkConfig,
		type DreamWorkGenerateRequest,
		submitTextToImageTask,
		submitImageToImageTask,
		getDreamWorkTaskStatus,
		getDreamWorkUserTaskHistory,
		getDreamWorkUserCredits,
		getDreamWorkUserConfig,
		deleteDreamWorkTask
	} from '$lib/apis/dreamwork';

	// Import Flux API functions
	import {
		type FluxTask,
		type FluxConfig,
		type FluxModel,
		type FluxTextToImageRequest,
		type FluxImageToImageRequest,
		type FluxMultiImageRequest,
		submitFluxTextToImage,
		submitFluxImageToImage,
		submitFluxMultiImage,
		getFluxTaskStatus,
		getFluxUserTaskHistory,
		getFluxUserCredits,
		getFluxUserConfig,
		getFluxModels,
		deleteFluxTask,
		uploadFluxImage,
		uploadFluxImages,
		formatFluxProgress,
		getFluxTaskImageUrl
	} from '$lib/apis/flux';

	// Import MJ streaming/callback system
	import { mjCallbackHandler, type MJTaskUpdate } from '$lib/apis/midjourney/streaming';

	const i18n = getContext('i18n');

	let loaded = false;
	let isGenerating = false;
	let currentTask: MJTask | null = null;
	let generatedImage: MJTask | null = null;
	let taskHistory: MJTask[] = [];
	let userCredits = 0;
	let loadingData = false;
	let streamingActive = false;
	let unsubscribeCallbacks: (() => void)[] = [];
	let pollingInterval: NodeJS.Timeout | null = null;
	let mjConfig: MJConfig | null = null;
	let dreamWorkConfig: DreamWorkConfig | null = null;
	let fluxConfig: FluxConfig | null = null;

	// 服务选择
	type ImageService = 'midjourney' | 'dreamwork' | 'flux';
	let selectedService: ImageService = 'midjourney';
	let availableServices: { id: ImageService; name: string; icon: string; enabled: boolean }[] = [];

	// 基础参数
	let prompt = '';
	let negativePrompt = '';
	let selectedMode: MJMode = 'fast';

	// 模型和版本
	let selectedVersion: MJVersion = 'v6.1';

	// 图片比例
	let selectedAspectRatio: MJAspectRatio = '1:1';
	let customWidth = 1;
	let customHeight = 1;

	// 图像质量
	let selectedQuality: MJQuality = 1;

	// 高级参数
	let chaosLevel = 0;
	let stylizeLevel = 100;
	let weirdLevel = 0;
	let seedValue: number | undefined = undefined;
	let enableTile = false;
	let disablePresets = false;

	// DreamWork 参数
	let dreamWorkTextToImageModel = 'doubao-seedream-3-0-t2i-250415';
	let dreamWorkImageToImageModel = 'doubao-seededit-3-0-i2i-250628';
	let dreamWorkSize = '1024x1024';
	let dreamWorkGuidanceScale = 2.5;
	let dreamWorkWatermarkEnabled = true;
	let dreamWorkInputImage: string | null = null; // 图生图的输入图片(base64)

	// Flux 参数
	let fluxModels: FluxModel[] = [];
	let selectedFluxModel = 'fal-ai/flux-1/schnell'; // 默认快速模型
	let fluxNumImages = 1; // 图片数量
	let fluxGuidanceScale = 3.5;
	let fluxInferenceSteps = 28;
	let fluxAspectRatio = '1:1';
	let fluxImageSize = 'landscape_4_3'; // Dev模型使用的图片尺寸
	let fluxSafetyTolerance = '2';
	let fluxOutputFormat = 'jpeg';
	let fluxEnableSafetyChecker = true;
	let fluxInputImageUrl: string | null = null; // 单图输入
	let fluxInputImageUrls: string[] = []; // 多图输入
	let fluxStrength = 0.95; // 图生图强度

	// 参考图片
	let referenceImages: MJReferenceImage[] = [];
	let styleImages: MJReferenceImage[] = [];
	let characterImages: MJReferenceImage[] = [];

	// 搜索和筛选
	let searchQuery = '';
	let selectedStatusFilter = 'all';
	let selectedTimeFilter = 'all';

	// 模式配置（积分消耗）- 动态从后台获取
	$: modeConfig = mjConfig?.modes
		? {
				turbo: {
					label: 'Turbo',
					credits: mjConfig.modes.turbo?.credits || 10,
					description: '最快速度，消耗积分最多',
					enabled: mjConfig.modes.turbo?.enabled || false
				},
				fast: {
					label: 'Fast',
					credits: mjConfig.modes.fast?.credits || 5,
					description: '快速生成，中等积分消耗',
					enabled: mjConfig.modes.fast?.enabled || false
				},
				relax: {
					label: 'Relax',
					credits: mjConfig.modes.relax?.credits || 2,
					description: '较慢速度，消耗积分最少',
					enabled: mjConfig.modes.relax?.enabled || false
				}
			}
		: {
				turbo: {
					label: 'Turbo',
					credits: 10,
					description: '最快速度，消耗积分最多',
					enabled: true
				},
				fast: { label: 'Fast', credits: 5, description: '快速生成，中等积分消耗', enabled: true },
				relax: { label: 'Relax', credits: 2, description: '较慢速度，消耗积分最少', enabled: true }
			};

	// 版本配置
	const versionConfig = {
		'v5.2': { label: 'V5.2', description: '经典版本，稳定可靠' },
		v6: { label: 'V6', description: '平衡版本，质量与速度兼顾' },
		'v6.1': { label: 'V6.1', description: '推荐版本，最新优化' },
		v7: { label: 'V7', description: '最新版本，最高质量' }
	};

	// 图片比例配置
	const aspectRatioConfig = {
		'1:1': { label: '头像', icon: '👤' },
		'3:2': { label: '文章配图', icon: '📄' },
		'3:4': { label: '社交媒体', icon: '📱' },
		'4:3': { label: '公众号配图', icon: '📰' },
		'9:16': { label: '海报图', icon: '📱' },
		'2:3': { label: '手机壁纸', icon: '📲' },
		'16:9': { label: '电脑壁纸', icon: '💻' },
		'21:9': { label: '超长横幅', icon: '🖥️' },
		custom: { label: '自定义', icon: '⚙️' }
	};

	// 计算Flux模型积分 - 基于后台配置的动态计算
	const getFluxModelCredits = (model: string): number => {
		// 支持两种字段名：model_credits (backend) 和 modelCredits (interface)
		const modelCredits = fluxConfig?.model_credits || fluxConfig?.modelCredits;

		if (!modelCredits) {
			// 如果没有配置，使用默认值
			const defaultCredits: Record<string, number> = {
				'fal-ai/flux-1/schnell': 5,
				'fal-ai/flux-1/dev': 10,
				'fal-ai/flux-1/dev/image-to-image': 10,
				'fal-ai/flux-pro': 20,
				'fal-ai/flux-pro/kontext': 25,
				'fal-ai/flux-pro/kontext/multi': 30,
				'fal-ai/flux-pro/max': 35
			};
			return defaultCredits[model] || 5;
		}

		return modelCredits[model] || 5;
	};

	// 质量配置
	const qualityConfig = {
		0.25: { label: '普通', description: '快速生成，较低质量' },
		0.5: { label: '一般', description: '标准质量，适中速度' },
		1: { label: '高清', description: '高质量，推荐选择' },
		2: { label: '超高清', description: '最高质量，较慢速度' }
	};

	// 筛选后的历史记录
	$: filteredTaskHistory = taskHistory.filter((task) => {
		// 搜索筛选
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			const matchPrompt = task.prompt?.toLowerCase().includes(query);
			const matchPromptEn = task.promptEn?.toLowerCase().includes(query);
			const matchDescription = task.description?.toLowerCase().includes(query);
			if (!matchPrompt && !matchPromptEn && !matchDescription) {
				return false;
			}
		}

		// 状态筛选
		if (selectedStatusFilter !== 'all' && task.status !== selectedStatusFilter) {
			return false;
		}

		// 时间筛选
		if (selectedTimeFilter !== 'all') {
			const taskDate = new Date(task.submitTime);
			const now = new Date();
			const daysDiff = Math.floor((now.getTime() - taskDate.getTime()) / (1000 * 60 * 60 * 24));

			switch (selectedTimeFilter) {
				case 'today':
					if (daysDiff > 0) return false;
					break;
				case 'week':
					if (daysDiff > 7) return false;
					break;
				case 'month':
					if (daysDiff > 30) return false;
					break;
			}
		}

		return true;
	});

	onMount(async () => {
		console.log('🔍 【页面调试】onMount执行');
		console.log('🔍 【页面调试】$user状态:', $user ? '有用户' : '无用户');
		console.log(
			'🔍 【页面调试】$user.token状态:',
			$user?.token ? `有token(${$user.token.length}字符)` : '无token'
		);

		if (!$user) {
			console.log('🔍 【页面调试】用户未登录，跳转到登录页');
			goto('/auth');
			return;
		}
		loaded = true;

		// 🔥 页面加载时自动修复任务状态
		await fixTaskStatesOnLoad();

		await loadUserData();
		await setupMJStreaming();
	});

	const setupMJStreaming = async () => {
		if (!$user?.token) return;

		try {
			// 订阅任务更新事件
			const unsubscribeTaskUpdate = mjCallbackHandler.subscribe(
				'task_update',
				(update: MJTaskUpdate) => {
					if (update.task && currentTask && update.taskId === currentTask.id) {
						currentTask = update.task;
						console.log('Task updated:', update.task);
					}
				}
			);

			// 订阅任务完成事件
			const unsubscribeTaskComplete = mjCallbackHandler.subscribe(
				'task_complete',
				(update: MJTaskUpdate) => {
					console.log('🔄 【前端流媒体修复版】收到任务完成事件:', update.taskId);

					if (update.task && currentTask && update.taskId === currentTask.id) {
						console.log('🔄 【前端流媒体修复版】当前任务完成，停止流媒体');
						generatedImage = update.task;
						currentTask = null;
						isGenerating = false;
						toast.success('图像生成完成！');

						// 🔥 任务完成后停止流媒体，避免无限循环
						mjCallbackHandler.stopAllStreams();

						// 刷新用户数据
						loadUserData();
					} else if (update.task) {
						// 更新历史记录中的其他完成任务
						console.log('🔄 【前端流媒体修复版】历史任务完成:', update.taskId);
						taskHistory = taskHistory.map((t) => (t.id === update.taskId ? { ...update.task } : t));
					}
				}
			);

			// 订阅任务失败事件
			const unsubscribeTaskFailed = mjCallbackHandler.subscribe(
				'task_failed',
				(update: MJTaskUpdate) => {
					if (update.task && currentTask && update.taskId === currentTask.id) {
						currentTask = null;
						isGenerating = false;
						toast.error(`生成失败: ${update.task.failReason || '未知错误'}`);
					}
				}
			);

			// 订阅积分更新事件
			const unsubscribeCreditsUpdate = mjCallbackHandler.subscribe(
				'credits_update',
				(update: MJTaskUpdate) => {
					if (update.credits !== undefined) {
						userCredits = update.credits;
					}
				}
			);

			// 订阅错误事件
			const unsubscribeError = mjCallbackHandler.subscribe('error', (update: MJTaskUpdate) => {
				console.error('MJ Stream Error:', update.error);
				toast.error(`连接错误: ${update.error}`);
			});

			// 保存取消订阅回调
			unsubscribeCallbacks = [
				unsubscribeTaskUpdate,
				unsubscribeTaskComplete,
				unsubscribeTaskFailed,
				unsubscribeCreditsUpdate,
				unsubscribeError
			];

			// 启动用户流
			await mjCallbackHandler.startUserStream($user.token, $user.id);
			streamingActive = true;
			console.log('MJ streaming setup complete');
		} catch (error) {
			console.error('Failed to setup MJ streaming:', error);
			toast.error('无法建立实时连接，将使用轮询模式');
		}
	};

	// 加载DreamWork配置
	const loadDreamWorkConfig = async () => {
		if (!$user?.token) return;

		try {
			const config = await getDreamWorkUserConfig($user.token);
			if (config) {
				dreamWorkConfig = config;
				console.log('即梦配置已加载:', config);
			}
		} catch (error) {
			console.error('加载即梦配置失败:', error);
		}
	};

	// 加载Flux配置
	const loadFluxConfig = async () => {
		if (!$user?.token) return;

		try {
			const config = await getFluxUserConfig($user.token);
			if (config) {
				fluxConfig = config;
				console.log('Flux配置已加载:', config);

				// 加载支持的模型列表
				const models = await getFluxModels($user.token);
				fluxModels = models;

				// 设置默认模型
				if (config.default_model && models.find((m) => m.id === config.default_model)) {
					selectedFluxModel = config.default_model;
				}
			}
		} catch (error) {
			console.error('加载Flux配置失败:', error);
		}
	};

	const updateAvailableServices = async () => {
		availableServices = [
			{
				id: 'midjourney',
				name: 'MidJourney',
				icon: '⛵',
				enabled: mjConfig?.enabled || false
			},
			{
				id: 'dreamwork',
				name: '即梦 (DreamWork)',
				icon: '🎨',
				enabled: dreamWorkConfig?.enabled || false
			},
			{
				id: 'flux',
				name: 'Flux AI',
				icon: '⚡',
				enabled: fluxConfig?.enabled || false
			}
		];

		// 选择第一个可用的服务
		const enabledService = availableServices.find((s) => s.enabled);
		if (enabledService && !availableServices.find((s) => s.id === selectedService)?.enabled) {
			selectedService = enabledService.id;
		}
	};

	const loadMJConfig = async () => {
		if (!$user?.token) return;

		try {
			const config = await getMJUserConfig($user.token);
			if (config) {
				mjConfig = config;
				// 如果当前选择的模式被禁用，切换到默认模式
				if (mjConfig.modes && !mjConfig.modes[selectedMode]?.enabled) {
					const enabledModes = Object.entries(mjConfig.modes).filter(
						([_, config]) => config.enabled
					);
					if (enabledModes.length > 0) {
						selectedMode =
							mjConfig.defaultMode && mjConfig.modes[mjConfig.defaultMode]?.enabled
								? mjConfig.defaultMode
								: (enabledModes[0][0] as MJMode);
					}
				}
			}
		} catch (configError) {
			console.error('Failed to load MJ config:', configError);
			// 配置加载失败时使用默认配置，不影响其他功能
		}
	};

	const loadUserData = async () => {
		console.log('🔍 【数据加载调试】loadUserData开始');
		console.log('🔍 【数据加载调试】$user状态:', $user ? '有用户' : '无用户');
		console.log(
			'🔍 【数据加载调试】$user.token状态:',
			$user?.token ? `有token(${$user.token.length}字符)` : '无token'
		);

		if (!$user?.token) {
			console.error('🔍 【数据加载调试】没有token，无法加载数据');
			return;
		}

		loadingData = true;
		try {
			// 加载配置 - 获取最新的积分设置
			await loadMJConfig();
			await loadDreamWorkConfig();
			await loadFluxConfig();
			await updateAvailableServices();

			// 加载用户积分 - 确保使用用户token进行隔离
			const credits = await getUserCredits($user.token);
			if (credits) {
				userCredits = credits.balance || 0;
			}

			// 加载用户历史记录 - 确保用户数据隔离
			let allTasks = [];

			// 1. 加载MidJourney历史记录
			try {
				const mjHistory = await getUserTaskHistory($user.token, 1, 20);
				if (mjHistory && mjHistory.data) {
					console.log('📋 加载MidJourney历史记录:', mjHistory.data.length, '个任务');
					// 为MidJourney任务添加serviceType标识以便区分
					const mjTasksWithType = mjHistory.data.map((task) => ({
						...task,
						properties: {
							...(task.properties || {}),
							serviceType: task.properties?.serviceType || 'midjourney'
						}
					}));
					allTasks = [...allTasks, ...mjTasksWithType];
				}
			} catch (error) {
				console.error('加载MidJourney历史记录失败:', error);
			}

			// 2. 加载DreamWork历史记录
			try {
				const dreamWorkHistory = await getDreamWorkUserTaskHistory($user.token, 1, 20);
				if (dreamWorkHistory && dreamWorkHistory.data) {
					console.log('🎨 加载DreamWork历史记录:', dreamWorkHistory.data.length, '个任务');
					// 为DreamWork任务添加serviceType标识以便区分
					const dreamWorkTasksWithType = dreamWorkHistory.data.map((task) => ({
						...task,
						properties: {
							...(task.properties || {}),
							serviceType: 'dreamwork'
						}
					}));
					allTasks = [...allTasks, ...dreamWorkTasksWithType];
				}
			} catch (error) {
				console.error('加载DreamWork历史记录失败:', error);
			}

			// 3. 加载Flux历史记录
			try {
				const fluxHistory = await getFluxUserTaskHistory($user.token, 1, 20);
				if (fluxHistory && fluxHistory.data) {
					console.log('⚡ 加载Flux历史记录:', fluxHistory.data.length, '个任务');
					// 为Flux任务添加serviceType标识以便区分，并转换为统一格式
					const fluxTasksWithType = fluxHistory.data.map((task) => ({
						...task,
						// 转换Flux格式到统一的MJTask格式
						action: task.task_type === 'image_to_image' ? 'IMAGE_TO_IMAGE' : 'TEXT_TO_IMAGE',
						promptEn: task.prompt,
						description: `Flux ${task.task_type === 'image_to_image' ? '图生图' : '文生图'}: ${task.prompt}`,
						submitTime: new Date(task.created_at).getTime(),
						startTime: task.updated_at ? new Date(task.updated_at).getTime() : 0,
						finishTime: task.completed_at ? new Date(task.completed_at).getTime() : 0,
						progress: formatFluxProgress(task),
						imageUrl: getFluxTaskImageUrl(task),
						failReason: task.error_message,
						properties: {
							serviceType: 'flux',
							model: task.model,
							task_type: task.task_type
						}
					}));
					allTasks = [...allTasks, ...fluxTasksWithType];
				}
			} catch (error) {
				console.error('加载Flux历史记录失败:', error);
			}

			if (allTasks.length > 0) {
				// 保留当前正在进行的任务，避免被覆盖
				const currentTaskInHistory = currentTask ? [currentTask] : [];
				const existingTaskIds = currentTaskInHistory.map((t) => t.id);

				// 保留本地已有的任务状态，优先使用本地数据（避免覆盖最新状态）
				const localTasksMap = new Map(taskHistory.map((t) => [t.id, t]));
				const mergedHistory = allTasks.map((serverTask) => {
					const localTask = localTasksMap.get(serverTask.id);
					// 如果本地任务存在且状态更新，优先使用本地数据
					if (localTask && (localTask.imageUrl || localTask.status === 'SUCCESS')) {
						console.log(
							'保留本地任务状态:',
							localTask.id,
							localTask.status,
							'有图片:',
							!!localTask.imageUrl,
							'服务:',
							localTask.properties?.serviceType || 'unknown'
						);
						return localTask;
					}
					// 确保服务器任务有正确的serviceType标识
					if (!serverTask.properties?.serviceType) {
						// 根据任务来源推断serviceType
						if (serverTask.action === 'TEXT_TO_IMAGE' || serverTask.action === 'IMAGE_TO_IMAGE') {
							serverTask.properties = {
								...(serverTask.properties || {}),
								serviceType: 'dreamwork'
							};
						} else {
							serverTask.properties = {
								...(serverTask.properties || {}),
								serviceType: 'midjourney'
							};
						}
					}
					return serverTask;
				});

				// 按时间排序（最新的在前）
				const sortedHistory = mergedHistory.sort(
					(a, b) => (b.submitTime || 0) - (a.submitTime || 0)
				);

				const newHistory = sortedHistory.filter((t) => !existingTaskIds.includes(t.id));
				taskHistory = [...currentTaskInHistory, ...newHistory];

				console.log(
					'📋 历史记录已更新，保留本地状态:',
					taskHistory.length,
					'个任务（MJ+DreamWork+Flux）'
				);
				console.log(
					'📋 DreamWork任务数量:',
					taskHistory.filter((t) => t.properties?.serviceType === 'dreamwork').length
				);
				console.log(
					'📋 MidJourney任务数量:',
					taskHistory.filter((t) => t.properties?.serviceType === 'midjourney').length
				);
				console.log(
					'📋 Flux任务数量:',
					taskHistory.filter((t) => t.properties?.serviceType === 'flux').length
				);

				// 🔥 加载数据后强制修复本地任务显示
				forceFixLocalTasks();

				// 页面刷新后恢复最新完成的图像状态
				if (!generatedImage && taskHistory.length > 0) {
					// 查找最新完成的图像任务
					const latestCompletedTask = taskHistory.find(
						(task) => task.imageUrl && (task.status === 'SUCCESS' || task.imageUrl)
					);

					if (latestCompletedTask) {
						console.log(
							'🔄 页面刷新后恢复最新生成图像:',
							latestCompletedTask.id,
							latestCompletedTask.properties?.serviceType || 'MJ'
						);
						generatedImage = { ...latestCompletedTask };
					}
				}
			}
		} catch (error) {
			console.error('Failed to load user data:', error);
			toast.error('加载用户数据失败');
		} finally {
			loadingData = false;
		}
	};

	// 只刷新积分，不刷新历史记录（避免状态覆盖）
	const refreshCreditsOnly = async () => {
		if (!$user?.token) return;

		try {
			// 只刷新积分
			const credits = await getUserCredits($user.token);
			if (credits) {
				userCredits = credits.balance || 0;
				console.log('💰 积分已刷新:', userCredits);
			}
		} catch (error) {
			console.error('刷新积分失败:', error);
		}
	};

	// 🔥 页面加载时自动修复任务状态
	const fixTaskStatesOnLoad = async () => {
		if (!$user?.token) return;

		try {
			console.log('🔧 自动修复任务状态...');
			const result = await fixTaskStates($user.token);
			if (result && result.fixed_count > 0) {
				console.log(`🔧 已修复 ${result.fixed_count} 个任务状态`);
				toast.success(`已修复 ${result.fixed_count} 个任务状态`);
				// 修复后立即重新加载数据
				setTimeout(() => {
					loadUserData();
				}, 1000);
			} else {
				console.log('🔧 没有需要修复的任务');
			}
		} catch (error) {
			console.error('自动修复任务状态失败:', error);
		}
	};

	// 🔥 强制本地数据修复 - 确保所有完成的任务显示正确
	const forceFixLocalTasks = () => {
		let fixedCount = 0;
		taskHistory = taskHistory.map((task) => {
			// 检查任务是否需要修复：有图片但状态或进度不对
			if (task.imageUrl && (task.status !== 'SUCCESS' || task.progress !== '100%')) {
				console.log(
					`🔧 强制修复本地任务: ${task.id} - ${task.status} -> SUCCESS, ${task.progress} -> 100%`
				);
				fixedCount++;
				return {
					...task,
					status: 'SUCCESS',
					progress: '100%'
				};
			}
			return task;
		});

		if (fixedCount > 0) {
			console.log(`🔧 本地修复了 ${fixedCount} 个任务`);
			toast.success(`本地修复了 ${fixedCount} 个任务显示`);
		}
	};

	// 🔥 强制刷新可疑任务 - 查询远程API获取最新状态
	const forceRefreshSuspiciousTasks = async () => {
		if (!$user?.token) return;

		console.log('🔧 开始强制刷新可疑任务...');
		let refreshedCount = 0;

		// 找出所有可疑任务：没有图片且状态不是失败的
		const suspiciousTasks = taskHistory.filter(
			(task) => !task.imageUrl && task.status !== 'FAILURE' && task.status !== 'FAILED'
		);

		console.log(`🔧 发现 ${suspiciousTasks.length} 个可疑任务需要刷新`);

		for (const task of suspiciousTasks) {
			try {
				console.log(`🔧 查询任务 ${task.id} 的远程状态...`);
				const remoteTask = await getTaskStatus($user.token, task.id);

				if (remoteTask && remoteTask.imageUrl) {
					console.log(`🔧 发现任务 ${task.id} 远程有图片: ${remoteTask.imageUrl}`);

					// 更新本地任务数据
					taskHistory = taskHistory.map((t) =>
						t.id === task.id
							? {
									...t,
									...remoteTask,
									status: 'SUCCESS',
									progress: '100%',
									imageUrl: remoteTask.imageUrl
								}
							: t
					);

					refreshedCount++;
				}
			} catch (error) {
				console.error(`🔧 查询任务 ${task.id} 失败:`, error);
			}
		}

		if (refreshedCount > 0) {
			console.log(`🔧 强制刷新了 ${refreshedCount} 个任务`);
			toast.success(`从远程API刷新了 ${refreshedCount} 个任务`);
		}
	};

	const generateImage = async () => {
		if (!prompt.trim()) {
			toast.error('请输入描述');
			return;
		}

		// 根据选择的服务检查积分
		const requiredCredits =
			selectedService === 'midjourney'
				? modeConfig[selectedMode].credits
				: selectedService === 'dreamwork'
					? dreamWorkConfig?.creditsPerGeneration || 10
					: selectedService === 'flux'
						? getFluxModelCredits(selectedFluxModel) * (fluxNumImages || 1) // Flux按模型和图片数量计算积分
						: 5;

		if (userCredits < requiredCredits) {
			toast.error('积分不足');
			return;
		}

		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		isGenerating = true;
		try {
			if (selectedService === 'midjourney') {
				// === MidJourney 生成逻辑 ===
				// 构建生成请求
				const advancedParams: MJAdvancedParams = {
					chaos: chaosLevel > 0 ? chaosLevel : undefined,
					stylize: stylizeLevel !== 100 ? stylizeLevel : undefined,
					weird: weirdLevel > 0 ? weirdLevel : undefined,
					seed: seedValue,
					quality: selectedQuality,
					version: selectedVersion,
					aspectRatio: selectedAspectRatio,
					customAspectRatio:
						selectedAspectRatio === 'custom'
							? { width: customWidth, height: customHeight }
							: undefined,
					tile: enableTile,
					noCommands: disablePresets
				};

				// 合并所有参考图片
				const allReferenceImages = [...referenceImages, ...styleImages, ...characterImages];

				const request: MJGenerateRequest = {
					prompt: prompt.trim(),
					negativePrompt: negativePrompt.trim() || undefined,
					mode: selectedMode,
					referenceImages: allReferenceImages.length > 0 ? allReferenceImages : undefined,
					advancedParams
				};

				// 调用 MJ API - 使用用户token确保隔离
				const result = await submitImagineTask($user.token, request);

				if (result && result.code === 1) {
					// 提交成功，开始轮询任务状态
					currentTask = {
						id: result.result,
						action: 'IMAGINE',
						status: 'SUBMITTED',
						prompt: request.prompt,
						promptEn: request.prompt,
						description: `/imagine ${request.prompt}`,
						submitTime: Date.now(),
						startTime: 0,
						finishTime: 0,
						progress: '0%'
					};

					toast.success('任务已提交，开始生成...');

					// 强制使用轮询模式（生产环境更稳定）
					console.log('开始轮询任务，流媒体状态:', streamingActive);

					// 立即添加到历史记录以便用户看到
					taskHistory = [currentTask, ...taskHistory];

					// 调试：验证状态已更新
					console.log('✅ 当前任务已设置:', currentTask);
					console.log('✅ 历史记录已更新:', taskHistory.length, '个任务');
					console.log('✅ 生成状态:', isGenerating);

					// 🔥 直接前端轮询 - 简单有效
					console.log('🔥 启动前端轮询，确保能拿到进度...');
					pollTaskStatus(result.result);
				} else if (result && result.code === 22) {
					// 任务进入队列，也需要显示状态和轮询
					currentTask = {
						id: result.result || 'queued',
						action: 'IMAGINE',
						status: 'SUBMITTED',
						prompt: request.prompt,
						promptEn: request.prompt,
						description: `/imagine ${request.prompt} (队列中)`,
						submitTime: Date.now(),
						startTime: 0,
						finishTime: 0,
						progress: '0%'
					};
					toast.info(`任务已进入队列，前面还有 ${result.properties?.numberOfQueues || 0} 个任务`);

					// 立即添加到历史记录
					taskHistory = [currentTask, ...taskHistory];

					// 队列任务也需要轮询
					if (result.result) {
						pollTaskStatus(result.result);
					}
				} else if (result && result.code === 24) {
					toast.error(`提示词包含敏感词: ${result.properties?.bannedWord || ''}`);
					// 任务失败，重置状态
					isGenerating = false;
					currentTask = null;
				} else {
					throw new Error(result?.description || '提交失败');
				}
			} else if (selectedService === 'dreamwork') {
				// === DreamWork 生成逻辑 ===
				if (!dreamWorkConfig || !dreamWorkConfig.enabled) {
					toast.error('即梦服务未配置或未启用');
					isGenerating = false;
					return;
				}

				// 正确判断是文生图还是图生图：根据用户选择的模型类型和是否有输入图片
				const isImageToImage =
					dreamWorkTextToImageModel === 'doubao-seededit-3-0-i2i-250628' && dreamWorkInputImage;

				console.log('🎨 【DreamWork前端】模式判断:', {
					selectedModel: dreamWorkTextToImageModel,
					hasInputImage: !!dreamWorkInputImage,
					isImageToImage: isImageToImage,
					textToImageModel: dreamWorkTextToImageModel,
					imageToImageModel: dreamWorkImageToImageModel
				});

				// 验证图生图模式的必要条件
				if (isImageToImage && !dreamWorkInputImage) {
					toast.error('图生图模式需要上传输入图片');
					isGenerating = false;
					return;
				}

				// 构建DreamWork请求，使用正确的模型
				const dreamWorkRequest: DreamWorkGenerateRequest = {
					model: isImageToImage ? dreamWorkImageToImageModel : dreamWorkTextToImageModel,
					prompt: prompt.trim(),
					responseFormat: 'url', // 改为url格式，避免base64过大
					size: dreamWorkSize,
					guidanceScale: dreamWorkGuidanceScale,
					watermark: dreamWorkWatermarkEnabled,
					seed: seedValue
				};

				// 如果是图生图，添加输入图片
				if (isImageToImage && dreamWorkInputImage) {
					// 确保图片数据格式正确
					let base64Data = dreamWorkInputImage;

					// 处理data URL格式
					if (dreamWorkInputImage.startsWith('data:')) {
						if (dreamWorkInputImage.includes(',')) {
							base64Data = dreamWorkInputImage.split(',')[1];
							console.log('🎨 【DreamWork前端】移除data URL前缀');
						} else {
							toast.error('无效的图片数据格式');
							isGenerating = false;
							return;
						}
					}

					// 清理可能的空白字符
					base64Data = base64Data.replace(/\s/g, '');

					// 验证base64数据
					if (!base64Data || base64Data.length < 100) {
						toast.error('图片数据无效，请重新上传');
						isGenerating = false;
						return;
					}

					console.log('🎨 【DreamWork前端】图片数据验证:', {
						originalLength: dreamWorkInputImage.length,
						processedLength: base64Data.length,
						hasDataPrefix: dreamWorkInputImage.startsWith('data:'),
						first50Chars: base64Data.substring(0, 50)
					});

					dreamWorkRequest.image = base64Data;
				}

				console.log('🎨 【DreamWork前端】提交任务:', {
					type: isImageToImage ? '图生图' : '文生图',
					model: dreamWorkRequest.model,
					hasInputImage: !!dreamWorkRequest.image,
					prompt: dreamWorkRequest.prompt
				});

				// 调用对应的DreamWork API
				const result = isImageToImage
					? await submitImageToImageTask($user.token, dreamWorkRequest)
					: await submitTextToImageTask($user.token, dreamWorkRequest);

				if (result && result.success) {
					// 提交成功，创建任务记录
					currentTask = {
						id: result.task_id,
						action: isImageToImage ? 'IMAGE_TO_IMAGE' : 'TEXT_TO_IMAGE',
						status: 'SUBMITTED',
						prompt: prompt.trim(),
						promptEn: prompt.trim(),
						description: `即梦${isImageToImage ? '图生图' : '文生图'}: ${prompt.trim()}`,
						submitTime: Date.now(),
						startTime: 0,
						finishTime: 0,
						progress: '0%',
						creditsCost: dreamWorkConfig.creditsPerGeneration,
						inputImage: isImageToImage ? dreamWorkInputImage : undefined,
						properties: {
							serviceType: 'dreamwork',
							model: dreamWorkRequest.model
						}
					};

					toast.success(`即梦${isImageToImage ? '图生图' : '文生图'}任务已提交，开始生成...`);

					// 立即添加到历史记录
					taskHistory = [currentTask, ...taskHistory];

					// DreamWork API通常是同步的，立即轮询结果
					pollDreamWorkTaskStatus(result.task_id);
				} else {
					console.error('🎨 【DreamWork前端】API返回错误:', result);
					throw new Error(result?.message || '即梦任务提交失败');
				}
			} else if (selectedService === 'flux') {
				// === Flux 生成逻辑 ===
				if (!fluxConfig || !fluxConfig.enabled) {
					toast.error('Flux服务未配置或未启用');
					isGenerating = false;
					return;
				}

				// 判断生成模式
				const isImageToImage = fluxInputImageUrl && selectedFluxModel.includes('image-to-image');
				const isMultiImage = fluxInputImageUrls.length > 0 && selectedFluxModel.includes('multi');

				console.log('⚡ 【Flux前端】模式判断:', {
					selectedModel: selectedFluxModel,
					hasInputImage: !!fluxInputImageUrl,
					hasMultiImages: fluxInputImageUrls.length > 0,
					isImageToImage: isImageToImage,
					isMultiImage: isMultiImage
				});

				// 验证必要条件
				if (isImageToImage && !fluxInputImageUrl) {
					toast.error('图生图模式需要上传输入图片');
					isGenerating = false;
					return;
				}
				if (isMultiImage && fluxInputImageUrls.length === 0) {
					toast.error('多图编辑模式需要上传图片');
					isGenerating = false;
					return;
				}

				try {
					let result;

					if (isMultiImage) {
						// 验证多图编辑的必要条件
						if (!fluxInputImageUrls || fluxInputImageUrls.length === 0) {
							throw new Error('多图编辑模式需要至少上传一张图片');
						}

						console.log('⚡ 【Flux多图】请求参数:', {
							model: selectedFluxModel,
							prompt: prompt.trim(),
							image_urls: fluxInputImageUrls,
							image_count: fluxInputImageUrls.length,
							guidance_scale: fluxGuidanceScale,
							num_images: fluxNumImages
						});

						// 多图编辑模式
						const fluxMultiRequest: FluxMultiImageRequest = {
							model: selectedFluxModel,
							prompt: prompt.trim(),
							image_urls: fluxInputImageUrls,
							guidance_scale: fluxGuidanceScale,
							num_images: fluxNumImages,
							seed: seedValue,
							sync_mode: false
						};

						// 根据模型类型添加参数
						if (selectedFluxModel.includes('pro') || selectedFluxModel.includes('kontext')) {
							fluxMultiRequest.aspect_ratio = fluxAspectRatio;
							fluxMultiRequest.safety_tolerance = fluxSafetyTolerance;
							fluxMultiRequest.output_format = fluxOutputFormat;
						}

						result = await submitFluxMultiImage($user.token, fluxMultiRequest);
					} else if (isImageToImage) {
						// 图生图
						const fluxImageRequest: FluxImageToImageRequest = {
							model: selectedFluxModel,
							prompt: prompt.trim(),
							image_url: fluxInputImageUrl,
							strength: fluxStrength,
							guidance_scale: fluxGuidanceScale,
							num_inference_steps: fluxInferenceSteps,
							seed: seedValue,
							sync_mode: false,
							enable_safety_checker: fluxEnableSafetyChecker
						};

						result = await submitFluxImageToImage($user.token, fluxImageRequest);
					} else {
						// 文生图 - 根据模型类型使用不同参数
						const fluxTextRequest: FluxTextToImageRequest = {
							model: selectedFluxModel,
							prompt: prompt.trim(),
							num_images: fluxNumImages,
							guidance_scale: fluxGuidanceScale,
							seed: seedValue,
							sync_mode: false,
							enable_safety_checker: fluxEnableSafetyChecker
						};

						// Pro/Kontext模型使用aspect_ratio和safety_tolerance
						if (selectedFluxModel.includes('pro') || selectedFluxModel.includes('kontext')) {
							fluxTextRequest.aspect_ratio = fluxAspectRatio;
							fluxTextRequest.safety_tolerance = fluxSafetyTolerance;
							fluxTextRequest.output_format = fluxOutputFormat;
						} else {
							// Dev/Schnell模型使用image_size和num_inference_steps
							fluxTextRequest.image_size = fluxImageSize;
							fluxTextRequest.num_inference_steps = fluxInferenceSteps;
						}

						result = await submitFluxTextToImage($user.token, fluxTextRequest);
					}

					if (result && result.id) {
						// 确定任务类型和描述
						let taskType = 'text_to_image';
						let description = `Flux 文生图 (${fluxNumImages}张): ${prompt.trim()}`;
						let inputImageData = undefined;

						if (isMultiImage) {
							taskType = 'multi_image';
							description = `Flux 多图编辑 (${fluxInputImageUrls.length}→${fluxNumImages}张): ${prompt.trim()}`;
							inputImageData = fluxInputImageUrls.join(';'); // 多个URL用分号分隔
						} else if (isImageToImage) {
							taskType = 'image_to_image';
							description = `Flux 图生图 (${fluxNumImages}张): ${prompt.trim()}`;
							inputImageData = fluxInputImageUrl;
						}

						// 提交成功，创建任务记录
						currentTask = {
							id: result.id,
							action: isImageToImage ? 'IMAGE_TO_IMAGE' : 'TEXT_TO_IMAGE',
							status: 'SUBMITTED',
							prompt: prompt.trim(),
							promptEn: prompt.trim(),
							description: description,
							submitTime: Date.now(),
							startTime: 0,
							finishTime: 0,
							progress: '0%',
							creditsCost: requiredCredits,
							inputImage: inputImageData,
							properties: {
								serviceType: 'flux',
								model: selectedFluxModel,
								task_type: taskType,
								multi_images_count: isMultiImage ? fluxInputImageUrls.length : 0
							}
						};

						let successMessage = `Flux 文生图任务已提交，开始生成${fluxNumImages}张图片...`;
						if (isMultiImage) {
							successMessage = `Flux 多图编辑任务已提交（${fluxInputImageUrls.length}→${fluxNumImages}张），开始生成...`;
						} else if (isImageToImage) {
							successMessage = `Flux 图生图任务已提交，开始生成${fluxNumImages}张图片...`;
						}
						toast.success(successMessage);

						// 立即添加到历史记录
						taskHistory = [currentTask, ...taskHistory];

						// Flux使用异步轮询
						pollFluxTaskStatus(result.id);
					} else {
						console.error('⚡ 【Flux前端】API返回错误:', result);
						throw new Error('Flux任务提交失败');
					}
				} catch (error) {
					console.error('⚡ 【Flux前端】任务提交失败:', error);
					throw error;
				}
			} else {
				toast.error('不支持的生成服务');
				isGenerating = false;
				return;
			}
		} catch (error) {
			console.error('Generation failed:', error);
			toast.error(`生成失败: ${error.message || error}`);
			// 只有在真正发生错误时才重置状态
			isGenerating = false;
			currentTask = null;
		}
		// 移除 finally 块 - 不要在这里重置 isGenerating，应该在任务真正完成时重置
	};

	// 图片上传处理函数
	const handleImageUpload = async (files: FileList, type: 'normal' | 'style' | 'character') => {
		for (const file of Array.from(files)) {
			if (!file.type.startsWith('image/')) {
				toast.error('只能上传图片文件');
				continue;
			}

			if (file.size > 5 * 1024 * 1024) {
				toast.error('图片大小不能超过5MB');
				continue;
			}

			try {
				const base64 = await fileToBase64(file);
				const image: MJReferenceImage = {
					id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
					base64,
					weight: type === 'normal' ? 1.0 : type === 'style' ? 100 : 500,
					type,
					filename: file.name
				};

				if (type === 'normal') {
					if (referenceImages.length >= 5) {
						toast.error('最多只能上传5张普通参考图');
						continue;
					}
					referenceImages = [...referenceImages, image];
				} else if (type === 'style') {
					if (styleImages.length >= 5) {
						toast.error('最多只能上传5张风格参考图');
						continue;
					}
					styleImages = [...styleImages, image];
				} else if (type === 'character') {
					if (characterImages.length >= 2) {
						toast.error('最多只能上传2张角色参考图');
						continue;
					}
					characterImages = [...characterImages, image];
				}
			} catch (error) {
				console.error('Image upload failed:', error);
				toast.error('图片上传失败');
			}
		}
	};

	// 文件转Base64
	const fileToBase64 = (file: File): Promise<string> => {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => resolve(reader.result as string);
			reader.onerror = reject;
			reader.readAsDataURL(file);
		});
	};

	// DreamWork 任务状态轮询
	const pollDreamWorkTaskStatus = async (taskId: string) => {
		const maxAttempts = 60; // 最多轮询60次 (约10分钟)
		let attempts = 0;

		const poll = async () => {
			try {
				attempts++;
				console.log(`🎨 【DreamWork轮询】第${attempts}次查询任务状态: ${taskId}`);

				const task = await getDreamWorkTaskStatus($user.token, taskId);

				if (task) {
					// 更新当前任务状态
					if (currentTask && currentTask.id === taskId) {
						currentTask = {
							...currentTask,
							status: task.status,
							progress:
								task.status === 'SUCCESS'
									? '100%'
									: task.status === 'FAILURE'
										? '失败'
										: '处理中...',
							imageUrl: task.imageUrl,
							failReason: task.failReason,
							finishTime: task.status === 'SUCCESS' || task.status === 'FAILURE' ? Date.now() : 0
						};
					}

					// 更新历史记录中的任务
					taskHistory = taskHistory.map((t) =>
						t.id === taskId
							? {
									...t,
									status: task.status,
									progress:
										task.status === 'SUCCESS'
											? '100%'
											: task.status === 'FAILURE'
												? '失败'
												: '处理中...',
									imageUrl: task.imageUrl,
									failReason: task.failReason,
									finishTime:
										task.status === 'SUCCESS' || task.status === 'FAILURE' ? Date.now() : 0
								}
							: t
					);

					if (task.status === 'SUCCESS') {
						console.log('🎨 【DreamWork轮询】任务完成成功:', task);
						toast.success('即梦图片生成完成!');
						generatedImage = currentTask;
						isGenerating = false;
						currentTask = null;
						return;
					} else if (task.status === 'FAILURE') {
						console.log('🎨 【DreamWork轮询】任务失败:', task.failReason);
						toast.error(`即梦生成失败: ${task.failReason || '未知错误'}`);
						isGenerating = false;
						currentTask = null;
						return;
					}
				}

				// 如果还没完成且未达到最大尝试次数，继续轮询
				if (attempts < maxAttempts) {
					setTimeout(poll, 10000); // 10秒后再次轮询
				} else {
					console.log('🎨 【DreamWork轮询】达到最大轮询次数，停止轮询');
					toast.error('即梦任务轮询超时');
					isGenerating = false;
					currentTask = null;
				}
			} catch (error) {
				console.error('🎨 【DreamWork轮询】轮询出错:', error);
				if (attempts < maxAttempts) {
					setTimeout(poll, 10000); // 出错也继续重试
				} else {
					toast.error('即梦任务状态查询失败');
					isGenerating = false;
					currentTask = null;
				}
			}
		};

		// 开始轮询
		poll();
	};

	// Flux 任务状态轮询
	const pollFluxTaskStatus = async (taskId: string) => {
		const maxAttempts = 60; // 最多轮询60次 (约10分钟)
		let attempts = 0;

		const poll = async () => {
			try {
				attempts++;
				console.log(`⚡ 【Flux轮询】第${attempts}次查询任务状态: ${taskId}`);

				const task = await getFluxTaskStatus($user.token, taskId);

				if (task) {
					// 更新当前任务状态
					if (currentTask && currentTask.id === taskId) {
						currentTask = {
							...currentTask,
							status: task.status,
							progress: formatFluxProgress(task),
							imageUrl: getFluxTaskImageUrl(task),
							failReason: task.error_message,
							finishTime: task.completed_at ? new Date(task.completed_at).getTime() : 0
						};
					}

					// 更新历史记录中的任务
					taskHistory = taskHistory.map((t) =>
						t.id === taskId
							? {
									...t,
									status: task.status,
									progress: formatFluxProgress(task),
									imageUrl: getFluxTaskImageUrl(task),
									failReason: task.error_message,
									finishTime: task.completed_at ? new Date(task.completed_at).getTime() : 0
								}
							: t
					);

					if (task.status === 'SUCCESS' || task.status === 'COMPLETED') {
						console.log('⚡ 【Flux轮询】任务完成成功:', task);
						toast.success('Flux图片生成完成!');
						generatedImage = currentTask;
						isGenerating = false;
						currentTask = null;
						return;
					} else if (task.status === 'FAILED' || task.status === 'FAILURE') {
						console.log('⚡ 【Flux轮询】任务失败:', task.error_message);
						toast.error(`Flux生成失败: ${task.error_message || '未知错误'}`);
						isGenerating = false;
						currentTask = null;
						return;
					}
				}

				// 如果还没完成且未达到最大尝试次数，继续轮询
				if (attempts < maxAttempts) {
					setTimeout(poll, 10000); // 10秒后再次轮询
				} else {
					console.log('⚡ 【Flux轮询】达到最大轮询次数，停止轮询');
					toast.error('Flux任务轮询超时');
					isGenerating = false;
					currentTask = null;
				}
			} catch (error) {
				console.error('⚡ 【Flux轮询】轮询出错:', error);
				if (attempts < maxAttempts) {
					setTimeout(poll, 10000); // 出错也继续重试
				} else {
					toast.error('Flux任务状态查询失败');
					isGenerating = false;
					currentTask = null;
				}
			}
		};

		// 开始轮询
		poll();
	};

	// 删除参考图片
	const removeReferenceImage = (id: string, type: 'normal' | 'style' | 'character') => {
		if (type === 'normal') {
			referenceImages = referenceImages.filter((img) => img.id !== id);
		} else if (type === 'style') {
			styleImages = styleImages.filter((img) => img.id !== id);
		} else if (type === 'character') {
			characterImages = characterImages.filter((img) => img.id !== id);
		}
	};

	// 更新图片权重
	const updateImageWeight = (
		id: string,
		weight: number,
		type: 'normal' | 'style' | 'character'
	) => {
		if (type === 'normal') {
			referenceImages = referenceImages.map((img) => (img.id === id ? { ...img, weight } : img));
		} else if (type === 'style') {
			styleImages = styleImages.map((img) => (img.id === id ? { ...img, weight } : img));
		} else if (type === 'character') {
			characterImages = characterImages.map((img) => (img.id === id ? { ...img, weight } : img));
		}
	};

	// DreamWork 图片上传处理
	const handleDreamWorkImageUpload = async (event: Event) => {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) return;

		// 验证文件类型
		if (!file.type.startsWith('image/')) {
			toast.error('请选择图片文件');
			return;
		}

		// 验证文件大小 (10MB)
		if (file.size > 10 * 1024 * 1024) {
			toast.error('图片大小不能超过10MB');
			return;
		}

		try {
			// 转换为base64
			const base64 = await fileToBase64(file);
			dreamWorkInputImage = base64;
			console.log('🎨 【DreamWork】图片上传成功:', file.name);
		} catch (error) {
			console.error('🎨 【DreamWork】图片上传失败:', error);
			toast.error('图片上传失败');
		}

		// 清空input值，允许重复上传同一文件
		target.value = '';
	};

	// Flux 单图上传处理
	const handleFluxImageUpload = async (event: Event) => {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) return;

		// 验证文件类型
		if (!file.type.startsWith('image/')) {
			toast.error('请选择图片文件');
			return;
		}

		// 验证文件大小 (10MB)
		if (file.size > 10 * 1024 * 1024) {
			toast.error('图片大小不能超过10MB');
			return;
		}

		try {
			console.log('⚡ 【Flux】开始上传图片:', file.name);
			const result = await uploadFluxImage($user.token, file);

			if (result.success && result.url) {
				fluxInputImageUrl = result.url;
				console.log('⚡ 【Flux】图片上传成功:', result.url);
				toast.success('图片上传成功');
			} else {
				throw new Error(result.message || '图片上传失败');
			}
		} catch (error) {
			console.error('⚡ 【Flux】图片上传失败:', error);
			toast.error(`图片上传失败: ${error.message || error}`);
		}

		// 清空input值，允许重复上传同一文件
		target.value = '';
	};

	// Flux 多图上传处理
	const handleFluxMultiImageUpload = async (event: Event) => {
		const target = event.target as HTMLInputElement;
		const files = target.files;

		if (!files || files.length === 0) return;

		// 检查文件数量限制
		if (fluxInputImageUrls.length + files.length > 5) {
			toast.error('最多可上传5张图片');
			return;
		}

		for (const file of Array.from(files)) {
			// 验证文件类型
			if (!file.type.startsWith('image/')) {
				toast.error(`${file.name} 不是图片文件`);
				continue;
			}

			// 验证文件大小 (10MB)
			if (file.size > 10 * 1024 * 1024) {
				toast.error(`${file.name} 文件过大（超过10MB）`);
				continue;
			}

			try {
				console.log('⚡ 【Flux多图】开始上传:', file.name);
				const result = await uploadFluxImage($user.token, file);

				if (result.success && result.url) {
					fluxInputImageUrls = [...fluxInputImageUrls, result.url];
					console.log('⚡ 【Flux多图】上传成功:', result.url);
				} else {
					throw new Error(result.message || '上传失败');
				}
			} catch (error) {
				console.error('⚡ 【Flux多图】上传失败:', error);
				toast.error(`${file.name} 上传失败: ${error.message || error}`);
			}
		}

		if (fluxInputImageUrls.length > 0) {
			toast.success(`成功上传 ${files.length} 张图片`);
		}

		// 清空input值，允许重复上传同一文件
		target.value = '';
	};

	// 删除多图中的某张图片
	const removeFluxImage = (index: number) => {
		fluxInputImageUrls = fluxInputImageUrls.filter((_, i) => i !== index);
	};

	// 🔥 简化轮询 - 直接有效
	const pollTaskStatus = async (taskId: string) => {
		console.log('🔥 【轮询调试】开始轮询任务:', taskId);
		console.log('🔥 【轮询调试】$user状态:', $user ? '有用户' : '无用户');
		console.log(
			'🔥 【轮询调试】$user.token状态:',
			$user?.token ? `有token(${$user.token.length}字符)` : '无token'
		);

		if (!$user?.token) {
			console.error('🔥 【轮询调试】无token，停止轮询');
			return;
		}

		// 清除之前的轮询
		if (pollingInterval) {
			clearInterval(pollingInterval);
		}

		pollingInterval = setInterval(async () => {
			try {
				console.log('🔥 轮询检查任务状态:', taskId);
				const task = await getTaskStatus($user.token, taskId);

				if (task) {
					console.log('🔥 任务状态更新:', {
						status: task.status,
						progress: task.progress,
						imageUrl: task.imageUrl,
						hasImage: !!task.imageUrl
					});

					// 更新前端状态
					currentTask = { ...task };
					taskHistory = taskHistory.map((t) => (t.id === task.id ? { ...task } : t));

					// 检查完成
					if (task.status === 'SUCCESS' || task.imageUrl) {
						console.log('🎉 任务完成!');
						generatedImage = { ...task };
						isGenerating = false;
						currentTask = null;

						if (pollingInterval) {
							clearInterval(pollingInterval);
							pollingInterval = null;
						}

						toast.success('图像生成完成！');
						return;
					} else if (task.status === 'FAILURE' || task.status === 'FAILED') {
						console.log('❌ 任务失败');
						isGenerating = false;
						currentTask = null;

						if (pollingInterval) {
							clearInterval(pollingInterval);
							pollingInterval = null;
						}

						toast.error(`生成失败: ${task.failReason || '未知错误'}`);
						return;
					}
				}
			} catch (error) {
				console.error('🔥 轮询出错:', error);
			}
		}, 3000); // 每3秒轮询一次

		// 10分钟超时
		setTimeout(() => {
			if (pollingInterval) {
				clearInterval(pollingInterval);
				pollingInterval = null;
				if (isGenerating) {
					isGenerating = false;
					currentTask = null;
					toast.error('任务超时');
				}
			}
		}, 600000);
	};

	const executeAction = async (customId: string, taskId: string) => {
		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		try {
			const result = await submitActionTask($user.token, taskId, customId);

			if (result && result.code === 1) {
				toast.success('操作已提交');

				// 🔥 立即创建新任务记录显示在UI中
				// 查找原始任务以获取更好的提示词
				const originalTask = taskHistory.find((t) => t.id === taskId);
				const actionLabel = customId.startsWith('MJ::JOB::upsample::')
					? `放大图片 ${customId.slice(-1)}`
					: customId.startsWith('MJ::JOB::variation::')
						? `变体图片 ${customId.slice(-1)}`
						: customId.includes('reroll')
							? '重新生成'
							: `操作 ${customId}`;

				const newTask: MJTask = {
					id: result.result,
					action: 'ACTION',
					status: 'SUBMITTED',
					prompt: originalTask ? `${actionLabel} - ${originalTask.prompt}` : `${actionLabel}`,
					promptEn: originalTask ? `${actionLabel} - ${originalTask.prompt}` : `${actionLabel}`,
					description: `${actionLabel}`,
					submitTime: Date.now(),
					startTime: 0,
					finishTime: 0,
					progress: '0%'
				};

				// 🔥 立即添加到历史记录顶部，用户可以马上看到
				taskHistory = [newTask, ...taskHistory];

				// 🔥 设置为当前任务
				currentTask = newTask;
				isGenerating = true;

				console.log('✅ 新动作任务已添加到历史记录:', newTask.id);

				// 🔥 启动轮询监控新任务
				pollTaskStatus(result.result);
			} else if (result && result.code === 21) {
				// 需要Modal确认
				toast.info('操作需要确认，请稍后...');
				// TODO: 处理Modal确认逻辑
			} else {
				throw new Error(result?.description || '操作失败');
			}
		} catch (error) {
			console.error('Action failed:', error);
			toast.error(`操作失败: ${error.message || error}`);
		}
	};

	// 清理资源
	const cleanup = () => {
		// 清理流媒体订阅
		unsubscribeCallbacks.forEach((unsubscribe) => unsubscribe());
		unsubscribeCallbacks = [];

		// 停止流媒体
		if (streamingActive) {
			mjCallbackHandler.stopAllStreams();
			streamingActive = false;
		}

		// 清理轮询定时器
		if (pollingInterval) {
			clearInterval(pollingInterval);
			pollingInterval = null;
		}
	};

	// 图像查看模态框
	let selectedImageForViewing: MJTask | null = null;
	let isImageModalOpen = false;

	// 复制图片到剪贴板
	const copyImageToClipboard = async (imageUrl: string) => {
		try {
			const response = await fetch(imageUrl);
			const blob = await response.blob();
			await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]);
			toast.success('图片已复制到剪贴板');
		} catch (error) {
			console.error('Failed to copy image:', error);
			toast.error('复制图片失败');
		}
	};

	// 下载图片
	const downloadImage = async (imageUrl: string, filename: string) => {
		try {
			const response = await fetch(imageUrl);
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = filename || 'midjourney-image.png';
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(url);
			document.body.removeChild(a);
			toast.success('图片下载开始');
		} catch (error) {
			console.error('Failed to download image:', error);
			toast.error('下载图片失败');
		}
	};

	// 使用相同参数重新生成
	const regenerateWithSameParams = async (task: MJTask) => {
		if (!task.prompt) {
			toast.error('无法获取原始提示词');
			return;
		}

		// 设置相同的参数
		prompt = task.prompt;

		// 开始生成
		await generateImage();
		toast.info('开始重新生成图像...');
	};

	// 打开图片查看模态框
	const openImageModal = (task: MJTask) => {
		selectedImageForViewing = task;
		isImageModalOpen = true;
	};

	// 关闭图片查看模态框
	const closeImageModal = () => {
		selectedImageForViewing = null;
		isImageModalOpen = false;
	};

	// 格式化进度显示
	const formatProgress = (progress: string | number | undefined, task?: MJTask): string => {
		console.log('🔢 格式化进度:', progress, '类型:', typeof progress, '任务状态:', task?.status);

		// 如果任务已完成且有图片，显示100%
		if (task && task.imageUrl && (task.status === 'SUCCESS' || task.imageUrl)) {
			console.log('🔢 任务已完成，强制显示100%');
			return '100%';
		}

		if (!progress) return '0%';

		if (typeof progress === 'string') {
			// 如果已经是百分比格式，直接返回
			if (progress.includes('%')) return progress;
			// 如果是纯数字字符串，添加%
			const num = parseFloat(progress);
			if (!isNaN(num)) return `${Math.min(Math.max(num, 0), 100)}%`;
			return progress;
		}

		if (typeof progress === 'number') {
			// 数字类型，确保在0-100范围内
			return `${Math.min(Math.max(progress, 0), 100)}%`;
		}

		return '0%';
	};

	// 删除任务
	const handleDeleteTask = async (task: MJTask) => {
		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		try {
			const confirmed = confirm(`确定要删除任务"${task.prompt?.slice(0, 50)}..."吗？`);
			if (!confirmed) return;

			// 根据任务类型调用不同的删除API
			const serviceType = task.properties?.serviceType || 'midjourney';
			console.log(`🗑️ 删除任务: ${task.id}, 服务类型: ${serviceType}`);

			let success = false;
			try {
				if (serviceType === 'dreamwork') {
					success = await deleteDreamWorkTask($user.token, task.id);
				} else if (serviceType === 'flux') {
					success = await deleteFluxTask($user.token, task.id);
				} else {
					success = await deleteTask($user.token, task.id);
				}
			} catch (error) {
				console.error(`删除${serviceType}任务失败:`, error);
				throw error;
			}
			if (success) {
				// 从历史记录中移除任务
				taskHistory = taskHistory.filter((t) => t.id !== task.id);

				// 如果删除的是当前任务，清空当前任务状态
				if (currentTask?.id === task.id) {
					currentTask = null;
					isGenerating = false;
				}

				// 如果删除的是最新生成的图像，清空显示
				if (generatedImage?.id === task.id) {
					generatedImage = null;
				}

				toast.success('任务已删除');
			} else {
				toast.error('删除任务失败');
			}
		} catch (error) {
			console.error('删除任务出错:', error);
			toast.error('删除任务出错');
		}
	};

	// 手动修复任务状态
	const handleManualRepair = async () => {
		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		try {
			console.log('🔧 开始全面修复任务状态...');

			// 1. 先进行本地修复
			forceFixLocalTasks();

			// 2. 强制查询所有可疑任务的远程状态
			await forceRefreshSuspiciousTasks();

			// 3. 再进行服务器端修复
			const result = await fixTaskStates($user.token);
			if (result && result.fixed_count > 0) {
				console.log(`🔧 服务器修复了 ${result.fixed_count} 个任务状态`);
				toast.success(`已修复 ${result.fixed_count} 个服务器任务状态`);
			} else {
				console.log('🔧 服务器端没有需要修复的任务');
			}

			// 4. 重新加载数据以显示修复后的状态
			setTimeout(() => {
				loadUserData();
			}, 1000);

			toast.success('任务状态修复完成！');
		} catch (error) {
			console.error('手动修复任务状态失败:', error);
			toast.error('修复任务状态失败');
		}
	};

	// 组件销毁时清理资源
	import { onDestroy } from 'svelte';
	onDestroy(cleanup);
</script>

<svelte:head>
	<title>
		{$i18n.t('Image Generation')} • {$WEBUI_NAME}
	</title>
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
					<!-- 图像生成服务 -->
					<div>
						<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">图像生成服务</h3>
						<div class="space-y-2">
							{#each availableServices as service}
								<div
									class="rounded-lg p-3 cursor-pointer transition-all {selectedService ===
									service.id
										? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
										: service.enabled
											? 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
											: 'bg-gray-50 dark:bg-gray-900 text-gray-400 dark:text-gray-600 cursor-not-allowed'}"
									on:click={() => service.enabled && (selectedService = service.id)}
								>
									<div class="flex items-center justify-between">
										<div>
											<div class="font-medium">{service.name}</div>
											<div class="text-xs opacity-75">
												{service.enabled ? '已启用' : '未配置'}
											</div>
										</div>
										<div class="text-xl">{service.icon}</div>
									</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- 当前服务信息 -->
					<div class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
						<div>
							当前服务: {selectedService === 'midjourney'
								? 'MidJourney'
								: selectedService === 'dreamwork'
									? '即梦 (DreamWork)'
									: 'Flux AI'}
						</div>
						{#if selectedService === 'midjourney'}
							<div>消耗积分: {modeConfig[selectedMode].credits}积分/次</div>
						{:else if selectedService === 'dreamwork' && dreamWorkConfig}
							<div>消耗积分: {dreamWorkConfig.creditsPerGeneration}积分/次</div>
						{:else if selectedService === 'flux'}
							<div>
								消耗积分: {getFluxModelCredits(selectedFluxModel) * (fluxNumImages || 1)}积分 ({fluxNumImages ||
									1}张图片)
							</div>
						{/if}
						<div class="flex justify-between items-center">
							<div class="text-green-600 dark:text-green-400">余额: {userCredits}积分</div>
							<button
								class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded transition-colors"
								on:click={loadUserData}
								disabled={loadingData}
								title="刷新积分和配置"
							>
								{loadingData ? '刷新中...' : '刷新'}
							</button>
						</div>
					</div>

					<!-- 图像描述 -->
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>图像描述</label
						>
						<textarea
							bind:value={prompt}
							placeholder="描述你想要生成的图像..."
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white resize-none"
							rows="3"
						></textarea>
						<div class="flex justify-between items-center mt-1">
							<div class="text-xs text-gray-500">{prompt.length}/2000</div>
							<button
								on:click={generateImage}
								disabled={isGenerating || !prompt.trim()}
								class="px-4 py-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white text-xs font-medium rounded transition-colors flex items-center gap-1"
							>
								{#if isGenerating}
									<Spinner className="size-3" />
									生成中...
								{:else}
									生成图像 ({selectedService === 'midjourney'
										? modeConfig[selectedMode].credits
										: selectedService === 'dreamwork'
											? dreamWorkConfig?.creditsPerGeneration || 10
											: selectedService === 'flux'
												? `${getFluxModelCredits(selectedFluxModel) * (fluxNumImages || 1)}`
												: 5}积分)
								{/if}
							</button>
						</div>
					</div>

					{#if selectedService === 'midjourney'}
						<!-- MidJourney 参数 -->
						<!-- 模型版本 -->
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>模型版本</label
							>
							<select
								bind:value={selectedVersion}
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
							>
								{#each Object.entries(versionConfig) as [version, config]}
									<option value={version}>{config.label} - {config.description}</option>
								{/each}
							</select>
						</div>

						<!-- 生成模式 -->
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>生成模式</label
							>
							<select
								bind:value={selectedMode}
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
							>
								{#each Object.entries(modeConfig).filter(([mode, config]) => config.enabled) as [mode, config]}
									<option value={mode}>{config.label} ({config.credits}积分)</option>
								{/each}
							</select>
						</div>

						<!-- 图像比例 -->
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>图像比例</label
							>
							<select
								bind:value={selectedAspectRatio}
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
							>
								{#each Object.entries(aspectRatioConfig) as [ratio, config]}
									<option value={ratio}>{ratio} - {config.label}</option>
								{/each}
							</select>
							{#if selectedAspectRatio === 'custom'}
								<div class="mt-2 flex items-center gap-2">
									<input
										type="number"
										bind:value={customWidth}
										min="1"
										max="10"
										class="w-16 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800"
									/>
									<span class="text-sm text-gray-500">:</span>
									<input
										type="number"
										bind:value={customHeight}
										min="1"
										max="10"
										class="w-16 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800"
									/>
								</div>
							{/if}
						</div>
					{:else if selectedService === 'dreamwork' && dreamWorkConfig}
						<!-- DreamWork 参数 -->
						<!-- 模型选择 -->
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>生成模型</label
							>
							<select
								bind:value={dreamWorkTextToImageModel}
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
							>
								<option value="doubao-seedream-3-0-t2i-250415">文生图模型</option>
								<option value="doubao-seededit-3-0-i2i-250628">图生图模型</option>
							</select>
						</div>

						<!-- 输入图片 (图生图模式) -->
						{#if dreamWorkTextToImageModel === 'doubao-seededit-3-0-i2i-250628'}
							<div>
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
									>输入图片</label
								>
								<div
									class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4"
								>
									{#if dreamWorkInputImage}
										<div class="relative">
											<img
												src={dreamWorkInputImage}
												alt="输入图片"
												class="w-full h-32 object-cover rounded"
											/>
											<button
												on:click={() => (dreamWorkInputImage = null)}
												class="absolute top-1 right-1 bg-red-500 hover:bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs transition-colors"
												title="删除图片"
											>
												×
											</button>
										</div>
									{:else}
										<div class="text-center">
											<input
												type="file"
												id="dreamwork-input-image"
												accept="image/*"
												class="hidden"
												on:change={handleDreamWorkImageUpload}
											/>
											<button
												type="button"
												on:click={() => document.getElementById('dreamwork-input-image')?.click()}
												class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded transition-colors"
											>
												选择图片
											</button>
											<div class="text-xs text-gray-500 mt-2">支持 JPG、PNG、WebP，最大 10MB</div>
										</div>
									{/if}
								</div>
							</div>
						{/if}

						<!-- 图片尺寸 -->
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>图片尺寸</label
							>
							<select
								bind:value={dreamWorkSize}
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
							>
								<option value="1024x1024">1024x1024 (正方形)</option>
								<option value="1024x768">1024x768 (4:3)</option>
								<option value="768x1024">768x1024 (3:4)</option>
								<option value="1216x832">1216x832 (3:2)</option>
								<option value="832x1216">832x1216 (2:3)</option>
							</select>
						</div>

						<!-- 引导尺度 -->
						<div>
							<div class="flex justify-between items-center mb-2">
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300">引导尺度</label>
								<span class="text-sm text-gray-500">{dreamWorkGuidanceScale}</span>
							</div>
							<input
								type="range"
								min="1"
								max="20"
								step="0.5"
								bind:value={dreamWorkGuidanceScale}
								class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
							/>
							<div class="flex justify-between text-xs text-gray-400 mt-1">
								<span>1.0</span>
								<span>20.0</span>
							</div>
							<div class="text-xs text-gray-500 mt-1">
								推荐值: 2.5-7.5，数值越高与提示词匹配度越高
							</div>
						</div>

						<!-- 种子值 -->
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>种子值（可选）</label
							>
							<input
								type="number"
								bind:value={seedValue}
								min="0"
								max="4294967295"
								placeholder="留空随机生成"
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
							/>
							<div class="text-xs text-gray-500 mt-1">相同种子值产生相似结果</div>
						</div>

						<!-- 水印设置 -->
						<div class="flex items-center gap-2">
							<input
								type="checkbox"
								id="dreamwork-watermark"
								bind:checked={dreamWorkWatermarkEnabled}
								class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
							/>
							<label for="dreamwork-watermark" class="text-sm text-gray-600 dark:text-gray-400"
								>启用水印</label
							>
						</div>
					{:else if selectedService === 'flux' && fluxConfig}
						<!-- Flux 参数 -->
						<!-- Flux模型选择 - 增强版本信息 -->
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>Flux模型</label
							>
							<select
								bind:value={selectedFluxModel}
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
							>
								{#each fluxModels as model}
									<option value={model.id}>
										{model.name} - {model.description}
										{#if model.id.includes('schnell')}
											(最多4张)
										{:else if model.id.includes('dev')}
											(最多4张)
										{:else if model.id.includes('kontext/max')}
											(最多8张)
										{:else if model.id.includes('kontext')}
											(最多6张)
										{/if}
									</option>
								{/each}
							</select>

							<!-- 模型能力说明 -->
							<div
								class="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-xs text-blue-600 dark:text-blue-400"
							>
								{#if selectedFluxModel.includes('schnell')}
									⚡ 快速模式：1-4推理步数，最多4张图片，适合快速原型制作
								{:else if selectedFluxModel.includes('dev')}
									🔧 开发模式：28步推理，最多4张图片，支持图片尺寸设置
								{:else if selectedFluxModel.includes('kontext/max')}
									🚀 Pro Max：最高质量，最多8张图片，支持比例调节和安全容忍度
								{:else if selectedFluxModel.includes('kontext')}
									💎 Pro版本：专业质量，最多6张图片，支持比例调节和安全容忍度
								{:else}
									📝 标准模式：通用参数配置
								{/if}
							</div>
						</div>

						<!-- 输入图片 -->
						{#if selectedFluxModel.includes('image-to-image')}
							<!-- 单图模式 -->
							<div>
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
									>输入图片</label
								>
								<div
									class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4"
								>
									{#if fluxInputImageUrl}
										<div class="relative">
											<img
												src={fluxInputImageUrl}
												alt="输入图片"
												class="w-full h-32 object-cover rounded"
											/>
											<button
												on:click={() => (fluxInputImageUrl = null)}
												class="absolute top-1 right-1 bg-red-500 hover:bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs transition-colors"
												title="删除图片"
											>
												×
											</button>
										</div>
									{:else}
										<div class="text-center">
											<input
												type="file"
												id="flux-input-image"
												accept="image/*"
												class="hidden"
												on:change={handleFluxImageUpload}
											/>
											<button
												type="button"
												on:click={() => document.getElementById('flux-input-image')?.click()}
												class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded transition-colors"
											>
												选择图片
											</button>
											<div class="text-xs text-gray-500 mt-2">支持 JPG、PNG、WebP，最大 10MB</div>
										</div>
									{/if}
								</div>
							</div>
						{:else if selectedFluxModel.includes('multi')}
							<!-- 多图模式 -->
							<div>
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
									>多图输入 ({fluxInputImageUrls.length}/5)</label
								>
								<div
									class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4"
								>
									{#if fluxInputImageUrls.length > 0}
										<div class="grid grid-cols-2 gap-2 mb-3">
											{#each fluxInputImageUrls as imageUrl, index}
												<div class="relative">
													<img
														src={imageUrl}
														alt={`输入图片 ${index + 1}`}
														class="w-full h-20 object-cover rounded"
													/>
													<button
														on:click={() => removeFluxImage(index)}
														class="absolute top-1 right-1 bg-red-500 hover:bg-red-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs transition-colors"
														title="删除图片"
													>
														×
													</button>
												</div>
											{/each}
										</div>
									{/if}
									<div class="text-center">
										<input
											type="file"
											id="flux-multi-images"
											accept="image/*"
											multiple
											class="hidden"
											on:change={handleFluxMultiImageUpload}
										/>
										<button
											type="button"
											on:click={() => document.getElementById('flux-multi-images')?.click()}
											class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded transition-colors"
											disabled={fluxInputImageUrls.length >= 5}
										>
											{fluxInputImageUrls.length > 0 ? '添加更多图片' : '选择图片'}
										</button>
										<div class="text-xs text-gray-500 mt-2">
											支持多选，JPG、PNG、WebP，最大 10MB/张，最多5张
										</div>
									</div>
								</div>
							</div>
						{/if}

						<!-- 图像尺寸/比例 -->
						{#if selectedFluxModel.includes('pro') || selectedFluxModel.includes('kontext')}
							<!-- Pro/Kontext 模型使用 aspect_ratio -->
							<div>
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
									>图像比例</label
								>
								<select
									bind:value={fluxAspectRatio}
									class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
								>
									<option value="21:9">21:9 (超宽)</option>
									<option value="16:9">16:9 (宽屏)</option>
									<option value="4:3">4:3 (标准)</option>
									<option value="3:2">3:2 (照片)</option>
									<option value="1:1">1:1 (正方形)</option>
									<option value="2:3">2:3 (竖版)</option>
									<option value="3:4">3:4 (社交)</option>
									<option value="9:16">9:16 (竖屏)</option>
									<option value="9:21">9:21 (超长)</option>
								</select>
								<div class="text-xs text-gray-500 mt-1">Pro模型支持的比例选项</div>
							</div>
						{:else}
							<!-- Dev/Schnell 模型使用 image_size -->
							<div>
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
									>图像尺寸</label
								>
								<select
									bind:value={fluxImageSize}
									class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
								>
									<option value="square_hd">正方形高清 (1024x1024)</option>
									<option value="square">正方形 (512x512)</option>
									<option value="portrait_4_3">竖版4:3 (768x1024)</option>
									<option value="portrait_16_9">竖版16:9 (576x1024)</option>
									<option value="landscape_4_3">横版4:3 (1024x768)</option>
									<option value="landscape_16_9">横版16:9 (1024x576)</option>
								</select>
								<div class="text-xs text-gray-500 mt-1">Dev/Schnell模型预设尺寸</div>
							</div>
						{/if}

						<!-- 图片数量选择 - 根据模型动态限制 -->
						<div>
							<div class="flex justify-between items-center mb-2">
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300">图片数量</label>
								<span class="text-sm text-gray-500">{fluxNumImages || 1}</span>
							</div>
							<input
								type="range"
								min="1"
								max={selectedFluxModel.includes('kontext/max')
									? 8
									: selectedFluxModel.includes('kontext')
										? 6
										: 4}
								step="1"
								bind:value={fluxNumImages}
								class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
							/>
							<div class="flex justify-between text-xs text-gray-400 mt-1">
								<span>1张</span>
								<span>
									{selectedFluxModel.includes('kontext/max')
										? '8张'
										: selectedFluxModel.includes('kontext')
											? '6张'
											: '4张'}
								</span>
							</div>
							<div class="text-xs text-gray-500 mt-1">
								{#if selectedFluxModel.includes('kontext/max')}
									Pro Max版本支持最多8张图片同时生成
								{:else if selectedFluxModel.includes('kontext')}
									Pro版本支持最多6张图片同时生成
								{:else}
									Dev/Schnell版本支持最多4张图片同时生成
								{/if}
							</div>
						</div>

						<!-- 引导尺度 -->
						<div>
							<div class="flex justify-between items-center mb-2">
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300">引导尺度</label>
								<span class="text-sm text-gray-500">{fluxGuidanceScale}</span>
							</div>
							<input
								type="range"
								min="1"
								max="20"
								step="0.5"
								bind:value={fluxGuidanceScale}
								class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
							/>
							<div class="flex justify-between text-xs text-gray-400 mt-1">
								<span>1.0</span>
								<span>20.0</span>
							</div>
							<div class="text-xs text-gray-500 mt-1">推荐值: 3.5，数值越高与提示词匹配度越高</div>
						</div>

						<!-- 推理步数 - 根据模型版本智能调整 -->
						{#if !selectedFluxModel.includes('kontext')}
							<div>
								<div class="flex justify-between items-center mb-2">
									<label class="text-sm font-medium text-gray-700 dark:text-gray-300"
										>推理步数</label
									>
									<span class="text-sm text-gray-500">{fluxInferenceSteps}</span>
								</div>
								<input
									type="range"
									min={selectedFluxModel.includes('schnell') ? 1 : 4}
									max={selectedFluxModel.includes('schnell') ? 4 : 50}
									step="1"
									bind:value={fluxInferenceSteps}
									class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
								/>
								<div class="flex justify-between text-xs text-gray-400 mt-1">
									<span>{selectedFluxModel.includes('schnell') ? '1' : '4'}</span>
									<span>{selectedFluxModel.includes('schnell') ? '4' : '50'}</span>
								</div>
								<div class="text-xs text-gray-500 mt-1">
									{#if selectedFluxModel.includes('schnell')}
										⚡ Schnell快速模式：推荐1-4步，更高步数无明显提升
									{:else if selectedFluxModel.includes('dev') && selectedFluxModel.includes('image-to-image')}
										🔄 Dev图生图：推荐40步获得最佳质量
									{:else if selectedFluxModel.includes('dev')}
										🔧 Dev文生图：推荐28步平衡质量与速度
									{:else}
										📝 标准模式：调整步数以平衡质量与生成时间
									{/if}
								</div>
							</div>
						{:else}
							<!-- Pro版本不显示推理步数控制 -->
							<div
								class="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded text-xs text-yellow-600 dark:text-yellow-400"
							>
								💎 Pro版本使用优化的推理参数，无需手动调节步数
							</div>
						{/if}

						<!-- 安全容忍度 (仅Pro模型) -->
						{#if selectedFluxModel.includes('pro') || selectedFluxModel.includes('kontext')}
							<div>
								<div class="flex justify-between items-center mb-2">
									<label class="text-sm font-medium text-gray-700 dark:text-gray-300"
										>安全容忍度</label
									>
									<span class="text-sm text-gray-500">{fluxSafetyTolerance}</span>
								</div>
								<input
									type="range"
									min="1"
									max="6"
									step="1"
									bind:value={fluxSafetyTolerance}
									class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
								/>
								<div class="flex justify-between text-xs text-gray-400 mt-1">
									<span>1 (最严格)</span>
									<span>6 (最宽松)</span>
								</div>
								<div class="text-xs text-gray-500 mt-1">控制内容审核严格程度，Pro模型专有参数</div>
							</div>
						{/if}

						<!-- 图生图强度 -->
						{#if selectedFluxModel.includes('image-to-image')}
							<div>
								<div class="flex justify-between items-center mb-2">
									<label class="text-sm font-medium text-gray-700 dark:text-gray-300">强度</label>
									<span class="text-sm text-gray-500">{fluxStrength}</span>
								</div>
								<input
									type="range"
									min="0.1"
									max="1.0"
									step="0.05"
									bind:value={fluxStrength}
									class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
								/>
								<div class="flex justify-between text-xs text-gray-400 mt-1">
									<span>0.1</span>
									<span>1.0</span>
								</div>
								<div class="text-xs text-gray-500 mt-1">数值越高变化越大，推荐0.95</div>
							</div>
						{/if}

						<!-- 种子值 -->
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>种子值（可选）</label
							>
							<input
								type="number"
								bind:value={seedValue}
								min="0"
								max="4294967295"
								placeholder="留空随机生成"
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
							/>
							<div class="text-xs text-gray-500 mt-1">相同种子值产生相似结果</div>
						</div>

						<!-- 安全检查 -->
						<div class="flex items-center gap-2">
							<input
								type="checkbox"
								id="flux-safety-checker"
								bind:checked={fluxEnableSafetyChecker}
								class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
							/>
							<label for="flux-safety-checker" class="text-sm text-gray-600 dark:text-gray-400"
								>启用安全检查</label
							>
						</div>
					{/if}

					{#if selectedService === 'midjourney'}
						<!-- 负面提示词 -->
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>负面提示词（可选）</label
							>
							<textarea
								bind:value={negativePrompt}
								placeholder="描述你不希望在画面中呈现的内容..."
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white resize-none"
								rows="2"
							></textarea>
						</div>
					{/if}

					{#if selectedService === 'midjourney'}
						<!-- 高级选项 -->
						<div>
							<details class="group" open>
								<summary
									class="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer flex items-center gap-2"
								>
									<span class="group-open:rotate-90 transition-transform">▶</span>
									高级选项
								</summary>
								<div class="mt-3 space-y-3 pl-4">
									<!-- 混乱程度 -->
									<div>
										<div class="flex justify-between items-center mb-1">
											<label class="text-xs text-gray-600 dark:text-gray-400"
												>混乱程度 (0-100)</label
											>
											<span class="text-xs text-gray-500">{chaosLevel}</span>
										</div>
										<input
											type="range"
											min="0"
											max="100"
											bind:value={chaosLevel}
											class="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
										/>
									</div>

									<!-- 风格化程度 -->
									<div>
										<div class="flex justify-between items-center mb-1">
											<label class="text-xs text-gray-600 dark:text-gray-400"
												>风格化程度 (0-1000)</label
											>
											<span class="text-xs text-gray-500">{stylizeLevel}</span>
										</div>
										<input
											type="range"
											min="0"
											max="1000"
											bind:value={stylizeLevel}
											class="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
										/>
									</div>

									<!-- 奇异程度 -->
									<div>
										<div class="flex justify-between items-center mb-1">
											<label class="text-xs text-gray-600 dark:text-gray-400"
												>奇异程度 (0-3000)</label
											>
											<span class="text-xs text-gray-500">{weirdLevel}</span>
										</div>
										<input
											type="range"
											min="0"
											max="3000"
											bind:value={weirdLevel}
											class="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
										/>
										<div class="mt-1 text-xs text-gray-400">留空使用默认值</div>
									</div>

									<!-- 平铺模式 -->
									<div class="flex items-center gap-2">
										<input
											type="checkbox"
											id="tile-mode"
											bind:checked={enableTile}
											class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
										/>
										<label for="tile-mode" class="text-xs text-gray-600 dark:text-gray-400"
											>平铺模式</label
										>
									</div>

									<!-- 种子值 -->
									<div>
										<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">种子值</label
										>
										<input
											type="text"
											bind:value={seedValue}
											placeholder="留空随机生成"
											class="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
										/>
									</div>

									<!-- 图像质量 -->
									<div>
										<div class="flex justify-between items-center mb-1">
											<label class="text-xs text-gray-600 dark:text-gray-400">图像质量 (1)</label>
											<span class="text-xs text-gray-500">{selectedQuality}</span>
										</div>
										<input
											type="range"
											min="0.25"
											max="2"
											step="0.25"
											bind:value={selectedQuality}
											class="w-full h-1 bg-blue-200 dark:bg-blue-700 rounded-lg appearance-none cursor-pointer slider"
										/>
										<div class="flex justify-between text-xs text-gray-400 mt-1">
											<span>0.25</span>
											<span>2.0</span>
										</div>
									</div>
								</div>
							</details>
						</div>

						<!-- 参考图片区域 -->
						<div>
							<details class="group" open>
								<summary
									class="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer flex items-center gap-2"
								>
									<span class="group-open:rotate-90 transition-transform">▶</span>
									参考图片（可选）
								</summary>
								<div class="mt-3 space-y-4 pl-4">
									<!-- 普通参考图 -->
									<div>
										<div class="flex items-center justify-between mb-2">
											<label class="text-xs font-medium text-gray-600 dark:text-gray-400"
												>普通参考图 ({referenceImages.length}/5)</label
											>
											<button
												on:click={() => document.getElementById('normal-ref-input')?.click()}
												class="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-600 dark:text-blue-400 rounded transition-colors"
											>
												添加图片
											</button>
										</div>
										<input
											id="normal-ref-input"
											type="file"
											accept="image/*"
											multiple
											class="hidden"
											on:change={(e) => handleImageUpload(e.target.files, 'normal')}
										/>
										{#if referenceImages.length > 0}
											<div class="grid grid-cols-2 gap-2">
												{#each referenceImages as image (image.id)}
													<div
														class="relative group border border-gray-200 dark:border-gray-600 rounded overflow-hidden"
													>
														<img
															src={image.base64}
															alt={image.filename}
															class="w-full h-16 object-cover"
														/>
														<div
															class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100"
														>
															<button
																on:click={() => removeReferenceImage(image.id, 'normal')}
																class="text-white hover:text-red-300 transition-colors"
															>
																🗑️
															</button>
														</div>
														<div
															class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs px-1 py-0.5"
														>
															权重: {image.weight}
														</div>
													</div>
												{/each}
											</div>
										{:else}
											<div
												class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded p-4 text-center"
											>
												<div class="text-gray-400 text-xs">拖拽图片到这里或点击添加</div>
											</div>
										{/if}
									</div>

									<!-- 风格参考图 -->
									<div>
										<div class="flex items-center justify-between mb-2">
											<label class="text-xs font-medium text-gray-600 dark:text-gray-400"
												>风格参考图 ({styleImages.length}/5)</label
											>
											<button
												on:click={() => document.getElementById('style-ref-input')?.click()}
												class="px-2 py-1 text-xs bg-purple-100 hover:bg-purple-200 dark:bg-purple-900 dark:hover:bg-purple-800 text-purple-600 dark:text-purple-400 rounded transition-colors"
											>
												添加风格图
											</button>
										</div>
										<input
											id="style-ref-input"
											type="file"
											accept="image/*"
											multiple
											class="hidden"
											on:change={(e) => handleImageUpload(e.target.files, 'style')}
										/>
										{#if styleImages.length > 0}
											<div class="grid grid-cols-2 gap-2">
												{#each styleImages as image (image.id)}
													<div
														class="relative group border border-purple-200 dark:border-purple-600 rounded overflow-hidden"
													>
														<img
															src={image.base64}
															alt={image.filename}
															class="w-full h-16 object-cover"
														/>
														<div
															class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100"
														>
															<button
																on:click={() => removeReferenceImage(image.id, 'style')}
																class="text-white hover:text-red-300 transition-colors"
															>
																🗑️
															</button>
														</div>
														<div
															class="absolute bottom-0 left-0 right-0 bg-purple-600 bg-opacity-75 text-white text-xs px-1 py-0.5"
														>
															风格: {image.weight}
														</div>
													</div>
												{/each}
											</div>
										{:else}
											<div
												class="border-2 border-dashed border-purple-300 dark:border-purple-600 rounded p-4 text-center"
											>
												<div class="text-purple-400 text-xs">添加风格参考图片</div>
											</div>
										{/if}
									</div>
								</div>
							</details>
						</div>
					{/if}

					<!-- 最新生成的图像 -->
					{#if generatedImage}
						<div
							class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3"
						>
							<div class="flex justify-between items-center mb-2">
								<span class="text-sm font-medium text-green-700 dark:text-green-300">最新生成</span>
								<span class="text-xs text-green-600 dark:text-green-400">已完成</span>
							</div>
							{#if generatedImage.imageUrl}
								<div class="relative mb-2">
									<img
										src={generatedImage.imageUrl}
										alt={generatedImage.prompt}
										class="w-full h-32 object-cover rounded cursor-pointer"
										on:click={() => openImageModal(generatedImage)}
										on:error={(e) => {
											console.error('❌ 图片加载失败:', generatedImage.imageUrl);
											console.error('❌ 错误详情:', e);
										}}
										on:load={() => {
											console.log('✅ 图片加载成功:', generatedImage.imageUrl);
										}}
									/>
								</div>
							{:else}
								<div
									class="w-full h-32 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center text-gray-500"
								>
									<span class="text-sm">暂无图片</span>
								</div>
							{/if}
							<div class="text-xs text-green-600 dark:text-green-400 truncate">
								{generatedImage.prompt}
							</div>
						</div>
					{/if}

					<!-- 当前任务状态 -->
					{#if currentTask}
						<div
							class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3"
						>
							<div class="flex justify-between items-center mb-2">
								<span class="text-sm font-medium text-blue-700 dark:text-blue-300">当前任务</span>
								<span class="text-xs text-blue-600 dark:text-blue-400">{currentTask.status}</span>
							</div>
							<div class="text-xs text-blue-600 dark:text-blue-400 mb-2 truncate">
								{currentTask.prompt}
							</div>
							<div
								class="flex items-center justify-between text-xs text-blue-600 dark:text-blue-400 mb-1"
							>
								<span>生成进度</span>
								<span>{formatProgress(currentTask.progress, currentTask)}</span>
							</div>
							<div class="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-1.5">
								<div
									class="bg-gradient-to-r from-blue-500 to-blue-600 h-1.5 rounded-full transition-all duration-500 ease-out"
									style="width: {formatProgress(currentTask.progress, currentTask)}"
								></div>
							</div>
						</div>
					{/if}
				</div>
			</div>

			<!-- 右侧历史记录栏 -->
			<div class="flex-1 flex flex-col bg-white dark:bg-gray-800">
				<!-- 搜索栏 -->
				<div class="p-4 border-b border-gray-200 dark:border-gray-600">
					<div class="flex flex-col gap-3">
						<!-- 搜索输入 -->
						<div class="flex items-center justify-between">
							<div class="relative flex-1 max-w-md">
								<input
									type="text"
									bind:value={searchQuery}
									placeholder="搜索图像历史..."
									class="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
								/>
								<div class="absolute left-3 top-2.5 text-gray-400">
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
										></path>
									</svg>
								</div>
							</div>
							<div class="flex items-center gap-3">
								<div class="text-sm text-gray-500 dark:text-gray-400">
									{#if searchQuery || selectedStatusFilter !== 'all' || selectedTimeFilter !== 'all'}
										显示 {filteredTaskHistory.length} / {taskHistory.length} 张图像
									{:else}
										共 {taskHistory.length} 张图像
									{/if}
								</div>
								<button
									class="px-3 py-1 text-xs bg-purple-100 hover:bg-purple-200 dark:bg-purple-900 dark:hover:bg-purple-800 text-purple-600 dark:text-purple-400 rounded transition-colors"
									on:click={handleManualRepair}
									title="修复任务状态 - 将已完成但显示不正确的任务状态修复"
								>
									修复状态
								</button>
							</div>
						</div>

						<!-- 筛选选项 -->
						<div class="flex items-center gap-3 text-sm">
							<div class="flex items-center gap-2">
								<span class="text-gray-600 dark:text-gray-400">状态:</span>
								<select
									bind:value={selectedStatusFilter}
									class="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
								>
									<option value="all">全部</option>
									<option value="SUCCESS">成功</option>
									<option value="IN_PROGRESS">进行中</option>
									<option value="SUBMITTED">已提交</option>
									<option value="FAILURE">失败</option>
								</select>
							</div>

							<div class="flex items-center gap-2">
								<span class="text-gray-600 dark:text-gray-400">时间:</span>
								<select
									bind:value={selectedTimeFilter}
									class="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
								>
									<option value="all">全部</option>
									<option value="today">今天</option>
									<option value="week">本周</option>
									<option value="month">本月</option>
								</select>
							</div>

							<!-- 清除筛选 -->
							{#if searchQuery || selectedStatusFilter !== 'all' || selectedTimeFilter !== 'all'}
								<button
									on:click={() => {
										searchQuery = '';
										selectedStatusFilter = 'all';
										selectedTimeFilter = 'all';
									}}
									class="px-2 py-1 text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
								>
									清除筛选
								</button>
							{/if}
						</div>
					</div>
				</div>

				<!-- 历史记录网格 -->
				<div class="flex-1 p-4 overflow-y-auto scrollbar-hide">
					{#if filteredTaskHistory.length > 0}
						<div class="grid grid-cols-3 gap-4">
							{#each filteredTaskHistory as task (task.id)}
								<div
									class="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
								>
									<!-- 版本标签 -->
									<div class="absolute top-2 left-2 z-10">
										<span
											class="px-2 py-1 text-xs font-medium text-white rounded {task.properties
												?.serviceType === 'dreamwork'
												? 'bg-gradient-to-r from-purple-500 to-pink-500'
												: task.properties?.serviceType === 'flux'
													? 'bg-gradient-to-r from-blue-500 to-cyan-500'
													: 'bg-purple-600'}"
										>
											{#if task.properties?.serviceType === 'dreamwork'}
												即梦 (DreamWork)
											{:else if task.properties?.serviceType === 'flux'}
												Flux AI
											{:else}
												{task.properties?.botType === 'NIJI_JOURNEY' ? 'Niji3.0' : 'MidJourney'}
											{/if}
										</span>
									</div>

									<!-- 图片 -->
									{#if task.imageUrl}
										<div class="relative aspect-square">
											<img
												src={task.imageUrl}
												alt={task.prompt}
												class="w-full h-full object-cover cursor-pointer"
												on:click={() => openImageModal(task)}
											/>
											<!-- 悬停操作层 -->
											<div
												class="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center opacity-0 hover:opacity-100"
											>
												<div class="flex flex-col gap-1">
													<div class="flex gap-1">
														<button
															on:click|stopPropagation={() => copyImageToClipboard(task.imageUrl)}
															class="px-2 py-1 bg-white bg-opacity-90 text-black text-xs rounded hover:bg-opacity-100 transition-all font-medium"
														>
															复制
														</button>
														<button
															on:click|stopPropagation={() =>
																downloadImage(
																	task.imageUrl,
																	`${task.properties?.serviceType === 'dreamwork' ? 'dreamwork' : task.properties?.serviceType === 'flux' ? 'flux' : 'mj'}-${task.id}.png`
																)}
															class="px-2 py-1 bg-green-500 bg-opacity-90 text-white text-xs rounded hover:bg-opacity-100 transition-all font-medium"
														>
															下载
														</button>
													</div>
													<div class="flex gap-1">
														<button
															on:click|stopPropagation={() => regenerateWithSameParams(task)}
															class="px-2 py-1 bg-blue-500 bg-opacity-90 text-white text-xs rounded hover:bg-opacity-100 transition-all font-medium"
														>
															重新生成
														</button>
														<button
															on:click|stopPropagation={() => openImageModal(task)}
															class="px-2 py-1 bg-gray-500 bg-opacity-90 text-white text-xs rounded hover:bg-opacity-100 transition-all font-medium"
														>
															查看大图
														</button>
													</div>
													<button
														on:click|stopPropagation={() => handleDeleteTask(task)}
														class="px-2 py-1 bg-red-500 bg-opacity-90 text-white text-xs rounded hover:bg-opacity-100 transition-all font-medium"
													>
														删除
													</button>
												</div>
											</div>
										</div>
									{:else if task.status === 'FAILURE' || task.status === 'FAILED'}
										<div
											class="aspect-square bg-red-100 dark:bg-red-900 flex items-center justify-center"
										>
											<div class="text-red-500 text-xs">生成失败</div>
										</div>
									{:else if task.status === 'SUCCESS'}
										<div
											class="aspect-square bg-yellow-100 dark:bg-yellow-900 flex items-center justify-center"
										>
											<div class="text-yellow-600 text-xs">已完成<br />无图片</div>
										</div>
									{:else}
										<div
											class="aspect-square bg-gray-100 dark:bg-gray-700 flex items-center justify-center relative"
										>
											<div class="text-center">
												<div class="text-gray-400 text-xs mb-1">
													{task.status === 'SUBMITTED' || task.status === 'NOT_START'
														? '等待中...'
														: '生成中...'}
												</div>
												<div class="text-gray-500 text-xs">
													{formatProgress(task.progress, task)}
												</div>
											</div>
										</div>
									{/if}

									<!-- 内容信息 -->
									<div class="p-3">
										<!-- 标题和删除按钮 -->
										<div class="flex items-center justify-between mb-1">
											<div
												class="font-medium text-sm text-gray-900 dark:text-white truncate flex-1"
											>
												{task.prompt?.split(' ').slice(0, 4).join(' ') || '无标题'}
											</div>
											<button
												on:click|stopPropagation={() => handleDeleteTask(task)}
												class="ml-2 px-2 py-1 text-xs text-gray-400 hover:text-white hover:bg-red-500 dark:text-gray-500 dark:hover:text-white dark:hover:bg-red-500 rounded transition-colors"
												title="删除任务"
											>
												删除
											</button>
										</div>

										<!-- 模型和时间 -->
										<div
											class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-2"
										>
											<span>
												{#if task.properties?.serviceType === 'dreamwork'}
													即梦 ({task.action === 'IMAGE_TO_IMAGE' ? '图生图' : '文生图'})
												{:else if task.properties?.serviceType === 'flux'}
													Flux ({task.action === 'IMAGE_TO_IMAGE' ? '图生图' : '文生图'})
												{:else}
													MidJourney (fast)
												{/if}
											</span>
											<span>{new Date(task.submitTime).toLocaleDateString()}</span>
										</div>

										<!-- 操作按钮 -->
										{#if task.buttons && task.buttons.length > 0}
											<div class="space-y-2">
												<!-- U1-U4 按钮 -->
												<div class="grid grid-cols-4 gap-1">
													{#each task.buttons.filter((btn) => btn.label?.startsWith('U')) as button}
														<button
															on:click={() => executeAction(button.customId, task.id)}
															class="px-2 py-1 text-xs border border-green-300 text-green-600 rounded hover:bg-green-50 dark:border-green-600 dark:text-green-400 dark:hover:bg-green-900 transition-colors"
														>
															{button.label}
														</button>
													{/each}
												</div>

												<!-- V1-V4 按钮 -->
												<div class="grid grid-cols-4 gap-1">
													{#each task.buttons.filter((btn) => btn.label?.startsWith('V')) as button}
														<button
															on:click={() => executeAction(button.customId, task.id)}
															class="px-2 py-1 text-xs border border-blue-300 text-blue-600 rounded hover:bg-blue-50 dark:border-blue-600 dark:text-blue-400 dark:hover:bg-blue-900 transition-colors"
														>
															{button.label}
														</button>
													{/each}
												</div>

												<!-- 其他按钮 -->
												<div class="grid grid-cols-2 gap-1">
													{#each task.buttons.filter((btn) => !btn.label?.startsWith('U') && !btn.label?.startsWith('V')) as button}
														<button
															on:click={() => executeAction(button.customId, task.id)}
															class="px-2 py-1 text-xs border border-gray-300 text-gray-600 rounded hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700 transition-colors flex items-center justify-center"
														>
															{button.emoji}
															{button.label || '操作'}
														</button>
													{/each}
												</div>
											</div>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div
							class="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400"
						>
							{#if taskHistory.length === 0}
								<div class="text-4xl mb-4">🎨</div>
								<div class="text-lg font-medium mb-2">暂无生成历史</div>
								<div class="text-sm">开始您的第一次图像生成吧！</div>
							{:else}
								<div class="text-4xl mb-4">🔍</div>
								<div class="text-lg font-medium mb-2">未找到匹配的图像</div>
								<div class="text-sm">尝试调整搜索条件或筛选器</div>
								<button
									on:click={() => {
										searchQuery = '';
										selectedStatusFilter = 'all';
										selectedTimeFilter = 'all';
									}}
									class="mt-3 px-3 py-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 border border-blue-300 dark:border-blue-600 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
								>
									清除所有筛选
								</button>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- 图片查看模态框 -->
	{#if isImageModalOpen && selectedImageForViewing}
		<div
			class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 backdrop-blur-sm"
			on:click={closeImageModal}
		>
			<div
				class="relative max-w-4xl max-h-[90vh] mx-4 bg-white dark:bg-gray-800 rounded-lg overflow-hidden shadow-2xl"
				on:click|stopPropagation
			>
				<!-- 模态框头部 -->
				<div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
					<div class="flex items-center gap-3">
						<span
							class="px-2 py-1 text-xs font-medium text-white rounded {selectedImageForViewing
								.properties?.serviceType === 'dreamwork'
								? 'bg-gradient-to-r from-purple-500 to-pink-500'
								: selectedImageForViewing.properties?.serviceType === 'flux'
									? 'bg-gradient-to-r from-blue-500 to-cyan-500'
									: 'bg-purple-600'}"
						>
							{#if selectedImageForViewing.properties?.serviceType === 'dreamwork'}
								即梦 (DreamWork)
							{:else if selectedImageForViewing.properties?.serviceType === 'flux'}
								Flux AI
							{:else}
								{selectedImageForViewing.properties?.botType === 'NIJI_JOURNEY'
									? 'Niji3.0'
									: 'MidJourney'}
							{/if}
						</span>
						<div class="text-sm font-medium text-gray-900 dark:text-white">
							{selectedImageForViewing.prompt?.split(' ').slice(0, 8).join(' ') || '无标题'}
						</div>
					</div>
					<button
						on:click={closeImageModal}
						class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
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
				</div>

				<!-- 图片显示区域 -->
				<div class="relative">
					<img
						src={selectedImageForViewing.imageUrl}
						alt={selectedImageForViewing.prompt}
						class="w-full max-h-[70vh] object-contain"
					/>
				</div>

				<!-- 模态框底部操作栏 -->
				<div
					class="flex items-center justify-between p-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-750"
				>
					<div class="flex items-center gap-3">
						<div class="text-xs text-gray-500 dark:text-gray-400">
							生成时间: {new Date(selectedImageForViewing.submitTime).toLocaleString()}
						</div>
						<div class="text-xs text-gray-500 dark:text-gray-400">
							状态: {selectedImageForViewing.status}
						</div>
						{#if selectedImageForViewing.progress}
							<div class="text-xs text-gray-500 dark:text-gray-400">
								进度: {selectedImageForViewing.progress}
							</div>
						{/if}
					</div>

					<div class="flex items-center gap-2">
						<button
							on:click={() => copyImageToClipboard(selectedImageForViewing.imageUrl)}
							class="px-3 py-1.5 text-sm bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded transition-colors"
						>
							复制
						</button>
						<button
							on:click={() =>
								downloadImage(
									selectedImageForViewing.imageUrl,
									`${selectedImageForViewing.properties?.serviceType === 'dreamwork' ? 'dreamwork' : selectedImageForViewing.properties?.serviceType === 'flux' ? 'flux' : 'mj'}-${selectedImageForViewing.id}.png`
								)}
							class="px-3 py-1.5 text-sm bg-green-500 hover:bg-green-600 text-white rounded transition-colors"
						>
							下载
						</button>
						<button
							on:click={() => {
								regenerateWithSameParams(selectedImageForViewing);
								closeImageModal();
							}}
							class="px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
						>
							重新生成
						</button>
					</div>
				</div>

				<!-- 提示词详情 -->
				{#if selectedImageForViewing.prompt}
					<div class="p-4 border-t dark:border-gray-700 bg-gray-25 dark:bg-gray-850">
						<div class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">完整提示词:</div>
						<div class="text-sm text-gray-600 dark:text-gray-400 break-words">
							{selectedImageForViewing.prompt}
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
{/if}

<style>
	/* 隐藏滚动条 */
	.scrollbar-hide {
		scrollbar-width: none; /* Firefox */
		-ms-overflow-style: none; /* Internet Explorer 10+ */
	}
	.scrollbar-hide::-webkit-scrollbar {
		display: none; /* WebKit */
	}
</style>
