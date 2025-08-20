/**
 * Flux API 前端封装
 * 支持多种Flux模型的文本生图和图生图功能
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface FluxTextToImageRequest {
	model: string;
	prompt: string;
	num_images?: number;
	aspect_ratio?: string;
	guidance_scale?: number;
	num_inference_steps?: number;
	seed?: number;
	sync_mode?: boolean;
	safety_tolerance?: number;
	output_format?: string;
	enable_safety_checker?: boolean;
}

export interface FluxImageToImageRequest {
	model: string;
	prompt: string;
	image_url: string;
	strength?: number;
	num_images?: number;
	guidance_scale?: number;
	num_inference_steps?: number;
	seed?: number;
	sync_mode?: boolean;
	enable_safety_checker?: boolean;
}

export interface FluxMultiImageRequest {
	model: string;
	prompt: string;
	image_urls: string[];
	num_images?: number;
	aspect_ratio?: string;
	guidance_scale?: number;
	seed?: number;
	sync_mode?: boolean;
	safety_tolerance?: number;
	output_format?: string;
}

export interface FluxTask {
	id: string;
	status: string;
	model: string;
	task_type: string;
	prompt?: string;
	image_url?: string;
	cloud_image_url?: string;
	queue_position?: number;
	generation_time?: number;
	error_message?: string;
	created_at: string;
	updated_at: string;
	completed_at?: string;
	progress?: string;
}

export interface FluxConfig {
	enabled: boolean;
	baseUrl?: string;
	apiKey?: string;
	defaultModel?: string;
	creditsPerGeneration?: number;
	maxConcurrentTasks?: number;
	taskTimeout?: number;
	modelCredits?: Record<string, number>;
	// Legacy fields for backward compatibility
	api_key?: string;
	base_url?: string;
	timeout?: number;
	max_concurrent_tasks?: number;
	default_model?: string;
	models?: FluxModel[];
}

export interface FluxModel {
	id: string;
	name: string;
	type: string;
	description: string;
}

export interface FluxCredits {
	balance: number;
	total_used: number;
}

export interface FluxUploadResponse {
	success: boolean;
	message: string;
	url?: string;
	file_id?: string;
}

// ==================== 配置管理 ====================

/**
 * 获取用户Flux配置
 */
export const getFluxUserConfig = async (token: string): Promise<FluxConfig | null> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/config/user`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			if (res.status === 404) {
				return null; // 服务未配置
			}
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('获取Flux用户配置失败:', error);
		return null;
	}
};

/**
 * 获取支持的Flux模型列表
 */
export const getFluxModels = async (token: string): Promise<FluxModel[]> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/models`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		const data = await res.json();
		return data.models || [];
	} catch (error) {
		console.error('获取Flux模型列表失败:', error);
		return [];
	}
};

// ==================== 任务管理 ====================

/**
 * 提交文本生图任务
 */
export const submitFluxTextToImage = async (
	token: string,
	request: FluxTextToImageRequest
): Promise<FluxTask> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/text-to-image`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(request)
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => null);
			const errorMessage =
				errorData?.detail || errorData?.message || `HTTP ${res.status}: ${res.statusText}`;
			throw new Error(errorMessage);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('提交Flux文本生图任务失败:', error);
		throw error;
	}
};

/**
 * 提交图生图任务
 */
export const submitFluxImageToImage = async (
	token: string,
	request: FluxImageToImageRequest
): Promise<FluxTask> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/image-to-image`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(request)
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => null);
			const errorMessage =
				errorData?.detail || errorData?.message || `HTTP ${res.status}: ${res.statusText}`;
			throw new Error(errorMessage);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('提交Flux图生图任务失败:', error);
		throw error;
	}
};

/**
 * 提交多图编辑任务
 */
export const submitFluxMultiImage = async (
	token: string,
	request: FluxMultiImageRequest
): Promise<FluxTask> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/multi-image-edit`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(request)
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => null);
			const errorMessage =
				errorData?.detail || errorData?.message || `HTTP ${res.status}: ${res.statusText}`;
			throw new Error(errorMessage);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('提交Flux多图编辑任务失败:', error);
		throw error;
	}
};

/**
 * 获取任务状态
 */
export const getFluxTaskStatus = async (
	token: string,
	taskId: string
): Promise<FluxTask | null> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/task/${taskId}`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			if (res.status === 404) {
				return null;
			}
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('获取Flux任务状态失败:', error);
		return null;
	}
};

/**
 * 取消任务
 */
export const cancelFluxTask = async (token: string, taskId: string): Promise<boolean> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/task/${taskId}`, {
			method: 'DELETE',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		return res.ok;
	} catch (error) {
		console.error('取消Flux任务失败:', error);
		return false;
	}
};

/**
 * 获取用户历史记录
 */
export const getFluxUserTaskHistory = async (
	token: string,
	page: number = 1,
	limit: number = 20
): Promise<{ data: FluxTask[]; total: number } | null> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/history?page=${page}&limit=${limit}`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('获取Flux历史记录失败:', error);
		return null;
	}
};

