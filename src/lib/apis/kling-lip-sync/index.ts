import { WEBUI_API_BASE_URL } from '$lib/constants';

// ======================== 类型定义 ========================

// 可灵对口型任务状态类型
export type KlingLipSyncTaskStatus = 'submitted' | 'processing' | 'succeed' | 'failed';

// 可灵对口型模式类型
export type KlingLipSyncMode = 'text2video' | 'audio2video';

// 可灵对口型配置接口
export interface KlingLipSyncConfig {
	enabled: boolean;
	baseUrl: string;
	apiKey: string;
	defaultVoiceId: string; // 默认 genshin_vindi2（阳光少年）
	defaultVoiceLanguage: string; // 默认 zh
	defaultVoiceSpeed: number; // 默认 1.0
	creditsCost: number; // 每次对口型消耗的积分，默认 50
}

// 可灵对口型请求接口
export interface KlingLipSyncRequest {
	mode: KlingLipSyncMode; // text2video, audio2video
	videoInput: string; // video_id 或 video_url
	inputType: 'video_id' | 'video_url';

	// 文本转视频参数
	text?: string;
	voiceId?: string;
	voiceLanguage?: string;
	voiceSpeed?: number;

	// 音频转视频参数
	audioFile?: string; // base64数据
	audioUrl?: string;
	audioType?: 'file' | 'url';

	callbackUrl?: string;
}

// 可灵对口型任务接口
export interface KlingLipSyncTask {
	id: string;
	userId: string;
	status: KlingLipSyncTaskStatus;
	taskStatusMsg?: string;
	mode: KlingLipSyncMode;
	videoInput: string;
	inputType: 'video_id' | 'video_url';

	// 文本转视频参数
	text?: string;
	voiceId?: string;
	voiceLanguage?: string;
	voiceSpeed?: number;

	// 音频转视频参数
	audioFile?: string;
	audioType?: 'file' | 'url';

	// 结果
	videoUrl?: string;
	videoDuration?: string;
	failReason?: string;

	// 任务管理
	creditsCost: number;
	submitTime?: string;
	finishTime?: string;
	progress: string;
	properties?: any;
	createdAt: string;
	updatedAt: string;
}

// 可灵对口型历史记录响应
export interface KlingLipSyncHistoryResponse {
	data: KlingLipSyncTask[];
	total: number;
	page: number;
	limit: number;
}

// 用户配置响应
export interface KlingLipSyncUserConfigResponse {
	enabled: boolean;
	defaultVoiceId: string;
	defaultVoiceLanguage: string;
	defaultVoiceSpeed: number;
	creditsCost: number;
}

// 积分余额响应
export interface KlingLipSyncCreditsResponse {
	balance: number;
}

// 任务提交响应
export interface KlingLipSyncTaskSubmitResponse {
	success: boolean;
	taskId: string;
	message: string;
}

// API通用响应
export interface KlingLipSyncApiResponse {
	success: boolean;
	message: string;
	data?: any;
}

// ======================== API 函数 ========================

