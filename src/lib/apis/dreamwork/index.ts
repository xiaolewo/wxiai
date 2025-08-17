import { WEBUI_API_BASE_URL } from '$lib/constants';

// DreamWork 任务状态类型
export type DreamWorkTaskStatus = 'SUBMITTED' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILURE';

// DreamWork 任务动作类型
export type DreamWorkTaskAction = 'TEXT_TO_IMAGE' | 'IMAGE_TO_IMAGE';

// DreamWork 配置接口
export interface DreamWorkConfig {
	enabled: boolean;
	baseUrl: string;
	apiKey: string;
	textToImageModel: string;
	imageToImageModel: string;
	defaultSize: string;
	defaultGuidanceScale: number;
	watermarkEnabled: boolean;
	creditsPerGeneration: number;
	maxConcurrentTasks: number;
	taskTimeout: number;
}

// DreamWork 生成请求参数
export interface DreamWorkGenerateRequest {
	model: string;
	prompt: string;
	responseFormat?: string; // 'url' | 'b64_json'
	size?: string;
	seed?: number;
	guidanceScale?: number;
	watermark?: boolean;
	image?: string; // 图生图时的输入图片(base64)
}

// DreamWork 任务接口
export interface DreamWorkTask {
	id: string;
	action: DreamWorkTaskAction;
	status: DreamWorkTaskStatus;
	prompt: string;
	model: string;
	size: string;
	guidanceScale?: number;
	seed?: number;
	watermark: boolean;
	submitTime: number;
	startTime?: number;
	finishTime?: number;
	progress: string;
	imageUrl?: string;
	failReason?: string;
	inputImage?: string; // 图生图的输入图片
	creditsCost: number;
	properties?: Record<string, any>;
}

