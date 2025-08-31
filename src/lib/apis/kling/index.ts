import { WEBUI_API_BASE_URL } from '$lib/constants';

// 可灵任务状态类型
export type KlingTaskStatus = 'submitted' | 'processing' | 'succeed' | 'failed';

// 可灵任务动作类型
export type KlingTaskAction = 'TEXT_TO_VIDEO' | 'IMAGE_TO_VIDEO' | 'MULTI_IMAGE_TO_VIDEO' | 'VIDEO_EXTEND';

// 可灵视频模式类型
export type KlingVideoMode = 'std' | 'pro';

// 可灵配置接口
export interface KlingConfig {
	enabled: boolean;
	baseUrl: string;
	apiKey: string;
	textToVideoModel: string;
	imageToVideoModel: string;
	defaultMode: string;
	defaultDuration: string;
	defaultAspectRatio: string;
	defaultCfgScale: number;
	modelCreditsConfig: Record<
		string,
		{
			std: { '5': number; '10': number };
			pro: { '5': number; '10': number };
		}
	>;
	maxConcurrentTasks: number;
	taskTimeout: number;
}

// 摄像机控制配置
export interface CameraControlConfig {
	horizontal?: number; // 水平运镜 [-10, 10]
	vertical?: number; // 垂直运镜 [-10, 10]
	pan?: number; // 水平摇镜 [-10, 10]
	tilt?: number; // 垂直摇镜 [-10, 10]
	roll?: number; // 旋转运镜 [-10, 10]
	zoom?: number; // 变焦 [-10, 10]
}

// 摄像机控制
export interface CameraControl {
	type?: 'simple' | 'down_back' | 'forward_up' | 'right_turn_forward' | 'left_turn_forward';
	config?: CameraControlConfig;
}

// 轨迹点
export interface TrajectoryPoint {
	x: number;
	y: number;
}

// 动态笔刷
export interface DynamicMask {
	mask: string; // base64图片数据
	trajectories: TrajectoryPoint[];
}

// 可灵视频生成请求参数
export interface KlingGenerateRequest {
	modelName?: string;
	prompt: string;
	negativePrompt?: string;
	cfgScale?: number;
	mode?: KlingVideoMode;
	duration?: string; // '5' | '10'
	aspectRatio?: string; // '16:9' | '9:16' | '1:1'

	// 图生视频专用
	image?: string; // base64数据
	imageTail?: string; // 尾帧图片
	staticMask?: string; // 静态笔刷
	dynamicMasks?: DynamicMask[]; // 动态笔刷

	// 多图参考生成专用
	generationMode?: string; // 'single_image' | 'multi_image'
	imageList?: Array<{ image: string }>; // 多图参考列表，最多4张

	// 摄像机控制
	cameraControl?: CameraControl;

	// 回调和自定义ID
	callbackUrl?: string;
	externalTaskId?: string;
}

// 可灵任务接口
export interface KlingTask {
	id: string;
	userId: string;
	externalTaskId?: string;
	action: KlingTaskAction;
	status: KlingTaskStatus;
	taskStatusMsg?: string;

	// 基础参数
	modelName?: string;
	prompt: string;
	negativePrompt?: string;
	cfgScale?: number;
	mode: string;
	duration: string;
	aspectRatio: string;

	// 图生视频参数
	inputImage?: string;
	imageTail?: string;
	staticMask?: string;
	dynamicMasks?: DynamicMask[];
	cameraControl?: CameraControl;

	// 多图参考参数
	generationMode?: string;
	inputImages?: Array<{ image: string }>;
	imageCount?: number;

	// 视频延长参数
	parentTaskId?: string;
	isExtended?: boolean;
	originalDuration?: string;
	extendCount?: number;

	// 任务管理
	creditsCost: number;
	submitTime?: string;
	startTime?: string;
	finishTime?: string;

	// 结果数据
	videoId?: string;
	videoUrl?: string;
	videoDuration?: string;
	failReason?: string;

	// 元数据
	properties?: any;
	progress: string;
	createdAt: string;
	updatedAt: string;
}

// 可灵历史记录响应
export interface KlingHistoryResponse {
	data: KlingTask[];
	total: number;
	page: number;
	limit: number;
}

// 视频延长请求参数
export interface KlingVideoExtendRequest {
	videoId: string;
	prompt?: string;
	negativePrompt?: string;
	cfgScale?: number;
	callbackUrl?: string;
}

// 视频延长资格检查响应
export interface KlingVideoExtendCheck {
	canExtend: boolean;
	reason?: string;
	creditsCost?: number;
	currentDuration: string;
	extendCount: number;
	maxDuration?: string;
}

