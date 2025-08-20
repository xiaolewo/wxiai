<script lang="ts">
	import { onMount } from 'svelte';

	export let stats: any = null;

	// 格式化文件数量
	function formatNumber(num: number): string {
		if (num >= 1000000) {
			return (num / 1000000).toFixed(1) + 'M';
		} else if (num >= 1000) {
			return (num / 1000).toFixed(1) + 'K';
		}
		return num.toString();
	}

	// 获取来源图标
	function getSourceIcon(source: string): string {
		const icons: Record<string, string> = {
			midjourney: '🎨',
			dreamwork: '✨',
			kling: '🎬',
			jimeng: '🎥',
			default: '📁'
		};
		return icons[source.toLowerCase()] || icons.default;
	}

	// 获取类型图标
	function getTypeIcon(type: string): string {
		return type === 'video' ? '🎥' : '🖼️';
	}
</script>

{#if stats}
	<!-- 存储统计增强版 -->
	<div class="space-y-6">
		<!-- 概览卡片 -->
		{#if stats.summary}
			<div>
				<h3 class="text-sm font-semibold mb-3 text-gray-700 dark:text-gray-300">存储概览</h3>
				<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
					<!-- 已上传 -->
					<div
						class="relative overflow-hidden bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 rounded-xl p-4 border border-green-200 dark:border-green-800"
					>
						<div class="relative z-10">
							<div class="text-2xl font-bold text-green-700 dark:text-green-400">
								{formatNumber(stats.summary.uploaded_files)}
							</div>
							<div class="text-xs text-green-600 dark:text-green-500 mt-1">已上传文件</div>
							<div class="text-xs text-green-500 dark:text-green-600 mt-0.5">
								{stats.summary.total_size_formatted}
							</div>
						</div>
						<div class="absolute -right-2 -bottom-2 text-6xl opacity-10">✅</div>
					</div>

					<!-- 待处理 -->
					<div
						class="relative overflow-hidden bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/30 dark:to-yellow-800/30 rounded-xl p-4 border border-yellow-200 dark:border-yellow-800"
					>
						<div class="relative z-10">
							<div class="text-2xl font-bold text-yellow-700 dark:text-yellow-400">
								{formatNumber(stats.summary.pending_files)}
							</div>
							<div class="text-xs text-yellow-600 dark:text-yellow-500 mt-1">待处理</div>
						</div>
						<div class="absolute -right-2 -bottom-2 text-6xl opacity-10">⏳</div>
					</div>

					<!-- 失败 -->
					<div
						class="relative overflow-hidden bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 rounded-xl p-4 border border-red-200 dark:border-red-800"
					>
						<div class="relative z-10">
							<div class="text-2xl font-bold text-red-700 dark:text-red-400">
								{formatNumber(stats.summary.failed_files)}
							</div>
							<div class="text-xs text-red-600 dark:text-red-500 mt-1">上传失败</div>
						</div>
						<div class="absolute -right-2 -bottom-2 text-6xl opacity-10">❌</div>
					</div>

					<!-- 成功率 -->
					<div
						class="relative overflow-hidden bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-xl p-4 border border-blue-200 dark:border-blue-800"
					>
						<div class="relative z-10">
							<div class="text-2xl font-bold text-blue-700 dark:text-blue-400">
								{stats.summary.success_rate}%
							</div>
							<div class="text-xs text-blue-600 dark:text-blue-500 mt-1">成功率</div>
							<div class="text-xs text-blue-500 dark:text-blue-600 mt-0.5">
								总计 {stats.summary.total_files} 个
							</div>
						</div>
						<div class="absolute -right-2 -bottom-2 text-6xl opacity-10">📊</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- 分布统计 -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
			<!-- 按来源分布 -->
			{#if stats.source_distribution && Object.keys(stats.source_distribution).length > 0}
				<div
					class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700"
				>
					<h4 class="text-sm font-semibold mb-3 flex items-center gap-2">
						<span>按来源分布</span>
						<span class="text-xs text-gray-500">Source</span>
					</h4>
					<div class="space-y-3">
						{#each Object.entries(stats.source_distribution) as [source, data]}
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-2 flex-1">
									<span class="text-lg">{getSourceIcon(source)}</span>
									<div class="flex-1">
										<div class="flex items-center gap-2">
											<span class="text-sm font-medium capitalize">{source}</span>
											<span class="text-xs text-gray-500">({data.count})</span>
										</div>
										<!-- 进度条 -->
										<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
											<div
												class="bg-blue-600 h-1.5 rounded-full"
												style="width: {((data.count / stats.summary.uploaded_files) * 100).toFixed(
													1
												)}%"
											></div>
										</div>
									</div>
								</div>
								<span class="text-sm font-medium ml-3">{data.size_formatted}</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- 按类型分布 -->
			{#if stats.type_distribution && Object.keys(stats.type_distribution).length > 0}
				<div
					class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700"
				>
					<h4 class="text-sm font-semibold mb-3 flex items-center gap-2">
						<span>按类型分布</span>
						<span class="text-xs text-gray-500">Type</span>
					</h4>
					<div class="space-y-3">
						{#each Object.entries(stats.type_distribution) as [type, data]}
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-2 flex-1">
									<span class="text-lg">{getTypeIcon(type)}</span>
									<div class="flex-1">
										<div class="flex items-center gap-2">
											<span class="text-sm font-medium capitalize">{type}</span>
											<span class="text-xs text-gray-500">({data.count})</span>
										</div>
										<!-- 进度条 -->
										<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
											<div
												class="bg-purple-600 h-1.5 rounded-full"
												style="width: {((data.count / stats.summary.uploaded_files) * 100).toFixed(
													1
												)}%"
											></div>
										</div>
									</div>
								</div>
								<span class="text-sm font-medium ml-3">{data.size_formatted}</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>

		<!-- 7天趋势 -->
		{#if stats.daily_trend && stats.daily_trend.length > 0}
			<div
				class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700"
			>
				<h4 class="text-sm font-semibold mb-3 flex items-center gap-2">
					<span>最近7天上传趋势</span>
					<span class="text-xs text-gray-500">Daily Trend</span>
				</h4>
				<div class="space-y-2">
					{#each stats.daily_trend as day}
						<div
							class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0"
						>
							<span class="text-sm text-gray-600 dark:text-gray-400">{day.date}</span>
							<div class="flex items-center gap-4">
								<div class="flex items-center gap-1">
									<span class="text-sm font-medium">{day.count}</span>
									<span class="text-xs text-gray-500">个文件</span>
								</div>
								<span class="text-xs text-gray-500 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
									{day.size_formatted}
								</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- TOP用户 -->
		{#if stats.top_users && stats.top_users.length > 0}
			<div
				class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700"
			>
				<h4 class="text-sm font-semibold mb-3 flex items-center gap-2">
					<span>存储使用排行</span>
					<span class="text-xs text-gray-500">Top Users</span>
				</h4>
				<div class="space-y-2">
					{#each stats.top_users.slice(0, 5) as user, index}
						<div
							class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0"
						>
							<div class="flex items-center gap-3">
								<span
									class="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white text-xs flex items-center justify-center font-bold"
								>
									{index + 1}
								</span>
								<span class="text-sm truncate max-w-[200px]" title={user.user_id}>
									{user.user_id}
								</span>
							</div>
							<div class="flex items-center gap-3">
								<span class="text-xs text-gray-500">{user.count} 个</span>
								<span class="text-sm font-semibold bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
									{user.size_formatted}
								</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- 最近失败 -->
		{#if stats.recent_failures && stats.recent_failures.length > 0}
			<div
				class="bg-red-50 dark:bg-red-900/20 rounded-xl p-4 border border-red-200 dark:border-red-800"
			>
				<h4
					class="text-sm font-semibold mb-3 text-red-700 dark:text-red-400 flex items-center gap-2"
				>
					<span>⚠️ 最近上传失败</span>
					<span class="text-xs">Recent Failures</span>
				</h4>
				<div class="space-y-2">
					{#each stats.recent_failures as failure}
						<div class="bg-white dark:bg-gray-800 rounded-lg p-3">
							<div class="flex justify-between items-start mb-1">
								<span class="text-sm font-medium truncate max-w-[300px]" title={failure.filename}>
									{failure.filename}
								</span>
								<span class="text-xs text-gray-500 whitespace-nowrap ml-2">
									{failure.created_at}
								</span>
							</div>
							<div class="flex items-center gap-2">
								<span
									class="text-xs bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-400 px-2 py-0.5 rounded"
								>
									{failure.source_type}
								</span>
								<span class="text-xs text-red-600 dark:text-red-400">
									{failure.error || '未知错误'}
								</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
{:else}
	<div class="text-center py-8 text-gray-500">
		<div class="text-4xl mb-2">📊</div>
		<div class="text-sm">暂无统计数据</div>
		<div class="text-xs mt-1">启用云存储后将显示详细统计</div>
	</div>
{/if}
