<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let src: string | null | undefined;
	export let poster: string | null | undefined = undefined;
	export let autoplay = true;
	export let muted = true;
	export let loop = true;
	export let playsinline = true;
	export let preload: 'auto' | 'metadata' | 'none' = 'metadata';
	export let controls = false;
	export let className = '';

	const dispatch = createEventDispatcher<{ error: Event }>();

	let hasError = false;

	function handleError(event: Event) {
		hasError = true;
		dispatch('error', event);
	}

	function handleLoaded() {
		hasError = false;
	}
</script>

<div class={`relative overflow-hidden ${className}`.trim()}>
	{#if src && !hasError}
		<video
			{src}
			poster={poster ?? undefined}
			{autoplay}
			{muted}
			{loop}
			{playsinline}
			{preload}
			{controls}
			class="object-cover w-full h-full"
			onerror={handleError}
			onloadeddata={handleLoaded}
		/>
	{:else}
		<slot name="fallback">
			<div class="flex h-full w-full flex-col items-center justify-center gap-2 text-gray-400">
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
				<span class="text-xs uppercase tracking-wide">Video</span>
			</div>
		</slot>
	{/if}
</div>
