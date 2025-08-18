import { WEBUI_API_BASE_URL } from '$lib/constants';

// MJ 任务状态类型
export type MJTaskStatus =
	| 'NOT_START'
	| 'SUBMITTED'
	| 'MODAL'
	| 'IN_PROGRESS'
	| 'FAILURE'
	| 'SUCCESS'
	| 'CANCEL';

// MJ 任务动作类型
export type MJTaskAction =
	| 'IMAGINE'
	| 'UPSCALE'
	| 'VARIATION'
	| 'ZOOM'
	| 'PAN'
	| 'DESCRIBE'
	| 'BLEND'
	| 'SHORTEN'
	| 'SWAP_FACE';

// MJ 生成模式
export type MJMode = 'turbo' | 'fast' | 'relax';

// MJ 版本
export type MJVersion = 'v5.2' | 'v6' | 'v6.1' | 'v7';

// MJ 图片比例
export type MJAspectRatio =
	| '1:1'
	| '3:2'
	| '3:4'
	| '4:3'
	| '9:16'
	| '2:3'
	| '16:9'
	| '21:9'
	| 'custom';

// MJ 图像质量
export type MJQuality = 0.25 | 0.5 | 1 | 2;

// MJ 参考图片类型
export interface MJReferenceImage {
	id: string;
	base64: string;
	weight: number; // 0.1-3.0
	type: 'normal' | 'style' | 'character'; // 普通参考图、风格参考图、角色参考图
	filename?: string;
}

// MJ 高级参数
export interface MJAdvancedParams {
	chaos?: number; // 0-100 混乱程度
	stylize?: number; // 0-1000 风格化程度
	seed?: number; // 0-4294967295 种子值
	weird?: number; // 0-3000 奇异程度
	quality?: MJQuality; // 0.25-2.0 图像质量
	version?: MJVersion; // MJ版本
	aspectRatio?: MJAspectRatio; // 图片比例
	customAspectRatio?: { width: number; height: number }; // 自定义比例
	tile?: boolean; // 平铺模式
	noCommands?: boolean; // 禁用预设指令
}

// MJ 生成请求参数
export interface MJGenerateRequest {
	prompt: string;
	negativePrompt?: string; // 负面提示词
	mode: MJMode;
	referenceImages?: MJReferenceImage[];
	advancedParams?: MJAdvancedParams;
}

// MJ 按钮类型
export interface MJButton {
	customId: string;
	emoji: string;
	label: string;
	style: number;
	type: number;
}

// MJ 任务接口
export interface MJTask {
	id: string;
	action: MJTaskAction;
	status: MJTaskStatus;
	prompt: string;
	promptEn: string;
	description: string;
	submitTime: number;
	startTime: number;
	finishTime: number;
	progress: string;
	imageUrl?: string;
	failReason?: string;
	properties?: Record<string, any>;
	buttons?: MJButton[];
}

// MJ 配置接口
export interface MJConfig {
	enabled: boolean;
	baseUrl: string;
	apiKey: string;
	modes: {
		turbo: { enabled: boolean; credits: number };
		fast: { enabled: boolean; credits: number };
		relax: { enabled: boolean; credits: number };
	};
	defaultMode: MJMode;
	maxConcurrentTasks: number;
	taskTimeout: number;
	imageProxy: 'relay' | 'origin' | 'proxy';
	webhookUrl?: string;
	webhookSecret?: string;
	enableWebhook?: boolean;
}

