import { WEBUI_API_BASE_URL } from '$lib/constants';

// 可灵对口型任务状态类型
export type KlingLipSyncTaskStatus = 'submitted' | 'processing' | 'succeed' | 'failed';

// 可灵对口型配置接口
export interface KlingLipSyncConfig {
	enabled: boolean;
	baseUrl: string;
	apiKey: string;
	defaultVoice: string;
	defaultLanguage: string;
	defaultSpeed: number;
	defaultPitch: number;
	defaultVolume: number;
	defaultStyle: string;
	defaultRole: string;
	defaultEmotion: string;
	creditsPer30s: number;
	creditsPer60s: number;
	creditsPer120s: number;
	credits_per_task: number;
	maxConcurrentTasks: number;
	taskTimeout: number;
}

// 可灵对口型任务接口
export interface KlingLipSyncTask {
	id: string;
	userId: string;
	externalTaskId?: string;
	status: KlingLipSyncTaskStatus;
	taskStatusMsg?: string;

	// 基础参数
	audioText: string;
	voiceType: string;
	language: string;
	speed: number;
	pitch: number;
	volume: number;
	style?: string;
	role?: string;
	emotion?: string;

	// 任务管理
	creditsCost: number;
	submitTime?: string;
	startTime?: string;
	finishTime?: string;

	// 文件相关
	inputVideoUrl?: string;
	outputVideoUrl?: string;
	cloudVideoUrl?: string;
	videoDuration?: string;
	failReason?: string;

	// 元数据
	properties?: any;
	progress: string;
	createdAt: string;
	updatedAt: string;
}

// 可灵对口型生成请求参数
export interface KlingLipSyncGenerateRequest {
	audioText: string;
	voiceType?: string;
	language?: string;
	speed?: number;
	pitch?: number;
	volume?: number;
	style?: string;
	role?: string;
	emotion?: string;
	callbackUrl?: string;
	externalTaskId?: string;
}

// 可灵对口型历史记录响应
export interface KlingLipSyncHistoryResponse {
	data: KlingLipSyncTask[];
	total: number;
	page: number;
	limit: number;
}

// ======================== API 函数 ========================

// 获取可灵对口型配置 (管理员)
export const getKlingLipSyncConfig = async (token: string): Promise<KlingLipSyncConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/config`, {
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
					defaultVoice: data.default_voice || 'zh-CN-XiaoxiaoNeural',
					defaultLanguage: data.default_language || 'zh-CN',
					defaultSpeed: data.default_speed || 1.0,
					defaultPitch: data.default_pitch || 0,
					defaultVolume: data.default_volume || 50,
					defaultStyle: data.default_style || 'general',
					defaultRole: data.default_role || 'Girl',
					defaultEmotion: data.default_emotion || 'neutral',
					creditsPer30s: data.credits_per_30s || 10,
					creditsPer60s: data.credits_per_60s || 20,
					creditsPer120s: data.credits_per_120s || 40,
					credits_per_task: data.credits_per_task || 50,
					maxConcurrentTasks: data.max_concurrent_tasks || 3,
					taskTimeout: data.task_timeout || 600000
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Kling Lip Sync config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取可灵对口型用户配置
export const getKlingLipSyncUserConfig = async (token: string): Promise<KlingLipSyncConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/config/user`, {
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
					defaultVoice: data.default_voice || 'zh-CN-XiaoxiaoNeural',
					defaultLanguage: data.default_language || 'zh-CN',
					defaultSpeed: data.default_speed || 1.0,
					defaultPitch: data.default_pitch || 0,
					defaultVolume: data.default_volume || 50,
					defaultStyle: data.default_style || 'general',
					defaultRole: data.default_role || 'Girl',
					defaultEmotion: data.default_emotion || 'neutral',
					creditsPer30s: data.credits_per_30s || 10,
					creditsPer60s: data.credits_per_60s || 20,
					creditsPer120s: data.credits_per_120s || 40,
					credits_per_task: data.credits_per_task || 50,
					maxConcurrentTasks: data.max_concurrent_tasks || 3,
					taskTimeout: data.task_timeout || 600000
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Kling Lip Sync user config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 保存可灵对口型配置 (管理员)
export const saveKlingLipSyncConfig = async (
	token: string,
	config: KlingLipSyncConfig
): Promise<any> => {
	let error = null;

	// 转换前端驼峰命名到后端下划线命名
	const backendConfig = {
		enabled: config.enabled,
		base_url: config.baseUrl,
		api_key: config.apiKey,
		default_voice: config.defaultVoice,
		default_language: config.defaultLanguage,
		default_speed: config.defaultSpeed,
		default_pitch: config.defaultPitch,
		default_volume: config.defaultVolume,
		default_style: config.defaultStyle,
		default_role: config.defaultRole,
		default_emotion: config.defaultEmotion,
		credits_per_30s: config.creditsPer30s,
		credits_per_60s: config.creditsPer60s,
		credits_per_120s: config.creditsPer120s,
		credits_per_task: config.credits_per_task,
		max_concurrent_tasks: config.maxConcurrentTasks,
		task_timeout: config.taskTimeout
	};

	console.log('🎤 【可灵对口型前端】保存配置:', backendConfig);

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/config`, {
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
			error = err.detail ?? 'Failed to save Kling Lip Sync config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 测试可灵对口型连接
export const testKlingLipSyncConnection = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/test`, {
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
			error = err.detail ?? 'Failed to test Kling Lip Sync connection';
			console.log(err);
			return { status: 'error', message: error };
		});

	if (error) {
		return { status: 'error', message: error };
	}

	return res;
};

