<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { fly } from 'svelte/transition';
	import { getSessions, type SessionSummary, type SessionListResponse } from '$lib/api';

	let data: SessionListResponse | null = $state(null);
	let loading = $state(true);
	let error = $state('');
	let currentPage = $state(1);
	let pollTimer: ReturnType<typeof setInterval> | null = $state(null);
	const perPage = 25;

	async function loadPage(page: number, quiet = false) {
		if (!quiet) loading = true;
		if (!quiet) error = '';
		try {
			data = await getSessions(page, perPage);
			currentPage = page;
			error = '';
		} catch (e) {
			if (!quiet) {
				const msg = e instanceof Error ? e.message : String(e);
				error = msg || 'Failed to load sessions';
			}
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadPage(1);
		pollTimer = setInterval(() => loadPage(currentPage, true), 1000);
	});

	onDestroy(() => {
		if (pollTimer) clearInterval(pollTimer);
	});

	function fmt(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit'
		});
	}

	function dur(s: number | null): string {
		if (!s) return '—';
		if (s < 60) return `${Math.round(s)}s`;
		return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
	}

	function tokens(n: number): string {
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
		if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
		return String(n);
	}

	function cost(n: number | null): string {
		if (n == null || n === 0) return '—';
		return `$${n.toFixed(3)}`;
	}

	function pluginBadges(list: string[]): { label: string; kind: string }[] {
		return list.map((p) => {
			const short = p.replace(/^(core|cloud|embedded|frontend)-/, '');
			let kind = 'core';
			if (p.startsWith('frontend-')) kind = 'team';
			else if (p.startsWith('cloud-')) kind = 'team';
			else if (p.startsWith('embedded-')) kind = 'team';
			else if (p.startsWith('system-')) kind = 'system';
			return { label: short, kind };
		});
	}

	function isLive(s: SessionSummary): boolean {
		return s.end_time === null;
	}

	function calcTotalPages(d: SessionListResponse | null): number {
		return d ? Math.ceil(d.total / perPage) : 0;
	}
	let totalPages = $derived(calcTotalPages(data));
</script>

<svelte:head>
	<title>Sessions — claude-kit</title>
</svelte:head>

