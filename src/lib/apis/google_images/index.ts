/**
 * 谷歌生图 API 客户端
 * 支持OpenAI DALL-E兼容格式的图像生成和编辑
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

// ======================== 类型定义 ========================

export interface GoogleImagesGenerateRequest {
	model: string;
	prompt: string;
	images?: string[];
	size?: string;
	n?: number;
	quality?: string;
	style?: string;
}

export interface GoogleImagesTask {
	id: string;
	user_id: string;
	status: string;
	prompt: string;
	model: string;
	size?: string;
	quality?: string;
	style?: string;
	input_images?: string[];
	cloud_input_images?: string[];
	result_images?: string[];
	cloud_result_images?: string[];
	progress?: string;
	fail_reason?: string;
	credits_cost?: number;
	properties?: Record<string, any>;
	created_at: string;
	updated_at?: string;
	finish_time?: string;
}

export interface GoogleImagesConfig {
	enabled: boolean;
	supported_models: string[];
	max_images_per_request: number;
	default_model: string;
	credits_per_generation: number;
	credits_per_image: number;
}

export interface GoogleImagesGenerateResponse {
	success: boolean;
	task_id?: string;
	credits_cost?: number;
	message?: string;
	error?: string;
}

export interface GoogleImagesTaskResponse {
	success: boolean;
	task_id?: string;
	task?: GoogleImagesTask;
	error?: string;
}

// ======================== API 函数 ========================

/**
 * 获取谷歌生图用户配置
 */
export const getGoogleImagesUserConfig = async (
	token: string
): Promise<GoogleImagesConfig | null> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/config/user`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('获取谷歌生图配置失败:', error);
		return null;
	}
};

/**
 * 生成图像 - OpenAI DALL-E 兼容格式
 */
export const generateGoogleImages = async (
	token: string,
	request: GoogleImagesGenerateRequest
): Promise<GoogleImagesGenerateResponse> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/generate`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('谷歌生图生成失败:', error);
		return {
			success: false,
			error: error instanceof Error ? error.message : '未知错误'
		};
	}
};

/**
 * OpenAI DALL-E 兼容的图像编辑接口
 */
export const createGoogleImageEdit = async (
	token: string,
	request: GoogleImagesGenerateRequest
): Promise<any> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/v1/images/edits`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('谷歌生图编辑失败:', error);
		throw error;
	}
};

/**
 * 获取任务状态
 */
export const getGoogleImagesTaskStatus = async (
	token: string,
	taskId: string
): Promise<GoogleImagesTask | null> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/task/${taskId}`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		const result: GoogleImagesTaskResponse = await response.json();
		if (result.success && result.task) {
			return result.task;
		}

		throw new Error(result.error || '获取任务失败');
	} catch (error) {
		console.error('获取谷歌生图任务状态失败:', error);
		return null;
	}
};

/**
 * 获取用户任务历史
 */
export const getGoogleImagesUserTaskHistory = async (
	token: string,
	page: number = 1,
	limit: number = 20
): Promise<{ data: GoogleImagesTask[]; total: number } | null> => {
	try {
		const offset = (page - 1) * limit;
		const response = await fetch(
			`${WEBUI_API_BASE_URL}/google_images/tasks?limit=${limit}&offset=${offset}`,
			{
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				}
			}
		);

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		const result = await response.json();
		if (result.success) {
			return {
				data: result.tasks || [],
				total: result.total || 0
			};
		}

		throw new Error(result.error || '获取任务历史失败');
	} catch (error) {
		console.error('获取谷歌生图任务历史失败:', error);
		return null;
	}
};

/**
 * 删除任务
 */
export const deleteGoogleImagesTask = async (token: string, taskId: string): Promise<boolean> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/task/${taskId}`, {
			method: 'DELETE',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		const result = await response.json();
		return result.success || false;
	} catch (error) {
		console.error('删除谷歌生图任务失败:', error);
		return false;
	}
};

/**
 * 获取用户积分信息
 */
export const getGoogleImagesUserCredits = async (
	token: string
): Promise<{ balance: number } | null> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/credits`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		const result = await response.json();
		if (result.success) {
			return { balance: result.balance || 0 };
		}

		throw new Error(result.error || '获取积分失败');
	} catch (error) {
		console.error('获取谷歌生图积分失败:', error);
		return null;
	}
};

/**
 * 获取积分使用历史
 */
export const getGoogleImagesCreditsHistory = async (
	token: string,
	limit: number = 50
): Promise<any[] | null> => {
	try {
		const response = await fetch(
			`${WEBUI_API_BASE_URL}/google_images/credits/history?limit=${limit}`,
			{
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				}
			}
		);

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		const result = await response.json();
		if (result.success) {
			return result.credits || [];
		}

		throw new Error(result.error || '获取积分历史失败');
	} catch (error) {
		console.error('获取谷歌生图积分历史失败:', error);
		return null;
	}
};

// ======================== 工具函数 ========================

/**
 * 验证图片数据格式
 */
export const validateImageData = (imageData: string): boolean => {
	if (!imageData) return false;

	// 检查是否为Base64格式
	if (imageData.startsWith('data:image/')) {
		return imageData.includes(',') && imageData.split(',')[1].length > 0;
	}

	// 检查是否为URL格式
	if (imageData.startsWith('http')) {
		try {
			new URL(imageData);
			return true;
		} catch {
			return false;
		}
	}

	return false;
};

/**
 * 格式化任务进度
 */
export const formatGoogleImagesProgress = (task: GoogleImagesTask): string => {
	if (task.status === 'completed') return '100%';
	if (task.status === 'failed') return '失败';
	if (task.status === 'processing') return task.progress || '处理中...';
	return '0%';
};

/**
 * 获取任务结果图片URL
 */
export const getGoogleImagesTaskImageUrl = (task: GoogleImagesTask): string | null => {
	// 优先返回云存储图片URL
	if (task.cloud_result_images && task.cloud_result_images.length > 0) {
		return task.cloud_result_images[0];
	}

	// 其次返回原始结果图片URL
	if (task.result_images && task.result_images.length > 0) {
		return task.result_images[0];
	}

	return null;
};

/**
 * 计算积分消费
 */
export const calculateGoogleImagesCredits = (
	config: GoogleImagesConfig,
	request: GoogleImagesGenerateRequest
): number => {
	let totalCredits = config.credits_per_generation;

	// 如果有输入图片，每张额外消耗积分
	if (request.images && request.images.length > 0) {
		totalCredits += request.images.length * config.credits_per_image;
	}

	return totalCredits;
};

/**
 * 转换任务为统一格式（兼容现有UI）
 */
export const convertGoogleImagesTaskToMJFormat = (task: GoogleImagesTask): any => {
	return {
		id: task.id,
		action: 'GENERATE',
		status: task.status.toUpperCase(),
		prompt: task.prompt,
		promptEn: task.prompt,
		description: `谷歌生图: ${task.prompt}`,
		submitTime: new Date(task.created_at).getTime(),
		startTime: task.updated_at ? new Date(task.updated_at).getTime() : 0,
		finishTime: task.finish_time ? new Date(task.finish_time).getTime() : 0,
		progress: formatGoogleImagesProgress(task),
		imageUrl: getGoogleImagesTaskImageUrl(task),
		failReason: task.fail_reason,
		creditsCost: task.credits_cost,
		properties: {
			serviceType: 'google_images',
			model: task.model,
			size: task.size,
			quality: task.quality,
			style: task.style,
			...task.properties
		}
	};
};
