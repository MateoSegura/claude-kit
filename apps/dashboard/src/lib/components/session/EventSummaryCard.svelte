<script lang="ts">
	import type { TelemetryEvent } from '$lib/api';
	import { countEvents, tokens } from './event-utils';

	let { events }: { events: TelemetryEvent[] } = $props();

	let counts = $derived(countEvents(events));

	// Mini sparkline: density over 30 bins
	let sparklinePath = $derived.by(() => {
		if (events.length < 2) return '';
		const bins = 30;
		const times = events.map((e) => new Date(e.timestamp).getTime());
		const min = Math.min(...times);
		const max = Math.max(...times);
		const span = max - min || 1;
		const buckets = new Array(bins).fill(0);
		for (const t of times) {
			const idx = Math.min(Math.floor(((t - min) / span) * bins), bins - 1);
			buckets[idx]++;
		}
		const maxBucket = Math.max(1, ...buckets);
		const w = 48;
		const h = 18;
		const points = buckets.map((b, i) => {
			const x = (i / (bins - 1)) * w;
			const y = h - (b / maxBucket) * (h - 2) - 1;
			return `${x.toFixed(1)},${y.toFixed(1)}`;
		});
		return `M${points.join('L')}`;
	});
</script>

<div class="flex items-center gap-3 px-2 py-1">
	<!-- Tool calls -->
	<div class="flex items-baseline gap-1.5">
		<span class="font-mono text-xs font-semibold" style="color: var(--color-aurora-violet)">{counts.tools}</span>
		<span class="text-[10px] font-medium" style="color: var(--color-text-muted)">tools</span>
	</div>

	<span style="color: var(--color-border); font-size: 14px;">|</span>

	<!-- Prompts -->
	<div class="flex items-baseline gap-1.5">
		<span class="font-mono text-xs font-semibold" style="color: var(--color-text)">{counts.prompts}</span>
		<span class="text-[10px] font-medium" style="color: var(--color-text-muted)">prompts</span>
	</div>

	{#if counts.errors > 0}
		<span style="color: var(--color-border); font-size: 14px;">|</span>
		<div class="flex items-baseline gap-1.5">
			<span class="font-mono text-xs font-semibold" style="color: var(--color-aurora-rose)">{counts.errors}</span>
			<span class="text-[10px] font-medium" style="color: var(--color-text-muted)">errors</span>
		</div>
	{/if}

	<span style="color: var(--color-border); font-size: 14px;">|</span>

	<!-- Tokens -->
	<div class="flex items-baseline gap-1.5">
		<span class="font-mono text-xs font-semibold" style="color: #34d399">{tokens(counts.tokensIn + counts.tokensOut)}</span>
		<span class="text-[10px] font-medium" style="color: var(--color-text-muted)">tokens</span>
	</div>

	{#if counts.kitEvents > 0}
		<span style="color: var(--color-border); font-size: 14px;">|</span>
		<div class="flex items-baseline gap-1.5">
			<span class="font-mono text-xs font-semibold" style="color: var(--color-aurora-teal)">{counts.kitEvents}</span>
			<span class="text-[10px] font-medium" style="color: var(--color-text-muted)">kit</span>
		</div>
	{/if}

	<!-- Mini sparkline -->
	{#if sparklinePath}
		<div class="sparkline ml-auto">
			<svg width="48" height="18" viewBox="0 0 48 18" fill="none">
				<path d={sparklinePath} stroke="var(--color-aurora-teal)" stroke-width="1.5" fill="none" opacity="0.6" />
			</svg>
		</div>
	{/if}
</div>
