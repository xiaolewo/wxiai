<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { MediaFolder } from '$lib/apis/media-library';

	export let getChildren: (parentId: string | null) => MediaFolder[];
	export let parentId: string | null = null;
	export let selectedId: string | null = null;

	const dispatch = createEventDispatcher();
	let children: MediaFolder[] = [];
	$: children = getChildren(parentId);

	function handleSelect(id: string) {
		dispatch('select', id);
	}

	function handleCreate(id: string | null) {
		dispatch('create', id);
	}

	function handleRename(folder: MediaFolder) {
		dispatch('rename', folder);
	}

	function handleDrop(event: DragEvent, targetId: string | null) {
		event.preventDefault();
		dispatch('drop', targetId);
	}

	function handleDragStart(event: DragEvent, folder: MediaFolder) {
		event.dataTransfer?.setData('text/plain', folder.id);
		dispatch('dragStart', folder.id);
	}
</script>

{#each children as folder}
	<div class="mt-1 first:mt-0">
		<div
			class={`group relative flex cursor-pointer items-center justify-between rounded-md px-3 py-1.5 text-xs transition ${selectedId === folder.id ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800/60'}`}
			draggable={true}
			on:click={() => handleSelect(folder.id)}
			on:dragstart={(event) => handleDragStart(event, folder)}
			on:dragover={(event) => event.preventDefault()}
			on:drop={(event) => handleDrop(event, folder.id)}
		>
			<span class="truncate">{folder.name}</span>
			<span
				class="pointer-events-none absolute right-2 top-1 hidden gap-1 text-[10px] text-gray-400 group-hover:flex group-hover:pointer-events-auto dark:text-gray-500"
			>
				<button
					class="pointer-events-auto hover:text-gray-700 dark:hover:text-gray-300"
					on:click|stopPropagation={() => handleRename(folder)}>✎</button
				>
				<button
					class="pointer-events-auto hover:text-gray-700 dark:hover:text-gray-300"
					on:click|stopPropagation={() => handleCreate(folder.id)}>+</button
				>
			</span>
		</div>
		<div class="pl-3">
			<svelte:self
				{getChildren}
				parentId={folder.id}
				{selectedId}
				on:select
				on:create
				on:rename
				on:drop
				on:dragStart
			/>
		</div>
	</div>
{/each}
