<script lang="ts">
	import { cn } from '$lib/utils/cn';

	interface Props {
		variant?: 'default' | 'secondary' | 'success' | 'warning' | 'destructive' | 'outline';
		class?: string;
		children?: import('svelte').Snippet;
	}

	let { variant = 'default', class: className = '', children }: Props = $props();

	const variants = {
		default: 'bg-violet-100 text-violet-800 dark:bg-violet-900 dark:text-violet-200',
		secondary: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
		success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
		warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
		destructive: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
		outline: 'border border-[var(--color-border)]',
	};
</script>

<span class={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', variants[variant], className)}>
	{@render children?.()}
</span>