<div class="mb-6 flex items-center justify-between">
	<div>
		<h1
			class="text-2xl tracking-tight text-aurora"
			style="font-family: var(--font-display)"
		>
			Sessions
		</h1>
		<p class="mt-1 text-sm" style="color: var(--color-text-muted)">
			{#if data}
				<span class="font-mono">{data.total}</span> sessions recorded
				<span class="ml-2 inline-flex items-center gap-1 text-[11px]" style="color: var(--color-success)">
					<span class="live-dot"></span>
					polling
				</span>
			{:else}
				Loading…
			{/if}
		</p>
	</div>
</div>

{#if loading && !data}
	<div class="flex items-center justify-center py-20">
		<div class="text-sm tracking-wide animate-pulse" style="color: var(--color-text-muted)">
			Loading sessions…
		</div>
	</div>
{:else if error}
	<div
		class="rounded-lg px-4 py-3 text-sm"
		style="background: var(--color-error-light); color: var(--color-error)"
	>
		{error}
	</div>
{:else if data && data.sessions.length === 0}
	<div class="glass-card px-8 py-16 text-center">
		<p class="text-sm" style="color: var(--color-text-muted)">No sessions recorded yet</p>
		<p class="mt-2 text-xs" style="color: var(--color-text-muted)">
			Run <code class="font-mono" style="color: var(--color-accent)">./claude-kit --kit &lt;name&gt;</code> to start
		</p>
	</div>
{:else if data}
	<div class="space-y-2">
		{#each data.sessions as s, i}
			<div in:fly={{ x: -20, duration: 350, delay: Math.min(i * 50, 500) }}>
				<button
					onclick={() => goto(`/sessions/${s.session_id}`)}
					class="glass-card flex w-full cursor-pointer items-center gap-4 px-5 py-4 text-left transition-all"
				>
					<!-- Status dot + ID -->
					<div class="flex items-center gap-3 min-w-[180px]">
						{#if isLive(s)}
							<span class="live-dot"></span>
						{:else}
							<span class="h-2.5 w-2.5 rounded-full" style="background: var(--color-border)"></span>
						{/if}
						<div>
							<div class="font-mono text-xs font-medium" style="color: var(--color-text)">
								{s.session_id.slice(0, 8)}
							</div>
							<div class="text-[11px]" style="color: var(--color-text-muted)">{fmt(s.start_time)}</div>
						</div>
					</div>

					<!-- Model -->
					<div class="min-w-[100px]">
						{#if s.model}
							<span
								class="inline-block rounded-md px-2 py-0.5 text-[11px] font-medium"
								style="background: var(--color-accent-light); color: var(--color-accent)"
							>
								{s.model}
							</span>
						{:else}
							<span class="text-[11px]" style="color: var(--color-text-muted)">—</span>
						{/if}
					</div>

					<!-- Plugins -->
					<div class="flex flex-1 flex-wrap gap-1">
						{#each pluginBadges(s.plugins_loaded).filter((b) => b.kind === 'team').slice(0, 4) as badge}
							<span
								class="inline-block rounded px-1.5 py-0.5 text-[10px] font-medium"
								style="background: var(--color-accent-light); color: var(--color-accent)"
							>
								{badge.label}
							</span>
						{/each}
						{#if s.plugins_loaded.length > 4}
							<span class="text-[10px]" style="color: var(--color-text-muted)">
								+{s.plugins_loaded.length - pluginBadges(s.plugins_loaded).filter((b) => b.kind === 'team').length} core
							</span>
						{/if}
					</div>

					<!-- Stats -->
					<div class="flex items-center gap-6 text-right">
						<div>
							<div class="font-mono text-xs font-medium" style="color: var(--color-text)">{s.total_turns}</div>
							<div class="text-[10px]" style="color: var(--color-text-muted)">turns</div>
						</div>
						<div>
							<div class="font-mono text-xs font-medium" style="color: var(--color-text)">
								{tokens(s.total_tokens_in + s.total_tokens_out)}
							</div>
							<div class="text-[10px]" style="color: var(--color-text-muted)">tokens</div>
						</div>
						<div>
							<div class="font-mono text-xs font-medium" style="color: var(--color-text)">{cost(s.cost_usd)}</div>
							<div class="text-[10px]" style="color: var(--color-text-muted)">cost</div>
						</div>
						<div class="min-w-[60px]">
							<div class="text-xs" style="color: var(--color-text-secondary)">{dur(s.duration_s)}</div>
						</div>
					</div>

					<!-- Arrow -->
					<div class="text-sm" style="color: var(--color-text-muted)">→</div>
				</button>
			</div>
		{/each}
	</div>

	<!-- Pagination -->
	{#if totalPages > 1}
		<div class="mt-6 flex items-center justify-between">
			<p class="text-xs" style="color: var(--color-text-muted)">
				Page {currentPage} of {totalPages}
			</p>
			<div class="flex gap-2">
				<button
					disabled={currentPage <= 1}
					onclick={() => loadPage(currentPage - 1)}
					class="cursor-pointer rounded-md border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-white/5 disabled:opacity-40 disabled:cursor-default"
					style="border-color: var(--color-border); color: var(--color-text-secondary); background: transparent"
				>
					Previous
				</button>
				<button
					disabled={currentPage >= totalPages}
					onclick={() => loadPage(currentPage + 1)}
					class="cursor-pointer rounded-md border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-white/5 disabled:opacity-40 disabled:cursor-default"
					style="border-color: var(--color-border); color: var(--color-text-secondary); background: transparent"
				>
					Next
				</button>
			</div>
		</div>
	{/if}
{/if}
