// 海螺（MiniMax Hailuo）API helpers（使用原生 fetch，与其他模块一致）

const apiGet = async (path: string, token?: string) => {
	try {
		const res = await fetch(path, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				...(token ? { Authorization: `Bearer ${token}` } : {})
			}
		});
		if (!res.ok) return null;
		return await res.json();
	} catch (e) {
		console.error('hailuo apiGet error:', e);
		return null;
	}
};

const apiCall = async (
	method: 'GET' | 'POST' | 'DELETE',
	path: string,
	body?: any,
	token?: string
) => {
	try {
		const res = await fetch(path, {
			method,
			headers: {
				'Content-Type': 'application/json',
				...(token ? { Authorization: `Bearer ${token}` } : {})
			},
			body: body ? JSON.stringify(body) : undefined
		});
		if (!res.ok) return null;
		return await res.json();
	} catch (e) {
		console.error('hailuo apiCall error:', e);
		return null;
	}
};

export type HailuoConfig = {
	enabled: boolean;
	base_url: string;
	api_key?: string;
	default_model: string;
	default_duration: number;
	default_resolution: string;
	prompt_optimizer: boolean;
	max_concurrent_tasks: number;
	task_timeout_ms: number;
	query_interval_ms: number;
	model_credits_config?: Record<string, any>;
};

export const getHailuoConfig = async (token: string): Promise<HailuoConfig | null> => {
	const res = await apiGet('/api/v1/hailuo/config', token);
	return res ?? null;
};

export const getHailuoUserConfig = async (token: string): Promise<Partial<HailuoConfig> | null> => {
	const res = await apiGet('/api/v1/hailuo/config/user', token);
	return res ?? null;
};

export const updateHailuoConfig = async (
	token: string,
	payload: Partial<HailuoConfig>
): Promise<boolean> => {
	const res = await apiCall('POST', '/api/v1/hailuo/config', payload, token);
	return !!res?.success;
};

export type HailuoGenerateRequest = {
	model?: string;
	prompt: string;
	duration?: number;
	resolution?: string;
	prompt_optimizer?: boolean;
	first_frame_image?: string; // URL or data URL
	last_frame_image?: string; // URL or data URL
};

export const hailuoGenerate = async (
	token: string,
	req: HailuoGenerateRequest
): Promise<{ success: boolean; task_id?: string; error?: string }> => {
	const res = await apiCall('POST', '/api/v1/hailuo/generate', req, token);
	return res ?? { success: false, error: 'request failed' };
};

export const getHailuoTaskStatus = async (token: string, taskId: string): Promise<any> => {
	const raw = await apiGet(`/api/v1/hailuo/task/${taskId}`, token);
	if (!raw) return null;
	// map to common fields
	return {
		...raw,
		serviceType: 'hailuo',
		action: raw.first_frame_url
			? raw.last_frame_url
				? 'IMAGE_TO_VIDEO'
				: 'IMAGE_TO_VIDEO'
			: 'TEXT_TO_VIDEO',
		videoUrl: raw.cloud_video_url || raw.result_video_url,
		submitTime: raw.created_at,
		duration: String(raw.duration || ''),
		aspectRatio: '16:9'
	};
};

export const getHailuoUserTaskHistory = async (
	token: string,
	page = 1,
	limit = 20
): Promise<{ data: any[] } | null> => {
	const res = await apiGet(`/api/v1/hailuo/history?page=${page}&limit=${limit}`, token);
	if (!res) return null;
	const items = (res.data || []).map((raw: any) => ({
		...raw,
		serviceType: 'hailuo',
		action: raw.first_frame_url
			? raw.last_frame_url
				? 'IMAGE_TO_VIDEO'
				: 'IMAGE_TO_VIDEO'
			: 'TEXT_TO_VIDEO',
		videoUrl: raw.cloud_video_url || raw.result_video_url,
		submitTime: raw.created_at,
		duration: String(raw.duration || ''),
		aspectRatio: '16:9'
	}));
	return { data: items };
};

export const getHailuoUserCredits = async (token: string): Promise<{ balance: number } | null> => {
	const res = await apiGet(`/api/v1/hailuo/credits`, token);
	if (!res) return null;
	return { balance: Number(res.balance || 0) };
};

export const deleteHailuoTask = async (token: string, taskId: string): Promise<boolean> => {
	const res = await apiCall('DELETE', `/api/v1/hailuo/task/${taskId}`, undefined, token);
	return !!res;
};

export const getHailuoTask = async (token: string, taskId: string): Promise<any> => {
	return await apiGet(`/api/v1/hailuo/task/${taskId}`, token);
};
