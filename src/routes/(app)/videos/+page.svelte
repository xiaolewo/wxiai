<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, showSidebar, user, mobile, config } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	// Import Kling API functions
	import {
		type KlingTask,
		type KlingConfig,
		type KlingGenerateRequest,
		type KlingVideoMode,
		type KlingVideoExtendRequest,
		type KlingVideoExtendCheck,
		submitKlingTextToVideoTask,
		submitKlingImageToVideoTask,
		getKlingTaskStatus,
		getKlingUserTaskHistory,
		getKlingUserCredits,
		getKlingUserConfig,
		deleteKlingTask,
		checkKlingVideoExtendEligibility,
		submitKlingVideoExtendTask,
		getKlingVideoExtendTaskStatus
	} from '$lib/apis/kling';

	// Import JiMeng API functions
	import {
		type JimengTask,
		type JimengConfig,
		type JimengGenerateRequest,
		submitJimengTextToVideoTask,
		submitJimengImageToVideoTask,
		getJimengTaskStatus,
		getJimengUserTaskHistory,
		getJimengUserCredits,
		getJimengUserConfig,
		deleteJimengTask
	} from '$lib/apis/jimeng';

	// Import Veo API functions
	import {
		type VeoTask,
		type VeoUserConfig,
		type VeoGenerateRequest,
		submitVeoTextToVideoTask,
		submitVeoImageToVideoTask,
		getVeoTaskStatus,
		getVeoUserTaskHistory,
		getVeoUserCredits,
		getVeoUserConfig,
		deleteVeoTask
	} from '$lib/apis/veo';

	const i18n = getContext('i18n');

	let loaded = false;
	let isGenerating = false;
	let currentTask: KlingTask | JimengTask | VeoTask | null = null;
	let generatedVideo: KlingTask | JimengTask | VeoTask | null = null;
	let taskHistory: (KlingTask | JimengTask | VeoTask)[] = [];
	let userCredits = 0;
	let loadingData = false;
	let pollingInterval: NodeJS.Timeout | null = null;
	let klingConfig: KlingConfig | null = null;
	let jimengConfig: JimengConfig | null = null;
	let veoConfig: VeoUserConfig | null = null;

	// 视频延长相关状态
	let extendingTasks = new Set<string>(); // 正在检查或延长中的任务ID
	let extendChecks = new Map<string, KlingVideoExtendCheck>(); // 延长资格检查结果缓存

	// Service selection
	let selectedService: 'kling' | 'jimeng' | 'veo' = 'kling';
	let lastServiceSwitch = '';
	let serviceSwitchTimeout: NodeJS.Timeout | null = null;

	// 当服务切换时，防抖处理
	$: if (selectedService && loaded && selectedService !== lastServiceSwitch) {
		console.log(`🎬 【服务切换】检测到切换: ${lastServiceSwitch} → ${selectedService}`);
		lastServiceSwitch = selectedService;

		// 清除之前的延时器
		if (serviceSwitchTimeout) {
			clearTimeout(serviceSwitchTimeout);
		}

		// 延迟执行，避免频繁触发
		serviceSwitchTimeout = setTimeout(async () => {
			console.log(`🎬 【服务切换】执行切换逻辑到: ${selectedService}`);

			// 确保配置已加载，如果没有则加载
			if (selectedService === 'jimeng' && !jimengConfig) {
				await loadJimengConfig();
			} else if (selectedService === 'kling' && !klingConfig) {
				await loadKlingConfig();
			} else if (selectedService === 'veo' && !veoConfig) {
				await loadVeoConfig();
			}

			// 立即刷新一次积分
			await refreshCredits();

			// 根据选择的服务设置水印默认值和模型默认值
			if (selectedService === 'jimeng' && jimengConfig?.defaultWatermark !== undefined) {
				watermark = jimengConfig.defaultWatermark;
			} else if (selectedService === 'kling') {
				watermark = false; // 可灵服务没有水印功能
				// 设置默认Kling模型
				if (!selectedModel.startsWith('kling-') && !selectedModel.includes('pro')) {
					selectedModel = 'kling-v1';
				}
			} else if (selectedService === 'veo') {
				watermark = false; // Veo服务没有水印功能
				// 设置默认Veo模型
				const veoModels = ['veo3', 'veo3-fast', 'veo3-pro', 'veo3-pro-frames', 'veo2', 'veo2-fast', 'veo2-fast-frames', 'veo2-fast-components', 'veo2-pro', 'veo3-fast-frames'];
				// 确保配置已加载后再设置默认模型
				if (veoConfig?.default_model) {
					selectedModel = veoConfig.default_model;
					console.log(`🎯 【Veo模型】已设置默认模型: ${veoConfig.default_model}`);
				} else if (!veoModels.includes(selectedModel)) {
					selectedModel = 'veo3'; // 如果当前模型不是Veo模型，使用默认值
					console.log(`🎯 【Veo模型】回退到默认模型: veo3`);
				}
			}
		}, 100); // 100ms防抖
	}

	// 基础参数
	let prompt = '';
	let negativePrompt = '';
	let selectedMode: KlingVideoMode = 'std';
	let selectedDuration = '5';
	let selectedAspectRatio = '16:9';
	let cfgScale = 0.5;
	let selectedModel = 'kling-v1'; // 选择的模型版本
	let watermark = false; // 水印设置
	let enhancePrompt = true; // Veo提示词优化

	// 图生视频参数
	let inputImage: string | null = null; // base64数据
	let imageTail: string | null = null; // 尾帧图片
	let selectedGenerationType: 'text-to-video' | 'image-to-video' = 'text-to-video';

	// 多图参考参数
	let multiImages: Array<{ image: string; preview: string }> = []; // 多图参考列表
	const maxMultiImages = 4;
	
	// Veo专用图片输入
	let veoImage1: string | null = null; // Veo第一张图片
	let veoImage2: string | null = null; // Veo第二张图片（首尾帧模式）
	let veoImage3: string | null = null; // Veo第三张图片（组件模式）
	let selectedVeoImageMode: 'single' | 'frames' | 'components' = 'single'; // Veo图片模式

	// 图生视频高级功能
	let staticMask: string | null = null; // 静态笔刷
	let dynamicMasks: Array<{ mask: string; trajectories: Array<{ x: number; y: number }> }> = []; // 动态笔刷
	let selectedImageVideoMode: 'basic' | 'first-last' | 'brush' | 'camera' | 'multi-image' = 'basic'; // 图生视频模式

	// 摄像机控制参数
	let cameraControlType:
		| 'simple'
		| 'down_back'
		| 'forward_up'
		| 'right_turn_forward'
		| 'left_turn_forward' = 'simple';
	let cameraControlConfig = {
		horizontal: 0,
		vertical: 0,
		pan: 0,
		tilt: 0,
		roll: 0,
		zoom: 0
	};

	// 搜索和筛选
	let searchQuery = '';
	let selectedStatusFilter = 'all';
	let selectedTimeFilter = 'all';

	// 文生视频模型选项
	const textToVideoModelOptions = [
		{ value: 'kling-v1', label: 'Kling V1' },
		{ value: 'kling-v1-6', label: 'Kling V1.6' },
		{ value: 'kling-v2-master', label: 'Kling V2 Master' },
		{ value: 'kling-v2-1-master', label: 'Kling V2.1 Master' }
	];

	// 图生视频模型选项
	const imageToVideoModelOptions = [
		{ value: 'kling-v1', label: 'Kling V1' },
		{ value: 'kling-v1-5', label: 'Kling V1.5' },
		{ value: 'kling-v1-6', label: 'Kling V1.6' },
		{ value: 'kling-v2-master', label: 'Kling V2 Master' },
		{ value: 'kling-v2-1', label: 'Kling V2.1' },
		{ value: 'kling-v2-1-master', label: 'Kling V2.1 Master' }
	];

	// Veo模型选项
	const veoModelOptions = [
		{ value: 'veo3', label: 'Veo 3 (最新)', description: '最新版本', type: 'text' },
		{ value: 'veo3-fast', label: 'Veo 3 Fast', description: '快速版本，生成速度更快', type: 'text' },
		{ value: 'veo3-pro', label: 'Veo 3 Pro', description: '专业版本，质量更高', type: 'text' },
		{ value: 'veo3-pro-frames', label: 'Veo 3 Pro Frames', description: '支持图生视频(单张图片)', type: 'image' },
		{ value: 'veo2', label: 'Veo 2', description: '稳定版本，平衡速度与质量', type: 'text' },
		{ value: 'veo2-fast', label: 'Veo 2 Fast', description: '快速版本', type: 'text' },
		{ value: 'veo2-fast-frames', label: 'Veo 2 Fast Frames', description: '支持图生视频(首尾帧)', type: 'image' },
		{ value: 'veo2-fast-components', label: 'Veo 2 Fast Components', description: '支持多图片输入(视频元素)', type: 'image' },
		{ value: 'veo2-pro', label: 'Veo 2 Pro', description: '专业版本', type: 'text' },
		{ value: 'veo3-fast-frames', label: 'Veo 3 Fast Frames', description: '支持图生视频的快速版本', type: 'image' }
	];

	// 根据生成类型和服务获取当前可用的模型选项
	$: currentModelOptions = (() => {
		if (selectedService === 'veo') {
			// Veo根据生成类型过滤支持的模型
			if (selectedGenerationType === 'text-to-video') {
				return veoModelOptions.filter(option => option.type === 'text');
			} else {
				return veoModelOptions.filter(option => option.type === 'image');
			}
		} else if (selectedService === 'kling') {
			return selectedGenerationType === 'text-to-video' ? textToVideoModelOptions : imageToVideoModelOptions;
		} else {
			// Jimeng 暂时使用固定选项
			return [{ value: 'jimeng-default', label: '即梦默认' }];
		}
	})();

	// 验证并修正选中的模型 - 确保模型在当前可用选项中
	$: if (currentModelOptions && currentModelOptions.length > 0 && selectedService && loaded) {
		const availableValues = currentModelOptions.map(option => option.value);
		console.log(`🔍 【模型验证】服务: ${selectedService}, 当前模型: ${selectedModel}, 可用模型: [${availableValues.join(', ')}]`);
		
		// 如果当前选中的模型不在可用选项中
		if (!availableValues.includes(selectedModel)) {
			console.log(`⚠️ 【模型验证】当前模型 "${selectedModel}" 不在可用选项中，需要修正`);
			
			// 优先选择后端配置的默认模型
			let newModel = null;
			
			if (selectedService === 'veo' && veoConfig?.default_model && availableValues.includes(veoConfig.default_model)) {
				newModel = veoConfig.default_model;
				console.log(`🎯 【模型验证】使用Veo默认模型: ${newModel}`);
			} else if (selectedService === 'kling' && availableValues.includes('kling-v1')) {
				newModel = 'kling-v1';
				console.log(`🎬 【模型验证】使用可灵默认模型: ${newModel}`);
			} else if (selectedService === 'jimeng' && availableValues.includes('jimeng-default')) {
				newModel = 'jimeng-default';
				console.log(`🌟 【模型验证】使用即梦默认模型: ${newModel}`);
			} else {
				// 如果没有匹配的默认模型，使用第一个可用模型
				newModel = availableValues[0];
				console.log(`⚠️ 【模型验证】使用第一个可用模型: ${newModel}`);
			}
			
			if (newModel && newModel !== selectedModel) {
				console.log(`🔄 【模型验证】模型修正: ${selectedModel} → ${newModel}`);
				selectedModel = newModel;
				console.log(`✅ 【模型验证】模型已修正为: ${selectedModel}`);
			}
		} else {
			console.log(`✅ 【模型验证】当前模型 "${selectedModel}" 有效，无需修正`);
		}
	}

	// 根据选择的Veo模型自动设置图片模式
	$: if (selectedService === 'veo' && selectedGenerationType === 'image-to-video') {
		if (selectedModel.includes('components')) {
			selectedVeoImageMode = 'components'; // 三张图片模式
		} else if (selectedModel === 'veo3-pro-frames') {
			selectedVeoImageMode = 'single'; // veo3-pro-frames只支持单张图片
		} else if (selectedModel.includes('frames')) {
			selectedVeoImageMode = 'frames'; // 首尾帧模式（两张图片）
		} else {
			selectedVeoImageMode = 'single'; // 单张图片模式
		}
	}

	// 图生视频模式选项 - 可灵服务才显示首尾帧模式
	$: imageVideoModeOptions = (() => {
		const baseOptions = [
			{ value: 'basic', label: '基础模式', desc: '仅使用首帧图片' },
			{ value: 'brush', label: '笔刷模式', desc: '使用静态或动态笔刷控制' },
			{ value: 'camera', label: '摄像机控制', desc: '使用摄像机运镜控制' }
		];

		// 首尾帧模式仅在可灵服务下可用
		if (selectedService === 'kling') {
			// 在基础模式后插入首尾帧模式
			baseOptions.splice(1, 0, {
				value: 'first-last',
				label: '首尾帧模式',
				desc: '同时使用首帧和尾帧图片 (自动使用V1.6专家模式)'
			});

			// 在首尾帧模式后插入多图参考模式
			baseOptions.splice(2, 0, {
				value: 'multi-image',
				label: '多图参考',
				desc: '使用多张参考图片（仅V1.6，最多4张，积分不变）'
			});
		}

		return baseOptions;
	})();

	// 当选择首尾帧模式时，自动设置模型和视频模式
	$: {
		if (selectedImageVideoMode === 'first-last' && selectedService === 'kling') {
			// 自动设置为可灵V1.6模型和专家模式
			if (selectedModel !== 'kling-v1-6') {
				selectedModel = 'kling-v1-6';
				console.log('🎬 【首尾帧模式】自动切换到可灵V1.6模型');
			}
			if (selectedMode !== 'pro') {
				selectedMode = 'pro';
				console.log('🎬 【首尾帧模式】自动切换到专家模式');
			}
		}
	}

	// 当选择多图参考模式时，自动设置模型
	$: {
		if (selectedImageVideoMode === 'multi-image' && selectedService === 'kling') {
			// 多图参考模式只支持可灵V1.6模型
			if (selectedModel !== 'kling-v1-6') {
				selectedModel = 'kling-v1-6';
				console.log('🎬 【多图参考模式】自动切换到可灵V1.6模型');
			}
		}
	}

	// 视频模式选项
	const modeOptions = [
		{ value: 'std', label: '标准模式 (Standard)' },
		{ value: 'pro', label: '专家模式 (Pro)' }
	];

	// 视频时长选项
	const durationOptions = [
		{ value: '5', label: '5秒' },
		{ value: '10', label: '10秒' }
	];

	// 画面比例选项 - 根据选择的服务动态切换
	$: aspectRatioOptions = (() => {
		if (selectedService === 'kling') {
			return [
				{ value: '16:9', label: '16:9 (横向)' },
				{ value: '9:16', label: '9:16 (竖向)' },
				{ value: '1:1', label: '1:1 (正方形)' }
			];
		} else if (selectedService === 'veo') {
			return []; // Veo不支持自定义画面比例，由模型决定
		} else {
			// Jimeng
			return [
				{ value: '1:1', label: '1:1 (正方形)' },
				{ value: '21:9', label: '21:9 (超宽屏)' },
				{ value: '16:9', label: '16:9 (横向)' },
				{ value: '9:16', label: '9:16 (竖向)' },
				{ value: '4:3', label: '4:3 (传统)' },
				{ value: '3:4', label: '3:4 (竖向传统)' }
			];
		}
	})();

	// 筛选后的历史记录
	$: filteredTaskHistory = taskHistory.filter((task) => {
		// 搜索筛选
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			const matchPrompt = task.prompt?.toLowerCase().includes(query);
			if (!matchPrompt) {
				return false;
			}
		}

		// 状态筛选
		if (selectedStatusFilter !== 'all' && task.status !== selectedStatusFilter) {
			return false;
		}

		// 时间筛选
		if (selectedTimeFilter !== 'all') {
			const taskDate = new Date(task.submitTime || '');
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
		console.log('🎬 【可灵视频页面】onMount执行');

		if (!$user) {
			console.log('🎬 【可灵视频页面】用户未登录，跳转到登录页');
			goto('/auth');
			return;
		}
		loaded = true;

		// 初始模型状态调试信息
		console.log(`🔍 【初始状态】selectedService: ${selectedService}, selectedModel: ${selectedModel}`);

		await loadUserData();

		// 数据加载完成后的状态调试信息
		console.log(`🔍 【数据加载后】selectedService: ${selectedService}, selectedModel: ${selectedModel}`);

		// 清除可能存在的旧定时器
		if (creditRefreshInterval) {
			clearInterval(creditRefreshInterval);
		}

		// 设置积分余额定期刷新 (每30秒)
		creditRefreshInterval = setInterval(async () => {
			console.log('⏰ 【定时刷新】30秒定时器触发，检查条件...');
			if (!isGenerating && $user?.token) {
				console.log('⏰ 【定时刷新】条件满足，执行积分刷新');
				await refreshCredits();
			} else {
				console.log(
					`⏰ 【定时刷新】跳过: isGenerating=${isGenerating}, hasToken=${!!$user?.token}`
				);
			}
		}, 30000);

		console.log('🎬 【积分刷新】设置定期刷新: 每30秒');
	});

	const loadKlingConfig = async () => {
		if (!$user?.token) return;

		try {
			const config = await getKlingUserConfig($user.token);
			if (config) {
				klingConfig = config;
				console.log('🎬 可灵配置已加载:', config);
			}
		} catch (error) {
			console.error('加载可灵配置失败:', error);
		}
	};

	const loadJimengConfig = async () => {
		if (!$user?.token) return;

		try {
			const config = await getJimengUserConfig($user.token);
			if (config) {
				jimengConfig = config;
				// 如果当前选择的是即梦服务，设置默认水印值
				if (selectedService === 'jimeng' && config.defaultWatermark !== undefined) {
					watermark = config.defaultWatermark;
				}
				console.log('🌟 即梦配置已加载:', config);
			}
		} catch (error) {
			console.error('加载即梦配置失败:', error);
		}
	};

	const loadVeoConfig = async () => {
		if (!$user?.token) return;

		try {
			const config = await getVeoUserConfig($user.token);
			if (config) {
				veoConfig = config;
				console.log('🎯 Veo配置已加载:', config);
			}
		} catch (error) {
			console.error('加载Veo配置失败:', error);
		}
	};

	const loadUserData = async () => {
		console.log('🎬 【数据加载调试】loadUserData开始');

		if (!$user?.token) {
			console.error('🎬 【数据加载调试】没有token，无法加载数据');
			return;
		}

		loadingData = true;
		try {
			// 加载所有配置
			await Promise.all([loadKlingConfig(), loadJimengConfig(), loadVeoConfig()]);

			// 配置加载完成后，根据当前选择的服务设置正确的默认模型
			if (selectedService === 'veo' && veoConfig?.default_model) {
				selectedModel = veoConfig.default_model;
				console.log(`🎯 【初始化】为Veo服务设置默认模型: ${veoConfig.default_model}`);
			} else if (selectedService === 'kling' && (!selectedModel.startsWith('kling-') && !selectedModel.includes('pro'))) {
				selectedModel = 'kling-v1';
				console.log(`🎬 【初始化】为可灵服务设置默认模型: kling-v1`);
			} else if (selectedService === 'jimeng') {
				// 即梦服务使用固定模型
				selectedModel = 'jimeng-default';
				console.log(`🌟 【初始化】为即梦服务设置默认模型: jimeng-default`);
			}

			// 检查当前选择的服务是否可用
			let currentConfig = null;
			let serviceName = '';
			
			if (selectedService === 'kling') {
				currentConfig = klingConfig;
				serviceName = '可灵';
			} else if (selectedService === 'jimeng') {
				currentConfig = jimengConfig;
				serviceName = '即梦';
			} else if (selectedService === 'veo') {
				currentConfig = veoConfig;
				serviceName = 'Veo';
			}
			
			if (!currentConfig?.enabled) {
				toast.error(`${serviceName}视频服务未启用，请联系管理员配置或切换到其他服务`);

				// 尝试切换到可用的服务
				if (selectedService === 'kling' && (jimengConfig?.enabled || veoConfig?.enabled)) {
					if (jimengConfig?.enabled) {
						selectedService = 'jimeng';
						selectedModel = 'jimeng-default';
						toast.info('已自动切换到即梦视频服务');
					} else if (veoConfig?.enabled) {
						selectedService = 'veo';
						selectedModel = veoConfig.default_model || 'veo3';
						toast.info('已自动切换到Veo视频服务');
					}
				} else if (selectedService === 'jimeng' && (klingConfig?.enabled || veoConfig?.enabled)) {
					if (klingConfig?.enabled) {
						selectedService = 'kling';
						selectedModel = 'kling-v1';
						toast.info('已自动切换到可灵视频服务');
					} else if (veoConfig?.enabled) {
						selectedService = 'veo';
						selectedModel = veoConfig.default_model || 'veo3';
						toast.info('已自动切换到Veo视频服务');
					}
				} else if (selectedService === 'veo' && (klingConfig?.enabled || jimengConfig?.enabled)) {
					if (klingConfig?.enabled) {
						selectedService = 'kling';
						selectedModel = 'kling-v1';
						toast.info('已自动切换到可灵视频服务');
					} else if (jimengConfig?.enabled) {
						selectedService = 'jimeng';
						selectedModel = 'jimeng-default';
						toast.info('已自动切换到即梦视频服务');
					}
				}
			}

			// 加载用户积分
			let getCreditsFunction;
			let serviceDisplayName;
			
			if (selectedService === 'kling') {
				getCreditsFunction = getKlingUserCredits;
				serviceDisplayName = '可灵';
			} else if (selectedService === 'jimeng') {
				getCreditsFunction = getJimengUserCredits;
				serviceDisplayName = '即梦';
			} else if (selectedService === 'veo') {
				getCreditsFunction = getVeoUserCredits;
				serviceDisplayName = 'Veo';
			}
			
			const credits = await getCreditsFunction($user.token);
			if (credits) {
				userCredits = credits.balance || 0;
				console.log(`🎬 【${serviceDisplayName}】积分余额加载:`, userCredits);
			} else {
				console.warn(`🎬 【${serviceDisplayName}】积分余额加载失败`);
			}

			// 加载用户历史记录 - 混合显示三种服务的记录
			const [klingHistory, jimengHistory, veoHistory] = await Promise.all([
				klingConfig?.enabled
					? getKlingUserTaskHistory($user.token, 1, 10).catch(() => ({ data: [] }))
					: { data: [] },
				jimengConfig?.enabled
					? getJimengUserTaskHistory($user.token, 1, 10).catch(() => ({ data: [] }))
					: { data: [] },
				veoConfig?.enabled
					? getVeoUserTaskHistory($user.token, 1, 10).catch(() => ({ data: [] }))
					: { data: [] }
			]);

			// 合并和排序历史记录（后端已经包含serviceType字段）
			const allTasks = [...(klingHistory.data || []), ...(jimengHistory.data || []), ...(veoHistory.data || [])].sort(
				(a, b) => {
					const timeA = new Date(a.submitTime || a.createdAt || '').getTime();
					const timeB = new Date(b.submitTime || b.createdAt || '').getTime();
					return timeB - timeA; // 降序排列，最新的在前
				}
			);

			taskHistory = allTasks;
			console.log('🎬 加载历史记录:', taskHistory.length, '个任务');

			// 页面刷新后恢复最新完成的视频状态
			if (!generatedVideo && taskHistory.length > 0) {
				const latestCompletedTask = taskHistory.find(
					(task) => task.videoUrl && (task.status === 'succeed' || task.videoUrl)
				);

				if (latestCompletedTask) {
					console.log('🎬 页面刷新后恢复最新生成视频:', latestCompletedTask.id);
					generatedVideo = { ...latestCompletedTask };
				}
			}
		} catch (error) {
			console.error('Failed to load user data:', error);
			toast.error('加载用户数据失败');
		} finally {
			loadingData = false;
		}
	};

	// 专门的积分刷新函数
	const refreshCredits = async () => {
		if (!$user?.token) {
			console.log('💰 【积分刷新】跳过: 没有用户token');
			return;
		}

		let serviceDisplayName;
		let getCreditsFunction;
		
		if (selectedService === 'kling') {
			serviceDisplayName = '可灵';
			getCreditsFunction = getKlingUserCredits;
		} else if (selectedService === 'jimeng') {
			serviceDisplayName = '即梦';
			getCreditsFunction = getJimengUserCredits;
		} else if (selectedService === 'veo') {
			serviceDisplayName = 'Veo';
			getCreditsFunction = getVeoUserCredits;
		}

		console.log(`💰 【积分刷新】开始获取${serviceDisplayName}积分...`);
		try {
			const credits = await getCreditsFunction($user.token);
			if (credits) {
				const oldBalance = userCredits;
				userCredits = credits.balance || 0;
				console.log(`💰 【积分刷新】${serviceDisplayName}积分: ${oldBalance} → ${userCredits}`);
			} else {
				console.log(`💰 【积分刷新】${serviceDisplayName}积分API返回空结果`);
			}
		} catch (error) {
			console.warn(`💰 【积分刷新】获取${serviceDisplayName}积分失败:`, error);
		}
	};

	const generateVideo = async () => {
		if (!prompt.trim()) {
			toast.error('请输入视频描述');
			return;
		}

		let currentConfig, serviceName;
		if (selectedService === 'kling') {
			currentConfig = klingConfig;
			serviceName = '可灵';
		} else if (selectedService === 'jimeng') {
			currentConfig = jimengConfig;
			serviceName = '即梦';
		} else if (selectedService === 'veo') {
			currentConfig = veoConfig;
			serviceName = 'Veo';
		}

		// 生成前重新获取最新配置，确保积分设置是最新的
		console.log(`🎬 【${serviceName}】生成前刷新配置和积分...`);
		await Promise.all([loadKlingConfig(), loadJimengConfig(), loadVeoConfig()]);

		// 重新获取积分余额以确保是最新的
		let getCreditsFunction;
		if (selectedService === 'kling') {
			getCreditsFunction = getKlingUserCredits;
		} else if (selectedService === 'jimeng') {
			getCreditsFunction = getJimengUserCredits;
		} else if (selectedService === 'veo') {
			getCreditsFunction = getVeoUserCredits;
		}
		
		const latestCredits = await getCreditsFunction($user.token);
		if (latestCredits) {
			userCredits = latestCredits.balance || 0;
			console.log(`🎬 【${serviceName}】生成前最新积分余额: ${userCredits}`);
		}

		if (!currentConfig || !currentConfig.enabled) {
			toast.error(`${serviceName}视频服务未配置或未启用`);
			return;
		}

		// 检查积分
		if (userCredits < requiredCredits) {
			toast.error(`积分不足，需要${requiredCredits}积分，当前余额${userCredits}积分`);
			return;
		}

		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		// 图生视频模式验证
		if (selectedGenerationType === 'image-to-video') {
			if (selectedService === 'veo') {
				// Veo图生视频验证
				if (!veoImage1) {
					toast.error('图生视频模式需要至少上传一张图片');
					return;
				}
				if (selectedVeoImageMode === 'frames' && !veoImage2) {
					toast.error('首尾帧模式需要上传两张图片');
					return;
				}
				if (selectedVeoImageMode === 'components' && (!veoImage2 || !veoImage3)) {
					toast.error('组件模式需要上传三张图片');
					return;
				}
			} else {
				// 可灵和即梦使用原有验证
				// 多图参考模式跳过单图验证
				if (selectedService === 'kling' && selectedImageVideoMode === 'multi-image') {
					// 多图模式验证将在可灵特有功能验证中处理
				} else if (!inputImage) {
					toast.error('图生视频模式需要上传输入图片');
					return;
				}

				// 可灵特有的高级功能验证
				if (selectedService === 'kling') {
					// 首尾帧模式验证
					if (selectedImageVideoMode === 'first-last' && !imageTail) {
						toast.error('首尾帧模式需要同时上传首帧和尾帧图片');
						return;
					}

					// 笔刷模式验证
					if (selectedImageVideoMode === 'brush' && !staticMask && dynamicMasks.length === 0) {
						toast.error('笔刷模式需要上传静态笔刷或配置动态笔刷');
						return;
					}

					// 多图参考模式验证
					if (selectedImageVideoMode === 'multi-image') {
						if (multiImages.length === 0) {
							toast.error('多图参考模式需要至少上传1张图片');
							return;
						}
						if (multiImages.length > maxMultiImages) {
							toast.error(`多图参考模式最多支持${maxMultiImages}张图片`);
							return;
						}
						// 验证模型是否为 kling-v1-6
						if (selectedModel !== 'kling-v1-6') {
							toast.error('多图参考模式只支持 kling-v1-6 模型');
							return;
						}
					}
				}
			}
		}

		isGenerating = true;
		try {
			// 构建生成请求 - 根据选择的服务
			let request: KlingGenerateRequest | JimengGenerateRequest | VeoGenerateRequest;

			if (selectedService === 'kling') {
				request = {
					modelName: selectedModel, // 使用用户选择的模型版本
					prompt: prompt.trim(),
					negativePrompt: negativePrompt.trim() || undefined,
					cfgScale: cfgScale,
					mode: selectedMode,
					duration: selectedDuration,
					aspectRatio: selectedAspectRatio
				} as KlingGenerateRequest;
			} else if (selectedService === 'jimeng') {
				// 即梦请求参数更简单
				request = {
					prompt: prompt.trim(),
					duration: selectedDuration,
					aspectRatio: selectedAspectRatio,
					cfgScale: cfgScale,
					watermark: watermark
				} as JimengGenerateRequest;
			} else if (selectedService === 'veo') {
				// Veo请求参数
				request = {
					prompt: prompt.trim(),
					model: selectedModel,
					enhance_prompt: enhancePrompt
				} as VeoGenerateRequest;
			}

			// 如果是图生视频，添加图片和相关参数
			if (selectedGenerationType === 'image-to-video') {
				if (selectedService === 'veo') {
					// Veo使用专用的图片数组
					const images: string[] = [];
					if (veoImage1) images.push(veoImage1);
					if (veoImage2) images.push(veoImage2);
					if (veoImage3) images.push(veoImage3);
					(request as VeoGenerateRequest).images = images;
				} else {
					// 可灵和即梦使用原有的inputImage
					if (inputImage) {
						let base64Data = inputImage;
						if (inputImage.startsWith('data:')) {
							base64Data = inputImage.split(',')[1];
						}

						if (selectedService === 'kling') {
							(request as KlingGenerateRequest).image = base64Data;
						} else if (selectedService === 'jimeng') {
							// 即梦支持两种方式：image (base64) 或 imageUrl
							// 这里使用 base64 方式
							(request as JimengGenerateRequest).image = base64Data;
						}
					}
				}
			}

				// 可灵特有的高级功能
				if (selectedService === 'kling') {
					const klingRequest = request as KlingGenerateRequest;

					// 根据选择的模式添加不同的参数
					if (selectedImageVideoMode === 'multi-image' && multiImages.length > 0) {
						// 多图参考模式
						klingRequest.generationMode = 'multi_image';
						klingRequest.imageList = multiImages.map(img => ({
							image: img.image.startsWith('data:') ? img.image.split(',')[1] : img.image
						}));
						console.log('🎬 【可灵多图】设置多图参考:', multiImages.length, '张图片');
					} else if (selectedImageVideoMode === 'first-last' && imageTail) {
						// 尾帧模式
						let tailBase64 = imageTail;
						if (imageTail.startsWith('data:')) {
							tailBase64 = imageTail.split(',')[1];
						}
						klingRequest.imageTail = tailBase64;
					} else if (selectedImageVideoMode === 'brush') {
						// 笔刷模式
						if (staticMask) {
							let maskBase64 = staticMask;
							if (staticMask.startsWith('data:')) {
								maskBase64 = staticMask.split(',')[1];
							}
							klingRequest.staticMask = maskBase64;
						}

						if (dynamicMasks.length > 0) {
							klingRequest.dynamicMasks = dynamicMasks.map((dm) => ({
								mask: dm.mask.startsWith('data:') ? dm.mask.split(',')[1] : dm.mask,
								trajectories: dm.trajectories
							}));
						}
					} else if (selectedImageVideoMode === 'camera') {
						// 摄像机控制模式
						if (cameraControlType !== 'simple') {
							// 预定义运镜类型
							klingRequest.cameraControl = {
								type: cameraControlType
							};
						} else {
							// 简单运镜模式 - 检查是否有非零参数
							const hasValidConfig = Object.values(cameraControlConfig).some(
								(value) => value !== 0
							);
							if (hasValidConfig) {
								// 确保只有一个参数不为0（根据API文档要求）
								const nonZeroParams = Object.entries(cameraControlConfig).filter(
									([key, value]) => value !== 0
								);
								if (nonZeroParams.length === 1) {
									klingRequest.cameraControl = {
										type: 'simple',
										config: cameraControlConfig
									};
								} else if (nonZeroParams.length > 1) {
									toast.error('简单运镜模式只能设置一个非零参数');
									isGenerating = false;
									return;
								}
							}
						}
					}
				}

			// 为所有可灵视频生成添加摄像机控制支持（文生视频和图生视频）
			if (selectedService === 'kling') {
				const klingRequest = request as KlingGenerateRequest;

				// 如果图生视频没有设置摄像机控制，或者是文生视频，则应用通用摄像机控制
				if (!klingRequest.cameraControl) {
					if (cameraControlType !== 'simple') {
						// 预定义运镜类型
						klingRequest.cameraControl = {
							type: cameraControlType
						};
					} else {
						// 简单运镜模式 - 检查是否有非零参数
						const hasValidConfig = Object.values(cameraControlConfig).some((value) => value !== 0);
						if (hasValidConfig) {
							const nonZeroParams = Object.entries(cameraControlConfig).filter(
								([key, value]) => value !== 0
							);
							if (nonZeroParams.length === 1) {
								klingRequest.cameraControl = {
									type: 'simple',
									config: cameraControlConfig
								};
							} else if (nonZeroParams.length > 1) {
								toast.error('简单运镜模式只能设置一个非零参数');
								isGenerating = false;
								return;
							}
						}
					}
				}
			}

			console.log(`🎬 【${serviceName}前端】提交视频生成任务:`, {
				service: selectedService,
				type: selectedGenerationType,
				model:
					selectedService === 'kling'
						? (request as KlingGenerateRequest).modelName
						: selectedService === 'veo'
						? (request as VeoGenerateRequest).model
						: 'jimeng-default',
				hasInputImage: !!(request as any).image || !!(request as any).images,
				prompt: request.prompt
			});

			// 调用对应的API
			let result;
			if (selectedService === 'kling') {
				result =
					selectedGenerationType === 'image-to-video'
						? await submitKlingImageToVideoTask($user.token, request as KlingGenerateRequest)
						: await submitKlingTextToVideoTask($user.token, request as KlingGenerateRequest);
			} else if (selectedService === 'jimeng') {
				result =
					selectedGenerationType === 'image-to-video'
						? await submitJimengImageToVideoTask($user.token, request as JimengGenerateRequest)
						: await submitJimengTextToVideoTask($user.token, request as JimengGenerateRequest);
			} else if (selectedService === 'veo') {
				result =
					selectedGenerationType === 'image-to-video'
						? await submitVeoImageToVideoTask($user.token, request as VeoGenerateRequest)
						: await submitVeoTextToVideoTask($user.token, request as VeoGenerateRequest);
			}

			if (result && result.success) {
				// 提交成功，立即查询真实积分余额（后端已扣除）
				try {
					const getCreditsFunction =
						selectedService === 'kling' ? getKlingUserCredits : 
						selectedService === 'jimeng' ? getJimengUserCredits : getVeoUserCredits;
					const credits = await getCreditsFunction($user.token);
					if (credits) {
						userCredits = credits.balance || 0;
						console.log(`🎬 【${serviceName}】任务提交成功，当前积分余额: ${userCredits}`);
					}
				} catch (error) {
					console.warn(`🎬 【${serviceName}】更新积分余额失败:`, error);
				}

				// 创建任务记录 - 兼容两种服务
				const baseTask = {
					id: result.task_id,
					userId: $user.id,
					action: selectedGenerationType === 'image-to-video' 
						? (selectedService === 'kling' && selectedImageVideoMode === 'multi-image' 
							? 'MULTI_IMAGE_TO_VIDEO' 
							: 'IMAGE_TO_VIDEO') 
						: 'TEXT_TO_VIDEO',
					status: 'submitted',
					prompt: prompt.trim(),
					duration: selectedDuration,
					aspectRatio: selectedAspectRatio,
					cfgScale: cfgScale,
					inputImage: selectedGenerationType === 'image-to-video' ? inputImage : undefined,
					creditsCost: requiredCredits,
					submitTime: new Date().toISOString(),
					progress: '0%',
					createdAt: new Date().toISOString(),
					updatedAt: new Date().toISOString(),
					serviceType: selectedService
				};

				if (selectedService === 'kling') {
					currentTask = {
						...baseTask,
						negativePrompt: negativePrompt.trim() || undefined,
						mode: selectedMode,
						modelName: selectedModel
					} as KlingTask & { serviceType: 'kling' };
				} else {
					currentTask = {
						...baseTask
					} as JimengTask & { serviceType: 'jimeng' };
				}

				toast.success(
					`${serviceName}${selectedGenerationType === 'image-to-video' ? '图生视频' : '文生视频'}任务已提交，开始生成...`
				);

				// 立即添加到历史记录
				taskHistory = [currentTask, ...taskHistory];

				// 开始轮询任务状态
				pollTaskStatus(result.task_id, selectedService);
			} else {
				console.error(`🎬 【${serviceName}前端】API返回错误:`, result);
				throw new Error(result?.message || `${serviceName}任务提交失败`);
			}
		} catch (error) {
			console.error('Video generation failed:', error);
			toast.error(`生成失败: ${error.message || error}`);
			isGenerating = false;
			currentTask = null;
		}
	};

	// 计算所需积分 - 响应式计算属性
	$: requiredCredits = (() => {
		let currentConfig;
		
		if (selectedService === 'kling') {
			currentConfig = klingConfig;
		} else if (selectedService === 'jimeng') {
			currentConfig = jimengConfig;
		} else if (selectedService === 'veo') {
			currentConfig = veoConfig;
		}

		if (!currentConfig) {
			console.log(`💰 【积分计算】配置未加载，使用默认值: 50`);
			return 50;
		}

		if (selectedService === 'kling') {
			// 可灵的积分配置
			const config = currentConfig as KlingConfig;

			// 优先使用模型版本特定的积分配置
			if (config.modelCreditsConfig && selectedModel && config.modelCreditsConfig[selectedModel]) {
				const modelConfig = config.modelCreditsConfig[selectedModel];
				if (modelConfig[selectedMode] && modelConfig[selectedMode][selectedDuration]) {
					const credits = modelConfig[selectedMode][selectedDuration];
					console.log(
						`💰 【可灵积分计算】模型特定配置: ${selectedModel}-${selectedMode}-${selectedDuration} = ${credits}积分`
					);
					return credits;
				}
			}

			// 使用默认积分配置（模型版本积分配置不可用时的回退方案）
			let credits = 50;
			if (selectedMode === 'std' && selectedDuration === '5') credits = 50;
			else if (selectedMode === 'std' && selectedDuration === '10') credits = 100;
			else if (selectedMode === 'pro' && selectedDuration === '5') credits = 100;
			else if (selectedMode === 'pro' && selectedDuration === '10') credits = 200;

			console.log(
				`💰 【可灵积分计算】默认配置: ${selectedMode}-${selectedDuration} = ${credits}积分`
			);
			return credits;
		} else if (selectedService === 'jimeng') {
			// 即梦的积分配置更简单
			const config = currentConfig as JimengConfig;
			let credits = 50;
			if (selectedDuration === '5') credits = config.creditsPer5s;
			else if (selectedDuration === '10') credits = config.creditsPer10s;

			console.log(`💰 【即梦积分计算】${selectedDuration}秒 = ${credits}积分`);
			return credits;
		} else if (selectedService === 'veo') {
			// Veo的积分配置基于模型
			const config = currentConfig as VeoUserConfig;
			const credits = config.model_credits_config[selectedModel] || 100;
			
			console.log(`💰 【Veo积分计算】模型 ${selectedModel} = ${credits}积分`);
			return credits;
		}
		
		return 50; // 默认值
	})();

	// 轮询任务状态
	const pollTaskStatus = async (taskId: string, service: 'kling' | 'jimeng' | 'veo') => {
		let serviceName;
		if (service === 'kling') {
			serviceName = '可灵';
		} else if (service === 'jimeng') {
			serviceName = '即梦';
		} else if (service === 'veo') {
			serviceName = 'Veo';
		}
		
		console.log(`🎬 【${serviceName}轮询】开始轮询任务:`, taskId);

		if (!$user?.token) {
			console.error(`🎬 【${serviceName}轮询】无token，停止轮询`);
			return;
		}

		// 清除之前的轮询
		if (pollingInterval) {
			clearInterval(pollingInterval);
		}

		const maxAttempts = 120; // 最多轮询120次 (约20分钟)
		let attempts = 0;

		pollingInterval = setInterval(async () => {
			try {
				attempts++;
				console.log(`🎬 【${serviceName}轮询】第${attempts}次查询任务状态: ${taskId}`);

				let getTaskStatusFunction;
				if (service === 'kling') {
					getTaskStatusFunction = getKlingTaskStatus;
				} else if (service === 'jimeng') {
					getTaskStatusFunction = getJimengTaskStatus;
				} else if (service === 'veo') {
					getTaskStatusFunction = getVeoTaskStatus;
				}
				
				const task = await getTaskStatusFunction($user.token, taskId);

				if (task) {
					console.log(`🎬 【${serviceName}轮询】任务状态更新:`, {
						status: task.status,
						progress: task.progress,
						videoUrl: task.videoUrl,
						hasVideo: !!task.videoUrl
					});

					// 更新前端状态（后端已返回serviceType）
					if (currentTask && currentTask.id === taskId) {
						currentTask = { ...task };
					}

					// 更新历史记录中的任务（后端已返回serviceType）
					taskHistory = taskHistory.map((t) => (t.id === taskId ? { ...task } : t));

					// 检查完成
					if (task.status === 'succeed' || task.videoUrl) {
						console.log(`🎉 ${serviceName}视频任务完成!`);
						generatedVideo = { ...task };
						isGenerating = false;
						currentTask = null;

						if (pollingInterval) {
							clearInterval(pollingInterval);
							pollingInterval = null;
						}

						// 更新积分余额
						try {
							const getCreditsFunction =
								service === 'kling' ? getKlingUserCredits : 
								service === 'jimeng' ? getJimengUserCredits : getVeoUserCredits;
							const credits = await getCreditsFunction($user.token);
							if (credits) {
								const oldBalance = userCredits;
								userCredits = credits.balance || 0;
								console.log(
									`🎬 【${serviceName}】任务完成后积分余额更新: ${oldBalance} → ${userCredits}`
								);
							}
						} catch (error) {
							console.warn(`🎬 【${serviceName}】更新积分余额失败:`, error);
						}

						toast.success('视频生成完成！');
						return;
					} else if (task.status === 'failed') {
						console.log(`❌ ${serviceName}视频任务失败`);
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

				// 检查超时
				if (attempts >= maxAttempts) {
					console.log(`🎬 【${serviceName}轮询】达到最大轮询次数，停止轮询`);
					if (pollingInterval) {
						clearInterval(pollingInterval);
						pollingInterval = null;
					}
					if (isGenerating) {
						isGenerating = false;
						currentTask = null;
						toast.error('任务超时');
					}
				}
			} catch (error) {
				console.error(`🎬 【${serviceName}轮询】轮询出错:`, error);
			}
		}, 10000); // 每10秒轮询一次
	};

	// 图片上传处理
	const handleImageUpload = async (event: Event, type: 'input' | 'tail' | 'static_mask' | 'veo1' | 'veo2' | 'veo3' | 'multi') => {
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

			if (type === 'input') {
				inputImage = base64;
				console.log('🎬 【可灵】输入图片上传成功:', file.name);
			} else if (type === 'tail') {
				imageTail = base64;
				console.log('🎬 【可灵】尾帧图片上传成功:', file.name);
			} else if (type === 'static_mask') {
				staticMask = base64;
				console.log('🎬 【可灵】静态笔刷上传成功:', file.name);
			} else if (type === 'veo1') {
				veoImage1 = base64;
				console.log('🎯 【Veo】第1张图片上传成功:', file.name);
			} else if (type === 'veo2') {
				veoImage2 = base64;
				console.log('🎯 【Veo】第2张图片上传成功:', file.name);
			} else if (type === 'veo3') {
				veoImage3 = base64;
				console.log('🎯 【Veo】第3张图片上传成功:', file.name);
			} else if (type === 'multi') {
				// 多图模式：检查数量限制
				if (multiImages.length >= maxMultiImages) {
					toast.error(`最多只能上传${maxMultiImages}张图片`);
					return;
				}

				multiImages = [...multiImages, {
					image: base64,
					preview: base64
				}];
				console.log('🎬 【可灵多图】图片上传成功:', file.name, `(${multiImages.length}/${maxMultiImages})`);
			}
		} catch (error) {
			console.error('🎬 【可灵】图片上传失败:', error);
			toast.error('图片上传失败');
		}

		// 清空input值，允许重复上传同一文件
		target.value = '';
	};

	// 批量多图上传处理
	const handleMultiImagesUpload = async (event: Event) => {
		const target = event.target as HTMLInputElement;
		const files = Array.from(target.files || []);

		if (files.length === 0) return;

		// 检查数量限制
		if (multiImages.length + files.length > maxMultiImages) {
			toast.error(`最多只能上传${maxMultiImages}张图片，当前已有${multiImages.length}张`);
			return;
		}

		for (const file of files) {
			// 验证文件类型
			if (!file.type.startsWith('image/')) {
				toast.error(`文件 ${file.name} 不是图片格式`);
				continue;
			}

			// 验证文件大小 (10MB)
			if (file.size > 10 * 1024 * 1024) {
				toast.error(`图片 ${file.name} 大小不能超过10MB`);
				continue;
			}

			try {
				// 转换为base64
				const base64 = await fileToBase64(file);
				
				multiImages = [...multiImages, {
					image: base64,
					preview: base64
				}];
				
				console.log('🎬 【可灵多图】批量上传成功:', file.name, `(${multiImages.length}/${maxMultiImages})`);
			} catch (error) {
				console.error('🎬 【可灵多图】上传失败:', file.name, error);
				toast.error(`图片 ${file.name} 上传失败`);
			}
		}

		// 清空input值
		target.value = '';
	};

	// 删除多图中的某张图片
	const removeMultiImage = (index: number) => {
		multiImages = multiImages.filter((_, i) => i !== index);
		console.log('🎬 【可灵多图】删除图片:', index, `剩余(${multiImages.length}/${maxMultiImages})`);
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

	// 删除任务
	const handleDeleteTask = async (task: KlingTask | JimengTask | VeoTask) => {
		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		try {
			const confirmed = confirm(`确定要删除任务"${task.prompt?.slice(0, 50)}..."吗？`);
			if (!confirmed) return;

			// 确定服务类型
			const taskServiceType = task.serviceType || 'kling'; // 默认为kling
			const serviceName = taskServiceType === 'kling' ? '可灵' : taskServiceType === 'jimeng' ? '即梦' : 'Veo';

			console.log(`🗑️ 删除${serviceName}任务: ${task.id}`);

			const deleteFunction = taskServiceType === 'kling' ? deleteKlingTask : 
								   taskServiceType === 'jimeng' ? deleteJimengTask : deleteVeoTask;
			const success = await deleteFunction($user.token, task.id);

			if (success) {
				// 从历史记录中移除任务
				taskHistory = taskHistory.filter((t) => t.id !== task.id);

				// 如果删除的是当前任务，清空当前任务状态
				if (currentTask?.id === task.id) {
					currentTask = null;
					isGenerating = false;
				}

				// 如果删除的是最新生成的视频，清空显示
				if (generatedVideo?.id === task.id) {
					generatedVideo = null;
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

	// 格式化进度显示
	const formatProgress = (progress: string | undefined, task?: KlingTask | JimengTask): string => {
		// 如果任务已完成且有视频，显示100%
		if (task && task.videoUrl && (task.status === 'succeed' || task.videoUrl)) {
			return '100%';
		}

		if (!progress) return '0%';

		if (typeof progress === 'string') {
			// 如果已经是百分比格式，直接返回
			if (progress.includes('%')) return progress;
			return progress;
		}

		return '0%';
	};

	// 格式化状态显示
	const formatStatus = (status: string): string => {
		const statusMap = {
			submitted: '已提交',
			processing: '处理中',
			succeed: '成功',
			failed: '失败'
		};
		return statusMap[status] || status;
	};

	// 视频查看模态框
	let selectedVideoForViewing: KlingTask | JimengTask | null = null;
	let isVideoModalOpen = false;

	// 打开视频查看模态框
	const openVideoModal = (task: KlingTask | JimengTask) => {
		selectedVideoForViewing = task;
		isVideoModalOpen = true;
	};

	// 关闭视频查看模态框
	const closeVideoModal = () => {
		selectedVideoForViewing = null;
		isVideoModalOpen = false;
	};

	// 下载视频
	const downloadVideo = async (videoUrl: string, filename: string) => {
		try {
			const response = await fetch(videoUrl);
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = filename || 'kling-video.mp4';
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(url);
			document.body.removeChild(a);
			toast.success('视频下载开始');
		} catch (error) {
			console.error('Failed to download video:', error);
			toast.error('下载视频失败');
		}
	};

	// 使用相同参数重新生成
	const regenerateWithSameParams = async (task: KlingTask | JimengTask | VeoTask) => {
		if (!task.prompt) {
			toast.error('无法获取原始提示词');
			return;
		}

		// 确定任务的服务类型
		const taskServiceType = task.serviceType || 'kling';
		selectedService = taskServiceType;

		// 设置相同的参数
		prompt = task.prompt;
		selectedDuration = task.duration;
		selectedAspectRatio = task.aspectRatio;
		cfgScale = task.cfgScale || 0.5;

		// 可灵特有参数
		if (taskServiceType === 'kling') {
			selectedMode = task.mode || 'std';
			negativePrompt = task.negativePrompt || '';
		}

		// 即梦特有参数
		if (taskServiceType === 'jimeng') {
			watermark = task.watermark || false;
		}

		// Veo特有参数
		if (taskServiceType === 'veo') {
			selectedModel = task.model || 'veo3';
			enhancePrompt = task.enhance_prompt !== undefined ? task.enhance_prompt : true;
		}

		if (task.action === 'IMAGE_TO_VIDEO' || task.action === 'MULTI_IMAGE_TO_VIDEO') {
			selectedGenerationType = 'image-to-video';
			
			if (task.action === 'MULTI_IMAGE_TO_VIDEO') {
				selectedImageVideoMode = 'multi-image';
				multiImages = task.inputImages || [];
			} else {
				inputImage = task.inputImage || null;
			}
		} else {
			selectedGenerationType = 'text-to-video';
		}

		// 开始生成
		await generateVideo();
		toast.info('开始重新生成视频...');
	};

	// ======================== 视频延长功能 ========================

	// 检查视频延长资格并缓存结果
	const checkVideoExtendEligibility = async (task: KlingTask) => {
		if (!$user?.token || task.serviceType !== 'kling' || !task.videoId) {
			return null;
		}

		// 检查缓存
		if (extendChecks.has(task.videoId)) {
			return extendChecks.get(task.videoId);
		}

		try {
			extendingTasks.add(task.id);
			extendingTasks = extendingTasks; // 触发响应性更新

			const result = await checkKlingVideoExtendEligibility($user.token, task.videoId);
			extendChecks.set(task.videoId, result);
			return result;
		} catch (error) {
			console.error('检查延长资格失败:', error);
			return null;
		} finally {
			extendingTasks.delete(task.id);
			extendingTasks = extendingTasks; // 触发响应性更新
		}
	};

	// 处理视频延长
	const handleVideoExtend = async (task: KlingTask) => {
		if (!$user?.token || task.serviceType !== 'kling' || !task.videoId) {
			toast.error('无法延长此视频');
			return;
		}

		// 先检查资格
		const eligibility = await checkVideoExtendEligibility(task);
		if (!eligibility || !eligibility.canExtend) {
			toast.error(eligibility?.reason || '无法延长此视频');
			return;
		}

		try {
			extendingTasks.add(task.id);
			extendingTasks = extendingTasks; // 触发响应性更新

			const extendRequest: KlingVideoExtendRequest = {
				videoId: task.videoId,
				prompt: task.prompt, // 使用原始提示词
				negativePrompt: task.negativePrompt,
				cfgScale: task.cfgScale
			};

			console.log(`🎬 【可灵延长】提交延长请求: ${task.videoId}, 积分: ${eligibility.creditsCost}`);
			const result = await submitKlingVideoExtendTask($user.token, extendRequest);

			if (result.success) {
				// 创建延长任务记录（模拟）
				const extendTask: KlingTask = {
					id: result.task_id,
					userId: $user.id,
					externalTaskId: '',
					action: 'VIDEO_EXTEND',
					status: 'submitted',
					taskStatusMsg: '延长任务已提交',
					modelName: task.modelName,
					prompt: task.prompt,
					negativePrompt: task.negativePrompt,
					cfgScale: task.cfgScale,
					mode: task.mode,
					duration: task.duration,
					aspectRatio: task.aspectRatio,
					parentTaskId: task.id,
					isExtended: true,
					extendCount: (eligibility.extendCount || 0) + 1,
					creditsCost: result.credits_cost || eligibility.creditsCost || 0,
					progress: '延长中...',
					createdAt: new Date().toISOString(),
					updatedAt: new Date().toISOString(),
					properties: {
						serviceType: 'kling',
						action: 'VIDEO_EXTEND',
						originalVideoId: task.videoId
					}
				};

				// 添加到任务历史
				taskHistory = [extendTask, ...taskHistory];

				// 开始轮询延长任务状态
				pollExtendTaskStatus(result.task_id);

				// 刷新积分
				await refreshCredits();

				// 清除缓存
				extendChecks.delete(task.videoId);

				toast.success(
					`视频延长任务已提交，消耗 ${result.credits_cost || eligibility.creditsCost} 积分`
				);
			}
		} catch (error) {
			console.error('延长视频失败:', error);
			toast.error('延长视频失败: ' + (error.message || error));
		} finally {
			extendingTasks.delete(task.id);
			extendingTasks = extendingTasks; // 触发响应性更新
		}
	};

	// 轮询延长任务状态
	const pollExtendTaskStatus = async (taskId: string) => {
		if (!$user?.token) return;

		const maxAttempts = 60; // 最多轮询60次
		const interval = 10000; // 每10秒轮询一次
		let attempts = 0;

		const poll = async () => {
			try {
				attempts++;
				console.log(`🔍 【可灵延长】轮询延长任务状态: ${taskId} (${attempts}/${maxAttempts})`);

				const task = await getKlingVideoExtendTaskStatus($user.token, taskId);

				// 更新任务历史中的任务状态
				taskHistory = taskHistory.map((t) => (t.id === taskId ? { ...task } : t));

				if (task.status === 'succeed') {
					console.log(`✅ 【可灵延长】延长任务完成: ${taskId}`);
					toast.success('视频延长完成！');
					// 刷新积分
					await refreshCredits();
					return; // 停止轮询
				} else if (task.status === 'failed') {
					console.log(`❌ 【可灵延长】延长任务失败: ${taskId}`);
					toast.error('视频延长失败: ' + (task.failReason || '未知错误'));
					return; // 停止轮询
				}

				// 继续轮询
				if (attempts < maxAttempts) {
					setTimeout(poll, interval);
				} else {
					console.log(`⏱️ 【可灵延长】延长任务轮询超时: ${taskId}`);
					toast.warning('延长任务状态查询超时，请稍后手动刷新');
				}
			} catch (error) {
				console.error('轮询延长任务状态失败:', error);
				if (attempts < maxAttempts) {
					setTimeout(poll, interval);
				}
			}
		};

		// 延迟一点开始轮询，给后端时间处理
		setTimeout(poll, 3000);
	};

	// 计算视频总时长（包括延长）
	const calculateTotalDuration = (task: KlingTask | JimengTask | VeoTask) => {
		if (task.serviceType !== 'kling') {
			return task.duration; // 非可灵任务直接返回原时长
		}

		const klingTask = task as KlingTask;
		
		// 如果是延长任务，显示累计时长
		if (klingTask.isExtended && klingTask.originalDuration) {
			const originalDuration = parseInt(klingTask.originalDuration) || 0;
			const extendDuration = parseInt(klingTask.duration) || 0;
			return (originalDuration + extendDuration * (klingTask.extendCount || 1)).toString();
		}
		
		// 如果有视频实际时长，使用实际时长
		if (klingTask.videoDuration) {
			return klingTask.videoDuration;
		}
		
		// 否则返回设置的时长
		return klingTask.duration;
	};

	// 积分余额定期刷新
	let creditRefreshInterval: NodeJS.Timeout | null = null;

	// 组件销毁时清理资源
	import { onDestroy } from 'svelte';
	onDestroy(() => {
		if (pollingInterval) {
			clearInterval(pollingInterval);
			pollingInterval = null;
		}
		if (creditRefreshInterval) {
			clearInterval(creditRefreshInterval);
			creditRefreshInterval = null;
		}
		if (serviceSwitchTimeout) {
			clearTimeout(serviceSwitchTimeout);
			serviceSwitchTimeout = null;
		}
	});
</script>

<svelte:head>
	<title>
		视频生成 • {$WEBUI_NAME}
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
					<!-- 服务选择 -->
					<div>
						<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							🎬 视频生成服务
						</h3>
						<div class="grid grid-cols-3 gap-1 mb-3">
							<button
								class="px-2 py-2 text-xs rounded border transition-colors {selectedService ===
								'kling'
									? 'bg-purple-500 text-white border-purple-500'
									: 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'}"
								on:click={() => (selectedService = 'kling')}
							>
								🎬 可灵
							</button>
							<button
								class="px-2 py-2 text-xs rounded border transition-colors {selectedService ===
								'jimeng'
									? 'bg-green-500 text-white border-green-500'
									: 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'}"
								on:click={() => (selectedService = 'jimeng')}
							>
								🌟 即梦
							</button>
							<button
								class="px-2 py-2 text-xs rounded border transition-colors {selectedService ===
								'veo'
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'}"
								on:click={() => (selectedService = 'veo')}
							>
								🎯 Veo AI
							</button>
						</div>

						<!-- 当前选择的服务状态 -->
						{#if selectedService === 'kling'}
							<div class="rounded-lg p-3 bg-gradient-to-r from-purple-500 to-pink-600 text-white">
								<div class="flex items-center justify-between">
									<div>
										<div class="font-medium">可灵 AI</div>
										<div class="text-xs opacity-75">
											{klingConfig?.enabled ? '已启用' : '未配置'}
										</div>
									</div>
									<div class="text-xl">🎬</div>
								</div>
							</div>
						{:else if selectedService === 'jimeng'}
							<div class="rounded-lg p-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white">
								<div class="flex items-center justify-between">
									<div>
										<div class="font-medium">即梦 AI</div>
										<div class="text-xs opacity-75">
											{jimengConfig?.enabled ? '已启用' : '未配置'}
										</div>
									</div>
									<div class="text-xl">🌟</div>
								</div>
							</div>
						{:else}
							<div class="rounded-lg p-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
								<div class="flex items-center justify-between">
									<div>
										<div class="font-medium">Veo AI</div>
										<div class="text-xs opacity-75">
											{veoConfig?.enabled ? '已启用' : '未配置'}
										</div>
									</div>
									<div class="text-xl">🎯</div>
								</div>
							</div>
						{/if}
					</div>

					<!-- 当前服务信息 -->
					<div class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
						<div>当前服务: {selectedService === 'kling' ? '可灵' : selectedService === 'jimeng' ? '即梦' : 'Veo'}视频生成</div>
						<div>消耗积分: {requiredCredits}积分/次</div>
						<div class="flex justify-between items-center">
							<div class="text-green-600 dark:text-green-400">余额: {userCredits}积分</div>
							<button
								class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded transition-colors"
								on:click={async () => {
									await Promise.all([loadUserData(), refreshCredits()]);
									toast.success('配置和积分已刷新');
								}}
								disabled={loadingData}
								title="刷新积分和配置"
							>
								{loadingData ? '刷新中...' : '刷新'}
							</button>
						</div>
					</div>

					<!-- 生成类型选择 -->
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>生成类型</label
						>
						<div class="grid grid-cols-2 gap-2">
							<button
								class="px-3 py-2 text-sm rounded border transition-colors {selectedGenerationType ===
								'text-to-video'
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'}"
								on:click={() => (selectedGenerationType = 'text-to-video')}
							>
								文生视频
							</button>
							<button
								class="px-3 py-2 text-sm rounded border transition-colors {selectedGenerationType ===
								'image-to-video'
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'}"
								on:click={() => (selectedGenerationType = 'image-to-video')}
							>
								图生视频
							</button>
						</div>
					</div>

					<!-- 视频描述 -->
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
							>视频描述</label
						>
						<textarea
							bind:value={prompt}
							placeholder="描述你想要生成的视频内容..."
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white resize-none"
							rows="3"
						></textarea>
						<div class="flex justify-between items-center mt-1">
							<div class="text-xs text-gray-500">{prompt.length}/2000</div>
							<button
								on:click={generateVideo}
								disabled={isGenerating ||
									!prompt.trim() ||
									!(selectedService === 'kling' ? klingConfig?.enabled : selectedService === 'jimeng' ? jimengConfig?.enabled : veoConfig?.enabled)}
								class="px-4 py-1 {selectedService === 'kling'
									? 'bg-purple-500 hover:bg-purple-600'
									: selectedService === 'jimeng' 
									? 'bg-green-500 hover:bg-green-600'
									: 'bg-blue-500 hover:bg-blue-600'} disabled:bg-gray-400 disabled:cursor-not-allowed text-white text-xs font-medium rounded transition-colors flex items-center gap-1"
							>
								{#if isGenerating}
									<Spinner className="size-3" />
									生成中...
								{:else}
									生成视频 ({requiredCredits}积分)
								{/if}
							</button>
						</div>
					</div>

					<!-- 图生视频设置 -->
					{#if selectedGenerationType === 'image-to-video'}
						<!-- 可灵特有的图生视频模式选择 -->
						{#if selectedService === 'kling'}
							<div>
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
									>生成模式</label
								>
								<div class="grid grid-cols-2 gap-2">
									{#each imageVideoModeOptions as option}
										<button
											class="px-3 py-2 text-sm rounded border transition-colors {selectedImageVideoMode ===
											option.value
												? 'bg-blue-500 text-white border-blue-500'
												: 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'}"
											on:click={() => (selectedImageVideoMode = option.value)}
											title={option.desc}
										>
											{option.label}
										</button>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Veo专用图片上传 -->
						{#if selectedService === 'veo'}
							<div class="space-y-3">
								<div class="text-sm font-medium text-gray-700 dark:text-gray-300">
									图片输入
									<span class="text-xs text-gray-500 ml-2">
										{selectedVeoImageMode === 'single' ? '(单张图片)' : 
										 selectedVeoImageMode === 'frames' ? '(首尾帧 - 两张图片)' : 
										 '(组件模式 - 三张图片)'}
									</span>
								</div>

								<!-- 第一张图片 -->
								<div>
									<label class="text-xs text-gray-500 mb-1 block">第1张图片</label>
									<div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4">
										{#if veoImage1}
											<div class="relative">
												<img src={veoImage1} alt="第1张图片" class="w-full h-32 object-cover rounded" />
												<button
													on:click={() => (veoImage1 = null)}
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
													id="veo-image-1"
													accept="image/*"
													class="hidden"
													on:change={(e) => handleImageUpload(e, 'veo1')}
												/>
												<button
													type="button"
													on:click={() => document.getElementById('veo-image-1')?.click()}
													class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded transition-colors"
												>
													选择第1张图片
												</button>
												<p class="text-xs text-gray-500 mt-1">支持 JPG、PNG 格式</p>
											</div>
										{/if}
									</div>
								</div>

								<!-- 第二张图片（首尾帧或组件模式） -->
								{#if selectedVeoImageMode === 'frames' || selectedVeoImageMode === 'components'}
									<div>
										<label class="text-xs text-gray-500 mb-1 block">
											{selectedVeoImageMode === 'frames' ? '第2张图片（尾帧）' : '第2张图片'}
										</label>
										<div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4">
											{#if veoImage2}
												<div class="relative">
													<img src={veoImage2} alt="第2张图片" class="w-full h-32 object-cover rounded" />
													<button
														on:click={() => (veoImage2 = null)}
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
														id="veo-image-2"
														accept="image/*"
														class="hidden"
														on:change={(e) => handleImageUpload(e, 'veo2')}
													/>
													<button
														type="button"
														on:click={() => document.getElementById('veo-image-2')?.click()}
														class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded transition-colors"
													>
														选择第2张图片
													</button>
													<p class="text-xs text-gray-500 mt-1">支持 JPG、PNG 格式</p>
												</div>
											{/if}
										</div>
									</div>
								{/if}

								<!-- 第三张图片（仅组件模式） -->
								{#if selectedVeoImageMode === 'components'}
									<div>
										<label class="text-xs text-gray-500 mb-1 block">第3张图片</label>
										<div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4">
											{#if veoImage3}
												<div class="relative">
													<img src={veoImage3} alt="第3张图片" class="w-full h-32 object-cover rounded" />
													<button
														on:click={() => (veoImage3 = null)}
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
														id="veo-image-3"
														accept="image/*"
														class="hidden"
														on:change={(e) => handleImageUpload(e, 'veo3')}
													/>
													<button
														type="button"
														on:click={() => document.getElementById('veo-image-3')?.click()}
														class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded transition-colors"
													>
														选择第3张图片
													</button>
													<p class="text-xs text-gray-500 mt-1">支持 JPG、PNG 格式</p>
												</div>
											{/if}
										</div>
									</div>
								{/if}
							</div>
						{:else}
							<!-- 可灵和即梦的输入图片 (多图参考模式下隐藏) -->
							{#if !(selectedService === 'kling' && selectedImageVideoMode === 'multi-image')}
								<div>
									<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
										{selectedService === 'kling' && selectedImageVideoMode === 'first-last'
											? '首帧图片'
											: '输入图片'}
									</label>
							<div
								class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4"
							>
								{#if inputImage}
									<div class="relative">
										<img src={inputImage} alt="输入图片" class="w-full h-32 object-cover rounded" />
										<button
											on:click={() => (inputImage = null)}
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
											id="input-image"
											accept="image/*"
											class="hidden"
											on:change={(e) => handleImageUpload(e, 'input')}
										/>
										<button
											type="button"
											on:click={() => document.getElementById('input-image')?.click()}
											class="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white text-sm rounded transition-colors"
										>
											选择图片
										</button>
										<div class="text-xs text-gray-500 mt-2">支持 JPG、PNG、WebP，最大 10MB</div>
									</div>
								{/if}
							</div>
								</div>
							{/if}
						{/if}

						<!-- 可灵特有的尾帧图片 (首尾帧模式) -->
						{#if selectedService === 'kling' && selectedImageVideoMode === 'first-last'}
							<div>
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
									>尾帧图片</label
								>
								<div
									class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4"
								>
									{#if imageTail}
										<div class="relative">
											<img
												src={imageTail}
												alt="尾帧图片"
												class="w-full h-32 object-cover rounded"
											/>
											<button
												on:click={() => (imageTail = null)}
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
												id="tail-image"
												accept="image/*"
												class="hidden"
												on:change={(e) => handleImageUpload(e, 'tail')}
											/>
											<button
												type="button"
												on:click={() => document.getElementById('tail-image')?.click()}
												class="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white text-sm rounded transition-colors"
											>
												选择尾帧图片
											</button>
											<div class="text-xs text-gray-500 mt-2">支持 JPG、PNG、WebP，最大 10MB</div>
										</div>
									{/if}
								</div>
							</div>
						{/if}

						<!-- 可灵特有的静态笔刷 (笔刷模式) -->
						{#if selectedService === 'kling' && selectedImageVideoMode === 'brush'}
							<div>
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
									>静态笔刷遮罩</label
								>
								<div
									class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4"
								>
									{#if staticMask}
										<div class="relative">
											<img
												src={staticMask}
												alt="静态笔刷"
												class="w-full h-32 object-cover rounded"
											/>
											<button
												on:click={() => (staticMask = null)}
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
												id="static-mask"
												accept="image/*"
												class="hidden"
												on:change={(e) => handleImageUpload(e, 'static_mask')}
											/>
											<button
												type="button"
												on:click={() => document.getElementById('static-mask')?.click()}
												class="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white text-sm rounded transition-colors"
											>
												选择笔刷遮罩
											</button>
											<div class="text-xs text-gray-500 mt-2">可选：静态笔刷涂抹区域</div>
										</div>
									{/if}
								</div>
							</div>
						{/if}

						<!-- 可灵特有的多图参考 (多图参考模式) -->
						{#if selectedService === 'kling' && selectedImageVideoMode === 'multi-image'}
							<div>
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
									多图参考上传 ({multiImages.length}/{maxMultiImages})
								</label>
								
								<!-- 图片网格显示 -->
								{#if multiImages.length > 0}
									<div class="grid grid-cols-2 gap-2 mb-4">
										{#each multiImages as image, index}
											<div class="relative">
												<img
													src={image.preview}
													alt="参考图片 {index + 1}"
													class="w-full h-24 object-cover rounded border"
												/>
												<button
													on:click={() => removeMultiImage(index)}
													class="absolute -top-1 -right-1 bg-red-500 hover:bg-red-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs transition-colors"
													title="删除图片"
												>
													×
												</button>
												<div class="absolute bottom-1 left-1 bg-black bg-opacity-50 text-white text-xs px-1 rounded">
													{index + 1}
												</div>
											</div>
										{/each}
									</div>
								{/if}

								<!-- 上传区域 -->
								<div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4">
									<div class="text-center">
										<input
											type="file"
											id="multi-images"
											accept="image/*"
											multiple
											class="hidden"
											on:change={handleMultiImagesUpload}
										/>
										<button
											type="button"
											on:click={() => document.getElementById('multi-images')?.click()}
											class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded transition-colors mr-2"
											disabled={multiImages.length >= maxMultiImages}
										>
											{multiImages.length === 0 ? '选择图片' : '继续添加'}
										</button>
										
										{#if multiImages.length > 0}
											<button
												type="button"
												on:click={() => multiImages = []}
												class="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white text-sm rounded transition-colors"
											>
												清空全部
											</button>
										{/if}
										
										<div class="text-xs text-gray-500 mt-2">
											• 支持 JPG、PNG、WebP 格式，单张图片最大 10MB<br>
											• 最多上传 {maxMultiImages} 张图片，仅支持 kling-v1-6 模型<br>
											• 积分费用与单图模式相同，多图不额外收费
										</div>
									</div>
								</div>
							</div>
						{/if}

						<!-- 可灵特有的摄像机控制 (摄像机控制模式) -->
						{#if selectedService === 'kling' && selectedImageVideoMode === 'camera'}
							<div class="space-y-4">
								<div>
									<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
										>运镜类型</label
									>
									<select
										bind:value={cameraControlType}
										class="w-full rounded-lg py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
									>
										<option value="simple">简单运镜 (自定义参数)</option>
										<option value="down_back">下移拉远 (镜头下压并后退)</option>
										<option value="forward_up">推进上移 (镜头前进并上仰)</option>
										<option value="right_turn_forward">右旋推进 (先右旋转后前进)</option>
										<option value="left_turn_forward">左旋推进 (先左旋并前进)</option>
									</select>
								</div>

								<!-- 简单运镜参数配置 -->
								{#if cameraControlType === 'simple'}
									<div
										class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4"
									>
										<div class="text-sm font-medium text-blue-700 dark:text-blue-300 mb-3">
											摄像机运动参数 (6选1，只能有一个参数不为0)
										</div>
										<div class="grid grid-cols-2 gap-3">
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													水平运镜 (沿X轴)
													<Tooltip content="负值向左平移，正值向右平移 [-10, 10]">
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
																d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
															/>
														</svg>
													</Tooltip>
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.horizontal}
													on:input={() => {
														// 当选择此参数时，重置其他参数
														if (cameraControlConfig.horizontal !== 0) {
															cameraControlConfig.vertical = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.roll = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													垂直运镜 (沿Y轴)
													<Tooltip content="负值向下平移，正值向上平移 [-10, 10]">
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
																d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
															/>
														</svg>
													</Tooltip>
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.vertical}
													on:input={() => {
														if (cameraControlConfig.vertical !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.roll = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													水平摇镜 (绕Y轴)
													<Tooltip content="负值向左旋转，正值向右旋转 [-10, 10]">
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
																d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
															/>
														</svg>
													</Tooltip>
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.pan}
													on:input={() => {
														if (cameraControlConfig.pan !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.vertical = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.roll = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													垂直摇镜 (绕X轴)
													<Tooltip content="负值向下旋转，正值向上旋转 [-10, 10]">
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
																d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
															/>
														</svg>
													</Tooltip>
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.tilt}
													on:input={() => {
														if (cameraControlConfig.tilt !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.vertical = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.roll = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													旋转运镜 (绕Z轴)
													<Tooltip content="负值逆时针旋转，正值顺时针旋转 [-10, 10]">
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
																d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
															/>
														</svg>
													</Tooltip>
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.roll}
													on:input={() => {
														if (cameraControlConfig.roll !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.vertical = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													变焦控制
													<Tooltip
														content="负值焦距变长(视野变小)，正值焦距变短(视野变大) [-10, 10]"
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
																d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
															/>
														</svg>
													</Tooltip>
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.zoom}
													on:input={() => {
														if (cameraControlConfig.zoom !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.vertical = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.roll = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
										</div>

										<!-- 参数重置按钮 -->
										<div class="mt-3 text-center">
											<button
												type="button"
												on:click={() => {
													cameraControlConfig = {
														horizontal: 0,
														vertical: 0,
														pan: 0,
														tilt: 0,
														roll: 0,
														zoom: 0
													};
												}}
												class="px-3 py-1.5 text-xs bg-gray-500 hover:bg-gray-600 text-white rounded transition-colors"
											>
												重置所有参数
											</button>
										</div>
									</div>
								{:else}
									<!-- 预定义运镜类型说明 -->
									<div
										class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3"
									>
										<div class="text-sm text-green-700 dark:text-green-300">
											{#if cameraControlType === 'down_back'}
												📹 下移拉远：镜头下压并后退，适合展现场景全貌
											{:else if cameraControlType === 'forward_up'}
												📹 推进上移：镜头前进并上仰，适合突出主体对象
											{:else if cameraControlType === 'right_turn_forward'}
												📹 右旋推进：先右旋转后前进，适合动态展示
											{:else if cameraControlType === 'left_turn_forward'}
												📹 左旋推进：先左旋并前进，适合创意运镜
											{/if}
										</div>
									</div>
								{/if}
							</div>
						{/if}
					{/if}

					<!-- 视频参数 -->
					<div class="space-y-3">
						<div class="flex justify-between items-center text-xs font-medium text-gray-500">
							<div>视频参数</div>
						</div>

						<!-- 模型版本选择 -->
						{#if selectedService === 'kling' || selectedService === 'veo'}
							<div>
								<div class="mb-1 text-xs text-gray-500">模型版本</div>
								<select
									bind:value={selectedModel}
									class="w-full rounded-lg py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
								>
									{#each currentModelOptions as option}
										<option value={option.value}>{option.label}{#if option.description} - {option.description}{/if}</option>
									{/each}
								</select>
							</div>
						{/if}

						<div class="grid {selectedService === 'kling' ? 'grid-cols-2' : 'grid-cols-1'} gap-3">
							<!-- 可灵特有的视频模式 -->
							{#if selectedService === 'kling'}
								<div>
									<div class="mb-1 text-xs text-gray-500">视频模式</div>
									<select
										bind:value={selectedMode}
										class="w-full rounded-lg py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
									>
										{#each modeOptions as option}
											<option value={option.value}>{option.label}</option>
										{/each}
									</select>
								</div>
							{/if}

							{#if selectedService !== 'veo'}
								<div>
									<div class="mb-1 text-xs text-gray-500">视频时长</div>
									<select
										bind:value={selectedDuration}
										class="w-full rounded-lg py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
									>
										{#each durationOptions as option}
											<option value={option.value}>{option.label}</option>
										{/each}
									</select>
								</div>
							{/if}

							{#if selectedService !== 'veo'}
								<div>
									<div class="mb-1 text-xs text-gray-500">画面比例</div>
									<select
										bind:value={selectedAspectRatio}
										class="w-full rounded-lg py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
									>
										{#each aspectRatioOptions as option}
											<option value={option.value}>{option.label}</option>
										{/each}
									</select>
								</div>
							{/if}

							{#if selectedService !== 'veo'}
								<div>
									<div class="mb-1 text-xs text-gray-500">
										CFG Scale
										<Tooltip content="生成自由度，值越大越符合提示词 (0-1)">
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
													d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
												/>
											</svg>
										</Tooltip>
									</div>
									<input
										class="w-full rounded-lg py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
										type="number"
										min="0"
										max="1"
										step="0.1"
										bind:value={cfgScale}
									/>
								</div>
							{/if}
						</div>
					</div>

					<!-- 即梦特有的水印设置 -->
					{#if selectedService === 'jimeng'}
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
								水印设置
							</label>
							<div class="flex items-center space-x-2">
								<input
									type="checkbox"
									id="watermark-checkbox"
									bind:checked={watermark}
									class="w-4 h-4 text-green-600 bg-gray-100 border-gray-300 rounded focus:ring-green-500 dark:focus:ring-green-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
								/>
								<label
									for="watermark-checkbox"
									class="text-sm text-gray-700 dark:text-gray-300 cursor-pointer"
								>
									在生成的视频中包含水印
								</label>
							</div>
							<div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
								启用后，生成的视频将包含服务提供商的水印
							</div>
						</div>
					{/if}

					<!-- 可灵特有的负面提示词 -->
					{#if selectedService === 'kling'}
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
								>负面提示词（可选）</label
							>
							<textarea
								bind:value={negativePrompt}
								placeholder="描述你不希望在视频中出现的内容..."
								class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white resize-none"
								rows="2"
							></textarea>
						</div>
					{/if}

					<!-- Veo特有的提示词优化设置 -->
					{#if selectedService === 'veo'}
						<div>
							<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
								提示词优化设置
							</label>
							<div class="flex items-center space-x-2">
								<input
									type="checkbox"
									id="enhance-prompt-checkbox"
									bind:checked={enhancePrompt}
									class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
								/>
								<label
									for="enhance-prompt-checkbox"
									class="text-sm text-gray-700 dark:text-gray-300 cursor-pointer"
								>
									启用智能提示词优化
								</label>
							</div>
							<div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
								开启后，AI 会自动优化您的提示词以获得更好的生成效果
							</div>
						</div>
					{/if}

					<!-- 可灵摄像机控制 (通用于文生视频和图生视频) -->
					{#if selectedService === 'kling'}
						<div class="space-y-3">
							<div class="flex justify-between items-center">
								<div class="text-sm font-medium text-gray-700 dark:text-gray-300">摄像机控制</div>
								<button
									type="button"
									on:click={() => {
										// 切换摄像机控制折叠状态
										const section = document.getElementById('camera-control-section');
										if (section) {
											section.style.display = section.style.display === 'none' ? 'block' : 'none';
										}
									}}
									class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
								>
									展开/收起
								</button>
							</div>

							<div id="camera-control-section" style="display: none;" class="space-y-4">
								<div>
									<label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
										>运镜类型</label
									>
									<select
										bind:value={cameraControlType}
										class="w-full rounded-lg py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
									>
										<option value="simple">简单运镜 (自定义参数)</option>
										<option value="down_back">下移拉远 (镜头下压并后退)</option>
										<option value="forward_up">推进上移 (镜头前进并上仰)</option>
										<option value="right_turn_forward">右旋推进 (先右旋转后前进)</option>
										<option value="left_turn_forward">左旋推进 (先左旋并前进)</option>
									</select>
								</div>

								<!-- 简单运镜参数配置 -->
								{#if cameraControlType === 'simple'}
									<div
										class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4"
									>
										<div class="text-sm font-medium text-blue-700 dark:text-blue-300 mb-3">
											摄像机运动参数 (6选1，只能有一个参数不为0)
										</div>
										<div class="grid grid-cols-2 gap-3">
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													水平运镜 (沿X轴)
													<Tooltip content="负值向左平移，正值向右平移 [-10, 10]">
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
																d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
															/>
														</svg>
													</Tooltip>
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.horizontal}
													on:input={() => {
														if (cameraControlConfig.horizontal !== 0) {
															cameraControlConfig.vertical = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.roll = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													垂直运镜 (沿Y轴)
													<Tooltip content="负值向下平移，正值向上平移 [-10, 10]">
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
																d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
															/>
														</svg>
													</Tooltip>
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.vertical}
													on:input={() => {
														if (cameraControlConfig.vertical !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.roll = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													水平摇镜 (绕Y轴)
													<Tooltip content="负值向左旋转，正值向右旋转 [-10, 10]">
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
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.pan}
													on:input={() => {
														if (cameraControlConfig.pan !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.vertical = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.roll = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													垂直摇镜 (绕X轴)
													<Tooltip content="负值向下旋转，正值向上旋转 [-10, 10]">
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
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.tilt}
													on:input={() => {
														if (cameraControlConfig.tilt !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.vertical = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.roll = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													旋转运镜 (绕Z轴)
													<Tooltip content="负值逆时针旋转，正值顺时针旋转 [-10, 10]">
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
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.roll}
													on:input={() => {
														if (cameraControlConfig.roll !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.vertical = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.zoom = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
											<div>
												<label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
													变焦控制
													<Tooltip
														content="负值焦距变长(视野变小)，正值焦距变短(视野变大) [-10, 10]"
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
												</label>
												<input
													type="number"
													min="-10"
													max="10"
													step="0.5"
													bind:value={cameraControlConfig.zoom}
													on:input={() => {
														if (cameraControlConfig.zoom !== 0) {
															cameraControlConfig.horizontal = 0;
															cameraControlConfig.vertical = 0;
															cameraControlConfig.pan = 0;
															cameraControlConfig.tilt = 0;
															cameraControlConfig.roll = 0;
														}
													}}
													class="w-full rounded py-1.5 px-2 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
												/>
											</div>
										</div>

										<!-- 参数重置按钮 -->
										<div class="mt-3 text-center">
											<button
												type="button"
												on:click={() => {
													cameraControlConfig = {
														horizontal: 0,
														vertical: 0,
														pan: 0,
														tilt: 0,
														roll: 0,
														zoom: 0
													};
												}}
												class="px-3 py-1.5 text-xs bg-gray-500 hover:bg-gray-600 text-white rounded transition-colors"
											>
												重置所有参数
											</button>
										</div>
									</div>
								{:else}
									<!-- 预定义运镜类型说明 -->
									<div
										class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3"
									>
										<div class="text-sm text-green-700 dark:text-green-300">
											{#if cameraControlType === 'down_back'}
												📹 下移拉远：镜头下压并后退，适合展现场景全貌
											{:else if cameraControlType === 'forward_up'}
												📹 推进上移：镜头前进并上仰，适合突出主体对象
											{:else if cameraControlType === 'right_turn_forward'}
												📹 右旋推进：先右旋转后前进，适合动态展示
											{:else if cameraControlType === 'left_turn_forward'}
												📹 左旋推进：先左旋并前进，适合创意运镜
											{/if}
										</div>
									</div>
								{/if}
							</div>
						</div>
					{/if}

					<!-- 最新生成的视频 -->
					{#if generatedVideo}
						<div
							class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3"
						>
							<div class="flex justify-between items-center mb-2">
								<span class="text-sm font-medium text-green-700 dark:text-green-300">最新生成</span>
								<span class="text-xs text-green-600 dark:text-green-400">已完成</span>
							</div>
							{#if generatedVideo.videoUrl}
								<div class="relative mb-2">
									<video
										src={generatedVideo.videoUrl}
										controls
										class="w-full h-32 object-cover rounded cursor-pointer"
										on:click={() => openVideoModal(generatedVideo)}
									>
										您的浏览器不支持视频播放
									</video>
								</div>
							{:else}
								<div
									class="w-full h-32 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center text-gray-500"
								>
									<span class="text-sm">暂无视频</span>
								</div>
							{/if}
							<div class="text-xs text-green-600 dark:text-green-400 truncate">
								{generatedVideo.prompt}
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
								<span class="text-xs text-blue-600 dark:text-blue-400"
									>{formatStatus(currentTask.status)}</span
								>
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
									placeholder="搜索视频历史..."
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
							<div class="text-sm text-gray-500 dark:text-gray-400">
								{#if searchQuery || selectedStatusFilter !== 'all' || selectedTimeFilter !== 'all'}
									显示 {filteredTaskHistory.length} / {taskHistory.length} 个视频
								{:else}
									共 {taskHistory.length} 个视频
								{/if}
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
									<option value="succeed">成功</option>
									<option value="processing">处理中</option>
									<option value="submitted">已提交</option>
									<option value="failed">失败</option>
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
									<!-- 服务标签 -->
									<div class="absolute top-2 left-2 z-10">
										{#if task.serviceType === 'jimeng'}
											<span
												class="px-2 py-1 text-xs font-medium text-white rounded bg-gradient-to-r from-green-500 to-emerald-500"
											>
												即梦 AI
											</span>
										{:else if task.serviceType === 'veo'}
											<span
												class="px-2 py-1 text-xs font-medium text-white rounded bg-gradient-to-r from-blue-500 to-indigo-500"
											>
												Veo AI
											</span>
										{:else}
											<span
												class="px-2 py-1 text-xs font-medium text-white rounded bg-gradient-to-r from-purple-500 to-pink-500"
											>
												可灵 AI
											</span>
										{/if}
									</div>

									<!-- 视频 -->
									{#if task.videoUrl}
										<div class="relative aspect-video">
											<video
												src={task.videoUrl}
												class="w-full h-full object-cover cursor-pointer"
												on:click={() => openVideoModal(task)}
												muted
												preload="metadata"
											>
												您的浏览器不支持视频播放
											</video>
											<!-- 悬停操作层 -->
											<div
												class="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center opacity-0 hover:opacity-100"
											>
												<div class="flex flex-col gap-1">
													<div class="flex gap-1">
														<button
															on:click|stopPropagation={() => {
																const serviceName =
																	task?.serviceType === 'jimeng' ? 'jimeng' : 'kling';
																downloadVideo(task.videoUrl, `${serviceName}-${task.id}.mp4`);
															}}
															class="px-2 py-1 bg-green-500 bg-opacity-90 text-white text-xs rounded hover:bg-opacity-100 transition-all font-medium"
														>
															下载
														</button>
														<button
															on:click|stopPropagation={() => openVideoModal(task)}
															class="px-2 py-1 bg-gray-500 bg-opacity-90 text-white text-xs rounded hover:bg-opacity-100 transition-all font-medium"
														>
															查看
														</button>
													</div>
													<div class="flex gap-1">
														<button
															on:click|stopPropagation={() => regenerateWithSameParams(task)}
															class="px-2 py-1 bg-blue-500 bg-opacity-90 text-white text-xs rounded hover:bg-opacity-100 transition-all font-medium"
														>
															重新生成
														</button>
														<!-- 可灵视频延长按钮 -->
														{#if task.serviceType === 'kling' && task.status === 'succeed' && task.videoUrl && task.videoId && ['kling-v1', 'kling-v1-5', 'kling-v1-6'].includes(task.modelName)}
															{#await checkVideoExtendEligibility(task)}
																<button
																	disabled
																	class="px-2 py-1 bg-purple-400 bg-opacity-90 text-white text-xs rounded transition-all font-medium cursor-not-allowed"
																>
																	检查中...
																</button>
															{:then eligibility}
																{#if eligibility && eligibility.canExtend}
																	<button
																		on:click|stopPropagation={() => handleVideoExtend(task)}
																		disabled={extendingTasks.has(task.id)}
																		class="px-2 py-1 bg-purple-500 bg-opacity-90 text-white text-xs rounded hover:bg-opacity-100 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
																		title={`延长视频 (${eligibility.creditsCost}积分)`}
																	>
																		{extendingTasks.has(task.id) ? '延长中...' : `延长 (${eligibility.creditsCost})`}
																	</button>
																{:else if eligibility && !eligibility.canExtend}
																	<button
																		disabled
																		class="px-2 py-1 bg-gray-400 bg-opacity-90 text-white text-xs rounded transition-all font-medium cursor-not-allowed"
																		title={eligibility.reason || '无法延长'}
																	>
																		无法延长
																	</button>
																{/if}
															{:catch error}
																<!-- 检查失败时不显示按钮 -->
															{/await}
														{/if}
														<button
															on:click|stopPropagation={() => handleDeleteTask(task)}
															class="px-2 py-1 bg-red-500 bg-opacity-90 text-white text-xs rounded hover:bg-opacity-100 transition-all font-medium"
														>
															删除
														</button>
													</div>
												</div>
											</div>
										</div>
									{:else if task.status === 'failed'}
										<div
											class="aspect-video bg-red-100 dark:bg-red-900 flex items-center justify-center"
										>
											<div class="text-red-500 text-xs">生成失败</div>
										</div>
									{:else if task.status === 'succeed'}
										<div
											class="aspect-video bg-yellow-100 dark:bg-yellow-900 flex items-center justify-center"
										>
											<div class="text-yellow-600 text-xs">已完成<br />无视频</div>
										</div>
									{:else}
										<div
											class="aspect-video bg-gray-100 dark:bg-gray-700 flex items-center justify-center relative"
										>
											<div class="text-center">
												<div class="text-gray-400 text-xs mb-1">
													{task.status === 'submitted' ? '等待中...' : '生成中...'}
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
												{task.serviceType === 'jimeng' ? '即梦' : task.serviceType === 'veo' ? 'Veo' : '可灵'} ({task.action === 'IMAGE_TO_VIDEO' || task.action === 'MULTI_IMAGE_TO_VIDEO'
													? '图生视频'
													: task.action === 'VIDEO_EXTEND' 
														? '延长视频' 
														: '文生视频'})
											</span>
											<span
												>{new Date(
													task.submitTime || task.createdAt || ''
												).toLocaleDateString()}</span
											>
										</div>

										<!-- 状态信息 -->
										<div class="flex items-center justify-between text-xs">
											<span class="text-gray-600 dark:text-gray-400">
												{#if task.serviceType === 'jimeng'}
													{task.duration}秒 • {task.aspectRatio}
												{:else if task.serviceType === 'veo'}
													{task.model || 'veo3'}
												{:else}
													<!-- 可灵任务显示 -->
													{task.mode || 'std'} • {calculateTotalDuration(task)}秒 • {task.aspectRatio}
													{#if task.serviceType === 'kling' && task.isExtended}
														<span class="text-purple-600 dark:text-purple-400 ml-1">[已延长{task.extendCount || 1}次]</span>
													{/if}
												{/if}
											</span>
											<span
												class="px-2 py-1 rounded text-xs {task.status === 'succeed'
													? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400'
													: task.status === 'failed'
														? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400'
														: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400'}"
											>
												{formatStatus(task.status)}
											</span>
										</div>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div
							class="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400"
						>
							{#if taskHistory.length === 0}
								<div class="text-4xl mb-4">🎬</div>
								<div class="text-lg font-medium mb-2">暂无生成历史</div>
								<div class="text-sm">开始您的第一次视频生成吧！</div>
							{:else}
								<div class="text-4xl mb-4">🔍</div>
								<div class="text-lg font-medium mb-2">未找到匹配的视频</div>
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

	<!-- 视频查看模态框 -->
	{#if isVideoModalOpen && selectedVideoForViewing}
		<div
			class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 backdrop-blur-sm"
			on:click={closeVideoModal}
		>
			<div
				class="relative max-w-4xl max-h-[90vh] mx-4 bg-white dark:bg-gray-800 rounded-lg overflow-hidden shadow-2xl"
				on:click|stopPropagation
			>
				<!-- 模态框头部 -->
				<div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
					<div class="flex items-center gap-3">
						{#if selectedVideoForViewing?.serviceType === 'jimeng'}
							<span
								class="px-2 py-1 text-xs font-medium text-white rounded bg-gradient-to-r from-green-500 to-emerald-500"
							>
								即梦 AI
							</span>
						{:else if selectedVideoForViewing?.serviceType === 'veo'}
							<span
								class="px-2 py-1 text-xs font-medium text-white rounded bg-gradient-to-r from-blue-500 to-indigo-500"
							>
								Veo AI
							</span>
						{:else}
							<span
								class="px-2 py-1 text-xs font-medium text-white rounded bg-gradient-to-r from-purple-500 to-pink-500"
							>
								可灵 AI
							</span>
						{/if}
						<div class="text-sm font-medium text-gray-900 dark:text-white">
							{selectedVideoForViewing.prompt?.split(' ').slice(0, 8).join(' ') || '无标题'}
						</div>
					</div>
					<button
						on:click={closeVideoModal}
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

				<!-- 视频显示区域 -->
				<div class="relative">
					<video
						src={selectedVideoForViewing.videoUrl}
						controls
						class="w-full max-h-[70vh] object-contain"
						autoplay
					>
						您的浏览器不支持视频播放
					</video>
				</div>

				<!-- 模态框底部操作栏 -->
				<div
					class="flex items-center justify-between p-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-750"
				>
					<div class="flex items-center gap-3">
						<div class="text-xs text-gray-500 dark:text-gray-400">
							生成时间: {new Date(selectedVideoForViewing.submitTime || '').toLocaleString()}
						</div>
						<div class="text-xs text-gray-500 dark:text-gray-400">
							状态: {formatStatus(selectedVideoForViewing.status)}
						</div>
						<div class="text-xs text-gray-500 dark:text-gray-400">
							{#if selectedVideoForViewing?.serviceType === 'jimeng'}
								{selectedVideoForViewing.duration}秒 • {selectedVideoForViewing.aspectRatio}
							{:else if selectedVideoForViewing?.serviceType === 'veo'}
								{selectedVideoForViewing?.model || 'veo3'}
							{:else}
								<!-- 可灵任务显示 -->
								{selectedVideoForViewing?.mode || 'std'} • {calculateTotalDuration(selectedVideoForViewing)}秒 • {selectedVideoForViewing.aspectRatio}
								{#if selectedVideoForViewing?.serviceType === 'kling' && selectedVideoForViewing.isExtended}
									<span class="text-purple-600 dark:text-purple-400 ml-1">[已延长{selectedVideoForViewing.extendCount || 1}次]</span>
								{/if}
							{/if}
						</div>
					</div>

					<div class="flex items-center gap-2">
						<button
							on:click={() => {
								const serviceName =
									selectedVideoForViewing?.serviceType === 'jimeng' ? 'jimeng' : 'kling';
								downloadVideo(
									selectedVideoForViewing.videoUrl,
									`${serviceName}-${selectedVideoForViewing.id}.mp4`
								);
							}}
							class="px-3 py-1.5 text-sm bg-green-500 hover:bg-green-600 text-white rounded transition-colors"
						>
							下载
						</button>
						<button
							on:click={() => {
								regenerateWithSameParams(selectedVideoForViewing);
								closeVideoModal();
							}}
							class="px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
						>
							重新生成
						</button>
					</div>
				</div>

				<!-- 提示词详情 -->
				{#if selectedVideoForViewing.prompt}
					<div class="p-4 border-t dark:border-gray-700 bg-gray-25 dark:bg-gray-850">
						<div class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">完整提示词:</div>
						<div class="text-sm text-gray-600 dark:text-gray-400 break-words">
							{selectedVideoForViewing.prompt}
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
