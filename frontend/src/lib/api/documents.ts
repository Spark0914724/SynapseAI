import api from './client';

export interface Document {
	id: string;
	filename: string;
	file_url: string;
	status: 'processing' | 'ready' | 'failed';
	page_count: number | null;
	workspace_id: string | null;
	created_at: string;
}

export interface Summary {
	document_id: string;
	content: string;
	format: 'bullets' | 'paragraph' | 'executive';
	created_at: string;
}

export const documentsApi = {
	list: (workspaceId?: string) =>
		api.get<Document[]>('/documents', { params: { workspace_id: workspaceId } }),

	upload: (file: File, workspaceId?: string) => {
		const form = new FormData();
		form.append('file', file);
		if (workspaceId) form.append('workspace_id', workspaceId);
		return api.post<Document>('/documents/upload', form, {
			headers: { 'Content-Type': 'multipart/form-data' },
		});
	},

	get: (id: string) =>
		api.get<Document>(`/documents/${id}`),

	delete: (id: string) =>
		api.delete(`/documents/${id}`),

	summarize: (id: string, format: Summary['format'] = 'bullets') =>
		api.post<Summary>(`/documents/${id}/summarize`, { format }),
};
