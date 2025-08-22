import { WEBUI_API_BASE_URL } from '$lib/constants';

// 即梦涂抹消除任务状态类型
export type InpaintingTaskStatus = 'submitted' | 'processing' | 'succeed' | 'failed';

// 即梦涂抹消除配置接口
export interface InpaintingConfig {
	enabled: boolean;
	baseUrl: string;
	apiKey: string;
	creditsPerTask: number;
	maxConcurrentTasks: number;
	taskTimeout: number;
	defaultSteps: number;
	defaultStrength: number;
	defaultScale: number;
	defaultQuality: string;
	defaultDilateSize: number;
}

// 即梦涂抹消除任务接口
export interface InpaintingTask {
	id: string;
	userId: string;
	externalTaskId?: string;
	status: InpaintingTaskStatus;
	taskStatusMsg?: string;

	// 基础参数
	steps: number;
	strength: number;
	scale: number;
	quality: string;
	dilateSize: number;

	// 任务管理
	creditsCost: number;
	submitTime?: string;
	startTime?: string;
	finishTime?: string;

	// 文件相关
	inputImageUrl?: string;
	maskImageUrl?: string;
	outputImageUrl?: string;
	cloudImageUrl?: string;
	failReason?: string;

	// 元数据
	properties?: any;
	progress: string;
	createdAt: string;
	updatedAt: string;
}

// 即梦涂抹消除生成请求参数
export interface InpaintingGenerateRequest {
	steps?: number;
	strength?: number;
	scale?: number;
	quality?: string;
	dilateSize?: number;
	seed?: number;
	callbackUrl?: string;
	externalTaskId?: string;
}

// 即梦涂抹消除历史记录响应
export interface InpaintingHistoryResponse {
	data: InpaintingTask[];
	total: number;
	page: number;
	limit: number;
}

// ======================== API 函数 ========================

// 获取即梦涂抹消除配置 (管理员)
export const getInpaintingConfig = async (token: string): Promise<InpaintingConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/config`, {
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
					baseUrl: data.base_url || 'https://api.linkapi.org',
					apiKey: data.api_key || '',
					creditsPerTask: data.credits_per_task || 50,
					maxConcurrentTasks: data.max_concurrent_tasks || 3,
					taskTimeout: data.task_timeout || 300000,
					defaultSteps: data.default_steps || 30,
					defaultStrength: data.default_strength || 0.8,
					defaultScale: data.default_scale || 7.0,
					defaultQuality: data.default_quality || 'M',
					defaultDilateSize: data.default_dilate_size || 15
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Inpainting config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取即梦涂抹消除用户配置
export const getInpaintingUserConfig = async (token: string): Promise<InpaintingConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/config/user`, {
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
					creditsPerTask: data.credits_per_task || 50,
					maxConcurrentTasks: data.max_concurrent_tasks || 3,
					taskTimeout: data.task_timeout || 300000,
					defaultSteps: data.default_steps || 30,
					defaultStrength: data.default_strength || 0.8,
					defaultScale: data.default_scale || 7.0,
					defaultQuality: data.default_quality || 'M',
					defaultDilateSize: data.default_dilate_size || 15
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Inpainting user config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 保存即梦涂抹消除配置 (管理员)
export const saveInpaintingConfig = async (
	token: string,
	config: InpaintingConfig
): Promise<any> => {
	let error = null;

	// 转换前端驼峰命名到后端下划线命名
	const backendConfig = {
		enabled: config.enabled,
		base_url: config.baseUrl,
		api_key: config.apiKey,
		credits_per_task: config.creditsPerTask,
		max_concurrent_tasks: config.maxConcurrentTasks,
		task_timeout: config.taskTimeout,
		default_steps: config.defaultSteps,
		default_strength: config.defaultStrength,
		default_scale: config.defaultScale,
		default_quality: config.defaultQuality,
		default_dilate_size: config.defaultDilateSize
	};

	console.log('🎨 【即梦涂抹消除前端】保存配置:', backendConfig);

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/config`, {
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
			error = err.detail ?? 'Failed to save Inpainting config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 测试即梦涂抹消除连接
export const testInpaintingConnection = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/test-connection`, {
		method: 'POST',
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
			error = err.detail ?? 'Failed to test Inpainting connection';
			console.log(err);
			return { status: 'error', message: error };
		});

	if (error) {
		return { status: 'error', message: error };
	}

	return res;
};

// 上传图片
export const uploadInpaintingImage = async (
	token: string,
	imageFile: File
): Promise<{ success: boolean; image_url: string; message: string }> => {
	let error = null;

	// 创建FormData对象
	const formData = new FormData();
	formData.append('file', imageFile);

	console.log('🎨 【即梦涂抹消除前端】上传图片:', {
		imageFile: `${imageFile.name} (${imageFile.size} bytes)`
	});

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/upload-image`, {
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
			error = err.detail ?? 'Failed to upload image';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 提交涂抹消除任务
export const submitInpaintingTask = async (
	token: string,
	inputImageBase64: string,
	maskImageBase64: string,
	request: InpaintingGenerateRequest
): Promise<{ success: boolean; task_id: string; message: string; result_image_url?: string }> => {
	let error = null;

	// 转换参数名称为后端期望的格式
	const backendRequest = {
		request: {
			input_image_base64: inputImageBase64,
			mask_image_base64: maskImageBase64,
			steps: request.steps,
			strength: request.strength,
			scale: request.scale,
			quality: request.quality,
			dilate_size: request.dilateSize,
			seed: request.seed
		}
	};

	// 移除undefined字段
	Object.keys(backendRequest.request).forEach((key) => {
		if (backendRequest.request[key as keyof typeof backendRequest.request] === undefined) {
			delete backendRequest.request[key as keyof typeof backendRequest.request];
		}
	});

	console.log('🎨 【即梦涂抹消除前端】提交涂抹消除任务:', backendRequest);

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/inpaint`, {
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
			error = err.detail ?? 'Failed to submit inpainting task';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 字段名转换辅助函数
const convertTaskFields = (task: any): InpaintingTask => {
	if (!task) return task;

	return {
		...task,
		externalTaskId: task.external_task_id,
		taskStatusMsg: task.task_status_msg,
		creditsCost: task.credits_cost,
		submitTime: task.submit_time,
		startTime: task.start_time,
		finishTime: task.finish_time,
		inputImageUrl: task.input_image_url,
		maskImageUrl: task.mask_image_url,
		outputImageUrl: task.output_image_url,
		cloudImageUrl: task.cloud_image_url,
		failReason: task.fail_reason,
		createdAt: task.created_at,
		updatedAt: task.updated_at,
		// 确保基本字段有默认值
		steps: task.steps || 30,
		strength: task.strength || 0.8,
		scale: task.scale || 7.0,
		quality: task.quality || 'M',
		dilateSize: task.dilate_size || 15,
		progress: task.progress || '0%'
	};
};

// 获取任务状态
export const getInpaintingTaskStatus = async (
	token: string,
	taskId: string
): Promise<InpaintingTask | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/task/${taskId}`, {
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
export const getInpaintingUserTaskHistory = async (
	token: string,
	page: number = 1,
	limit: number = 20
): Promise<InpaintingHistoryResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/history?page=${page}&limit=${limit}`, {
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
export const getInpaintingUserCredits = async (
	token: string
): Promise<{ balance: number; success: boolean }> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/credits`, {
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
export const deleteInpaintingTask = async (token: string, taskId: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/task/${taskId}`, {
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
export const getInpaintingUserStats = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/inpainting/stats/user`, {
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
