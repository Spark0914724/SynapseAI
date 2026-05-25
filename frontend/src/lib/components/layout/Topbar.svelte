<script lang="ts">
	import { Sun, Moon, Bell, Search } from '@lucide/svelte';
	import { themeStore } from '$lib/stores';
	import Avatar from '$lib/components/ui/Avatar.svelte';
	import { authStore } from '$lib/stores';

	interface Props { title?: string }
	let { title = '' }: Props = $props();
</script>

<header class="flex h-16 items-center justify-between px-6"
	style="border-bottom: 1px solid var(--color-border); background-color: var(--color-card);">
	<div class="flex items-center gap-4">
		{#if title}
			<h1 class="text-lg font-semibold" style="color: var(--color-foreground)">{title}</h1>
		{/if}
	</div>

	<div class="flex items-center gap-2">
		<!-- Global search hint -->
		<button
			class="hidden md:flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors hover:bg-[var(--color-accent)]"
			style="border: 1px solid var(--color-border); background-color: var(--color-background); color: var(--color-muted-foreground);"
		>
			<Search class="h-3.5 w-3.5" />
			<span>Search...</span>
			<kbd class="ml-2 rounded px-1.5 py-0.5 text-xs" style="background-color: var(--color-muted)">⌘K</kbd>
		</button>

		<!-- Theme toggle -->
		<button
			onclick={() => themeStore.toggle()}
			class="flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:bg-[var(--color-accent)]"
			style="color: var(--color-muted-foreground)"
			title="Toggle theme"
		>
			{#if $themeStore === 'dark'}
				<Sun class="h-4 w-4" />
			{:else}
				<Moon class="h-4 w-4" />
			{/if}
		</button>

		<!-- Notifications -->
		<button class="flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:bg-[var(--color-accent)]"
			style="color: var(--color-muted-foreground)">
			<Bell class="h-4 w-4" />
		</button>

		<Avatar
			src={$authStore.user?.avatar_url}
			name={$authStore.user?.full_name ?? $authStore.user?.email ?? ''}
			size="sm"
		/>
	</div>
</header>
