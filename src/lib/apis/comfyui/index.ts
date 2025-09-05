import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface ComfyUIConfig {
	id?: string;
	access_key: string;
	secret_key: string;
	base_url: string;
	enabled: boolean;
	timeout: number;
	max_concurrent_tasks: number;
	created_at?: string;
	updated_at?: string;
}

export interface ComfyUIWorkflow {
	id: string;
	template_uuid: string;
	workflow_uuid: string;
	name: string;
	description?: string;
	category?: string;
	preview_image?: string;
	parameter_schema: any;
	default_params?: any;
	base_credits: number;
	complexity_multiplier: number;
	enabled: boolean;
	is_public: boolean;
	sort_order: number;
	created_at?: string;
	updated_at?: string;
}

export interface ComfyUITask {
	id: string;
	user_id: string;
	workflow_id: string;
	generate_uuid?: string;
	input_params: any;
	template_uuid: string;
	workflow_uuid: string;
	status: string;
	generate_status?: number;
	percent_completed: number;
	output_images?: any[];
	output_videos?: any[];
	cloud_images?: string[];
	cloud_videos?: string[];
	credits_cost?: number;
	generation_time?: number;
	error_message?: string;
	retry_count: number;
	created_at?: string;
	updated_at?: string;
	completed_at?: string;
}

export interface ComfyUICredits {
	user_id: string;
	credits_balance: number;
	total_used?: number;
	created_at?: number;
	updated_at?: number;
}

// 获取ComfyUI管理员配置
export const getComfyUIConfig = async (token: string): Promise<ComfyUIConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/admin/config`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 保存ComfyUI管理员配置
export const saveComfyUIConfig = async (
	token: string,
	config: Partial<ComfyUIConfig>
): Promise<ComfyUIConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/admin/config`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(config)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取所有工作流（管理员）
export const getComfyUIWorkflows = async (token: string): Promise<ComfyUIWorkflow[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/admin/workflows`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 创建工作流
export const createComfyUIWorkflow = async (
	token: string,
	workflow: Partial<ComfyUIWorkflow>
): Promise<ComfyUIWorkflow> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/admin/workflows`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(workflow)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 更新工作流
export const updateComfyUIWorkflow = async (
	token: string,
	workflowId: string,
	workflow: Partial<ComfyUIWorkflow>
): Promise<ComfyUIWorkflow> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/admin/workflows/${workflowId}`, {
		method: 'PUT',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(workflow)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 删除工作流
export const deleteComfyUIWorkflow = async (token: string, workflowId: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/admin/workflows/${workflowId}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 导入示例工作流
export const importSampleWorkflows = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/admin/workflows/import-samples`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取公开工作流
export const getPublicComfyUIWorkflows = async (category?: string): Promise<ComfyUIWorkflow[]> => {
	let error = null;
	let url = `${WEBUI_API_BASE_URL}/comfyui/workflows/public`;
	if (category) {
		url += `?category=${encodeURIComponent(category)}`;
	}

	const res = await fetch(url, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取工作流参数结构
export const getComfyUIWorkflowSchema = async (workflowId: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/workflows/${workflowId}/schema`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 提交ComfyUI任务
export const submitComfyUITask = async (
	token: string,
	workflowId: string,
	inputParams: any
): Promise<ComfyUITask> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/tasks`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			workflow_id: workflowId,
			input_params: inputParams
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取任务状态
export const getComfyUITaskStatus = async (token: string, taskId: string): Promise<ComfyUITask> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/tasks/${taskId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取用户任务历史
export const getUserComfyUITasks = async (
	token: string,
	page = 1,
	limit = 20,
	status?: string
): Promise<ComfyUITask[]> => {
	let error = null;
	let url = `${WEBUI_API_BASE_URL}/comfyui/tasks?page=${page}&limit=${limit}`;
	if (status) {
		url += `&status=${encodeURIComponent(status)}`;
	}

	const res = await fetch(url, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取用户积分
export const getComfyUICredits = async (token: string): Promise<ComfyUICredits> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/credits`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 历史记录相关类型
export interface ComfyUIHistoryItem {
	id: string;
	workflow_id: string;
	workflow_name: string;
	status: string;
	credits_cost: number;
	generation_time?: number;
	created_at: string;
	completed_at?: string;
	results: {
		images: Array<{
			cloud_url: string;
			original_url: string;
			node_id?: string;
			output_name?: string;
		}>;
		videos: Array<{
			cloud_url: string;
			cover_url?: string;
			original_url: string;
			node_id?: string;
			output_name?: string;
		}>;
	};
	input_summary: string;
}

export interface ComfyUIHistoryResponse {
	history: ComfyUIHistoryItem[];
	page: number;
	limit: number;
	total: number;
}

// 获取用户历史记录
export const getComfyUIHistory = async (
	token: string,
	page: number = 1,
	limit: number = 20
): Promise<ComfyUIHistoryResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/history?page=${page}&limit=${limit}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 管理员给用户增加积分
export const addUserComfyUICredits = async (
	token: string,
	userId: string,
	amount: number
): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/admin/credits/add`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			user_id: userId,
			amount: amount
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取ComfyUI服务状态
export const getComfyUIStatus = async (): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/comfyui/status`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
