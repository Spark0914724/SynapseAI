<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Check, Zap } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import { billingApi, type PlanInfo } from '$lib/api/billing';
	import { authStore } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import { formatTokens } from '$lib/utils/format';

	let plans = $state<PlanInfo[]>([]);
	let loading = $state(true);
	let checkoutLoading = $state<string | null>(null);

	onMount(async () => {
		try {
			const { data } = await billingApi.getPlans();
			plans = data;
		} catch {
			toast.error('Failed to load plans');
		} finally {
			loading = false;
		}
	});

	async function handleUpgrade(plan: PlanInfo) {
		if (plan.plan === 'free') return;
		if (!$authStore.isAuthenticated) {
			goto('/register');
			return;
		}
		checkoutLoading = plan.plan;
		try {
			const { data } = await billingApi.createCheckout(plan.plan);
			window.location.href = data.checkout_url;
		} catch (err: any) {
			toast.error(err.response?.data?.detail ?? 'Failed to start checkout');
		} finally {
			checkoutLoading = null;
		}
	}

	const highlighted = 'pro';
</script>

<svelte:head><title>Pricing — SynapseAI</title></svelte:head>

<div class="min-h-screen py-20 px-4" style="background-color: var(--color-background)">
	<div class="max-w-5xl mx-auto">
		<!-- Header -->
		<div class="text-center mb-14 space-y-4">
			<div class="flex justify-center">
				<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
					<Zap class="h-6 w-6 text-white" />
				</div>
			</div>
			<h1 class="text-4xl font-bold" style="color: var(--color-foreground)">Simple, transparent pricing</h1>
			<p class="text-lg max-w-xl mx-auto" style="color: var(--color-muted-foreground)">
				Start free. Upgrade when you need more power.
			</p>
		</div>

		<!-- Plans grid -->
		{#if loading}
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
				{#each Array(3) as _}
					<div class="h-96 rounded-2xl animate-pulse" style="background-color: var(--color-secondary)"></div>
				{/each}
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
				{#each plans as plan}
					{@const isHighlighted = plan.plan === highlighted}
					<div
						class="relative rounded-2xl p-7 flex flex-col gap-6 transition-shadow"
						style="
							background-color: {isHighlighted ? '#7c3aed' : 'var(--color-card)'};
							border: 2px solid {isHighlighted ? '#7c3aed' : 'var(--color-border)'};
							color: {isHighlighted ? '#fff' : 'var(--color-foreground)'};
							box-shadow: {isHighlighted ? '0 20px 60px rgba(124,58,237,0.3)' : 'none'};
						"
					>
						{#if isHighlighted}
							<div class="absolute -top-3.5 left-1/2 -translate-x-1/2">
								<span class="rounded-full bg-white text-violet-700 px-3 py-1 text-xs font-bold shadow">
									Most Popular
								</span>
							</div>
						{/if}

						<!-- Plan name & price -->
						<div>
							<p class="text-sm font-semibold uppercase tracking-wider opacity-75">{plan.name}</p>
							<div class="flex items-end gap-1 mt-2">
								<span class="text-4xl font-bold">${plan.price_monthly}</span>
								{#if plan.price_monthly > 0}
									<span class="text-sm opacity-70 mb-1">/month</span>
								{/if}
							</div>
							<p class="text-sm mt-1 opacity-75">
								{formatTokens(plan.tokens_per_month)} tokens / month
							</p>
						</div>

						<!-- CTA -->
						<Button
							variant={isHighlighted ? 'secondary' : 'default'}
							class="w-full {isHighlighted ? 'bg-white text-violet-700 hover:bg-violet-50' : ''}"
							loading={checkoutLoading === plan.plan}
							onclick={() => handleUpgrade(plan)}
						>
							{plan.plan === 'free' ? 'Get started free' : `Upgrade to ${plan.name}`}
						</Button>

						<!-- Features -->
						<ul class="space-y-3">
							{#each plan.features as feature}
								<li class="flex items-start gap-2.5 text-sm">
									<Check class="h-4 w-4 shrink-0 mt-0.5 {isHighlighted ? 'text-white' : 'text-violet-600'}" />
									<span class="opacity-90">{feature}</span>
								</li>
							{/each}
						</ul>
					</div>
				{/each}
			</div>
		{/if}

		<!-- Footer note -->
		<p class="text-center text-sm mt-10" style="color: var(--color-muted-foreground)">
			All plans include a 14-day free trial. No credit card required for Free plan.
			<a href="/login" class="text-violet-600 hover:underline ml-1">Sign in</a>
		</p>
	</div>
</div>
