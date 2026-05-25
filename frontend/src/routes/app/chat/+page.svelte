<script lang="ts">
	import { tick } from 'svelte';
	import { MessageSquare, Plus, Send, Trash2, Copy, Check, ChevronDown } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Skeleton from '$lib/components/ui/Skeleton.svelte';
	import { chatApi } from '$lib/api';
	import type { Conversation, Message } from '$lib/api/chat';
	import { timeAgo } from '$lib/utils/format';
	import { toast } from 'svelte-sonner';
	import { browser } from '$app/environment';

	// ── State ──────────────────────────────────────────────────────────────────
	let conversations = $state<Conversation[]>([]);
	let activeConversation = $state<Conversation | null>(null);
	let messages = $state<Message[]>([]);
	let input = $state('');
	let streaming = $state(false);
	let streamingContent = $state('');
	let loadingConvos = $state(true);
	let loadingMessages = $state(false);
	let selectedModel = $state('gpt-4o');
	let copiedId = $state<string | null>(null);
	let messagesEl = $state<HTMLDivElement | null>(null);

	const MODELS = [
		'deepseek/deepseek-v4-flash:free',
		'google/gemma-4-31b-it:free',
		'nvidia/nemotron-3-super-120b-a12b:free',
		'minimax/minimax-m2.5:free',
	];

	// ── Conversations ──────────────────────────────────────────────────────────
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
		selectedModel = convo.model;
		loadingMessages = true;
		try {
			const { data } = await chatApi.getMessages(convo.id);
			messages = data;
			await scrollToBottom();
		} catch {
			toast.error('Failed to load messages');
		} finally {
			loadingMessages = false;
		}
	}

	async function newConversation() {
		try {
			const { data } = await chatApi.createConversation(undefined);
			conversations = [data, ...conversations];
			activeConversation = data;
			messages = [];
		} catch {
			toast.error('Failed to create conversation');
		}
	}

	async function deleteConversation(id: string, e: MouseEvent) {
		e.stopPropagation();
		try {
			await chatApi.deleteConversation(id);
			conversations = conversations.filter((c) => c.id !== id);
			if (activeConversation?.id === id) {
				activeConversation = null;
				messages = [];
			}
			toast.success('Conversation deleted');
		} catch {
			toast.error('Failed to delete');
		}
	}

	// ── Send message ───────────────────────────────────────────────────────────
	async function sendMessage() {
		if (!input.trim() || !activeConversation || streaming) return;
		const content = input.trim();
		input = '';

		// Optimistic user message
		const tempUserMsg: Message = {
			id: crypto.randomUUID(),
			conversation_id: activeConversation.id,
			role: 'user',
			content,
			tokens_used: 0,
			created_at: new Date().toISOString(),
		};
		messages = [...messages, tempUserMsg];
		await scrollToBottom();

		streaming = true;
		streamingContent = '';
		let finalContent = '';

		try {
			const res = await chatApi.sendMessage(activeConversation.id, content, selectedModel);
			if (!res.ok) {
				const err = await res.json();
				throw new Error(err.detail ?? 'Request failed');
			}

			const reader = res.body!.getReader();
			const decoder = new TextDecoder();
			let buffer = '';
			let done = false;

			while (!done) {
				const { done: streamDone, value } = await reader.read();
				done = streamDone;
				if (value) buffer += decoder.decode(value, { stream: !streamDone });

				// Process all complete lines in the buffer
				const lines = buffer.split('\n');
				// Keep the last (potentially incomplete) line in the buffer
				buffer = lines.pop() ?? '';

				for (const line of lines) {
					const trimmed = line.trim();
					if (!trimmed.startsWith('data: ')) continue;
					const payload = trimmed.slice(6).trim();
					if (payload === '[DONE]') { done = true; break; }
					if (!payload) continue;
					try {
						const parsed = JSON.parse(payload);
						if (parsed.error) throw new Error(parsed.error);
						if (parsed.delta) {
							streamingContent += parsed.delta;
							finalContent = streamingContent;
							await scrollToBottom();
						}
					} catch (parseErr) {
						// ignore malformed chunks
					}
				}
			}

			// Commit streamed message to list
			const assistantMsg: Message = {
				id: crypto.randomUUID(),
				conversation_id: activeConversation.id,
				role: 'assistant',
				content: finalContent,
				tokens_used: 0,
				created_at: new Date().toISOString(),
			};
			messages = [...messages, assistantMsg];

			// Update conversation title in sidebar if it was auto-titled
			const { data: updated } = await chatApi.getConversation(activeConversation.id);
			activeConversation = updated;
			conversations = conversations.map((c) => (c.id === updated.id ? updated : c));

		} catch (err: any) {
			toast.error(err.message ?? 'Failed to send message');
			messages = messages.filter((m) => m.id !== tempUserMsg.id);
		} finally {
			streaming = false;
			streamingContent = '';
			finalContent = '';
			await scrollToBottom();
		}
	}

	// ── Helpers ────────────────────────────────────────────────────────────────
	async function scrollToBottom() {
		await tick();
		if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
	}

	async function copyMessage(id: string, content: string) {
		await navigator.clipboard.writeText(content);
		copiedId = id;
		setTimeout(() => (copiedId = null), 2000);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}

	$effect(() => { loadConversations(); });
