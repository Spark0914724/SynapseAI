<script lang="ts">
	import { cn } from '$lib/utils/cn';

	interface Props {
		class?: string;
		children?: import('svelte').Snippet;
	}

	let { class: className = '', children }: Props = $props();
</script>

<div class={cn('rounded-xl border bg-[var(--color-card)] text-[var(--color-card-foreground)] shadow-sm', className)}>
	{@render children?.()}
</div>
