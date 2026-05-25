import api from './client';

export interface Conversation {
	id: string;
	title: string;
	model: string;
	workspace_id: string | null;
	created_at: string;
	updated_at: string;
}

export interface Message {
	id: string;
	conversation_id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	tokens_used: number;
	created_at: string;
}

export const chatApi = {
	listConversations: (workspaceId?: string) =>
		api.get<Conversation[]>('/chat/conversations', { params: { workspace_id: workspaceId } }),

	createConversation: (workspaceId?: string) =>
		api.post<Conversation>('/chat/conversations', { workspace_id: workspaceId }),

	getConversation: (id: string) =>
		api.get<Conversation>(`/chat/conversations/${id}`),

	deleteConversation: (id: string) =>
		api.delete(`/chat/conversations/${id}`),

	getMessages: (conversationId: string) =>
		api.get<Message[]>(`/chat/conversations/${conversationId}/messages`),

	// Returns a ReadableStream for SSE streaming
	sendMessage: (conversationId: string, content: string, model?: string) => {
		const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : '';
		return fetch(`/api/v1/chat/conversations/${conversationId}/messages`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token ?? ''}`,
			},
			body: JSON.stringify({ content, model }),
		});
	},
};
