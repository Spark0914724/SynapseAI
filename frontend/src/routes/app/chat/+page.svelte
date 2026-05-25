<script lang="ts">
	import { MessageSquare, Plus, Send, Trash2 } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Skeleton from '$lib/components/ui/Skeleton.svelte';
	import { chatApi } from '$lib/api';
	import type { Conversation, Message } from '$lib/api/chat';
	import { timeAgo } from '$lib/utils/format';
	import { toast } from 'svelte-sonner';

	let conversations = $state<Conversation[]>([]);
	let activeConversation = $state<Conversation | null>(null);
	let messages = $state<Message[]>([]);
	let input = $state('');
	let streaming = $state(false);
	let streamingContent = $state('');
	let loadingConvos = $state(true);

	async function loadConversations() {
		try {
			const { data } = await chatApi.listConversations();
			conversations = data;
		} catch {
			toast.error('Failed to load conversations');
		} finally {
			loadingConvos = false;
		}
	}

	async function selectConversation(convo: Conversation) {
		activeConversation = convo;
		const { data } = await chatApi.getMessages(convo.id);
		messages = data;
	}

	async function newConversation() {
		const { data } = await chatApi.createConversation();
		conversations = [data, ...conversations];
		activeConversation = data;
		messages = [];
	}

	async function sendMessage() {
		if (!input.trim() || !activeConversation || streaming) return;
		const content = input.trim();
		input = '';

		// Optimistic user message
		messages = [...messages, {
			id: crypto.randomUUID(), conversation_id: activeConversation.id,
			role: 'user', content, tokens_used: 0, created_at: new Date().toISOString()
		}];

		streaming = true;
		streamingContent = '';

		try {
			const res = await chatApi.sendMessage(activeConversation.id, content);
			const reader = res.body!.getReader();
			const decoder = new TextDecoder();

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				const chunk = decoder.decode(value);
				const lines = chunk.split('\n').filter((l) => l.startsWith('data: '));
				for (const line of lines) {
					const data = line.slice(6);
					if (data === '[DONE]') break;
					try { streamingContent += JSON.parse(data).delta ?? ''; } catch {}
				}
			}

			messages = [...messages, {
				id: crypto.randomUUID(), conversation_id: activeConversation.id,
				role: 'assistant', content: streamingContent, tokens_used: 0,
				created_at: new Date().toISOString()
			}];
		} catch {
			toast.error('Failed to send message');
		} finally {
			streaming = false;
			streamingContent = '';
		}
	}

	$effect(() => { loadConversations(); });
</script>

<svelte:head><title>AI Chat — SynapseAI</title></svelte:head>

<div class="flex h-full gap-4 -m-6 overflow-hidden" style="height: calc(100vh - 4rem)">
	<!-- Sidebar: conversation list -->
	<div class="w-64 shrink-0 flex flex-col overflow-hidden" style="border-right: 1px solid var(--color-border); background-color: var(--color-card)">
		<div class="flex items-center justify-between p-4" style="border-bottom: 1px solid var(--color-border)">
			<h2 class="font-semibold text-sm">Conversations</h2>
			<Button size="icon" variant="ghost" onclick={newConversation}>
				<Plus class="h-4 w-4" />
			</Button>
		</div>
		<div class="flex-1 overflow-y-auto p-2 space-y-1">
			{#if loadingConvos}
				{#each Array(5) as _}
					<Skeleton class="h-12 w-full rounded-lg" />
				{/each}
			{:else if conversations.length === 0}
				<div class="flex flex-col items-center justify-center h-32 text-center px-4">
					<MessageSquare class="h-8 w-8 text-muted-foreground mb-2" />
					<p class="text-xs text-muted-foreground">No conversations yet</p>
				</div>
			{:else}
				{#each conversations as convo}
					<button
						onclick={() => selectConversation(convo)}
						class="w-full text-left rounded-lg px-3 py-2.5 text-sm transition-colors
							{activeConversation?.id === convo.id
								? 'bg-violet-50 text-violet-700 dark:bg-violet-950 dark:text-violet-300'
								: 'hover:bg-accent text-foreground'}"
					>
						<p class="font-medium truncate">{convo.title || 'New conversation'}</p>
						<p class="text-xs text-muted-foreground mt-0.5">{timeAgo(convo.updated_at)}</p>
					</button>
				{/each}
			{/if}
		</div>
	</div>

	<!-- Chat area -->
	<div class="flex flex-1 flex-col overflow-hidden">
		{#if !activeConversation}
			<div class="flex flex-1 flex-col items-center justify-center gap-4 text-center p-8">
				<div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-50 dark:bg-violet-950">
					<MessageSquare class="h-8 w-8 text-violet-600" />
				</div>
				<div>
					<h3 class="text-lg font-semibold">Start a conversation</h3>
					<p class="text-sm text-muted-foreground mt-1">Select a conversation or create a new one</p>
				</div>
				<Button onclick={newConversation}>
					<Plus class="h-4 w-4" />
					New conversation
				</Button>
			</div>
		{:else}
			<!-- Messages -->
			<div class="flex-1 overflow-y-auto p-6 space-y-4">
				{#each messages as msg}
					<div class="flex gap-3 {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
						<div class="max-w-[70%] rounded-2xl px-4 py-3 text-sm
							{msg.role === 'user'
								? 'bg-violet-600 text-white rounded-br-sm'
								: 'bg-muted text-foreground rounded-bl-sm'}">
							{msg.content}
						</div>
					</div>
				{/each}
				{#if streaming && streamingContent}
					<div class="flex gap-3 justify-start">
						<div class="max-w-[70%] rounded-2xl rounded-bl-sm bg-muted px-4 py-3 text-sm">
							{streamingContent}<span class="animate-pulse">▋</span>
						</div>
					</div>
				{/if}
			</div>

			<!-- Input -->
			<div class="p-4" style="border-top: 1px solid var(--color-border)">
				<form onsubmit={(e) => { e.preventDefault(); sendMessage(); }} class="flex gap-2">
					<input
						bind:value={input}
						placeholder="Message SynapseAI..."
						disabled={streaming}
						class="flex-1 rounded-xl px-4 py-2.5 text-sm
							focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50"
						style="border: 1px solid var(--color-border); background-color: var(--color-background); color: var(--color-foreground);"
					/>
					<Button type="submit" loading={streaming} size="icon">
						<Send class="h-4 w-4" />
					</Button>
				</form>
			</div>
		{/if}
	</div>
</div>
