<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import Google Images API functions
	import {
		getGoogleImagesAdminConfig,
		saveGoogleImagesAdminConfig
	} from '$lib/apis/google_images/admin';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;

	// 谷歌生图配置
	let googleImagesConfig = {
		enabled: false,
		base_url: 'https://api.google-images.com',
		api_key: '',
		default_model: 'nano-banana',
		max_images_per_request: 10,
		timeout: 60,
		credits_per_generation: 20,
		credits_per_image: 5,
		additional_config: {}
	};

	onMount(async () => {
		await loadGoogleImagesConfig();
	});

	const loadGoogleImagesConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getGoogleImagesAdminConfig($user.token);
			if (config) {
				googleImagesConfig = { ...googleImagesConfig, ...config };
				console.log('谷歌生图配置加载成功:', googleImagesConfig);
			}
		} catch (error) {
			console.error('Failed to load Google Images config:', error);
			toast.error('加载谷歌生图配置失败');
		} finally {
			loading = false;
		}
	};

	const saveGoogleImagesConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const result = await saveGoogleImagesAdminConfig($user.token, googleImagesConfig);
			if (result.success) {
				toast.success('谷歌生图配置已保存');
				dispatch('save');
			} else {
				throw new Error(result.message || '保存失败');
			}
		} catch (error) {
			console.error('Failed to save Google Images config:', error);
			toast.error('保存谷歌生图配置失败: ' + error.message);
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!googleImagesConfig.base_url || !googleImagesConfig.api_key) {
			toast.error('请先配置 API URL 和密钥');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			// 先保存配置，然后测试用户配置接口
			await saveGoogleImagesConfigData();

			// 测试用户配置接口
			const response = await fetch(`/api/v1/google_images/config/user`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${$user.token}`
				}
			});

			if (response.ok) {
				const data = await response.json();
				if (data.enabled) {
					toast.success('谷歌生图连接测试成功！');
				} else {
					toast.warning('服务未启用');
				}
			} else {
				throw new Error('连接测试失败');
			}
		} catch (error) {
			console.error('Failed to test Google Images connection:', error);
			toast.error('连接测试失败: ' + error.message);
		} finally {
			loading = false;
		}
	};
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm">
	<div class="space-y-3 pr-1.5 overflow-y-scroll scrollbar-hidden h-full">
		<div>
			<div class=" mb-2 text-sm font-medium">🔍 谷歌生图服务</div>
			<div class="text-xs text-gray-400">
				配置谷歌生图服务，支持OpenAI DALL-E兼容格式的图像生成和编辑
			</div>
		</div>

		<hr class=" dark:border-gray-700" />

		<!-- 启用开关 -->
		<div class="space-y-3">
			<div class="flex justify-between items-center">
				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">启用谷歌生图</div>
						<Tooltip content="启用后用户可以使用谷歌生图进行图像生成和编辑">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<div class="text-xs text-gray-500">开启谷歌生图服务功能</div>
				</div>
				<Switch bind:state={googleImagesConfig.enabled} />
			</div>
		</div>

		<hr class=" dark:border-gray-700" />

		<!-- API配置 -->
		{#if googleImagesConfig.enabled}
			<div class="space-y-3">
				<div class="text-sm font-medium">API 配置</div>

				<!-- API URL -->
				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">API URL</div>
						<Tooltip content="谷歌生图 API 服务地址">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<input
						class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-600"
						placeholder="https://api.google-images.com"
						bind:value={googleImagesConfig.base_url}
						required
					/>
				</div>

				<!-- API Key -->
				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">API Key</div>
						<Tooltip content="谷歌生图 API 密钥">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<SensitiveInput
						placeholder="输入你的谷歌生图 API Key"
						bind:value={googleImagesConfig.api_key}
						required
					/>
				</div>

				<!-- 连接测试按钮 -->
				<div class="flex justify-end">
					<button
						class="px-3 py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-200 transition duration-200 rounded-lg"
						on:click={testConnection}
						disabled={loading || !googleImagesConfig.base_url || !googleImagesConfig.api_key}
					>
						{loading ? '测试中...' : '测试连接'}
					</button>
				</div>
			</div>

			<hr class=" dark:border-gray-700" />

			<!-- 模型信息 -->
			<div class="space-y-3">
				<div class="text-sm font-medium">模型信息</div>
				<div
					class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
				>
					<div class="text-sm">当前模型</div>
					<div class="text-sm font-medium text-blue-600 dark:text-blue-400">
						Nano Banana - 通用模型
					</div>
				</div>
				<div class="text-xs text-gray-500">
					所有图像生成请求将使用 nano-banana 模型，结果自动上传到云存储
				</div>
			</div>

			<hr class=" dark:border-gray-700" />

			<!-- 请求限制设置 -->
			<div class="space-y-3">
				<div class="text-sm font-medium">请求限制设置</div>

				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">单次最大图片数</div>
						<Tooltip content="单次请求最多可上传的参考图片数量">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<input
						type="number"
						min="1"
						max="20"
						class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-600"
						bind:value={googleImagesConfig.max_images_per_request}
					/>
				</div>

				<div class="space-y-1">
					<div class="flex items-center space-x-2">
						<div class="font-medium text-sm">请求超时时间 (秒)</div>
						<Tooltip content="API请求的超时时间">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									fill-rule="evenodd"
									d="M15 8A7 7 0 1 1 1 8a7 7 0 0 1 14 0ZM6 4a1 1 0 0 1 2 0v3a1 1 0 1 1-2 0V4Zm2 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
									clip-rule="evenodd"
								/>
							</svg>
						</Tooltip>
					</div>
					<input
						type="number"
						min="10"
						max="300"
						class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-600"
						bind:value={googleImagesConfig.timeout}
					/>
				</div>
			</div>

			<hr class=" dark:border-gray-700" />

			<!-- 积分配置 -->
			<div class="space-y-3">
				<div class="text-sm font-medium">积分配置</div>
				<div class="text-xs text-gray-500 mb-3">设置每次图像生成和参考图片的积分消耗</div>

				<!-- 基础积分 -->
				<div class="space-y-2">
					<div class="text-sm font-medium text-blue-600 dark:text-blue-400">基础消费</div>
					<div
						class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
					>
						<div class="text-sm">每次生成基础积分</div>
						<div class="flex items-center space-x-2">
							<input
								type="number"
								min="1"
								max="1000"
								class="w-16 rounded-lg py-1 px-2 text-sm dark:text-gray-300 dark:bg-gray-700 outline-none border border-gray-200 dark:border-gray-600"
								bind:value={googleImagesConfig.credits_per_generation}
							/>
							<span class="text-xs text-gray-500">积分</span>
						</div>
					</div>

					<div
						class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
					>
						<div class="text-sm">每张参考图额外积分</div>
						<div class="flex items-center space-x-2">
							<input
								type="number"
								min="0"
								max="100"
								class="w-16 rounded-lg py-1 px-2 text-sm dark:text-gray-300 dark:bg-gray-700 outline-none border border-gray-200 dark:border-gray-600"
								bind:value={googleImagesConfig.credits_per_image}
							/>
							<span class="text-xs text-gray-500">积分</span>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-gray-50 transition rounded-lg"
			disabled={loading}
			on:click={saveGoogleImagesConfigData}
		>
			{loading ? '保存中...' : '保存配置'}
		</button>
	</div>
</div>