// 获取可灵对口型配置 (管理员)
export const getKlingLipSyncConfig = async (token: string): Promise<KlingLipSyncConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/config`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换字段名从蛇形到驼峰
			return {
				enabled: data.enabled,
				baseUrl: data.base_url || data.baseUrl,
				apiKey: data.api_key || data.apiKey,
				defaultVoiceId: data.default_voice_id || data.defaultVoiceId,
				defaultVoiceLanguage: data.default_voice_language || data.defaultVoiceLanguage,
				defaultVoiceSpeed: data.default_voice_speed || data.defaultVoiceSpeed,
				creditsCost: data.credits_cost || data.creditsCost
			};
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Kling Lip Sync config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 保存可灵对口型配置 (管理员)
export const saveKlingLipSyncConfig = async (
	token: string,
	config: Omit<KlingLipSyncConfig, 'baseUrl' | 'apiKey'> & { baseUrl?: string; apiKey?: string }
): Promise<KlingLipSyncApiResponse> => {
	let error = null;

	// 转换字段名称为后端期望的格式
	const backendConfig = {
		enabled: config.enabled,
		base_url: config.baseUrl,
		api_key: config.apiKey,
		default_voice_id: config.defaultVoiceId,
		default_voice_language: config.defaultVoiceLanguage,
		default_voice_speed: config.defaultVoiceSpeed,
		credits_cost: config.creditsCost
	};

	console.log('🎬 【可灵对口型前端】保存配置:', backendConfig);

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/config`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(backendConfig)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to save Kling Lip Sync config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 测试可灵对口型连接
export const testKlingLipSyncConnection = async (token: string): Promise<any> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/test`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to test Kling Lip Sync connection';
			console.log(err);
			return { status: 'error', message: error };
		});

	if (error) {
		return { status: 'error', message: error };
	}

	return res;
};

// 获取用户可灵对口型配置
export const getKlingLipSyncUserConfig = async (
	token: string
): Promise<KlingLipSyncUserConfigResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/config/user`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换字段名从蛇形到驼峰
			return {
				enabled: data.enabled,
				defaultVoiceId: data.default_voice_id || data.defaultVoiceId,
				defaultVoiceLanguage: data.default_voice_language || data.defaultVoiceLanguage,
				defaultVoiceSpeed: data.default_voice_speed || data.defaultVoiceSpeed,
				creditsCost: data.credits_cost || data.creditsCost
			};
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get Kling Lip Sync user config';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 提交对口型任务
export const submitKlingLipSyncTask = async (
	token: string,
	request: KlingLipSyncRequest
): Promise<KlingLipSyncTaskSubmitResponse> => {
	let error = null;

	// 转换参数名称为后端期望的格式
	const backendRequest = {
		mode: request.mode,
		video_input: request.videoInput,
		input_type: request.inputType,
		text: request.text,
		voice_id: request.voiceId,
		voice_language: request.voiceLanguage,
		voice_speed: request.voiceSpeed,
		audio_file: request.audioFile,
		audio_url: request.audioUrl,
		audio_type: request.audioType,
		callback_url: request.callbackUrl
	};

	// 移除undefined字段和空字符串
	Object.keys(backendRequest).forEach((key) => {
		const value = backendRequest[key as keyof typeof backendRequest];
		if (value === undefined || value === '' || value === null) {
			delete backendRequest[key as keyof typeof backendRequest];
		}
	});

	console.log('🎬 【可灵对口型前端】提交任务:', {
		...backendRequest,
		audio_file: backendRequest.audio_file
			? `[base64 data, ${backendRequest.audio_file.length} chars]`
			: undefined
	});

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/submit`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(backendRequest)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to submit lip sync task';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return {
		success: res.success,
		taskId: res.task_id,
		message: res.message
	};
};

// 字段名转换辅助函数
const convertTaskFields = (task: any): KlingLipSyncTask => {
	if (!task) return task;

	return {
		...task,
		userId: task.user_id || task.userId,
		taskStatusMsg: task.task_status_msg || task.taskStatusMsg,
		videoInput: task.video_input || task.videoInput,
		inputType: task.input_type || task.inputType,
		voiceId: task.voice_id || task.voiceId,
		voiceLanguage: task.voice_language || task.voiceLanguage,
		voiceSpeed: task.voice_speed || task.voiceSpeed,
		audioFile: task.audio_file || task.audioFile,
		audioType: task.audio_type || task.audioType,
		videoUrl: task.video_url || task.videoUrl,
		videoDuration: task.video_duration || task.videoDuration,
		failReason: task.fail_reason || task.failReason,
		creditsCost: task.credits_cost || task.creditsCost,
		submitTime: task.submit_time || task.submitTime,
		finishTime: task.finish_time || task.finishTime,
		createdAt: task.created_at || task.createdAt,
		updatedAt: task.updated_at || task.updatedAt
	};
};

// 获取任务状态
export const getKlingLipSyncTaskStatus = async (
	token: string,
	taskId: string
): Promise<KlingLipSyncTask> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/task/${taskId}`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换字段名从下划线到驼峰
			return convertTaskFields(data);
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get task status';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 获取用户任务历史
export const getKlingLipSyncHistory = async (
	token: string,
	page: number = 1,
	limit: number = 20
): Promise<KlingLipSyncHistoryResponse> => {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/kling-lip-sync/history?page=${page}&limit=${limit}`,
		{
			method: 'GET',
			headers: {
				Authorization: `Bearer ${token}`,
				'Content-Type': 'application/json'
			}
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();

			// 转换任务列表中每个任务的字段名
			if (data && data.data) {
				return {
					...data,
					data: data.data.map(convertTaskFields)
				};
			}
			return data;
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get task history';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 删除任务
export const deleteKlingLipSyncTask = async (token: string, taskId: string): Promise<boolean> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/task/${taskId}`, {
		method: 'DELETE',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to delete task';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res.success || false;
};

// 获取用户积分余额
export const getKlingLipSyncCredits = async (
	token: string
): Promise<KlingLipSyncCreditsResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/credits`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to get user credits';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 视频上传响应接口
export interface VideoUploadResponse {
	success: boolean;
	message: string;
	video_url?: string;
	cloud_path?: string;
}

// 音频上传响应接口
export interface AudioUploadResponse {
	success: boolean;
	message: string;
	audio_url?: string;
	cloud_path?: string;
}

// 上传视频文件到云存储
export const uploadVideoForLipSync = async (
	token: string,
	videoFile: File
): Promise<VideoUploadResponse> => {
	let error = null;

	const formData = new FormData();
	formData.append('video', videoFile);

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/upload-video`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
			// 注意：不要设置 Content-Type，让浏览器自动设置 multipart/form-data
		},
		body: formData
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to upload video';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// 上传音频文件到云存储
export const uploadAudioForLipSync = async (
	token: string,
	audioFile: File
): Promise<AudioUploadResponse> => {
	let error = null;

	const formData = new FormData();
	formData.append('audio', audioFile);

	const res = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/upload-audio`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
			// 注意：不要设置 Content-Type，让浏览器自动设置 multipart/form-data
		},
		body: formData
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err.detail ?? 'Failed to upload audio';
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// ======================== 音色数据 ========================

// 中文音色选项
export const chineseVoiceOptions = [
	{ value: 'genshin_vindi2', label: '阳光少年' },
	{ value: 'zhinen_xuesheng', label: '懂事小弟' },
	{ value: 'tiyuxi_xuedi', label: '运动少年' },
	{ value: 'ai_shatang', label: '青春少女' },
	{ value: 'genshin_klee2', label: '温柔小妹' },
	{ value: 'genshin_kirara', label: '元气少女' },
	{ value: 'ai_kaiya', label: '阳光男生' },
	{ value: 'tiexin_nanyou', label: '幽默小哥' },
	{ value: 'ai_chenjiahao_712', label: '文艺小哥' },
	{ value: 'girlfriend_1_speech02', label: '甜美邻家' },
	{ value: 'chat1_female_new-3', label: '温柔姐姐' },
	{ value: 'girlfriend_2_speech02', label: '职场女青' },
	{ value: 'cartoon-boy-07', label: '活泼男童' },
	{ value: 'cartoon-girl-01', label: '俏皮女童' },
	{ value: 'ai_huangyaoshi_712', label: '稳重老爸' },
	{ value: 'you_pingjing', label: '温柔妈妈' },
	{ value: 'ai_laoguowang_712', label: '严肃上司' },
	{ value: 'chengshu_jiejie', label: '优雅贵妇' },
	{ value: 'zhuxi_speech02', label: '慈祥爷爷' },
	{ value: 'uk_oldman3', label: '唠叨爷爷' },
	{ value: 'laopopo_speech02', label: '唠叨奶奶' },
	{ value: 'heainainai_speech02', label: '和蔼奶奶' },
	{ value: 'dongbeilaotie_speech02', label: '东北老铁' },
	{ value: 'chongqingxiaohuo_speech02', label: '重庆小伙' },
	{ value: 'chuanmeizi_speech02', label: '四川妹子' },
	{ value: 'chaoshandashu_speech02', label: '潮汕大叔' },
	{ value: 'ai_taiwan_man2_speech02', label: '台湾男生' },
	{ value: 'xianzhanggui_speech02', label: '西安掌柜' },
	{ value: 'tianjinjiejie_speech02', label: '天津姐姐' },
	{ value: 'diyinnansang_DB_CN_M_04-v2', label: '新闻播报男' },
	{ value: 'yizhipiannan-v1', label: '译制片男' },
	{ value: 'guanxiaofang-v2', label: '元气少女' },
	{ value: 'tianmeixuemei-v1', label: '撒娇女友' },
	{ value: 'daopianyansang-v1', label: '刀片烟嗓' },
	{ value: 'mengwa-v1', label: '乖巧正太' }
];

// 英文音色选项
export const englishVoiceOptions = [
	{ value: 'genshin_vindi2', label: 'Sunny' },
	{ value: 'zhinen_xuesheng', label: 'Sage' },
	{ value: 'AOT', label: 'Ace' },
	{ value: 'ai_shatang', label: 'Blossom' },
	{ value: 'genshin_klee2', label: 'Peppy' },
	{ value: 'genshin_kirara', label: 'Dove' },
	{ value: 'ai_kaiya', label: 'Shine' },
	{ value: 'oversea_male1', label: 'Anchor' },
	{ value: 'ai_chenjiahao_712', label: 'Lyric' },
	{ value: 'girlfriend_4_speech02', label: 'Melody' },
	{ value: 'chat1_female_new-3', label: 'Tender' },
	{ value: 'chat_0407_5-1', label: 'Siren' },
	{ value: 'cartoon-boy-07', label: 'Zippy' },
	{ value: 'uk_boy1', label: 'Bud' },
	{ value: 'cartoon-girl-01', label: 'Sprite' },
	{ value: 'PeppaPig_platform', label: 'Candy' },
	{ value: 'ai_huangzhong_712', label: 'Beacon' },
	{ value: 'ai_huangyaoshi_712', label: 'Rock' },
	{ value: 'ai_laoguowang_712', label: 'Titan' },
	{ value: 'chengshu_jiejie', label: 'Grace' },
	{ value: 'you_pingjing', label: 'Helen' },
	{ value: 'calm_story1', label: 'Lore' },
	{ value: 'uk_man2', label: 'Crag' },
	{ value: 'laopopo_speech02', label: 'Prattle' },
	{ value: 'heainainai_speech02', label: 'Hearth' },
	{ value: 'reader_en_m-v1', label: 'The Reader' },
	{ value: 'commercial_lady_en_f-v1', label: 'Commercial Lady' }
];

// 根据语言获取音色选项
export const getVoiceOptions = (language: string) => {
	return language === 'zh' ? chineseVoiceOptions : englishVoiceOptions;
};

// 根据语言和音色ID获取音色名称
export const getVoiceName = (language: string, voiceId: string): string => {
	const options = getVoiceOptions(language);
	const option = options.find((opt) => opt.value === voiceId);
	return option?.label || voiceId;
};
