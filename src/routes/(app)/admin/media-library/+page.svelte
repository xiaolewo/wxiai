<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { showSidebar } from '$lib/stores';
	import {
		adminGetMediaLibrarySettings,
		adminUpdateSettings,
		adminListMediaAssets,
		adminReassignAsset,
		deleteMediaAsset,
		restoreMediaAsset,
		type MediaLibrarySettingsForm,
		type MediaAsset
	} from '$lib/apis/media-library';

	const i18n = getContext('i18n');

	let settingsForm: MediaLibrarySettingsForm = {
		enable_group_sharing: false,
		allow_bulk_download: true,
		allowed_media_types: null,
		default_visibility: 'user',
		max_storage_per_user: null,
		max_storage_per_group: null,
		signed_url_ttl_seconds: null,
		thumbnail_strategy: null,
		extra_config: null
	};

	let loadingSettings = true;
	let savingSettings = false;
	let assets: MediaAsset[] = [];
	let assetsLoading = true;
	let assetPage = 1;
	let assetLimit = 20;
	let assetTotal = 0;
	let assetOwnerFilter = '';
	let assetVisibilityFilter = '';

	onMount(async () => {
		try {
			await Promise.all([loadSettings(), loadAssets()]);
		} catch (error) {
			toast.error(`${error}`);
		}
	});

	async function loadSettings() {
		const token = localStorage.token;
		if (!token) return;
		loadingSettings = true;
		try {
			const data = await adminGetMediaLibrarySettings(token);
			settingsForm = {
				enable_group_sharing: data.enable_group_sharing,
				allow_bulk_download: data.allow_bulk_download,
				allowed_media_types: data.allowed_media_types,
				default_visibility: data.default_visibility,
				max_storage_per_user: data.max_storage_per_user,
				max_storage_per_group: data.max_storage_per_group,
				signed_url_ttl_seconds: data.signed_url_ttl_seconds,
				thumbnail_strategy: data.thumbnail_strategy,
				extra_config: data.extra_config
			};
		} finally {
			loadingSettings = false;
		}
	}

	async function saveSettings() {
		const token = localStorage.token;
		if (!token) return;
		savingSettings = true;
		try {
			await adminUpdateSettings(token, settingsForm);
			toast.success($i18n.t('设置已保存。'));
			await loadSettings();
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			savingSettings = false;
		}
	}

	async function loadAssets() {
		const token = localStorage.token;
		if (!token) return;
		assetsLoading = true;
		try {
			const response = await adminListMediaAssets(token, {
				page: assetPage,
				limit: assetLimit,
				ownerId: assetOwnerFilter || undefined,
				visibilityScope: assetVisibilityFilter || undefined,
				includeDeleted: true
			});
			assets = response.data;
			assetTotal = response.total;
		} finally {
			assetsLoading = false;
		}
	}

	async function reassignAsset(asset: MediaAsset) {
		const token = localStorage.token;
		if (!token) return;
		const newOwner = prompt($i18n.t('请输入新的所属主体 ID'), asset.owner_id);
		if (!newOwner || newOwner.trim() === '') return;
		const newScope = prompt($i18n.t('请输入新的可见范围（user 或 group）'), asset.visibility_scope);
		if (!newScope || !['user', 'group'].includes(newScope)) {
			toast.error($i18n.t('可见范围不正确。'));
			return;
		}
		await adminReassignAsset(token, asset.id, {
			owner_id: newOwner.trim(),
			visibility_scope: newScope as 'user' | 'group'
		});
		toast.success($i18n.t('资产已重新分配。'));
		await loadAssets();
	}

	async function removeAsset(asset: MediaAsset) {
		const token = localStorage.token;
		if (!token) return;
		await deleteMediaAsset(token, asset.id);
		toast.success($i18n.t('资产已移除。'));
		await loadAssets();
	}

	async function restoreAssetHandler(asset: MediaAsset) {
		const token = localStorage.token;
		if (!token) return;
		await restoreMediaAsset(token, asset.id);
		toast.success($i18n.t('资产已恢复。'));
		await loadAssets();
	}
</script>

<svelte:head>
	<title>{$i18n.t('媒体库管理')} · Open WebUI</title>
</svelte:head>

<div
	class="relative flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-260px)]'
		: ''} max-w-full"
