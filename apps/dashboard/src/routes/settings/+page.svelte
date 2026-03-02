<script lang="ts">
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { createApiKey, type ApiKeyResponse, checkHealth } from '$lib/api';
	import { user } from '$lib/stores/auth';

	let apiKeyName = $state('');
	let generatedKey: ApiKeyResponse | null = $state(null);
	let creating = $state(false);
	let error = $state('');
	let copied = $state(false);
	let apiHealthy = $state<boolean | null>(null);

	onMount(async () => {
		apiHealthy = await checkHealth();
	});

	async function handleCreateKey() {
		if (!apiKeyName.trim()) return;
		error = '';
		creating = true;
		try {
			generatedKey = await createApiKey(apiKeyName.trim());
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create API key';
		} finally {
			creating = false;
		}
	}

	async function copyKey() {
		if (!generatedKey) return;
		await navigator.clipboard.writeText(generatedKey.raw_key);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<svelte:head>
	<title>Settings — claude-kit</title>
</svelte:head>

<div class="mb-8">
	<h1
		class="text-2xl tracking-tight text-aurora"
		style="font-family: var(--font-display)"
	>
		Settings
	</h1>
	<p class="mt-1 text-sm" style="color: var(--color-text-muted)">
		Manage API keys and configuration
	</p>
</div>

<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
	<!-- API Status -->
	<div class="glass-card p-6" in:fly={{ y: 20, duration: 400, delay: 0 }}>
		<h3 class="mb-4 text-sm font-semibold" style="color: var(--color-text)">API Connection</h3>

		<div class="space-y-3">
			<div class="flex items-center justify-between">
				<span class="text-sm" style="color: var(--color-text-secondary)">Status</span>
				{#if apiHealthy === null}
					<span class="text-xs animate-pulse" style="color: var(--color-text-muted)">
						Checking…
					</span>
				{:else if apiHealthy}
					<span
						class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
						style="background: var(--color-success-light); color: var(--color-success)"
					>
						<span class="live-dot"></span>
						Connected
					</span>
				{:else}
					<span
						class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
						style="background: var(--color-error-light); color: var(--color-error)"
					>
						<span class="h-1.5 w-1.5 rounded-full" style="background: var(--color-error)"></span>
						Disconnected
					</span>
				{/if}
			</div>

			<div class="flex items-center justify-between">
				<span class="text-sm" style="color: var(--color-text-secondary)">Endpoint</span>
				<code class="text-xs font-mono" style="color: var(--color-text-muted)">
					/api/v1
				</code>
			</div>

			{#if $user}
				<div class="flex items-center justify-between">
					<span class="text-sm" style="color: var(--color-text-secondary)">Account</span>
					<span class="text-xs" style="color: var(--color-text-muted)">{$user.email}</span>
				</div>
			{/if}
		</div>
	</div>

	<!-- API Key Generation -->
	<div class="glass-card p-6" in:fly={{ y: 20, duration: 400, delay: 100 }}>
		<h3 class="mb-1 text-sm font-semibold" style="color: var(--color-text)">API Keys</h3>
		<p class="mb-4 text-xs" style="color: var(--color-text-muted)">
			Generate keys for CLI telemetry ingestion
		</p>

		{#if generatedKey}
			<div
				class="mb-4 rounded-lg p-4"
				style="background: var(--color-success-light); border: 1px solid var(--color-success)"
			>
				<p class="mb-2 text-xs font-medium" style="color: var(--color-success)">
					Key created — copy it now, it won't be shown again
				</p>
				<div class="flex items-center gap-2">
					<code
						class="flex-1 rounded-md px-3 py-2 text-xs font-mono"
						style="background: var(--color-bg-subtle); color: var(--color-text)"
					>
						{generatedKey.raw_key}
					</code>
					<button
						onclick={copyKey}
						class="cursor-pointer rounded-md px-3 py-2 text-xs font-medium text-white transition-colors"
						style="background: var(--color-success)"
					>
						{copied ? 'Copied' : 'Copy'}
					</button>
				</div>
			</div>
		{/if}

		<form onsubmit={handleCreateKey} class="flex gap-2">
			<input
				type="text"
				bind:value={apiKeyName}
				placeholder="Key name (e.g. dev-laptop)"
				required
				class="flex-1 rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
			/>
			<button
				type="submit"
				disabled={creating || !apiKeyName.trim()}
				class="cursor-pointer rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors disabled:opacity-50"
				style="background: linear-gradient(135deg, var(--color-aurora-teal), var(--color-aurora-violet))"
			>
				{creating ? '…' : 'Generate'}
			</button>
		</form>

		{#if error}
			<div
				class="mt-3 rounded-lg px-3 py-2 text-xs font-medium"
				style="background: var(--color-error-light); color: var(--color-error)"
			>
				{error}
			</div>
		{/if}
	</div>

	<!-- Configuration Guide -->
	<div class="glass-card p-6 lg:col-span-2" in:fly={{ y: 20, duration: 400, delay: 200 }}>
		<h3 class="mb-4 text-sm font-semibold" style="color: var(--color-text)">
			Connect Your CLI
		</h3>

		<div class="space-y-4">
			<div>
				<p class="mb-2 text-xs font-medium" style="color: var(--color-text-secondary)">
					1. Set the telemetry endpoint
				</p>
				<code
					class="block rounded-lg px-4 py-3 text-xs font-mono"
					style="background: var(--color-bg-subtle); color: var(--color-text)"
				>
					export CLAUDE_KIT_API_URL=http://localhost:8000/api/v1
				</code>
			</div>

			<div>
				<p class="mb-2 text-xs font-medium" style="color: var(--color-text-secondary)">
					2. Set your API key
				</p>
				<code
					class="block rounded-lg px-4 py-3 text-xs font-mono"
					style="background: var(--color-bg-subtle); color: var(--color-text)"
				>
					export CLAUDE_KIT_API_KEY=ck_your_api_key_here
				</code>
			</div>

			<div>
				<p class="mb-2 text-xs font-medium" style="color: var(--color-text-secondary)">
					3. Run with a kit
				</p>
				<code
					class="block rounded-lg px-4 py-3 text-xs font-mono"
					style="background: var(--color-bg-subtle); color: var(--color-text)"
				>
					claude-kit --kit cloud-python-engineer
				</code>
			</div>

			<p class="text-xs" style="color: var(--color-text-muted)">
				Telemetry events will automatically appear in the dashboard within seconds.
			</p>
		</div>
	</div>
</div>
