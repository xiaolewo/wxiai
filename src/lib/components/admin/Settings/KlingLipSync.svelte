<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import Kling Lip Sync API functions
	import {
		type KlingLipSyncConfig,
		getKlingLipSyncConfig,
		saveKlingLipSyncConfig,
		testKlingLipSyncConnection,
		chineseVoiceOptions,
		englishVoiceOptions
	} from '$lib/apis/kling-lip-sync';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	// 可灵对口型配置
	let klingLipSyncConfig = {
		enabled: false,
		baseUrl: 'https://api.kling.com',
		apiKey: '',
		defaultVoiceId: 'genshin_vindi2',
		defaultVoiceLanguage: 'zh',
		defaultVoiceSpeed: 1.0,
		creditsCost: 50
	};

	// 语言选项
	const languageOptions = [
		{ value: 'zh', label: '中文' },
		{ value: 'en', label: 'English' }
	];

	// 根据语言获取音色选项
	$: currentVoiceOptions =
		klingLipSyncConfig.defaultVoiceLanguage === 'zh' ? chineseVoiceOptions : englishVoiceOptions;

	// 当语言切换时，自动切换默认音色
	$: if (
		klingLipSyncConfig.defaultVoiceLanguage === 'zh' &&
		!chineseVoiceOptions.find((v) => v.value === klingLipSyncConfig.defaultVoiceId)
	) {
		klingLipSyncConfig.defaultVoiceId = 'genshin_vindi2'; // 默认中文音色：阳光少年
	} else if (
		klingLipSyncConfig.defaultVoiceLanguage === 'en' &&
		!englishVoiceOptions.find((v) => v.value === klingLipSyncConfig.defaultVoiceId)
	) {
		klingLipSyncConfig.defaultVoiceId = 'genshin_vindi2'; // 默认英文音色：Sunny
	}

	onMount(async () => {
		await loadKlingLipSyncConfig();
	});

	const loadKlingLipSyncConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getKlingLipSyncConfig($user.token);
			if (config) {
				klingLipSyncConfig = { ...klingLipSyncConfig, ...config };
			}
		} catch (error) {
			console.error('Failed to load Kling Lip Sync config:', error);
			toast.error('加载可灵对口型配置失败');
		} finally {
			loading = false;
		}
	};

	const saveKlingLipSyncConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveKlingLipSyncConfig($user.token, klingLipSyncConfig);
			toast.success('可灵对口型配置已保存');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save Kling Lip Sync config:', error);
			toast.error('保存可灵对口型配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!klingLipSyncConfig.baseUrl || !klingLipSyncConfig.apiKey) {
			toast.error('请先配置 API URL 和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const result = await testKlingLipSyncConnection($user.token);
			if (result.status === 'success') {
				toast.success('可灵对口型连接测试成功');
			} else {
				toast.error(`连接测试失败: ${result.message}`);
			}
		} catch (error) {
			console.error('Connection test failed:', error);
			toast.error('连接测试失败');
		} finally {
			loading = false;
		}
	};
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={() => {
		saveKlingLipSyncConfigData();
	}}
