<script lang="ts">
	import { onMount } from 'svelte';
	import type { TokenBucket } from '$lib/api';
	import Chart from 'chart.js/auto';

	let { buckets }: { buckets: TokenBucket[] } = $props();
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;

	function shortLabel(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	onMount(() => {
		const labels = buckets.map((b) => shortLabel(b.bucket));
		chart = new Chart(canvas, {
			type: 'line',
			data: {
				labels,
				datasets: [
					{
						label: 'Tokens In',
						data: buckets.map((b) => b.tokens_in),
						borderColor: '#14b8a6',
						backgroundColor: 'rgba(20, 184, 166, 0.08)',
						fill: true,
						tension: 0.35,
						pointRadius: 3,
						pointHoverRadius: 5
					},
					{
						label: 'Tokens Out',
						data: buckets.map((b) => b.tokens_out),
						borderColor: '#8b5cf6',
						backgroundColor: 'rgba(139, 92, 246, 0.08)',
						fill: true,
						tension: 0.35,
						pointRadius: 3,
						pointHoverRadius: 5
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				interaction: { intersect: false, mode: 'index' },
				plugins: {
					legend: {
						position: 'bottom',
						labels: {
							font: { family: 'Inter', size: 11 },
							color: '#7a8ba3',
							usePointStyle: true,
							pointStyle: 'circle',
							padding: 16
						}
					},
					tooltip: {
						backgroundColor: 'rgba(15, 20, 36, 0.95)',
						borderColor: 'rgba(255, 255, 255, 0.08)',
						borderWidth: 1,
						titleFont: { family: 'Inter', size: 12 },
						titleColor: '#c8d6e5',
						bodyFont: { family: 'JetBrains Mono', size: 11 },
						bodyColor: '#c8d6e5',
						padding: 10,
						cornerRadius: 8,
						callbacks: {
							label: (ctx) => {
								const v = ctx.parsed.y ?? 0;
								const label = ctx.dataset.label || '';
								return v >= 1000 ? `${label}: ${(v / 1000).toFixed(1)}K` : `${label}: ${v}`;
							}
						}
					}
				},
				scales: {
					x: {
						grid: { display: false },
						ticks: { font: { family: 'Inter', size: 11 }, color: '#4a5568' }
					},
					y: {
						grid: { color: 'rgba(255, 255, 255, 0.04)' },
						ticks: {
							font: { family: 'JetBrains Mono', size: 11 },
							color: '#4a5568',
							callback: (v) => {
								const n = typeof v === 'number' ? v : Number(v);
								return n >= 1000 ? `${(n / 1000).toFixed(0)}K` : String(n);
							}
						}
					}
				}
			}
		});

		return () => chart?.destroy();
	});
</script>

<div class="relative w-full" style="height: 260px">
	<canvas bind:this={canvas}></canvas>
</div>
