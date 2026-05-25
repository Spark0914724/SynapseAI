<script lang="ts">
	import { MessageSquare, FileText, Mic, Zap, TrendingUp, Clock } from '@lucide/svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import { authStore } from '$lib/stores';
	import { formatTokens } from '$lib/utils/format';

	// Placeholder stats — wired to real API in Step 11
	const stats = [
		{ label: 'AI Chats', value: '24', icon: MessageSquare, change: '+12%' },
		{ label: 'Documents', value: '8', icon: FileText, change: '+3' },
		{ label: 'Transcriptions', value: '5', icon: Mic, change: '+2' },
		{ label: 'Tokens Used', value: formatTokens(12_400), icon: Zap, change: '24.8%' },
	];

	const recentActivity = [
		{ label: 'Chat: Project planning session', time: '2m ago', type: 'chat' },
		{ label: 'Uploaded: Q2 Report.pdf', time: '1h ago', type: 'document' },
		{ label: 'Transcribed: Team standup', time: '3h ago', type: 'transcription' },
		{ label: 'Generated: Sprint meeting notes', time: '5h ago', type: 'tool' },
	];
</script>

<svelte:head><title>Dashboard — SynapseAI</title></svelte:head>

<div class="space-y-6">
	<!-- Greeting -->
	<div>
		<h2 class="text-2xl font-bold text-foreground">
			Good morning, {$authStore.user?.full_name?.split(' ')[0] ?? 'there'} 👋
		</h2>
		<p class="text-muted-foreground mt-1">Here's what's happening in your workspace.</p>
	</div>

	<!-- Stats grid -->
	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#each stats as stat}
			{@const Icon = stat.icon}
			<Card class="p-5">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm text-muted-foreground">{stat.label}</p>
						<p class="text-2xl font-bold text-foreground mt-1">{stat.value}</p>
					</div>
					<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-50 dark:bg-violet-950">
						<Icon class="h-5 w-5 text-violet-600" />
					</div>
				</div>
				<p class="text-xs text-muted-foreground mt-3">
					<span class="text-green-600 font-medium">{stat.change}</span> this month
				</p>
			</Card>
		{/each}
	</div>

	<!-- Token usage bar -->
	<Card class="p-5">
		<div class="flex items-center justify-between mb-3">
			<div>
				<p class="font-medium text-foreground">Token Usage</p>
				<p class="text-sm text-muted-foreground">Free plan · resets monthly</p>
			</div>
			<Badge variant="default">Free</Badge>
		</div>
		<div class="h-2 w-full rounded-full bg-muted overflow-hidden">
			<div class="h-full rounded-full bg-violet-600 transition-all" style="width: 24.8%"></div>
		</div>
		<div class="flex justify-between mt-2 text-xs text-muted-foreground">
			<span>12,400 used</span>
			<span>50,000 limit</span>
		</div>
	</Card>

	<!-- Recent activity -->
	<Card class="p-5">
		<div class="flex items-center gap-2 mb-4">
			<Clock class="h-4 w-4 text-muted-foreground" />
			<h3 class="font-medium text-foreground">Recent Activity</h3>
		</div>
		<div class="space-y-3">
			{#each recentActivity as item}
				<div class="flex items-center justify-between py-2 border-b border-border last:border-0">
					<p class="text-sm text-foreground">{item.label}</p>
					<span class="text-xs text-muted-foreground shrink-0 ml-4">{item.time}</span>
				</div>
			{/each}
		</div>
	</Card>
</div>
