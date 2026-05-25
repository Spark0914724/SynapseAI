<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Zap, CheckCircle, XCircle } from '@lucide/svelte';
	import { authApi } from '$lib/api';

	let status = $state<'loading' | 'success' | 'error'>('loading');

	onMount(async () => {
		const token = $page.url.searchParams.get('token');
		if (!token) { status = 'error'; return; }
		try {
			await authApi.verifyEmail(token);
			status = 'success';
			setTimeout(() => goto('/app'), 2500);
		} catch {
			status = 'error';
		}
	});
</script>

<svelte:head><title>Verify Email — SynapseAI</title></svelte:head>

<div class="flex min-h-screen items-center justify-center px-4" style="background-color: var(--color-background)">
	<div class="flex flex-col items-center gap-4 text-center max-w-sm">
		<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
			<Zap class="h-6 w-6 text-white" />
		</div>

		{#if status === 'loading'}
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-violet-600 border-t-transparent"></div>
			<p style="color: var(--color-muted-foreground)">Verifying your email...</p>

		{:else if status === 'success'}
			<CheckCircle class="h-12 w-12 text-green-500" />
			<h2 class="text-xl font-bold" style="color: var(--color-foreground)">Email verified!</h2>
			<p style="color: var(--color-muted-foreground)">Redirecting you to the app...</p>

		{:else}
			<XCircle class="h-12 w-12 text-red-500" />
			<h2 class="text-xl font-bold" style="color: var(--color-foreground)">Verification failed</h2>
			<p style="color: var(--color-muted-foreground)">This link is invalid or has expired.</p>
			<a href="/login" class="text-violet-600 hover:underline text-sm">Back to sign in</a>
		{/if}
	</div>
</div>
