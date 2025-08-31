/**
 * Veo视频生成API接口
 * 支持Google Veo多模型视频生成，包括文生视频和图生视频
 */

const API_BASE_URL = '/api/v1/veo';

// ======================== 类型定义 ========================

export interface VeoConfig {
	enabled: boolean;
	base_url: string;
	api_key?: string;
	model_credits_config: Record<string, number>;
	default_model: string;
	default_enhance_prompt: boolean;
	max_concurrent_tasks: number;
	task_timeout: number;
	query_interval: number;
}

export interface VeoUserConfig {
	enabled: boolean;
	supported_models: string[];
	model_credits_config: Record<string, number>;
	default_model: string;
	default_enhance_prompt: boolean;
	model_image_limits: Record<string, { max: number; description: string }>;
}

export interface VeoGenerateRequest {
	prompt: string;
	model: string;
	enhance_prompt?: boolean;
	images?: string[];
}

export interface VeoTask {
	id: string;
	user_id: string;
	status: string;
	prompt: string;
	model: string;
	enhance_prompt: boolean;
	input_images?: string[];
	cloud_input_images?: string[];
	result_video_url?: string;
	cloud_video_url?: string;
	external_task_id?: string;
	progress: string;
	fail_reason?: string;
	credits_cost?: number;
	properties?: Record<string, any>;
	created_at: string;
	updated_at?: string;
	finish_time?: string;
	serviceType?: 'veo'; // 兼容字段，用于前端统一处理
	action?: string; // 兼容字段
	videoUrl?: string; // 兼容字段，指向cloud_video_url
	duration?: string; // 兼容字段
	aspectRatio?: string; // 兼容字段
	submitTime?: string; // 兼容字段，指向created_at
}

export interface VeoGenerateResponse {
	success: boolean;
	task_id?: string;
	external_task_id?: string;
	credits_cost?: number;
	message?: string;
	estimated_time?: string;
	error?: string;
}

export interface VeoTaskResponse {
	success: boolean;
	task?: VeoTask;
	error?: string;
}

export interface VeoTasksResponse {
	success: boolean;
	tasks?: VeoTask[];
	total?: number;
	limit?: number;
	offset?: number;
	error?: string;
}

export interface VeoCreditsResponse {
	success: boolean;
	current_balance?: number;
	veo_credits?: Array<{
		id: string;
		task_id: string;
		credit_amount: number;
		operation_type: string;
		model_name?: string;
		description?: string;
		created_at?: string;
	}>;
	statistics?: {
		total_consumed: number;
		total_refunded: number;
		net_consumed: number;
	};
	error?: string;
}

// ======================== API函数 ========================

/**
 * 获取Veo用户配置
 */
export const getVeoUserConfig = async (token: string): Promise<VeoUserConfig | null> => {
	try {
		const response = await fetch(`${API_BASE_URL}/config/user`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			console.error('获取Veo用户配置失败:', response.status, response.statusText);
			return null;
		}

		const data = await response.json();
		return data;
	} catch (error) {
		console.error('获取Veo用户配置异常:', error);
		return null;
	}
};

/**
 * 获取用户Veo积分信息
 */
export const getVeoUserCredits = async (token: string): Promise<{ balance: number } | null> => {
	try {
		console.log('🎯 【Veo前端】开始获取用户积分...');
		
		const response = await fetch(`${API_BASE_URL}/user/credits`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			console.error('🎯 【Veo前端】获取积分失败:', response.status, response.statusText);
			return null;
		}

		const data = await response.json();
		console.log('🎯 【Veo前端】积分API响应:', data);
		
		// 尝试多种可能的响应格式
		let balance = null;
		
		// 格式1: 直接返回 { balance: number }
		if (typeof data.balance === 'number') {
			balance = data.balance;
		}
		// 格式2: 返回 { success: true, current_balance: number }
		else if (data.success && typeof data.current_balance === 'number') {
			balance = data.current_balance;
		}
		// 格式3: 返回 { success: true, balance: number }
		else if (data.success && typeof data.balance === 'number') {
			balance = data.balance;
		}
		
		if (balance !== null) {
			console.log('🎯 【Veo前端】积分余额获取成功:', balance);
			return { balance };
		}
		
		console.warn('🎯 【Veo前端】积分余额解析失败，API响应格式不符合预期:', data);
		return null;
	} catch (error) {
		console.error('🎯 【Veo前端】获取积分异常:', error);
		return null;
	}
};

