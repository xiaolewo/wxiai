<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { user, showSidebar } from '$lib/stores';

	import {
		type ComfyUIWorkflow,
		type ComfyUITask,
		type ComfyUICredits,
		getComfyUIWorkflowSchema,
		submitComfyUITask,
		getComfyUITaskStatus,
		getComfyUICredits
	} from '$lib/apis/comfyui';

	const i18n = getContext('i18n');
	const workflowId = $page.params.id;

	let workflow: ComfyUIWorkflow | null = null;
	let parameterSchema: any = null;
	let userCredits: ComfyUICredits | null = null;
	let loading = true;
	let submitting = false;
	let formData: Record<string, any> = {};
	let currentTask: ComfyUITask | null = null;
	let taskPollingInterval: any = null;

	// 图片模态框
	let showImageModal = false;
	let modalImageUrl = '';

	// 加载工作流参数结构
	const loadWorkflowSchema = async () => {
		loading = true;
		try {
			const result = await getComfyUIWorkflowSchema(workflowId);
			workflow = result.workflow;
			parameterSchema = result.parameter_schema;

			// 初始化表单数据
			if (parameterSchema?.fields) {
				for (const field of parameterSchema.fields) {
					formData[field.id] = field.defaultValue;
				}
			}
		} catch (error) {
			console.error('获取工作流参数失败:', error);
			toast.error('获取工作流参数失败');
			goto('/comfyui');
		}
		loading = false;
	};

	// 加载用户积分
	const loadUserCredits = async () => {
		if (!$user.token) return;

		try {
			userCredits = await getComfyUICredits($user.token);
		} catch (error) {
			console.error('获取用户积分失败:', error);
		}
	};

	// 提交任务
	const submitTask = async () => {
		if (!$user.token) {
			toast.error('请先登录');
			return;
		}

		if (!workflow) {
			toast.error('工作流信息不完整');
			return;
		}

		// 检查必填字段
		const requiredFields = parameterSchema?.fields?.filter((f: any) => f.required) || [];
		for (const field of requiredFields) {
			if (!formData[field.id]) {
				toast.error(`请填写必填字段：${field.displayName}`);
				return;
			}
		}

		submitting = true;
		try {
			console.log('🚀 提交参数数据:', formData);
			// 检查是否有图像参数
			Object.keys(formData).forEach((key) => {
				const value = formData[key];
				if (typeof value === 'string' && value.startsWith('data:image/')) {
					console.log(`📷 检测到图像参数 ${key}:`, value.substring(0, 100) + '...');
				}
			});

			const task = await submitComfyUITask($user.token, workflowId, formData);
			currentTask = task;
			toast.success('任务提交成功，正在处理中...');

			// 开始轮询任务状态
			startTaskPolling();
		} catch (error) {
			console.error('提交任务失败:', error);
			toast.error(`提交任务失败: ${error.detail || error.message}`);
		}
		submitting = false;
	};

	// 开始轮询任务状态
	const startTaskPolling = () => {
		if (taskPollingInterval) {
			clearInterval(taskPollingInterval);
		}

		taskPollingInterval = setInterval(async () => {
			if (!currentTask || !$user.token) return;

			try {
				const updatedTask = await getComfyUITaskStatus($user.token, currentTask.id);
				currentTask = updatedTask;

				if (updatedTask.status === 'SUCCESS') {
					clearInterval(taskPollingInterval);
					toast.success('任务完成！');
					// 重新加载用户积分
					await loadUserCredits();
				} else if (updatedTask.status === 'FAILED') {
					clearInterval(taskPollingInterval);
					toast.error(`任务失败: ${updatedTask.error_message || '未知错误'}`);
				}
			} catch (error) {
				console.error('查询任务状态失败:', error);
			}
		}, 3000); // 每3秒查询一次
	};

	// 渲染表单字段
	const renderField = (field: any) => {
		// 优先根据字段类型判断
		if (field.type === 'IMAGE') {
			return 'file';
		} else if (field.type === 'BOOLEAN') {
			return 'switch';
		} else if (field.type === 'INTEGER' || field.type === 'FLOAT' || field.type === 'INT') {
			return 'input';
		} else if (field.type === 'STRING' && field.multiline) {
			return 'textarea';
		}

		// 备用：根据controlType判断
		switch (field.controlType) {
			case 'imageUpload':
				return 'file';
			case 'switch':
				return 'switch';
			case 'number':
				return 'input';
			case 'textarea':
				return 'textarea';
			case 'text':
			default:
				return 'input';
		}
	};

	// 处理文件上传
	const handleFileUpload = async (event: Event, fieldId: string) => {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		// 检查文件大小（限制为5MB）
		const maxSizeMB = 5;
		const maxSizeBytes = maxSizeMB * 1024 * 1024;
		if (file.size > maxSizeBytes) {
			toast.error(`图片文件过大，请选择小于 ${maxSizeMB}MB 的图片`);
			input.value = ''; // 清除文件选择
			return;
		}

		// 检查文件类型
		if (!file.type.startsWith('image/')) {
			toast.error('请选择图片文件');
			input.value = '';
			return;
		}

		try {
			// 将文件转换为base64格式
			const base64 = await fileToBase64(file);
			formData[fieldId] = base64;
			toast.success(`图片上传成功 (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
		} catch (error) {
			console.error('图片转换失败:', error);
			toast.error('图片处理失败');
		}
	};

	// 将文件转换为base64
	const fileToBase64 = (file: File): Promise<string> => {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => {
				if (typeof reader.result === 'string') {
					resolve(reader.result);
				} else {
					reject(new Error('文件读取失败'));
				}
			};
			reader.onerror = () => reject(reader.error);
			reader.readAsDataURL(file);
		});
	};

	// 打开图片模态框
	const openImageModal = (imageUrl: string) => {
		modalImageUrl = imageUrl;
		showImageModal = true;
	};

	// 关闭图片模态框
	const closeImageModal = () => {
		showImageModal = false;
		modalImageUrl = '';
	};

	onMount(() => {
		loadWorkflowSchema();
		loadUserCredits();

		// 页面卸载时清理轮询
		return () => {
			if (taskPollingInterval) {
				clearInterval(taskPollingInterval);
			}
		};
	});
</script>

<svelte:head>
	<title>{workflow?.name || 'ComfyUI 工作流'}</title>
</svelte:head>

<div
	class="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900 transition-all duration-300 {$showSidebar
		? 'md:max-w-[calc(100%-260px)]'
		: ''}"
>
	{#if loading}
		<!-- 加载状态 -->
		<div class="px-4 py-8 sm:px-6 lg:px-8">
			<div class="max-w-4xl mx-auto">
				<div
					class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 animate-pulse border dark:border-gray-700"
				>
					<div class="h-8 bg-gray-200 dark:bg-gray-700 rounded mb-4 w-1/3"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-8 w-2/3"></div>
					<div class="space-y-6">
						{#each Array(4) as _}
							<div>
								<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2 w-1/4"></div>
								<div class="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{:else if workflow}
		<!-- 主要内容 -->
		<div class="px-4 py-8 sm:px-6 lg:px-8">
			<div class="max-w-4xl mx-auto">
				<!-- 返回按钮 -->
				<button
					class="mb-4 flex items-center text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition"
					on:click={() => goto('/comfyui')}
				>
					<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M15 19l-7-7 7-7"
						/>
					</svg>
					返回工作流广场
				</button>

				<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
					<!-- 参数配置区域 -->
					<div class="lg:col-span-2">
						<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700">
							<div class="p-6 border-b dark:border-gray-700">
								<div class="flex items-start justify-between">
									<div>
										<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
											{workflow.name}
										</h1>
										{#if workflow.description}
											<p class="text-gray-600 dark:text-gray-300">
												{workflow.description}
											</p>
										{/if}
									</div>
									{#if workflow.category}
										<span
											class="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm"
										>
											{workflow.category}
										</span>
									{/if}
								</div>
							</div>

							<!-- 参数表单 -->
							<div class="p-6">
								{#if parameterSchema?.fields && parameterSchema.fields.length > 0}
									<form on:submit|preventDefault={submitTask} class="space-y-6">
										{#each parameterSchema.fields as field}
											<div class="space-y-2">
												<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
													{field.displayName || field.paramName}
													{#if field.required}
														<span class="text-red-500">*</span>
													{/if}
												</label>

												{#if renderField(field) === 'input'}
													{#if field.type === 'INTEGER' || field.type === 'FLOAT'}
														<input
															type="number"
															bind:value={formData[field.id]}
															min={field.min || 0}
															max={field.max || 1000}
															step={field.step || (field.type === 'FLOAT' ? 0.1 : 1)}
															class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
															required={field.required}
														/>
													{:else}
														<input
															type="text"
															bind:value={formData[field.id]}
															class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
															required={field.required}
														/>
													{/if}
												{:else if renderField(field) === 'textarea'}
													<textarea
														bind:value={formData[field.id]}
														rows={field.rows || 3}
														class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white resize-vertical"
														required={field.required}
													></textarea>
												{:else if renderField(field) === 'switch'}
													<label class="flex items-center space-x-3">
														<input
															type="checkbox"
															bind:checked={formData[field.id]}
															class="form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500 border-gray-300 dark:border-gray-600"
														/>
														<span class="text-sm text-gray-700 dark:text-gray-300">
															{field.label_on || '启用'}
														</span>
													</label>
												{:else if renderField(field) === 'file'}
													<div class="space-y-2">
														<input
															type="file"
															accept={field.accept || 'image/*'}
															on:change={(e) => handleFileUpload(e, field.id)}
															class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
															required={field.required}
														/>
														{#if formData[field.id]}
															<div class="mt-2">
																<img
																	src={formData[field.id]}
																	alt="预览"
																	class="max-w-xs h-32 object-cover rounded-lg border border-gray-300 dark:border-gray-600"
																/>
															</div>
														{/if}
													</div>
												{/if}

												{#if field.tooltip}
													<p class="text-xs text-gray-500 dark:text-gray-400">
														{field.tooltip}
													</p>
												{/if}
											</div>
										{/each}

										<div class="flex justify-end pt-4">
											<button
												type="submit"
												disabled={submitting ||
													!userCredits ||
													userCredits.credits_balance < (workflow.base_credits || 10)}
												class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg transition-colors duration-200 font-medium"
											>
												{submitting ? '提交中...' : '开始生成'}
											</button>
										</div>
									</form>
								{:else}
									<div class="text-center py-8 text-gray-500 dark:text-gray-400">
										<p>此工作流暂无可配置参数</p>
									</div>
								{/if}
							</div>
						</div>
					</div>

					<!-- 侧边栏 -->
					<div class="space-y-6">
						<!-- 用户积分 -->
						{#if userCredits}
							<div
								class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-4"
							>
								<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">我的积分</h3>
								<div class="flex items-center justify-between mb-2">
									<span class="text-gray-600 dark:text-gray-300">当前余额</span>
									<span class="text-2xl font-bold text-blue-600">{userCredits.credits_balance}</span
									>
								</div>
							</div>
						{/if}

						<!-- 工作流信息 -->
						<div
							class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-4"
						>
							<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">消费信息</h3>
							<div class="space-y-2 text-sm">
								<div class="flex justify-between">
									<span class="text-gray-600 dark:text-gray-300">基础积分</span>
									<span class="font-medium">{workflow.base_credits}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-600 dark:text-gray-300">复杂度系数</span>
									<span class="font-medium">×{workflow.complexity_multiplier}</span>
								</div>
								<hr class="dark:border-gray-700" />
								<div class="flex justify-between font-semibold">
									<span class="text-gray-900 dark:text-white">预估消费</span>
									<span class="text-blue-600"
										>{Math.ceil(workflow.base_credits * workflow.complexity_multiplier)}</span
									>
								</div>
							</div>
						</div>

						<!-- 任务状态 -->
						{#if currentTask}
							<div
								class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-4"
							>
								<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">任务状态</h3>
								<div class="space-y-3">
									<div class="flex items-center space-x-2">
										{#if currentTask.status === 'PENDING'}
											<div class="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
											<span class="text-yellow-600 dark:text-yellow-400">等待处理</span>
										{:else if currentTask.status === 'IN_PROGRESS'}
											<div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
											<span class="text-blue-600 dark:text-blue-400">处理中</span>
										{:else if currentTask.status === 'SUCCESS'}
											<div class="w-2 h-2 bg-green-500 rounded-full"></div>
											<span class="text-green-600 dark:text-green-400">已完成</span>
										{:else if currentTask.status === 'FAILED'}
											<div class="w-2 h-2 bg-red-500 rounded-full"></div>
											<span class="text-red-600 dark:text-red-400">失败</span>
										{/if}
									</div>

									{#if currentTask.percent_completed > 0}
										<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
											<div
												class="bg-blue-600 h-2 rounded-full transition-all duration-300"
												style="width: {currentTask.percent_completed * 100}%"
											></div>
										</div>
									{/if}

									<!-- 显示生成的图片结果 -->
									{#if (currentTask.cloud_images && currentTask.cloud_images.length > 0) || (currentTask.output_images && currentTask.output_images.length > 0)}
										<div class="space-y-2">
											<h4 class="font-medium text-gray-900 dark:text-white">生成图片</h4>
											<div class="grid grid-cols-1 gap-2">
												<!-- 优先显示云存储的图片 -->
												{#if currentTask.cloud_images && currentTask.cloud_images.length > 0}
													{#each currentTask.cloud_images as image}
														{@const imageUrl = image.cloud_url || image.original_url}
														<div class="relative group">
															<img
																src={imageUrl}
																alt="生成结果"
																class="w-full rounded-lg border border-gray-300 dark:border-gray-700 cursor-pointer"
																on:error={(e) => {
																	// 如果云存储URL失败，尝试原始URL
																	if (e.target.src === image.cloud_url && image.original_url) {
																		e.target.src = image.original_url;
																	}
																}}
																on:click={() => openImageModal(imageUrl)}
															/>
															<div class="absolute top-2 right-2">
																<span class="px-2 py-1 bg-green-500 text-white text-xs rounded">
																	已保存
																</span>
															</div>
															<div
																class="absolute bottom-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity"
															>
																<button
																	class="px-2 py-1 bg-black/50 text-white text-xs rounded hover:bg-black/70"
																	on:click={() => openImageModal(imageUrl)}
																>
																	查看原图
																</button>
															</div>
														</div>
													{/each}
												{:else if currentTask.output_images}
													{#each currentTask.output_images as image}
														<div class="relative">
															<img
																src={image.imageUrl}
																alt="生成结果"
																class="w-full rounded-lg border border-gray-300 dark:border-gray-700 cursor-pointer"
																on:click={() => openImageModal(image.imageUrl)}
															/>
															<div class="absolute top-2 right-2">
																<span class="px-2 py-1 bg-yellow-500 text-white text-xs rounded">
																	处理中
																</span>
															</div>
														</div>
													{/each}
												{/if}
											</div>
										</div>
									{/if}

									<!-- 显示生成的视频结果 -->
									{#if (currentTask.cloud_videos && currentTask.cloud_videos.length > 0) || (currentTask.output_videos && currentTask.output_videos.length > 0)}
										<div class="space-y-2">
											<h4 class="font-medium text-gray-900 dark:text-white">生成视频</h4>
											<div class="grid grid-cols-1 gap-2">
												<!-- 优先显示云存储的视频 -->
												{#if currentTask.cloud_videos && currentTask.cloud_videos.length > 0}
													{#each currentTask.cloud_videos as video}
														<div class="space-y-2 relative group">
															<video
																src={video.cloud_url}
																controls
																class="w-full rounded-lg border border-gray-300 dark:border-gray-700"
																preload="metadata"
															>
																您的浏览器不支持视频播放。
															</video>
															<div class="absolute top-2 right-2">
																<span class="px-2 py-1 bg-green-500 text-white text-xs rounded">
																	已保存
																</span>
															</div>
															{#if video.cover_url}
																<div class="absolute top-2 left-2">
																	<img
																		src={video.cover_url}
																		alt="封面"
																		class="w-12 h-12 rounded border border-gray-300 dark:border-gray-600 bg-white/90"
																	/>
																</div>
															{/if}
														</div>
													{/each}
												{:else if currentTask.output_videos}
													{#each currentTask.output_videos as video}
														<div class="space-y-2 relative">
															<video
																src={video.videoUrl}
																controls
																class="w-full rounded-lg border border-gray-300 dark:border-gray-700"
																preload="metadata"
															>
																您的浏览器不支持视频播放。
															</video>
															<div class="absolute top-2 right-2">
																<span class="px-2 py-1 bg-yellow-500 text-white text-xs rounded">
																	处理中
																</span>
															</div>
															{#if video.coverPath}
																<div class="absolute top-2 left-2">
																	<img
																		src={video.coverPath}
																		alt="封面"
																		class="w-12 h-12 rounded border border-gray-300 dark:border-gray-600 bg-white/90"
																	/>
																</div>
															{/if}
														</div>
													{/each}
												{/if}
											</div>
										</div>
									{/if}

									{#if currentTask.error_message}
										<div
											class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
										>
											<p class="text-sm text-red-600 dark:text-red-400">
												{currentTask.error_message}
											</p>
										</div>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<!-- 图片模态框 -->
{#if showImageModal}
	<div
		class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
		on:click={closeImageModal}
	>
		<div class="relative max-w-4xl max-h-full">
			<button
				class="absolute top-4 right-4 text-white hover:text-gray-300 text-2xl z-10"
				on:click={closeImageModal}
			>
				×
			</button>
			<img
				src={modalImageUrl}
				alt="查看大图"
				class="max-w-full max-h-full object-contain rounded-lg"
				on:click|stopPropagation
			/>
		</div>
	</div>
{/if}
