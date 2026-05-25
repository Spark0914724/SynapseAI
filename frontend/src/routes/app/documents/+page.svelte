<script lang="ts">
	import { Upload, FileText, Trash2, Sparkles, AlertCircle, CheckCircle, Clock } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Skeleton from '$lib/components/ui/Skeleton.svelte';
	import { documentsApi } from '$lib/api';
	import type { Document } from '$lib/api/documents';
	import { formatBytes, formatDate } from '$lib/utils/format';
	import { toast } from 'svelte-sonner';

	let documents = $state<Document[]>([]);
	let loading = $state(true);
	let uploading = $state(false);
	let dragOver = $state(false);

	async function loadDocuments() {
		try {
			const { data } = await documentsApi.list();
			documents = data;
		} catch {
			toast.error('Failed to load documents');
		} finally {
			loading = false;
		}
	}

	async function handleUpload(files: FileList | null) {
		if (!files?.length) return;
		const file = files[0];
		const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
		if (!allowed.includes(file.type)) {
			toast.error('Only PDF and DOCX files are supported');
			return;
		}
		uploading = true;
		try {
			const { data } = await documentsApi.upload(file);
			documents = [data, ...documents];
			toast.success('Document uploaded — processing in background');
		} catch {
			toast.error('Upload failed');
		} finally {
			uploading = false;
		}
	}

	async function deleteDocument(id: string) {
		try {
			await documentsApi.delete(id);
			documents = documents.filter((d) => d.id !== id);
			toast.success('Document deleted');
		} catch {
			toast.error('Failed to delete document');
		}
	}

	const statusConfig = {
		processing: { label: 'Processing', variant: 'warning' as const, icon: Clock },
		ready: { label: 'Ready', variant: 'success' as const, icon: CheckCircle },
		failed: { label: 'Failed', variant: 'destructive' as const, icon: AlertCircle },
	};

	$effect(() => { loadDocuments(); });
</script>

<svelte:head><title>Documents — SynapseAI</title></svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-xl font-bold">Documents</h2>
			<p class="text-sm text-muted-foreground mt-0.5">Upload PDFs and DOCX files for AI analysis</p>
		</div>
	</div>

	<!-- Drop zone -->
	<div
		role="button"
		tabindex="0"
		class="relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors cursor-pointer
			{dragOver ? 'border-violet-500 bg-violet-50 dark:bg-violet-950/30' : 'border-border hover:border-violet-400 hover:bg-accent'}"
		ondragover={(e) => { e.preventDefault(); dragOver = true; }}
		ondragleave={() => (dragOver = false)}
		ondrop={(e) => { e.preventDefault(); dragOver = false; handleUpload(e.dataTransfer?.files ?? null); }}
		onclick={() => document.getElementById('file-input')?.click()}
		onkeydown={(e) => e.key === 'Enter' && document.getElementById('file-input')?.click()}
	>
		<input
			id="file-input"
			type="file"
			accept=".pdf,.docx"
			class="hidden"
			onchange={(e) => handleUpload((e.target as HTMLInputElement).files)}
		/>
		<Upload class="h-10 w-10 text-muted-foreground mb-3" />
		<p class="font-medium text-foreground">Drop files here or click to upload</p>
		<p class="text-sm text-muted-foreground mt-1">PDF, DOCX up to 50MB</p>
		{#if uploading}
			<div class="mt-4 flex items-center gap-2 text-sm text-violet-600">
				<div class="h-4 w-4 animate-spin rounded-full border-2 border-violet-600 border-t-transparent"></div>
				Uploading...
			</div>
		{/if}
	</div>

	<!-- Document list -->
	{#if loading}
		<div class="space-y-3">
			{#each Array(3) as _}
				<Skeleton class="h-20 w-full rounded-xl" />
			{/each}
		</div>
	{:else if documents.length === 0}
		<Card class="flex flex-col items-center justify-center p-12 text-center">
			<FileText class="h-12 w-12 text-muted-foreground mb-3" />
			<p class="font-medium">No documents yet</p>
			<p class="text-sm text-muted-foreground mt-1">Upload your first PDF or DOCX to get started</p>
		</Card>
	{:else}
		<div class="space-y-3">
			{#each documents as doc}
				{@const status = statusConfig[doc.status]}
				<Card class="flex items-center gap-4 p-4">
					<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-violet-50 dark:bg-violet-950">
						<FileText class="h-5 w-5 text-violet-600" />
					</div>
					<div class="flex-1 min-w-0">
						<p class="font-medium truncate">{doc.filename}</p>
						<p class="text-xs text-muted-foreground mt-0.5">
							{doc.page_count ? `${doc.page_count} pages · ` : ''}{formatDate(doc.created_at)}
						</p>
					</div>
					<Badge variant={status.variant}>{status.label}</Badge>
					{#if doc.status === 'ready'}
						<Button size="sm" variant="outline" onclick={() => {}}>
							<Sparkles class="h-3.5 w-3.5" />
							Summarize
						</Button>
					{/if}
					<Button size="icon" variant="ghost" onclick={() => deleteDocument(doc.id)}>
						<Trash2 class="h-4 w-4 text-muted-foreground" />
					</Button>
				</Card>
			{/each}
		</div>
	{/if}
</div>
