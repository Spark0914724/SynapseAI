import { writable } from 'svelte/store';
import { browser } from '$app/environment';

type Theme = 'light' | 'dark';

function createThemeStore() {
	// Default to light on SSR — only read localStorage in browser
	const initial: Theme = browser
		? ((localStorage.getItem('theme') as Theme) ??
		   (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))
		: 'light';

	const { subscribe, set } = writable<Theme>(initial);

	function apply(theme: Theme) {
		if (browser) {
			document.documentElement.classList.toggle('dark', theme === 'dark');
			localStorage.setItem('theme', theme);
		}
		set(theme);
	}

	// Apply on init (browser only)
	if (browser) apply(initial);

	return {
		subscribe,
		toggle() {
			const current = browser ? (localStorage.getItem('theme') as Theme) : 'light';
			apply(current === 'dark' ? 'light' : 'dark');
		},
		set: apply,
	};
}

export const themeStore = createThemeStore();
