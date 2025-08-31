/**
 * 谷歌生图管理员API
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

/**
 * 获取谷歌生图管理员配置
 */
export const getGoogleImagesAdminConfig = async (token: string): Promise<any> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/config`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('获取谷歌生图管理员配置失败:', error);
		throw error;
	}
};

/**
 * 保存谷歌生图管理员配置
 */
export const saveGoogleImagesAdminConfig = async (token: string, config: any): Promise<any> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/config`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(config)
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('保存谷歌生图管理员配置失败:', error);
		throw error;
	}
};

/**
 * 获取谷歌生图系统统计信息
 */
export const getGoogleImagesAdminStats = async (token: string): Promise<any> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/admin/stats`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('获取谷歌生图系统统计失败:', error);
		throw error;
	}
};

/**
 * 管理员给用户充值积分
 */
export const addGoogleImagesCreditsToUser = async (
	token: string,
	targetUserId: string,
	credits: number,
	reason: string = '管理员充值'
): Promise<any> => {
	try {
		const response = await fetch(`${WEBUI_API_BASE_URL}/google_images/admin/credits/add`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify({
				target_user_id: targetUserId,
				credits,
				reason
			})
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
		}

		return await response.json();
	} catch (error) {
		console.error('管理员充值谷歌生图积分失败:', error);
		throw error;
	}
};
