<script lang="ts">
	import { v4 as uuidv4 } from 'uuid';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { WEBUI_NAME, showSidebar, user, mobile, config, models, settings } from '$lib/stores';
	import { WEBUI_BASE_URL } from '$lib/constants';

	import { onMount, tick, getContext } from 'svelte';
	import { createNewModel, getModelById } from '$lib/apis/models';
	import { getModels } from '$lib/apis';

	import ModelEditor from '$lib/components/workspace/Models/ModelEditor.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';

	const i18n = getContext('i18n');

	let loaded = false;

	const onSubmit = async (modelInfo) => {
		if ($models.find((m) => m.id === modelInfo.id)) {
			toast.error(
				`Error: A model with the ID '${modelInfo.id}' already exists. Please select a different ID to proceed.`
			);
			return;
		}

		if (modelInfo.id === '') {
			toast.error('Error: Model ID cannot be empty. Please enter a valid ID to proceed.');
			return;
		}

		if (modelInfo) {
			const res = await createNewModel(localStorage.token, {
				...modelInfo,
				meta: {
					...modelInfo.meta,
					profile_image_url:
						modelInfo.meta.profile_image_url ?? `${WEBUI_BASE_URL}/static/favicon.png`,
					suggestion_prompts: modelInfo.meta.suggestion_prompts
						? modelInfo.meta.suggestion_prompts.filter((prompt) => prompt.content !== '')
						: null
				},
				params: { ...modelInfo.params }
			}).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (res) {
				await models.set(
					await getModels(
						localStorage.token,
						$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
					)
				);
				toast.success($i18n.t('Model created successfully!'));
				await goto('/models');
			}
		}
	};

	let model = null;

	onMount(async () => {
		// 权限检查
		if ($user?.role !== 'admin' && !$user?.permissions?.workspace?.models) {
			goto('/');
			return;
		}

		window.addEventListener('message', async (event) => {
			if (
				!['https://openwebui.com', 'https://www.openwebui.com', 'http://localhost:5173'].includes(
					event.origin
				)
			) {
				return;
			}

			let data = JSON.parse(event.data);

			if (data?.info) {
				data = data.info;
			}

			model = data;
		});

		if (window.opener ?? false) {
			window.opener.postMessage('loaded', '*');
		}

		if (sessionStorage.model) {
			model = JSON.parse(sessionStorage.model);
			sessionStorage.removeItem('model');
		}

		loaded = true;
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Create Model')} • {$WEBUI_NAME}
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
							href="/models"
						>
							{$i18n.t('Models')}
						</a>
						<div class="min-w-fit p-1.5 text-gray-900 dark:text-white font-medium">
							{$i18n.t('Create')}
						</div>
					</div>
				</div>
			</div>
		</nav>

		<div class="  pb-1 px-[18px] flex-1 max-h-full overflow-y-auto" id="models-create-container">
			{#key model}
				<ModelEditor {model} {onSubmit} />
			{/key}
		</div>
	</div>
{/if}
