<script lang="ts">
	import { onMount, onDestroy, getContext } from 'svelte';
	import { get } from 'svelte/store';
	import { toast } from 'svelte-sonner';

	import {
		listMediaAssets,
		getMediaLibrarySettings,
		deleteMediaAsset,
		restoreMediaAsset,
		updateMediaAsset,
		listMediaFolders,
		createMediaFolder,
		updateMediaFolder,
		uploadMediaAsset,
		type MediaAsset,
		type MediaFolder
	} from '$lib/apis/media-library';
	import VideoPreview from '$lib/components/media-library/VideoPreview.svelte';
	import FolderTree from '$lib/components/media-library/FolderTree.svelte';
	import { user, showSidebar } from '$lib/stores';
	import {
		resolveAssetPreviewUrl,
		resolveAssetDownloadUrl,
		buildAssetContentUrl
	} from '$lib/utils/media-assets';

	const i18n = getContext('i18n');

	const presetFolders = [
		{ name: '项目名称', key: 'project' },
		{ name: '角色', key: 'character' },
		{ name: '道具', key: 'props' },
		{ name: '场景', key: 'scene' },
		{ name: '集数', key: 'episode' }
	];

	const timeRangeOptions = [
		{ value: 'all', label: '全部时间' },
		{ value: '7', label: '近 7 天' },
		{ value: '30', label: '近 30 天' }
	];

	const scopeOptions = [
		{ value: 'mine', label: '我的资产' },
		{ value: 'group', label: '工作组资产' },
		{ value: 'all', label: '全部可见范围' }
	];

	const mediaTypeOptions = [
		{ value: 'all', label: '全部类型' },
		{ value: 'image', label: '图片' },
		{ value: 'video', label: '视频' }
	];

	let settings: Record<string, unknown> | null = null;
	let assets: MediaAsset[] = [];
	let filteredAssets: MediaAsset[] = [];
	const PAGE_SIZE = 8;
	let currentPage = 1;
	let totalPages = 1;
	let paginatedAssets: MediaAsset[] = [];
	let lastFilterSignature = '';
	let folders: MediaFolder[] = [];
	let folderMap = new Map<string, MediaFolder>();
	let folderChildren = new Map<string | null, MediaFolder[]>();
	let uploadInput: HTMLInputElement | null = null;
	let isUploading = false;

	let scope = 'mine';
	let mediaType = 'all';
	let timeRange = 'all';
	let tagKeyword = '';
	let searchTerm = '';
	let includeDeleted = false;
	let selectedFolderId: string | null = null;
	let breadcrumb: { id: string | null; name: string }[] = [];

	let loadingAssets = false;
	let loadingFolders = false;

	let selectedIds: string[] = [];
	let draggedFolderId: string | null = null;

	let bulkMoveFolderId = '';

	let currentUser: { id: string } | null = get(user) ?? null;
	const unsubscribeUser = user.subscribe((value) => {
		currentUser = value ?? null;
	});
	onDestroy(unsubscribeUser);

	onMount(async () => {
		try {
			await loadSettings();
			await loadFolders();
			await loadAssets();
		} catch (error) {
			console.error(error);
			toast.error(`${error}`);
		}
	});

	async function loadSettings() {
		const token = localStorage.token;
		if (!token) return;
		settings = await getMediaLibrarySettings(token);
	}

	async function loadFolders() {
		const token = localStorage.token;
		if (!token) return;

		loadingFolders = true;
		try {
			const scopeParam = scope === 'group' ? 'group' : 'mine';
			const result = await listMediaFolders(token, scopeParam);
			folders = result ?? [];
			folderMap = new Map(folders.map((folder) => [folder.id, folder]));
			folderChildren = buildFolderChildren(folders);

			if (scope === 'mine' && currentUser) {
				await ensurePresetFolders(token);
				folderMap = new Map(folders.map((folder) => [folder.id, folder]));
				folderChildren = buildFolderChildren(folders);
			}

			if (selectedFolderId && !folderMap.has(selectedFolderId)) {
				selectedFolderId = null;
			}
			breadcrumb = buildBreadcrumb();
			bulkMoveFolderId = selectedFolderId ?? '';
		} finally {
			loadingFolders = false;
		}
	}

	async function ensurePresetFolders(token: string) {
		const existingKeys = new Set(
			folders.filter((folder) => folder.preset_key).map((folder) => folder.preset_key as string)
		);

		for (const preset of presetFolders) {
			if (!existingKeys.has(preset.key)) {
				try {
					const ownerId = currentUser?.id;
					if (!ownerId) continue;
					const created = await createMediaFolder(token, {
						name: preset.name,
						owner_id: ownerId,
						visibility_scope: 'user',
						preset_key: preset.key
					});
					folders = [...folders, created];
				} catch (error) {
					console.warn('无法创建预设文件夹', preset.name, error);
				}
			}
		}
	}

	async function loadAssets() {
		const token = localStorage.token;
		if (!token) return;

		loadingAssets = true;
		try {
			const response = await listMediaAssets(token, {
				scope,
				mediaType: mediaType === 'all' ? undefined : mediaType,
				folderId: selectedFolderId ?? undefined,
				includeDeleted
			});
			assets = response?.data ?? [];
			currentPage = 1;
			filteredAssets = applyFilters(assets);
			selectedIds = selectedIds.filter((id) => assets.some((asset) => asset.id === id));
		} finally {
			loadingAssets = false;
		}
	}

	function applyFilters(list: MediaAsset[]): MediaAsset[] {
		const searchLower = searchTerm.trim().toLowerCase();
		const tagLower = tagKeyword.trim().toLowerCase();
		const now = Date.now();

		return list.filter((asset) => {
			if (mediaType !== 'all' && asset.media_type !== mediaType) return false;

			if (searchLower) {
				const haystacks = [asset.display_name, asset.source, asset.folder_id]
					.filter(Boolean)
					.map((value) => value!.toLowerCase());
				const matches = haystacks.some((value) => value.includes(searchLower));
				if (!matches) return false;
			}

			if (tagLower) {
				const tags = asset.tags ? Object.values(asset.tags) : [];
				const keys = asset.tags ? Object.keys(asset.tags) : [];
				const combined = [...keys, ...tags].map((value) => String(value).toLowerCase());
				if (!combined.some((value) => value.includes(tagLower))) return false;
			}

			if (timeRange !== 'all' && asset.created_at) {
				const created = Date.parse(asset.created_at);
				if (!Number.isNaN(created)) {
					const days = Number(timeRange);
					const diff = (now - created) / (1000 * 60 * 60 * 24);
					if (diff > days) return false;
				}
			}

			return true;
		});
	}

	$: {
		const signature = [
			scope,
			mediaType,
			timeRange,
			tagKeyword,
			searchTerm,
			selectedFolderId ?? '',
			includeDeleted ? '1' : '0'
		].join('|');

		if (signature !== lastFilterSignature) {
			currentPage = 1;
			lastFilterSignature = signature;
		}
	}

	$: {
		const computedTotal = Math.ceil(filteredAssets.length / PAGE_SIZE);
		totalPages = Math.max(1, Number.isFinite(computedTotal) ? computedTotal : 1);

		if (currentPage > totalPages) {
			currentPage = totalPages;
		} else if (currentPage < 1) {
			currentPage = 1;
		}

		paginatedAssets = filteredAssets.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
	}

	$: filteredAssets = applyFilters(assets);
	$: breadcrumb = buildBreadcrumb();
	$: selectedAssets = assets.filter((asset) => selectedIds.includes(asset.id));

	function buildFolderChildren(list: MediaFolder[]): Map<string | null, MediaFolder[]> {
		const map = new Map<string | null, MediaFolder[]>();
		for (const folder of list) {
			const bucket = map.get(folder.parent_id ?? null) ?? [];
			bucket.push(folder);
			map.set(folder.parent_id ?? null, bucket);
		}
		for (const bucket of map.values()) {
			bucket.sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name));
		}
		return map;
	}

	function buildBreadcrumb(): { id: string | null; name: string }[] {
		const rootLabel = scope === 'group' ? '工作组媒体库' : '我的媒体库';
		const path: { id: string | null; name: string }[] = [{ id: null, name: rootLabel }];

		if (!selectedFolderId) return path;

		const stack: MediaFolder[] = [];
		let current = folderMap.get(selectedFolderId) ?? null;
		while (current) {
			stack.unshift(current);
			current = current.parent_id ? (folderMap.get(current.parent_id) ?? null) : null;
		}

		for (const folder of stack) {
			path.push({ id: folder.id, name: folder.name });
		}
		return path;
	}

	function onSelectFolder(folderId: string | null) {
		selectedFolderId = folderId;
		selectedIds = [];
		bulkMoveFolderId = folderId ?? '';
		loadAssets();
	}

	async function createFolder(parentId: string | null = null) {
		const token = localStorage.token;
		if (!token) return;

		const name = prompt('请输入文件夹名称');
		if (!name || !name.trim()) return;

		const parent = parentId ? folderMap.get(parentId) : null;
		const ownerId = parent?.owner_id ?? currentUser?.id;
		const visibility = parent?.visibility_scope ?? (scope === 'group' ? 'group' : 'user');

		if (!ownerId) {
			toast.error('无法确定文件夹所有者');
			return;
		}

		try {
			const created = await createMediaFolder(token, {
				name: name.trim(),
				owner_id: ownerId,
				visibility_scope: visibility,
				parent_id: parentId ?? undefined
			});
			folders = [...folders, created];
			folderMap.set(created.id, created);
			folderChildren = buildFolderChildren(folders);
			onSelectFolder(created.id);
			toast.success('文件夹已创建');
		} catch (error) {
			toast.error(`创建文件夹失败: ${error}`);
		}
	}

	async function renameFolder(folder: MediaFolder) {
		const token = localStorage.token;
		if (!token) return;

		const name = prompt('重命名文件夹', folder.name);
		if (!name || !name.trim() || name.trim() === folder.name) return;

		try {
			const updated = await updateMediaFolder(token, folder.id, { name: name.trim() });
			folders = folders.map((item) => (item.id === folder.id ? updated : item));
			folderMap.set(updated.id, updated);
			folderChildren = buildFolderChildren(folders);
			breadcrumb = buildBreadcrumb();
			toast.success('文件夹已重命名');
		} catch (error) {
			toast.error(`文件夹重命名失败: ${error}`);
		}
	}

	async function moveFolder(folderId: string, targetParentId: string | null) {
		if (folderId === targetParentId) return;
		const token = localStorage.token;
		if (!token) return;

		if (targetParentId) {
			let current = targetParentId;
			while (current) {
				if (current === folderId) {
					toast.error('不能将文件夹移动到其自身或子层级');
					return;
				}
				const parent = folderMap.get(current);
				current = parent?.parent_id ?? null;
			}
		}

		try {
			const updated = await updateMediaFolder(token, folderId, {
				parent_id: targetParentId ?? undefined
			});
			folders = folders.map((item) => (item.id === folderId ? updated : item));
			folderMap.set(updated.id, updated);
			folderChildren = buildFolderChildren(folders);
			breadcrumb = buildBreadcrumb();
			toast.success('文件夹已移动');
		} catch (error) {
			toast.error(`移动文件夹失败: ${error}`);
		}
	}

	function toggleSelectAsset(assetId: string) {
		if (selectedIds.includes(assetId)) {
			selectedIds = selectedIds.filter((id) => id !== assetId);
		} else {
			selectedIds = [...selectedIds, assetId];
		}
	}

	function toggleSelectAll() {
		if (selectedIds.length === filteredAssets.length) {
			selectedIds = [];
		} else {
			selectedIds = filteredAssets.map((asset) => asset.id);
		}
	}

	async function renameAsset(asset: MediaAsset) {
		const token = localStorage.token;
		if (!token) return;

		const newName = prompt('重命名素材', resolveAssetTitle(asset));
		if (!newName || !newName.trim() || newName.trim() === asset.display_name) return;

		try {
			await updateMediaAsset(token, asset.id, { display_name: newName.trim() });
			toast.success('素材已重命名');
			await loadAssets();
		} catch (error) {
			toast.error(`素材重命名失败: ${error}`);
		}
	}

	async function moveAsset(asset: MediaAsset, folderId: string | null) {
		const token = localStorage.token;
		if (!token) return;

		try {
			await updateMediaAsset(token, asset.id, { folder_id: folderId ?? null });
			toast.success('素材已移动');
			await loadAssets();
		} catch (error) {
			toast.error(`素材移动失败: ${error}`);
		}
	}

	async function removeAsset(asset: MediaAsset) {
		const token = localStorage.token;
		if (!token) return;

		await deleteMediaAsset(token, asset.id);
		toast.success('素材已删除');
		selectedIds = selectedIds.filter((id) => id !== asset.id);
		await loadAssets();
	}

	async function restoreAsset(asset: MediaAsset) {
		const token = localStorage.token;
		if (!token) return;

		await restoreMediaAsset(token, asset.id);
		toast.success('素材已恢复');
		await loadAssets();
	}

	async function bulkMove() {
		if (!selectedIds.length) return;
		const token = localStorage.token;
		if (!token) return;

		const targetFolderId = bulkMoveFolderId || selectedFolderId || null;

		await Promise.all(
			selectedIds.map((id) => updateMediaAsset(token, id, { folder_id: targetFolderId }))
		);
		toast.success('素材已批量移动');
		await loadAssets();
	}

	async function bulkDelete() {
		if (!selectedIds.length) return;
		const token = localStorage.token;
		if (!token) return;

		await Promise.all(selectedIds.map((id) => deleteMediaAsset(token, id)));
		toast.success('素材已批量删除');
		selectedIds = [];
		await loadAssets();
	}

	async function bulkDownload() {
		const targets = assets.filter((asset) => selectedIds.includes(asset.id));
		if (!targets.length) return;
		let missing = 0;
		for (const asset of targets) {
			const url =
				resolveAssetDownloadUrl(asset) ?? asset.file?.cloud_url ?? asset.thumbnail_url ?? null;
			if (url) {
				window.open(url, '_blank');
			} else {
				missing += 1;
			}
		}
		if (missing) {
			toast.error(`有 ${missing} 个素材缺少可用链接`);
		}
	}

	function copyPath(asset: MediaAsset) {
		const url = buildAssetContentUrl(asset) ?? asset.file?.cloud_url ?? asset.thumbnail_url ?? null;
		if (!url) {
			toast.error('无法复制路径');
			return;
		}
		navigator.clipboard.writeText(url);
		toast.success('已复制路径');
	}

	function formatFileSize(bytes?: number | null): string {
		if (!bytes) return '-';
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
		return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`;
	}

	function formatDuration(seconds?: number | null): string {
		if (!seconds || Number.isNaN(seconds)) return '-';
		const totalSeconds = Math.floor(seconds);
		const mins = Math.floor(totalSeconds / 60)
			.toString()
			.padStart(2, '0');
		const secs = (totalSeconds % 60).toString().padStart(2, '0');
		return `${mins}:${secs}`;
	}

	function resolveAssetTitle(asset: MediaAsset): string {
		const metadata = (asset.metadata ?? {}) as Record<string, unknown>;
		const tags = (asset.tags ?? {}) as Record<string, unknown>;
		const candidates = [
			metadata.prompt,
			metadata.title,
			metadata.name,
			tags.prompt,
			tags.title,
			asset.display_name,
			asset.file?.id,
			asset.id
		];
		for (const value of candidates) {
			if (typeof value === 'string' && value.trim().length) {
				return value.trim();
			}
		}
		return asset.id;
	}

	function currentFolderChildren(parentId: string | null): MediaFolder[] {
		return folderChildren.get(parentId ?? null) ?? [];
	}

	function handleFolderDragStart(folderId: string) {
		draggedFolderId = folderId;
	}

	function handleFolderDrop(targetFolderId: string | null) {
		if (draggedFolderId) {
			moveFolder(draggedFolderId, targetFolderId);
			draggedFolderId = null;
		}
	}

	async function handleFileSelection(event: Event) {
		const input = event.currentTarget as HTMLInputElement;
		const files = input.files;
		if (!files || !files.length) {
			return;
		}

		const token = localStorage.token;
		if (!token) {
			toast.error('请先登录后再上传媒体文件');
			return;
		}

		isUploading = true;
		const uploadedAssets: MediaAsset[] = [];
		try {
			const folder = selectedFolderId ? (folderMap.get(selectedFolderId) ?? null) : null;
			let uploadVisibility: 'user' | 'group' = 'user';
			let uploadOwnerId: string | undefined = currentUser?.id ?? undefined;

			if (folder && folder.visibility_scope === 'group') {
				uploadVisibility = 'group';
				uploadOwnerId = folder.owner_id;
			}

			for (const file of Array.from(files)) {
				const baseTitle = file.name.replace(/\.[^.]+$/, '').slice(0, 120);
				const asset = await uploadMediaAsset(token, file, {
					folderId: selectedFolderId ?? undefined,
					visibilityScope: uploadVisibility,
					ownerId: uploadVisibility === 'group' ? uploadOwnerId : undefined,
					title: baseTitle || undefined
				});
				uploadedAssets.push(asset);
			}

			if (uploadedAssets.length) {
				assets = [...uploadedAssets, ...assets];
				currentPage = 1;
				filteredAssets = applyFilters(assets);
				selectedIds = [];
				toast.success(`已上传 ${uploadedAssets.length} 个文件`);
			}
		} catch (error) {
			console.error(error);
			toast.error(`上传失败：${error instanceof Error ? error.message : error}`);
		} finally {
			isUploading = false;
			if (input) {
				input.value = '';
			}
		}
	}

	function clearFilters() {
		searchTerm = '';
		tagKeyword = '';
		timeRange = 'all';
		mediaType = 'all';
		includeDeleted = false;
		loadAssets();
	}

	function goToPreviousPage() {
		if (currentPage > 1) {
			currentPage -= 1;
		}
	}

	function goToNextPage() {
		if (currentPage < totalPages) {
			currentPage += 1;
		}
	}

	function setAsWorkflowInput() {
		toast.info('设为输入暂未接入当前流程');
	}
</script>

<svelte:head>
	<title>媒体库 · Open WebUI</title>
</svelte:head>

<div
	class={`relative flex h-screen max-h-[100dvh] w-full flex-col transition-[max-width] duration-200 ${$showSidebar ? 'md:max-w-[calc(100%-260px)]' : 'max-w-full'}`}
>
	<div class="media-library-page flex h-full flex-1 flex-col overflow-hidden">
		<div class="flex h-full flex-1 overflow-hidden">
			<aside
				class="hidden w-64 shrink-0 border-r border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900/40 lg:flex lg:flex-col"
			>
				<div class="flex items-center justify-between px-4 py-4">
					<h2 class="text-sm font-semibold text-gray-700 dark:text-gray-200">文件夹</h2>
					<button
						class="text-xs text-blue-600 hover:underline dark:text-blue-400"
						on:click={() => createFolder(selectedFolderId)}
					>
						新建
					</button>
				</div>
				<div class="flex-1 overflow-y-auto px-2 pb-6">
					{#if loadingFolders}
						<div class="py-4 text-center text-xs text-gray-500 dark:text-gray-400">加载文件夹…</div>
					{:else}
						<div class="space-y-1">
							<button
								class={`flex w-full items-center justify-between rounded-md px-3 py-2 text-xs ${selectedFolderId === null ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800/60'}`}
								on:click={() => onSelectFolder(null)}
							>
								<span>全部资产</span>
								<span class="text-[10px]">{filteredAssets.length}</span>
							</button>
							<div
								class="rounded-md"
								on:dragover={(event) => event.preventDefault()}
								on:drop={(event) => handleFolderDrop(null)}
							>
								<FolderTree
									getChildren={currentFolderChildren}
									parentId={null}
									selectedId={selectedFolderId}
									on:select={(event) => onSelectFolder(event.detail)}
									on:create={(event) => createFolder(event.detail)}
									on:rename={(event) => renameFolder(event.detail)}
									on:drop={(event) => handleFolderDrop(event.detail)}
									on:dragStart={(event) => handleFolderDragStart(event.detail)}
								/>
							</div>
						</div>
					{/if}
				</div>
			</aside>

			<main class="flex flex-1 flex-col overflow-hidden">
				<section
					class="border-b border-gray-200 bg-white px-4 py-4 dark:border-gray-800 dark:bg-gray-900"
				>
					<div
						class="mb-3 flex flex-wrap items-center gap-2 text-sm text-gray-500 dark:text-gray-400"
					>
						{#each breadcrumb as crumb, index}
							<button
								class={`flex items-center gap-1 text-xs ${index === breadcrumb.length - 1 ? 'font-semibold text-blue-600 dark:text-blue-300' : 'text-gray-600 hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-300'}`}
								on:click={() => onSelectFolder(crumb.id)}
							>
								{crumb.name}
							</button>
							{#if index !== breadcrumb.length - 1}
								<span class="text-xs text-gray-400">/</span>
							{/if}
						{/each}
					</div>
					<div class="flex flex-wrap items-center gap-3">
						<div class="relative flex-1 min-w-[220px]">
							<input
								class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-gray-700 dark:bg-gray-900"
								placeholder="搜索名称、来源或文件夹"
								bind:value={searchTerm}
							/>
							<button
								class="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
								on:click={clearFilters}
							>
								清除
							</button>
						</div>
						<select
							bind:value={scope}
							class="h-9 rounded-lg border border-gray-200 bg-white px-3 text-sm dark:border-gray-700 dark:bg-gray-900"
							on:change={async () => {
								selectedFolderId = null;
								selectedIds = [];
								await loadFolders();
								await loadAssets();
							}}
						>
							{#each scopeOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
						<select
							bind:value={mediaType}
							class="h-9 rounded-lg border border-gray-200 bg-white px-3 text-sm dark:border-gray-700 dark:bg-gray-900"
							on:change={loadAssets}
						>
							{#each mediaTypeOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
						<select
							bind:value={timeRange}
							class="h-9 rounded-lg border border-gray-200 bg-white px-3 text-sm dark:border-gray-700 dark:bg-gray-900"
						>
							{#each timeRangeOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
						<input
							class="h-9 w-40 rounded-lg border border-gray-200 bg-white px-3 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-gray-700 dark:bg-gray-900"
							placeholder="标签关键字"
							bind:value={tagKeyword}
						/>
						<label class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
							<input type="checkbox" bind:checked={includeDeleted} on:change={loadAssets} />
							显示已删除
						</label>
						<input
							class="hidden"
							type="file"
							accept="image/*,video/*"
							multiple
							bind:this={uploadInput}
							on:change={handleFileSelection}
						/>
						<button
							class={`flex items-center gap-2 rounded-lg border border-blue-200 px-3 py-2 text-sm font-medium text-blue-600 shadow-sm transition hover:bg-blue-50 disabled:cursor-wait disabled:opacity-70 dark:border-blue-400/40 dark:text-blue-200 dark:hover:bg-blue-900/40 ${isUploading ? 'cursor-wait' : ''}`}
							on:click={() => uploadInput?.click()}
							disabled={isUploading}
						>
							{isUploading ? '上传中…' : '上传文件'}
						</button>
					</div>
				</section>

				<section class="relative flex flex-1 flex-col overflow-hidden">
					{#if loadingAssets}
						<div
							class="flex h-full items-center justify-center text-sm text-gray-500 dark:text-gray-400"
						>
							正在加载媒体资产…
						</div>
					{:else if filteredAssets.length === 0}
						<div
							class="m-6 flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 bg-white p-10 text-sm text-gray-500 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400"
						>
							暂无媒体资产
						</div>
					{:else}
						<div class="flex flex-1 flex-col">
							<div
								class="grid flex-1 gap-4 overflow-y-auto p-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
							>
								{#each paginatedAssets as asset}
									{@const assetTitle = resolveAssetTitle(asset)}
									<article
										class={`group relative flex cursor-pointer flex-col overflow-hidden rounded-2xl border border-transparent bg-white shadow-[0_12px_28px_-20px_rgba(15,23,42,0.55)] transition-all duration-200 hover:-translate-y-[2px] hover:shadow-[0_18px_32px_-18px_rgba(15,23,42,0.6)] dark:bg-slate-900/95 ${selectedIds.includes(asset.id) ? 'ring-2 ring-offset-2 ring-blue-500 dark:ring-blue-400 dark:ring-offset-slate-950' : ''}`}
										on:click={() => toggleSelectAsset(asset.id)}
									>
										<input
											type="checkbox"
											class="absolute right-4 top-4 z-30 size-4 rounded border-slate-300 text-blue-500 shadow-sm focus:ring-blue-300 dark:border-slate-600"
											checked={selectedIds.includes(asset.id)}
											on:click|stopPropagation={() => toggleSelectAsset(asset.id)}
										/>
										<div
											class="relative aspect-[4/3] overflow-hidden bg-slate-100 dark:bg-slate-800"
										>
											<span
												class="absolute left-3 top-3 z-20 inline-flex items-center gap-1 rounded-full bg-black/55 px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wide text-white shadow"
											>
												<span class="inline-block size-2 rounded-full bg-emerald-300"></span>
												{asset.media_type === 'video' ? '视频' : '图片'}
											</span>

											{#if asset.media_type === 'image' && resolveAssetPreviewUrl(asset)}
												<img
													src={resolveAssetPreviewUrl(asset) ?? ''}
													alt={assetTitle}
													class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
													loading="lazy"
												/>
											{:else if asset.media_type === 'video' && resolveAssetPreviewUrl(asset)}
												<VideoPreview
													src={resolveAssetPreviewUrl(asset) ?? ''}
													poster={asset.thumbnail_url ?? undefined}
													className="h-full w-full"
												>
													<div
														slot="fallback"
														class="flex h-full w-full flex-col items-center justify-center gap-2 text-slate-300"
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															fill="none"
															viewBox="0 0 24 24"
															stroke-width="1.5"
															stroke="currentColor"
															class="size-10"
														>
															<path
																stroke-linecap="round"
																stroke-linejoin="round"
																d="M15.75 10.5l4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9A2.25 2.25 0 0 0 15.75 16.5v-9A2.25 2.25 0 0 0 13.5 5.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
															/>
														</svg>
														<span class="text-xs uppercase tracking-wide">视频</span>
													</div>
												</VideoPreview>
												<span
													class="absolute bottom-3 left-3 z-20 flex items-center gap-1 rounded-full bg-black/60 px-2.5 py-0.5 text-[10px] font-medium text-white shadow"
												>
													▶︎ {formatDuration(asset.duration)}
												</span>
											{:else}
												<div
													class="flex h-full w-full flex-col items-center justify-center gap-2 text-slate-400"
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														fill="none"
														viewBox="0 0 24 24"
														stroke-width="1.5"
														stroke="currentColor"
														class="size-10"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															d="M15.75 10.5l4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9A2.25 2.25 0 0 0 15.75 16.5v-9A2.25 2.25 0 0 0 13.5 5.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
														/>
													</svg>
													<span class="text-xs uppercase tracking-wide">未知</span>
												</div>
											{/if}

											<div
												class="pointer-events-none absolute inset-x-0 bottom-0 z-20 bg-gradient-to-t from-black/75 via-black/10 to-transparent p-3"
											>
												<p class="line-clamp-2 text-sm font-semibold text-white drop-shadow">
													{assetTitle}
												</p>
												<div
													class="mt-1 flex flex-wrap items-center gap-3 text-[11px] text-slate-100/90"
												>
													<span
														>{asset.created_at
															? new Date(asset.created_at).toLocaleString()
															: '-'}</span
													>
													<span class="inline-flex items-center gap-1">
														<span class="inline-block size-1.5 rounded-full bg-emerald-300"></span>
														{asset.visibility_scope === 'group' ? '工作组' : '个人'}
													</span>
													{#if asset.media_type === 'video'}
														<span>{formatDuration(asset.duration)}</span>
													{:else if asset.width && asset.height}
														<span>{asset.width}×{asset.height}</span>
													{/if}
												</div>
											</div>
										</div>

										<footer
											class="flex flex-1 flex-col gap-3 bg-white px-4 py-3 text-xs text-slate-600 dark:bg-slate-950/90 dark:text-slate-300"
										>
											<div class="flex items-center justify-between gap-3">
												<div class="flex min-w-0 flex-1 flex-col gap-1">
													<span
														class="line-clamp-2 text-sm font-semibold text-slate-800 dark:text-slate-100"
														title={assetTitle}
													>
														{assetTitle}
													</span>
													<span
														class="text-[11px] uppercase tracking-wide text-slate-400 dark:text-slate-500"
														>{asset.source ?? '未知来源'}</span
													>
												</div>
												{#if asset.file?.cloud_url}
													<button
														class="rounded-full bg-blue-500/10 px-3 py-1 text-[11px] font-medium text-blue-600 transition hover:bg-blue-500/20 dark:bg-blue-500/20 dark:text-blue-200 dark:hover:bg-blue-500/30"
														on:click|stopPropagation={() => {
															const url =
																resolveAssetDownloadUrl(asset) ?? asset.file?.cloud_url ?? '#';
															window.open(url, '_blank');
														}}
													>
														下载
													</button>
												{/if}
											</div>
											<div
												class="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-slate-500 dark:text-slate-400"
											>
												<div class="flex items-center gap-1">
													<span class="text-slate-400">文件夹</span>
													<span class="truncate font-medium text-slate-600 dark:text-slate-200"
														>{asset.folder_id
															? (folderMap.get(asset.folder_id)?.name ?? asset.folder_id)
															: '—'}</span
													>
												</div>
												<div class="flex items-center justify-end gap-1">
													<span class="text-slate-400">大小</span>
													<span class="font-medium text-slate-600 dark:text-slate-200"
														>{formatFileSize(asset.file?.file_size)}</span
													>
												</div>
											</div>
										</footer>
									</article>
								{/each}
							</div>

							{#if totalPages > 1}
								<div
									class="flex items-center justify-between border-t border-gray-100 bg-white px-6 py-4 text-xs text-gray-500 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400"
								>
									<div>共 {filteredAssets.length} 项</div>
									<div class="flex items-center gap-3">
										<button
											class="rounded-md border border-gray-200 px-3 py-1 text-xs font-medium text-gray-600 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
											on:click={goToPreviousPage}
											disabled={currentPage === 1}
										>
											上一页
										</button>
										<span class="text-xs">第 {currentPage} / {totalPages} 页</span>
										<button
											class="rounded-md border border-gray-200 px-3 py-1 text-xs font-medium text-gray-600 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
											on:click={goToNextPage}
											disabled={currentPage === totalPages}
										>
											下一页
										</button>
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</section>
			</main>

			{#if selectedAssets.length}
				<aside
					class="w-80 shrink-0 border-l border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900"
				>
					{#if selectedAssets.length > 1}
						<div class="pb-4 text-sm font-semibold text-blue-600 dark:text-blue-300">
							已选择 {selectedAssets.length} 个素材
						</div>
					{/if}
					{#if selectedAssets.length}
						{#each selectedAssets.slice(0, 1) as asset}
							<div class="space-y-4 text-sm text-gray-600 dark:text-gray-200">
								<div>
									<div class="text-xs text-gray-400 dark:text-gray-500">标题</div>
									<div class="font-semibold text-gray-900 dark:text-gray-100">
										{resolveAssetTitle(asset)}
									</div>
								</div>
								<div class="grid grid-cols-2 gap-3 text-xs">
									<div>
										<div class="text-gray-400 dark:text-gray-500">类型</div>
										<div>{asset.media_type === 'video' ? '视频' : '图片'}</div>
									</div>
									<div>
										<div class="text-gray-400 dark:text-gray-500">大小</div>
										<div>{formatFileSize(asset.file?.file_size)}</div>
									</div>
									<div>
										<div class="text-gray-400 dark:text-gray-500">分辨率</div>
										<div>
											{asset.width && asset.height ? `${asset.width} × ${asset.height}` : '-'}
										</div>
									</div>
									<div>
										<div class="text-gray-400 dark:text-gray-500">时长</div>
										<div>{asset.media_type === 'video' ? formatDuration(asset.duration) : '-'}</div>
									</div>
									<div>
										<div class="text-gray-400 dark:text-gray-500">所属文件夹</div>
										<div>
											{asset.folder_id
												? (folderMap.get(asset.folder_id)?.name ?? asset.folder_id)
												: '—'}
										</div>
									</div>
									<div>
										<div class="text-gray-400 dark:text-gray-500">可见性</div>
										<div>{asset.visibility_scope === 'group' ? '工作组' : '个人'}</div>
									</div>
									<div>
										<div class="text-gray-400 dark:text-gray-500">来源</div>
										<div>{asset.source ?? '-'}</div>
									</div>
									<div>
										<div class="text-gray-400 dark:text-gray-500">创建者</div>
										<div>{asset.created_by_user_id ?? '-'}</div>
									</div>
								</div>

								<div class="flex flex-col gap-2">
									<button
										class="rounded-lg border border-gray-200 px-3 py-1.5 text-xs hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
										on:click={() => renameAsset(asset)}
									>
										重命名
									</button>
									<button
										class="rounded-lg border border-gray-200 px-3 py-1.5 text-xs hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
										on:click={() => moveAsset(asset, selectedFolderId)}
									>
										移动到当前文件夹
									</button>
									<button
										class="rounded-lg border border-gray-200 px-3 py-1.5 text-xs hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
										on:click={() => {
											const url = resolveAssetDownloadUrl(asset) ?? asset.file?.cloud_url ?? '#';
											window.open(url, '_blank');
										}}
									>
										下载
									</button>
									<button
										class="rounded-lg border border-gray-200 px-3 py-1.5 text-xs hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
										on:click={() => copyPath(asset)}
									>
										复制路径
									</button>
									<button
										class="rounded-lg border border-gray-200 px-3 py-1.5 text-xs hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
										on:click={setAsWorkflowInput}
									>
										设为输入
									</button>
									{#if asset.deleted_at}
										<button
											class="rounded-lg border border-emerald-200 px-3 py-1.5 text-xs text-emerald-700 hover:bg-emerald-50 dark:border-emerald-700/60 dark:text-emerald-300 dark:hover:bg-emerald-900/30"
											on:click={() => restoreAsset(asset)}
										>
											恢复
										</button>
									{:else}
										<button
											class="rounded-lg border border-red-200 px-3 py-1.5 text-xs text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-900/30"
											on:click={() => removeAsset(asset)}
										>
											删除
										</button>
									{/if}
								</div>
							</div>
						{/each}
					{/if}
				</aside>
			{/if}
		</div>
	</div>

	{#if selectedIds.length}
		<div
			class="sticky bottom-0 flex items-center border-t border-gray-200 bg-white px-6 py-3 shadow-lg dark:border-gray-800 dark:bg-gray-900"
		>
			<div class="flex flex-1 items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
				<span>已选择 {selectedIds.length} 项</span>
				<label class="flex items-center gap-2 text-xs">
					目标文件夹：
					<select
						class="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs dark:border-gray-700 dark:bg-gray-900"
						bind:value={bulkMoveFolderId}
					>
						<option value="">默认（当前文件夹）</option>
						{#each folders as folder}
							<option value={folder.id}>{folder.name}</option>
						{/each}
					</select>
				</label>
			</div>
			<div class="flex items-center gap-3 text-xs">
				<button
					class="rounded-lg border border-gray-200 px-3 py-1.5 hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
					on:click={bulkMove}
				>
					批量移动
				</button>
				<button
					class="rounded-lg border border-gray-200 px-3 py-1.5 hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
					on:click={bulkDownload}
				>
					批量下载
				</button>
				<button
					class="rounded-lg border border-red-200 px-3 py-1.5 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-300 dark:hover:bg-red-900/30"
					on:click={bulkDelete}
				>
					批量删除
				</button>
				<button
					class="rounded-lg border border-gray-200 px-3 py-1.5 hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
					on:click={toggleSelectAll}
				>
					{selectedIds.length === filteredAssets.length ? '取消全选' : '全选'}
				</button>
			</div>
		</div>
	{/if}
</div>
