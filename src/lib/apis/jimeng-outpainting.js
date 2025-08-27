const JIMENG_OUTPAINTING_API_BASE_URL = '/api/v1/jimeng-outpainting';

// ======================== 管理员接口 ========================

/**
 * 获取即梦智能扩图配置（管理员）
 */
export const getJimengOutpaintingConfig = async (token) => {
	let error = null;

	const res = await fetch(`${JIMENG_OUTPAINTING_API_BASE_URL}/config`, {
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
			console.error(err);
			error = err.detail ?? err.message ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 保存即梦智能扩图配置（管理员）
 */
export const saveJimengOutpaintingConfig = async (token, config) => {
	let error = null;

	const res = await fetch(`${JIMENG_OUTPAINTING_API_BASE_URL}/config`, {
		method: 'PUT',
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
			console.error(err);
			error = err.detail ?? err.message ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 测试即梦智能扩图连接（管理员）
 */
export const testJimengOutpaintingConnection = async (token) => {
	let error = null;

	const res = await fetch(`${JIMENG_OUTPAINTING_API_BASE_URL}/config/test`, {
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
			console.error(err);
			error = err.detail ?? err.message ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// ======================== 用户接口 ========================

/**
 * 获取用户配置
 */
export const getJimengOutpaintingUserConfig = async (token) => {
	let error = null;

	const res = await fetch(`${JIMENG_OUTPAINTING_API_BASE_URL}/user-config`, {
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
			error = err.detail ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 上传图片
 */
export const uploadImageForOutpainting = async (token, file) => {
	let error = null;

	const formData = new FormData();
	formData.append('file', file);

	const res = await fetch(`${JIMENG_OUTPAINTING_API_BASE_URL}/upload-image`, {
		method: 'POST',
		headers: {
			authorization: `Bearer ${token}`
		},
		body: formData
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Upload failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 提交智能扩图任务
 */
export const submitJimengOutpaintingTask = async (token, requestData) => {
	let error = null;

	const res = await fetch(`${JIMENG_OUTPAINTING_API_BASE_URL}/tasks`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(requestData)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Task submission failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 获取任务状态
 */
export const getJimengOutpaintingTaskStatus = async (token, taskId) => {
	let error = null;

	const res = await fetch(`${JIMENG_OUTPAINTING_API_BASE_URL}/tasks/${taskId}`, {
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
			error = err.detail ?? 'Failed to get task status';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 获取历史记录
 */
export const getJimengOutpaintingHistory = async (token, page = 1, limit = 20) => {
	let error = null;

	const res = await fetch(
		`${JIMENG_OUTPAINTING_API_BASE_URL}/history?page=${page}&limit=${limit}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${token}`
			}
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get history';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * 删除任务
 */
export const deleteJimengOutpaintingTask = async (token, taskId) => {
	let error = null;

	const res = await fetch(`${JIMENG_OUTPAINTING_API_BASE_URL}/tasks/${taskId}`, {
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
			error = err.detail ?? 'Failed to delete task';
			return null;
		});

	if (error) {
		throw error;
	}

	return res?.success ?? false;
};

/**
 * 获取积分信息
 */
export const getJimengOutpaintingCredits = async (token) => {
	let error = null;

	const res = await fetch(`${JIMENG_OUTPAINTING_API_BASE_URL}/credits`, {
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
			error = err.detail ?? 'Failed to get credits';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// TypeScript 类型定义
/**
 * @typedef {Object} JimengOutpaintingRequest
 * @property {string} original_image_url - 原始图片URL
 * @property {string} [mask_image_url] - 遮罩图片URL (画布模式使用)
 * @property {string} expansion_mode - 扩展模式: equal/aspect/custom/canvas
 * @property {string} [custom_prompt] - 自定义提示词
 * @property {number} [top] - 向上扩展比例
 * @property {number} [bottom] - 向下扩展比例
 * @property {number} [left] - 向左扩展比例
 * @property {number} [right] - 向右扩展比例
 * @property {number} [steps] - 采样步数
 * @property {number} [strength] - 扩展强度
 * @property {number} [scale] - 控制程度
 * @property {number} [seed] - 随机种子
 * @property {string} [quality] - 质量等级
 * @property {number} [max_width] - 最大宽度
 * @property {number} [max_height] - 最大高度
 * @property {boolean} [return_url] - 返回图片URL
 */

/**
 * @typedef {Object} JimengOutpaintingTask
 * @property {string} id - 任务ID
 * @property {string} user_id - 用户ID
 * @property {string} original_image_url - 原始图片URL
 * @property {string} [mask_image_url] - 遮罩图片URL
 * @property {string} expansion_mode - 扩展模式
 * @property {string} [custom_prompt] - 自定义提示词
 * @property {number} [top] - 向上扩展比例
 * @property {number} [bottom] - 向下扩展比例
 * @property {number} [left] - 向左扩展比例
 * @property {number} [right] - 向右扩展比例
 * @property {number} steps - 采样步数
 * @property {number} strength - 扩展强度
 * @property {number} scale - 控制程度
 * @property {number} seed - 随机种子
 * @property {string} quality - 质量等级
 * @property {number} max_width - 最大宽度
 * @property {number} max_height - 最大高度
 * @property {string} status - 任务状态
 * @property {string} [progress] - 进度
 * @property {string} [fail_reason] - 失败原因
 * @property {string} [result_image_url] - 结果图片URL
 * @property {string} [cloud_image_url] - 云端图片URL
 * @property {string} [request_id] - 请求ID
 * @property {number} credits_cost - 积分消耗
 * @property {string} created_at - 创建时间
 * @property {string} [updated_at] - 更新时间
 */
