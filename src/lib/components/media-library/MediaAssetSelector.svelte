<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { listMediaAssets, uploadMediaAsset, type MediaAsset } from '$lib/apis/media-library';
	import VideoPreview from '$lib/components/media-library/VideoPreview.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { resolveAssetPreviewUrl } from '$lib/utils/media-assets';

	export let token = '';
	export let open = false;
	export let mediaType: 'image' | 'video' | 'all' = 'all';
	export let multiple = false;
	export let scope: 'mine' | 'group' | 'all' = 'mine';
	export let allowUpload = true;

	const dispatch = createEventDispatcher<{
		close: void;
		confirm: MediaAsset[];
	}>();

	let assets: MediaAsset[] = [];
	let page = 1;
	let total = 0;
	let limit = 24;
	let loading = false;
	let search = '';
	let includeDeleted = false;
	let selected = new Set<string>();
	let uploading = false;
	let uploadInput: HTMLInputElement | null = null;

	$: if (!open) {
		selected = new Set();
	}

	const mediaTypeOptions: { value: 'image' | 'video' | 'all'; label: string }[] = [
		{ value: 'all', label: '全部类型' },
		{ value: 'image', label: '图片' },
		{ value: 'video', label: '视频' }
	];

	onMount(() => {
		if (open) {
			void loadAssets(true);
		}
	});

	$: if (open && assets.length === 0 && !loading) {
		void loadAssets(true);
	}

	async function loadAssets(reset = false) {
		if (!token) return;
		if (reset) {
			page = 1;
			total = 0;
			assets = [];
		}

		loading = true;
		try {
			const response = await listMediaAssets(token, {
				scope,
				page,
				limit,
				mediaType: mediaType === 'all' ? undefined : mediaType,
				includeDeleted,
				search: search.trim() || undefined
			});
			assets = reset ? response.data : [...assets, ...response.data];
			total = response.total ?? assets.length;
		} catch (error) {
			console.error('加载媒体资产失败:', error);
		} finally {
			loading = false;
		}
	}

	function toggleSelection(asset: MediaAsset) {
		if (selected.has(asset.id)) {
			selected.delete(asset.id);
		} else {
			if (!multiple) {
				selected.clear();
			}
			selected.add(asset.id);
		}
		selected = new Set(selected);
	}

	function confirmSelection() {
		const chosen = assets.filter((asset) => selected.has(asset.id));
		dispatch('confirm', chosen);
	}

	function close() {
		dispatch('close');
	}

	async function handleUpload(event: Event) {
		if (!allowUpload) return;
		const input = event.currentTarget as HTMLInputElement;
		const fileList = input.files;
		if (!fileList || fileList.length === 0 || !token) return;

		const files = Array.from(fileList);
		uploading = true;
		try {
			for (const file of files) {
				const uploaded = await uploadMediaAsset(token, file, {
					visibilityScope: scope === 'group' ? 'group' : 'user'
				});
				assets = [uploaded, ...assets];
				selected.add(uploaded.id);
			}
		} catch (error) {
			console.error('上传文件失败:', error);
		} finally {
			uploading = false;
			if (uploadInput) uploadInput.value = '';
			selected = new Set(selected);
		}
	}

	function loadMore() {
		if (loading) return;
		const totalPages = Math.ceil(total / limit) || 1;
		if (page >= totalPages) return;
		page += 1;
		void loadAssets();
	}
</script>

