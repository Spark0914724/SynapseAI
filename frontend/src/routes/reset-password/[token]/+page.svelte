<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { Zap } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { authApi } from '$lib/api';
	import { z } from 'zod';

	const token = $derived($page.params.token ?? '');

	let password = $state('');
	let confirm_password = $state('');
	let loading = $state(false);
	let errors = $state<Record<string, string>>({});

	const schema = z.object({
		password: z.string().min(8, 'Password must be at least 8 characters'),
		confirm_password: z.string(),
	}).refine((d) => d.password === d.confirm_password, {
		message: 'Passwords do not match',
		path: ['confirm_password'],
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		errors = {};

		const result = schema.safeParse({ password, confirm_password });
		if (!result.success) {
			result.error.issues.forEach((issue) => {
				if (issue.path.length > 0) errors[String(issue.path[0])] = issue.message;
			});
			return;
		}

		loading = true;
		try {
			await authApi.resetPassword(token, password);
			toast.success('Password reset! Please sign in.');
			goto('/login');
		} catch (err: any) {
			toast.error(err.response?.data?.detail ?? 'Reset failed. The link may have expired.');
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>Reset Password — SynapseAI</title></svelte:head>

<div class="flex min-h-screen items-center justify-center px-4" style="background-color: var(--color-background)">
	<div class="w-full max-w-sm space-y-8">
		<div class="flex flex-col items-center gap-3">
			<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
				<Zap class="h-6 w-6 text-white" />
			</div>
			<div class="text-center">
				<h1 class="text-2xl font-bold" style="color: var(--color-foreground)">Set new password</h1>
				<p class="text-sm mt-1" style="color: var(--color-muted-foreground)">
					Choose a strong password for your account
				</p>
			</div>
		</div>

		<form onsubmit={handleSubmit} class="space-y-4">
			<Input
				id="password"
				type="password"
				label="New password"
				placeholder="••••••••"
				bind:value={password}
				error={errors.password}
				required
			/>
			<Input
				id="confirm_password"
				type="password"
				label="Confirm password"
				placeholder="••••••••"
				bind:value={confirm_password}
				error={errors.confirm_password}
				required
			/>
			<Button type="submit" {loading} class="w-full">Reset password</Button>
		</form>
	</div>
</div>