/**
 * 提交文生视频任务
 */
export const submitVeoTextToVideoTask = async (
	token: string,
	request: VeoGenerateRequest
): Promise<VeoGenerateResponse> => {
	try {
		console.log('🎬 【Veo前端】提交文生视频任务:', request);

		const response = await fetch(`${API_BASE_URL}/generate`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify({
				...request,
				images: undefined // 文生视频不需要图片
			})
		});

		const data = await response.json();
		
		if (!response.ok) {
			console.error('🎬 【Veo前端】文生视频任务提交失败:', data);
			return {
				success: false,
				error: data.detail || data.error || `HTTP ${response.status}`,
				message: data.message
			};
		}

		console.log('🎬 【Veo前端】文生视频任务提交成功:', data);
		return {
			success: true,
			task_id: data.task_id,
			external_task_id: data.external_task_id,
			credits_cost: data.credits_cost,
			message: data.message || '任务已提交',
			estimated_time: data.estimated_time
		};
	} catch (error) {
		console.error('🎬 【Veo前端】文生视频任务提交异常:', error);
		return {
			success: false,
			error: `请求异常: ${error.message || error}`
		};
	}
};

/**
 * 提交图生视频任务
 */
export const submitVeoImageToVideoTask = async (
	token: string,
	request: VeoGenerateRequest
): Promise<VeoGenerateResponse> => {
	try {
		console.log('🎬 【Veo前端】提交图生视频任务:', { ...request, images: request.images?.length });

		const response = await fetch(`${API_BASE_URL}/generate`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(request)
		});

		const data = await response.json();
		
		if (!response.ok) {
			console.error('🎬 【Veo前端】图生视频任务提交失败:', data);
			return {
				success: false,
				error: data.detail || data.error || `HTTP ${response.status}`,
				message: data.message
			};
		}

		console.log('🎬 【Veo前端】图生视频任务提交成功:', data);
		return {
			success: true,
			task_id: data.task_id,
			external_task_id: data.external_task_id,
			credits_cost: data.credits_cost,
			message: data.message || '任务已提交',
			estimated_time: data.estimated_time
		};
	} catch (error) {
		console.error('🎬 【Veo前端】图生视频任务提交异常:', error);
		return {
			success: false,
			error: `请求异常: ${error.message || error}`
		};
	}
};

/**
 * 获取任务状态
 */
export const getVeoTaskStatus = async (token: string, taskId: string): Promise<VeoTask | null> => {
	try {
		const response = await fetch(`${API_BASE_URL}/task/${taskId}`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			console.error('获取Veo任务状态失败:', response.status, response.statusText);
			return null;
		}

		const data: VeoTaskResponse = await response.json();
		
		if (data.success && data.task) {
			// 转换为前端兼容格式
			const task = data.task;
			return {
				...task,
				serviceType: 'veo',
				action: task.input_images?.length ? 'IMAGE_TO_VIDEO' : 'TEXT_TO_VIDEO',
				videoUrl: task.cloud_video_url || task.result_video_url,
				submitTime: task.created_at,
				duration: '10', // Veo默认10秒
				aspectRatio: '16:9' // Veo默认16:9
			};
		}
		
		return null;
	} catch (error) {
		console.error('获取Veo任务状态异常:', error);
		return null;
	}
};

/**
 * 获取用户任务历史
 */