// 提交对口型任务
export const submitKlingLipSyncTask = async (
	token: string,
	videoFile: File,
	request: KlingLipSyncGenerateRequest
): Promise<{ success: boolean; task_id: string; message: string }> => {
	let error = null;

	// 创建FormData对象
	const formData = new FormData();
	formData.append('video', videoFile);

	// 转换参数名称为后端期望的格式
	const backendRequest = {
		audio_text: request.audioText,
		voice_type: request.voiceType,
		language: request.language,
		speed: request.speed,
		pitch: request.pitch,
		volume: request.volume,
		style: request.style,
		role: request.role,
		emotion: request.emotion,
		callback_url: request.callbackUrl,
		external_task_id: request.externalTaskId
	};

	// 移除undefined字段
	Object.keys(backendRequest).forEach((key) => {
		if (backendRequest[key as keyof typeof backendRequest] === undefined) {
			delete backendRequest[key as keyof typeof backendRequest];
		}
	});

	// 将请求参数添加到FormData
	formData.append('request', JSON.stringify(backendRequest));

	console.log('🎤 【可灵对口型前端】提交对口型任务:', {
		...backendRequest,
		videoFile: `${videoFile.name} (${videoFile.size} bytes)`
	});

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/submit`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
			// 注意：不要设置Content-Type，让浏览器自动设置multipart/form-data边界
		},
		body: formData
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to submit lip sync task';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 字段名转换辅助函数
const convertTaskFields = (task: any): KlingLipSyncTask => {
	if (!task) return task;

	return {
		...task,
		externalTaskId: task.external_task_id,
		taskStatusMsg: task.task_status_msg,
		audioText: task.audio_text,
		voiceType: task.voice_type,
		creditsCost: task.credits_cost,
		submitTime: task.submit_time,
		startTime: task.start_time,
		finishTime: task.finish_time,
		inputVideoUrl: task.input_video_url,
		outputVideoUrl: task.output_video_url,
		cloudVideoUrl: task.cloud_video_url,
		videoDuration: task.video_duration,
		failReason: task.fail_reason,
		createdAt: task.created_at,
		updatedAt: task.updated_at,
		// 确保基本字段有默认值
		speed: task.speed || 1.0,
		pitch: task.pitch || 0,
		volume: task.volume || 50,
		progress: task.progress || '0%'
	};
};

// 获取任务状态
export const getKlingLipSyncTaskStatus = async (
	token: string,
	taskId: string
): Promise<KlingLipSyncTask | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/task/${taskId}`, {
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
export const getKlingLipSyncUserTaskHistory = async (
	token: string,
	page: number = 1,
	limit: number = 20
): Promise<KlingLipSyncHistoryResponse> => {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/kling-lip-sync/history?page=${page}&limit=${limit}`,
		{
			method: 'GET',
			headers: {
				Authorization: `Bearer ${token}`,
				'Content-Type': 'application/json'
			}
		}
	)
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
export const getKlingLipSyncUserCredits = async (
	token: string
): Promise<{ balance: number; success: boolean }> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/credits`, {
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
export const deleteKlingLipSyncTask = async (token: string, taskId: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/task/${taskId}`, {
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
export const getKlingLipSyncUserStats = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/stats/user`, {
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
