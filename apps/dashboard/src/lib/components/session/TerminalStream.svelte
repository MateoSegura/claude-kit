<script lang="ts">
	import type { TelemetryEvent } from '$lib/api';
	import { fmtTime, dur } from './event-utils';

	let {
		events,
		sessionId,
		isLive
	}: {
		events: TelemetryEvent[];
		sessionId: string;
		isLive: boolean;
	} = $props();

	let bodyEl: HTMLDivElement | undefined = $state();
	let userScrolledUp = $state(false);
	let prevEventCount = $state(0);

	function onScroll() {
		if (!bodyEl) return;
		const atBottom = bodyEl.scrollHeight - bodyEl.scrollTop - bodyEl.clientHeight < 40;
		userScrolledUp = !atBottom;
	}

	function scrollToBottom() {
		if (bodyEl) {
			bodyEl.scrollTop = bodyEl.scrollHeight;
			userScrolledUp = false;
		}
	}

	$effect(() => {
		if (events.length > prevEventCount && !userScrolledUp && bodyEl) {
			// Use requestAnimationFrame to ensure DOM has updated
			requestAnimationFrame(() => {
				if (bodyEl) bodyEl.scrollTop = bodyEl.scrollHeight;
			});
		}
		prevEventCount = events.length;
	});

	interface TerminalLine {
		prefix: string;
		text: string;
		color: string;
		dim?: boolean;
		center?: boolean;
		separator?: boolean;
	}

	function toolName(payload: Record<string, unknown>): string {
		return (payload.tool_name as string) ?? (payload.name as string) ?? '';
	}

	function parseInputPreview(payload: Record<string, unknown>): Record<string, string> {
		const raw = (payload.input_preview as string) ?? '';
		if (!raw || !raw.startsWith('{')) return {};
		try { return JSON.parse(raw); } catch { return {}; }
	}

	function mapEvent(event: TelemetryEvent, prevEvent: TelemetryEvent | null): TerminalLine[] {
		const lines: TerminalLine[] = [];
		const p = event.payload;

		// Add separator before prompt.submitted (except first one)
		if (event.event_type === 'prompt.submitted' && prevEvent) {
			lines.push({ prefix: '', text: '···', color: 'var(--color-text-muted)', center: true, separator: true });
		}

		switch (event.event_type) {
			case 'prompt.submitted': {
				const text = (p.text as string) ?? (p.prompt as string) ?? (p.prompt_text as string) ?? '';
				lines.push({ prefix: fmtTime(event.timestamp), text: `❯ ${text}`, color: '#e2e8f0' });
				break;
			}
			case 'tool.used': {
				const name = toolName(p);
				const inp = parseInputPreview(p);
				const command = (p.command as string) ?? (inp.command as string) ?? (p.input as string) ?? '';
				const path = (p.file_path as string) ?? (inp.file_path as string) ?? (p.path as string) ?? '';
				const pattern = (p.pattern as string) ?? (inp.pattern as string) ?? '';
				const resultText = (p.result as string) ?? (p.output as string) ?? '';
				const isError = !!(p.error || p.is_error);

				if (name === 'Bash') {
					lines.push({ prefix: fmtTime(event.timestamp), text: `$ ${command}`, color: '#34d399' });
					if (resultText) lines.push({ prefix: '', text: resultText.slice(0, 200), color: 'var(--color-text-muted)', dim: true });
				} else if (name === 'Read') {
					lines.push({ prefix: fmtTime(event.timestamp), text: `[Read] ${path}`, color: '#14b8a6' });
				} else if (name === 'Write') {
					lines.push({ prefix: fmtTime(event.timestamp), text: `[Write] ${path}`, color: '#8b5cf6' });
				} else if (name === 'Edit') {
					lines.push({ prefix: fmtTime(event.timestamp), text: `[Edit] ${path}`, color: '#8b5cf6' });
				} else if (name === 'Grep') {
					lines.push({ prefix: fmtTime(event.timestamp), text: `[Grep] ${pattern}`, color: '#f97316' });
				} else if (name === 'Glob') {
					lines.push({ prefix: fmtTime(event.timestamp), text: `[Glob] ${pattern}`, color: '#fbbf24' });
				} else if (name === 'Skill') {
					const inputStr = (p.input_preview as string) ?? (p.input as string) ?? '';
					const skillMatch = inputStr.match(/"skill"\s*:\s*"([^"]+)"/);
					const skillName = skillMatch ? skillMatch[1] : 'unknown';
					lines.push({ prefix: fmtTime(event.timestamp), text: `[skill] ${skillName}`, color: '#fbbf24' });
				} else if (name === 'Agent') {
					const inputStr = (p.input_preview as string) ?? (p.input as string) ?? '';
					const descMatch = inputStr.match(/"description"\s*:\s*"([^"]+)"/);
					const typeMatch = inputStr.match(/"subagent_type"\s*:\s*"([^"]+)"/);
					const desc = descMatch ? descMatch[1] : '';
					const agentType = typeMatch ? typeMatch[1] : '';
					lines.push({ prefix: fmtTime(event.timestamp), text: `[agent] ${agentType ? agentType + ': ' : ''}${desc}`, color: '#a78bfa' });
				} else {
					const preview = command || path || pattern || Object.values(p).slice(0, 1).join(', ');
					lines.push({ prefix: fmtTime(event.timestamp), text: `[${name}] ${preview}`.trim(), color: 'var(--color-accent)' });
				}

				if (isError && resultText) {
					lines.push({ prefix: '', text: `ERROR: ${resultText.slice(0, 200)}`, color: '#f43f5e' });
				}
				break;
			}
			case 'tool.result': {
				const isErr = !!(p.is_error);
				const errText = (p.error as string) ?? '';
				const resultText = (p.result as string) ?? (p.output as string) ?? '';
				if (isErr) {
					const name = toolName(p);
					lines.push({ prefix: fmtTime(event.timestamp), text: `[${name || 'tool'}] ERROR: ${(errText || resultText).slice(0, 300)}`, color: '#f43f5e' });
				} else if (resultText) {
					lines.push({ prefix: fmtTime(event.timestamp), text: resultText.slice(0, 200), color: 'var(--color-text-muted)', dim: true });
				}
				break;
			}
			case 'session.start':
				lines.push({ prefix: '', text: '── session started ──', color: 'var(--color-text-muted)', center: true });
				break;
			case 'session.end': {
				const duration = (p.duration_s as number) ?? null;
				lines.push({ prefix: '', text: `── session ended (${dur(duration)}) ──`, color: 'var(--color-text-muted)', center: true });
				break;
			}
			case 'session.compact':
				lines.push({ prefix: fmtTime(event.timestamp), text: '[compact] context window compacted', color: '#fbbf24' });
				break;
			case 'session.error': {
				const msg = (p.message as string) ?? (p.error as string) ?? 'unknown error';
				lines.push({ prefix: fmtTime(event.timestamp), text: `ERROR: ${msg}`, color: '#f43f5e' });
				break;
			}
			case 'plugin.loaded': {
				const name = (p.plugin as string) ?? (p.name as string) ?? '';
				lines.push({ prefix: fmtTime(event.timestamp), text: `[kit] loaded ${name}`, color: 'var(--color-text-muted)', dim: true });
				break;
			}
			case 'skill.invoked': {
				const name = (p.skill as string) ?? (p.name as string) ?? '';
				lines.push({ prefix: fmtTime(event.timestamp), text: `[kit] skill: ${name}`, color: '#fbbf24' });
				break;
			}
			case 'hook.fired': {
				const hookEvent = (p.event as string) ?? (p.hook as string) ?? '';
				lines.push({ prefix: fmtTime(event.timestamp), text: `[kit] hook: ${hookEvent}`, color: '#f43f5e' });
				break;
			}
			case 'autorouter.match': {
				const intent = (p.intent as string) ?? '';
				const skill = (p.skill as string) ?? (p.target as string) ?? '';
				lines.push({ prefix: fmtTime(event.timestamp), text: `[kit] route: "${intent}" → ${skill}`, color: '#f97316' });
				break;
			}
			case 'autorouter.miss': {
				const intent = (p.intent as string) ?? '';
				lines.push({ prefix: fmtTime(event.timestamp), text: `[kit] route miss: "${intent}"`, color: '#f97316', dim: true });
				break;
			}
			case 'message.assistant': {
				const text = (p.text as string) ?? (p.content_preview as string) ?? '';
				const truncated = text.length > 300 ? text.slice(0, 300) + '…' : text;
				if (truncated) {
					lines.push({ prefix: fmtTime(event.timestamp), text: `[Claude] ${truncated}`, color: '#60a5fa' });
				} else {
					lines.push({ prefix: fmtTime(event.timestamp), text: '[Claude] (empty response)', color: '#60a5fa', dim: true });
				}
				break;
			}
			case 'message.system': {
				const text = (p.text as string) ?? (p.message as string) ?? '';
				lines.push({ prefix: fmtTime(event.timestamp), text: `[system] ${text.slice(0, 200)}`, color: '#fbbf24', dim: true });
				break;
			}
			case 'turn.completed': {
				const tokensIn = (p.tokens_in as number) ?? 0;
				const tokensOut = (p.tokens_out as number) ?? 0;
				const turn = (p.turn_number as number) ?? null;
				const cost = (p.cost_usd as number) ?? null;
				let detail = `${tokensIn} in / ${tokensOut} out`;
				if (turn) detail = `#${turn} · ${detail}`;
				if (cost !== null) detail += ` · $${cost.toFixed(4)}`;
				lines.push({ prefix: fmtTime(event.timestamp), text: `[turn] ${detail}`, color: '#34d399', dim: true });
				break;
			}
			case 'subagent.start': {
				const agentType = (p.agent_type as string) ?? 'unknown';
				const agentName = (p.agent_name as string) ?? '';
				const label = agentName ? `${agentType}:${agentName}` : agentType;
				lines.push({ prefix: fmtTime(event.timestamp), text: `[agent] ▸ ${label}`, color: '#a78bfa' });
				break;
			}
			case 'subagent.stop': {
				const agentType = (p.agent_type as string) ?? 'unknown';
				const agentName = (p.agent_name as string) ?? '';
				const label = agentName ? `${agentType}:${agentName}` : agentType;
				lines.push({ prefix: fmtTime(event.timestamp), text: `[agent] ◂ ${label}`, color: '#a78bfa', dim: true });
				break;
			}
			case 'validation.result': {
				const passed = (p.passed as boolean) ?? true;
				const msg = (p.message as string) ?? (passed ? 'passed' : 'failed');
				lines.push({ prefix: fmtTime(event.timestamp), text: `[validate] ${msg}`, color: passed ? '#34d399' : '#f43f5e' });
				break;
			}
			default: {
				const preview = Object.entries(p).slice(0, 2).map(([k, v]) => `${k}=${v}`).join(' ');
				lines.push({ prefix: fmtTime(event.timestamp), text: `[${event.event_type}] ${preview}`, color: 'var(--color-text-secondary)' });
			}
		}
		return lines;
	}

	let terminalLines = $derived.by(() => {
		const lines: TerminalLine[] = [];
		for (let i = 0; i < events.length; i++) {
			lines.push(...mapEvent(events[i], i > 0 ? events[i - 1] : null));
		}
		return lines;
	});
