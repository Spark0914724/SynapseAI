<script lang="ts">
	import { cn } from '$lib/utils/cn';

	interface Props {
		variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'link';
		size?: 'sm' | 'md' | 'lg' | 'icon';
		disabled?: boolean;
		loading?: boolean;
		type?: 'button' | 'submit' | 'reset';
		class?: string;
		onclick?: (e: MouseEvent) => void;
		children?: import('svelte').Snippet;
	}

	let {
		variant = 'default',
		size = 'md',
		disabled = false,
		loading = false,
		type = 'button',
		class: className = '',
		onclick,
		children,
	}: Props = $props();

	const base =
		'inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 disabled:pointer-events-none disabled:opacity-50';

	const variants = {
		default: 'bg-violet-600 text-white hover:bg-violet-700',
		secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700',
		outline: 'border border-[var(--color-border)] bg-transparent hover:bg-[var(--color-accent)] hover:text-[var(--color-accent-foreground)]',
		ghost: 'hover:bg-[var(--color-accent)] hover:text-[var(--color-accent-foreground)]',
		destructive: 'bg-red-600 text-white hover:bg-red-700',
		link: 'text-violet-600 underline-offset-4 hover:underline',
	};

	const sizes = {
		sm: 'h-8 px-3 text-xs',
		md: 'h-10 px-4 text-sm',
		lg: 'h-11 px-6 text-base',
		icon: 'h-10 w-10',
	};
</script>

<button
	{type}
	disabled={disabled || loading}
	class={cn(base, variants[variant], sizes[size], className)}
	{onclick}
>
	{#if loading}
		<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
		</svg>
	{/if}
	{@render children?.()}
</button>
