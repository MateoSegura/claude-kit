<script lang="ts">
	import { onMount } from 'svelte';
	import Chart from 'chart.js/auto';

	let { skills }: { skills: { skill: string; count: number }[] } = $props();
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;

	const palette = ['#14b8a6', '#8b5cf6', '#f43f5e', '#60a5fa', '#34d399', '#fbbf24', '#f472b6'];

	onMount(() => {
		const top = skills.slice(0, 7);
		chart = new Chart(canvas, {
			type: 'doughnut',
			data: {
				labels: top.map((s) => s.skill.replace(/^(core|cloud|embedded|frontend)-/, '')),
				datasets: [
					{
						data: top.map((s) => s.count),
						backgroundColor: palette.slice(0, top.length),
						borderWidth: 2,
						borderColor: '#0a0e1a',
						hoverOffset: 4
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				cutout: '65%',
				plugins: {
					legend: {
						position: 'right',
						labels: {
							font: { family: 'Inter', size: 11 },
							color: '#7a8ba3',
							usePointStyle: true,
							pointStyle: 'circle',
							padding: 12
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
						cornerRadius: 8
					}
				}
			}
		});

		return () => chart?.destroy();
	});
</script>

<div class="relative w-full" style="height: 220px">
	<canvas bind:this={canvas}></canvas>
</div>
