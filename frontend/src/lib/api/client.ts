import axios from 'axios';
import { browser } from '$app/environment';
import { authStore } from '$lib/stores/auth';
import { get } from 'svelte/store';

const api = axios.create({
	baseURL: '/api/v1',
	withCredentials: true, // send httpOnly refresh token cookie
	headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor — attach access token ──────────────────────────────
api.interceptors.request.use((config) => {
	const { accessToken } = get(authStore);
	if (accessToken) {
		config.headers.Authorization = `Bearer ${accessToken}`;
	}
	return config;
});

// ── Response interceptor — silent token refresh on 401 ────────────────────
let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null) {
	failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
	failedQueue = [];
}

api.interceptors.response.use(
	(res) => res,
	async (error) => {
		const original = error.config;
		if (error.response?.status === 401 && !original._retry) {
			if (isRefreshing) {
				return new Promise((resolve, reject) => {
					failedQueue.push({ resolve, reject });
				}).then((token) => {
					original.headers.Authorization = `Bearer ${token}`;
					return api(original);
				});
			}
			original._retry = true;
			isRefreshing = true;
			try {
				const { data } = await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true });
				authStore.setToken(data.access_token);
				processQueue(null, data.access_token);
				original.headers.Authorization = `Bearer ${data.access_token}`;
				return api(original);
			} catch (err) {
				processQueue(err, null);
				authStore.logout();
				return Promise.reject(err);
			} finally {
				isRefreshing = false;
			}
		}
		return Promise.reject(error);
	}
);

export default api;
