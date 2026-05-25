<script lang="ts">
	import { FileText, CheckSquare, Mic, Search, Sparkles } from '@lucide/svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	const tools = [
		{
			icon: FileText,
			title: 'Meeting Notes Generator',
			description: 'Paste a transcript or upload audio — get structured notes, action items, and decisions.',
			href: '/app/tools/meeting-notes',
			badge: 'Popular',
		},
		{
			icon: CheckSquare,
			title: 'AI Task Planner',
			description: 'Describe your project goal and get a full task breakdown with priorities and estimates.',
			href: '/app/tools/task-planner',
			badge: null,
		},
		{
			icon: Sparkles,
			title: 'AI Summarizer',
			description: 'Summarize any text or document into bullets, paragraphs, or executive briefs.',
			href: '/app/tools/summarizer',
			badge: null,
		},
		{
			icon: Search,
			title: 'AI Search',
			description: 'Semantic search across all your uploaded documents and chat history.',
			href: '/app/search',
			badge: null,
		},
	];
</script>

<svelte:head><title>AI Tools — SynapseAI</title></svelte:head>

<div class="space-y-6">
	<div>
		<h2 class="text-xl font-bold">AI Tools</h2>
		<p class="text-sm text-muted-foreground mt-0.5">Specialized AI tools for your workflow</p>
	</div>

	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-2">
		{#each tools as tool}
			{@const Icon = tool.icon}
			<Card class="flex flex-col gap-4 p-6 hover:shadow-md transition-shadow">
				<div class="flex items-start gap-4">
					<div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-50 dark:bg-violet-950">
						<Icon class="h-5 w-5 text-violet-600" />
					</div>
					<div class="flex-1">
						<div class="flex items-center gap-2">
							<h3 class="font-semibold text-foreground">{tool.title}</h3>
							{#if tool.badge}
								<span class="rounded-full bg-violet-100 dark:bg-violet-900 px-2 py-0.5 text-xs font-medium text-violet-700 dark:text-violet-300">
									{tool.badge}
								</span>
							{/if}
						</div>
						<p class="text-sm text-muted-foreground mt-1">{tool.description}</p>
					</div>
				</div>
				<Button variant="outline" class="w-full" onclick={() => {}}>Open tool</Button>
			</Card>
		{/each}
	</div>
</div>
