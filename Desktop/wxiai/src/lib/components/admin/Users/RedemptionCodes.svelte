<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import {
		getRedemptionCodes,
		deleteRedemptionCode,
		exportRedemptionCodes
	} from '$lib/apis/credit';
	import CreateRedemptionCodeModal from './CreateRedemptionCodeModal.svelte';
	import EditRedemptionCodeModal from './EditRedemptionCodeModal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let page = 1;
	let limit = 30;
	let total = null;
	let keyword = '';
	let codes: any[] = [];

	let showCreateModal = false;
	let showEditModal = false;
	let selectedCode: any = null;

	$: if (page) {
		loadCodes();
	}

	$: if (keyword !== undefined) {
		page = 1;
		loadCodes();
	}

	const loadCodes = async () => {
		try {
			const data = await getRedemptionCodes(localStorage.token, page, limit, keyword);
			if (data) {
				total = data.total ?? 0;
				codes = data.results ?? [];
			}
		} catch (error) {
			toast.error(`Failed to load redemption codes: ${error}`);
		}
	};

	const handleDelete = async (code: string) => {
		if (!confirm($i18n.t('Are you sure you want to delete this redemption code?'))) {
			return;
		}

		try {
			await deleteRedemptionCode(localStorage.token, code);
			toast.success($i18n.t('Redemption code deleted successfully'));
			await loadCodes();
		} catch (error) {
			toast.error(`Failed to delete redemption code: ${error}`);
		}
	};

	const handleEdit = (code: any) => {
		selectedCode = code;
		showEditModal = true;
	};

	const handleExport = async () => {
		if (!keyword.trim()) {
			toast.error($i18n.t('Please enter a keyword to export'));
			return;
		}

		try {
			const response = await exportRedemptionCodes(localStorage.token, keyword);
			if (response) {
				const blob = await response.blob();
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = `${keyword}.csv`;
				document.body.appendChild(a);
				a.click();
				window.URL.revokeObjectURL(url);
				document.body.removeChild(a);
				toast.success($i18n.t('Export completed'));
			}
		} catch (error) {
			toast.error(`Export failed: ${error}`);
		}
	};

	const formatDate = (timestamp: number): string => {
		return timestamp ? new Date(timestamp * 1000).toLocaleString() : '-';
	};

	const getStatusText = (code: any): string => {
		if (code.received_at) {
			return $i18n.t('Used');
		}
		if (code.expired_at && code.expired_at < Date.now() / 1000) {
			return $i18n.t('Expired');
		}
		return $i18n.t('Available');
	};

	const getStatusClass = (code: any): string => {
		if (code.received_at) {
			return 'text-gray-500';
		}
		if (code.expired_at && code.expired_at < Date.now() / 1000) {
			return 'text-red-500';
		}
		return 'text-green-500';
	};

	const hideCode = (code: string): string => {
		return code.replace(/(.{4})(.*)(.{4})/, '$1****$3');
	};

	onMount(async () => {
		await loadCodes();
	});
</script>

<CreateRedemptionCodeModal
	bind:show={showCreateModal}
	on:save={async () => {
		page = 1;
		await loadCodes();
	}}
/>

<EditRedemptionCodeModal
	bind:show={showEditModal}
	bind:code={selectedCode}
	on:save={async () => {
		await loadCodes();
	}}
/>

<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
	<div class="flex md:self-center text-lg font-medium px-0.5">
		<div class="flex-shrink-0">
			{$i18n.t('Redemption Codes')}
		</div>
	</div>

	<div class="flex gap-1">
		<div class="flex w-full space-x-2">
			<div>
				<Tooltip content={$i18n.t('Create Redemption Code')}>
					<button
						class="p-2 rounded-xl hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition font-medium text-sm flex items-center space-x-1"
						on:click={() => {
							showCreateModal = true;
						}}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="w-4 h-4"
						>
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
						</svg>
					</button>
				</Tooltip>
			</div>

			<div>
				<Tooltip content={$i18n.t('Export Redemption Codes')}>
					<button
						class="p-2 rounded-xl hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition font-medium text-sm flex items-center space-x-1"
						on:click={handleExport}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="w-4 h-4"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
							/>
						</svg>
					</button>
				</Tooltip>
			</div>

			<div class="flex flex-1 w-full">
				<div class="self-center ml-1 mr-3">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 20 20"
						fill="currentColor"
						class="w-4 h-4"
					>
						<path
							fill-rule="evenodd"
							d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
				<input
					class="w-full text-sm pr-4 py-1 rounded-r-xl outline-hidden bg-transparent"
					bind:value={keyword}
					placeholder={$i18n.t('Search by code or topic')}
				/>
			</div>
		</div>
	</div>
</div>

{#if total === null}
	<div class="my-10">
		<Spinner className="size-5" />
	</div>
{:else}
	<div
		class="mt-2 scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm"
	>
		<table
			class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-auto max-w-full rounded-sm"
		>
			<thead
				class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5"
			>
				<tr>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Redemption Code')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Topic')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Credit Amount')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Status')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Used By')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Used At')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Expired At')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Actions')}
					</th>
				</tr>
			</thead>
			<tbody>
				{#each codes as code}
					<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs group">
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white">
							<div class="line-clamp-1 font-mono text-xs">
								{hideCode(code.code)}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white">
							<div class="line-clamp-1">
								{code.purpose}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white">
							<div class="line-clamp-1">
								{parseFloat(code.amount).toFixed(2)}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium {getStatusClass(code)}">
							<div class="line-clamp-1">
								{getStatusText(code)}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white">
							<div class="line-clamp-1">
								{code.username || '-'}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white">
							<div class="line-clamp-1">
								{formatDate(code.received_at)}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white">
							<div class="line-clamp-1">
								{formatDate(code.expired_at)}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left">
							<div class="flex items-center space-x-1">
								<Tooltip content={$i18n.t('Edit')}>
									<button
										class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
										on:click={() => handleEdit(code)}
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											viewBox="0 0 24 24"
											stroke-width="1.5"
											stroke="currentColor"
											class="w-3 h-3"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
											/>
										</svg>
									</button>
								</Tooltip>

								<Tooltip content={$i18n.t('Delete')}>
									<button
										class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-red-500"
										on:click={() => handleDelete(code.code)}
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											viewBox="0 0 24 24"
											stroke-width="1.5"
											stroke="currentColor"
											class="w-3 h-3"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
											/>
										</svg>
									</button>
								</Tooltip>
							</div>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<Pagination bind:page count={total} perPage={limit} />
{/if}
