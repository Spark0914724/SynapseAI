<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		MessageSquare, FileText, Mic, Zap, Search,
		Settings, Users, LayoutDashboard, ChevronDown, LogOut
	} from '@lucide/svelte';
	import Avatar from '$lib/components/ui/Avatar.svelte';
	import { authStore, workspaceStore } from '$lib/stores';
	import { authApi } from '$lib/api';

	const navItems = [
		{ href: '/app', label: 'Dashboard', icon: LayoutDashboard },
		{ href: '/app/chat', label: 'AI Chat', icon: MessageSquare },
		{ href: '/app/documents', label: 'Documents', icon: FileText },
		{ href: '/app/search', label: 'AI Search', icon: Search },
		{ href: '/app/tools', label: 'AI Tools', icon: Zap },
		{ href: '/app/transcription', label: 'Transcription', icon: Mic },
		{ href: '/app/workspace', label: 'Workspace', icon: Users },
		{ href: '/app/settings', label: 'Settings', icon: Settings },
	];

	async function handleLogout() {
		try { await authApi.logout(); } catch {}
		authStore.logout();
		workspaceStore.reset();
		goto('/login');
	}
</script>

<aside class="flex h-screen w-64 flex-col" style="border-right: 1px solid var(--color-border); background-color: var(--color-card);">
	<!-- Logo -->
	<div class="flex h-16 items-center gap-2 px-6" style="border-bottom: 1px solid var(--color-border);">
		<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600">
			<Zap class="h-4 w-4 text-white" />
		</div>
		<span class="text-lg font-bold" style="color: var(--color-foreground)">SynapseAI</span>
	</div>

	<!-- Workspace switcher -->
	{#if $workspaceStore.activeWorkspace}
		<div class="px-3 py-3" style="border-bottom: 1px solid var(--color-border);">
			<button
				class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-[var(--color-accent)]"
				onclick={() => goto('/app/workspace')}
			>
				<div class="flex h-6 w-6 items-center justify-center rounded bg-violet-100 dark:bg-violet-900 text-violet-600 text-xs font-bold">
					{$workspaceStore.activeWorkspace.name[0].toUpperCase()}
				</div>
				<span class="flex-1 truncate text-left font-medium" style="color: var(--color-foreground)">{$workspaceStore.activeWorkspace.name}</span>
				<ChevronDown class="h-3.5 w-3.5" style="color: var(--color-muted-foreground)" />
			</button>
		</div>
	{/if}

	<!-- Nav -->
	<nav class="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
		{#each navItems as item}
			{@const active = $page.url.pathname === item.href || ($page.url.pathname.startsWith(item.href) && item.href !== '/app')}
			{@const Icon = item.icon}
			<a
				href={item.href}
				class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors
					{active
						? 'bg-violet-50 text-violet-700 font-medium dark:bg-violet-950 dark:text-violet-300'
						: 'hover:bg-[var(--color-accent)]'}"
				style={!active ? `color: var(--color-muted-foreground)` : ''}
			>
				<Icon class="h-4 w-4 shrink-0" />
				{item.label}
			</a>
		{/each}
	</nav>

	<!-- User footer -->
	<div class="p-3" style="border-top: 1px solid var(--color-border);">
		<div class="flex items-center gap-3 rounded-lg px-3 py-2">
			<Avatar src={$authStore.user?.avatar_url} name={$authStore.user?.full_name ?? $authStore.user?.email ?? ''} size="sm" />
			<div class="flex-1 min-w-0">
				<p class="text-sm font-medium truncate" style="color: var(--color-foreground)">{$authStore.user?.full_name ?? 'User'}</p>
				<p class="text-xs truncate" style="color: var(--color-muted-foreground)">{$authStore.user?.email}</p>
			</div>
			<button onclick={handleLogout} class="transition-colors hover:text-red-500" style="color: var(--color-muted-foreground)" title="Log out">
				<LogOut class="h-4 w-4" />
			</button>
		</div>
	</div>
</aside>
