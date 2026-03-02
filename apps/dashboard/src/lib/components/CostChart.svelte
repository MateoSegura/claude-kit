<script lang="ts">
	import { onMount } from 'svelte';
	import type { CostBucket } from '$lib/api';
	import Chart from 'chart.js/auto';

	let { buckets }: { buckets: CostBucket[] } = $props();
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;

	function shortLabel(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	onMount(() => {
		const labels = buckets.map((b) => shortLabel(b.bucket));

		// Create aurora gradient for bars
		const ctx = canvas.getContext('2d')!;
		const gradient = ctx.createLinearGradient(0, 0, 0, 260);
		gradient.addColorStop(0, 'rgba(20, 184, 166, 0.8)');
		gradient.addColorStop(1, 'rgba(139, 92, 246, 0.6)');

		const hoverGradient = ctx.createLinearGradient(0, 0, 0, 260);
		hoverGradient.addColorStop(0, '#14b8a6');
		hoverGradient.addColorStop(1, '#8b5cf6');

		chart = new Chart(canvas, {
			type: 'bar',
			data: {
				labels,
				datasets: [
					{
						label: 'Cost (USD)',
						data: buckets.map((b) => b.cost_usd),
						backgroundColor: gradient,
						hoverBackgroundColor: hoverGradient,
						borderRadius: 6,
						borderSkipped: false,
						maxBarThickness: 40
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				interaction: { intersect: false, mode: 'index' },
				plugins: {
					legend: {
						display: false
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
							label: (ctx) => `$${(ctx.parsed.y ?? 0).toFixed(3)}`
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
							callback: (v) => `$${v}`
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
