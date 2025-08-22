// ======================== 谷歌视频前端API接口 ========================

import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface GoogleVideoConfig {
	enabled: boolean;
	base_url: string;
	api_key: string;
	default_text_model: string;
	default_image_model: string;
	default_enhance_prompt: boolean;
	model_credits_config: Record<string, number>;
	max_concurrent_tasks: number;
	task_timeout: number;
}

export interface GoogleVideoTask {
	id: string;
	user_id: string;
	external_task_id?: string;
	task_type: 'text_to_video' | 'image_to_video';
	status: 'SUBMITTED' | 'NOT_START' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILURE';
	action?: string;
	model: string;
	prompt: string;
	enhance_prompt: boolean;
	input_images?: string[];
	uploaded_images?: string[];
	submit_time?: number;
	start_time?: number;
	finish_time?: number;
	progress: string;
	video_url?: string;
	video_duration?: number;
	fail_reason?: string;
	credits_cost: number;
	cloud_upload_status: string;
	created_at: string;
	updated_at: string;
}

export interface GoogleVideoTextToVideoRequest {
	prompt: string;
	model: string;
	enhance_prompt?: boolean;
}

export interface GoogleVideoImageToVideoRequest {
	prompt: string;
	model: string;
	enhance_prompt?: boolean;
	images: string[];
}

export interface GoogleVideoModel {
	id: string;
	name: string;
	description: string;
	maxImages?: number; // 图生视频模型的最大图片数
	imageType?: string; // 图片类型描述
}

export interface GoogleVideoModels {
	text_to_video_models: GoogleVideoModel[];
	image_to_video_models: GoogleVideoModel[];
}

// ======================== API函数 ========================

export async function getGoogleVideoConfig(token: string = ''): Promise<GoogleVideoConfig> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/config`, {
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
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function saveGoogleVideoConfig(
	config: GoogleVideoConfig,
	token: string = ''
): Promise<any> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/config`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(config)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoUserConfig(
	token: string = ''
): Promise<Partial<GoogleVideoConfig>> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/config/user`, {
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
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function testGoogleVideoConnection(
	token: string = ''
): Promise<{ success: boolean; message: string }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/test-connection`, {
		method: 'POST',
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
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return { success: false, message: error };
		});

	if (error && !res) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoModels(token: string = ''): Promise<GoogleVideoModels> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/models`, {
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
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function submitGoogleVideoTextToVideo(
	request: GoogleVideoTextToVideoRequest,
	token: string = ''
): Promise<{ success: boolean; task: GoogleVideoTask }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/text-to-video`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(request)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function submitGoogleVideoImageToVideo(
	request: GoogleVideoImageToVideoRequest,
	token: string = ''
): Promise<{ success: boolean; task: GoogleVideoTask }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/image-to-video`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(request)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoTaskStatus(
	token: string = '',
	taskId: string
): Promise<{ success: boolean; task: GoogleVideoTask }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/task/${taskId}`, {
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
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoUserHistory(
	page: number = 1,
	limit: number = 20,
	token: string = ''
): Promise<{
	success: boolean;
	tasks: GoogleVideoTask[];
	page: number;
	limit: number;
	total: number;
}> {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/google-video/history?page=${page}&limit=${limit}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function deleteGoogleVideoTask(
	token: string = '',
	taskId: string
): Promise<{ success: boolean; message: string }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/task/${taskId}`, {
		method: 'DELETE',
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
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function uploadGoogleVideoImage(
	file: File,
	token: string = ''
): Promise<{ success: boolean; url: string }> {
	let error = null;

	const formData = new FormData();
	formData.append('file', file);

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/upload-image`, {
		method: 'POST',
		headers: {
			...(token && { authorization: `Bearer ${token}` })
		},
		body: formData
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export async function getGoogleVideoUserCredits(
	token: string = ''
): Promise<{ success: boolean; balance: number }> {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/google-video/credits`, {
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
			console.log(err);
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error || !res) {
		throw new Error(error || 'Failed to get Google Video credits');
	}

	return res;
}

// ======================== 模型验证工具函数 ========================

export function validateImageCountForModel(
	model: string,
	imageCount: number
): { valid: boolean; message: string } {
	const modelLimits: Record<string, { max: number; type: string }> = {
		'veo3-pro-frames': { max: 1, type: '首帧' },
		'veo3-fast-frames': { max: 1, type: '首帧' },
		'veo2-fast-frames': { max: 2, type: '首尾帧' },
		'veo2-fast-components': { max: 3, type: '视频元素' }
	};

	const limit = modelLimits[model];
	if (!limit) {
		return { valid: false, message: '不支持的模型' };
	}

	if (imageCount > limit.max) {
		return {
			valid: false,
			message: `${model} 模型最多支持 ${limit.max} 张图片（${limit.type}）`
		};
	}

	if (imageCount === 0) {
		return { valid: false, message: '图生视频必须提供至少一张图片' };
	}

	return { valid: true, message: '' };
}

export function getModelImageLimit(model: string): { max: number; type: string } | null {
	const modelLimits: Record<string, { max: number; type: string }> = {
		'veo3-pro-frames': { max: 1, type: '首帧' },
		'veo3-fast-frames': { max: 1, type: '首帧' },
		'veo2-fast-frames': { max: 2, type: '首尾帧' },
		'veo2-fast-components': { max: 3, type: '视频元素' }
	};

	return modelLimits[model] || null;
}

// ======================== 工具函数 ========================

export function formatGoogleVideoTaskStatus(status: string): string {
	const statusMap: Record<string, string> = {
		NOT_START: '未启动',
		SUBMITTED: '已提交',
		IN_PROGRESS: '生成中',
		SUCCESS: '已完成',
		FAILURE: '失败'
	};
	return statusMap[status] || status;
}

export function formatGoogleVideoTaskType(type: string): string {
	const typeMap: Record<string, string> = {
		text_to_video: '文生视频',
		image_to_video: '图生视频'
	};
	return typeMap[type] || type;
}

export function getGoogleVideoModelCreditsConfig(): Record<string, number> {
	return {
		veo3: 100,
		'veo3-fast': 80,
		'veo3-pro': 150,
		'veo3-pro-frames': 200,
		veo2: 80,
		'veo2-fast': 60,
		'veo2-pro': 120,
		'veo3-fast-frames': 160,
		'veo2-fast-frames': 120,
		'veo2-fast-components': 100
	};
}

export function getGoogleVideoProgressDescription(status: string, progress: string): string {
	switch (status) {
		case 'NOT_START':
			return '等待开始';
		case 'SUBMITTED':
			return '已提交，等待处理';
		case 'IN_PROGRESS':
			return `生成中 ${progress}`;
		case 'SUCCESS':
			return '生成完成';
		case 'FAILURE':
			return '生成失败';
		default:
			return progress || '未知状态';
	}
}

export function isGoogleVideoTaskCompleted(status: string): boolean {
	return status === 'SUCCESS' || status === 'FAILURE';
}

export function isGoogleVideoTaskFailed(status: string): boolean {
	return status === 'FAILURE';
}

export function isGoogleVideoTaskRunning(status: string): boolean {
	return status === 'SUBMITTED' || status === 'IN_PROGRESS';
}
