<script lang="ts">
	import type { SessionSummary } from '$lib/api';

	let { sessions }: { sessions: SessionSummary[] } = $props();

	function fmt(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function dur(s: number | null): string {
		if (!s) return '—';
		if (s < 60) return `${Math.round(s)}s`;
		return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
	}

	function tokens(n: number): string {
		if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
		return String(n);
	}

	function cost(n: number | null): string {
		if (n == null || n === 0) return '—';
		return `$${n.toFixed(3)}`;
	}

	function plugins(list: string[]): string {
		if (!list.length) return '—';
		return list.map((p) => p.replace(/^(core|cloud|embedded|frontend)-/, '')).join(', ');
	}
</script>

<div class="glass-card overflow-hidden">
	<div class="flex items-center justify-between border-b px-5 py-3.5" style="border-color: var(--color-border-subtle)">
		<h3 class="text-sm font-semibold" style="color: var(--color-text)">Recent Sessions</h3>
		<a
			href="/sessions"
			class="text-xs font-medium no-underline transition-colors hover:opacity-80"
			style="color: var(--color-accent)"
		>
			View all →
		</a>
	</div>

	{#if sessions.length === 0}
		<div class="px-5 py-12 text-center">
			<p class="text-sm" style="color: var(--color-text-muted)">No sessions yet</p>
			<p class="mt-1 text-xs" style="color: var(--color-text-muted)">
				Run <code class="font-mono" style="color: var(--color-accent)">claude-kit --kit &lt;name&gt;</code> to start
			</p>
		</div>
	{:else}
		<table class="w-full text-left text-[13px]">
			<thead>
				<tr style="background: var(--color-bg-subtle); color: var(--color-text-muted)">
					<th class="px-5 py-2.5 font-medium">Session</th>
					<th class="px-5 py-2.5 font-medium">Plugins</th>
					<th class="px-5 py-2.5 font-medium text-right">Turns</th>
					<th class="px-5 py-2.5 font-medium text-right">Tokens</th>
					<th class="px-5 py-2.5 font-medium text-right">Cost</th>
					<th class="px-5 py-2.5 font-medium text-right">Duration</th>
				</tr>
			</thead>
			<tbody>
				{#each sessions as s}
					<tr class="border-t transition-colors hover:bg-white/[0.03]" style="border-color: var(--color-border-subtle)">
						<td class="px-5 py-3">
							<div class="font-mono text-xs" style="color: var(--color-text-secondary)">
								{s.session_id.slice(0, 8)}…
							</div>
							<div class="mt-0.5 text-[11px]" style="color: var(--color-text-muted)">{fmt(s.start_time)}</div>
						</td>
						<td class="max-w-[200px] truncate px-5 py-3" style="color: var(--color-text-secondary)">
							{plugins(s.plugins_loaded)}
						</td>
						<td class="px-5 py-3 text-right font-mono" style="color: var(--color-text)">{s.total_turns}</td>
						<td class="px-5 py-3 text-right font-mono" style="color: var(--color-text)">
							{tokens(s.total_tokens_in + s.total_tokens_out)}
						</td>
						<td class="px-5 py-3 text-right font-mono" style="color: var(--color-text)">{cost(s.cost_usd)}</td>
						<td class="px-5 py-3 text-right" style="color: var(--color-text-secondary)">{dur(s.duration_s)}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>
