<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let originalImageUrl = '';
	export let maskImageUrl = '';
	export let hasMask = false;

	// 预览图片加载状态
	let imageLoaded = false;
	let maskLoaded = false;

	// Canvas相关变量
	let maskImage: HTMLImageElement;
	let previewCanvas: HTMLCanvasElement;

	const handleImageLoad = () => {
		imageLoaded = true;
	};

	const handleMaskLoad = () => {
		maskLoaded = true;
	};

	const handleEditMask = () => {
		dispatch('edit-mask');
	};

	const handleClearMask = () => {
		if (confirm('确定要清除当前的蒙版标记吗？')) {
			dispatch('clear-mask');
		}
	};

	// 当蒙版图片加载完成后，生成预览效果
	$: if (maskLoaded && previewCanvas && maskImage) {
		generateMaskPreview();
	}

	const generateMaskPreview = () => {
		if (!previewCanvas || !maskImage) return;

		const canvas = previewCanvas;
		const ctx = canvas.getContext('2d');
		if (!ctx) return;

		// 设置canvas尺寸匹配容器
		const rect = canvas.getBoundingClientRect();
		canvas.width = rect.width;
		canvas.height = rect.height;

		// 清除画布
		ctx.clearRect(0, 0, canvas.width, canvas.height);

		// 简化处理：直接绘制蒙版图片并应用红色滤镜
		// 避免CORS问题，使用CSS滤镜和混合模式来实现红色覆盖效果
		try {
			// 绘制蒙版图片
			ctx.drawImage(maskImage, 0, 0, canvas.width, canvas.height);

			// 在蒙版上方绘制红色半透明层
			ctx.globalCompositeOperation = 'source-atop';
			ctx.fillStyle = 'rgba(255, 0, 0, 0.6)';
			ctx.fillRect(0, 0, canvas.width, canvas.height);

			// 重置混合模式
			ctx.globalCompositeOperation = 'source-over';
		} catch (error) {
			console.warn('绘制蒙版预览时出错:', error);
			// 完全降级：只显示红色半透明矩形表示有蒙版
			ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
			ctx.fillRect(0, 0, canvas.width, canvas.height);
		}
	};
</script>

<div class="space-y-3">
	<div class="flex items-center justify-between">
		<label class="text-xs font-medium text-gray-700 dark:text-gray-300"> 蒙版预览 </label>
		{#if hasMask}
			<div class="flex items-center space-x-2">
				<button
					on:click={handleEditMask}
					class="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 dark:bg-blue-900 dark:hover:bg-blue-800 dark:text-blue-300 rounded transition"
				>
					重新编辑
				</button>
				<button
					on:click={handleClearMask}
					class="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-700 dark:bg-red-900 dark:hover:bg-red-800 dark:text-red-300 rounded transition"
				>
					清除
				</button>
			</div>
		{/if}
	</div>

	<!-- 预览区域 -->
	<div
		class="relative bg-gray-100 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden"
	>
		{#if originalImageUrl}
			<!-- 原图 -->
			<img
				src={originalImageUrl}
				alt="原图"
				class="w-full h-40 object-cover"
				crossorigin="anonymous"
				on:load={handleImageLoad}
			/>

			<!-- 蒙版叠加层 -->
			{#if hasMask && maskImageUrl}
				<div class="absolute inset-0">
					<!-- 创建蒙版叠加效果 -->
					<div class="relative w-full h-full">
						<img
							src={maskImageUrl}
							alt="蒙版"
							class="absolute inset-0 w-full h-full object-cover opacity-0"
							crossorigin="anonymous"
							on:load={handleMaskLoad}
							bind:this={maskImage}
						/>
						<canvas
							bind:this={previewCanvas}
							class="absolute inset-0 w-full h-full"
							style="mix-blend-mode: multiply;"
						></canvas>
					</div>
				</div>
			{/if}

			<!-- 状态指示器 -->
			<div class="absolute top-2 left-2">
				{#if hasMask}
					<span
						class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
					>
						✓ 已标记
					</span>
				{:else}
					<span
						class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300"
					>
						未标记
					</span>
				{/if}
			</div>

			<!-- 编辑按钮覆盖层 -->
			{#if !hasMask}
				<div
					class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-20 hover:bg-opacity-30 transition-all duration-200"
				>
					<button
						on:click={handleEditMask}
						class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg shadow-lg transition flex items-center space-x-2"
					>
						<span>🎨</span>
						<span>开始涂抹</span>
					</button>
				</div>
			{/if}
		{:else}
			<!-- 无图片状态 -->
			<div class="w-full h-40 flex items-center justify-center text-gray-400 dark:text-gray-500">
				<div class="text-center">
					<div class="text-2xl mb-2">📷</div>
					<div class="text-sm">请先上传图片</div>
				</div>
			</div>
		{/if}
	</div>

	<!-- 蒙版说明 -->
	{#if hasMask}
		<div class="text-xs text-gray-500 dark:text-gray-400">
			✅ 红色区域已标记为待消除区域，可重新编辑或清除后重新标记
		</div>
	{:else if originalImageUrl}
		<div class="text-xs text-gray-500 dark:text-gray-400">
			💡 点击"开始涂抹"按钮标记需要消除的区域
		</div>
	{/if}
</div>
