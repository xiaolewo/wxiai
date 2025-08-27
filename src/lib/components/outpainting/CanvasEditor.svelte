<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';

	export let show: boolean = false;
	export let originalImageUrl: string = '';

	const dispatch = createEventDispatcher();

	let canvas: HTMLCanvasElement;
	let ctx: CanvasRenderingContext2D | null = null;
	let originalImage: HTMLImageElement | null = null;
	let maskCanvas: HTMLCanvasElement;
	let maskCtx: CanvasRenderingContext2D | null = null;

	// Canvas dimensions
	let canvasWidth = 800;
	let canvasHeight = 600;

	// Image position and size
	let imageX = 200;
	let imageY = 150;
	let imageWidth = 400;
	let imageHeight = 300;

	// Dragging state
	let isDragging = false;
	let dragStartX = 0;
	let dragStartY = 0;
	let dragStartImageX = 0;
	let dragStartImageY = 0;

	// Resizing state
	let isResizing = false;
	let resizeHandle = '';
	let resizeStartX = 0;
	let resizeStartY = 0;
	let resizeStartWidth = 0;
	let resizeStartHeight = 0;

	onMount(() => {
		if (canvas) {
			ctx = canvas.getContext('2d');
			canvas.width = canvasWidth;
			canvas.height = canvasHeight;
		}

		if (maskCanvas) {
			maskCtx = maskCanvas.getContext('2d');
			maskCanvas.width = canvasWidth;
			maskCanvas.height = canvasHeight;
		}

		loadImage();
	});

	const loadImage = () => {
		if (!originalImageUrl) return;

		originalImage = new Image();
		originalImage.crossOrigin = 'anonymous';
		originalImage.onload = () => {
			// Calculate initial size and position
			const imgAspect = originalImage!.width / originalImage!.height;

			if (imgAspect > 1) {
				// Wide image
				imageWidth = Math.min(400, canvasWidth * 0.5);
				imageHeight = imageWidth / imgAspect;
			} else {
				// Tall image
				imageHeight = Math.min(300, canvasHeight * 0.5);
				imageWidth = imageHeight * imgAspect;
			}

			// Center the image
			imageX = (canvasWidth - imageWidth) / 2;
			imageY = (canvasHeight - imageHeight) / 2;

			redrawCanvas();
		};
		originalImage.src = originalImageUrl;
	};

	const redrawCanvas = () => {
		if (!ctx || !originalImage) return;

		// Clear canvas
		ctx.clearRect(0, 0, canvasWidth, canvasHeight);

		// Draw background (expansion area)
		ctx.fillStyle = 'rgba(59, 130, 246, 0.1)';
		ctx.fillRect(0, 0, canvasWidth, canvasHeight);

		// Draw grid
		drawGrid();

		// Draw image
		ctx.drawImage(originalImage, imageX, imageY, imageWidth, imageHeight);

		// Draw image border
		ctx.strokeStyle = 'rgba(34, 197, 94, 0.8)';
		ctx.lineWidth = 2;
		ctx.strokeRect(imageX, imageY, imageWidth, imageHeight);

		// Draw resize handles
		drawResizeHandles();

		// Draw canvas border
		ctx.strokeStyle = 'rgba(59, 130, 246, 0.8)';
		ctx.lineWidth = 2;
		ctx.setLineDash([10, 5]);
		ctx.strokeRect(0, 0, canvasWidth, canvasHeight);
		ctx.setLineDash([]);

		// Update mask canvas
		updateMaskCanvas();
	};

	const drawGrid = () => {
		if (!ctx) return;

		ctx.strokeStyle = 'rgba(156, 163, 175, 0.3)';
		ctx.lineWidth = 1;

		// Vertical lines
		for (let x = 0; x <= canvasWidth; x += 50) {
			ctx.beginPath();
			ctx.moveTo(x, 0);
			ctx.lineTo(x, canvasHeight);
			ctx.stroke();
		}

		// Horizontal lines
		for (let y = 0; y <= canvasHeight; y += 50) {
			ctx.beginPath();
			ctx.moveTo(0, y);
			ctx.lineTo(canvasWidth, y);
			ctx.stroke();
		}
	};

	const drawResizeHandles = () => {
		if (!ctx) return;

		const handleSize = 8;
		ctx.fillStyle = 'rgba(34, 197, 94, 0.8)';
		ctx.strokeStyle = 'white';
		ctx.lineWidth = 2;

		// Corner handles
		const handles = [
			{ x: imageX - handleSize / 2, y: imageY - handleSize / 2, cursor: 'nw-resize', handle: 'nw' },
			{
				x: imageX + imageWidth - handleSize / 2,
				y: imageY - handleSize / 2,
				cursor: 'ne-resize',
				handle: 'ne'
			},
			{
				x: imageX - handleSize / 2,
				y: imageY + imageHeight - handleSize / 2,
				cursor: 'sw-resize',
				handle: 'sw'
			},
			{
				x: imageX + imageWidth - handleSize / 2,
				y: imageY + imageHeight - handleSize / 2,
				cursor: 'se-resize',
				handle: 'se'
			}
		];

		handles.forEach((handle) => {
			ctx.fillRect(handle.x, handle.y, handleSize, handleSize);
			ctx.strokeRect(handle.x, handle.y, handleSize, handleSize);
		});
	};

	const updateMaskCanvas = () => {
		if (!maskCtx || !originalImage) return;

		// Clear mask
		maskCtx.clearRect(0, 0, canvasWidth, canvasHeight);

		// Fill entire canvas with white (expansion area)
		maskCtx.fillStyle = 'white';
		maskCtx.fillRect(0, 0, canvasWidth, canvasHeight);

		// Fill image area with black (original image area)
		maskCtx.fillStyle = 'black';
		maskCtx.fillRect(imageX, imageY, imageWidth, imageHeight);
	};

	const getMousePos = (e: MouseEvent) => {
		const rect = canvas.getBoundingClientRect();
		return {
			x: (e.clientX - rect.left) * (canvasWidth / rect.width),
			y: (e.clientY - rect.top) * (canvasHeight / rect.height)
		};
	};

	const getResizeHandle = (mouseX: number, mouseY: number) => {
		const handleSize = 8;
		const tolerance = handleSize;

		// Check corner handles
		if (
			mouseX >= imageX - tolerance &&
			mouseX <= imageX + tolerance &&
			mouseY >= imageY - tolerance &&
			mouseY <= imageY + tolerance
		) {
			return 'nw';
		}
		if (
			mouseX >= imageX + imageWidth - tolerance &&
			mouseX <= imageX + imageWidth + tolerance &&
			mouseY >= imageY - tolerance &&
			mouseY <= imageY + tolerance
		) {
			return 'ne';
		}
		if (
			mouseX >= imageX - tolerance &&
			mouseX <= imageX + tolerance &&
			mouseY >= imageY + imageHeight - tolerance &&
			mouseY <= imageY + imageHeight + tolerance
		) {
			return 'sw';
		}
		if (
			mouseX >= imageX + imageWidth - tolerance &&
			mouseX <= imageX + imageWidth + tolerance &&
			mouseY >= imageY + imageHeight - tolerance &&
			mouseY <= imageY + imageHeight + tolerance
		) {
			return 'se';
		}

		return '';
	};

	const isInsideImage = (mouseX: number, mouseY: number) => {
		return (
			mouseX >= imageX &&
			mouseX <= imageX + imageWidth &&
			mouseY >= imageY &&
			mouseY <= imageY + imageHeight
		);
	};

	const handleMouseDown = (e: MouseEvent) => {
		const pos = getMousePos(e);
		const handle = getResizeHandle(pos.x, pos.y);

		if (handle) {
			// Start resizing
			isResizing = true;
			resizeHandle = handle;
			resizeStartX = pos.x;
			resizeStartY = pos.y;
			resizeStartWidth = imageWidth;
			resizeStartHeight = imageHeight;
		} else if (isInsideImage(pos.x, pos.y)) {
			// Start dragging
			isDragging = true;
			dragStartX = pos.x;
			dragStartY = pos.y;
			dragStartImageX = imageX;
			dragStartImageY = imageY;
		}
	};

	const handleMouseMove = (e: MouseEvent) => {
		const pos = getMousePos(e);

		if (isResizing && resizeHandle) {
			// Handle resizing
			const deltaX = pos.x - resizeStartX;
			const deltaY = pos.y - resizeStartY;
			const aspectRatio = originalImage!.width / originalImage!.height;

			let newWidth = resizeStartWidth;
			let newHeight = resizeStartHeight;

			if (resizeHandle.includes('e')) {
				newWidth = Math.max(50, resizeStartWidth + deltaX);
			}
			if (resizeHandle.includes('w')) {
				newWidth = Math.max(50, resizeStartWidth - deltaX);
			}
			if (resizeHandle.includes('s')) {
				newHeight = Math.max(50, resizeStartHeight + deltaY);
			}
			if (resizeHandle.includes('n')) {
				newHeight = Math.max(50, resizeStartHeight - deltaY);
			}

			// Maintain aspect ratio
			if (Math.abs(newWidth - imageWidth) > Math.abs(newHeight - imageHeight)) {
				newHeight = newWidth / aspectRatio;
			} else {
				newWidth = newHeight * aspectRatio;
			}

			// Adjust position for corner resizing
			if (resizeHandle.includes('w')) {
				imageX = imageX + imageWidth - newWidth;
			}
			if (resizeHandle.includes('n')) {
				imageY = imageY + imageHeight - newHeight;
			}

			imageWidth = newWidth;
			imageHeight = newHeight;

			// Keep image within canvas
			if (imageX < 0) {
				imageWidth += imageX;
				imageX = 0;
			}
			if (imageY < 0) {
				imageHeight += imageY;
				imageY = 0;
			}
			if (imageX + imageWidth > canvasWidth) {
				imageWidth = canvasWidth - imageX;
			}
			if (imageY + imageHeight > canvasHeight) {
				imageHeight = canvasHeight - imageY;
			}

			redrawCanvas();
		} else if (isDragging) {
			// Handle dragging
			const deltaX = pos.x - dragStartX;
			const deltaY = pos.y - dragStartY;

			imageX = Math.max(0, Math.min(canvasWidth - imageWidth, dragStartImageX + deltaX));
			imageY = Math.max(0, Math.min(canvasHeight - imageHeight, dragStartImageY + deltaY));

			redrawCanvas();
		} else {
			// Update cursor
			const handle = getResizeHandle(pos.x, pos.y);
			if (handle) {
				canvas.style.cursor =
					handle.includes('n') && handle.includes('w')
						? 'nw-resize'
						: handle.includes('n') && handle.includes('e')
							? 'ne-resize'
							: handle.includes('s') && handle.includes('w')
								? 'sw-resize'
								: 'se-resize';
			} else if (isInsideImage(pos.x, pos.y)) {
				canvas.style.cursor = 'move';
			} else {
				canvas.style.cursor = 'default';
			}
		}
	};

	const handleMouseUp = () => {
		isDragging = false;
		isResizing = false;
		resizeHandle = '';
		canvas.style.cursor = 'default';
	};

	const generateMaskImage = (): string => {
		if (!maskCanvas) return '';
		return maskCanvas.toDataURL('image/png');
	};

	const handleConfirm = () => {
		const maskImageUrl = generateMaskImage();

		// Calculate expansion parameters
		const topExpansion = imageY / canvasHeight;
		const bottomExpansion = (canvasHeight - imageY - imageHeight) / canvasHeight;
		const leftExpansion = imageX / canvasWidth;
		const rightExpansion = (canvasWidth - imageX - imageWidth) / canvasWidth;

		dispatch('confirm', {
			maskImageUrl,
			canvasWidth,
			canvasHeight,
			imageX,
			imageY,
			imageWidth,
			imageHeight,
			expansionParams: {
				top: topExpansion,
				bottom: bottomExpansion,
				left: leftExpansion,
				right: rightExpansion
			}
		});
	};

	const handleClose = () => {
		dispatch('close');
	};

	const resetImage = () => {
		if (!originalImage) return;

		// Reset to center position
		const imgAspect = originalImage.width / originalImage.height;

		if (imgAspect > 1) {
			imageWidth = Math.min(400, canvasWidth * 0.5);
			imageHeight = imageWidth / imgAspect;
		} else {
			imageHeight = Math.min(300, canvasHeight * 0.5);
			imageWidth = imageHeight * imgAspect;
		}

		imageX = (canvasWidth - imageWidth) / 2;
		imageY = (canvasHeight - imageHeight) / 2;

		redrawCanvas();
	};

	const adjustCanvasSize = (width: number, height: number) => {
		canvasWidth = Math.max(400, Math.min(1200, width));
		canvasHeight = Math.max(300, Math.min(900, height));

		canvas.width = canvasWidth;
		canvas.height = canvasHeight;
		maskCanvas.width = canvasWidth;
		maskCanvas.height = canvasHeight;

		// Keep image proportionally positioned
		imageX = Math.max(0, Math.min(canvasWidth - imageWidth, imageX));
		imageY = Math.max(0, Math.min(canvasHeight - imageHeight, imageY));

		redrawCanvas();
	};
