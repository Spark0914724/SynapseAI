<script lang="ts">
	import { cn } from '$lib/utils/cn';

	interface Props {
		type?: string;
		placeholder?: string;
		value?: string;
		disabled?: boolean;
		error?: string;
		label?: string;
		id?: string;
		class?: string;
		required?: boolean;
		oninput?: (e: Event) => void;
		onchange?: (e: Event) => void;
	}

	let {
		type = 'text',
		placeholder = '',
		value = $bindable(''),
		disabled = false,
		error = '',
		label = '',
		id = '',
		class: className = '',
		required = false,
		oninput,
		onchange,
	}: Props = $props();
</script>

<div class="flex flex-col gap-1.5">
	{#if label}
		<label for={id} class="text-sm font-medium" style="color: var(--color-foreground)">
			{label}
			{#if required}<span class="text-red-500 ml-0.5">*</span>{/if}
		</label>
	{/if}
	<input
		{id}
		{type}
		{placeholder}
		{disabled}
		{required}
		bind:value
		{oninput}
		{onchange}
		class={cn(
			'flex h-10 w-full rounded-md border px-3 py-2 text-sm',
			'placeholder:text-[var(--color-muted-foreground)]',
			'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2',
			'disabled:cursor-not-allowed disabled:opacity-50',
			error ? 'border-red-500' : 'border-[var(--color-border)]',
			className
		)}
		style="background-color: var(--color-background); color: var(--color-foreground);"
	/>
	{#if error}
		<p class="text-xs text-red-500">{error}</p>
	{/if}
</div>
