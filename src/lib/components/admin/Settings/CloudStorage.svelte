<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import CloudStorageStats from './CloudStorageStats.svelte';

	// Import Storage API functions
	import {
		type CloudStorageConfig,
		type StorageStats,
		getStorageConfig,
		saveStorageConfig,
		testStorageConnection,
		getStorageStats,
		migrateExternalFiles
	} from '$lib/apis/storage';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let testingConnection = false;
	let migrating = false;
	let stats: StorageStats | null = null;

	// 云存储配置
	let storageConfig: CloudStorageConfig = {
		provider: 'tencent-cos',
		enabled: false,
		secretId: '',
		secretKey: '',
		region: 'ap-beijing',
		bucket: '',
		domain: '',
		autoUpload: true,
		allowedTypes: ['image/*', 'video/*'],
		maxFileSize: 104857600, // 100MB
		basePath: 'generated/',
		imagePath: 'images/',
		videoPath: 'videos/'
	};

	// 地域选项
	const regions = [
		{ value: 'ap-beijing', label: '北京 (ap-beijing)' },
		{ value: 'ap-shanghai', label: '上海 (ap-shanghai)' },
		{ value: 'ap-guangzhou', label: '广州 (ap-guangzhou)' },
		{ value: 'ap-chengdu', label: '成都 (ap-chengdu)' },
		{ value: 'ap-chongqing', label: '重庆 (ap-chongqing)' },
		{ value: 'ap-nanjing', label: '南京 (ap-nanjing)' },
		{ value: 'ap-hongkong', label: '香港 (ap-hongkong)' },
		{ value: 'ap-singapore', label: '新加坡 (ap-singapore)' },
		{ value: 'ap-tokyo', label: '东京 (ap-tokyo)' },
		{ value: 'na-siliconvalley', label: '硅谷 (na-siliconvalley)' }
	];

	// 文件类型选项
	const fileTypeOptions = [
		{ value: 'image/*', label: '图片文件' },
		{ value: 'video/*', label: '视频文件' },
		{ value: 'image/jpeg', label: 'JPEG 图片' },
		{ value: 'image/png', label: 'PNG 图片' },
		{ value: 'image/gif', label: 'GIF 图片' },
		{ value: 'video/mp4', label: 'MP4 视频' },
		{ value: 'video/avi', label: 'AVI 视频' }
	];

	onMount(async () => {
		await loadStorageConfig();
		if (storageConfig.enabled) {
			await loadStorageStats();
		}
	});

	const loadStorageConfig = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			const config = await getStorageConfig($user.token);
			if (config) {
				storageConfig = { ...storageConfig, ...config };
			}
		} catch (error) {
			console.error('Failed to load storage config:', error);
			toast.error('加载云存储配置失败');
		} finally {
			loading = false;
		}
	};

	const loadStorageStats = async () => {
		if (!$user?.token || !storageConfig.enabled) {
			return;
		}

		try {
			const result = await getStorageStats($user.token);
			if (result) {
				stats = result;
			}
		} catch (error) {
			console.error('Failed to load storage stats:', error);
		}
	};

	const saveStorageConfigData = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		loading = true;
		try {
			await saveStorageConfig($user.token, storageConfig);
			toast.success('云存储配置已保存');
			dispatch('save');

			if (storageConfig.enabled) {
				await loadStorageStats();
			}
		} catch (error) {
			console.error('Failed to save storage config:', error);
			toast.error('保存云存储配置失败');
		} finally {
			loading = false;
		}
	};

	const testConnection = async () => {
		if (!storageConfig.secretId || !storageConfig.secretKey || !storageConfig.bucket) {
			toast.error('请先配置完整的腾讯云COS信息');
			return;
		}

		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		testingConnection = true;
		try {
			const result = await testStorageConnection($user.token);
			if (result?.success) {
				toast.success(`连接测试成功！${result.details ? `存储桶: ${result.details.bucket}` : ''}`);
			} else {
				toast.error(`连接测试失败: ${result?.message || '未知错误'}`);
			}
		} catch (error) {
			console.error('Connection test failed:', error);
			toast.error('连接测试失败');
		} finally {
			testingConnection = false;
		}
	};

	const migrateFiles = async () => {
		if (!$user?.token) {
			toast.error('需要管理员权限');
			return;
		}

		if (!storageConfig.enabled) {
			toast.error('请先启用云存储功能');
			return;
		}

		migrating = true;
		try {
			const result = await migrateExternalFiles($user.token);
			if (result?.success) {
				toast.success(`迁移完成: 成功 ${result.migrated_count} 个，失败 ${result.failed_count} 个`);
				await loadStorageStats();
			} else {
				toast.error(`迁移失败: ${result?.message || '未知错误'}`);
			}
		} catch (error) {
			console.error('Migration failed:', error);
			toast.error('批量迁移失败');
		} finally {
			migrating = false;
		}
	};

	const formatFileSize = (bytes: number) => {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	};

	const addFileType = (type: string) => {
		if (!storageConfig.allowedTypes.includes(type)) {
			storageConfig.allowedTypes = [...storageConfig.allowedTypes, type];
		}
	};

	const removeFileType = (index: number) => {
		storageConfig.allowedTypes = storageConfig.allowedTypes.filter((_, i) => i !== index);
	};
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class=" space-y-3 pr-1.5">
		<div>
			<div class=" mb-1 text-sm font-medium">云存储配置</div>
			<div class="text-xs text-gray-400 dark:text-gray-500">
				配置腾讯云COS存储，自动保存AI生成的图片和视频
			</div>
		</div>

		<hr class="dark:border-gray-700" />

		<!-- 启用开关 -->
		<div class="flex w-full justify-between">
			<div class="flex flex-col">
				<div class="text-sm font-medium">启用云存储</div>
				<div class="text-xs text-gray-400">启用后将自动上传AI生成的内容到腾讯云COS</div>
			</div>
			<Switch bind:state={storageConfig.enabled} />
		</div>

		{#if storageConfig.enabled}
			<!-- COS 配置 -->
			<div>
				<div class="mb-2 text-sm font-medium">腾讯云COS配置</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">SecretId</div>
					<SensitiveInput
						placeholder="请输入SecretId"
						bind:value={storageConfig.secretId}
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">SecretKey</div>
					<SensitiveInput
						placeholder="请输入SecretKey"
						bind:value={storageConfig.secretKey}
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">地域 (Region)</div>
					<select
						bind:value={storageConfig.region}
						class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					>
						{#each regions as region}
							<option value={region.value}>{region.label}</option>
						{/each}
					</select>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">存储桶名称 (Bucket)</div>
					<input
						bind:value={storageConfig.bucket}
						placeholder="your-bucket-name-1234567890"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">
						自定义域名 (可选)
						<Tooltip content="如果配置了自定义域名，生成的文件URL将使用此域名">
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
									d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
								/>
							</svg>
						</Tooltip>
					</div>
					<input
						bind:value={storageConfig.domain}
						placeholder="https://cdn.example.com"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="flex gap-2">
					<button
						class="px-3 py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-lg"
						on:click={testConnection}
						disabled={testingConnection}
					>
						{testingConnection ? '测试中...' : '测试连接'}
					</button>
				</div>
			</div>

			<hr class="dark:border-gray-700" />

			<!-- 上传设置 -->
			<div>
				<div class="mb-3 text-sm font-medium">上传设置</div>

				<div class="flex w-full justify-between mb-3">
					<div class="flex flex-col">
						<div class="text-sm font-medium">自动上传</div>
						<div class="text-xs text-gray-400">AI生成内容时自动上传到云存储</div>
					</div>
					<Switch bind:state={storageConfig.autoUpload} />
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">最大文件大小 (字节)</div>
					<input
						type="number"
						bind:value={storageConfig.maxFileSize}
						min="1048576"
						max="1073741824"
						step="1048576"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
					<div class="text-xs text-gray-500 mt-1">
						当前设置: {formatFileSize(storageConfig.maxFileSize)}
					</div>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-2">允许的文件类型</div>
					<div class="flex flex-wrap gap-2 mb-2">
						{#each storageConfig.allowedTypes as type, index}
							<span
								class="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs flex items-center gap-1"
							>
								{type}
								<button
									on:click={() => removeFileType(index)}
									class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
								>
									×
								</button>
							</span>
						{/each}
					</div>
					<div class="flex gap-2">
						<select
							class="rounded py-1 px-2 text-xs bg-gray-50 dark:bg-gray-800 border dark:border-gray-700 outline-none"
							on:change={(e) => {
								const value = e.target.value;
								if (value) {
									addFileType(value);
									e.target.value = '';
								}
							}}
						>
							<option value="">选择文件类型</option>
							{#each fileTypeOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
				</div>
			</div>

			<hr class="dark:border-gray-700" />

			<!-- 路径配置 -->
			<div>
				<div class="mb-3 text-sm font-medium">存储路径配置</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">基础路径</div>
					<input
						bind:value={storageConfig.basePath}
						placeholder="generated/"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">图片子路径</div>
					<input
						bind:value={storageConfig.imagePath}
						placeholder="images/"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="mb-3">
					<div class="text-xs text-gray-400 mb-1">视频子路径</div>
					<input
						bind:value={storageConfig.videoPath}
						placeholder="videos/"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none border border-gray-100 dark:border-gray-800"
					/>
				</div>

				<div class="text-xs text-gray-500 p-2 bg-gray-50 dark:bg-gray-800 rounded">
					<strong>示例路径:</strong><br />
					图片: {storageConfig.basePath}{storageConfig.imagePath}2024/01/15/user_abc123_image.jpg<br
					/>
					视频: {storageConfig.basePath}{storageConfig.videoPath}2024/01/15/user_abc123_video.mp4
				</div>
			</div>

			{#if stats || storageConfig.enabled}
				<hr class="dark:border-gray-700" />

				<!-- 存储统计 -->
				<div>
					<div class="mb-4 flex items-center justify-between">
						<div class="text-sm font-medium">存储统计</div>
						<button
							class="px-3 py-1 text-xs font-medium bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-800 dark:text-blue-200 transition rounded-lg"
							on:click={loadStorageStats}
							disabled={loading}
						>
							刷新统计
						</button>
					</div>

					<CloudStorageStats {stats} />

					<div class="mt-4 flex gap-2">
						<button
							class="px-3 py-1.5 text-xs font-medium bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-800 dark:text-green-200 transition rounded-lg"
							on:click={migrateFiles}
							disabled={migrating}
						>
							{migrating ? '迁移中...' : '批量迁移外部文件'}
						</button>
					</div>
				</div>
			{/if}
		{/if}
	</div>

	<div class="flex justify-end pt-3">
		<button
			class="px-3 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 dark:bg-white dark:hover:bg-gray-100 dark:text-black text-white transition rounded-lg"
			on:click={saveStorageConfigData}
			disabled={loading}
		>
			{loading ? '保存中...' : '保存配置'}
		</button>
	</div>
</div>
