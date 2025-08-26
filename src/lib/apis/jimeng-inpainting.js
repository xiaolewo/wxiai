import { WEBUI_API_BASE_URL } from '$lib/constants';

// API基础路径
export const JIMENG_INPAINTING_API_BASE_URL = '/jimeng-inpainting';

// ======================== 管理员接口 ========================

/**
 * 获取即梦涂抹消除配置（管理员）
 */
export async function getJimengInpaintingConfig(token) {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng-inpainting/config`, {
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
}

/**
 * 保存即梦涂抹消除配置（管理员）
 */
export async function saveJimengInpaintingConfig(token, config) {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng-inpainting/config`, {
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
			console.error(err);
			error = err.detail ?? err.message ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

/**
 * 测试即梦涂抹消除连接（管理员）
 */
export async function testJimengInpaintingConnection(token) {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng-inpainting/test`, {
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
}

// ======================== 用户接口 ========================

/**
 * 获取用户可见的即梦涂抹消除配置
 */
export async function getJimengInpaintingUserConfig(token) {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng-inpainting/config/user`, {
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
}

/**
 * 提交涂抹消除任务
 */
export async function submitJimengInpaintingTask(token, request) {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng-inpainting/submit`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(request)
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
}

/**
 * 获取任务状态
 */
export async function getJimengInpaintingTaskStatus(token, taskId) {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng-inpainting/task/${taskId}`, {
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
}

/**
 * 获取用户任务历史
 */
export async function getJimengInpaintingHistory(token, page = 1, limit = 20) {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/jimeng-inpainting/history?page=${page}&limit=${limit}`,
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
			console.error(err);
			error = err.detail ?? err.message ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

/**
 * 删除任务
 */
export async function deleteJimengInpaintingTask(token, taskId) {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng-inpainting/task/${taskId}`, {
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
			console.error(err);
			error = err.detail ?? err.message ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res.success || false;
}

/**
 * 获取用户积分余额
 */
export async function getJimengInpaintingCredits(token) {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng-inpainting/credits`, {
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
}

/**
 * 上传图片文件到云存储
 */
export async function uploadImageForInpainting(token, file) {
	let error = null;

	const formData = new FormData();
	formData.append('image', file);

	const res = await fetch(`${WEBUI_API_BASE_URL}/jimeng-inpainting/upload-image`, {
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
			console.error(err);
			error = err.detail ?? err.message ?? 'Server connection failed';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

// ======================== 类型定义 ========================

/**
 * @typedef {Object} JimengInpaintingRequest
 * @property {string} original_image_url - 原始图片URL
 * @property {string} mask_image_url - 遮罩图片URL
 * @property {string} [mode="remove"] - 功能模式: 'remove'(涂抹消除) 或 'edit'(涂抹编辑)
 * @property {string} [custom_prompt] - 涂抹编辑模式的提示词（仅在mode="edit"时使用）
 * @property {number} [steps=30] - 采样步数
 * @property {number} [strength=0.8] - 消除强度
 * @property {number} [scale=7.0] - 文本描述程度
 * @property {number} [seed=0] - 随机种子
 * @property {number} [dilate_size=15] - 遮罩膨胀半径
 * @property {string} [quality="M"] - 质量参数 H/M/L
 * @property {boolean} [return_url=true] - 是否返回图片链接
 */

/**
 * @typedef {Object} JimengInpaintingTask
 * @property {string} id - 任务ID
 * @property {string} user_id - 用户ID
 * @property {string} status - 任务状态: submitted/processing/succeed/failed
 * @property {string} progress - 进度百分比
 * @property {string} mode - 功能模式: 'remove'(涂抹消除) 或 'edit'(涂抹编辑)
 * @property {string} [custom_prompt] - 涂抹编辑模式的提示词
 * @property {string} original_image_url - 原始图片URL
 * @property {string} mask_image_url - 遮罩图片URL
 * @property {number} steps - 采样步数
 * @property {number} strength - 消除强度
 * @property {number} scale - 文本描述程度
 * @property {number} seed - 随机种子
 * @property {number} dilate_size - 遮罩膨胀半径
 * @property {string} quality - 质量参数
 * @property {string} [result_image_url] - 结果图片URL
 * @property {string} [cloud_image_url] - 云存储图片URL
 * @property {number} credits_cost - 积分消耗
 * @property {string} [fail_reason] - 失败原因
 * @property {string} created_at - 创建时间
 * @property {string} updated_at - 更新时间
 * @property {string} [finish_time] - 完成时间
 */
