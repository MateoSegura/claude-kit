<script lang="ts">
	let { label, value, detail = '', icon = '' }: { label: string; value: string; detail?: string; icon?: string } =
		$props();
</script>

<div class="glass-card aurora-border-top flex flex-col p-5">
	<div class="mb-3 flex items-center justify-between">
		<span class="text-xs font-medium uppercase tracking-wider" style="color: var(--color-text-muted)">
			{label}
		</span>
		{#if icon}
			<span class="text-sm" style="color: var(--color-aurora-teal)">{icon}</span>
		{/if}
	</div>
	<div class="text-2xl font-semibold tracking-tight" style="color: var(--color-text)">{value}</div>
	{#if detail}
		<div class="mt-1 text-xs" style="color: var(--color-text-secondary)">{detail}</div>
	{/if}
</div>
