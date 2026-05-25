import api from './client';

export interface LoginPayload {
	email: string;
	password: string;
}

export interface RegisterPayload {
	email: string;
	password: string;
	full_name?: string;
}

export interface AuthResponse {
	access_token: string;
	token_type: string;
	user: User;
}

export interface User {
	id: string;
	email: string;
	full_name: string | null;
	avatar_url: string | null;
	is_verified: boolean;
	is_superuser: boolean;
}

export const authApi = {
	login: (payload: LoginPayload) =>
		api.post<AuthResponse>('/auth/login', payload),

	register: (payload: RegisterPayload) =>
		api.post<AuthResponse>('/auth/register', payload),

	logout: () =>
		api.post('/auth/logout'),

	refresh: () =>
		api.post<{ access_token: string }>('/auth/refresh'),

	me: () =>
		api.get<User>('/auth/me'),

	forgotPassword: (email: string) =>
		api.post('/auth/forgot-password', { email }),

	resetPassword: (token: string, password: string) =>
		api.post('/auth/reset-password', { token, password }),

	verifyEmail: (token: string) =>
		api.get(`/auth/verify-email/${token}`),
};