</script>

<svelte:head><title>AI Chat — SynapseAI</title></svelte:head>

<div class="flex -m-6 overflow-hidden" style="height: calc(100vh - 4rem)">

	<!-- ── Conversation sidebar ── -->
	<div class="w-64 shrink-0 flex flex-col" style="border-right: 1px solid var(--color-border); background-color: var(--color-card)">
		<div class="flex items-center justify-between px-4 py-3" style="border-bottom: 1px solid var(--color-border)">
			<span class="text-sm font-semibold" style="color: var(--color-foreground)">Conversations</span>
			<Button size="icon" variant="ghost" onclick={newConversation}>
				<Plus class="h-4 w-4" />
			</Button>
		</div>

		<div class="flex-1 overflow-y-auto p-2 space-y-0.5">
			{#if loadingConvos}
				{#each Array(5) as _}
					<Skeleton class="h-14 w-full rounded-lg mb-1" />
				{/each}
			{:else if conversations.length === 0}
				<div class="flex flex-col items-center justify-center h-40 text-center px-4 gap-2">
					<MessageSquare class="h-8 w-8" style="color: var(--color-muted-foreground)" />
					<p class="text-xs" style="color: var(--color-muted-foreground)">No conversations yet</p>
					<Button size="sm" variant="outline" onclick={newConversation}>Start one</Button>
				</div>
			{:else}
				{#each conversations as convo}
					{@const active = activeConversation?.id === convo.id}
					<div
						role="button"
						tabindex="0"
						onclick={() => selectConversation(convo)}
						onkeydown={(e) => e.key === 'Enter' && selectConversation(convo)}
						class="group w-full text-left rounded-lg px-3 py-2.5 text-sm transition-colors relative cursor-pointer
							{active ? 'bg-violet-50 dark:bg-violet-950' : 'hover:bg-[var(--color-accent)]'}"
					>
						<p class="font-medium truncate pr-6 {active ? 'text-violet-700 dark:text-violet-300' : ''}"
							style={!active ? 'color: var(--color-foreground)' : ''}>
							{convo.title || 'New conversation'}
						</p>
						<p class="text-xs mt-0.5" style="color: var(--color-muted-foreground)">
							{timeAgo(convo.updated_at)}
						</p>
						<button
							onclick={(e) => deleteConversation(convo.id, e)}
							class="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:text-red-500"
							style="color: var(--color-muted-foreground)"
						>
							<Trash2 class="h-3.5 w-3.5" />
						</button>
					</div>
				{/each}
			{/if}
		</div>
	</div>

	<!-- ── Chat area ── -->
	<div class="flex flex-1 flex-col overflow-hidden">
		{#if !activeConversation}
			<!-- Empty state -->
			<div class="flex flex-1 flex-col items-center justify-center gap-5 text-center p-8">
				<div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-50 dark:bg-violet-950">
					<MessageSquare class="h-8 w-8 text-violet-600" />
				</div>
				<div>
					<h3 class="text-lg font-semibold" style="color: var(--color-foreground)">Start a conversation</h3>
					<p class="text-sm mt-1" style="color: var(--color-muted-foreground)">
						Ask anything — SynapseAI is ready to help
					</p>
				</div>
				<Button onclick={newConversation}>
					<Plus class="h-4 w-4" />
					New conversation
				</Button>
			</div>
		{:else}
			<!-- Topbar with model selector -->
			<div class="flex items-center justify-between px-5 py-3 shrink-0"
				style="border-bottom: 1px solid var(--color-border)">
				<p class="text-sm font-medium truncate max-w-xs" style="color: var(--color-foreground)">
					{activeConversation.title || 'New conversation'}
				</p>
				<div class="flex items-center gap-1 rounded-lg px-2 py-1 text-xs"
					style="border: 1px solid var(--color-border); color: var(--color-muted-foreground)">
					<select
						bind:value={selectedModel}
						class="bg-transparent outline-none cursor-pointer text-xs"
						style="color: var(--color-foreground)"
					>
						{#each MODELS as m}
							<option value={m}>{m}</option>
						{/each}
					</select>
				</div>
			</div>

			<!-- Messages -->
			<div bind:this={messagesEl} class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
				{#if loadingMessages}
					{#each Array(3) as _}
						<div class="flex gap-3">
							<Skeleton class="h-10 w-10 rounded-full shrink-0" />
							<Skeleton class="h-16 flex-1 rounded-2xl" />
						</div>
					{/each}
				{:else}
					{#each messages as msg (msg.id)}
						<div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'} group">
							<div class="relative max-w-[72%]">
								<div
									class="rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap
										{msg.role === 'user'
											? 'bg-violet-600 text-white rounded-br-sm'
											: 'rounded-bl-sm'}"
									style={msg.role !== 'user' ? 'background-color: var(--color-secondary); color: var(--color-foreground)' : ''}
								>
									{msg.content}
								</div>
								<!-- Copy button -->
								<button
									onclick={() => copyMessage(msg.id, msg.content)}
									class="absolute -bottom-5 {msg.role === 'user' ? 'right-0' : 'left-0'}
										opacity-0 group-hover:opacity-100 transition-opacity text-xs flex items-center gap-1 px-1.5 py-0.5 rounded"
									style="color: var(--color-muted-foreground)"
								>
									{#if copiedId === msg.id}
										<Check class="h-3 w-3 text-green-500" />
										<span class="text-green-500">Copied</span>
									{:else}
										<Copy class="h-3 w-3" />
										<span>Copy</span>
									{/if}
								</button>
							</div>
						</div>
					{/each}

					<!-- Streaming bubble -->
					{#if streaming}
						<div class="flex justify-start">
							<div class="max-w-[72%] rounded-2xl rounded-bl-sm px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap"
								style="background-color: var(--color-secondary); color: var(--color-foreground)">
								{#if streamingContent}
									{streamingContent}<span class="animate-pulse ml-0.5">▋</span>
								{:else}
									<span class="flex gap-1 items-center" style="color: var(--color-muted-foreground)">
										<span class="h-1.5 w-1.5 rounded-full bg-violet-500 animate-bounce" style="animation-delay:0ms"></span>
										<span class="h-1.5 w-1.5 rounded-full bg-violet-500 animate-bounce" style="animation-delay:150ms"></span>
										<span class="h-1.5 w-1.5 rounded-full bg-violet-500 animate-bounce" style="animation-delay:300ms"></span>
									</span>
								{/if}
							</div>
						</div>
					{/if}
				{/if}
			</div>

			<!-- Input bar -->
			<div class="px-5 py-4 shrink-0" style="border-top: 1px solid var(--color-border)">
				<div class="flex gap-2 items-end">
					<textarea
						bind:value={input}
						onkeydown={handleKeydown}
						placeholder="Message SynapseAI… (Enter to send, Shift+Enter for newline)"
						disabled={streaming}
						rows={1}
						class="flex-1 resize-none rounded-xl px-4 py-2.5 text-sm leading-relaxed
							focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50
							max-h-40 overflow-y-auto"
						style="border: 1px solid var(--color-border); background-color: var(--color-background); color: var(--color-foreground);"
					></textarea>
					<Button
						onclick={sendMessage}
						loading={streaming}
						disabled={!input.trim()}
						size="icon"
						class="shrink-0 mb-0.5"
					>
						<Send class="h-4 w-4" />
					</Button>
				</div>
				<p class="text-xs mt-1.5 text-center" style="color: var(--color-muted-foreground)">
					SynapseAI can make mistakes. Verify important information.
				</p>
			</div>
		{/if}
	</div>
</div>
