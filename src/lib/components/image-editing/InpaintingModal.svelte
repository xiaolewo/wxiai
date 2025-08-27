<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';

	const dispatch = createEventDispatcher();

	export let show = false;
	export let originalImageUrl = '';
	export let existingMaskData: string | null = null; // 已有的蒙版数据

	// 画布相关
	let canvasContainer: HTMLDivElement;
	let canvas: HTMLCanvasElement;
	let ctx: CanvasRenderingContext2D | null = null;
	let maskCanvas: HTMLCanvasElement;
	let maskCtx: CanvasRenderingContext2D | null = null;
	let originalImage: HTMLImageElement | null = null;

	// 涂抹状态
	let isDrawing = false;
	let brushSize = 25;
	let brushOpacity = 0.7;

	// 历史记录（用于撤销功能）
	let maskHistory: ImageData[] = [];
	let historyIndex = -1;
	let maxHistorySize = 10;

	// 加载图片并初始化画布
	onMount(() => {
		if (originalImageUrl && show) {
			loadImageAndInitCanvas();
		}
	});

	$: if (originalImageUrl && show) {
		loadImageAndInitCanvas();
	}

	const loadImageAndInitCanvas = () => {
		if (!originalImageUrl) return;

		originalImage = new Image();
		originalImage.crossOrigin = 'anonymous';
		originalImage.onload = () => {
			initializeCanvas();
			// 如果有已存在的蒙版，加载它
			if (existingMaskData) {
				loadExistingMask();
			}
		};
		originalImage.src = originalImageUrl;
	};

	const initializeCanvas = () => {
		if (!canvas || !originalImage) return;

		ctx = canvas.getContext('2d');
		if (!ctx) return;

		// 计算画布尺寸 - 最大尺寸为屏幕的80%
		const maxWidth = Math.min(window.innerWidth * 0.8, 900);
		const maxHeight = Math.min(window.innerHeight * 0.7, 600);

		// 保持图片比例
		const imageAspect = originalImage.width / originalImage.height;
		const maxAspect = maxWidth / maxHeight;

		let canvasWidth: number, canvasHeight: number;
		if (imageAspect > maxAspect) {
			canvasWidth = maxWidth;
			canvasHeight = maxWidth / imageAspect;
		} else {
			canvasHeight = maxHeight;
			canvasWidth = maxHeight * imageAspect;
		}

		// 设置画布尺寸
		canvas.width = canvasWidth;
		canvas.height = canvasHeight;

		// 绘制原图
		ctx.drawImage(originalImage, 0, 0, canvasWidth, canvasHeight);

		// 初始化蒙版画布（实际图片尺寸）
		if (!maskCanvas) {
			maskCanvas = document.createElement('canvas');
		}
		maskCanvas.width = originalImage.width;
		maskCanvas.height = originalImage.height;
		maskCtx = maskCanvas.getContext('2d');

		if (maskCtx) {
			// 蒙版画布默认为黑色（保留区域）
			maskCtx.fillStyle = 'black';
			maskCtx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);

			// 保存初始状态到历史记录
			saveToHistory();
		}
	};

	const loadExistingMask = () => {
		// TODO: 如果有已存在的蒙版数据，在这里加载并显示
		// 这个功能可以后续添加，用于编辑已有的蒙版
	};

	// 历史记录管理
	const saveToHistory = () => {
		if (!maskCtx || !maskCanvas) return;

		const imageData = maskCtx.getImageData(0, 0, maskCanvas.width, maskCanvas.height);

		// 如果不是在历史记录的末尾，移除后面的记录
		if (historyIndex < maskHistory.length - 1) {
			maskHistory = maskHistory.slice(0, historyIndex + 1);
		}

		// 添加新记录
		maskHistory.push(imageData);
		if (maskHistory.length > maxHistorySize) {
			maskHistory.shift();
		} else {
			historyIndex++;
		}
	};

	const undo = () => {
		if (historyIndex > 0 && maskCtx) {
			historyIndex--;
			maskCtx.putImageData(maskHistory[historyIndex], 0, 0);
			redrawCanvas();
		}
	};

	const redo = () => {
		if (historyIndex < maskHistory.length - 1 && maskCtx) {
			historyIndex++;
			maskCtx.putImageData(maskHistory[historyIndex], 0, 0);
			redrawCanvas();
		}
	};

	// 重新绘制显示画布
	const redrawCanvas = () => {
		if (!ctx || !originalImage || !maskCtx || !canvas || !maskCanvas) return;

		// 清除画布
		ctx.clearRect(0, 0, canvas.width, canvas.height);

		// 重新绘制原图
		ctx.drawImage(originalImage, 0, 0, canvas.width, canvas.height);

		// 绘制蒙版覆盖层
		const tempCanvas = document.createElement('canvas');
		tempCanvas.width = canvas.width;
		tempCanvas.height = canvas.height;
		const tempCtx = tempCanvas.getContext('2d');

		if (tempCtx) {
			// 将蒙版缩放到显示尺寸
			tempCtx.drawImage(maskCanvas, 0, 0, canvas.width, canvas.height);

			// 将白色区域（待消除）显示为红色半透明
			const imageData = tempCtx.getImageData(0, 0, canvas.width, canvas.height);
			const data = imageData.data;

			for (let i = 0; i < data.length; i += 4) {
				const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
				if (brightness > 128) {
					// 白色区域
					data[i] = 255; // R
					data[i + 1] = 0; // G
					data[i + 2] = 0; // B
					data[i + 3] = brushOpacity * 255; // A
				} else {
					data[i + 3] = 0; // 透明
				}
			}

			tempCtx.putImageData(imageData, 0, 0);
			ctx.drawImage(tempCanvas, 0, 0);
		}
	};

	// 鼠标/触摸事件处理
	const startDrawing = (event: MouseEvent | TouchEvent) => {
		isDrawing = true;
		draw(event);
		// 开始新的涂抹操作前保存状态
		saveToHistory();
	};

	const stopDrawing = () => {
		isDrawing = false;
	};

	const draw = (event: MouseEvent | TouchEvent) => {
		if (!isDrawing || !ctx || !maskCtx || !canvas) return;

		const rect = canvas.getBoundingClientRect();
		let clientX: number, clientY: number;

		if (event instanceof MouseEvent) {
			clientX = event.clientX;
			clientY = event.clientY;
		} else {
			clientX = event.touches[0].clientX;
			clientY = event.touches[0].clientY;
		}

		const x = clientX - rect.left;
		const y = clientY - rect.top;

		// 在显示画布上绘制红色涂抹
		ctx.globalCompositeOperation = 'source-over';
		ctx.fillStyle = `rgba(255, 0, 0, ${brushOpacity})`;
		ctx.beginPath();
		ctx.arc(x, y, brushSize / 2, 0, Math.PI * 2);
		ctx.fill();

		// 在蒙版画布上绘制白色（待消除区域）
		const scaleX = maskCanvas.width / canvas.width;
		const scaleY = maskCanvas.height / canvas.height;
		const maskX = x * scaleX;
		const maskY = y * scaleY;

		maskCtx.fillStyle = 'white';
		maskCtx.beginPath();
		maskCtx.arc(maskX, maskY, (brushSize / 2) * scaleX, 0, Math.PI * 2);
		maskCtx.fill();
	};

	const clearMask = () => {
		if (!ctx || !maskCtx || !originalImage) return;

		// 重置蒙版画布为黑色
		maskCtx.fillStyle = 'black';
		maskCtx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);

		// 重新绘制显示画布
		ctx.clearRect(0, 0, canvas.width, canvas.height);
		ctx.drawImage(originalImage, 0, 0, canvas.width, canvas.height);

		// 保存清除状态
		saveToHistory();
	};

	// 确定按钮 - 将蒙版数据返回给父组件
	const handleConfirm = async () => {
		if (!maskCanvas) {
			dispatch('close');
			return;
		}

		try {
			// 将蒙版画布转换为blob
			const blob = await new Promise<Blob | null>((resolve) => {
				maskCanvas.toBlob(resolve, 'image/png');
			});

			if (blob) {
				dispatch('confirm', { maskBlob: blob });
			}
		} catch (error) {
			console.error('生成蒙版失败:', error);
		}

		show = false;
	};

	const handleCancel = () => {
		dispatch('close');
		show = false;
	};

	// 键盘快捷键
	const handleKeydown = (event: KeyboardEvent) => {
		if (!show) return;

		if (event.ctrlKey || event.metaKey) {
			if (event.key === 'z' && !event.shiftKey) {
				event.preventDefault();
				undo();
			} else if ((event.key === 'z' && event.shiftKey) || event.key === 'y') {
				event.preventDefault();
				redo();
			}
		} else if (event.key === 'Escape') {
			event.preventDefault();
			handleCancel();
		}
	};
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show}
	<!-- 弹窗遮罩 -->
	<div class="fixed inset-0 z-[60] flex items-center justify-center bg-black bg-opacity-50">
		<!-- 弹窗内容 -->
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-[95vw] max-h-[95vh] flex flex-col"
		>
			<!-- 弹窗头部 -->
			<div
				class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-600"
			>
				<div>
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white">🎨 涂抹编辑器</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">用红色画笔标记需要消除的区域</p>
				</div>
				<button
					on:click={handleCancel}
					class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
				>
					×
				</button>
			</div>

			<!-- 工具栏 -->
			<div
				class="px-6 py-3 border-b border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700"
			>
				<div class="flex items-center justify-between">
					<!-- 左侧工具 -->
					<div class="flex items-center space-x-4">
						<!-- 画笔大小 -->
						<div class="flex items-center space-x-2">
							<label class="text-sm text-gray-600 dark:text-gray-400">画笔:</label>
							<input type="range" bind:value={brushSize} min="5" max="100" class="w-24" />
							<span class="text-sm text-gray-600 dark:text-gray-400 w-8">{brushSize}</span>
						</div>

						<!-- 透明度 -->
						<div class="flex items-center space-x-2">
							<label class="text-sm text-gray-600 dark:text-gray-400">透明度:</label>
							<input
								type="range"
								bind:value={brushOpacity}
								min="0.1"
								max="1"
								step="0.1"
								class="w-20"
							/>
							<span class="text-sm text-gray-600 dark:text-gray-400 w-8">{brushOpacity}</span>
						</div>
					</div>

					<!-- 右侧操作按钮 -->
					<div class="flex items-center space-x-2">
						<button
							on:click={undo}
							disabled={historyIndex <= 0}
							class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 dark:disabled:bg-gray-700 rounded transition"
							title="撤销 (Ctrl+Z)"
						>
							撤销
						</button>
						<button
							on:click={redo}
							disabled={historyIndex >= maskHistory.length - 1}
							class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 dark:disabled:bg-gray-700 rounded transition"
							title="重做 (Ctrl+Y)"
						>
							重做
						</button>
						<button
							on:click={clearMask}
							class="px-3 py-1.5 text-sm bg-red-100 hover:bg-red-200 text-red-700 dark:bg-red-900 dark:hover:bg-red-800 dark:text-red-300 rounded transition"
						>
							清除全部
						</button>
					</div>
				</div>
			</div>

			<!-- 画布区域 -->
			<div class="flex-1 p-6 flex items-center justify-center min-h-0">
				<div
					bind:this={canvasContainer}
					class="relative bg-gray-100 dark:bg-gray-700 rounded-lg shadow-inner"
				>
					<canvas
						bind:this={canvas}
						class="block rounded-lg cursor-crosshair"
						on:mousedown={startDrawing}
						on:mousemove={draw}
						on:mouseup={stopDrawing}
						on:mouseleave={stopDrawing}
						on:touchstart|preventDefault={startDrawing}
						on:touchmove|preventDefault={draw}
						on:touchend|preventDefault={stopDrawing}
						style="max-width: 100%; max-height: 100%;"
					></canvas>
				</div>
			</div>

			<!-- 操作提示 -->
			<div class="px-6 py-2 text-center">
				<p class="text-sm text-gray-500 dark:text-gray-400">
					💡 提示：用画笔标记红色区域将被AI消除 • 支持 Ctrl+Z 撤销 • ESC 取消
				</p>
			</div>

			<!-- 底部按钮 -->
			<div
				class="flex items-center justify-end space-x-3 px-6 py-4 border-t border-gray-200 dark:border-gray-600"
			>
				<button
					on:click={handleCancel}
					class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition"
				>
					取消
				</button>
				<button
					on:click={handleConfirm}
					class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition"
				>
					确定
				</button>
			</div>
		</div>
	</div>
{/if}
