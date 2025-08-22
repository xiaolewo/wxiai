<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Spinner from './Spinner.svelte';

	const dispatch = createEventDispatcher();

	export let show = false;
	export let imageFile: File | null = null;
	export let isProcessing = false;

	// Canvas 相关
	let canvasContainer: HTMLDivElement;
	let originalCanvas: HTMLCanvasElement;
	let maskCanvas: HTMLCanvasElement;
	let isDrawing = false;
	let brushSize = 20;
	let showMask = true;

	// 绘图参数
	let steps = 50; // 增加采样步数
	let strength = 1.0; // 增加强度到最大
	let scale = 15.0; // 增加文本描述程度
	let quality = 'H'; // 使用高质量
	let dilateSize = 25; // 增加膨胀半径

	onMount(() => {
		// Canvas初始化通过响应式语句处理
		console.log('🎨 InpaintingModal组件已挂载');
	});

	let hasInitialized = false;

	$: if (show && imageFile && originalCanvas && maskCanvas && !hasInitialized) {
		displayImageOnCanvas();
		hasInitialized = true;
	}

	// 重置初始化标志当模态框关闭时
	$: if (!show) {
		hasInitialized = false;
	}

	const displayImageOnCanvas = () => {
		if (!imageFile || !originalCanvas || !maskCanvas) {
			console.log('🎨 Canvas初始化检查:', {
				imageFile: !!imageFile,
				originalCanvas: !!originalCanvas,
				maskCanvas: !!maskCanvas
			});
			return;
		}

		console.log('🎨 开始加载图片到Canvas:', imageFile.name);

		const reader = new FileReader();
		reader.onload = (e) => {
			const img = new Image();
			img.onload = () => {
				console.log('🎨 图片加载成功，原始尺寸:', img.width, 'x', img.height);

				// 使用标准尺寸以确保AI模型兼容性
				let { width, height } = img;
				const aspect = width / height;

				// 选择合适的标准尺寸 (常见AI模型支持的尺寸)
				if (aspect >= 1.5) {
					// 横向图片
					width = 512;
					height = 384;
				} else if (aspect <= 0.7) {
					// 纵向图片
					width = 384;
					height = 512;
				} else {
					// 接近正方形
					width = 512;
					height = 512;
				}

				console.log('🎨 使用标准AI尺寸:', width, 'x', height, '(宽高比:', aspect.toFixed(2), ')');

				// 设置原图canvas
				originalCanvas.width = width;
				originalCanvas.height = height;
				originalCanvas.style.width = `${width}px`;
				originalCanvas.style.height = `${height}px`;
				const ctx = originalCanvas.getContext('2d');
				ctx.drawImage(img, 0, 0, width, height);

				// 设置mask canvas
				maskCanvas.width = width;
				maskCanvas.height = height;
				maskCanvas.style.width = `${width}px`;
				maskCanvas.style.height = `${height}px`;
				const maskCtx = maskCanvas.getContext('2d');
				maskCtx.clearRect(0, 0, width, height);

				// 设置容器尺寸
				if (canvasContainer) {
					canvasContainer.style.width = `${width}px`;
					canvasContainer.style.height = `${height}px`;
				}

				// 初始化绘图事件
				initCanvasDrawing();
			};
			img.src = e.target.result as string;
		};
		reader.readAsDataURL(imageFile);
	};

	let lastX = 0;
	let lastY = 0;

	const initCanvasDrawing = () => {
		if (!maskCanvas) return;

		// 清除之前的事件监听器（如果存在）
		// 这里简单地重新绑定，因为函数在内部定义

		const ctx = maskCanvas.getContext('2d');

		// 设置绘制样式
		ctx.globalCompositeOperation = 'source-over';
		ctx.fillStyle = 'rgba(255, 0, 0, 0.8)'; // 更明显的红色
		ctx.strokeStyle = 'rgba(255, 0, 0, 0.8)';
		ctx.lineJoin = 'round';
		ctx.lineCap = 'round';

		const startDrawing = (e: MouseEvent) => {
			isDrawing = true;
			const coords = getCanvasCoordinates(e);
			lastX = coords.x;
			lastY = coords.y;

			// 绘制起始点
			ctx.lineWidth = brushSize;
			ctx.beginPath();
			ctx.arc(coords.x, coords.y, brushSize / 2, 0, 2 * Math.PI);
			ctx.fill();

			console.log('🎨 开始绘制，坐标:', coords.x, coords.y, '画笔大小:', brushSize);
			console.log('🎨 Canvas尺寸:', maskCanvas.width, 'x', maskCanvas.height);
			console.log('🎨 showMask状态:', showMask);
		};

		const draw = (e: MouseEvent) => {
			if (!isDrawing) return;

			const coords = getCanvasCoordinates(e);

			// 绘制连线
			ctx.lineWidth = brushSize;
			ctx.beginPath();
			ctx.moveTo(lastX, lastY);
			ctx.lineTo(coords.x, coords.y);
			ctx.stroke();

			// 绘制当前点
			ctx.beginPath();
			ctx.arc(coords.x, coords.y, brushSize / 2, 0, 2 * Math.PI);
			ctx.fill();

			lastX = coords.x;
			lastY = coords.y;
		};

		const stopDrawing = () => {
			if (isDrawing) {
				console.log('🎨 停止绘制');
				isDrawing = false;
			}
		};

		const getCanvasCoordinates = (e: MouseEvent) => {
			const rect = maskCanvas.getBoundingClientRect();
			const scaleX = maskCanvas.width / rect.width;
			const scaleY = maskCanvas.height / rect.height;

			return {
				x: (e.clientX - rect.left) * scaleX,
				y: (e.clientY - rect.top) * scaleY
			};
		};

		// 触摸事件处理函数
		const handleTouchStart = (e: TouchEvent) => {
			e.preventDefault();
			const touch = e.touches[0];
			const mouseEvent = new MouseEvent('mousedown', {
				clientX: touch.clientX,
				clientY: touch.clientY
			});
			startDrawing(mouseEvent);
		};

		const handleTouchMove = (e: TouchEvent) => {
			e.preventDefault();
			const touch = e.touches[0];
			const mouseEvent = new MouseEvent('mousemove', {
				clientX: touch.clientX,
				clientY: touch.clientY
			});
			draw(mouseEvent);
		};

		const handleTouchEnd = (e: TouchEvent) => {
			e.preventDefault();
			stopDrawing();
		};

		// 绑定鼠标事件
		maskCanvas.addEventListener('mousedown', startDrawing);
		maskCanvas.addEventListener('mousemove', draw);
		maskCanvas.addEventListener('mouseup', stopDrawing);
		maskCanvas.addEventListener('mouseout', stopDrawing);
		maskCanvas.addEventListener('mouseleave', stopDrawing);

		// 绑定触摸事件
		maskCanvas.addEventListener('touchstart', handleTouchStart, { passive: false });
		maskCanvas.addEventListener('touchmove', handleTouchMove, { passive: false });
		maskCanvas.addEventListener('touchend', handleTouchEnd, { passive: false });
		maskCanvas.addEventListener('touchcancel', handleTouchEnd, { passive: false });

		console.log('🎨 Canvas绘制事件已初始化');
	};

	const clearMask = () => {
		if (maskCanvas) {
			const ctx = maskCanvas.getContext('2d');
			ctx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
			console.log('🎨 Mask已清除');
		}
	};

	// 测试绘制功能
	const testDraw = () => {
		if (maskCanvas) {
			const ctx = maskCanvas.getContext('2d');
			ctx.fillStyle = 'rgba(255, 0, 0, 1)'; // 完全不透明的红色
			ctx.fillRect(50, 50, 100, 100);
			ctx.fillStyle = 'rgba(0, 255, 0, 1)'; // 绿色圆形
			ctx.beginPath();
			ctx.arc(200, 200, 50, 0, 2 * Math.PI);
			ctx.fill();
			console.log('🎨 测试绘制完成 - 应该看到红色方块和绿色圆形');
		}
	};

	// 下载mask数据用于调试
	const downloadMask = () => {
		if (!maskCanvas) return;

		const maskDataUrl = generateMaskData();
		const link = document.createElement('a');
		link.download = 'mask-debug.png';
		link.href = maskDataUrl;
		link.click();
		console.log('🎨 Mask已下载，可以查看生成的mask图片');
	};

	const generateMaskData = () => {
		if (!maskCanvas) return '';

		// 创建临时canvas来生成黑白mask
		const tempCanvas = document.createElement('canvas');
		tempCanvas.width = maskCanvas.width;
		tempCanvas.height = maskCanvas.height;
		const tempCtx = tempCanvas.getContext('2d');

		// 获取mask canvas的数据
		const imageData = maskCanvas
			.getContext('2d')
			.getImageData(0, 0, maskCanvas.width, maskCanvas.height);
		const data = imageData.data;

		let whitePixels = 0;
		let totalPixels = data.length / 4;

		// 转换为黑白mask: 有内容的地方变白色(255)，其他地方黑色(0)
		for (let i = 0; i < data.length; i += 4) {
			const alpha = data[i + 3];
			if (alpha > 0) {
				data[i] = 255; // R
				data[i + 1] = 255; // G
				data[i + 2] = 255; // B
				data[i + 3] = 255; // A
				whitePixels++;
			} else {
				data[i] = 0; // R
				data[i + 1] = 0; // G
				data[i + 2] = 0; // B
				data[i + 3] = 255; // A
			}
		}

		console.log('🎨 Mask统计:', {
			总像素: totalPixels,
			白色像素: whitePixels,
			涂抹覆盖率: `${((whitePixels / totalPixels) * 100).toFixed(2)}%`
		});

		tempCtx.putImageData(imageData, 0, 0);
		return tempCanvas.toDataURL('image/png');
	};

	const handleSubmit = () => {
		if (!maskCanvas || !originalCanvas) {
			toast.error('Canvas未初始化');
			return;
		}

		// 检查是否有涂抹内容
		const imageData = maskCanvas
			.getContext('2d')
			.getImageData(0, 0, maskCanvas.width, maskCanvas.height);
		const data = imageData.data;
		let hasMask = false;

		for (let i = 3; i < data.length; i += 4) {
			// 检查alpha通道
			if (data[i] > 0) {
				hasMask = true;
				break;
			}
		}

		if (!hasMask) {
			toast.error('请先在图片上涂抹需要消除的区域');
			return;
		}

		console.log('🎨 检测到涂抹内容，生成缩放后的输入图片和mask数据');

		// 生成缩放后的输入图片Base64 (与mask相同尺寸)
		const scaledInputImageBase64 = originalCanvas.toDataURL('image/jpeg', 0.9).split(',')[1];

		// 生成mask数据
		const maskDataUrl = generateMaskData();
		const maskImageBase64 = maskDataUrl.split(',')[1];

		console.log('🎨 缩放后输入图片Base64长度:', scaledInputImageBase64.length);
		console.log('🎨 Mask数据Base64长度:', maskImageBase64.length);
		console.log('🎨 Canvas尺寸:', originalCanvas.width, 'x', originalCanvas.height);
		console.log('🎨 Mask Canvas尺寸:', maskCanvas.width, 'x', maskCanvas.height);

		dispatch('submit', {
			scaledInputImageBase64, // 使用缩放后的输入图片
			maskImageBase64,
			parameters: {
				steps,
				strength,
				scale,
				quality,
				dilateSize
			}
		});
	};

	const handleClose = () => {
		show = false;
		dispatch('close');
	};

	onDestroy(() => {
		// Canvas事件会在组件销毁时自动清理
		console.log('🎨 InpaintingModal组件销毁');
	});
