<script lang="ts">
	import { Mic, Upload, FileAudio } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import api from '$lib/api/client';
	import { toast } from 'svelte-sonner';

	let uploading = $state(false);
	let transcript = $state('');
	let filename = $state('');

	async function handleUpload(files: FileList | null) {
		if (!files?.length) return;
		const file = files[0];
		const allowed = ['audio/mpeg', 'audio/mp4', 'audio/wav', 'audio/x-m4a', 'audio/webm'];
		if (!allowed.includes(file.type)) {
			toast.error('Supported formats: MP3, MP4, WAV, M4A, WebM');
			return;
		}
		filename = file.name;
		uploading = true;
		try {
			const form = new FormData();
			form.append('file', file);
			const { data } = await api.post<{ transcript: string }>('/transcription/upload', form, {
				headers: { 'Content-Type': 'multipart/form-data' },
			});
			transcript = data.transcript;
			toast.success('Transcription complete');
		} catch {
			toast.error('Transcription failed');
		} finally {
			uploading = false;
		}
	}
</script>

<svelte:head><title>Transcription — SynapseAI</title></svelte:head>

<div class="space-y-6 max-w-3xl">
	<div>
		<h2 class="text-xl font-bold">Voice-to-Text Transcription</h2>
		<p class="text-sm text-muted-foreground mt-0.5">Upload audio files and get accurate transcripts via Whisper AI</p>
	</div>

	<!-- Upload zone -->
	<div
		role="button"
		tabindex="0"
		class="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border p-12 cursor-pointer hover:border-violet-400 hover:bg-accent transition-colors"
		onclick={() => document.getElementById('audio-input')?.click()}
		onkeydown={(e) => e.key === 'Enter' && document.getElementById('audio-input')?.click()}
	>
		<input
			id="audio-input"
			type="file"
			accept=".mp3,.mp4,.wav,.m4a,.webm"
			class="hidden"
			onchange={(e) => handleUpload((e.target as HTMLInputElement).files)}
		/>
		{#if uploading}
			<div class="h-10 w-10 animate-spin rounded-full border-4 border-violet-600 border-t-transparent mb-3"></div>
			<p class="font-medium">Transcribing {filename}...</p>
			<p class="text-sm text-muted-foreground mt-1">This may take a moment</p>
		{:else}
			<Mic class="h-10 w-10 text-muted-foreground mb-3" />
			<p class="font-medium">Drop audio file or click to upload</p>
			<p class="text-sm text-muted-foreground mt-1">MP3, MP4, WAV, M4A, WebM · max 25MB</p>
		{/if}
	</div>

	<!-- Transcript output -->
	{#if transcript}
		<Card class="p-5 space-y-4">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2">
					<FileAudio class="h-4 w-4 text-violet-600" />
					<span class="font-medium text-sm">{filename}</span>
				</div>
				<div class="flex gap-2">
					<Button size="sm" variant="outline" onclick={() => navigator.clipboard.writeText(transcript).then(() => toast.success('Copied'))}>
						Copy
					</Button>
					<Button size="sm" variant="outline">Generate Notes</Button>
				</div>
			</div>
			<div class="rounded-lg bg-muted p-4 text-sm leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto">
				{transcript}
			</div>
		</Card>
	{/if}
</div>
