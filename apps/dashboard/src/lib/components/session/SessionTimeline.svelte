<script lang="ts">
	import type { TelemetryEvent } from '$lib/api';
	import { type TimeWindow, type Interval } from './time-window.svelte';
	import { isClaudeEvent, isKitEvent, fmtTimeShort } from './event-utils';

	let {
		events,
		tw
	}: {
		events: TelemetryEvent[];
		tw: TimeWindow;
	} = $props();

	// ── Interval pills ──
	const intervals: Interval[] = ['1m', '5m', '20m', '1h', 'all'];

	function pillLabel(i: Interval): string {
		return i === 'all' ? 'All' : i.toUpperCase();
	}

	// ── Histogram buckets ──
	let bucketCount = $derived(tw.interval === '1m' ? 30 : tw.interval === '5m' ? 50 : 80);

	let buckets = $derived.by(() => {
		const start = tw.sessionStart;
		const end = tw.sessionEnd;
		const span = end - start || 1;
		const count = bucketCount;
		const b: { count: number; claudeCount: number; kitCount: number }[] = Array.from(
			{ length: count },
			() => ({ count: 0, claudeCount: 0, kitCount: 0 })
		);
		for (const e of events) {
			const t = new Date(e.timestamp).getTime();
			const idx = Math.min(Math.floor(((t - start) / span) * count), count - 1);
			if (idx >= 0) {
				b[idx].count++;
				if (isClaudeEvent(e)) b[idx].claudeCount++;
				if (isKitEvent(e)) b[idx].kitCount++;
			}
		}
		return b;
	});

	let maxCount = $derived(Math.max(1, ...buckets.map((b) => b.count)));

	// ── Selection as fraction [0..1] of full session ──
	let sessionSpan = $derived(tw.sessionEnd - tw.sessionStart || 1);
	let selStart = $derived((tw.windowStart - tw.sessionStart) / sessionSpan);
	let selEnd = $derived((tw.windowEnd - tw.sessionStart) / sessionSpan);

	// ── Drag state ──
	let dragging: 'left' | 'right' | 'body' | null = $state(null);
	let dragStartX = $state(0);
	let dragStartSelStart = $state(0);
	let dragStartSelEnd = $state(0);
	let lastDragEnd = $state(0); // timestamp of last drag end — prevents click-after-drag

	let containerEl: HTMLDivElement | undefined = $state();

	function fractionFromX(clientX: number, rect: DOMRect): number {
		return Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
	}

	function fractionToTime(f: number): number {
		return tw.sessionStart + f * sessionSpan;
	}

	function onPointerDown(e: PointerEvent, handle: 'left' | 'right' | 'body') {
		dragging = handle;
		dragStartX = e.clientX;
		dragStartSelStart = selStart;
		dragStartSelEnd = selEnd;
		(e.target as HTMLElement).setPointerCapture(e.pointerId);
	}

	function onPointerMove(e: PointerEvent) {
		if (!dragging || !containerEl) return;
		const rect = containerEl.getBoundingClientRect();
		const currentFrac = fractionFromX(e.clientX, rect);
		const deltaFrac = currentFrac - fractionFromX(dragStartX, rect);

		if (dragging === 'left') {
			const newStart = Math.max(0, Math.min(dragStartSelStart + deltaFrac, selEnd - 0.02));
			tw.setWindowFromScrubber(fractionToTime(newStart), tw.windowEnd);
		} else if (dragging === 'right') {
			const newEnd = Math.min(1, Math.max(dragStartSelEnd + deltaFrac, selStart + 0.02));
			tw.setWindowFromScrubber(tw.windowStart, fractionToTime(newEnd));
		} else if (dragging === 'body') {
			const width = dragStartSelEnd - dragStartSelStart;
			let newStart = dragStartSelStart + deltaFrac;
			let newEnd = dragStartSelEnd + deltaFrac;
			if (newStart < 0) { newStart = 0; newEnd = width; }
			if (newEnd > 1) { newEnd = 1; newStart = 1 - width; }
			tw.setWindowFromScrubber(fractionToTime(newStart), fractionToTime(newEnd));
		}
	}

	function onPointerUp() {
		if (dragging) {
			lastDragEnd = Date.now();
		}
		dragging = null;
	}

	// Click-to-jump — only fires for real clicks, not at the end of a drag
	function onBarClick(e: MouseEvent) {
		if (Date.now() - lastDragEnd < 300) return; // skip click-after-drag
		if (!containerEl) return;
		const rect = containerEl.getBoundingClientRect();
		const frac = fractionFromX(e.clientX, rect);
		const clickTime = fractionToTime(frac);
		const halfWindow = (tw.windowEnd - tw.windowStart) / 2;
		let newStart = clickTime - halfWindow;
		let newEnd = clickTime + halfWindow;
		if (newStart < tw.sessionStart) {
			newStart = tw.sessionStart;
			newEnd = tw.sessionStart + halfWindow * 2;
		}
		if (newEnd > tw.sessionEnd) {
			newEnd = tw.sessionEnd;
			newStart = tw.sessionEnd - halfWindow * 2;
		}
		newStart = Math.max(tw.sessionStart, newStart);
		tw.setWindowFromScrubber(newStart, newEnd);
	}

	// ── Tick labels ──
	let tickLabels = $derived.by(() => {
		const count = 4;
		const result: string[] = [];
		for (let i = 0; i <= count; i++) {
			const frac = i / count;
			result.push(fmtTimeShort(tw.sessionStart + frac * sessionSpan));
		}
		return result;
	});

	let isLiveEdge = $derived(tw.mode === 'live' && !tw.paused);
