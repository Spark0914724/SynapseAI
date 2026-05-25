<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { Zap } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { authApi } from '$lib/api';
	import { authStore } from '$lib/stores';
	import { registerSchema } from '$lib/utils/validation';

	let full_name = $state('');
	let email = $state('');
	let password = $state('');
	let confirm_password = $state('');
	let loading = $state(false);
	let errors = $state<Record<string, string>>({});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		errors = {};

		const result = registerSchema.safeParse({ full_name, email, password, confirm_password });
		if (!result.success) {
			result.error.issues.forEach((issue) => {
				if (issue.path.length > 0) errors[String(issue.path[0])] = issue.message;
			});
			return;
		}

		loading = true;
		try {
			const { data } = await authApi.register({ full_name, email, password });
			authStore.setAuth(data.user, data.access_token);
			toast.success('Account created! Check your email to verify.');
			goto('/app');
		} catch (err: any) {
			toast.error(err.response?.data?.detail ?? 'Registration failed');
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>Sign Up — SynapseAI</title></svelte:head>

<div class="flex min-h-screen items-center justify-center px-4" style="background-color: var(--color-background)">
	<div class="w-full max-w-sm space-y-8">
		<div class="flex flex-col items-center gap-3">
			<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
				<Zap class="h-6 w-6 text-white" />
			</div>
			<div class="text-center">
				<h1 class="text-2xl font-bold" style="color: var(--color-foreground)">Create your account</h1>
				<p class="text-sm mt-1" style="color: var(--color-muted-foreground)">
					Start your AI workspace today
				</p>
			</div>
		</div>

		<form onsubmit={handleSubmit} class="space-y-4">
			<Input id="full_name" label="Full name" placeholder="Jane Smith" bind:value={full_name} error={errors.full_name} />
			<Input id="email" type="email" label="Email" placeholder="you@example.com" bind:value={email} error={errors.email} required />
			<Input id="password" type="password" label="Password" placeholder="••••••••" bind:value={password} error={errors.password} required />
			<Input id="confirm_password" type="password" label="Confirm password" placeholder="••••••••" bind:value={confirm_password} error={errors.confirm_password} required />

			<Button type="submit" {loading} class="w-full">Create account</Button>
		</form>

		<p class="text-center text-sm" style="color: var(--color-muted-foreground)">
			Already have an account?
			<a href="/login" class="text-violet-600 hover:underline font-medium">Sign in</a>
		</p>
	</div>
</div>