>
	<div class="page-container flex-1 w-full max-w-6xl mx-auto flex flex-col gap-8 p-6">
		<section
			class="border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-900 p-6 shadow-sm"
		>
			<header class="flex items-center justify-between mb-4">
				<h1 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
					{$i18n.t('媒体库设置')}
				</h1>
			</header>

			{#if loadingSettings}
				<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('正在加载设置…')}</div>
			{:else}
				<form class="flex flex-col gap-4" on:submit|preventDefault={saveSettings}>
					<label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
						<input type="checkbox" bind:checked={settingsForm.enable_group_sharing} />
						{$i18n.t('启用工作组共享')}
					</label>

					<label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
						<input type="checkbox" bind:checked={settingsForm.allow_bulk_download} />
						{$i18n.t('允许批量下载')}
					</label>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
						<label class="flex flex-col gap-1">
							<span class="text-gray-600 dark:text-gray-400">{$i18n.t('默认可见范围')}</span>
							<select
								bind:value={settingsForm.default_visibility}
								class="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
							>
								<option value="user">{$i18n.t('个人')}</option>
								<option value="group">{$i18n.t('工作组')}</option>
							</select>
						</label>

						<label class="flex flex-col gap-1">
							<span class="text-gray-600 dark:text-gray-400">{$i18n.t('签名链接有效期（秒）')}</span
							>
							<input
								type="number"
								min="0"
								bind:value={settingsForm.signed_url_ttl_seconds}
								class="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
							/>
						</label>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
						<label class="flex flex-col gap-1">
							<span class="text-gray-600 dark:text-gray-400"
								>{$i18n.t('单个用户最大存储（MB）')}</span
							>
							<input
								type="number"
								min="0"
								bind:value={settingsForm.max_storage_per_user}
								class="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
							/>
						</label>

						<label class="flex flex-col gap-1">
							<span class="text-gray-600 dark:text-gray-400"
								>{$i18n.t('单个工作组最大存储（MB）')}</span
							>
							<input
								type="number"
								min="0"
								bind:value={settingsForm.max_storage_per_group}
								class="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
							/>
						</label>
					</div>

					<button
						type="submit"
						class="self-start px-4 py-2 text-sm rounded-lg border border-transparent bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
						disabled={savingSettings}
					>
						{savingSettings ? $i18n.t('Saving...') : $i18n.t('Save Settings')}
					</button>
				</form>
			{/if}
		</section>

		<section
			class="border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-900 p-6 shadow-sm"
		>
			<header class="flex items-center justify-between mb-4">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
					{$i18n.t('媒体资产')}
				</h2>
				<div class="flex gap-2">
					<input
						type="text"
						placeholder={$i18n.t('按所属主体筛选')}
						bind:value={assetOwnerFilter}
						class="px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
					/>
					<select
						bind:value={assetVisibilityFilter}
						class="px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
					>
						<option value="">{$i18n.t('全部范围')}</option>
						<option value="user">{$i18n.t('个人')}</option>
						<option value="group">{$i18n.t('工作组')}</option>
					</select>
					<button
						class="px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
						on:click={() => {
							assetPage = 1;
							loadAssets();
						}}
					>
						{$i18n.t('应用')}
					</button>
				</div>
			</header>

			{#if assetsLoading}
				<div class="text-sm text-gray-500 dark:text-gray-400">{$i18n.t('正在加载资产…')}</div>
			{:else if assets.length === 0}
				<div class="text-sm text-gray-500 dark:text-gray-400">
					{$i18n.t('当前筛选条件下暂无资产。')}
				</div>
			{:else}
				<div class="overflow-x-auto">
					<table class="min-w-full text-sm">
						<thead class="text-left uppercase text-xs text-gray-500 dark:text-gray-400">
							<tr>
								<th class="py-2 pr-4">{$i18n.t('名称')}</th>
								<th class="py-2 pr-4">{$i18n.t('所属主体')}</th>
								<th class="py-2 pr-4">{$i18n.t('可见范围')}</th>
								<th class="py-2 pr-4">{$i18n.t('类型')}</th>
								<th class="py-2 pr-4">{$i18n.t('创建时间')}</th>
								<th class="py-2 pr-4 text-right">{$i18n.t('操作')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-800">
							{#each assets as asset}
								<tr>
									<td class="py-2 pr-4 max-w-[200px] truncate" title={asset.display_name}
										>{asset.display_name}</td
									>
									<td class="py-2 pr-4 text-gray-600 dark:text-gray-400">{asset.owner_id}</td>
									<td class="py-2 pr-4">{asset.visibility_scope}</td>
									<td class="py-2 pr-4">{asset.media_type}</td>
									<td class="py-2 pr-4 text-gray-500 dark:text-gray-400"
										>{new Date(asset.created_at).toLocaleString()}</td
									>
									<td class="py-2 pr-4">
										<div class="flex gap-2 justify-end">
											<button
												class="px-3 py-1 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
												on:click={() => reassignAsset(asset)}
											>
												{$i18n.t('重新分配')}
											</button>
											{#if asset.deleted_at}
												<button
													class="px-3 py-1 rounded-lg border border-emerald-200 text-emerald-700 dark:border-emerald-800 dark:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/40"
													on:click={() => restoreAssetHandler(asset)}
												>
													{$i18n.t('Restore')}
												</button>
											{:else}
												<button
													class="px-3 py-1 rounded-lg border border-red-200 text-red-600 dark:border-red-800 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/40"
													on:click={() => removeAsset(asset)}
												>
													{$i18n.t('删除')}
												</button>
											{/if}
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				{#if assetTotal > assetLimit}
					<div
						class="flex justify-end items-center gap-3 text-sm text-gray-600 dark:text-gray-300 mt-4"
					>
						<button
							class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-50"
							disabled={assetPage === 1}
							on:click={async () => {
								assetPage = Math.max(1, assetPage - 1);
								await loadAssets();
							}}
						>
							{$i18n.t('上一页')}
						</button>
						<span>{$i18n.t('页码')} {assetPage} / {Math.ceil(assetTotal / assetLimit)}</span>
						<button
							class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-50"
							disabled={assetPage * assetLimit >= assetTotal}
							on:click={async () => {
								assetPage = assetPage + 1;
								await loadAssets();
							}}
						>
							{$i18n.t('下一页')}
						</button>
					</div>
				{/if}
			{/if}
		</section>
	</div>
</div>
