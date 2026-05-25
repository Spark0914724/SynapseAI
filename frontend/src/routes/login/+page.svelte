<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { Zap } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { authApi } from '$lib/api';
	import { authStore } from '$lib/stores';
	import { loginSchema } from '$lib/utils/validation';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let errors = $state<Record<string, string>>({});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		errors = {};

		const result = loginSchema.safeParse({ email, password });
		if (!result.success) {
			result.error.issues.forEach((issue) => {
				if (issue.path.length > 0) errors[String(issue.path[0])] = issue.message;
			});
			return;
		}

		loading = true;
		try {
			const { data } = await authApi.login({ email, password });
			authStore.setAuth(data.user, data.access_token);
			toast.success('Welcome back!');
			goto('/app');
		} catch (err: any) {
			toast.error(err.response?.data?.detail ?? 'Login failed');
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>Login — SynapseAI</title></svelte:head>

<div class="flex min-h-screen items-center justify-center px-4" style="background-color: var(--color-background)">
	<div class="w-full max-w-sm space-y-8">
		<!-- Logo -->
		<div class="flex flex-col items-center gap-3">
			<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
				<Zap class="h-6 w-6 text-white" />
			</div>
			<div class="text-center">
				<h1 class="text-2xl font-bold" style="color: var(--color-foreground)">Welcome back</h1>
				<p class="text-sm mt-1" style="color: var(--color-muted-foreground)">
					Sign in to your SynapseAI account
				</p>
			</div>
		</div>

		<!-- Form -->
		<form onsubmit={handleSubmit} class="space-y-4">
			<Input
				id="email"
				type="email"
				label="Email"
				placeholder="you@example.com"
				bind:value={email}
				error={errors.email}
				required
			/>
			<Input
				id="password"
				type="password"
				label="Password"
				placeholder="••••••••"
				bind:value={password}
				error={errors.password}
				required
			/>

			<div class="flex justify-end">
				<a href="/forgot-password" class="text-xs text-violet-600 hover:underline">
					Forgot password?
				</a>
			</div>

			<Button type="submit" {loading} class="w-full">Sign in</Button>
		</form>

		<p class="text-center text-sm" style="color: var(--color-muted-foreground)">
			Don't have an account?
			<a href="/register" class="text-violet-600 hover:underline font-medium">Sign up</a>
		</p>
	</div>
</div>
