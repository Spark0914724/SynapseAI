<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { Zap, ArrowLeft } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { authApi } from '$lib/api';

	let email = $state('');
	let loading = $state(false);
	let sent = $state(false);

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!email.trim()) return;
		loading = true;
		try {
			await authApi.forgotPassword(email);
			sent = true;
		} catch {
			toast.error('Something went wrong. Please try again.');
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>Forgot Password — SynapseAI</title></svelte:head>

<div class="flex min-h-screen items-center justify-center px-4" style="background-color: var(--color-background)">
	<div class="w-full max-w-sm space-y-8">
		<div class="flex flex-col items-center gap-3">
			<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
				<Zap class="h-6 w-6 text-white" />
			</div>
			<div class="text-center">
				<h1 class="text-2xl font-bold" style="color: var(--color-foreground)">Forgot password?</h1>
				<p class="text-sm mt-1" style="color: var(--color-muted-foreground)">
					Enter your email and we'll send a reset link
				</p>
			</div>
		</div>

		{#if sent}
			<div class="rounded-xl p-5 text-center space-y-2" style="background-color: var(--color-secondary)">
				<p class="font-medium" style="color: var(--color-foreground)">Check your inbox</p>
				<p class="text-sm" style="color: var(--color-muted-foreground)">
					If <strong>{email}</strong> has an account, a reset link is on its way.
				</p>
			</div>
		{:else}
			<form onsubmit={handleSubmit} class="space-y-4">
				<Input
					id="email"
					type="email"
					label="Email"
					placeholder="you@example.com"
					bind:value={email}
					required
				/>
				<Button type="submit" {loading} class="w-full">Send reset link</Button>
			</form>
		{/if}

		<div class="text-center">
			<a href="/login" class="inline-flex items-center gap-1.5 text-sm text-violet-600 hover:underline">
				<ArrowLeft class="h-3.5 w-3.5" />
				Back to login
			</a>
		</div>
	</div>
</div>