// 获取 DreamWork 配置 (管理员专用)
export const getDreamWorkConfig = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/config`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换后端下划线命名到前端驼峰命名
			if (data) {
				return {
					enabled: data.enabled,
					baseUrl: data.base_url || '',
					apiKey: data.api_key || '',
					textToImageModel: data.text_to_image_model || 'doubao-seedream-3-0-t2i-250415',
					imageToImageModel: data.image_to_image_model || 'doubao-seededit-3-0-i2i-250628',
					defaultSize: data.default_size || '1024x1024',
					defaultGuidanceScale: data.default_guidance_scale || 2.5,
					watermarkEnabled: data.watermark_enabled !== undefined ? data.watermark_enabled : true,
					creditsPerGeneration: data.credits_per_generation || 10,
					maxConcurrentTasks: data.max_concurrent_tasks || 5,
					taskTimeout: data.task_timeout || 300000
				};
			}
			return data;
		})
		.catch((err) => {
			console.error(err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取 DreamWork 用户配置 (普通用户可用)
export const getDreamWorkUserConfig = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/config/user`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 处理用户配置数据
			if (data) {
				return {
					enabled: data.enabled,
					textToImageModel: data.text_to_image_model || 'doubao-seedream-3-0-t2i-250415',
					imageToImageModel: data.image_to_image_model || 'doubao-seededit-3-0-i2i-250628',
					defaultSize: data.default_size || '1024x1024',
					defaultGuidanceScale: data.default_guidance_scale || 2.5,
					watermarkEnabled: data.watermark_enabled !== undefined ? data.watermark_enabled : true,
					creditsPerGeneration: data.credits_per_generation || 10
				};
			}
			return data;
		})
		.catch((err) => {
			console.error(err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 保存 DreamWork 配置
export const saveDreamWorkConfig = async (token: string = '', config: Partial<DreamWorkConfig>) => {
	let error = null;

	// 转换前端驼峰命名到后端下划线命名
	const backendConfig = {
		enabled: config.enabled,
		base_url: config.baseUrl,
		api_key: config.apiKey,
		text_to_image_model: config.textToImageModel,
		image_to_image_model: config.imageToImageModel,
		default_size: config.defaultSize,
		default_guidance_scale: config.defaultGuidanceScale,
		watermark_enabled: config.watermarkEnabled,
		credits_per_generation: config.creditsPerGeneration,
		max_concurrent_tasks: config.maxConcurrentTasks,
		task_timeout: config.taskTimeout
	};

	const res = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/config`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(backendConfig)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 测试 DreamWork 连接
export const testDreamWorkConnection = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/test`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 提交文生图任务
export const submitTextToImageTask = async (
	token: string = '',
	request: DreamWorkGenerateRequest
) => {
	let error = null;

	console.log('🎨 【DreamWork前端】文生图请求:', request);

	// 转换参数名从驼峰到下划线
	const backendRequest = {
		model: request.model,
		prompt: request.prompt,
		response_format: request.responseFormat || 'b64_json',
		size: request.size,
		seed: request.seed,
		guidance_scale: request.guidanceScale,
		watermark: request.watermark,
		...(request.image && { image: request.image })
	};

	console.log('🎨 【DreamWork前端】转换后的请求:', backendRequest);

	const res = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/submit/text-to-image`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(backendRequest)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error('🎨 【DreamWork前端】文生图错误:', err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 提交图生图任务
export const submitImageToImageTask = async (
	token: string = '',
	request: DreamWorkGenerateRequest
) => {
	let error = null;

	console.log('🎨 【DreamWork前端】图生图请求:', {
		prompt: request.prompt,
		model: request.model,
		size: request.size,
		hasInputImage: !!request.image,
		inputImageLength: request.image?.length || 0
	});

	// 转换参数名从驼峰到下划线
	const backendRequest = {
		model: request.model,
		prompt: request.prompt,
		response_format: request.responseFormat || 'b64_json',
		size: request.size,
		seed: request.seed,
		guidance_scale: request.guidanceScale,
		watermark: request.watermark,
		image: request.image
	};

	console.log('🎨 【DreamWork前端】转换后的请求:', {
		...backendRequest,
		image: backendRequest.image ? `${backendRequest.image.substring(0, 50)}...` : 'None'
	});

	const res = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/submit/image-to-image`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(backendRequest)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error('🎨 【DreamWork前端】图生图错误:', err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取任务状态
export const getDreamWorkTaskStatus = async (
	token: string = '',
	taskId: string
): Promise<DreamWorkTask | null> => {
	console.log('🎨 【DreamWork前端】获取任务状态:', taskId);

	try {
		const headers = {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		};

		const response = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/task/${taskId}`, {
			method: 'GET',
			headers
		});

		console.log('🎨 【DreamWork前端】API响应状态:', response.status);

		if (!response.ok) {
			const errorData = await response.json();
			console.error('🎨 【DreamWork前端】API错误:', errorData);
			return null;
		}

		const result = await response.json();
		console.log('🎨 【DreamWork前端】API成功响应:', {
			id: result.id,
			status: result.status,
			progress: result.progress,
			hasImage: !!result.imageUrl
		});
		return result;
	} catch (error) {
		console.error('🎨 【DreamWork前端】API调用异常:', error);
		return null;
	}
};

// 获取用户任务历史
export const getDreamWorkUserTaskHistory = async (
	token: string = '',
	page: number = 1,
	limit: number = 20
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/history?page=${page}&limit=${limit}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取用户积分余额
export const getDreamWorkUserCredits = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/credits`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 删除任务
export const deleteDreamWorkTask = async (token: string = '', taskId: string): Promise<boolean> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/dreamwork/task/${taskId}`, {
			method: 'DELETE',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		});

		if (!response.ok) {
			const errorData = await response.json();
			console.error('删除DreamWork任务失败:', errorData);
			return false;
		}

		return true;
	} catch (error) {
		console.error('删除DreamWork任务异常:', error);
		return false;
	}
};

// 图片处理工具函数
export const encodeImageToBase64 = (file: File): Promise<string> => {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = () => {
			const result = reader.result as string;
			// 移除data:image/...;base64,前缀，只保留base64数据
			const base64Data = result.split(',')[1];
			resolve(base64Data);
		};
		reader.onerror = reject;
		reader.readAsDataURL(file);
	});
};

// 验证图片格式
export const validateImageFormat = (file: File): boolean => {
	const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
	return allowedTypes.includes(file.type);
};

// 验证图片大小
export const validateImageSize = (file: File, maxSizeMB: number = 10): boolean => {
	const maxSizeBytes = maxSizeMB * 1024 * 1024;
	return file.size <= maxSizeBytes;
};
