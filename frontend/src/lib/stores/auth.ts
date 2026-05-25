import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { User } from '$lib/api/auth';

interface AuthState {
	user: User | null;
	accessToken: string | null;
	isLoading: boolean;
	isAuthenticated: boolean;
}

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>({
		user: null,
		accessToken: browser ? localStorage.getItem('access_token') : null,
		isLoading: true,
		isAuthenticated: false,
	});

	return {
		subscribe,

		setAuth(user: User, token: string) {
			if (browser) localStorage.setItem('access_token', token);
			set({ user, accessToken: token, isLoading: false, isAuthenticated: true });
		},

		setToken(token: string) {
			if (browser) localStorage.setItem('access_token', token);
			update((s) => ({ ...s, accessToken: token }));
		},

		setUser(user: User) {
			update((s) => ({ ...s, user, isLoading: false, isAuthenticated: true }));
		},

		setLoading(isLoading: boolean) {
			update((s) => ({ ...s, isLoading }));
		},

		logout() {
			if (browser) localStorage.removeItem('access_token');
			set({ user: null, accessToken: null, isLoading: false, isAuthenticated: false });
		},
	};
}

export const authStore = createAuthStore();
