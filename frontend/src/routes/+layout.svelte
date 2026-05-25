<script lang="ts">
	import '../app.css';
	import { Toaster } from 'svelte-sonner';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { authStore } from '$lib/stores/auth';
	import { authApi } from '$lib/api';

	let { children } = $props();

	onMount(async () => {
		const token = browser ? localStorage.getItem('access_token') : null;
		if (token) {
			try {
				const { data } = await authApi.me();
				authStore.setUser(data);
			} catch {
				authStore.logout();
			}
		} else {
			authStore.setLoading(false);
		}
	});
</script>

{@render children()}
<Toaster richColors position="top-right" />
