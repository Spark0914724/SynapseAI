<script lang="ts">
	import { onMount } from 'svelte';
	import { MessageSquare, FileText, Mic, Zap, Clock } from '@lucide/svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import { authStore } from '$lib/stores';
	import { billingApi, type Subscription } from '$lib/api/billing';
	import { formatTokens, timeAgo } from '$lib/utils/format';

	let subscription = $state<Subscription | null>(null);

	onMount(async () => {
		try {
			const { data } = await billingApi.getSubscription();
			subscription = data;
		} catch {}
	});

	const stats = $derived([
		{ label: 'AI Chats', value: '24', icon: MessageSquare, change: '+12%' },
		{ label: 'Documents', value: '8', icon: FileText, change: '+3' },
		{ label: 'Transcriptions', value: '5', icon: Mic, change: '+2' },
		{
			label: 'Tokens Used',
			value: subscription ? formatTokens(subscription.tokens_used) : '—',
			icon: Zap,
			change: subscription ? `${Math.round((subscription.tokens_used / subscription.tokens_limit) * 100)}%` : '—',
		},
	]);

	const usagePercent = $derived(
		subscription ? Math.min(100, Math.round((subscription.tokens_used / subscription.tokens_limit) * 100)) : 0
	);

	const recentActivity = [
		{ label: 'Chat: Project planning session', time: '2m ago' },
		{ label: 'Uploaded: Q2 Report.pdf', time: '1h ago' },
		{ label: 'Transcribed: Team standup', time: '3h ago' },
		{ label: 'Generated: Sprint meeting notes', time: '5h ago' },
	];
</script>

<svelte:head><title>Dashboard — SynapseAI</title></svelte:head>

<div class="space-y-6">
	<!-- Greeting -->
	<div>
		<h2 class="text-2xl font-bold" style="color: var(--color-foreground)">
			Good morning, {$authStore.user?.full_name?.split(' ')[0] ?? 'there'} 👋
		</h2>
		<p class="mt-1" style="color: var(--color-muted-foreground)">Here's what's happening in your workspace.</p>
	</div>

	<!-- Stats grid -->
	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#each stats as stat}
			{@const Icon = stat.icon}
			<Card class="p-5">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm" style="color: var(--color-muted-foreground)">{stat.label}</p>
						<p class="text-2xl font-bold mt-1" style="color: var(--color-foreground)">{stat.value}</p>
					</div>
					<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-50 dark:bg-violet-950">
						<Icon class="h-5 w-5 text-violet-600" />
					</div>
				</div>
				<p class="text-xs mt-3" style="color: var(--color-muted-foreground)">
					<span class="text-green-600 font-medium">{stat.change}</span> this month
				</p>
			</Card>
		{/each}
	</div>

	<!-- Token usage bar -->
	<Card class="p-5">
		<div class="flex items-center justify-between mb-3">
			<div>
				<p class="font-medium" style="color: var(--color-foreground)">Token Usage</p>
				<p class="text-sm" style="color: var(--color-muted-foreground)">
					{subscription?.plan ?? 'free'} plan · resets monthly
				</p>
			</div>
			<Badge variant={subscription?.plan === 'pro' ? 'default' : subscription?.plan === 'team' ? 'success' : 'secondary'}>
				{(subscription?.plan ?? 'free').charAt(0).toUpperCase() + (subscription?.plan ?? 'free').slice(1)}
			</Badge>
		</div>
		<div class="h-2 w-full rounded-full overflow-hidden" style="background-color: var(--color-secondary)">
			<div
				class="h-full rounded-full transition-all {usagePercent >= 90 ? 'bg-red-500' : usagePercent >= 70 ? 'bg-yellow-500' : 'bg-violet-600'}"
				style="width: {usagePercent}%"
			></div>
		</div>
		<div class="flex justify-between mt-2 text-xs" style="color: var(--color-muted-foreground)">
			<span>{subscription ? formatTokens(subscription.tokens_used) : '—'} used</span>
			<span>{subscription ? formatTokens(subscription.tokens_limit) : '—'} limit</span>
		</div>
	</Card>

	<!-- Recent activity -->
	<Card class="p-5">
		<div class="flex items-center gap-2 mb-4">
			<Clock class="h-4 w-4" style="color: var(--color-muted-foreground)" />
			<h3 class="font-medium" style="color: var(--color-foreground)">Recent Activity</h3>
		</div>
		<div class="space-y-3">
			{#each recentActivity as item}
				<div class="flex items-center justify-between py-2" style="border-bottom: 1px solid var(--color-border)">
					<p class="text-sm" style="color: var(--color-foreground)">{item.label}</p>
					<span class="text-xs shrink-0 ml-4" style="color: var(--color-muted-foreground)">{item.time}</span>
				</div>
			{/each}
		</div>
	</Card>
</div>