{#if open}
	<div class="fixed inset-0 z-[1200] flex items-center justify-center bg-black/50">
		<div
			class="flex h-[80vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-slate-950"
		>
			<header
				class="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800"
			>
				<div>
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">选择媒体资源</h3>
					<p class="text-xs text-slate-500 dark:text-slate-400">可从媒体库挑选或直接上传本地文件</p>
				</div>
				<button
					class="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
					on:click={close}
				>
					✕
				</button>
			</header>

			<div class="flex flex-1 overflow-hidden">
				<aside
					class="hidden w-60 shrink-0 border-r border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/60 md:flex md:flex-col"
				>
					<h4 class="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">筛选</h4>
					<label class="mb-2 block text-xs text-slate-500 dark:text-slate-400">类型</label>
					<select
						bind:value={mediaType}
						class="mb-4 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-900"
						on:change={() => loadAssets(true)}
					>
						{#each mediaTypeOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>

					<label class="mb-2 block text-xs text-slate-500 dark:text-slate-400">搜索</label>
					<input
						bind:value={search}
						class="mb-4 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-900"
						placeholder="输入关键词"
						on:keydown={(event) => event.key === 'Enter' && loadAssets(true)}
					/>

					<label class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
						<input
							type="checkbox"
							bind:checked={includeDeleted}
							on:change={() => loadAssets(true)}
						/>
						显示已删除
					</label>

					{#if allowUpload}
						<div class="mt-6">
							<input
								type="file"
								accept={mediaType === 'video'
									? 'video/*'
									: mediaType === 'image'
										? 'image/*'
										: 'image/*,video/*'}
								{multiple}
								class="hidden"
								bind:this={uploadInput}
								on:change={handleUpload}
							/>
							<button
								class="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-500 px-3 py-2 text-xs font-medium text-white shadow hover:bg-blue-600 disabled:opacity-60"
								on:click={() => uploadInput?.click()}
								disabled={uploading}
							>
								{#if uploading}
									<Spinner className="size-3" />
								{/if}
								{uploading ? '上传中…' : '上传本地文件'}
							</button>
						</div>
					{/if}
				</aside>

				<main class="flex flex-1 flex-col overflow-hidden">
					<div
						class="flex items-center gap-2 border-b border-slate-200 px-4 py-3 dark:border-slate-800 md:hidden"
					>
						<input
							bind:value={search}
							class="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-900"
							placeholder="搜索素材"
							on:keydown={(event) => event.key === 'Enter' && loadAssets(true)}
						/>
						<button
							class="rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-500 dark:border-slate-700 dark:text-slate-300"
							on:click={() => loadAssets(true)}
						>
							搜索
						</button>
						{#if allowUpload}
							<button
								class="flex items-center gap-1 rounded-lg bg-blue-500 px-3 py-2 text-xs font-medium text-white shadow hover:bg-blue-600 disabled:opacity-60"
								on:click={() => uploadInput?.click()}
								disabled={uploading}
							>
								{#if uploading}
									<Spinner className="size-3" />
								{/if}
								{uploading ? '上传中…' : '上传'}
							</button>
						{/if}
					</div>

					<div class="flex-1 overflow-y-auto p-4">
						{#if loading && assets.length === 0}
							<div
								class="flex h-full items-center justify-center text-sm text-slate-500 dark:text-slate-300"
							>
								正在加载媒体资产…
							</div>
						{:else if assets.length === 0}
							<div
								class="flex h-full flex-col items-center justify-center text-sm text-slate-500 dark:text-slate-300"
							>
								暂无素材，可先上传文件
							</div>
						{:else}
							<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
								{#each assets as asset}
									<article
										class={`group relative flex cursor-pointer flex-col overflow-hidden rounded-xl border ${selected.has(asset.id) ? 'border-blue-400 ring-2 ring-blue-200' : 'border-slate-200'} bg-white shadow hover:shadow-lg dark:border-slate-800 dark:bg-slate-900`}
										on:click={() => toggleSelection(asset)}
									>
										<div class="relative aspect-[4/3] bg-slate-100 dark:bg-slate-800">
											{#if asset.media_type === 'image'}
												<img
													src={resolveAssetPreviewUrl(asset) ?? ''}
													alt={asset.display_name}
													class="h-full w-full object-cover"
													loading="lazy"
												/>
											{:else if asset.media_type === 'video'}
												<VideoPreview
													src={resolveAssetPreviewUrl(asset) ?? ''}
													poster={asset.thumbnail_url ?? undefined}
													className="h-full w-full"
													muted
													autoplay={false}
													loop={false}
												/>
											{/if}
											{#if selected.has(asset.id)}
												<span
													class="absolute left-2 top-2 inline-flex items-center gap-1 rounded-full bg-blue-500 px-2 py-0.5 text-[10px] font-medium text-white shadow"
												>
													已选
												</span>
											{/if}
										</div>
										<div
											class="flex flex-1 flex-col gap-1 px-3 py-2 text-[11px] text-slate-500 dark:text-slate-300"
										>
											<div
												class="truncate text-sm font-semibold text-slate-700 dark:text-slate-100"
												title={asset.display_name}
											>
												{asset.display_name}
											</div>
											<div class="flex items-center justify-between gap-2">
												<span>{asset.media_type === 'video' ? '视频' : '图片'}</span>
												<span
													>{asset.created_at
														? new Date(asset.created_at).toLocaleDateString()
														: ''}</span
												>
											</div>
										</div>
									</article>
								{/each}
							</div>
							{#if assets.length < total}
								<div class="mt-4 flex justify-center">
									<button
										class="rounded-full border border-slate-300 px-4 py-1.5 text-xs text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
										on:click={loadMore}
									>
										加载更多
									</button>
								</div>
							{/if}
						{/if}
					</div>
				</main>
			</div>

			<footer
				class="flex items-center justify-between border-t border-slate-200 px-6 py-4 text-sm dark:border-slate-800"
			>
				<div class="text-slate-500 dark:text-slate-400">
					已选择 {selected.size} 个素材
				</div>
				<div class="flex items-center gap-3">
					<button
						class="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
						on:click={close}
					>
						取消
					</button>
					<button
						class="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white shadow hover:bg-blue-600 disabled:opacity-60"
						on:click={confirmSelection}
						disabled={selected.size === 0}
					>
						确认
					</button>
				</div>
			</footer>
		</div>
	</div>
{/if}
