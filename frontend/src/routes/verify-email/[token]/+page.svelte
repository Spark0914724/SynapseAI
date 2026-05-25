<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Zap, CheckCircle, XCircle } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import { authApi } from '$lib/api';

	const token = $derived($page.params.token ?? '');

	let status = $state<'loading' | 'success' | 'error'>('loading');
	let message = $state('');

	onMount(async () => {
		try {
			await authApi.verifyEmail(token);
			status = 'success';
			message = 'Your email has been verified successfully!';
			// Redirect to app after 2 seconds
			setTimeout(() => goto('/app'), 2000);
		} catch (err: any) {
			status = 'error';
			message = err.response?.data?.detail ?? 'This verification link is invalid or has expired.';
		}
	});
</script>

<svelte:head><title>Verify Email — SynapseAI</title></svelte:head>

<div class="flex min-h-screen items-center justify-center px-4" style="background-color: var(--color-background)">
	<div class="w-full max-w-sm space-y-6 text-center">
		<div class="flex justify-center">
			<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
				<Zap class="h-6 w-6 text-white" />
			</div>
		</div>

		{#if status === 'loading'}
			<div class="space-y-3">
				<div class="h-8 w-8 animate-spin rounded-full border-4 border-violet-600 border-t-transparent mx-auto"></div>
				<p style="color: var(--color-muted-foreground)">Verifying your email...</p>
			</div>

		{:else if status === 'success'}
			<div class="space-y-3">
				<CheckCircle class="h-12 w-12 text-green-500 mx-auto" />
				<h2 class="text-xl font-bold" style="color: var(--color-foreground)">Email verified!</h2>
				<p style="color: var(--color-muted-foreground)">{message}</p>
				<p class="text-sm" style="color: var(--color-muted-foreground)">Redirecting to your workspace...</p>
			</div>

		{:else}
			<div class="space-y-4">
				<XCircle class="h-12 w-12 text-red-500 mx-auto" />
				<h2 class="text-xl font-bold" style="color: var(--color-foreground)">Verification failed</h2>
				<p style="color: var(--color-muted-foreground)">{message}</p>
				<Button onclick={() => goto('/login')} class="w-full">Back to login</Button>
			</div>
		{/if}
	</div>
</div>
