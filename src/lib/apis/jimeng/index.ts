import { WEBUI_API_BASE_URL } from '$lib/constants';

// 即梦任务状态类型
export type JimengTaskStatus = 'submitted' | 'processing' | 'succeed' | 'failed';

// 即梦任务动作类型
export type JimengTaskAction = 'TEXT_TO_VIDEO' | 'IMAGE_TO_VIDEO';

// 即梦配置接口
export interface JimengConfig {
	enabled: boolean;
	baseUrl: string;
	apiKey: string;
	defaultDuration: string;
	defaultAspectRatio: string;
	defaultCfgScale: number;
	defaultWatermark: boolean;
	creditsPer5s: number;
	creditsPer10s: number;
	maxConcurrentTasks: number;
	taskTimeout: number;
	queryInterval: number;
}

// 即梦视频生成请求参数
export interface JimengGenerateRequest {
	prompt: string;
	imageUrl?: string; // 图生视频时的图片URL
	image?: string; // 图生视频时的base64图片数据
	duration?: string; // '5' | '10'
	aspectRatio?: string; // '1:1' | '21:9' | '16:9' | '9:16' | '4:3' | '3:4'
	cfgScale?: number; // 0-1
	watermark?: boolean; // 是否包含水印

	// 回调和自定义ID
	callbackUrl?: string;
	externalTaskId?: string;
}

// 即梦任务接口
export interface JimengTask {
	id: string;
	userId: string;
	externalTaskId?: string;
	action: JimengTaskAction;
	status: JimengTaskStatus;

	// 基础参数
	prompt: string;
	duration: string;
	aspectRatio: string;
	cfgScale: number;
	watermark: boolean;

	// 图生视频参数
	imageUrl?: string;
	inputImage?: string;

	// 任务管理
	creditsCost: number;
	submitTime?: string;
	startTime?: string;
	completeTime?: string;

	// 结果数据
	videoUrl?: string;
	progress: string;
	failReason?: string;

	// 元数据
	properties?: any;
	createdAt: string;
	updatedAt: string;
}

// 即梦历史记录响应
export interface JimengHistoryResponse {
	data: JimengTask[];
	total: number;
	page: number;
	limit: number;
}

// ======================== API 函数 ========================

// 获取即梦配置 (管理员)
export const getJimengConfig = async (token: string): Promise<JimengConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/config`, {
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
					baseUrl: data.base_url || 'https://ark.cn-beijing.volces.com',
					apiKey: data.api_key || '',
					defaultDuration: data.default_duration || '5',
					defaultAspectRatio: data.default_aspect_ratio || '16:9',
					defaultCfgScale: data.default_cfg_scale || 0.5,
					creditsPer5s: data.credits_per_5s || 30,
					creditsPer10s: data.credits_per_10s || 60,
					maxConcurrentTasks: data.max_concurrent_tasks || 5,
					taskTimeout: data.task_timeout || 600000,
					queryInterval: data.query_interval || 10000
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Jimeng config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取即梦用户配置
export const getJimengUserConfig = async (token: string): Promise<JimengConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/config/user`, {
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
					defaultDuration: data.default_duration || '5',
					defaultAspectRatio: data.default_aspect_ratio || '16:9',
					defaultCfgScale: data.default_cfg_scale || 0.5,
					creditsPer5s: data.credits_per_5s || 30,
					creditsPer10s: data.credits_per_10s || 60,
					maxConcurrentTasks: data.max_concurrent_tasks || 5,
					taskTimeout: data.task_timeout || 600000,
					queryInterval: data.query_interval || 10000
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Jimeng user config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 保存即梦配置 (管理员)
export const saveJimengConfig = async (token: string, config: JimengConfig): Promise<any> => {
	let error = null;

	// 转换前端驼峰命名到后端下划线命名
	const backendConfig = {
		enabled: config.enabled,
		base_url: config.baseUrl,
		api_key: config.apiKey,
		default_duration: config.defaultDuration,
		default_aspect_ratio: config.defaultAspectRatio,
		default_cfg_scale: config.defaultCfgScale,
		credits_per_5s: config.creditsPer5s,
		credits_per_10s: config.creditsPer10s,
		max_concurrent_tasks: config.maxConcurrentTasks,
		task_timeout: config.taskTimeout,
		query_interval: config.queryInterval
	};

	console.log('🌟 【即梦前端】保存配置:', backendConfig);

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/config`, {
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
			error = err.detail ?? 'Failed to save Jimeng config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 测试即梦连接
export const testJimengConnection = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/test`, {
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
			error = err.detail ?? 'Failed to test Jimeng connection';
			console.log(err);
			return { status: 'error', message: error };
		});

	if (error) {
		return { status: 'error', message: error };
	}

	return res;
};

// 提交文生视频任务
export const submitJimengTextToVideoTask = async (
	token: string,
	request: JimengGenerateRequest
): Promise<{ success: boolean; task_id: string; message: string }> => {
	let error = null;

	// 转换参数名称为后端期望的格式
	const backendRequest = {
		prompt: request.prompt,
		duration: request.duration,
		aspect_ratio: request.aspectRatio,
		cfg_scale: request.cfgScale,
		callback_url: request.callbackUrl,
		external_task_id: request.externalTaskId
	};

	// 移除undefined字段
	Object.keys(backendRequest).forEach((key) => {
		if (backendRequest[key] === undefined) {
			delete backendRequest[key];
		}
	});

	console.log('🌟 【即梦前端】提交文生视频任务:', backendRequest);

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/submit/text-to-video`, {
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
export const submitJimengImageToVideoTask = async (
	token: string,
	request: JimengGenerateRequest
): Promise<{ success: boolean; task_id: string; message: string }> => {
	let error = null;

	// 转换参数名称为后端期望的格式
	const backendRequest = {
		prompt: request.prompt,
		image_url: request.imageUrl,
		image: request.image,
		duration: request.duration,
		aspect_ratio: request.aspectRatio,
		cfg_scale: request.cfgScale,
		callback_url: request.callbackUrl,
		external_task_id: request.externalTaskId
	};

	// 移除undefined字段
	Object.keys(backendRequest).forEach((key) => {
		if (backendRequest[key] === undefined) {
			delete backendRequest[key];
		}
	});

	console.log('🌟 【即梦前端】提交图生视频任务:', {
		...backendRequest,
		image: backendRequest.image ? `[base64 data, ${backendRequest.image.length} chars]` : undefined
	});

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/submit/image-to-video`, {
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
const convertTaskFields = (task: any): JimengTask => {
	if (!task) return task;

	return {
		...task,
		videoUrl: task.video_url,
		failReason: task.fail_reason,
		createdAt: task.created_at,
		updatedAt: task.updated_at,
		submitTime: task.submit_time,
		startTime: task.start_time,
		completeTime: task.complete_time,
		externalTaskId: task.external_task_id,
		aspectRatio: task.aspect_ratio,
		cfgScale: task.cfg_scale,
		inputImage: task.input_image,
		imageUrl: task.image_url,
		creditsCost: task.credits_cost
	};
};

// 获取任务状态
export const getJimengTaskStatus = async (token: string, taskId: string): Promise<JimengTask> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/task/${taskId}`, {
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
export const getJimengUserTaskHistory = async (
	token: string,
	page: number = 1,
	limit: number = 20
): Promise<JimengHistoryResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/history?page=${page}&limit=${limit}`, {
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
export const getJimengUserCredits = async (token: string): Promise<{ balance: number }> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/credits`, {
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
export const deleteJimengTask = async (token: string, taskId: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/task/${taskId}`, {
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
export const getJimengUserStats = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng/stats/user`, {
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
