<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { listMediaAssets, type MediaAsset } from '$lib/apis/media-library';
	import { resolveAssetPreviewUrl } from '$lib/utils/media-assets';

	export let token: string;
	export let scope: string = 'mine';
	export let media类型: 'all' | 'image' | 'video' = 'image';
	export let limit = 20;

	const dispatch = createEventDispatcher<{ select: MediaAsset }>();
	let assets: MediaAsset[] = [];
	let loading = false;
	let page = 1;
	let total = 0;

	onMount(loadAssets);

	async function loadAssets() {
		if (!token) return;
		loading = true;
		try {
			const res = await listMediaAssets(token, {
				scope,
				page,
				limit,
				media类型: media类型 === 'all' ? undefined : media类型
			});
			assets = res.data;
			total = res.total;
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			loading = false;
		}
	}

	function selectAsset(asset: MediaAsset) {
		dispatch('select', asset);
	}
</script>

<div class="flex flex-col gap-4">
	<div class="flex justify-between items-center">
		<h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100">媒体库</h3>
		<button
			class="px-3 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
			on:click={loadAssets}
		>
			刷新
		</button>
	</div>

	{#if loading}
		<div class="text-sm text-gray-500 dark:text-gray-400">正在加载资产…</div>
	{:else if assets.length === 0}
		<div class="text-sm text-gray-500 dark:text-gray-400">暂无媒体资产。</div>
	{:else}
		<div class="grid gap-3 grid-cols-2 sm:grid-cols-3">
			{#each assets as asset}
				<button
					class="border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden text-left bg-white dark:bg-gray-900 hover:border-blue-400 focus:outline-none"
					on:click={() => selectAsset(asset)}
				>
					<div class="aspect-square bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
						{#if asset.media_type === 'image' && resolveAssetPreviewUrl(asset)}
							<img
								src={resolveAssetPreviewUrl(asset) ?? ''}
								alt={asset.display_name}
								class="object-cover w-full h-full"
							/>
						{:else}
							<div class="text-gray-400 text-xs uppercase">{asset.media_type}</div>
						{/if}
					</div>
					<div class="p-2">
						<div class="text-xs font-medium text-gray-800 dark:text-gray-100 truncate">
							{asset.display_name}
						</div>
						<div class="text-[11px] text-gray-500 dark:text-gray-400 truncate">
							{asset.source ?? asset.visibility_scope}
						</div>
					</div>
				</button>
			{/each}
		</div>
	{/if}

	{#if total > limit}
		<div class="flex justify-end gap-2 text-xs text-gray-600 dark:text-gray-400">
			<button
				class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-40"
				disabled={page === 1}
				on:click={async () => {
					page = Math.max(1, page - 1);
					await loadAssets();
				}}
			>
				Prev
			</button>
			<button
				class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-40"
				disabled={page * limit >= total}
				on:click={async () => {
					page = page + 1;
					await loadAssets();
				}}
			>
				下一页
			</button>
		</div>
	{/if}
</div>
