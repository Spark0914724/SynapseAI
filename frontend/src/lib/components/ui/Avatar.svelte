<script lang="ts">
	import { cn } from '$lib/utils/cn';

	interface Props {
		src?: string | null;
		name?: string;
		size?: 'sm' | 'md' | 'lg';
		class?: string;
	}

	let { src = null, name = '', size = 'md', class: className = '' }: Props = $props();

	const sizes = { sm: 'h-7 w-7 text-xs', md: 'h-9 w-9 text-sm', lg: 'h-12 w-12 text-base' };

	const initials = $derived(
		name
			.split(' ')
			.map((n) => n[0])
			.slice(0, 2)
			.join('')
			.toUpperCase() || '?'
	);
</script>

<div class={cn('relative flex shrink-0 overflow-hidden rounded-full', sizes[size], className)}>
	{#if src}
		<img {src} alt={name} class="aspect-square h-full w-full object-cover" />
	{:else}
		<div class="flex h-full w-full items-center justify-center bg-violet-600 text-white font-medium">
			{initials}
		</div>
	{/if}
</div>
