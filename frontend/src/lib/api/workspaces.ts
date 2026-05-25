import api from './client';

export interface Workspace {
	id: string;
	name: string;
	slug: string;
	logo_url: string | null;
	owner_id: string;
	created_at: string;
}

export interface WorkspaceMember {
	user_id: string;
	email: string;
	full_name: string | null;
	avatar_url: string | null;
	role: 'owner' | 'admin' | 'member';
	joined_at: string;
}

export const workspacesApi = {
	list: () =>
		api.get<Workspace[]>('/workspaces'),

	create: (name: string) =>
		api.post<Workspace>('/workspaces', { name }),

	get: (id: string) =>
		api.get<Workspace>(`/workspaces/${id}`),

	update: (id: string, data: Partial<Pick<Workspace, 'name' | 'logo_url'>>) =>
		api.patch<Workspace>(`/workspaces/${id}`, data),

	delete: (id: string) =>
		api.delete(`/workspaces/${id}`),

	getMembers: (id: string) =>
		api.get<WorkspaceMember[]>(`/workspaces/${id}/members`),

	invite: (id: string, email: string) =>
		api.post(`/workspaces/${id}/invite`, { email }),

	removeMember: (workspaceId: string, userId: string) =>
		api.delete(`/workspaces/${workspaceId}/members/${userId}`),

	updateMemberRole: (workspaceId: string, userId: string, role: WorkspaceMember['role']) =>
		api.patch(`/workspaces/${workspaceId}/members/${userId}`, { role }),

	joinByToken: (token: string) =>
		api.post(`/workspaces/join/${token}`),
};