export const getVeoUserTaskHistory = async (
	token: string,
	page: number = 1,
	limit: number = 20
): Promise<{ data: VeoTask[] } | null> => {
	try {
		const response = await fetch(`${API_BASE_URL}/tasks?limit=${limit}&offset=${(page - 1) * limit}`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			console.error('获取Veo任务历史失败:', response.status, response.statusText);
			return null;
		}

		const data: VeoTasksResponse = await response.json();
		
		if (data.success && data.tasks) {
			// 转换为前端兼容格式
			const tasks = data.tasks.map(task => ({
				...task,
				serviceType: 'veo' as const,
				action: task.input_images?.length ? 'IMAGE_TO_VIDEO' : 'TEXT_TO_VIDEO',
				videoUrl: task.cloud_video_url || task.result_video_url,
				submitTime: task.created_at,
				duration: '10', // Veo默认10秒
				aspectRatio: '16:9' // Veo默认16:9
			}));
			
			return { data: tasks };
		}
		
		return null;
	} catch (error) {
		console.error('获取Veo任务历史异常:', error);
		return null;
	}
};

/**
 * 检查任务是否可以被取消
 */
export const canCancelVeoTask = (task: VeoTask): boolean => {
	const cancellableStatuses = ['submitted', 'processing'];
	return cancellableStatuses.includes(task.status);
};

/**
 * 获取任务状态的显示文本和样式
 */
export const getVeoTaskStatusInfo = (status: string) => {
	const statusMap = {
		'submitted': { text: '已提交', class: 'text-blue-600', canCancel: true },
		'processing': { text: '处理中', class: 'text-orange-600', canCancel: true },
		'completed': { text: '已完成', class: 'text-green-600', canCancel: false },
		'failed': { text: '失败', class: 'text-red-600', canCancel: false },
		'cancelled': { text: '已取消', class: 'text-gray-600', canCancel: false },
		'timeout': { text: '超时', class: 'text-red-600', canCancel: false }
	};
	
	return statusMap[status] || { text: status, class: 'text-gray-600', canCancel: false };
};

/**
 * 取消任务（只能取消进行中的任务）
 */
export const cancelVeoTask = async (token: string, taskId: string): Promise<{success: boolean, error?: string, message?: string}> => {
	try {
		console.log('🚫 【Veo前端】取消任务:', taskId);

		const requestBody = {
			action: 'cancel',
			task_id: taskId
		};
		
		console.log('🚫 【Veo前端】请求数据:', requestBody);

		const response = await fetch(`${API_BASE_URL}/action`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(requestBody)
		});

		console.log('🚫 【Veo前端】响应状态:', response.status, response.statusText);

		if (!response.ok) {
			let errorDetail = '';
			let userMessage = '取消任务失败';
			
			try {
				const errorData = await response.json();
				errorDetail = errorData.detail || errorData.message || errorData.error || response.statusText;
				console.error('🚫 【Veo前端】错误详情:', errorData);
				
				if (response.status === 400) {
					if (errorDetail.includes('任务已完成') || errorDetail.includes('已取消')) {
						userMessage = '任务已完成或已取消，无法取消';
					} else {
						userMessage = errorDetail;
					}
				} else if (response.status === 403) {
					userMessage = '没有权限取消此任务';
				} else if (response.status === 404) {
					userMessage = '任务不存在或已被删除';
				} else {
					userMessage = errorDetail || '取消任务失败';
				}
			} catch (e) {
				errorDetail = response.statusText;
				userMessage = '服务错误，请稍后重试';
				console.error('🚫 【Veo前端】无法解析错误响应');
			}
			
			console.error('🚫 【Veo前端】取消任务失败:', response.status, errorDetail);
			return {
				success: false,
				error: userMessage
			};
		}

		const data = await response.json();
		console.log('🚫 【Veo前端】取消任务成功:', data);
		return {
			success: data.success || false,
			message: data.message || '任务已取消'
		};
	} catch (error) {
		console.error('🚫 【Veo前端】取消任务异常:', error);
		return {
			success: false,
			error: '网络连接异常，请检查网络后重试'
		};
	}
};

/**
 * 删除任务（可以删除任何状态的任务）
 */
