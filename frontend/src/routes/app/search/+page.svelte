<script lang="ts">
	import { Search, FileText } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import api from '$lib/api/client';
	import { toast } from 'svelte-sonner';

	interface SearchResult {
		chunk_id: string;
		document_id: string;
		filename: string;
		content: string;
		score: number;
	}

	let query = $state('');
	let results = $state<SearchResult[]>([]);
	let loading = $state(false);
	let searched = $state(false);

	async function handleSearch(e: SubmitEvent) {
		e.preventDefault();
		if (!query.trim()) return;
		loading = true;
		searched = true;
		try {
			const { data } = await api.post<SearchResult[]>('/search', { query });
			results = data;
		} catch {
			toast.error('Search failed');
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>AI Search — SynapseAI</title></svelte:head>

<div class="space-y-6 max-w-3xl mx-auto">
	<div>
		<h2 class="text-xl font-bold">AI Search</h2>
		<p class="text-sm text-muted-foreground mt-0.5">Semantic search across all your documents</p>
	</div>

	<form onsubmit={handleSearch} class="flex gap-2">
		<div class="relative flex-1">
			<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
			<input
				bind:value={query}
				placeholder="Search your documents..."
				class="w-full rounded-xl pl-10 pr-4 py-2.5 text-sm
					focus:outline-none focus:ring-2 focus:ring-violet-500"
			style="border: 1px solid var(--color-border); background-color: var(--color-background); color: var(--color-foreground);"
			/>
		</div>
		<Button type="submit" loading={loading}>Search</Button>
	</form>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-violet-600 border-t-transparent"></div>
		</div>
	{:else if searched && results.length === 0}
		<Card class="flex flex-col items-center justify-center p-12 text-center">
			<Search class="h-10 w-10 text-muted-foreground mb-3" />
			<p class="font-medium">No results found</p>
			<p class="text-sm text-muted-foreground mt-1">Try a different search query</p>
		</Card>
	{:else if results.length > 0}
		<div class="space-y-3">
			{#each results as result}
				<Card class="p-4 space-y-2">
					<div class="flex items-center gap-2">
						<FileText class="h-4 w-4 text-violet-600 shrink-0" />
						<span class="text-sm font-medium text-violet-600">{result.filename}</span>
						<span class="ml-auto text-xs text-muted-foreground">
							{Math.round(result.score * 100)}% match
						</span>
					</div>
					<p class="text-sm text-foreground leading-relaxed">{result.content}</p>
				</Card>
			{/each}
		</div>
	{/if}
</div>