/**
 * 删除任务
 */
export const deleteFluxTask = async (token: string, taskId: string): Promise<boolean> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/task/${taskId}`, {
			method: 'DELETE',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		return res.ok;
	} catch (error) {
		console.error('删除Flux任务失败:', error);
		return false;
	}
};

// ==================== 文件管理 ====================

/**
 * 上传图片用于图生图
 */
export const uploadFluxImage = async (token: string, file: File): Promise<FluxUploadResponse> => {
	try {
		const formData = new FormData();
		formData.append('file', file);

		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/upload-image`, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${token}`
			},
			body: formData
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => null);
			const errorMessage =
				errorData?.detail || errorData?.message || `HTTP ${res.status}: ${res.statusText}`;
			throw new Error(errorMessage);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('上传Flux图片失败:', error);
		throw error;
	}
};

/**
 * 批量上传图片用于多图编辑
 */
export const uploadFluxImages = async (
	token: string,
	files: File[]
): Promise<FluxUploadResponse[]> => {
	try {
		const formData = new FormData();
		files.forEach((file) => {
			formData.append('files', file);
		});

		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/upload-images`, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${token}`
			},
			body: formData
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => null);
			const errorMessage =
				errorData?.detail || errorData?.message || `HTTP ${res.status}: ${res.statusText}`;
			throw new Error(errorMessage);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('批量上传Flux图片失败:', error);
		throw error;
	}
};

// ==================== 积分管理 ====================

/**
 * 获取用户积分
 */
export const getFluxUserCredits = async (token: string): Promise<FluxCredits | null> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/credits`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('获取Flux用户积分失败:', error);
		return null;
	}
};

// ==================== 服务状态 ====================

/**
 * 检查Flux服务健康状态
 */
export const checkFluxHealth = async (token: string): Promise<boolean> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/health`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		return res.ok;
	} catch (error) {
		console.error('检查Flux服务状态失败:', error);
		return false;
	}
};

// ==================== 工具函数 ====================

/**
 * 格式化Flux任务进度显示
 */
export const formatFluxProgress = (task: FluxTask): string => {
	if (task.status === 'SUCCESS' && task.cloud_image_url) {
		return '100%';
	}

	if (task.status === 'FAILED' || task.status === 'FAILURE') {
		return '失败';
	}

	if (task.queue_position !== undefined && task.queue_position > 0) {
		return `队列中 (${task.queue_position})`;
	}

	if (task.status === 'IN_PROGRESS') {
		return '生成中...';
	}

	if (task.status === 'IN_QUEUE') {
		return '排队中...';
	}

	return task.progress || '0%';
};

/**
 * 获取Flux任务显示状态
 */
export const getFluxTaskDisplayStatus = (task: FluxTask): string => {
	if (task.status === 'SUCCESS' && task.cloud_image_url) {
		return 'SUCCESS';
	}

	if (task.status === 'FAILED' || task.status === 'FAILURE') {
		return 'FAILURE';
	}

	return task.status;
};

/**
 * 检查任务是否完成
 */
export const isFluxTaskCompleted = (task: FluxTask): boolean => {
	return task.status === 'SUCCESS' || task.status === 'FAILED' || task.status === 'FAILURE';
};

/**
 * 获取任务的显示图片URL
 */
export const getFluxTaskImageUrl = (task: FluxTask): string | null => {
	return task.cloud_image_url || task.image_url || null;
};

// ==================== 管理员配置API ====================

/**
 * 获取管理员Flux配置
 */
export const getFluxConfig = async (token: string): Promise<FluxConfig | null> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/admin/config`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			if (res.status === 404) {
				return null; // 配置不存在，返回默认值
			}
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('获取Flux管理员配置失败:', error);
		return null;
	}
};

/**
 * 保存管理员Flux配置
 */
export const saveFluxConfig = async (token: string, config: FluxConfig): Promise<void> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/admin/config`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(config)
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => null);
			const errorMessage =
				errorData?.detail || errorData?.message || `HTTP ${res.status}: ${res.statusText}`;
			throw new Error(errorMessage);
		}
	} catch (error) {
		console.error('保存Flux管理员配置失败:', error);
		throw error;
	}
};

/**
 * 测试Flux连接
 */
export const testFluxConnection = async (
	token: string,
	config: { baseUrl: string; apiKey: string }
): Promise<{ success: boolean; error?: string }> => {
	try {
		const res = await fetch(`${WEBUI_API_BASE_URL}/flux/admin/test-connection`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(config)
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({}));
			return {
				success: false,
				error: errorData.detail || `HTTP ${res.status}: ${res.statusText}`
			};
		}

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('测试Flux连接失败:', error);
		return {
			success: false,
			error: error instanceof Error ? error.message : '连接测试失败'
		};
	}
};
