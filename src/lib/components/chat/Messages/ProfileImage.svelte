<script lang="ts">
	import { WEBUI_BASE_URL } from '$lib/constants';

	export let className = 'size-8';
	export let src = `${WEBUI_BASE_URL}/static/favicon.png`;
</script>

<img
	src={src ?? `${WEBUI_BASE_URL}/static/favicon.png`}
	class=" {className} object-cover rounded-full"
	alt="profile"
	draggable="false"
/>
