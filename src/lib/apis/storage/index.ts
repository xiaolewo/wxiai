import { WEBUI_API_BASE_URL } from '$lib/constants';

// 云存储配置接口
export interface CloudStorageConfig {
	id?: string;
	provider: string;
	enabled: boolean;
	secretId: string;
	secretKey: string;
	region: string;
	bucket: string;
	domain?: string;
	autoUpload: boolean;
	allowedTypes: string[];
	maxFileSize: number;
	basePath: string;
	imagePath: string;
	videoPath: string;
	createdAt?: string;
	updatedAt?: string;
}

// 生成文件记录接口
export interface GeneratedFile {
	id: string;
	filename: string;
	fileType: string;
	fileSize: number;
	mimeType: string;
	cloudUrl?: string;
	cloudPath?: string;
	sourceType: string;
	sourceTaskId?: string;
	status: 'pending' | 'uploaded' | 'failed';
	metadata?: Record<string, any>;
	createdAt: string;
	errorMessage?: string;
}

// 存储统计信息接口
export interface StorageStats {
	totalFiles: number;
	uploadedFiles: number;
	failedFiles: number;
	pendingFiles: number;
	typeDistribution: Record<string, number>;
	sourceDistribution: Record<string, number>;
}

// 获取云存储配置 (管理员专用)
export const getStorageConfig = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/storage/config`, {
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
					id: data.id,
					provider: data.provider || 'tencent-cos',
					enabled: data.enabled || false,
					secretId: data.secret_id || '',
					secretKey: data.secret_key || '',
					region: data.region || 'ap-beijing',
					bucket: data.bucket || '',
					domain: data.domain || '',
					autoUpload: data.auto_upload !== undefined ? data.auto_upload : true,
					allowedTypes: data.allowed_types || ['image/*', 'video/*'],
					maxFileSize: data.max_file_size || 104857600,
					basePath: data.base_path || 'generated/',
					imagePath: data.image_path || 'images/',
					videoPath: data.video_path || 'videos/',
					createdAt: data.created_at,
					updatedAt: data.updated_at
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

// 保存云存储配置 (管理员专用)
export const saveStorageConfig = async (
	token: string = '',
	config: Partial<CloudStorageConfig>
) => {
	let error = null;

	// 转换前端驼峰命名到后端下划线命名
	const backendConfig = {
		provider: config.provider,
		enabled: config.enabled,
		secret_id: config.secretId,
		secret_key: config.secretKey,
		region: config.region,
		bucket: config.bucket,
		domain: config.domain,
		auto_upload: config.autoUpload,
		allowed_types: config.allowedTypes,
		max_file_size: config.maxFileSize,
		base_path: config.basePath,
		image_path: config.imagePath,
		video_path: config.videoPath
	};

	const res = await fetch(`${WEBUI_API_BASE_URL}/storage/config`, {
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

// 测试云存储连接 (管理员专用)
export const testStorageConnection = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/storage/test`, {
		method: 'POST',
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

// 获取生成文件列表 (用户)
export const getGeneratedFiles = async (
	token: string = '',
	page: number = 1,
	limit: number = 20,
	fileType?: string,
	sourceType?: string,
	status?: string
) => {
	let error = null;

	const params = new URLSearchParams({
		page: page.toString(),
		limit: limit.toString()
	});

	if (fileType) params.append('file_type', fileType);
	if (sourceType) params.append('source_type', sourceType);
	if (status) params.append('status', status);

	const res = await fetch(`${WEBUI_API_BASE_URL}/storage/files/generated?${params.toString()}`, {
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

// 删除生成的文件 (用户)
export const deleteGeneratedFile = async (token: string = '', fileId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/storage/files/generated/${fileId}`, {
		method: 'DELETE',
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

// 批量迁移外部URL到云存储 (管理员专用)
export const migrateExternalFiles = async (
	token: string = '',
	sourceType?: string,
	batchSize: number = 100
) => {
	let error = null;

	const params = new URLSearchParams({
		batch_size: batchSize.toString()
	});

	if (sourceType) params.append('source_type', sourceType);

	const res = await fetch(`${WEBUI_API_BASE_URL}/storage/files/migrate?${params.toString()}`, {
		method: 'POST',
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

// 获取存储统计信息 (管理员专用)
export const getStorageStats = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/storage/stats`, {
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

	return res?.stats || null;
};

// 内部文件上传接口 (供其他模块调用)
export const uploadFile = async (
	token: string = '',
	data: {
		userId: string;
		fileUrl?: string;
		fileData?: ArrayBuffer;
		filename: string;
		fileType: 'image' | 'video';
		sourceType: string;
		sourceTaskId?: string;
		metadata?: Record<string, any>;
	}
) => {
	let error = null;

	// 如果有文件数据，需要转换为 base64
	let fileData = null;
	if (data.fileData) {
		const uint8Array = new Uint8Array(data.fileData);
		const binary = uint8Array.reduce((acc, byte) => acc + String.fromCharCode(byte), '');
		fileData = btoa(binary);
	}

	const requestData = {
		user_id: data.userId,
		file_url: data.fileUrl,
		file_data: fileData,
		filename: data.filename,
		file_type: data.fileType,
		source_type: data.sourceType,
		source_task_id: data.sourceTaskId,
		metadata: data.metadata
	};

	const res = await fetch(`${WEBUI_API_BASE_URL}/storage/internal/upload`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(requestData)
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

// 内部URL迁移接口 (供其他模块调用)
export const migrateUrl = async (
	token: string = '',
	data: {
		externalUrl: string;
		userId: string;
		sourceType: string;
		sourceTaskId?: string;
		filename?: string;
	}
) => {
	let error = null;

	const requestData = {
		external_url: data.externalUrl,
		user_id: data.userId,
		source_type: data.sourceType,
		source_task_id: data.sourceTaskId,
		filename: data.filename
	};

	const res = await fetch(`${WEBUI_API_BASE_URL}/storage/internal/migrate-url`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(requestData)
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
