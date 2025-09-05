<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	// Import ComfyUI API functions
	import {
		type ComfyUIConfig,
		type ComfyUIWorkflow,
		getComfyUIConfig,
		saveComfyUIConfig,
		getComfyUIWorkflows,
		createComfyUIWorkflow,
		updateComfyUIWorkflow,
		deleteComfyUIWorkflow,
		importSampleWorkflows
	} from '$lib/apis/comfyui';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let workflowsLoading = false;
	let workflows: ComfyUIWorkflow[] = [];
	let showWorkflowModal = false;
	let editingWorkflow: Partial<ComfyUIWorkflow> | null = null;

	// ComfyUI 配置
	let comfyuiConfig: ComfyUIConfig = {
		access_key: '',
		secret_key: '',
		base_url: 'https://openapi.liblibai.cloud',
		enabled: false,
		timeout: 300,
		max_concurrent_tasks: 5
	};

	// 工作流表单数据
	let workflowForm = {
		name: '',
		description: '',
		category: '',
		preview_image: '',
		template_uuid: '',
		workflow_uuid: '',
		base_credits: 10,
		complexity_multiplier: 1.0,
		enabled: true,
		is_public: false,
		sort_order: 0,
		parameter_schema: {},
		default_params: {}
	};

	// 图片上传相关
	let fileInput: HTMLInputElement;
	let previewImageUrl = '';

	// 加载ComfyUI配置
	const loadComfyUIConfig = async () => {
		loading = true;
		try {
			const res = await getComfyUIConfig($user.token);
			comfyuiConfig = { ...comfyuiConfig, ...res };
		} catch (error) {
			console.error('获取ComfyUI管理员配置失败:', error);
			toast.error(`获取ComfyUI管理员配置失败: ${error.detail || error.message}`);
		}
		loading = false;
	};

	// 保存ComfyUI配置
	const saveComfyUIConfigData = async () => {
		loading = true;
		try {
			await saveComfyUIConfig($user.token, comfyuiConfig);
			toast.success('ComfyUI配置保存成功');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save ComfyUI config:', error);
			toast.error(`保存ComfyUI配置失败: ${error.detail || error.message}`);
		}
		loading = false;
	};

	// 加载工作流列表
	const loadWorkflows = async () => {
		workflowsLoading = true;
		try {
			workflows = await getComfyUIWorkflows($user.token);
		} catch (error) {
			console.error('获取工作流列表失败:', error);
			toast.error(`获取工作流列表失败: ${error.detail || error.message}`);
		}
		workflowsLoading = false;
	};

	// 导入示例工作流
	const importSamples = async () => {
		workflowsLoading = true;
		try {
			const result = await importSampleWorkflows($user.token);
			toast.success(result.message);
			await loadWorkflows(); // 重新加载列表
		} catch (error) {
			console.error('导入示例工作流失败:', error);
			toast.error(`导入示例工作流失败: ${error.detail || error.message}`);
		}
		workflowsLoading = false;
	};

	// 打开工作流编辑模态框
	const openWorkflowModal = (workflow: ComfyUIWorkflow | null = null) => {
		if (workflow) {
			editingWorkflow = workflow;
			workflowForm = {
				name: workflow.name,
				description: workflow.description || '',
				category: workflow.category || '',
				preview_image: workflow.preview_image || '',
				template_uuid: workflow.template_uuid,
				workflow_uuid: workflow.workflow_uuid,
				base_credits: workflow.base_credits,
				complexity_multiplier: workflow.complexity_multiplier,
				enabled: workflow.enabled,
				is_public: workflow.is_public,
				sort_order: workflow.sort_order,
				parameter_schema:
					typeof workflow.parameter_schema === 'object'
						? JSON.stringify(workflow.parameter_schema, null, 2)
						: workflow.parameter_schema || '{"fields": []}',
				default_params:
					typeof workflow.default_params === 'object'
						? JSON.stringify(workflow.default_params, null, 2)
						: workflow.default_params || '{}'
			};
			previewImageUrl = workflow.preview_image || '';
		} else {
			editingWorkflow = null;
			workflowForm = {
				name: '',
				description: '',
				category: '',
				preview_image: '',
				template_uuid: '',
				workflow_uuid: '',
				base_credits: 10,
				complexity_multiplier: 1.0,
				enabled: true,
				is_public: false,
				sort_order: 0,
				parameter_schema: '{"fields": []}',
				default_params: '{}'
			};
			previewImageUrl = '';
		}
		showWorkflowModal = true;
	};

	// 保存工作流
	const saveWorkflow = async () => {
		try {
			// 准备提交数据，将JSON字符串转换为对象
			const submitData = { ...workflowForm };

			// 解析parameter_schema
			if (typeof submitData.parameter_schema === 'string') {
				try {
					submitData.parameter_schema = JSON.parse(submitData.parameter_schema);
				} catch (error) {
					toast.error('参数结构JSON格式不正确');
					return;
				}
			}

			// 解析default_params
			if (typeof submitData.default_params === 'string') {
				try {
					submitData.default_params = JSON.parse(submitData.default_params);
				} catch (error) {
					toast.error('默认参数JSON格式不正确');
					return;
				}
			}

			if (editingWorkflow) {
				await updateComfyUIWorkflow($user.token, editingWorkflow.id!, submitData);
				toast.success('工作流更新成功');
			} else {
				await createComfyUIWorkflow($user.token, submitData);
				toast.success('工作流创建成功');
			}
			showWorkflowModal = false;
			await loadWorkflows();
		} catch (error) {
			console.error('保存工作流失败:', error);
			toast.error(`保存工作流失败: ${error.detail || error.message}`);
		}
	};

	// 删除工作流
	const deleteWorkflow = async (workflowId: string) => {
		if (!confirm('确定要删除此工作流吗？')) return;

		try {
			await deleteComfyUIWorkflow($user.token, workflowId);
			toast.success('工作流删除成功');
			await loadWorkflows();
		} catch (error) {
			console.error('删除工作流失败:', error);
			toast.error(`删除工作流失败: ${error.detail || error.message}`);
		}
	};

	// 验证参数结构JSON
	const validateParameterSchema = () => {
		try {
			if (workflowForm.parameter_schema && typeof workflowForm.parameter_schema === 'string') {
				const parsed = JSON.parse(workflowForm.parameter_schema);
				// 确保解析后的对象有fields字段
				if (!parsed.fields) {
					parsed.fields = [];
				}
				// 保持字符串格式，但格式化显示
				workflowForm.parameter_schema = JSON.stringify(parsed, null, 2);
			}
		} catch (error) {
			toast.error('参数结构JSON格式不正确');
			console.error('Parameter schema JSON parse error:', error);
		}
	};

	// 验证默认参数JSON
	const validateDefaultParams = () => {
		try {
			if (workflowForm.default_params && typeof workflowForm.default_params === 'string') {
				const parsed = JSON.parse(workflowForm.default_params);
				// 保持字符串格式，但格式化显示
				workflowForm.default_params = JSON.stringify(parsed, null, 2);
			}
		} catch (error) {
			toast.error('默认参数JSON格式不正确');
			console.error('Default params JSON parse error:', error);
		}
	};

	// 处理图片文件选择
	const handleFileSelect = (event: Event) => {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) return;

		// 检查文件类型
		if (!file.type.startsWith('image/')) {
			toast.error('请选择图片文件');
			return;
		}

		// 检查文件大小（限制为5MB）
		const maxSize = 5 * 1024 * 1024;
		if (file.size > maxSize) {
			toast.error('图片文件大小不能超过5MB');
			return;
		}

		// 读取文件并转换为base64
		const reader = new FileReader();
		reader.onload = (e) => {
			const result = e.target?.result as string;
			workflowForm.preview_image = result;
			previewImageUrl = result;
		};
		reader.readAsDataURL(file);
	};

	// 移除预览图片
	const removePreviewImage = () => {
		workflowForm.preview_image = '';
		previewImageUrl = '';
		if (fileInput) {
			fileInput.value = '';
		}
	};

	onMount(() => {
		loadComfyUIConfig();
		loadWorkflows();
	});
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={saveComfyUIConfigData}
>
	<div class="space-y-3">
		<div>
			<div class="mb-2 text-sm font-medium">ComfyUI 集成配置</div>
		</div>

		<div>
			<div class="py-0.5 flex w-full justify-between">
				<div class="self-center text-xs font-medium">启用 ComfyUI</div>
				<div class="self-center">
					<Switch state="enabled" bind:value={comfyuiConfig.enabled} />
				</div>
			</div>
		</div>

		<hr class="dark:border-gray-700" />

		<div class="space-y-3">
			<div class="w-full">
				<div class="flex w-full">
					<div class="flex-1 mr-2">
						<div class="text-xs mb-1 text-gray-500">哩布 API 基础 URL</div>
						<div class="flex w-full">
							<div class="flex-1">
								<input
									class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
									bind:value={comfyuiConfig.base_url}
									placeholder="https://openapi.liblibai.cloud"
									required
								/>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="w-full">
				<div class="flex w-full">
					<div class="flex-1 mr-2">
						<div class="text-xs mb-1 text-gray-500">Access Key</div>
						<div class="flex w-full">
							<div class="flex-1">
								<SensitiveInput
									placeholder="输入 Access Key"
									bind:value={comfyuiConfig.access_key}
									required
								/>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="w-full">
				<div class="flex w-full">
					<div class="flex-1 mr-2">
						<div class="text-xs mb-1 text-gray-500">Secret Key</div>
						<div class="flex w-full">
							<div class="flex-1">
								<SensitiveInput
									placeholder="输入 Secret Key"
									bind:value={comfyuiConfig.secret_key}
									required
								/>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="flex space-x-4">
				<div class="flex-1">
					<div class="text-xs mb-1 text-gray-500">超时时间（秒）</div>
					<input
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
						type="number"
						bind:value={comfyuiConfig.timeout}
						min="10"
						max="600"
						required
					/>
				</div>
				<div class="flex-1">
					<div class="text-xs mb-1 text-gray-500">最大并发任务数</div>
					<input
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
						type="number"
						bind:value={comfyuiConfig.max_concurrent_tasks}
						min="1"
						max="20"
						required
					/>
				</div>
			</div>
		</div>

		<hr class="dark:border-gray-700" />

		<!-- 工作流管理 -->
		<div class="space-y-3">
			<div class="flex justify-between items-center">
				<div class="text-sm font-medium">工作流管理</div>
				<div class="flex space-x-2">
					<button
						type="button"
						class="px-3 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition"
						on:click={importSamples}
						disabled={workflowsLoading}
					>
						导入示例
					</button>
					<button
						type="button"
						class="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
						on:click={() => openWorkflowModal()}
					>
						添加工作流
					</button>
				</div>
			</div>

			{#if workflowsLoading}
				<div class="text-center py-8">
					<div
						class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"
					></div>
				</div>
			{:else if workflows.length === 0}
				<div class="text-center py-8 text-gray-500">
					<div class="mb-2">暂无工作流</div>
					<div class="text-xs">点击"导入示例"或"添加工作流"开始使用</div>
				</div>
			{:else}
				<div class="space-y-2">
					{#each workflows as workflow (workflow.id)}
						<div
							class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-850 rounded-lg"
						>
							<div class="flex items-center space-x-3 flex-1">
								{#if workflow.preview_image}
									<img
										src={workflow.preview_image}
										alt={workflow.name}
										class="w-16 h-16 object-cover rounded-lg border border-gray-300 dark:border-gray-600"
									/>
								{:else}
									<div
										class="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center"
									>
										<svg
											class="w-8 h-8 text-white opacity-70"
											fill="currentColor"
											viewBox="0 0 24 24"
										>
											<path
												fill-rule="evenodd"
												d="M3 6a3 3 0 013-3h2.25a3 3 0 013 3v2.25a3 3 0 01-3 3H6a3 3 0 01-3-3V6zm9.75 0a3 3 0 013-3H18a3 3 0 013 3v2.25a3 3 0 01-3 3h-2.25a3 3 0 01-3-3V6zM3 15.75a3 3 0 013-3h2.25a3 3 0 013 3V18a3 3 0 01-3 3H6a3 3 0 01-3-3v-2.25zm9.75 0a3 3 0 013-3H18a3 3 0 013 3V18a3 3 0 01-3 3h-2.25a3 3 0 01-3-3v-2.25z"
												clip-rule="evenodd"
											/>
										</svg>
									</div>
								{/if}
								<div class="flex-1">
									<div class="font-medium">{workflow.name}</div>
									{#if workflow.description}
										<div class="text-xs text-gray-500 mt-1">{workflow.description}</div>
									{/if}
									<div class="flex items-center space-x-4 mt-2 text-xs text-gray-500">
										<span>积分: {workflow.base_credits}</span>
										<span>倍率: {workflow.complexity_multiplier}</span>
										{#if workflow.category}
											<span>分类: {workflow.category}</span>
										{/if}
										<span
											class="px-2 py-1 rounded {workflow.enabled
												? 'bg-green-100 text-green-800'
												: 'bg-gray-100 text-gray-800'}"
										>
											{workflow.enabled ? '启用' : '禁用'}
										</span>
										{#if workflow.is_public}
											<span class="px-2 py-1 rounded bg-blue-100 text-blue-800">公开</span>
										{/if}
									</div>
								</div>
							</div>
							<div class="flex space-x-2">
								<button
									type="button"
									class="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded"
									on:click={() => openWorkflowModal(workflow)}
								>
									编辑
								</button>
								<button
									type="button"
									class="px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded"
									on:click={() => deleteWorkflow(workflow.id)}
								>
									删除
								</button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<div class="flex justify-end pt-3">
		<button
			class="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-gray-100 transition rounded-lg"
			type="submit"
			disabled={loading}
		>
			{loading ? '保存中...' : '保存'}
		</button>
	</div>
</form>

<!-- 工作流编辑模态框 -->
{#if showWorkflowModal}
	<div
		class="fixed inset-0 bg-gray-900 bg-opacity-50 overflow-y-auto h-full w-full z-50"
		on:click={() => (showWorkflowModal = false)}
	>
		<div
			class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white dark:bg-gray-900"
			on:click|stopPropagation
		>
			<div class="mt-3">
				<div class="flex justify-between items-center mb-4">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
						{editingWorkflow ? '编辑工作流' : '添加工作流'}
					</h3>
					<button
						type="button"
						class="text-gray-400 hover:text-gray-600"
						on:click={() => (showWorkflowModal = false)}
					>
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							></path>
						</svg>
					</button>
				</div>

				<form on:submit|preventDefault={saveWorkflow} class="space-y-4">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label class="block text-sm font-medium mb-1">工作流名称</label>
							<input
								type="text"
								bind:value={workflowForm.name}
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
								required
							/>
						</div>
						<div>
							<label class="block text-sm font-medium mb-1">分类</label>
							<input
								type="text"
								bind:value={workflowForm.category}
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
								placeholder="如：图像处理、换脸等"
							/>
						</div>
					</div>

					<div>
						<label class="block text-sm font-medium mb-1">描述</label>
						<textarea
							bind:value={workflowForm.description}
							class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
							rows="3"
							placeholder="工作流功能描述"
						></textarea>
					</div>

					<div>
						<label class="block text-sm font-medium mb-1">封面图片</label>
						<div class="space-y-3">
							{#if previewImageUrl}
								<div class="relative inline-block">
									<img
										src={previewImageUrl}
										alt="预览图片"
										class="max-w-xs h-32 object-cover rounded-lg border border-gray-300 dark:border-gray-600"
									/>
									<button
										type="button"
										class="absolute top-1 right-1 bg-red-500 hover:bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
										on:click={removePreviewImage}
									>
										×
									</button>
								</div>
							{/if}
							<div>
								<input
									type="file"
									accept="image/*"
									bind:this={fileInput}
									on:change={handleFileSelect}
									class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
								/>
								<div class="text-xs text-gray-500 mt-1">
									支持 JPG、PNG 格式，建议尺寸 400x300，文件大小不超过 5MB
								</div>
							</div>
						</div>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label class="block text-sm font-medium mb-1">模板 UUID</label>
							<input
								type="text"
								bind:value={workflowForm.template_uuid}
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
								placeholder="哩布模板UUID"
								required
							/>
						</div>
						<div>
							<label class="block text-sm font-medium mb-1">工作流 UUID</label>
							<input
								type="text"
								bind:value={workflowForm.workflow_uuid}
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
								placeholder="哩布工作流UUID"
								required
							/>
						</div>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
						<div>
							<label class="block text-sm font-medium mb-1">基础积分</label>
							<input
								type="number"
								bind:value={workflowForm.base_credits}
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
								min="1"
								required
							/>
						</div>
						<div>
							<label class="block text-sm font-medium mb-1">复杂度系数</label>
							<input
								type="number"
								bind:value={workflowForm.complexity_multiplier}
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
								min="0.1"
								max="10"
								step="0.1"
								required
							/>
						</div>
						<div>
							<label class="block text-sm font-medium mb-1">排序权重</label>
							<input
								type="number"
								bind:value={workflowForm.sort_order}
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
							/>
						</div>
					</div>

					<div class="flex items-center space-x-6">
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:checked={workflowForm.enabled}
								class="form-checkbox h-4 w-4 text-blue-600"
							/>
							<span class="ml-2 text-sm">启用工作流</span>
						</label>
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:checked={workflowForm.is_public}
								class="form-checkbox h-4 w-4 text-blue-600"
							/>
							<span class="ml-2 text-sm">公开显示</span>
						</label>
					</div>

					<div>
						<label class="block text-sm font-medium mb-1">参数结构 (Parameter Schema)</label>
						<textarea
							bind:value={workflowForm.parameter_schema}
							class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white font-mono text-xs"
							rows="6"
							placeholder={`{\"fields\": []}`}
							on:blur={validateParameterSchema}
						></textarea>
						<div class="text-xs text-gray-500 mt-1">JSON格式的参数结构定义，用于生成前端表单</div>
					</div>

					<div>
						<label class="block text-sm font-medium mb-1">默认参数 (Default Params)</label>
						<textarea
							bind:value={workflowForm.default_params}
							class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white font-mono text-xs"
							rows="8"
							placeholder={`{
  "27": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}},
  "40": {"class_type": "LoadImage", "inputs": {"image": ""}},
  "workflowUuid": ""
}`}
							on:blur={validateDefaultParams}
						></textarea>
						<div class="text-xs text-gray-500 mt-1">
							JSON格式的默认参数，需包含class_type和workflowUuid
						</div>
					</div>

					<div class="flex justify-end space-x-3 pt-4">
						<button
							type="button"
							class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-white dark:border-gray-600"
							on:click={() => (showWorkflowModal = false)}
						>
							取消
						</button>
						<button
							type="submit"
							class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
						>
							保存
						</button>
					</div>
				</form>
			</div>
		</div>
	</div>
{/if}
