<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import Topbar from '$lib/components/layout/Topbar.svelte';
	import { authStore, workspaceStore } from '$lib/stores';
	import { workspacesApi } from '$lib/api';

	let { children } = $props();

	onMount(async () => {
		if (!$authStore.isAuthenticated && !$authStore.isLoading) {
			goto('/login');
			return;
		}
		try {
			const { data } = await workspacesApi.list();
			workspaceStore.setWorkspaces(data);
		} catch {}
	});

	$effect(() => {
		if (!$authStore.isLoading && !$authStore.isAuthenticated) {
			goto('/login');
		}
	});
</script>

{#if $authStore.isLoading}
	<div class="flex h-screen items-center justify-center" style="background-color: var(--color-background)">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-violet-600 border-t-transparent"></div>
	</div>
{:else if $authStore.isAuthenticated}
	<div class="flex h-screen overflow-hidden" style="background-color: var(--color-background)">
		<Sidebar />
		<div class="flex flex-1 flex-col overflow-hidden">
			<Topbar />
			<main class="flex-1 overflow-y-auto p-6">
				{@render children()}
			</main>
		</div>
	</div>
{/if}