// 获取 MJ 配置 (管理员专用)
export const getMJConfig = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/config`, {
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
					modes: data.modes || {
						turbo: { enabled: true, credits: 10 },
						fast: { enabled: true, credits: 5 },
						relax: { enabled: true, credits: 2 }
					},
					defaultMode: data.default_mode || 'fast',
					maxConcurrentTasks: data.max_concurrent_tasks || 5,
					taskTimeout: data.task_timeout || 300000,
					imageProxy: 'relay',
					webhookUrl: '',
					webhookSecret: '',
					enableWebhook: false
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

// 获取 MJ 用户配置 (普通用户可用)
export const getMJUserConfig = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/config/user`, {
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
					modes: data.modes || {
						turbo: { enabled: true, credits: 10 },
						fast: { enabled: true, credits: 5 },
						relax: { enabled: true, credits: 2 }
					},
					defaultMode: data.default_mode || 'fast'
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

// 保存 MJ 配置
export const saveMJConfig = async (token: string = '', config: Partial<MJConfig>) => {
	let error = null;

	// 转换前端驼峰命名到后端下划线命名
	const backendConfig = {
		enabled: config.enabled,
		base_url: config.baseUrl,
		api_key: config.apiKey,
		modes: config.modes,
		default_mode: config.defaultMode,
		max_concurrent_tasks: config.maxConcurrentTasks,
		task_timeout: config.taskTimeout
	};

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/config`, {
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

// 测试 MJ 连接
export const testMJConnection = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/test`, {
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

// 提交 Imagine 任务 (文生图) - 增强版
export const submitImagineTask = async (token: string = '', request: MJGenerateRequest) => {
	let error = null;

	// 不在前端构建参数，让后端统一处理
	// 这样避免重复添加参数的问题
	const finalPrompt = request.prompt;

	// 准备参考图片数据
	const base64Array = request.referenceImages?.map((img) => img.base64) || [];
	const imageWeights = request.referenceImages?.map((img) => img.weight) || [];

	// 🔥 调试信息：检查前端参考图片
	if (request.referenceImages && request.referenceImages.length > 0) {
		console.log('🖼️ 【前端调试】发送参考图片:', {
			数量: request.referenceImages.length,
			图片信息: request.referenceImages.map((img) => ({
				类型: img.type,
				权重: img.weight,
				文件名: img.filename,
				Base64长度: img.base64?.length || 0
			}))
		});
	}

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/submit/imagine`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			prompt: finalPrompt,
			negative_prompt: request.negativePrompt,
			mode: request.mode,
			base64Array,
			imageWeights,
			reference_images: request.referenceImages,
			advanced_params: request.advancedParams
		})
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

// 向后兼容的简单版本
export const submitSimpleImagineTask = async (
	token: string = '',
	prompt: string,
	mode: MJMode = 'fast',
	base64Array: string[] = []
) => {
	const request: MJGenerateRequest = {
		prompt,
		mode,
		referenceImages: base64Array.map((base64, index) => ({
			id: `ref_${index}`,
			base64,
			weight: 1.0,
			type: 'normal' as const
		}))
	};

	return submitImagineTask(token, request);
};

// 提交 Blend 任务 (图生图)
export const submitBlendTask = async (
	token: string = '',
	base64Array: string[],
	mode: MJMode = 'fast',
	dimensions: 'PORTRAIT' | 'SQUARE' | 'LANDSCAPE' = 'SQUARE'
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/submit/blend`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			base64Array,
			mode,
			dimensions
		})
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

// 提交 Describe 任务 (图生文)
export const submitDescribeTask = async (
	token: string = '',
	base64: string,
	mode: MJMode = 'fast'
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/submit/describe`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			base64,
			mode
		})
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

// 执行动作 (U1-U4, V1-V4, 重新生成等)
export const submitActionTask = async (token: string = '', taskId: string, customId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/submit/action`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			task_id: taskId,
			custom_id: customId
		})
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

// 获取任务状态
export const getTaskStatus = async (token: string = '', taskId: string): Promise<MJTask | null> => {
	console.log('🔍 【调试版】前端获取任务状态:', taskId);
	console.log('🔍 【调试版】Token状态:', token ? `有token(${token.length}字符)` : '无token');

	try {
		const headers = {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		};

		console.log('🔍 【调试版】请求头:', Object.keys(headers));

		const response = await fetch(`${WEBUI_API_BASE_URL}/midjourney/task/${taskId}`, {
			method: 'GET',
			headers
		});

		console.log('🔍 【调试版】前端API响应状态:', response.status);

		if (!response.ok) {
			const errorData = await response.json();
			console.error('🔍 【调试版】前端API错误:', errorData);
			if (response.status === 401) {
				console.error('🔍 【调试版】认证失败 - 检查token是否正确传递');
			}
			return null;
		}

		const result = await response.json();
		console.log('🔍 【调试版】前端API成功响应:', {
			id: result.id,
			status: result.status,
			progress: result.progress,
			hasImage: !!result.imageUrl
		});
		return result;
	} catch (error) {
		console.error('🔍 【调试版】前端API调用异常:', error);
		return null;
	}
};

// 获取用户任务历史
export const getUserTaskHistory = async (
	token: string = '',
	page: number = 1,
	limit: number = 20
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/history?page=${page}&limit=${limit}`, {
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

// 获取用户积分余额 - 现在使用系统积分
export const getUserCredits = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/credits`, {
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

// 获取系统积分余额（备用函数，如果需要直接从系统积分API获取）
export const getSystemCredits = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/credit`, {
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

// 提交 Modal 确认任务
export const submitModalTask = async (
	token: string = '',
	taskId: string,
	prompt: string = '',
	maskBase64?: string
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/submit/modal`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			task_id: taskId,
			prompt,
			...(maskBase64 && { mask_base64: maskBase64 })
		})
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

// 获取任务图片的 Seed
export const getTaskImageSeed = async (token: string = '', taskId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/midjourney/task/${taskId}/image-seed`, {
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
export const deleteTask = async (token: string = '', taskId: string): Promise<boolean> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/midjourney/task/${taskId}`, {
			method: 'DELETE',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		});

		if (!response.ok) {
			const errorData = await response.json();
			console.error('删除任务失败:', errorData);
			return false;
		}

		return true;
	} catch (error) {
		console.error('删除任务异常:', error);
		return false;
	}
};

// 修复任务状态
export const fixTaskStates = async (
	token: string = ''
): Promise<{ fixed_count: number } | null> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/midjourney/fix-tasks`, {
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		});

		if (!response.ok) {
			const errorData = await response.json();
			console.error('修复任务状态失败:', errorData);
			return null;
		}

		return await response.json();
	} catch (error) {
		console.error('修复任务状态异常:', error);
		return null;
	}
};
