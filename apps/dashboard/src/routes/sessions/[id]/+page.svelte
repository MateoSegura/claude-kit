<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { fly } from 'svelte/transition';
	import {
		getSession,
		getSessionEventsStream,
		type SessionSummary,
		type TelemetryEvent
	} from '$lib/api';
	import { fmtDate, dur, tokens } from '$lib/components/session/event-utils';
	import { createTimeWindow } from '$lib/components/session/time-window.svelte';
	import ViewSelector from '$lib/components/session/ViewSelector.svelte';
	import EventSummaryCard from '$lib/components/session/EventSummaryCard.svelte';
	import SessionTimeline from '$lib/components/session/SessionTimeline.svelte';
	import ChatView from '$lib/components/session/ChatView.svelte';
	import SwimLaneTimeline from '$lib/components/session/SwimLaneTimeline.svelte';

	let sessionId = $derived($page.params.id ?? '');
	let session: (SessionSummary & { event_count: number }) | null = $state(null);
	let events: TelemetryEvent[] = $state([]);
	let loading = $state(true);
	let error = $state('');
	let pollTimer: ReturnType<typeof setInterval> | null = $state(null);
	let activeView: 'chat' | 'timeline' = $state('chat');
	let lastEventTimestamp: string | undefined = $state(undefined);

	const tw = createTimeWindow();

	let visibleEvents = $derived(
		events.filter((e) => {
			const t = new Date(e.timestamp).getTime();
			return t >= tw.windowStart && t <= tw.windowEnd;
		})
	);

	async function loadSession() {
		try {
			session = await getSession(sessionId);
		} catch {
			// session summary errors handled by initial load
		}
	}

	async function loadEvents(initial = false) {
		try {
			const resp = await getSessionEventsStream(sessionId, lastEventTimestamp);
			if (resp.events.length > 0) {
				if (initial) {
					events = resp.events;
				} else {
					const existingIds = new Set(events.map((e) => e.id));
					const newEvents = resp.events.filter((e) => !existingIds.has(e.id));
					if (newEvents.length > 0) {
						events = [...events, ...newEvents];
					}
				}
				lastEventTimestamp = events[events.length - 1].timestamp;
			}
		} catch (e) {
			if (initial) {
				const msg = e instanceof Error ? e.message : String(e);
				error = msg || 'Failed to load events';
			}
		}
	}

	function initSessionBounds() {
		if (!session) return;
		if (session.end_time === null) {
			tw.setSessionBounds(new Date(session.start_time).getTime(), Date.now());
			tw.mode = 'live';
		} else {
			tw.setSessionBounds(
				new Date(session.start_time).getTime(),
				new Date(session.end_time).getTime()
			);
			tw.mode = 'history';
		}
	}

	async function initialLoad() {
		loading = true;
		try {
			await Promise.all([loadSession(), loadEvents(true)]);
			initSessionBounds();
			error = '';
		} catch (e) {
			const msg = e instanceof Error ? e.message : String(e);
			error = msg || 'Failed to load session';
		} finally {
			loading = false;
		}
	}

	async function poll() {
		await Promise.all([loadSession(), loadEvents(false)]);
		if (session) {
			if (session.end_time !== null) {
				tw.mode = 'history';
				tw.setSessionBounds(
					new Date(session.start_time).getTime(),
					new Date(session.end_time).getTime()
				);
			} else {
				tw.tick();
			}
		}
	}

	onMount(() => {
		initialLoad();
		pollTimer = setInterval(poll, 1000);
	});

	onDestroy(() => {
		if (pollTimer) clearInterval(pollTimer);
	});
</script>

<svelte:head>
	<title>Session {sessionId.slice(0, 8)} — claude-kit</title>
</svelte:head>

<!-- Back link -->
<a
	href="/sessions"
	class="mb-3 inline-flex items-center gap-1 text-xs font-medium no-underline transition-colors hover:opacity-70"
	style="color: var(--color-accent)"
>
	← Sessions
</a>

{#if loading && !session}
	<div class="flex items-center justify-center py-20">
		<div class="text-sm tracking-wide animate-pulse" style="color: var(--color-text-muted)">
			Loading session…
		</div>
	</div>
{:else if error}
	<div
		class="rounded-lg px-4 py-3 text-sm"
		style="background: var(--color-error-light); color: var(--color-error)"
	>
		{error}
	</div>
{:else if session}
	<!-- Header row: session ID + badge + compact stats -->
	<div class="mb-3 flex flex-wrap items-center gap-3">
		<h1 class="font-mono text-base font-semibold" style="color: var(--color-text)">
			{session.session_id.slice(0, 8)}
		</h1>
		{#if session.end_time === null}
			<span
				class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium"
				style="background: var(--color-success-light); color: var(--color-success)"
			>
				<span class="live-dot"></span>
				live
			</span>
		{:else}
			<span
				class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium"
				style="background: var(--color-bg-subtle); color: var(--color-text-muted)"
			>
				ended
			</span>
		{/if}
		<!-- Inline compact stats -->
		<div class="ml-auto flex items-center gap-3 font-mono text-[10px]" style="color: var(--color-text-secondary)">
			<span>{dur(session.duration_s)}</span>
			<span>{session.total_turns} turns</span>
			<span>{tokens(session.total_tokens_in)} in / {tokens(session.total_tokens_out)} out</span>
			{#if session.cost_usd != null}
				<span>${session.cost_usd.toFixed(3)}</span>
			{/if}
			<span>{session.model ?? ''}</span>
		</div>
	</div>

	<!-- Time controls + histogram scrubber — unified top bar -->
	<SessionTimeline {events} {tw} />

	<!-- Compact info row: plugins + windowed summary side by side -->
	<div class="mb-4 flex flex-wrap items-start gap-4">
		<!-- Plugins (compact inline) -->
		<div class="flex items-center gap-1.5 flex-wrap">
			<span class="text-[9px] font-semibold uppercase tracking-wider" style="color: var(--color-text-muted)">Plugins</span>
			{#each session.plugins_loaded as p}
				<span
					class="inline-block rounded px-1.5 py-0.5 text-[10px] font-medium"
					style="background: {p.startsWith('core-') ? 'var(--color-bg-subtle)' : 'var(--color-accent-light)'}; color: {p.startsWith('core-') ? 'var(--color-text-secondary)' : 'var(--color-accent)'}"
				>
					{p}
				</span>
			{/each}
		</div>

		<!-- Windowed event summary -->
		<div class="ml-auto">
			<EventSummaryCard events={visibleEvents} />
		</div>
	</div>

	<!-- View selector + event count -->
	<div class="mb-3 flex items-center justify-between">
		<ViewSelector {activeView} onViewChange={(v: 'chat' | 'timeline') => activeView = v} />
		<span class="text-[11px] font-mono" style="color: var(--color-text-muted)">
			{visibleEvents.length} of {events.length} events
		</span>
	</div>

	<!-- Active view -->
	{#if activeView === 'chat'}
		<ChatView events={visibleEvents} {sessionId} isLive={session?.end_time === null} />
	{:else}
		<SwimLaneTimeline events={visibleEvents} {tw} />
	{/if}
{/if}
