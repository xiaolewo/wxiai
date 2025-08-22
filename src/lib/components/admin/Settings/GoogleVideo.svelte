<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';

	import {
		getGoogleVideoConfig,
		saveGoogleVideoConfig,
		testGoogleVideoConnection,
		type GoogleVideoConfig
	} from '$lib/apis/google-video';

	let loading = false;
	let testing = false;
	let config: GoogleVideoConfig = {
		enabled: false,
		base_url: '',
		api_key: '',
		default_text_model: 'veo3',
		default_image_model: 'veo3-pro-frames',
		default_enhance_prompt: false,
		model_credits_config: getDefaultModelCredits(),
		max_concurrent_tasks: 3,
		task_timeout: 600000
	};

	// 谷歌视频支持的模型
	const GOOGLE_VIDEO_MODELS = {
		// 文生视频模型（10个）- 根据API文档
		text_to_video: [
			{ id: 'veo3', name: 'Veo 3.0', description: '最新版本，高质量输出' },
			{ id: 'veo3-fast', name: 'Veo 3.0 Fast', description: '快速生成版本' },
			{ id: 'veo3-pro', name: 'Veo 3.0 Pro', description: '专业版本，最高质量' },
			{
				id: 'veo3-pro-frames',
				name: 'Veo 3.0 Pro Frames',
				description: '专业版本（可用于图生视频）'
			},
			{ id: 'veo2', name: 'Veo 2.0', description: '经典版本' },
			{ id: 'veo2-fast', name: 'Veo 2.0 Fast', description: '快速版本' },
			{
				id: 'veo2-fast-frames',
				name: 'Veo 2.0 Fast Frames',
				description: '快速帧处理版本（可用于图生视频）'
			},
			{
				id: 'veo2-fast-components',
				name: 'Veo 2.0 Fast Components',
				description: '组件化快速生成（可用于图生视频）'
			},
			{ id: 'veo2-pro', name: 'Veo 2.0 Pro', description: '专业版本' },
			{
				id: 'veo3-fast-frames',
				name: 'Veo 3.0 Fast Frames',
				description: '快速帧处理版本（可用于图生视频）'
			}
		],
		// 图生视频模型（4个）- 根据API文档
		image_to_video: [
			{
				id: 'veo3-pro-frames',
				name: 'Veo 3.0 Pro Frames',
				description: '专业图生视频',
				maxImages: 1,
				imageType: '首帧'
			},
			{
				id: 'veo3-fast-frames',
				name: 'Veo 3.0 Fast Frames',
				description: '快速图生视频',
				maxImages: 1,
				imageType: '首帧'
			},
			{
				id: 'veo2-fast-frames',
				name: 'Veo 2.0 Fast Frames',
				description: '经典图生视频',
				maxImages: 2,
				imageType: '首尾帧'
			},
			{
				id: 'veo2-fast-components',
				name: 'Veo 2.0 Fast Components',
				description: '组件化图生视频',
				maxImages: 3,
				imageType: '视频元素'
			}
		]
	};

	function getDefaultModelCredits(): Record<string, number> {
		return {
			// 文生视频专用模型 (6个)
			veo3: 100,
			'veo3-fast': 80,
			'veo3-pro': 150,
			veo2: 80,
			'veo2-fast': 60,
			'veo2-pro': 120,
			// 文生视频&图生视频通用模型 (4个)
			'veo3-pro-frames': 200,
			'veo3-fast-frames': 160,
			'veo2-fast-frames': 120,
			'veo2-fast-components': 100
		};
	}

	onMount(async () => {
		await loadConfig();
	});

	const loadConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		try {
			loading = true;
			const response = await getGoogleVideoConfig($user.token);
			config = response;

			// 确保积分配置存在，合并默认值
			const defaultCredits = getDefaultModelCredits();
			if (!config.model_credits_config) {
				config.model_credits_config = defaultCredits;
			} else {
				// 合并默认积分配置，确保所有模型都有积分设置
				config.model_credits_config = { ...defaultCredits, ...config.model_credits_config };
			}
		} catch (error) {
			console.error('加载配置失败:', error);
			toast.error('加载配置失败');
		} finally {
			loading = false;
		}
	};

	const handleSaveConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		try {
			loading = true;

			// 确保积分配置完整
			if (!config.model_credits_config || Object.keys(config.model_credits_config).length === 0) {
				config.model_credits_config = getDefaultModelCredits();
			}

			await saveGoogleVideoConfig(config, $user.token);
			toast.success('配置保存成功');
		} catch (error) {
			console.error('保存配置失败:', error);
			toast.error('保存配置失败');
		} finally {
			loading = false;
		}
	};

	const handleTestConnection = async () => {
		if (!config.base_url || !config.api_key) {
			toast.error('请先填写API地址和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		try {
			testing = true;
			const response = await testGoogleVideoConnection($user.token);

			if (response.success) {
				toast.success('连接测试成功');
			} else {
				toast.error(`连接测试失败: ${response.message}`);
			}
		} catch (error) {
			console.error('测试连接失败:', error);
			toast.error('测试连接失败');
		} finally {
			testing = false;
		}
	};
</script>

<div class="flex flex-col h-full justify-between space-y-6">
	<div class="space-y-6">
		<!-- 服务状态 -->
		<div class="flex items-center justify-between">
			<div>
				<h2 class="text-xl font-semibold">谷歌视频配置</h2>
				<p class="text-sm text-gray-600 dark:text-gray-400">
					配置谷歌Veo视频生成服务，支持文生视频和图生视频
				</p>
			</div>
			<div class="flex items-center space-x-2">
				<div class="w-3 h-3 rounded-full {config.enabled ? 'bg-green-500' : 'bg-red-500'}"></div>
				<span class="text-sm {config.enabled ? 'text-green-600' : 'text-red-600'}">
					{config.enabled ? '已启用' : '未启用'}
				</span>
			</div>
		</div>

		<!-- 基本配置 -->
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
			<h3 class="text-lg font-medium">基本配置</h3>

			<!-- 启用开关 -->
			<div class="flex items-center space-x-3">
				<input
					type="checkbox"
					id="enabled"
					bind:checked={config.enabled}
					class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
				/>
				<label for="enabled" class="text-sm font-medium">启用谷歌视频生成服务</label>
			</div>

			<!-- API配置 -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div>
					<label for="base_url" class="block text-sm font-medium mb-1">API Base URL</label>
					<input
						type="text"
						id="base_url"
						bind:value={config.base_url}
						placeholder="https://api.linkapi.org"
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>

				<div>
					<label for="api_key" class="block text-sm font-medium mb-1">API Key</label>
					<input
						type="password"
						id="api_key"
						bind:value={config.api_key}
						placeholder="sk-..."
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>
			</div>
		</div>

		<!-- 模型配置 -->
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
			<h3 class="text-lg font-medium">模型配置</h3>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div>
					<label for="default_text_model" class="block text-sm font-medium mb-1"
						>默认文生视频模型</label
					>
					<select
						id="default_text_model"
						bind:value={config.default_text_model}
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						{#each GOOGLE_VIDEO_MODELS.text_to_video as model}
							<option value={model.id}>{model.name} - {model.description}</option>
						{/each}
					</select>
				</div>

				<div>
					<label for="default_image_model" class="block text-sm font-medium mb-1"
						>默认图生视频模型</label
					>
					<select
						id="default_image_model"
						bind:value={config.default_image_model}
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						{#each GOOGLE_VIDEO_MODELS.image_to_video as model}
							<option value={model.id}>{model.name} - {model.description}</option>
						{/each}
					</select>
				</div>
			</div>

			<!-- 提示词增强 -->
			<div class="flex items-center space-x-3">
				<input
					type="checkbox"
					id="default_enhance_prompt"
					bind:checked={config.default_enhance_prompt}
					class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
				/>
				<label for="default_enhance_prompt" class="text-sm font-medium">
					默认启用提示词增强（中文转英文）
				</label>
			</div>
		</div>

		<!-- 积分配置 -->
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
			<div class="flex items-center justify-between">
				<h3 class="text-lg font-medium">积分配置</h3>
				<div class="flex items-center space-x-2">
					<span class="text-xs text-gray-500">
						{Object.keys(config.model_credits_config || {}).length} 个模型
					</span>
					<button
						type="button"
						on:click={() => {
							config.model_credits_config = getDefaultModelCredits();
							toast.success('已重置为默认积分配置');
						}}
						class="px-2 py-1 text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 border border-blue-300 dark:border-blue-600 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
					>
						重置默认
					</button>
				</div>
			</div>
			<p class="text-sm text-gray-600 dark:text-gray-400">设置不同模型的积分消耗</p>

			{#if config.model_credits_config && Object.keys(config.model_credits_config).length > 0}
				<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
					{#each Object.keys(config.model_credits_config) as model}
						<div>
							<label for="credits_{model}" class="block text-xs font-medium mb-1">
								{model}
								{#if ['veo3-pro-frames', 'veo3-fast-frames', 'veo2-fast-frames', 'veo2-fast-components'].includes(model)}
									<span class="text-green-500 text-xs">(图生视频)</span>
								{:else if GOOGLE_VIDEO_MODELS.text_to_video.find((m) => m.id === model)}
									<span class="text-blue-500 text-xs">(文生视频)</span>
								{/if}
							</label>
							<input
								type="number"
								id="credits_{model}"
								bind:value={config.model_credits_config[model]}
								min="1"
								step="1"
								class="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
							/>
						</div>
					{/each}
				</div>
			{:else}
				<div
					class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 text-center"
				>
					<p class="text-sm text-yellow-700 dark:text-yellow-300">
						模型积分配置为空，请点击"重新加载"或"保存配置"来初始化默认设置
					</p>
				</div>
			{/if}
		</div>

		<!-- 系统配置 -->
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
			<h3 class="text-lg font-medium">系统配置</h3>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div>
					<label for="max_concurrent_tasks" class="block text-sm font-medium mb-1"
						>最大并发任务数</label
					>
					<input
						type="number"
						id="max_concurrent_tasks"
						bind:value={config.max_concurrent_tasks}
						min="1"
						max="10"
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>

				<div>
					<label for="task_timeout" class="block text-sm font-medium mb-1"
						>任务超时时间（毫秒）</label
					>
					<input
						type="number"
						id="task_timeout"
						bind:value={config.task_timeout}
						min="60000"
						step="60000"
						class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					<p class="text-xs text-gray-500 mt-1">
						当前设置: {Math.floor(config.task_timeout / 60000)} 分钟
					</p>
				</div>
			</div>
		</div>

		<!-- 图生视频模型限制提示 -->
		<div class="bg-blue-50 dark:bg-blue-900 rounded-lg p-4 space-y-4">
			<h3 class="text-lg font-medium">图生视频模型限制</h3>
			<p class="text-sm text-gray-600 dark:text-gray-400">不同模型支持的图片数量和类型有所不同</p>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				{#each GOOGLE_VIDEO_MODELS.image_to_video as model}
					<div class="bg-white dark:bg-gray-800 rounded border p-3">
						<div class="font-medium text-sm">{model.name}</div>
						<div class="text-xs text-gray-500 mt-1">{model.description}</div>
						<div class="text-xs text-blue-600 dark:text-blue-400 mt-2">
							最多 {model.maxImages} 张图片（{model.imageType}）
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>

	<!-- 操作按钮 -->
	<div class="flex flex-wrap gap-2">
		<button
			type="button"
			on:click={handleSaveConfig}
			disabled={loading}
			class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
		>
			{#if loading}
				<div class="inline-flex items-center">
					<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					保存中...
				</div>
			{:else}
				保存配置
			{/if}
		</button>

		<button
			type="button"
			on:click={handleTestConnection}
			disabled={testing}
			class="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
		>
			{#if testing}
				<div class="inline-flex items-center">
					<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					测试中...
				</div>
			{:else}
				测试连接
			{/if}
		</button>

		<button
			type="button"
			on:click={loadConfig}
			disabled={loading}
			class="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50"
		>
			重新加载
		</button>
	</div>
</div>

<style>
	/* 响应式样式调整 */
	@media (max-width: 640px) {
		.grid {
			grid-template-columns: 1fr;
		}
	}
</style>