// ======================== API 函数 ========================

// 获取可灵配置 (管理员)
export const getKlingConfig = async (token: string): Promise<KlingConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/config`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换后端下划线命名到前端驼峰命名
			if (data) {
				return {
					enabled: data.enabled,
					baseUrl: data.base_url || 'https://api.klingai.com',
					apiKey: data.api_key || '',
					textToVideoModel: data.text_to_video_model || 'kling-v1',
					imageToVideoModel: data.image_to_video_model || 'kling-v1',
					defaultMode: data.default_mode || 'std',
					defaultDuration: data.default_duration || '5',
					defaultAspectRatio: data.default_aspect_ratio || '16:9',
					defaultCfgScale: data.default_cfg_scale || 0.5,
					modelCreditsConfig: data.model_credits_config || {},
					maxConcurrentTasks: data.max_concurrent_tasks || 3,
					taskTimeout: data.task_timeout || 600000
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Kling config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取可灵用户配置
export const getKlingUserConfig = async (token: string): Promise<KlingConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/config/user`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换后端下划线命名到前端驼峰命名 (用户配置)
			if (data) {
				return {
					enabled: data.enabled,
					baseUrl: '', // 用户配置不包含敏感信息
					apiKey: '', // 用户配置不包含敏感信息
					textToVideoModel: data.text_to_video_model || 'kling-v1',
					imageToVideoModel: data.image_to_video_model || 'kling-v1',
					defaultMode: data.default_mode || 'std',
					defaultDuration: data.default_duration || '5',
					defaultAspectRatio: data.default_aspect_ratio || '16:9',
					defaultCfgScale: data.default_cfg_scale || 0.5,
					modelCreditsConfig: data.model_credits_config || {},
					maxConcurrentTasks: data.max_concurrent_tasks || 3,
					taskTimeout: data.task_timeout || 600000
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Kling user config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 保存可灵配置 (管理员)
export const saveKlingConfig = async (token: string, config: KlingConfig): Promise<any> => {
	let error = null;

	// 转换前端驼峰命名到后端下划线命名
	const backendConfig = {
		enabled: config.enabled,
		base_url: config.baseUrl,
		api_key: config.apiKey,
		text_to_video_model: config.textToVideoModel,
		image_to_video_model: config.imageToVideoModel,
		default_mode: config.defaultMode,
		default_duration: config.defaultDuration,
		default_aspect_ratio: config.defaultAspectRatio,
		default_cfg_scale: config.defaultCfgScale,
		model_credits_config: config.modelCreditsConfig,
		max_concurrent_tasks: config.maxConcurrentTasks,
		task_timeout: config.taskTimeout
	};

	console.log('🎬 【可灵前端】保存配置:', backendConfig);

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/config`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(backendConfig)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to save Kling config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 测试可灵连接
export const testKlingConnection = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/test`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to test Kling connection';
			console.log(err);
			return { status: 'error', message: error };
		});

	if (error) {
		return { status: 'error', message: error };
	}

	return res;
};

