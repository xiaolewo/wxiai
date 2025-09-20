import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface Jimeng4Config {
	enabled: boolean;
	baseUrl: string;
	apiKey: string;
	defaultModel: string;
	defaultSize: string;
	defaultWatermark: boolean;
	defaultSequentialMode: string;
	defaultN: number;
	creditsPerImage: number;
	maxConcurrentTasks: number;
	taskTimeout: number;
}

export interface Jimeng4GenerateRequest {
	prompt: string;
	model?: string;
	image?: string[];
	n?: number;
	sequential_image_generation?: string;
	response_format?: string;
	size?: string;
	stream?: boolean;
	watermark?: boolean;
}

export interface Jimeng4Task {
	id: string;
	status: string;
	prompt: string;
	model: string;
	size: string;
	n: number;
	request_image_urls?: string[];
	response_urls?: string[];
	cloud_image_urls?: string[];
	fail_reason?: string;
	usage?: Record<string, unknown>;
	sequential_mode?: string;
	response_format?: string;
	stream?: boolean;
	watermark?: boolean;
	credits_cost?: number;
	created_at: string;
	updated_at: string;
	completed_at?: string;
	imageUrl?: string;
}

export interface Jimeng4TaskListResponse {
	items: Jimeng4Task[];
}

export interface Jimeng4UploadResponse {
	success: boolean;
	message: string;
	url?: string;
	fileId?: string;
}

const toCamel = (data: Record<string, unknown>) => ({
	enabled: (data.enabled ?? false) as boolean,
	baseUrl: (data.base_url ?? '') as string,
	apiKey: (data.api_key ?? '') as string,
	defaultModel: (data.default_model ?? 'doubao-seedream-4-0-250828') as string,
	defaultSize: (data.default_size ?? '2K') as string,
	defaultWatermark: (data.default_watermark ?? true) as boolean,
	defaultSequentialMode: (data.default_sequential_mode ?? 'auto') as string,
	defaultN: (data.default_n ?? 1) as number,
	creditsPerImage: (data.credits_per_image ?? 30) as number,
	maxConcurrentTasks: (data.max_concurrent_tasks ?? 5) as number,
	taskTimeout: (data.task_timeout ?? 300000) as number
});

const parseResponse = async (res: Response) => {
	const text = await res.text();
	if (!text) return {};
	try {
		return JSON.parse(text);
	} catch (error) {
		return { detail: text };
	}
};

export const getJimeng4Config = async (token: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng4/config`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseResponse(res);
	if (!res.ok) throw data;
	return toCamel(data as Record<string, unknown>);
};

export const saveJimeng4Config = async (token: string, config: Jimeng4Config) => {
	const payload = {
		enabled: config.enabled,
		base_url: config.baseUrl,
		api_key: config.apiKey,
		default_model: config.defaultModel,
		default_size: config.defaultSize,
		default_watermark: config.defaultWatermark,
		default_sequential_mode: config.defaultSequentialMode,
		default_n: config.defaultN,
		credits_per_image: config.creditsPerImage,
		max_concurrent_tasks: config.maxConcurrentTasks,
		task_timeout: config.taskTimeout
	};
	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng4/config`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(payload)
	});
	const data = await parseResponse(res);
	if (!res.ok) throw data;
	const savedConfig = (data as Record<string, unknown>)?.config ?? payload;
	return toCamel(savedConfig as Record<string, unknown>);
};

export const testJimeng4Connection = async (token: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng4/config/test`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseResponse(res);
	if (!res.ok) throw data;
	return data;
};

export const getJimeng4UserConfig = async (token: string): Promise<Jimeng4Config | null> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng4/config/user`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseResponse(res);
	if (!res.ok) return null;
	return toCamel(data as Record<string, unknown>);
};

export const submitJimeng4Task = async (
	token: string,
	request: Jimeng4GenerateRequest
): Promise<{ task: Jimeng4Task }> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng4/generate`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(request)
	});
	const data = await parseResponse(res);
	if (!res.ok) throw data;
	return data as { task: Jimeng4Task };
};

export const getJimeng4TaskStatus = async (token: string, taskId: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng4/tasks/${taskId}`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseResponse(res);
	if (!res.ok) throw data;
	return data as Jimeng4Task;
};

export const getJimeng4TaskHistory = async (token: string, limit = 20, offset = 0) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng4/tasks?limit=${limit}&offset=${offset}`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseResponse(res);
	if (!res.ok) throw data;
	return data as Jimeng4TaskListResponse;
};

export const deleteJimeng4Task = async (token: string, taskId: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng4/tasks/${taskId}`, {
		method: 'DELETE',
		headers: {
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseResponse(res);
	if (!res.ok) throw data;
	return data;
};

export const uploadJimeng4ReferenceImage = async (
	token: string,
	file: File
): Promise<Jimeng4UploadResponse> => {
	const formData = new FormData();
	formData.append('file', file);

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng4/reference/upload`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
		},
		body: formData
	});

	const data = await parseResponse(res);
	if (!res.ok) {
		const detail =
			(data as { detail?: string; message?: string })?.detail ||
			(data as { message?: string })?.message ||
			`上传失败: HTTP ${res.status}`;
		throw new Error(detail);
	}

	const payload = data as Record<string, unknown>;
	return {
		success: (payload.success as boolean) ?? false,
		message: (payload.message as string) ?? '',
		url: (payload.url as string) ?? undefined,
		fileId: (payload.file_id as string) ?? (payload.fileId as string) ?? undefined
	};
};
