import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface BananaConfig {
	enabled: boolean;
	baseUrl: string;
	apiKey?: string;
	defaultModel: string;
	defaultOutputFormat: string;
	defaultAspectRatio: string;
	creditsPerGeneration: number;
	creditsPerEdit: number;
	maxConcurrentTasks: number;
	taskTimeout: number;
}

export interface BananaTask {
	id: string;
	status: string;
	prompt: string;
	model: string;
	task_type: 'generation' | 'edit';
	response_format: string;
	aspect_ratio?: string;
	response_urls?: string[];
	cloud_image_urls?: string[];
	fail_reason?: string;
	credits_cost: number;
	created_at: string;
	updated_at: string;
	completed_at?: string;
}

export interface BananaGenerateRequest {
	prompt: string;
	model?: string;
	aspect_ratio?: string;
	response_format?: string;
	reference_urls?: string[];
	images?: string[];
}

export interface BananaGenerateResponse {
	task: BananaTask;
	raw: Record<string, unknown>;
}

const parseJson = async (res: Response) => {
	const text = await res.text();
	if (!text) return {};
	try {
		return JSON.parse(text);
	} catch (error) {
		return { detail: text };
	}
};

const normalizeConfig = (data: Record<string, unknown>): BananaConfig => ({
	enabled: Boolean(data.enabled),
	baseUrl: (data.base_url as string) ?? '',
	apiKey: (data.api_key as string) ?? '',
	defaultModel: (data.default_model as string) ?? 'nano-banana',
	defaultOutputFormat: (data.default_output_format as string) ?? 'url',
	defaultAspectRatio: (data.default_aspect_ratio as string) ?? '1:1',
	creditsPerGeneration: Number(data.credits_per_generation ?? 10),
	creditsPerEdit: Number(data.credits_per_edit ?? 10),
	maxConcurrentTasks: Number(data.max_concurrent_tasks ?? 5),
	taskTimeout: Number(data.task_timeout ?? 300000)
});

export const getBananaConfig = async (token: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/banana/config`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseJson(res);
	if (!res.ok) throw data;
	return normalizeConfig(data as Record<string, unknown>);
};

export const getBananaUserConfig = async (token: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/banana/config/user`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseJson(res);
	if (!res.ok) throw data;
	return normalizeConfig(data as Record<string, unknown>);
};

export const saveBananaConfig = async (token: string, config: BananaConfig) => {
	const payload = {
		enabled: config.enabled,
		base_url: config.baseUrl,
		api_key: config.apiKey ?? '',
		default_model: config.defaultModel,
		default_output_format: config.defaultOutputFormat,
		default_aspect_ratio: config.defaultAspectRatio,
		credits_per_generation: config.creditsPerGeneration,
		credits_per_edit: config.creditsPerEdit,
		max_concurrent_tasks: config.maxConcurrentTasks ?? 5,
		task_timeout: config.taskTimeout ?? 300000
	};

	const res = await fetch(`${WEBUI_API_BASE_URL}/banana/config`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
	const data = await parseJson(res);
	if (!res.ok) throw data;
	const saved = ((data as Record<string, unknown>)?.config ?? payload) as Record<string, unknown>;
	return normalizeConfig(saved);
};

export const submitBananaTask = async (
	token: string,
	payload: BananaGenerateRequest
): Promise<BananaGenerateResponse> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/banana/generate`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
	const data = await parseJson(res);
	if (!res.ok) throw data;
	return data as BananaGenerateResponse;
};

export const listBananaTasks = async (token: string, page = 1, limit = 20) => {
	const offset = (page - 1) * limit;
	const res = await fetch(`${WEBUI_API_BASE_URL}/banana/tasks?limit=${limit}&offset=${offset}`, {
		headers: {
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseJson(res);
	if (!res.ok) throw data;
	return data as { items: BananaTask[] };
};

export const getBananaTask = async (token: string, taskId: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/banana/tasks/${taskId}`, {
		headers: {
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseJson(res);
	if (!res.ok) throw data;
	return data as BananaTask;
};

export const deleteBananaTask = async (token: string, taskId: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/banana/tasks/${taskId}`, {
		method: 'DELETE',
		headers: {
			Authorization: `Bearer ${token}`
		}
	});
	const data = await parseJson(res);
	if (!res.ok) throw data;
	return data;
};
