import { WEBUI_API_BASE_URL } from '$lib/constants';

export type SeedanceTaskStatus = 'submitted' | 'processing' | 'succeed' | 'failed';
export type SeedanceTaskAction = 'TEXT_TO_VIDEO' | 'IMAGE_TO_VIDEO' | 'IMAGE_TO_VIDEO_FIRST_LAST';

export type SeedanceGenerateMode = 'text_to_video' | 'image_to_video' | 'image_to_video_first_last';

export interface SeedanceConfig {
	enabled: boolean;
	baseUrl: string;
	apiKey: string;
	defaultModel: string;
	defaultDuration: string;
	defaultResolution: string;
	defaultRatio: string;
	defaultWatermark: boolean;
	defaultCameraFixed: boolean;
	defaultReturnLastFrame: boolean;
	creditsPer5s: number;
	creditsPer10s: number;
	queryInterval: number;
	maxConcurrentTasks: number;
	taskTimeout: number;
	modelCreditsConfig?: Record<string, unknown>;
}

export interface SeedanceGenerateRequest {
	prompt: string;
	model: string;
	mode: SeedanceGenerateMode;
	duration?: string;
	resolution?: string;
	ratio?: string;
	watermark?: boolean;
	seed?: number;
	camera_fixed?: boolean;
	return_last_frame?: boolean;
	images?: string[]; // base64 或 data URL
}

export interface SeedanceTask {
	id: string;
	userId: string;
	externalTaskId?: string;
	serviceType: 'seedance';
	action: SeedanceTaskAction;
	status: SeedanceTaskStatus;
	prompt: string;
	model?: string;
	duration?: string;
	resolution?: string;
	ratio?: string;
	watermark?: boolean;
	seed?: number;
	camera_fixed?: boolean;
	return_last_frame?: boolean;
	imageUrls?: string[];
	creditsCost: number;
	submitTime?: string;
	startTime?: string;
	finishTime?: string;
	videoUrl?: string;
	cloudVideoUrl?: string;
	lastFrameUrl?: string;
	cloudLastFrameUrl?: string;
	progress?: string;
	failReason?: string;
	properties?: any;
	createdAt?: string;
	updatedAt?: string;
}

export interface SeedanceHistoryResponse {
	data: SeedanceTask[];
	total: number;
	page: number;
	limit: number;
}

export interface SeedanceCreditsResponse {
	balance: number;
}

export interface SeedanceTaskSubmitResponse {
	success: boolean;
	task_id: string;
	message: string;
}

const handleResponse = async (res: Response) => {
	if (!res.ok) {
		let detail = res.statusText;
		try {
			const body = await res.json();
			detail = body?.detail ?? body?.message ?? JSON.stringify(body);
		} catch (error) {
			// ignore
		}
		throw new Error(detail);
	}
	try {
		return await res.json();
	} catch (error) {
		return null;
	}
};

export const getSeedanceConfig = async (token: string): Promise<SeedanceConfig> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/config`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	const data = await handleResponse(res);
	return {
		enabled: Boolean(data?.enabled),
		baseUrl: data?.base_url ?? 'https://ark.cn-beijing.volces.com',
		apiKey: data?.api_key ?? '',
		defaultModel: data?.default_model ?? 'doubao-seedance-1-0-pro-250528',
		defaultDuration: data?.default_duration ?? '5',
		defaultResolution: data?.default_resolution ?? '720p',
		defaultRatio: data?.default_ratio ?? '16:9',
		defaultWatermark: Boolean(data?.default_watermark),
		defaultCameraFixed: Boolean(data?.default_camera_fixed),
		defaultReturnLastFrame: Boolean(data?.default_return_last_frame),
		creditsPer5s: Number(data?.credits_per_5s ?? 40),
		creditsPer10s: Number(data?.credits_per_10s ?? 80),
		queryInterval: Number(data?.query_interval ?? 10000),
		maxConcurrentTasks: Number(data?.max_concurrent_tasks ?? 5),
		taskTimeout: Number(data?.task_timeout ?? 600000),
		modelCreditsConfig: data?.model_credits_config ?? {}
	};
};

export const saveSeedanceConfig = async (token: string, body: object) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/config`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(body)
	});
	return handleResponse(res);
};

export const testSeedanceConnection = async (token: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/test`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	return handleResponse(res);
};

export const getSeedanceUserConfig = async (token: string): Promise<SeedanceConfig> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/config/user`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	const data = await handleResponse(res);
	return {
		enabled: Boolean(data?.enabled),
		baseUrl: '',
		apiKey: '',
		defaultModel: data?.default_model ?? 'doubao-seedance-1-0-pro-250528',
		defaultDuration: data?.default_duration ?? '5',
		defaultResolution: data?.default_resolution ?? '720p',
		defaultRatio: data?.default_ratio ?? '16:9',
		defaultWatermark: Boolean(data?.default_watermark),
		defaultCameraFixed: Boolean(data?.default_camera_fixed),
		defaultReturnLastFrame: Boolean(data?.default_return_last_frame),
		creditsPer5s: Number(data?.credits_per_5s ?? 40),
		creditsPer10s: Number(data?.credits_per_10s ?? 80),
		queryInterval: Number(data?.query_interval ?? 10000),
		maxConcurrentTasks: Number(data?.max_concurrent_tasks ?? 5),
		taskTimeout: Number(data?.task_timeout ?? 600000),
		modelCreditsConfig: data?.model_credits_config ?? {}
	};
};

export const getSeedanceUserCredits = async (token: string): Promise<SeedanceCreditsResponse> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/credits`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	return handleResponse(res);
};

export const submitSeedanceTextToVideoTask = async (
	token: string,
	request: SeedanceGenerateRequest
) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/submit/text-to-video`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(request)
	});
	return handleResponse(res) as Promise<SeedanceTaskSubmitResponse>;
};

export const submitSeedanceImageToVideoTask = async (
	token: string,
	request: SeedanceGenerateRequest
) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/submit/image-to-video`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(request)
	});
	return handleResponse(res) as Promise<SeedanceTaskSubmitResponse>;
};

export const getSeedanceTaskStatus = async (
	token: string,
	taskId: string
): Promise<SeedanceTask> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/task/${taskId}`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	return handleResponse(res);
};

export const getSeedanceUserTaskHistory = async (
	token: string,
	page = 1,
	limit = 10
): Promise<SeedanceHistoryResponse> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/history?page=${page}&limit=${limit}`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	return handleResponse(res);
};

export const deleteSeedanceTask = async (token: string, taskId: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/seedance/task/${taskId}`, {
		method: 'DELETE',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	return handleResponse(res);
};
