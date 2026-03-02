<script lang="ts">
	let { activeView, onViewChange }: { activeView: 'chat' | 'timeline'; onViewChange: (view: 'chat' | 'timeline') => void } = $props();
</script>

<div class="flex items-center gap-1">
	<button
		onclick={() => onViewChange('chat')}
		class="cursor-pointer rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
		style="background: {activeView === 'chat' ? 'var(--color-accent)' : 'transparent'}; color: {activeView === 'chat' ? 'white' : 'var(--color-text-secondary)'}"
	>
		💬 Chat
	</button>
	<button
		onclick={() => onViewChange('timeline')}
		class="cursor-pointer rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
		style="background: {activeView === 'timeline' ? 'var(--color-accent)' : 'transparent'}; color: {activeView === 'timeline' ? 'white' : 'var(--color-text-secondary)'}"
	>
		≡ Timeline
	</button>
</div>
