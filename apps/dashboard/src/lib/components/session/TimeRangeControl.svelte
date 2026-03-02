<script lang="ts">
	import { type TimeWindow, type Interval } from './time-window.svelte';
	import { fmtTimeShort } from './event-utils';

	let { tw }: { tw: TimeWindow } = $props();

	const intervals: Interval[] = ['1m', '5m', '20m', '1h', 'all'];

	function label(i: Interval): string {
		return i === 'all' ? 'All' : i.toUpperCase();
	}
</script>

<div class="flex items-center gap-2">
	<!-- Step backward -->
	<button
		onclick={() => tw.stepBackward()}
		disabled={!tw.canStepBack}
		class="time-nav-btn"
		aria-label="Step backward"
	>
		&#8249;
	</button>

	<!-- Interval pills -->
	<div class="flex items-center gap-1">
		{#each intervals as i}
			<button
				onclick={() => tw.setInterval(i)}
				class="time-pill"
				class:time-pill-active={tw.interval === i}
			>
				{label(i)}
			</button>
		{/each}
	</div>

	<!-- Step forward / jump to now -->
	{#if tw.mode === 'live' && tw.interval !== 'all'}
		<button
			onclick={() => { tw.paused = false; tw.tick(); }}
			class="time-nav-btn"
			aria-label="Jump to now"
			style="font-size: 10px; letter-spacing: 0.05em;"
		>
			NOW
		</button>
	{:else}
		<button
			onclick={() => tw.stepForward()}
			disabled={!tw.canStepForward}
			class="time-nav-btn"
			aria-label="Step forward"
		>
			&#8250;
		</button>
	{/if}

	<!-- Pause button (live mode only) -->
	{#if tw.mode === 'live'}
		<button
			onclick={() => tw.togglePause()}
			class="time-pill"
			class:time-pill-paused={tw.paused}
			aria-label={tw.paused ? 'Resume' : 'Pause'}
			style="font-size: 12px; min-width: 30px;"
		>
			{tw.paused ? '▶' : '⏸'}
		</button>
	{/if}

	<!-- Time display — separator + readable color -->
	<span class="ml-1 rounded-md px-2 py-1 font-mono text-[11px]" style="color: var(--color-text); background: var(--color-bg-subtle);">
		{fmtTimeShort(tw.windowStart)}&ensp;–&ensp;{fmtTimeShort(tw.windowEnd)}
	</span>
</div>
