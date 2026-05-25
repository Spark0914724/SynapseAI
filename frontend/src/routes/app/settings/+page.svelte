<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { Sun, Moon, User, Bell, Shield, CreditCard, Check, ExternalLink } from '@lucide/svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import { themeStore, authStore } from '$lib/stores';
	import { billingApi, type Subscription, type PlanInfo } from '$lib/api/billing';
	import { formatTokens } from '$lib/utils/format';
	import { toast } from 'svelte-sonner';

	let full_name = $state($authStore.user?.full_name ?? '');
	let email = $state($authStore.user?.email ?? '');

	// Billing state
	let subscription = $state<Subscription | null>(null);
	let plans = $state<PlanInfo[]>([]);
	let billingLoading = $state(false);
	let checkoutLoading = $state<string | null>(null);
	let portalLoading = $state(false);

	const sections = [
		{ id: 'profile', label: 'Profile', icon: User },
		{ id: 'appearance', label: 'Appearance', icon: Sun },
		{ id: 'notifications', label: 'Notifications', icon: Bell },
		{ id: 'billing', label: 'Billing', icon: CreditCard },
		{ id: 'security', label: 'Security', icon: Shield },
	];

	// Read tab from URL query param
	let activeSection = $state($page.url.searchParams.get('tab') ?? 'profile');

	onMount(async () => {
		// Show success/cancel toast from Stripe redirect
		const success = $page.url.searchParams.get('success');
		const canceled = $page.url.searchParams.get('canceled');
		if (success) toast.success('Subscription activated! Welcome to the new plan.');
		if (canceled) toast.info('Checkout canceled. No charges were made.');

		// Load billing data
		billingLoading = true;
		try {
			const [subRes, plansRes] = await Promise.all([
				billingApi.getSubscription(),
				billingApi.getPlans(),
			]);
			subscription = subRes.data;
			plans = plansRes.data;
		} catch {
			// Not critical — user may not be logged in yet
		} finally {
			billingLoading = false;
		}
	});

	async function handleUpgrade(plan: PlanInfo) {
		if (plan.plan === 'free') return;
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

	async function openPortal() {
		portalLoading = true;
		try {
			const { data } = await billingApi.getBillingPortal();
			window.location.href = data.portal_url;
		} catch (err: any) {
			toast.error(err.response?.data?.detail ?? 'Failed to open billing portal');
		} finally {
			portalLoading = false;
		}
	}

	const planBadgeVariant = (plan: string) =>
		plan === 'pro' ? 'default' : plan === 'team' ? 'success' : 'secondary';

	const usagePercent = $derived(
		subscription ? Math.min(100, Math.round((subscription.tokens_used / subscription.tokens_limit) * 100)) : 0
	);
</script>

<svelte:head><title>Settings — SynapseAI</title></svelte:head>

<div class="flex gap-6">
	<!-- Settings nav -->
	<div class="w-48 shrink-0">
		<nav class="space-y-1">
			{#each sections as section}
				{@const Icon = section.icon}
				<button
					onclick={() => (activeSection = section.id)}
					class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors
						{activeSection === section.id
							? 'bg-violet-50 text-violet-700 font-medium dark:bg-violet-950 dark:text-violet-300'
							: 'hover:bg-[var(--color-accent)]'}"
					style={activeSection !== section.id ? 'color: var(--color-muted-foreground)' : ''}
				>
					<Icon class="h-4 w-4" />
					{section.label}
				</button>
			{/each}
		</nav>
	</div>

	<!-- Settings content -->
	<div class="flex-1 max-w-2xl space-y-4">

		<!-- ── Profile ── -->
		{#if activeSection === 'profile'}
			<Card class="p-6 space-y-5">
				<h3 class="font-semibold text-lg" style="color: var(--color-foreground)">Profile</h3>
				<Input id="full_name" label="Full name" bind:value={full_name} />
				<Input id="email" type="email" label="Email" bind:value={email} disabled />
				<Button onclick={() => toast.success('Profile updated')}>Save changes</Button>
			</Card>

		<!-- ── Appearance ── -->
		{:else if activeSection === 'appearance'}
			<Card class="p-6 space-y-5">
				<h3 class="font-semibold text-lg" style="color: var(--color-foreground)">Appearance</h3>
				<div class="grid grid-cols-2 gap-3">
					<button
						onclick={() => themeStore.set('light')}
						class="flex flex-col items-center gap-3 rounded-xl border-2 p-4 transition-colors"
						style="border-color: {$themeStore === 'light' ? '#7c3aed' : 'var(--color-border)'}; background-color: {$themeStore === 'light' ? '#f5f3ff' : 'transparent'}; color: var(--color-foreground)"
					>
						<Sun class="h-6 w-6" />
						<span class="text-sm font-medium">Light</span>
					</button>
					<button
						onclick={() => themeStore.set('dark')}
						class="flex flex-col items-center gap-3 rounded-xl border-2 p-4 transition-colors"
						style="border-color: {$themeStore === 'dark' ? '#7c3aed' : 'var(--color-border)'}; background-color: {$themeStore === 'dark' ? '#2e1065' : 'transparent'}; color: var(--color-foreground)"
					>
						<Moon class="h-6 w-6" />
						<span class="text-sm font-medium">Dark</span>
					</button>
				</div>
			</Card>

		<!-- ── Billing ── -->
		{:else if activeSection === 'billing'}
			{#if billingLoading}
				<Card class="p-6">
					<div class="space-y-3">
						{#each Array(3) as _}
							<div class="h-5 rounded animate-pulse" style="background-color: var(--color-secondary)"></div>
						{/each}
					</div>
				</Card>
			{:else if subscription}
				<!-- Current plan card -->
				<Card class="p-6 space-y-5">
					<div class="flex items-center justify-between">
						<h3 class="font-semibold text-lg" style="color: var(--color-foreground)">Current Plan</h3>
						<Badge variant={planBadgeVariant(subscription.plan)}>
							{subscription.plan.charAt(0).toUpperCase() + subscription.plan.slice(1)}
						</Badge>
					</div>

					<!-- Token usage bar -->
					<div class="space-y-2">
						<div class="flex justify-between text-sm">
							<span style="color: var(--color-foreground)">Token usage this month</span>
							<span style="color: var(--color-muted-foreground)">
								{formatTokens(subscription.tokens_used)} / {formatTokens(subscription.tokens_limit)}
							</span>
						</div>
						<div class="h-2.5 w-full rounded-full overflow-hidden" style="background-color: var(--color-secondary)">
							<div
								class="h-full rounded-full transition-all {usagePercent >= 90 ? 'bg-red-500' : usagePercent >= 70 ? 'bg-yellow-500' : 'bg-violet-600'}"
								style="width: {usagePercent}%"
							></div>
						</div>
						<p class="text-xs" style="color: var(--color-muted-foreground)">
							{subscription.tokens_remaining.toLocaleString()} tokens remaining · resets monthly
						</p>
					</div>

					{#if subscription.stripe_subscription_id}
						<Button variant="outline" loading={portalLoading} onclick={openPortal}>
							<ExternalLink class="h-4 w-4" />
							Manage billing & invoices
						</Button>
					{/if}
				</Card>

				<!-- Upgrade plans -->
				{#if subscription.plan === 'free'}
					<div class="space-y-3">
						<h3 class="font-semibold" style="color: var(--color-foreground)">Upgrade your plan</h3>
						{#each plans.filter(p => p.plan !== 'free') as plan}
							<Card class="p-5">
								<div class="flex items-start justify-between gap-4">
									<div class="flex-1">
										<div class="flex items-center gap-2 mb-1">
											<p class="font-semibold" style="color: var(--color-foreground)">{plan.name}</p>
											<span class="text-sm font-bold text-violet-600">${plan.price_monthly}/mo</span>
										</div>
										<ul class="space-y-1 mt-2">
											{#each plan.features.slice(0, 4) as feature}
												<li class="flex items-center gap-2 text-sm" style="color: var(--color-muted-foreground)">
													<Check class="h-3.5 w-3.5 text-violet-600 shrink-0" />
													{feature}
												</li>
											{/each}
										</ul>
									</div>
									<Button
										loading={checkoutLoading === plan.plan}
										onclick={() => handleUpgrade(plan)}
										class="shrink-0"
									>
										Upgrade
									</Button>
								</div>
							</Card>
						{/each}
					</div>
				{/if}
			{/if}

		<!-- ── Security ── -->
		{:else if activeSection === 'security'}
			<Card class="p-6 space-y-5">
				<h3 class="font-semibold text-lg" style="color: var(--color-foreground)">Security</h3>
				<div class="space-y-4">
					<div>
						<p class="text-sm font-medium mb-1" style="color: var(--color-foreground)">Change password</p>
						<p class="text-sm mb-3" style="color: var(--color-muted-foreground)">
							Use the forgot password flow to set a new password.
						</p>
						<Button variant="outline" onclick={() => window.location.href = '/forgot-password'}>
							Send reset email
						</Button>
					</div>
				</div>
			</Card>

		<!-- ── Other ── -->
		{:else}
			<Card class="p-6">
				<h3 class="font-semibold text-lg capitalize" style="color: var(--color-foreground)">{activeSection}</h3>
				<p class="text-sm mt-2" style="color: var(--color-muted-foreground)">Coming in a future step.</p>
			</Card>
		{/if}
	</div>
</div>