</script>

{#if show}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
		on:click={handleClose}
	>
		<div
			class="relative max-w-[95vw] max-h-[95vh] flex flex-col bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden"
			on:click|stopPropagation
		>
			<!-- Header -->
			<div
				class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700"
			>
				<div>
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white">🎨 画布编辑器</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
						拖拽调整图片位置，拖拽角落调整大小
					</p>
				</div>
				<button
					on:click={handleClose}
					class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg text-xl"
				>
					×
				</button>
			</div>

			<!-- Canvas Container -->
			<div class="flex-1 p-6 overflow-auto">
				<div class="flex flex-col lg:flex-row gap-6">
					<!-- Canvas Area -->
					<div class="flex-1">
						<div class="mb-4">
							<canvas
								bind:this={canvas}
								class="border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm cursor-default max-w-full"
								style="max-height: 600px;"
								on:mousedown={handleMouseDown}
								on:mousemove={handleMouseMove}
								on:mouseup={handleMouseUp}
								on:mouseleave={handleMouseUp}
							></canvas>

							<!-- Hidden mask canvas -->
							<canvas bind:this={maskCanvas} class="hidden"></canvas>
						</div>
					</div>

					<!-- Control Panel -->
					<div class="w-80 bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-4">
						<div>
							<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">画布设置</h4>

							<div class="space-y-3">
								<div>
									<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
										画布宽度
									</label>
									<input
										type="range"
										min="400"
										max="1200"
										bind:value={canvasWidth}
										on:input={() => adjustCanvasSize(canvasWidth, canvasHeight)}
										class="w-full"
									/>
									<span class="text-xs text-gray-500">{canvasWidth}px</span>
								</div>

								<div>
									<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
										画布高度
									</label>
									<input
										type="range"
										min="300"
										max="900"
										bind:value={canvasHeight}
										on:input={() => adjustCanvasSize(canvasWidth, canvasHeight)}
										class="w-full"
									/>
									<span class="text-xs text-gray-500">{canvasHeight}px</span>
								</div>
							</div>
						</div>

						<div class="border-t border-gray-200 dark:border-gray-600 pt-4">
							<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">图片位置</h4>

							<div class="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-400">
								<div>X: {Math.round(imageX)}px</div>
								<div>Y: {Math.round(imageY)}px</div>
								<div>宽: {Math.round(imageWidth)}px</div>
								<div>高: {Math.round(imageHeight)}px</div>
							</div>

							<button
								on:click={resetImage}
								class="mt-3 w-full px-3 py-2 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors"
							>
								🔄 重置位置
							</button>
						</div>

						<div class="border-t border-gray-200 dark:border-gray-600 pt-4">
							<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">操作说明</h4>
							<div class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
								<div>• 拖拽图片移动位置</div>
								<div>• 拖拽角落调整大小</div>
								<div>• 蓝色区域为扩展区域</div>
								<div>• 绿色边框为原图区域</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Footer -->
			<div
				class="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700"
			>
				<div class="text-sm text-gray-500 dark:text-gray-400">调整完成后点击确认保存设置</div>
				<div class="flex items-center gap-3">
					<button
						on:click={handleClose}
						class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors"
					>
						取消
					</button>
					<button
						on:click={handleConfirm}
						class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
					>
						✅ 确认
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