export const deleteVeoTask = async (token: string, taskId: string): Promise<{success: boolean, error?: string, message?: string}> => {
	try {
		console.log('🗑️ 【Veo前端】删除任务:', taskId);

		const requestBody = {
			action: 'delete',
			task_id: taskId
		};
		
		console.log('🗑️ 【Veo前端】请求数据:', requestBody);

		const response = await fetch(`${API_BASE_URL}/action`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(requestBody)
		});

		console.log('🗑️ 【Veo前端】响应状态:', response.status, response.statusText);

		if (!response.ok) {
			let errorDetail = '';
			let userMessage = '删除任务失败';
			
			try {
				const errorData = await response.json();
				errorDetail = errorData.detail || errorData.message || errorData.error || response.statusText;
				console.error('🗑️ 【Veo前端】错误详情:', errorData);
				
				// 为不同的错误状态提供友好的用户消息
				if (response.status === 400) {
					if (errorDetail.includes('缺少必要参数')) {
						userMessage = '请求参数错误，请刷新页面重试';
					} else {
						userMessage = errorDetail;
					}
				} else if (response.status === 403) {
					userMessage = '没有权限删除此任务';
				} else if (response.status === 404) {
					userMessage = '任务不存在或已被删除';
				} else if (response.status === 502) {
					userMessage = '服务暂时不可用，请稍后重试';
				} else {
					userMessage = errorDetail || '删除任务失败';
				}
			} catch (e) {
				errorDetail = response.statusText;
				userMessage = '服务错误，请稍后重试';
				console.error('🗑️ 【Veo前端】无法解析错误响应');
			}
			
			console.error('🗑️ 【Veo前端】删除任务失败:', response.status, errorDetail);
			return {
				success: false,
				error: userMessage
			};
		}

		const data = await response.json();
		console.log('🗑️ 【Veo前端】删除任务成功:', data);
		return {
			success: data.success || false,
			message: data.message || '任务已删除'
		};
	} catch (error) {
		console.error('🗑️ 【Veo前端】删除任务异常:', error);
		return {
			success: false,
			error: '网络连接异常，请检查网络后重试'
		};
	}
};

/**
 * 健康检查
 */
export const getVeoHealth = async (): Promise<{ status: string; enabled: boolean } | null> => {
	try {
		const response = await fetch(`${API_BASE_URL}/health`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json'
			}
		});

		if (!response.ok) {
			return null;
		}

		const data = await response.json();
		return {
			status: data.status || 'unknown',
			enabled: data.enabled || false
		};
	} catch (error) {
		console.error('Veo健康检查异常:', error);
		return null;
	}
};

// ======================== 管理员API ========================

/**
 * 获取Veo配置（管理员）
 */
export const getVeoConfig = async (token: string): Promise<VeoConfig | null> => {
	try {
		const response = await fetch(`${API_BASE_URL}/config`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			console.error('获取Veo配置失败:', response.status, response.statusText);
			return null;
		}

		const data = await response.json();
		return data;
	} catch (error) {
		console.error('获取Veo配置异常:', error);
		return null;
	}
};

/**
 * 更新Veo配置（管理员）
 */
export const updateVeoConfig = async (token: string, config: Partial<VeoConfig>): Promise<boolean> => {
	try {
		const response = await fetch(`${API_BASE_URL}/config`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(config)
		});

		if (!response.ok) {
			console.error('更新Veo配置失败:', response.status, response.statusText);
			return false;
		}

		const data = await response.json();
		return data.success || false;
	} catch (error) {
		console.error('更新Veo配置异常:', error);
		return false;
	}
};

/**
 * 获取管理员统计信息
 */
export const getVeoAdminStats = async (token: string): Promise<any | null> => {
	try {
		const response = await fetch(`${API_BASE_URL}/admin/stats`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			console.error('获取Veo统计信息失败:', response.status, response.statusText);
			return null;
		}

		const data = await response.json();
		return data;
	} catch (error) {
		console.error('获取Veo统计信息异常:', error);
		return null;
	}
};