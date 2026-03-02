<script lang="ts">
	import { onMount } from 'svelte';
	import { fly, fade } from 'svelte/transition';
	import {
		getMetricsSummary,
		getSessions,
		getTokenUsage,
		getCostOverTime,
		type MetricsSummary,
		type SessionListResponse,
		type TokenBucket,
		type CostBucket
	} from '$lib/api';
	import MetricCard from '$lib/components/MetricCard.svelte';
	import SessionTable from '$lib/components/SessionTable.svelte';
	import TokenChart from '$lib/components/TokenChart.svelte';
	import CostChart from '$lib/components/CostChart.svelte';
	import SkillsChart from '$lib/components/SkillsChart.svelte';

	let metrics: MetricsSummary | null = $state(null);
	let sessions: SessionListResponse | null = $state(null);
	let tokenBuckets: TokenBucket[] = $state([]);
	let costBuckets: CostBucket[] = $state([]);
	let loading = $state(true);
	let error = $state('');

	function fmtTokens(n: number): string {
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
		if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
		return String(n);
	}

	function fmtCost(n: number): string {
		if (n === 0) return '$0.00';
		return `$${n.toFixed(2)}`;
	}

	function fmtDuration(s: number): string {
		if (!s) return '—';
		if (s < 60) return `${Math.round(s)}s`;
		return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
	}

	function fmtRate(n: number): string {
		return `${(n * 100).toFixed(0)}%`;
	}

	function buildMetricCards(m: MetricsSummary) {
		return [
			{
				label: 'Sessions',
				value: String(m.total_sessions),
				detail: 'this week',
				icon: '◎'
			},
			{
				label: 'Total Tokens',
				value: fmtTokens(m.total_tokens_in + m.total_tokens_out),
				detail: `${fmtTokens(m.total_tokens_in)} in / ${fmtTokens(m.total_tokens_out)} out`,
				icon: '⟡'
			},
			{
				label: 'Cost',
				value: fmtCost(m.total_cost_usd),
				detail: 'estimated this week',
				icon: '◆'
			},
			{
				label: 'Autorouter',
				value: fmtRate(m.autorouter_hit_rate),
				detail: `hit rate  ·  avg ${fmtDuration(m.avg_session_duration_s)} per session`,
				icon: '⚡'
			}
		];
	}

	let metricCards = $derived(metrics ? buildMetricCards(metrics) : []);

	onMount(async () => {
		try {
			const [m, s, t, c] = await Promise.all([
				getMetricsSummary('week'),
				getSessions(1, 8),
				getTokenUsage('day'),
				getCostOverTime('day')
			]);
			metrics = m;
			sessions = s;
			tokenBuckets = t.buckets;
			costBuckets = c.buckets;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load dashboard';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Dashboard — claude-kit</title>
</svelte:head>

{#if loading}
	<div class="flex items-center justify-center py-20" transition:fade={{ duration: 200 }}>
		<div class="text-sm tracking-wide animate-pulse" style="color: var(--color-text-muted)">
			Loading dashboard…
		</div>
	</div>
{:else if error}
	<div class="flex flex-col items-center justify-center py-20">
		<div
			class="rounded-lg px-4 py-3 text-sm"
			style="background: var(--color-error-light); color: var(--color-error)"
		>
			{error}
		</div>
		<p class="mt-3 text-xs" style="color: var(--color-text-muted)">
			Make sure the API is running at <code class="font-mono">localhost:8000</code>
		</p>
	</div>
{:else}
	<!-- Page header -->
	<div class="mb-8">
		<h1
			class="text-2xl tracking-tight text-aurora"
			style="font-family: var(--font-display)"
		>
			Overview
		</h1>
		<p class="mt-1 text-sm" style="color: var(--color-text-muted)">
			Last 7 days of session telemetry
		</p>
	</div>

	<!-- Metric cards -->
	<div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#each metricCards as card, i}
			<div in:fly={{ y: 20, duration: 400, delay: i * 100 }}>
				<MetricCard
					label={card.label}
					value={card.value}
					detail={card.detail}
					icon={card.icon}
				/>
			</div>
		{/each}
	</div>

	<!-- Charts row -->
	<div class="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
		<!-- Token usage chart -->
		<div class="glass-card aurora-border-top p-5" in:fly={{ y: 20, duration: 400, delay: 500 }}>
			<h3 class="mb-4 text-sm font-semibold" style="color: var(--color-text)">Token Usage</h3>
			{#if tokenBuckets.length > 0}
				<TokenChart buckets={tokenBuckets} />
			{:else}
				<div class="flex h-[260px] items-center justify-center">
					<p class="text-sm" style="color: var(--color-text-muted)">
						No token data yet
					</p>
				</div>
			{/if}
		</div>

		<!-- Cost chart -->
		<div class="glass-card aurora-border-top p-5" in:fly={{ y: 20, duration: 400, delay: 700 }}>
			<h3 class="mb-4 text-sm font-semibold" style="color: var(--color-text)">
				Cost Over Time
			</h3>
			{#if costBuckets.length > 0}
				<CostChart buckets={costBuckets} />
			{:else}
				<div class="flex h-[260px] items-center justify-center">
					<p class="text-sm" style="color: var(--color-text-muted)">
						No cost data yet
					</p>
				</div>
			{/if}
		</div>
	</div>

	<!-- Skills + Sessions row -->
	<div class="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
		<!-- Top skills -->
		<div class="glass-card aurora-border-top p-5" in:fly={{ y: 20, duration: 400, delay: 900 }}>
			<h3 class="mb-4 text-sm font-semibold" style="color: var(--color-text)">
				Top Skills
			</h3>
			{#if metrics?.top_skills && metrics.top_skills.length > 0}
				<SkillsChart skills={metrics.top_skills} />
			{:else}
				<div class="flex h-[220px] items-center justify-center">
					<p class="text-sm" style="color: var(--color-text-muted)">
						No skill data yet
					</p>
				</div>
			{/if}
		</div>

		<!-- Recent sessions table -->
		<div class="lg:col-span-2" in:fly={{ y: 20, duration: 400, delay: 900 }}>
			<SessionTable sessions={sessions?.sessions ?? []} />
		</div>
	</div>
{/if}