</script>

<div
	class="glass-card mb-4 px-3 py-2"
	bind:this={containerEl}
	onpointermove={onPointerMove}
	onpointerup={onPointerUp}
	role="slider"
	aria-label="Session timeline range selector"
	tabindex="0"
	aria-valuemin={0}
	aria-valuemax={100}
	aria-valuenow={Math.round(selStart * 100)}
>
	<!-- Row 1: Interval pills + time display -->
	<div class="mb-2 flex items-center gap-2">
		<!-- Step backward -->
		<button
			onclick={() => tw.stepBackward()}
			disabled={!tw.canStepBack}
			class="time-nav-btn"
			style="width: 24px; height: 24px; font-size: 16px;"
			aria-label="Step backward"
		>
			&#8249;
		</button>

		<!-- Interval pills -->
		<div class="flex items-center gap-0.5">
			{#each intervals as i}
				<button
					onclick={() => tw.setInterval(i)}
					class="time-pill"
					class:time-pill-active={tw.interval === i}
					style="padding: 2px 8px; font-size: 10px;"
				>
					{pillLabel(i)}
				</button>
			{/each}
		</div>

		<!-- Step forward / NOW -->
		{#if tw.mode === 'live' && tw.interval !== 'all'}
			<button
				onclick={() => { tw.paused = false; tw.tick(); }}
				class="time-nav-btn"
				style="width: 24px; height: 24px; font-size: 9px; letter-spacing: 0.05em;"
				aria-label="Jump to now"
			>
				NOW
			</button>
		{:else}
			<button
				onclick={() => tw.stepForward()}
				disabled={!tw.canStepForward}
				class="time-nav-btn"
				style="width: 24px; height: 24px; font-size: 16px;"
				aria-label="Step forward"
			>
				&#8250;
			</button>
		{/if}

		<!-- Pause (live only) -->
		{#if tw.mode === 'live'}
			<button
				onclick={() => tw.togglePause()}
				class="time-pill"
				class:time-pill-paused={tw.paused}
				style="padding: 2px 6px; font-size: 11px; min-width: 24px;"
				aria-label={tw.paused ? 'Resume' : 'Pause'}
			>
				{tw.paused ? '▶' : '⏸'}
			</button>
		{/if}

		<!-- Time display -->
		<span class="ml-auto rounded px-1.5 py-0.5 font-mono text-[10px]" style="color: var(--color-text); background: var(--color-bg-subtle);">
			{fmtTimeShort(tw.windowStart)}&ensp;–&ensp;{fmtTimeShort(tw.windowEnd)}
		</span>
	</div>

	<!-- Row 2: Histogram scrubber (compact) -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="relative" style="height: 32px; cursor: crosshair;" onclick={onBarClick}>
		<!-- Buckets -->
		<div class="absolute inset-0 flex items-end gap-px" style="pointer-events: none;">
			{#each buckets as bucket, i}
				{@const height = (bucket.count / maxCount) * 100}
				{@const claudeRatio = bucket.count > 0 ? bucket.claudeCount / bucket.count : 0.5}
				{@const isLast = i === buckets.length - 1}
				<div
					class="flex-1 rounded-t-sm"
					class:live-edge-glow={isLast && isLiveEdge}
					style="height: {height}%; background: color-mix(in srgb, #14b8a6 {claudeRatio * 100}%, #8b5cf6); opacity: 0.6;"
				></div>
			{/each}
		</div>

		<!-- Selection overlay — dim regions pass clicks through -->
		{#if events.length > 0}
			<div
				class="absolute top-0 bottom-0 left-0"
				style="width: {selStart * 100}%; background: rgba(0,0,0,0.5); pointer-events: none;"
			></div>
			<div
				class="absolute top-0 bottom-0 right-0"
				style="width: {(1 - selEnd) * 100}%; background: rgba(0,0,0,0.5); pointer-events: none;"
			></div>
			<div
				class="absolute top-0 bottom-0"
				style="left: {selStart * 100}%; width: {(selEnd - selStart) * 100}%; cursor: grab; border-top: 2px solid var(--color-accent); border-bottom: 2px solid var(--color-accent);"
				onpointerdown={(e) => onPointerDown(e, 'body')}
				role="presentation"
			></div>
			<div
				class="absolute top-0 bottom-0"
				style="left: {selStart * 100}%; width: 8px; margin-left: -4px; cursor: ew-resize;"
				onpointerdown={(e) => onPointerDown(e, 'left')}
				role="presentation"
			>
				<div class="mx-auto h-full w-0.5 rounded" style="background: var(--color-accent);"></div>
			</div>
			<div
				class="absolute top-0 bottom-0"
				style="left: {selEnd * 100}%; width: 8px; margin-left: -4px; cursor: ew-resize;"
				onpointerdown={(e) => onPointerDown(e, 'right')}
				role="presentation"
			>
				<div class="mx-auto h-full w-0.5 rounded" style="background: var(--color-accent);"></div>
			</div>
		{/if}
	</div>

	<!-- Tick labels -->
	<div class="mt-0.5 flex justify-between">
		{#each tickLabels as label}
			<span class="font-mono text-[10px]" style="color: var(--color-text-secondary)">
				{label}
			</span>
		{/each}
	</div>
</div>
