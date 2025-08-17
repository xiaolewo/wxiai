<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, showSidebar, user, mobile } from '$lib/stores';
	import { goto } from '$app/navigation';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';

	import CreateKnowledgeBase from '$lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte';

	const i18n = getContext('i18n');

	let loaded = false;

	onMount(async () => {
		// 权限检查
		if ($user?.role !== 'admin' && !$user?.permissions?.workspace?.knowledge) {
			goto('/');
			return;
		}

		loaded = true;
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Create Knowledge Base')} • {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<div
		class=" relative flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
			? 'md:max-w-[calc(100%-260px)]'
			: ''} max-w-full"
	>
		<nav class="   px-2.5 pt-1.5 backdrop-blur-xl drag-region">
			<div class=" flex items-center gap-1">
				{#if $mobile}
					<div class="{$showSidebar ? 'md:hidden' : ''} self-center flex flex-none items-center">
						<Tooltip
							content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
							interactive={true}
						>
							<button
								id="sidebar-toggle-button"
								class=" cursor-pointer flex rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition cursor-"
								on:click={() => {
									showSidebar.set(!$showSidebar);
								}}
							>
								<div class=" self-center p-1.5">
									<Sidebar />
								</div>
							</button>
						</Tooltip>
					</div>
				{/if}

				<div class="">
					<div
						class="flex gap-1 scrollbar-none overflow-x-auto w-fit text-center text-sm font-medium rounded-full bg-transparent py-1 touch-auto pointer-events-auto"
					>
						<a
							class="min-w-fit p-1.5 text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white transition"
							href="/knowledge"
						>
							{$i18n.t('Knowledge Base')}
						</a>
						<div class="min-w-fit p-1.5 text-gray-900 dark:text-white font-medium">
							{$i18n.t('Create')}
						</div>
					</div>
				</div>
			</div>
		</nav>

		<div class="  pb-1 px-[18px] flex-1 max-h-full overflow-y-auto" id="knowledge-create-container">
			<CreateKnowledgeBase />
		</div>
	</div>
{/if}