// 提交文生视频任务
export const submitKlingTextToVideoTask = async (
	token: string,
	request: KlingGenerateRequest
): Promise<{ success: boolean; task_id: string; message: string }> => {
	let error = null;

	// 转换参数名称为后端期望的格式
	const backendRequest = {
		model_name: request.modelName,
		prompt: request.prompt,
		negative_prompt: request.negativePrompt,
		cfg_scale: request.cfgScale,
		mode: request.mode,
		duration: request.duration,
		aspect_ratio: request.aspectRatio,
		camera_control: request.cameraControl,
		callback_url: request.callbackUrl,
		external_task_id: request.externalTaskId
	};

	// 移除undefined字段
	Object.keys(backendRequest).forEach((key) => {
		if (backendRequest[key] === undefined) {
			delete backendRequest[key];
		}
	});

	console.log('🎬 【可灵前端】提交文生视频任务:', backendRequest);

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/submit/text-to-video`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(backendRequest)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to submit text-to-video task';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 提交图生视频任务
export const submitKlingImageToVideoTask = async (
	token: string,
	request: KlingGenerateRequest
): Promise<{ success: boolean; task_id: string; message: string }> => {
	let error = null;

	// 转换参数名称为后端期望的格式
	const backendRequest = {
		model_name: request.modelName,
		prompt: request.prompt,
		negative_prompt: request.negativePrompt,
		cfg_scale: request.cfgScale,
		mode: request.mode,
		duration: request.duration,
		image: request.image,
		image_tail: request.imageTail,
		static_mask: request.staticMask,
		dynamic_masks: request.dynamicMasks,
		camera_control: request.cameraControl,
		callback_url: request.callbackUrl,
		external_task_id: request.externalTaskId,
		generation_mode: request.generationMode,
		image_list: request.imageList
	};

	// 移除undefined字段
	Object.keys(backendRequest).forEach((key) => {
		if (backendRequest[key] === undefined) {
			delete backendRequest[key];
		}
	});

	console.log('🎬 【可灵前端】提交图生视频任务:', {
		...backendRequest,
		image: backendRequest.image ? `[base64 data, ${backendRequest.image.length} chars]` : undefined,
		image_tail: backendRequest.image_tail
			? `[base64 data, ${backendRequest.image_tail.length} chars]`
			: undefined,
		static_mask: backendRequest.static_mask
			? `[base64 data, ${backendRequest.static_mask.length} chars]`
			: undefined
	});

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/submit/image-to-video`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(backendRequest)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to submit image-to-video task';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 字段名转换辅助函数
const convertTaskFields = (task: any): KlingTask => {
	if (!task) return task;

	return {
		...task,
		videoId: task.video_id,
		videoUrl: task.video_url,
		videoDuration: task.video_duration,
		failReason: task.fail_reason,
		createdAt: task.created_at,
		updatedAt: task.updated_at,
		submitTime: task.submit_time,
		startTime: task.start_time,
		finishTime: task.finish_time,
		externalTaskId: task.external_task_id,
		taskStatusMsg: task.task_status_msg,
		modelName: task.model_name,
		negativePrompt: task.negative_prompt,
		cfgScale: task.cfg_scale,
		aspectRatio: task.aspect_ratio,
		inputImage: task.input_image,
		imageTail: task.image_tail,
		staticMask: task.static_mask,
		dynamicMasks: task.dynamic_masks,
		cameraControl: task.camera_control,
		creditsCost: task.credits_cost,
		generationMode: task.generation_mode,
		inputImages: task.input_images,
		imageCount: task.image_count,
		// 视频延长字段转换
		parentTaskId: task.parent_task_id,
		isExtended: task.is_extended,
		originalDuration: task.original_duration,
		extendCount: task.extend_count
	};
};

// 获取任务状态
export const getKlingTaskStatus = async (token: string, taskId: string): Promise<KlingTask> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/task/${taskId}`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换字段名从下划线到驼峰
			return convertTaskFields(data);
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get task status';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取用户任务历史
export const getKlingUserTaskHistory = async (
	token: string,
	page: number = 1,
	limit: number = 20
): Promise<KlingHistoryResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/history?page=${page}&limit=${limit}`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换任务列表中每个任务的字段名
			if (data && data.data) {
				return {
					...data,
					data: data.data.map(convertTaskFields)
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get task history';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取用户积分余额
export const getKlingUserCredits = async (token: string): Promise<{ balance: number }> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/credits`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get user credits';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 删除任务
export const deleteKlingTask = async (token: string, taskId: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/task/${taskId}`, {
		method: 'DELETE',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to delete task';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取用户统计
export const getKlingUserStats = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/stats/user`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get user stats';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// ======================== 视频延长功能 ========================

// 检查视频延长资格
export const checkKlingVideoExtendEligibility = async (
	token: string,
	videoId: string
): Promise<KlingVideoExtendCheck> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/video/${videoId}/extend/check`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换字段名从下划线到驼峰
			return {
				canExtend: data.can_extend,
				reason: data.reason,
				creditsCost: data.credits_cost,
				currentDuration: data.current_duration,
				extendCount: data.extend_count || 0,
				maxDuration: data.max_duration || '180'
			};
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to check video extend eligibility';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 提交视频延长任务
export const submitKlingVideoExtendTask = async (
	token: string,
	request: KlingVideoExtendRequest
): Promise<{ success: boolean; task_id: string; message: string; credits_cost: number }> => {
	let error = null;

	// 转换参数名称为后端期望的格式
	const backendRequest = {
		video_id: request.videoId,
		prompt: request.prompt,
		negative_prompt: request.negativePrompt,
		cfg_scale: request.cfgScale,
		callback_url: request.callbackUrl
	};

	// 移除undefined字段
	Object.keys(backendRequest).forEach((key) => {
		if (backendRequest[key] === undefined) {
			delete backendRequest[key];
		}
	});

	console.log('🎬 【可灵延长】提交视频延长任务:', backendRequest);

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/video/extend`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(backendRequest)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to submit video extend task';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取视频延长任务状态
export const getKlingVideoExtendTaskStatus = async (
	token: string,
	taskId: string
): Promise<KlingTask> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling/video/extend/${taskId}`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换字段名从下划线到驼峰
			return convertTaskFields(data);
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get video extend task status';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