</script>

<div class="terminal-window">
	<!-- Title bar -->
	<div class="terminal-titlebar">
		<span class="terminal-dot" style="background: #ff5f56;"></span>
		<span class="terminal-dot" style="background: #ffbd2e;"></span>
		<span class="terminal-dot" style="background: #27c93f;"></span>
		<span class="ml-2 font-mono text-[11px]" style="color: var(--color-text-muted)">
			{sessionId.slice(0, 8)} · {events.length} events
		</span>
		{#if isLive}
			<span
				class="ml-auto inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
				style="background: var(--color-success-light); color: var(--color-success)"
			>
				<span class="live-dot"></span>
				LIVE
			</span>
		{/if}
	</div>

	<!-- Terminal body -->
	<div class="terminal-body relative" bind:this={bodyEl} onscroll={onScroll}>
		<!-- Window boundary: start marker -->
		{#if events.length > 0 && events[0].event_type !== 'session.start'}
			<div class="my-2 text-center" style="color: var(--color-text-muted); opacity: 0.5;">
				── viewing from {fmtTime(events[0].timestamp)} ──
			</div>
		{/if}

		{#each terminalLines as line}
			{#if line.center}
				<div class="my-2 text-center" style="color: {line.color}; opacity: {line.dim ? 0.5 : 0.7}">
					{line.text}
				</div>
			{:else}
				<div class="flex gap-2" style="opacity: {line.dim ? 0.5 : 1}">
					{#if line.prefix}
						<span class="shrink-0 select-none" style="color: var(--color-text-muted); min-width: 100px;">{line.prefix}</span>
					{:else}
						<span class="shrink-0" style="min-width: 100px;"></span>
					{/if}
					<span style="color: {line.color}; word-break: break-all;">{line.text}</span>
				</div>
			{/if}
		{/each}

		<!-- Window boundary: end marker -->
		{#if events.length > 0 && events[events.length - 1].event_type !== 'session.end'}
			<div class="my-2 text-center" style="color: var(--color-text-muted); opacity: 0.5;">
				── window ends {fmtTime(events[events.length - 1].timestamp)} ──
			</div>
		{/if}

		{#if events.length === 0}
			<div class="py-8 text-center" style="color: var(--color-text-muted)">
				Waiting for events…
			</div>
		{/if}
	</div>

	<!-- Scroll to bottom button -->
	{#if userScrolledUp}
		<button
			onclick={scrollToBottom}
			class="absolute bottom-4 right-4 cursor-pointer rounded-md px-3 py-1.5 text-xs font-medium"
			style="background: var(--color-accent); color: white; z-index: 10;"
		>
			↓ scroll to bottom
		</button>
	{/if}
</div>
