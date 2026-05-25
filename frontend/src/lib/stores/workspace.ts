import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { Workspace } from '$lib/api/workspaces';

interface WorkspaceState {
	workspaces: Workspace[];
	activeWorkspace: Workspace | null;
}

function createWorkspaceStore() {
	const { subscribe, set, update } = writable<WorkspaceState>({
		workspaces: [],
		activeWorkspace: null,
	});

	return {
		subscribe,

		setWorkspaces(workspaces: Workspace[]) {
			const savedId = browser ? localStorage.getItem('active_workspace_id') : null;
			const active = workspaces.find((w) => w.id === savedId) ?? workspaces[0] ?? null;
			update((s) => ({ ...s, workspaces, activeWorkspace: s.activeWorkspace ?? active }));
		},

		setActive(workspace: Workspace) {
			if (browser) localStorage.setItem('active_workspace_id', workspace.id);
			update((s) => ({ ...s, activeWorkspace: workspace }));
		},

		reset() {
			set({ workspaces: [], activeWorkspace: null });
		},
	};
}

export const workspaceStore = createWorkspaceStore();
