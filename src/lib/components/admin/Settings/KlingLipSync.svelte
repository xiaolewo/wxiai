<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let testing = false;

	// 可灵对口型配置
	let klingLipSyncConfig = {
		enabled: false,
		baseUrl: 'https://api.klingai.com',
		apiKey: '',
		creditsPerTask: 50,
		maxConcurrentTasks: 3,
		taskTimeout: 300000, // 5分钟
		defaultMode: 'text2video',
		defaultVoiceId: 'girlfriend_1_speech02',
		defaultVoiceLanguage: 'zh'
	};

	// 音色和语言数据
	let availableVoices = [];
	let availableLanguages = [];
	let filteredVoices = [];

	// 根据选择的语言过滤音色
	$: {
		if (klingLipSyncConfig.defaultVoiceLanguage && availableVoices.length > 0) {
			filteredVoices = availableVoices.filter(
				(voice) => voice.language === klingLipSyncConfig.defaultVoiceLanguage
			);
			// 如果当前选中的音色不在过滤后的列表中，选择首个可用音色
			if (
				filteredVoices.length > 0 &&
				!filteredVoices.find((v) => v.id === klingLipSyncConfig.defaultVoiceId)
			) {
				klingLipSyncConfig.defaultVoiceId = filteredVoices[0].id;
			}
		} else {
			filteredVoices = [];
		}
	}

	onMount(async () => {
		await loadConfig();
		await loadVoicesAndLanguages();
	});

	const loadConfig = async () => {
		try {
			loading = true;
			const response = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/config`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${localStorage.getItem('token')}`
				}
			});

			if (response.ok) {
				const data = await response.json();
				klingLipSyncConfig = {
					enabled: data.enabled || false,
					baseUrl: data.base_url || 'https://api.klingai.com',
					apiKey: data.api_key || '',
					creditsPerTask: data.credits_per_task || 50,
					maxConcurrentTasks: data.max_concurrent_tasks || 3,
					taskTimeout: data.task_timeout || 300000,
					defaultMode: data.default_mode || 'text2video',
					defaultVoiceId: data.default_voice_id || 'girlfriend_1_speech02',
					defaultVoiceLanguage: data.default_voice_language || 'zh'
				};
			} else {
				toast.error('加载配置失败');
			}
		} catch (error) {
			console.error('Load config error:', error);
			toast.error('加载配置失败');
		} finally {
			loading = false;
		}
	};

	const saveConfig = async () => {
		try {
			loading = true;
			const requestData = {
				enabled: klingLipSyncConfig.enabled,
				base_url: klingLipSyncConfig.baseUrl,
				api_key: klingLipSyncConfig.apiKey,
				credits_per_task: klingLipSyncConfig.creditsPerTask,
				max_concurrent_tasks: klingLipSyncConfig.maxConcurrentTasks,
				task_timeout: klingLipSyncConfig.taskTimeout,
				default_mode: klingLipSyncConfig.defaultMode,
				default_voice_id: klingLipSyncConfig.defaultVoiceId,
				default_voice_language: klingLipSyncConfig.defaultVoiceLanguage
			};

			const response = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/config`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${localStorage.getItem('token')}`
				},
				body: JSON.stringify(requestData)
			});

			if (response.ok) {
				toast.success('配置保存成功');
			} else {
				const errorData = await response.json();
				toast.error(errorData.detail || '保存配置失败');
			}
		} catch (error) {
			console.error('Save config error:', error);
			toast.error('保存配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!klingLipSyncConfig.apiKey.trim()) {
			toast.error('请先填写API密钥');
			return;
		}

		try {
			testing = true;
			const response = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/test-connection`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${localStorage.getItem('token')}`
				}
			});

			if (response.ok) {
				const result = await response.json();
				if (result.success) {
					toast.success('连接测试成功');
				} else {
					toast.error(result.message || '连接测试失败');
				}
			} else {
				toast.error('连接测试失败');
			}
		} catch (error) {
			console.error('Test connection error:', error);
			toast.error('连接测试失败');
		} finally {
			testing = false;
		}
	};

	const loadVoicesAndLanguages = async () => {
		try {
			// 加载语言列表
			const languageResponse = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/languages`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${localStorage.getItem('token')}`
				}
			});

			if (languageResponse.ok) {
				const languageData = await languageResponse.json();
				availableLanguages = languageData.languages || [];
			}

			// 加载音色列表
			const voiceResponse = await fetch(`${WEBUI_API_BASE_URL}/kling-lip-sync/voices`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${localStorage.getItem('token')}`
				}
			});

			if (voiceResponse.ok) {
				const voiceData = await voiceResponse.json();
				availableVoices = voiceData.voices || [];
			}
		} catch (error) {
			console.error('Load voices and languages error:', error);
		}
	};
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={saveConfig}
>
	<div class=" space-y-3">
		<div>
			<div class=" mb-1 text-sm font-medium">可灵对口型</div>
			<div class="text-xs text-gray-400">
				配置可灵AI对口型功能，让视频中的人物与文本内容同步对口型
			</div>
		</div>

		<hr class=" border-gray-700" />

		<!-- 启用开关 -->
		<div>
			<div class=" py-0.5 flex w-full justify-between">
				<div class=" self-center text-xs font-medium">启用可灵对口型</div>
				<Switch bind:state={klingLipSyncConfig.enabled} />
			</div>
		</div>

		{#if klingLipSyncConfig.enabled}
			<!-- API配置 -->
			<div class="space-y-3">
				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium">API基础URL</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="https://api.klingai.com"
								bind:value={klingLipSyncConfig.baseUrl}
								required
							/>
						</div>
					</div>
				</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium">API密钥</div>
						<button
							type="button"
							class="text-xs font-medium text-blue-600 hover:text-blue-500"
							on:click={testConnection}
							disabled={testing || !klingLipSyncConfig.apiKey.trim()}
						>
							{#if testing}
								测试中...
							{:else}
								测试连接
							{/if}
						</button>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<SensitiveInput
								placeholder="请输入可灵API密钥"
								bind:value={klingLipSyncConfig.apiKey}
								required
							/>
						</div>
					</div>
				</div>
			</div>

			<hr class=" border-gray-700" />

			<!-- 积分配置 -->
			<div>
				<div class="flex w-full justify-between mb-2">
					<div class="self-center text-xs font-medium flex items-center space-x-1">
						<span>每个任务消耗积分</span>
						<Tooltip content="每次对口型生成任务消耗的积分数量">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="w-3 h-3"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
								/>
							</svg>
						</Tooltip>
					</div>
				</div>
				<div class="flex w-full">
					<div class="flex-1">
						<input
							class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
							placeholder="50"
							type="number"
							min="1"
							max="1000"
							bind:value={klingLipSyncConfig.creditsPerTask}
							required
						/>
					</div>
				</div>
			</div>

			<hr class=" border-gray-700" />

			<!-- 默认参数配置 -->
			<div class="space-y-3">
				<div class="text-xs font-medium text-gray-600 dark:text-gray-400">默认参数配置</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium">默认音色</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<select
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								bind:value={klingLipSyncConfig.defaultVoiceId}
							>
								{#each filteredVoices as voice}
									<option value={voice.id}>{voice.name}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium">默认语言</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<select
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								bind:value={klingLipSyncConfig.defaultVoiceLanguage}
							>
								{#each availableLanguages as language}
									<option value={language.code}>{language.name}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>
			</div>

			<hr class=" border-gray-700" />

			<!-- 高级配置 -->
			<div class="space-y-3">
				<div class="text-xs font-medium text-gray-600 dark:text-gray-400">高级配置</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium flex items-center space-x-1">
							<span>最大并发任务数</span>
							<Tooltip content="同时处理的最大任务数量">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
									/>
								</svg>
							</Tooltip>
						</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="3"
								type="number"
								min="1"
								max="10"
								bind:value={klingLipSyncConfig.maxConcurrentTasks}
								required
							/>
						</div>
					</div>
				</div>

				<div>
					<div class="flex w-full justify-between mb-2">
						<div class="self-center text-xs font-medium flex items-center space-x-1">
							<span>任务超时时间 (毫秒)</span>
							<Tooltip content="单个任务的最长等待时间，超时会被标记为失败">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-3 h-3"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9.879 7.519c.188-.351.375-.703.563-1.055a.75.75 0 1 1 1.327.706c-.188.351-.375.703-.563 1.055-.188.351-.375.703-.563 1.054a.75.75 0 0 1-1.327-.706c.188-.351.375-.703.563-1.054Z M12 17.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
									/>
								</svg>
							</Tooltip>
						</div>
					</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-850"
								placeholder="300000"
								type="number"
								min="60000"
								max="1800000"
								step="1000"
								bind:value={klingLipSyncConfig.taskTimeout}
								required
							/>
						</div>
					</div>
					<div class="text-xs text-gray-400 mt-1">推荐值: 300000ms (5分钟)</div>
				</div>
			</div>
		{/if}
	</div>

	<hr class=" border-gray-700" />

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class=" px-4 py-2 bg-blue-600 hover:bg-blue-700 text-gray-100 transition rounded-lg flex items-center space-x-2"
			type="submit"
			disabled={loading}
		>
			{#if loading}
				<svg
					class=" w-4 h-4 animate-spin"
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
				>
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					></path>
				</svg>
				<span>保存中...</span>
			{:else}
				<span>保存配置</span>
			{/if}
		</button>
	</div>

	<div class=" text-xs text-gray-400">
		配置完成后，用户将能够使用可灵对口型功能生成视频。请确保API密钥有效且账户余额充足。
	</div>
</form>
