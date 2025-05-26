<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { user } from '$lib/stores';
	import { createTradeTicket, getCreditConfig, listCreditLog } from '$lib/apis/credit';
	import { toast } from 'svelte-sonner';
	import { getSessionUser } from '$lib/apis/auths';

	const i18n = getContext('i18n');

	type Model = {
		id: string;
		name: string;
	};
	type APIParams = {
		model: Model;
	};
	type Usage = {
		total_price: number;
		prompt_unit_price: number;
		completion_unit_price: number;
		request_unit_price: number;
		completion_tokens: number;
		prompt_tokens: number;
	};
	type LogDetail = {
		desc: string;
		api_params: APIParams;
		usage: Usage;
	};
	type Log = {
		id: string;
		credit: string;
		detail: LogDetail;
		created_at: number;
	};
	let page = 1;
	let hasMore = true;
	let logs: Array<Log> = [];
	const loadLogs = async (append: boolean) => {
		const data = await listCreditLog(localStorage.token, page).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (data.length === 0) {
			hasMore = false;
		}
		if (append) {
			logs = [...logs, ...data];
		} else {
			logs = data;
		}
	};
	const nextLogs = async () => {
		page++;
		await loadLogs(true);
	};

	let credit = 0;
	let payType = 'alipay';
	let payTypes = [
		{
			code: 'alipay',
			title: $i18n.t('Alipay')
		},
		{
			code: 'wxpay',
			title: $i18n.t('WXPay')
		}
	];
	let amount = null;

	let config = {
		CREDIT_EXCHANGE_RATIO: 0,
		EZFP_PAY_PRIORITY: 'qrcode'
	};

	let tradeInfo = {
		detail: {
			code: -1,
			msg: '',
			payurl: '',
			qrcode: '',
			urlscheme: '',
			img: '',
			imgDisplayUrl: ''
		}
	};

	const showQRCode = (detail: object): Boolean => {
		if (detail?.img) {
			tradeInfo.detail.imgDisplayUrl = detail.img;
			return true;
		}

		if (detail?.qrcode) {
			document.getElementById('trade-qrcode').innerHTML = '';
			new QRCode(document.getElementById('trade-qrcode'), {
				text: detail.qrcode,
				width: 128,
				height: 128,
				colorDark: '#000000',
				colorLight: '#ffffff',
				correctLevel: QRCode.CorrectLevel.H
			});
			return true;
		}

		return false;
	};

	const redirectLink = (detail: object): Boolean => {
		if (detail?.payurl) {
			window.location.href = detail.payurl;
			return true;
		}

		if (detail?.urlscheme) {
			window.location.href = detail.urlscheme;
			return true;
		}

		return false;
	};

	const handleAddCreditClick = async () => {
		const res = await createTradeTicket(localStorage.token, payType, amount).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (res) {
			tradeInfo = res;
			if (tradeInfo.detail === undefined) {
				toast.error('init payment failed');
				return;
			}

			const detail = tradeInfo.detail;
			if (detail?.code !== 1) {
				toast.error(tradeInfo?.detail?.msg);
				return;
			}

			if (config.EZFP_PAY_PRIORITY === 'qrcode') {
				if (showQRCode(detail)) {
					return;
				}
				redirectLink(detail);
			} else {
				if (redirectLink(detail)) {
					return;
				}
				showQRCode(detail);
			}
		}
	};

	const handleWeChatClick = async () => {
		payType = 'wxpay';
		await handleAddCreditClick();
	};

	const handleAlipayClick = async () => {
		payType = 'alipay';
		await handleAddCreditClick();
	};

	const formatDate = (t: number): string => {
		return new Date(t * 1000).toLocaleString();
	};

	const formatDesc = (log: Log): string => {
		const usage = log?.detail?.usage ?? {};
		if (usage && Object.keys(usage).length > 0) {
			if (usage.total_price !== undefined && usage.total_price !== null) {
				return `-${Math.round(usage.total_price * 1e6) / 1e6}`;
			}
			if (usage.request_unit_price) {
				return `-${usage.request_unit_price / 1e6}`;
			}
			if (usage.prompt_unit_price || usage.completion_unit_price) {
				return `-${Math.round(usage.prompt_tokens * usage.prompt_unit_price + usage.completion_tokens * usage.completion_unit_price) / 1e6}`;
			}
		}
		return log?.detail?.desc;
	};

	const doInit = async () => {
		const sessionUser = await getSessionUser(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		await user.set(sessionUser);

		const res = await getCreditConfig(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (res) {
			config = res;
		}

		credit = $user?.credit ? $user?.credit : 0;
		tradeInfo = {};
		document.getElementById('trade-qrcode').innerHTML = '';

		await loadLogs(false);
	};

	onMount(async () => {
		await doInit();
	});
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class=" space-y-3 lg:max-h-full">
		<div class="space-y-1">
		



			{#if !tradeInfo?.detail?.qrcode && !tradeInfo?.detail?.imgDisplayUrl}
				<hr class=" border-gray-100 dark:border-gray-700/10 my-2.5 w-full" />

				<div class="pt-0.5">
					<div class="flex flex-col w-full">
						<div class="mb-1 text-base font-medium">{$i18n.t('Credit Log')}</div>
						<div
							class="overflow-y-scroll max-h-[14rem] flex flex-col scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm"
						>
							{#if logs.length > 0}
								<table
									class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-auto max-w-full rounded-sm}"
								>
									<thead
										class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5"
									>
										<tr>
											<th scope="col" class="px-3 py-1.5 select-none w-3">
												{$i18n.t('Date')}
											</th>
											<th scope="col" class="px-3 py-1.5 select-none w-3">
												{$i18n.t('Credit')}
											</th>
											<th scope="col" class="px-3 py-1.5 select-none w-3">
												{$i18n.t('Model')}
											</th>
											<th scope="col" class="px-3 py-1.5 select-none w-3">
												{$i18n.t('Desc')}
											</th>
										</tr>
									</thead>
									<tbody>
										{#each logs as log}
											<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs group">
												<td
													class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit"
												>
													<div class=" line-clamp-1">
														{formatDate(log.created_at)}
													</div>
												</td>
												<td
													class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit"
												>
													<div class=" line-clamp-1">
														{parseFloat(log.credit).toFixed(6)}
													</div>
												</td>
												<td
													class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit"
												>
													<div class=" line-clamp-1">
														{log.detail?.api_params?.model?.name ||
															log.detail?.api_params?.model?.id ||
															'- -'}
													</div>
												</td>
												<td
													class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit"
												>
													<div class=" line-clamp-1">
														{formatDesc(log)}
													</div>
												</td>
											</tr>
										{/each}
									</tbody>
								</table>
								{#if hasMore}
									<button
										class="text-xs mt-2"
										type="button"
										on:click={() => {
											nextLogs(true);
										}}
									>
										{$i18n.t('Load More')}
									</button>
								{/if}
							{:else}
								<div>{$i18n.t('No Log')}</div>
							{/if}
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
