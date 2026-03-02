<script lang="ts">
	import type { TelemetryEvent } from '$lib/api';
	import { type TimeWindow } from './time-window.svelte';
	import { fmtTime, fmtTimeShort, payloadPreview } from './event-utils';

	let {
		events,
		tw
	}: {
		events: TelemetryEvent[];
		tw: TimeWindow;
	} = $props();

	// ── Track definitions ──
	interface Track {
		key: string;
		label: string;
		shortLabel: string;
		color: string;
		match: (t: string) => boolean;
	}

	const CONV_TRACKS: Track[] = [
		{ key: 'prompt',  label: 'Prompts',   shortLabel: 'PRMT', color: '#e2e8f0', match: (t) => t === 'prompt.submitted' },
		{ key: 'message', label: 'Messages',  shortLabel: 'MSG',  color: '#60a5fa', match: (t) => t.startsWith('message.') },
		{ key: 'tool',    label: 'Tool calls', shortLabel: 'TOOL', color: '#8b5cf6', match: (t) => t === 'tool.used' || t === 'tool.result' },
		{ key: 'turn',    label: 'Turns',     shortLabel: 'TURN', color: '#34d399', match: (t) => t === 'turn.completed' },
	];

	const KIT_TRACKS: Track[] = [
		{ key: 'route',   label: 'Router',       shortLabel: 'ROUTE', color: '#fbbf24', match: (t) => t === 'skill.invoked' || t.startsWith('autorouter.') || t === 'validation.result' },
		{ key: 'agent',   label: 'Agents',       shortLabel: 'AGENT', color: '#a78bfa', match: (t) => t === 'subagent.start' || t === 'subagent.stop' },
		{ key: 'hooks',   label: 'Hooks',        shortLabel: 'HOOKS', color: '#f97316', match: (t) => t === 'hook.fired' },
		{ key: 'load',    label: 'Plugins',      shortLabel: 'LOAD',  color: '#64748b', match: (t) => t === 'plugin.loaded' },
		{ key: 'error',   label: 'Errors',       shortLabel: 'ERR',   color: '#f43f5e', match: (t) => t === 'session.error' },
	];

	const ALL_TRACKS = [...CONV_TRACKS, ...KIT_TRACKS];

	const TRACK_HEIGHT = 24;
	const BLOCK_HEIGHT = 16;
	const LABEL_WIDTH = 56;

	let enabledTracks: Record<string, boolean> = $state(
		Object.fromEntries(ALL_TRACKS.map((t) => [t.key, true]))
	);

	function toggleTrack(key: string) {
		enabledTracks = { ...enabledTracks, [key]: !enabledTracks[key] };
	}

	function isErrorEvent(ev: TelemetryEvent): boolean {
		if (ev.event_type === 'session.error') return true;
		if (ev.payload?.is_error) return true;
		if (ev.event_type === 'tool.used' && ev.payload?.error) return true;
		return false;
	}

	function trackForEvent(ev: TelemetryEvent): string | null {
		if (isErrorEvent(ev)) return 'error';
		if (ev.event_type === 'tool.used' || ev.event_type === 'tool.result') {
			const toolName = (ev.payload?.tool_name as string) ?? (ev.payload?.name as string) ?? '';
			if (toolName === 'Skill') return 'route';
			if (toolName === 'Agent') return 'agent';
		}
		for (const track of ALL_TRACKS) {
			if (track.match(ev.event_type)) return track.key;
		}
		return null;
	}

	function colorForEvent(ev: TelemetryEvent): string {
		if (isErrorEvent(ev)) return '#f43f5e';
		if (ev.event_type === 'tool.used' || ev.event_type === 'tool.result') {
			const toolName = (ev.payload?.tool_name as string) ?? (ev.payload?.name as string) ?? '';
			if (toolName === 'Skill') return '#fbbf24';
			if (toolName === 'Agent') return '#a78bfa';
		}
		for (const track of ALL_TRACKS) {
			if (track.match(ev.event_type)) return track.color;
		}
		return '#4a5568';
	}

	function categoryLabel(eventType: string): string {
		for (const track of ALL_TRACKS) {
			if (track.match(eventType)) return track.label;
		}
		return eventType;
	}

	// ── Filter + paginate ──
	let filteredEvents = $derived(
		events.filter((e) => {
			const t = trackForEvent(e);
			return t !== null && enabledTracks[t];
		})
	);

	const PAGE_SIZE = 40;
	let pageOffset = $state(0);

	$effect(() => {
		filteredEvents.length;
		pageOffset = 0;
	});

	let canPageBack = $derived(pageOffset > 0);
	let canPageForward = $derived(pageOffset + PAGE_SIZE < filteredEvents.length);
	let visibleSlice = $derived(filteredEvents.slice(pageOffset, pageOffset + PAGE_SIZE));

	function pageBack() {
		pageOffset = Math.max(0, pageOffset - PAGE_SIZE);
		selectedEventId = null;
	}

	function pageForward() {
		if (pageOffset + PAGE_SIZE < filteredEvents.length) {
			pageOffset += PAGE_SIZE;
			selectedEventId = null;
		}
	}

	// ── Time range ──
	let displayRange = $derived.by(() => {
		if (visibleSlice.length === 0) return { start: tw.windowStart, end: tw.windowEnd };
		const times = visibleSlice.map((e) => new Date(e.timestamp).getTime());
		const start = Math.min(...times);
		const end = Math.max(...times);
		const span = end - start || 1000;
		return { start: start - span * 0.03, end: end + span * 0.03 };
	});

	function xPercent(timestamp: string): number {
		const t = new Date(timestamp).getTime();
		const { start, end } = displayRange;
		const span = end - start || 1;
		return ((t - start) / span) * 100;
	}

	let blockWidthPct = $derived.by(() => {
		if (visibleSlice.length <= 1) return 3;
		return Math.max(0.8, Math.min(4, 80 / visibleSlice.length));
	});

	// ── Clustering ──
	interface EventCluster {
		events: TelemetryEvent[];
		xPct: number;
		widthPct: number;
		trackKey: string;
	}

	function buildClusters(evts: TelemetryEvent[], trackKeys: Set<string>): EventCluster[] {
		const MERGE_THRESHOLD = blockWidthPct * 0.8;
		const byTrack = new Map<string, TelemetryEvent[]>();

		for (const ev of evts) {
			const t = trackForEvent(ev);
			if (t === null || !trackKeys.has(t)) continue;
			if (!byTrack.has(t)) byTrack.set(t, []);
			byTrack.get(t)!.push(ev);
		}

		const result: EventCluster[] = [];
		for (const [trackKey, trackEvents] of byTrack) {
			const sorted = [...trackEvents].sort(
				(a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
			);
			let current: TelemetryEvent[] = [sorted[0]];
			let currentX = xPercent(sorted[0].timestamp);

			for (let i = 1; i < sorted.length; i++) {
				const evX = xPercent(sorted[i].timestamp);
				const lastX = xPercent(current[current.length - 1].timestamp);
				if (evX - lastX < MERGE_THRESHOLD) {
					current.push(sorted[i]);
				} else {
					result.push({
						events: current,
						xPct: currentX,
						widthPct: current.length === 1 ? blockWidthPct : Math.max(blockWidthPct, xPercent(current[current.length - 1].timestamp) - currentX + blockWidthPct * 0.5),
						trackKey
					});
					current = [sorted[i]];
					currentX = evX;
				}
			}
			if (current.length > 0) {
				result.push({
					events: current,
					xPct: currentX,
					widthPct: current.length === 1 ? blockWidthPct : Math.max(blockWidthPct, xPercent(current[current.length - 1].timestamp) - currentX + blockWidthPct * 0.5),
					trackKey
				});
			}
		}
		return result;
	}

	const CONV_KEYS = new Set(CONV_TRACKS.map((t) => t.key));
	const KIT_KEYS = new Set(KIT_TRACKS.map((t) => t.key));

	let convClusters = $derived(buildClusters(visibleSlice, CONV_KEYS));
	let kitClusters = $derived(buildClusters(visibleSlice, KIT_KEYS));

	// ── Kit summary stats ──
	let kitStats = $derived.by(() => {
		let plugins = 0, routed = 0, agents = 0, hooks = 0, errors = 0;
		for (const ev of events) {
			if (ev.event_type === 'plugin.loaded') plugins++;
			else if (ev.event_type === 'skill.invoked' || ev.event_type.startsWith('autorouter.')) routed++;
			else if (ev.event_type === 'hook.fired') hooks++;
			else if (ev.event_type === 'subagent.start') agents++;
			else if (ev.event_type === 'session.error') errors++;
			else if (ev.event_type === 'tool.used') {
				const name = (ev.payload?.tool_name as string) ?? (ev.payload?.name as string) ?? '';
				if (name === 'Skill') routed++;
				else if (name === 'Agent') agents++;
			}
		}
		return { plugins, routed, agents, hooks, errors };
	});

	let kitHasData = $derived(
		kitStats.plugins > 0 || kitStats.routed > 0 || kitStats.agents > 0 || kitStats.hooks > 0
	);

	// ── Selection ──
	let selectedEventId: string | null = $state(null);
	let selectedCluster: EventCluster | null = $state(null);
	let selectedEvent = $derived(
		selectedEventId ? visibleSlice.find((e) => e.id === selectedEventId) ?? null : null
	);

	let hoveredCluster: { cluster: EventCluster; x: number; y: number } | null = $state(null);

	function showClusterPopover(cluster: EventCluster, e: MouseEvent) {
		if (cluster.events.length > 1) hoveredCluster = { cluster, x: e.clientX, y: e.clientY };
	}
	function hideClusterPopover() { hoveredCluster = null; }

	function onBlockClick(ev: TelemetryEvent) {
		selectedCluster = null;
		selectedEventId = selectedEventId === ev.id ? null : ev.id;
	}
	function onClusterClick(cluster: EventCluster) {
		selectedEventId = null;
		selectedCluster = selectedCluster === cluster ? null : cluster;
	}
	function selectClusterEvent(ev: TelemetryEvent) { selectedEventId = ev.id; }

	let tooltip: { event: TelemetryEvent; x: number; y: number } | null = $state(null);
	function showTooltip(event: TelemetryEvent, e: MouseEvent) { tooltip = { event, x: e.clientX, y: e.clientY }; }
	function hideTooltip() { tooltip = null; }

	function formatValue(value: unknown, depth = 0): string {
		if (value === null || value === undefined) return 'null';
		if (typeof value === 'string') return value.length > 200 ? value.slice(0, 197) + '...' : value;
		if (typeof value === 'number' || typeof value === 'boolean') return String(value);
		if (Array.isArray(value)) {
			if (depth > 1) return `[${value.length} items]`;
			return `[${value.map((v) => formatValue(v, depth + 1)).join(', ')}]`;
		}
		if (typeof value === 'object') {
			if (depth > 1) return '{...}';
			return Object.entries(value as Record<string, unknown>)
				.map(([k, v]) => `${k}: ${formatValue(v, depth + 1)}`)
				.join(', ');
		}
		return String(value);
	}

	let tickLabels = $derived.by(() => {
		const { start, end } = displayRange;
		const span = end - start;
		const count = Math.min(5, visibleSlice.length > 1 ? 5 : 1);
		const result: string[] = [];
		for (let i = 0; i <= count; i++) result.push(fmtTimeShort(start + (i / count) * span));
		return result;
	});

	function eventDetailLabel(ev: TelemetryEvent): string {
		const toolName = (ev.payload?.tool_name as string) ?? (ev.payload?.name as string) ?? '';
		if (ev.event_type === 'tool.used' && toolName === 'Skill') return 'Auto-routed';
		if (ev.event_type === 'tool.used' && toolName === 'Agent') return 'Agent spawn';
		return categoryLabel(ev.event_type);
	}
</script>

<!-- ═══════════ Card 1: Session Conversation ═══════════ -->
<div class="glass-card p-4">
	<div class="mb-3 flex items-center justify-between">
		<span class="font-mono text-[11px] font-bold tracking-wide" style="color: var(--color-text-secondary)">
			Conversation
		</span>
		<div class="flex gap-3">
			{#each CONV_TRACKS as track}
				<label class="flex cursor-pointer items-center gap-1 select-none">
					<input type="checkbox" checked={enabledTracks[track.key]} onchange={() => toggleTrack(track.key)} class="sr-only" />
					<span class="inline-block rounded-sm" style="width: 10px; height: 10px; border: 2px solid {track.color}; background: {enabledTracks[track.key] ? track.color : 'transparent'}; transition: background 0.15s;"></span>
					<span class="text-[10px]" style="color: {enabledTracks[track.key] ? 'var(--color-text-secondary)' : 'var(--color-text-muted)'}">{track.label}</span>
				</label>
			{/each}
		</div>
	</div>

	{@render trackLanes(CONV_TRACKS, convClusters)}

	<!-- Time axis -->
	{#if visibleSlice.length > 0}
		<div class="flex" style="border-top: 1px solid var(--color-border-subtle); padding-top: 3px; margin-top: 4px;">
			<div style="width: {LABEL_WIDTH}px;" class="shrink-0"></div>
			<div class="flex flex-1 justify-between">
				{#each tickLabels as label}
					<span class="font-mono text-[9px]" style="color: var(--color-text-secondary)">{label}</span>
				{/each}
			</div>
		</div>
	{/if}
</div>

<!-- ═══════════ Card 2: Kit Orchestration ═══════════ -->
<div class="glass-card p-4 mt-3" style="border-left: 2px solid #f97316;">
	<div class="mb-3 flex items-center justify-between">
		<div class="flex items-center gap-3">
			<span class="font-mono text-[11px] font-bold tracking-wide" style="color: #f97316">
				claude-kit
			</span>
			<!-- Kit value badges -->
			<div class="flex items-center gap-2">
				{#if kitStats.plugins > 0}
					<span class="rounded-full px-2 py-0.5 font-mono text-[9px] font-semibold" style="background: rgba(249,115,22,0.12); color: #f97316;">
						{kitStats.plugins} plugins
					</span>
				{/if}
				{#if kitStats.routed > 0}
					<span class="rounded-full px-2 py-0.5 font-mono text-[9px] font-semibold" style="background: rgba(251,191,36,0.12); color: #fbbf24;">
						{kitStats.routed} routed
					</span>
				{/if}
				{#if kitStats.agents > 0}
					<span class="rounded-full px-2 py-0.5 font-mono text-[9px] font-semibold" style="background: rgba(167,139,250,0.12); color: #a78bfa;">
						{kitStats.agents} agents
					</span>
				{/if}
				{#if kitStats.hooks > 0}
					<span class="rounded-full px-2 py-0.5 font-mono text-[9px] font-semibold" style="background: rgba(249,115,22,0.12); color: #f97316;">
						{kitStats.hooks} hooks
					</span>
				{/if}
				{#if kitStats.errors > 0}
					<span class="rounded-full px-2 py-0.5 font-mono text-[9px] font-semibold" style="background: rgba(244,63,94,0.12); color: #f43f5e;">
						{kitStats.errors} errors
					</span>
				{/if}
				{#if !kitHasData}
					<span class="font-mono text-[9px]" style="color: var(--color-text-muted)">no kit activity</span>
				{/if}
			</div>
		</div>
		<div class="flex gap-3">
			{#each KIT_TRACKS as track}
				<label class="flex cursor-pointer items-center gap-1 select-none">
					<input type="checkbox" checked={enabledTracks[track.key]} onchange={() => toggleTrack(track.key)} class="sr-only" />
					<span class="inline-block rounded-sm" style="width: 10px; height: 10px; border: 2px solid {track.color}; background: {enabledTracks[track.key] ? track.color : 'transparent'}; transition: background 0.15s;"></span>
					<span class="text-[10px]" style="color: {enabledTracks[track.key] ? 'var(--color-text-secondary)' : 'var(--color-text-muted)'}">{track.label}</span>
				</label>
			{/each}
		</div>
	</div>

	{@render trackLanes(KIT_TRACKS, kitClusters)}

	<!-- Shared time axis -->
	{#if visibleSlice.length > 0}
		<div class="flex" style="border-top: 1px solid var(--color-border-subtle); padding-top: 3px; margin-top: 4px;">
			<div style="width: {LABEL_WIDTH}px;" class="shrink-0"></div>
			<div class="flex flex-1 justify-between">
				{#each tickLabels as label}
					<span class="font-mono text-[9px]" style="color: var(--color-text-secondary)">{label}</span>
				{/each}
			</div>
		</div>
	{/if}
</div>

<!-- ═══════════ Shared pagination ═══════════ -->
{#if filteredEvents.length > PAGE_SIZE}
	<div class="mt-2 flex items-center justify-center gap-3">
		<button onclick={pageBack} disabled={!canPageBack} class="time-nav-btn" style="width: 24px; height: 24px; font-size: 14px;" aria-label="Previous page">&#8249;</button>
		<span class="font-mono text-[11px]" style="color: var(--color-text-secondary)">
			{pageOffset + 1}–{Math.min(pageOffset + PAGE_SIZE, filteredEvents.length)} of {filteredEvents.length}
		</span>
		<button onclick={pageForward} disabled={!canPageForward} class="time-nav-btn" style="width: 24px; height: 24px; font-size: 14px;" aria-label="Next page">&#8250;</button>
	</div>
{/if}

<!-- ═══════════ Detail panels ═══════════ -->

<!-- Cluster event list -->
{#if selectedCluster && !selectedEventId}
	<div class="glass-card mt-3 p-0 overflow-hidden">
		<div class="flex items-center gap-2 px-3 py-2" style="border-bottom: 1px solid var(--color-border-subtle);">
			<span class="font-mono text-[11px] font-bold" style="color: {colorForEvent(selectedCluster.events[0])}">
				{selectedCluster.events.length} grouped events
			</span>
			<span class="text-[10px]" style="color: var(--color-text-muted)">
				{fmtTimeShort(new Date(selectedCluster.events[0].timestamp).getTime())} – {fmtTimeShort(new Date(selectedCluster.events[selectedCluster.events.length - 1].timestamp).getTime())}
			</span>
			<button onclick={() => { selectedCluster = null; }} class="ml-auto cursor-pointer rounded px-2 py-0.5 text-[11px] font-medium" style="color: var(--color-text-muted); background: transparent;">✕</button>
		</div>
		<div class="p-2" style="max-height: 200px; overflow-y: auto;">
			{#each selectedCluster.events as ev}
				<button
					class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left transition-colors"
					style="background: transparent; border: none; cursor: pointer;"
					onmouseenter={(e) => (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)'}
					onmouseleave={(e) => (e.currentTarget as HTMLElement).style.background = 'transparent'}
					onclick={() => selectClusterEvent(ev)}
				>
					<span class="shrink-0 font-mono text-[10px]" style="color: var(--color-text-secondary); min-width: 72px;">{fmtTimeShort(new Date(ev.timestamp).getTime())}</span>
					<span class="shrink-0 rounded px-1 py-0.5 font-mono text-[9px] font-semibold" style="background: color-mix(in srgb, {colorForEvent(ev)} 15%, transparent); color: {colorForEvent(ev)}">{ev.event_type}</span>
					<span class="truncate font-mono text-[10px]" style="color: var(--color-text-muted)">{payloadPreview(ev.payload)}</span>
				</button>
			{/each}
		</div>
	</div>
{/if}

<!-- Single event detail -->
{#if selectedEvent}
	<div class="glass-card mt-3 p-0 overflow-hidden">
		<div class="flex items-center gap-2 px-3 py-2" style="border-bottom: 1px solid var(--color-border-subtle);">
			<span class="inline-block shrink-0 rounded px-1.5 py-0.5 font-mono text-[11px] font-semibold" style="background: color-mix(in srgb, {colorForEvent(selectedEvent)} 15%, transparent); color: {colorForEvent(selectedEvent)}">{selectedEvent.event_type}</span>
			<span class="font-mono text-[11px]" style="color: var(--color-text-secondary)">{fmtTime(selectedEvent.timestamp)}</span>
			<span class="ml-auto text-[10px]" style="color: var(--color-text-muted)">{eventDetailLabel(selectedEvent)}</span>
			<button onclick={() => { selectedEventId = null; }} class="cursor-pointer rounded px-2 py-0.5 text-[11px] font-medium" style="color: var(--color-text-muted); background: transparent;">{selectedCluster ? '← Back' : '✕'}</button>
		</div>
		<div class="p-3">
			<div class="mb-3 grid grid-cols-2 gap-3">
				<div>
					<div class="text-[9px] font-semibold uppercase tracking-wider" style="color: var(--color-text-muted)">Event ID</div>
					<div class="mt-0.5 font-mono text-[11px]" style="color: var(--color-text-secondary)">{selectedEvent.id}</div>
				</div>
				<div>
					<div class="text-[9px] font-semibold uppercase tracking-wider" style="color: var(--color-text-muted)">Timestamp</div>
					<div class="mt-0.5 font-mono text-[11px]" style="color: var(--color-text-secondary)">{selectedEvent.timestamp}</div>
				</div>
			</div>
			{#if Object.keys(selectedEvent.payload).length > 0}
				<div class="text-[9px] font-semibold uppercase tracking-wider mb-2" style="color: var(--color-text-muted)">Payload</div>
				<div class="rounded-md p-2.5" style="background: rgba(0,0,0,0.2); border: 1px solid var(--color-border-subtle);">
					<div class="grid gap-1.5">
						{#each Object.entries(selectedEvent.payload) as [key, value]}
							<div class="flex gap-2">
								<span class="shrink-0 font-mono text-[11px] font-semibold" style="color: var(--color-accent); min-width: 80px;">{key}</span>
								<span class="font-mono text-[11px] break-all" style="color: var(--color-text-secondary)">{formatValue(value)}</span>
							</div>
						{/each}
					</div>
				</div>
			{:else}
				<div class="text-[11px]" style="color: var(--color-text-muted)">No payload data</div>
			{/if}
		</div>
	</div>
{/if}

<!-- ═══════════ Tooltips ═══════════ -->

{#if tooltip && !selectedEventId}
	<div class="glass-card fixed z-50 px-3 py-2" style="left: {tooltip.x + 12}px; top: {tooltip.y - 10}px; pointer-events: none; min-width: 180px; max-width: 320px;">
		<div class="mb-1 flex items-center gap-2">
			<span class="inline-block rounded px-1.5 py-0.5 font-mono text-[10px] font-semibold" style="background: color-mix(in srgb, {colorForEvent(tooltip.event)} 15%, transparent); color: {colorForEvent(tooltip.event)}">{tooltip.event.event_type}</span>
			<span class="font-mono text-[11px]" style="color: var(--color-text-secondary)">{fmtTime(tooltip.event.timestamp)}</span>
		</div>
		{#if Object.keys(tooltip.event.payload).length > 0}
			<div class="truncate font-mono text-[10px]" style="color: var(--color-text-muted); max-width: 280px;">{payloadPreview(tooltip.event.payload)}</div>
		{/if}
		<div class="mt-1 text-[9px]" style="color: var(--color-text-muted)">Click to inspect</div>
	</div>
{/if}

{#if hoveredCluster && !selectedEventId}
	<div class="glass-card fixed z-50 px-3 py-2" style="left: {hoveredCluster.x + 12}px; top: {hoveredCluster.y - 10}px; pointer-events: none; min-width: 200px; max-width: 360px;">
		<div class="mb-1.5 flex items-center gap-2">
			<span class="font-mono text-[10px] font-bold" style="color: {colorForEvent(hoveredCluster.cluster.events[0])}">{hoveredCluster.cluster.events.length} events</span>
			<span class="text-[9px]" style="color: var(--color-text-muted)">grouped</span>
		</div>
		<div class="flex flex-col gap-1" style="max-height: 160px; overflow-y: auto;">
			{#each hoveredCluster.cluster.events.slice(0, 8) as ev}
				<div class="flex items-center gap-2">
					<span class="font-mono text-[9px]" style="color: var(--color-text-secondary)">{fmtTimeShort(new Date(ev.timestamp).getTime())}</span>
					<span class="truncate font-mono text-[10px]" style="color: var(--color-text-muted); max-width: 200px;">{ev.event_type}{Object.keys(ev.payload).length > 0 ? ' — ' + payloadPreview(ev.payload) : ''}</span>
				</div>
			{/each}
			{#if hoveredCluster.cluster.events.length > 8}
				<span class="text-[9px]" style="color: var(--color-text-muted)">+{hoveredCluster.cluster.events.length - 8} more</span>
			{/if}
		</div>
		<div class="mt-1 text-[9px]" style="color: var(--color-text-muted)">Click to expand</div>
	</div>
{/if}

<!-- ═══════════ Shared render snippet ═══════════ -->

{#snippet trackLanes(tracks: Track[], cls: EventCluster[])}
	{@const activeTracks = tracks.filter((t) => enabledTracks[t.key])}
	<div class="flex" style="min-height: {activeTracks.length * TRACK_HEIGHT + 4}px;">
		<!-- Labels -->
		<div class="shrink-0 flex flex-col" style="width: {LABEL_WIDTH}px;">
			{#each activeTracks as track}
				<div class="flex items-center" style="height: {TRACK_HEIGHT}px;">
					<span class="font-mono text-[10px] font-bold tracking-wide" style="color: {track.color}; opacity: 0.8;">{track.shortLabel}</span>
				</div>
			{/each}
		</div>
		<!-- Lanes -->
		<div class="relative flex-1" style="min-height: {activeTracks.length * TRACK_HEIGHT}px;">
			{#each activeTracks as track, i}
				<div class="absolute left-0 right-0" style="top: {i * TRACK_HEIGHT}px; height: {TRACK_HEIGHT}px; background: {i % 2 === 0 ? 'rgba(255,255,255,0.015)' : 'transparent'}; border-bottom: 1px solid rgba(255,255,255,0.03);"></div>
			{/each}
			{#each cls as cluster}
				{@const trackIndex = activeTracks.findIndex((t) => t.key === cluster.trackKey)}
				{@const isSingle = cluster.events.length === 1}
				{@const firstEv = cluster.events[0]}
				{@const isSelected = isSingle && selectedEventId === firstEv.id}
				{#if trackIndex >= 0}
					<div
						class="absolute rounded-sm"
						style="left: {cluster.xPct}%; top: {trackIndex * TRACK_HEIGHT + (TRACK_HEIGHT - BLOCK_HEIGHT) / 2}px; width: {cluster.widthPct}%; height: {BLOCK_HEIGHT}px; background: {colorForEvent(firstEv)}; opacity: {isSelected ? 1 : 0.7}; cursor: pointer; outline: {isSelected ? '2px solid var(--color-text)' : 'none'}; outline-offset: 1px; transition: opacity 0.1s; z-index: {isSelected ? 10 : 1};"
						onmouseenter={(e) => { if (isSingle) showTooltip(firstEv, e); else showClusterPopover(cluster, e); }}
						onmouseleave={() => { hideTooltip(); hideClusterPopover(); }}
						onclick={() => { if (isSingle) onBlockClick(firstEv); else onClusterClick(cluster); }}
						onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); if (isSingle) onBlockClick(firstEv); else onClusterClick(cluster); } }}
						role="button"
						tabindex="0"
						aria-label="{isSingle ? firstEv.event_type : cluster.events.length + ' events'} at {fmtTime(firstEv.timestamp)}"
					>
						{#if !isSingle}
							<span class="absolute -top-1.5 -right-1.5 flex items-center justify-center rounded-full font-mono text-[8px] font-bold" style="width: 14px; height: 14px; background: var(--color-bg); color: {colorForEvent(firstEv)}; border: 1px solid {colorForEvent(firstEv)}; z-index: 2;">{cluster.events.length}</span>
						{/if}
					</div>
				{/if}
			{/each}
			{#if activeTracks.length > 0 && cls.length === 0}
				<div class="absolute inset-0 flex items-center justify-center text-[11px]" style="color: var(--color-text-muted)">No events in window</div>
			{/if}
		</div>
	</div>
{/snippet}