>
	<div class="space-y-3 overflow-y-scroll scrollbar-hidden h-full">
		<div>
			<div class="mb-2 flex w-full justify-between">
				<div class="flex items-center space-x-2">
					<div class="font-medium text-sm">🎭 可灵对口型服务</div>
					<Tooltip content="可灵AI的视频对口型服务，支持文本转语音和音频驱动的对口型生成">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="w-4 h-4"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
							/>
						</svg>
					</Tooltip>
				</div>
				<Switch bind:state={klingLipSyncConfig.enabled} />
			</div>
		</div>

		{#if klingLipSyncConfig.enabled}
			<!-- API 配置 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>API 配置</div>
				</div>

				<div>
					<div class="flex w-full">
						<div class="flex-1 mr-2">
							<div class="mb-1 text-xs text-gray-500">API URL</div>
							<div class="flex w-full">
								<div class="flex-1">
									<input
										class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
										placeholder="https://api.kling.com"
										bind:value={klingLipSyncConfig.baseUrl}
										autocomplete="off"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div>
					<div class="mb-1 text-xs text-gray-500">API 密钥</div>
					<SensitiveInput placeholder="输入可灵API密钥..." bind:value={klingLipSyncConfig.apiKey} />
				</div>

				<div class="flex justify-end">
					<button
						class="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition"
						type="button"
						on:click={testConnection}
						disabled={loading || !klingLipSyncConfig.baseUrl || !klingLipSyncConfig.apiKey}
					>
						{loading ? '测试中...' : '测试连接'}
					</button>
				</div>
			</div>

			<!-- 默认设置 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>默认设置</div>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<div class="mb-1 text-xs text-gray-500">默认语言</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={klingLipSyncConfig.defaultVoiceLanguage}
						>
							{#each languageOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">默认音色</div>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							bind:value={klingLipSyncConfig.defaultVoiceId}
						>
							{#each currentVoiceOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							默认语速
							<Tooltip content="语音播放速度，范围 0.8 - 2.0">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3 inline ml-1"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l-.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="0.8"
							max="2.0"
							step="0.1"
							bind:value={klingLipSyncConfig.defaultVoiceSpeed}
						/>
					</div>

					<div>
						<div class="mb-1 text-xs text-gray-500">
							积分消耗
							<Tooltip content="每次对口型生成消耗的积分数量">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3 inline ml-1"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l-.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
									/>
								</svg>
							</Tooltip>
						</div>
						<input
							class="w-full rounded-lg py-2 px-4 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
							type="number"
							min="1"
							bind:value={klingLipSyncConfig.creditsCost}
						/>
					</div>
				</div>
			</div>

			<!-- 音色选项说明 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>音色说明</div>
				</div>

				<div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<div class="text-xs text-gray-600 dark:text-gray-400 space-y-2">
						<div class="font-medium">可用音色数量：</div>
						<div>• 中文音色：35 种</div>
						<div>• 英文音色：27 种</div>
						<div class="mt-2">
							<div class="font-medium">使用说明：</div>
							<div>• 用户界面会根据所选语言自动切换显示对应的音色选项</div>
							<div>• 用户端只显示音色名称，不显示内部ID</div>
							<div>• 语言切换时会自动选择相应语言的默认音色</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 功能特性 -->
			<div class="space-y-3">
				<div class="flex justify-between items-center text-xs font-medium text-gray-500">
					<div>功能特性</div>
				</div>

				<div class="grid grid-cols-1 gap-3">
					<div class="p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							支持的生成模式
						</div>
						<div class="space-y-1 text-xs text-gray-600 dark:text-gray-400">
							<div>• <strong>文本转视频对口型：</strong>输入文本 + 音色 + 视频，生成对口型视频</div>
							<div>
								• <strong>音频驱动对口型：</strong>上传音频文件或提供音频URL + 视频，生成对口型视频
							</div>
						</div>
					</div>

					<div class="p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							视频输入支持
						</div>
						<div class="space-y-1 text-xs text-gray-600 dark:text-gray-400">
							<div>• <strong>视频URL：</strong>支持 .mp4/.mov 格式，≤100MB，2-60秒</div>
							<div>• <strong>视频ID：</strong>支持可灵生成的视频ID</div>
						</div>
					</div>

					<div class="p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							音频输入支持（音频模式）
						</div>
						<div class="space-y-1 text-xs text-gray-600 dark:text-gray-400">
							<div>• <strong>文件上传：</strong>支持 MP3、WAV、M4A、AAC 格式，≤5MB</div>
							<div>• <strong>音频URL：</strong>支持音频文件的直接下载链接</div>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3">
		<button
			class="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-gray-100 transition rounded-lg text-sm"
			type="submit"
			disabled={loading}
		>
			{loading ? '保存中...' : '保存'}
		</button>
	</div>
</form>
