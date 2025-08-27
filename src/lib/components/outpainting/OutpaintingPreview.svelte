<script lang="ts">
	import { onMount } from 'svelte';

	export let originalImageUrl: string = '';
	export let expansionMode: string = 'equal';
	export let top: number = 0.1;
	export let bottom: number = 0.1;
	export let left: number = 0.1;
	export let right: number = 0.1;

	let canvas: HTMLCanvasElement;
	let ctx: CanvasRenderingContext2D | null = null;
	let originalImage: HTMLImageElement | null = null;
	let containerWidth = 200;
	let containerHeight = 150;

	onMount(() => {
		if (canvas) {
			ctx = canvas.getContext('2d');
			loadAndDrawPreview();
		}
	});

	$: if (originalImageUrl && ctx) {
		loadAndDrawPreview();
	}

	$: if (
		ctx &&
		originalImage &&
		(top !== undefined ||
			bottom !== undefined ||
			left !== undefined ||
			right !== undefined ||
			expansionMode)
	) {
		drawPreview();
	}

	const loadAndDrawPreview = () => {
		if (!originalImageUrl || !ctx) return;

		originalImage = new Image();
		originalImage.crossOrigin = 'anonymous';
		originalImage.onload = () => {
			drawPreview();
		};
		originalImage.src = originalImageUrl;
	};

	const drawPreview = () => {
		if (!ctx || !originalImage || !canvas) return;

		// 设置画布尺寸
		canvas.width = containerWidth;
		canvas.height = containerHeight;

		// 清除画布
		ctx.clearRect(0, 0, canvas.width, canvas.height);

		// 计算原图在预览中的尺寸和位置
		const imgAspect = originalImage.width / originalImage.height;
		const containerAspect = containerWidth / containerHeight;

		let previewImgWidth: number, previewImgHeight: number;
		if (imgAspect > containerAspect) {
			previewImgWidth = containerWidth * 0.6; // 预留扩展空间
			previewImgHeight = previewImgWidth / imgAspect;
		} else {
			previewImgHeight = containerHeight * 0.6;
			previewImgWidth = previewImgHeight * imgAspect;
		}

		// 计算扩展后的尺寸
		const expandedWidth = previewImgWidth * (1 + left + right);
		const expandedHeight = previewImgHeight * (1 + top + bottom);

		// 居中显示扩展后的图片
		const expandedX = (containerWidth - expandedWidth) / 2;
		const expandedY = (containerHeight - expandedHeight) / 2;

		// 原图在扩展图中的位置
		const originalX = expandedX + (expandedWidth * left) / (1 + left + right);
		const originalY = expandedY + (expandedHeight * top) / (1 + top + bottom);

		// 绘制扩展区域背景（淡蓝色）
		ctx.fillStyle = 'rgba(59, 130, 246, 0.2)';
		ctx.fillRect(expandedX, expandedY, expandedWidth, expandedHeight);

		// 绘制扩展区域边框
		ctx.strokeStyle = 'rgba(59, 130, 246, 0.5)';
		ctx.lineWidth = 1;
		ctx.setLineDash([5, 5]);
		ctx.strokeRect(expandedX, expandedY, expandedWidth, expandedHeight);

		// 绘制原始图片
		ctx.drawImage(originalImage, originalX, originalY, previewImgWidth, previewImgHeight);

		// 绘制原图边框
		ctx.strokeStyle = 'rgba(34, 197, 94, 0.8)';
		ctx.lineWidth = 2;
		ctx.setLineDash([]);
		ctx.strokeRect(originalX, originalY, previewImgWidth, previewImgHeight);

		// 绘制扩展方向指示
		drawExpansionIndicators(
			originalX,
			originalY,
			previewImgWidth,
			previewImgHeight,
			expandedX,
			expandedY,
			expandedWidth,
			expandedHeight
		);
	};

	const drawExpansionIndicators = (
		origX: number,
		origY: number,
		origW: number,
		origH: number,
		expX: number,
		expY: number,
		expW: number,
		expH: number
	) => {
		if (!ctx) return;

		ctx.fillStyle = 'rgba(59, 130, 246, 0.7)';
		ctx.font = '10px Arial';
		ctx.textAlign = 'center';

		// 向上扩展指示
		if (top > 0) {
			const upHeight = origY - expY;
			if (upHeight > 10) {
				ctx.fillText(`↑${(top * 100).toFixed(0)}%`, origX + origW / 2, expY + upHeight / 2 + 3);
			}
		}

		// 向下扩展指示
		if (bottom > 0) {
			const downHeight = expY + expH - (origY + origH);
			if (downHeight > 10) {
				ctx.fillText(
					`↓${(bottom * 100).toFixed(0)}%`,
					origX + origW / 2,
					origY + origH + downHeight / 2 + 3
				);
			}
		}

		// 向左扩展指示
		if (left > 0) {
			const leftWidth = origX - expX;
			if (leftWidth > 20) {
				ctx.save();
				ctx.translate(expX + leftWidth / 2, origY + origH / 2);
				ctx.rotate(-Math.PI / 2);
				ctx.fillText(`←${(left * 100).toFixed(0)}%`, 0, 3);
				ctx.restore();
			}
		}

		// 向右扩展指示
		if (right > 0) {
			const rightWidth = expX + expW - (origX + origW);
			if (rightWidth > 20) {
				ctx.save();
				ctx.translate(origX + origW + rightWidth / 2, origY + origH / 2);
				ctx.rotate(-Math.PI / 2);
				ctx.fillText(`→${(right * 100).toFixed(0)}%`, 0, 3);
				ctx.restore();
			}
		}
	};

	const getModeDescription = (mode: string) => {
		switch (mode) {
			case 'equal':
				return '等比扩展 - 四边相同比例扩展';
			case 'aspect':
				return '画幅扩展 - 扩展为指定画幅比例';
			case 'custom':
				return '四边扩展 - 自定义各边扩展比例';
			case 'canvas':
				return '画布扩展 - 在画布中自定义位置';
			default:
				return '未知模式';
		}
	};
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
	<div class="mb-2">
		<span class="text-xs font-medium text-gray-700 dark:text-gray-300"> 扩展预览 </span>
	</div>

	<!-- 预览画布 -->
	<div class="w-full bg-gray-50 dark:bg-gray-700 rounded border">
		<canvas
			bind:this={canvas}
			width={containerWidth}
			height={containerHeight}
			class="w-full h-auto rounded"
		></canvas>
	</div>

	<!-- 模式说明 -->
	<div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
		{getModeDescription(expansionMode)}
	</div>

	<!-- 扩展参数显示 -->
	{#if expansionMode === 'custom'}
		<div class="mt-2 text-xs text-gray-600 dark:text-gray-400">
			<div class="grid grid-cols-2 gap-1">
				<span>上: {(top * 100).toFixed(0)}%</span>
				<span>下: {(bottom * 100).toFixed(0)}%</span>
				<span>左: {(left * 100).toFixed(0)}%</span>
				<span>右: {(right * 100).toFixed(0)}%</span>
			</div>
		</div>
	{:else if expansionMode === 'equal'}
		<div class="mt-2 text-xs text-gray-600 dark:text-gray-400">
			扩展比例: {(top * 100).toFixed(0)}%
		</div>
	{/if}

	<!-- 图例 -->
	<div class="mt-2 flex items-center justify-between text-xs">
		<div class="flex items-center space-x-2">
			<div class="flex items-center">
				<div class="w-3 h-2 bg-green-500 border border-green-600 mr-1"></div>
				<span class="text-gray-500 dark:text-gray-400">原图</span>
			</div>
			<div class="flex items-center">
				<div class="w-3 h-2 bg-blue-200 border border-blue-400 border-dashed mr-1"></div>
				<span class="text-gray-500 dark:text-gray-400">扩展</span>
			</div>
		</div>
	</div>
</div>
