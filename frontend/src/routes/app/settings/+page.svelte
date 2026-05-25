<script lang="ts">
	import { Sun, Moon, User, Bell, Shield, CreditCard } from '@lucide/svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { themeStore, authStore } from '$lib/stores';
	import { toast } from 'svelte-sonner';

	let full_name = $state($authStore.user?.full_name ?? '');
	let email = $state($authStore.user?.email ?? '');

	const sections = [
		{ id: 'profile', label: 'Profile', icon: User },
		{ id: 'appearance', label: 'Appearance', icon: Sun },
		{ id: 'notifications', label: 'Notifications', icon: Bell },
		{ id: 'billing', label: 'Billing', icon: CreditCard },
		{ id: 'security', label: 'Security', icon: Shield },
	];

	let activeSection = $state('profile');
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
	<div class="flex-1 max-w-2xl">
		{#if activeSection === 'profile'}
			<Card class="p-6 space-y-5">
				<h3 class="font-semibold text-lg" style="color: var(--color-foreground)">Profile</h3>
				<Input id="full_name" label="Full name" bind:value={full_name} />
				<Input id="email" type="email" label="Email" bind:value={email} disabled />
				<Button onclick={() => toast.success('Profile updated')}>Save changes</Button>
			</Card>

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

		{:else if activeSection === 'billing'}
			<Card class="p-6 space-y-5">
				<h3 class="font-semibold text-lg" style="color: var(--color-foreground)">Billing</h3>
				<div class="rounded-lg p-4" style="background-color: var(--color-secondary)">
					<p class="font-medium" style="color: var(--color-foreground)">Free Plan</p>
					<p class="text-sm mt-1" style="color: var(--color-muted-foreground)">50,000 tokens/month · 3 documents</p>
				</div>
				<Button>Upgrade to Pro</Button>
			</Card>

		{:else}
			<Card class="p-6">
				<h3 class="font-semibold text-lg capitalize" style="color: var(--color-foreground)">{activeSection}</h3>
				<p class="text-sm mt-2" style="color: var(--color-muted-foreground)">Coming in a future step.</p>
			</Card>
		{/if}
	</div>
</div>
