<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth';

	onMount(() => {
		if ($authStore.isAuthenticated) {
			goto('/app');
		} else {
			goto('/login');
		}
	});
</script>

<div class="flex h-screen items-center justify-center">
	<div class="h-8 w-8 animate-spin rounded-full border-4 border-violet-600 border-t-transparent"></div>
</div>