</script>

{#if show}
	<!-- 弹窗背景 -->
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
		<!-- 弹窗内容 -->
		<div class="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
			<!-- 弹窗头部 -->
			<div
				class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-600"
			>
				<h2 class="text-xl font-semibold">涂抹需要消除的区域</h2>
				<button
					on:click={handleClose}
					class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
					disabled={isProcessing}
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

			<!-- 弹窗主体 -->
			<div class="p-4 overflow-y-auto" style="max-height: calc(90vh - 160px);">
				<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
					<!-- 左侧：图片涂抹区域 -->
					<div class="lg:col-span-2">
						<div class="space-y-4">
							<!-- Canvas区域 -->
							<div
								class="relative border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700"
							>
								<div
									bind:this={canvasContainer}
									class="relative min-h-[300px] flex items-center justify-center"
								>
									<canvas bind:this={originalCanvas} class="absolute top-0 left-0 z-10"></canvas>
									<canvas
										bind:this={maskCanvas}
										class="absolute top-0 left-0 z-20 cursor-crosshair {showMask
											? 'opacity-70'
											: 'opacity-0'}"
									></canvas>
								</div>
							</div>

							<!-- 绘图工具 -->
							<div
								class="flex items-center justify-between bg-gray-50 dark:bg-gray-700 p-3 rounded-lg"
							>
								<div class="flex items-center space-x-4">
									<div class="flex items-center space-x-2">
										<label class="text-sm text-gray-600 dark:text-gray-400">画笔大小:</label>
										<input type="range" bind:value={brushSize} min="5" max="50" class="w-20" />
										<span class="text-sm text-gray-600 dark:text-gray-400 w-8">{brushSize}px</span>
									</div>
								</div>

								<div class="flex items-center space-x-2">
									<button
										on:click={clearMask}
										class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 rounded transition-colors"
									>
										清除涂抹
									</button>
									<button
										on:click={testDraw}
										class="px-3 py-1 text-sm bg-blue-200 hover:bg-blue-300 dark:bg-blue-600 dark:hover:bg-blue-500 rounded transition-colors"
									>
										测试绘制
									</button>
									<button
										on:click={downloadMask}
										class="px-3 py-1 text-sm bg-green-200 hover:bg-green-300 dark:bg-green-600 dark:hover:bg-green-500 rounded transition-colors"
									>
										下载Mask
									</button>
									<button
										on:click={() => (showMask = !showMask)}
										class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 rounded transition-colors"
									>
										{showMask ? '隐藏涂抹' : '显示涂抹'}
									</button>
								</div>
							</div>
						</div>
					</div>

					<!-- 右侧：参数设置 -->
					<div class="space-y-4">
						<h3 class="font-medium text-gray-700 dark:text-gray-300">生成参数</h3>

						<div>
							<label class="text-sm text-gray-600 dark:text-gray-400">采样步数: {steps}</label>
							<input type="range" bind:value={steps} min="10" max="50" class="w-full mt-1" />
						</div>

						<div>
							<label class="text-sm text-gray-600 dark:text-gray-400">强度: {strength}</label>
							<input
								type="range"
								bind:value={strength}
								min="0.1"
								max="1.0"
								step="0.1"
								class="w-full mt-1"
							/>
						</div>

						<div>
							<label class="text-sm text-gray-600 dark:text-gray-400">文本描述程度: {scale}</label>
							<input type="range" bind:value={scale} min="1" max="20" class="w-full mt-1" />
						</div>

						<div>
							<label class="text-sm text-gray-600 dark:text-gray-400">质量</label>
							<select
								bind:value={quality}
								class="w-full mt-1 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-800 dark:text-white"
							>
								<option value="L">低质量 (快速)</option>
								<option value="M">中质量</option>
								<option value="H">高质量 (慢速)</option>
							</select>
						</div>

						<div>
							<label class="text-sm text-gray-600 dark:text-gray-400">膨胀半径: {dilateSize}</label>
							<input type="range" bind:value={dilateSize} min="0" max="50" class="w-full mt-1" />
						</div>
					</div>
				</div>
			</div>

			<!-- 弹窗底部 -->
			<div
				class="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-600"
			>
				<div class="text-sm text-gray-500 dark:text-gray-400">
					提示：用鼠标在图片上涂抹需要消除的区域，红色区域将被处理
				</div>

				<div class="flex items-center space-x-3">
					<button
						on:click={handleClose}
						class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
						disabled={isProcessing}
					>
						取消
					</button>
					<button
						on:click={handleSubmit}
						disabled={isProcessing}
						class="px-6 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded transition-colors flex items-center gap-2"
					>
						{#if isProcessing}
							<Spinner className="size-4" />
							处理中...
						{:else}
							开始消除
						{/if}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	canvas {
		border: 1px solid #d1d5db;
	}

	.dark canvas {
		border-color: #4b5563;
	}
</style>
