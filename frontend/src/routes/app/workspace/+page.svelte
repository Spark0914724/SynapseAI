<script lang="ts">
	import { Users, Plus, Mail, Crown, Shield, User, Trash2 } from '@lucide/svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Avatar from '$lib/components/ui/Avatar.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { workspacesApi } from '$lib/api';
	import { workspaceStore } from '$lib/stores';
	import type { WorkspaceMember } from '$lib/api/workspaces';
	import { toast } from 'svelte-sonner';

	let members = $state<WorkspaceMember[]>([]);
	let inviteEmail = $state('');
	let inviting = $state(false);
	let loading = $state(true);

	const roleConfig = {
		owner: { label: 'Owner', variant: 'default' as const, icon: Crown },
		admin: { label: 'Admin', variant: 'secondary' as const, icon: Shield },
		member: { label: 'Member', variant: 'outline' as const, icon: User },
	};

	async function loadMembers() {
		const ws = $workspaceStore.activeWorkspace;
		if (!ws) return;
		try {
			const { data } = await workspacesApi.getMembers(ws.id);
			members = data;
		} catch {
			toast.error('Failed to load members');
		} finally {
			loading = false;
		}
	}

	async function inviteMember() {
		const ws = $workspaceStore.activeWorkspace;
		if (!ws || !inviteEmail.trim()) return;
		inviting = true;
		try {
			await workspacesApi.invite(ws.id, inviteEmail);
			toast.success(`Invite sent to ${inviteEmail}`);
			inviteEmail = '';
		} catch {
			toast.error('Failed to send invite');
		} finally {
			inviting = false;
		}
	}

	$effect(() => { loadMembers(); });
</script>

<svelte:head><title>Workspace — SynapseAI</title></svelte:head>

<div class="space-y-6 max-w-3xl">
	<div>
		<h2 class="text-xl font-bold">Workspace</h2>
		<p class="text-sm text-muted-foreground mt-0.5">
			{$workspaceStore.activeWorkspace?.name ?? 'No workspace selected'}
		</p>
	</div>

	<!-- Invite -->
	<Card class="p-5">
		<h3 class="font-semibold mb-4">Invite Members</h3>
		<div class="flex gap-2">
			<div class="flex-1">
				<Input
					id="invite-email"
					type="email"
					placeholder="colleague@company.com"
					bind:value={inviteEmail}
				/>
			</div>
			<Button loading={inviting} onclick={inviteMember}>
				<Mail class="h-4 w-4" />
				Send invite
			</Button>
		</div>
	</Card>

	<!-- Members list -->
	<Card class="p-5">
		<div class="flex items-center gap-2 mb-4">
			<Users class="h-4 w-4 text-muted-foreground" />
			<h3 class="font-semibold">Members ({members.length})</h3>
		</div>

		{#if loading}
			<div class="space-y-3">
				{#each Array(3) as _}
					<div class="flex items-center gap-3 py-2">
						<div class="h-9 w-9 rounded-full bg-muted animate-pulse"></div>
						<div class="flex-1 space-y-1.5">
							<div class="h-3.5 w-32 rounded bg-muted animate-pulse"></div>
							<div class="h-3 w-48 rounded bg-muted animate-pulse"></div>
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="space-y-1">
				{#each members as member}
					{@const role = roleConfig[member.role]}
					<div class="flex items-center gap-3 rounded-lg px-2 py-2.5 hover:bg-accent transition-colors">
						<Avatar src={member.avatar_url} name={member.full_name ?? member.email} size="sm" />
						<div class="flex-1 min-w-0">
							<p class="text-sm font-medium truncate">{member.full_name ?? member.email}</p>
							<p class="text-xs text-muted-foreground truncate">{member.email}</p>
						</div>
						<Badge variant={role.variant}>{role.label}</Badge>
						{#if member.role !== 'owner'}
							<Button size="icon" variant="ghost">
								<Trash2 class="h-3.5 w-3.5 text-muted-foreground" />
							</Button>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</Card>
</div>
