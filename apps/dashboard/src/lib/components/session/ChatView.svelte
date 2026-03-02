<script lang="ts">
	import type { TelemetryEvent } from '$lib/api';
	import { fmtTime } from './event-utils';

	let {
		events,
		sessionId,
		isLive
	}: {
		events: TelemetryEvent[];
		sessionId: string;
		isLive: boolean;
	} = $props();

	let chatEl: HTMLDivElement | undefined = $state();
	let userScrolledUp = $state(false);
	let prevCount = $state(0);
	let expandedTools: Set<string> = $state(new Set());
	let expandedGroups: Set<number> = $state(new Set());
	let expandedErrors: Set<string> = $state(new Set());

	function onScroll() {
		if (!chatEl) return;
		userScrolledUp = chatEl.scrollHeight - chatEl.scrollTop - chatEl.clientHeight > 40;
	}

	function scrollToBottom() {
		if (chatEl) { chatEl.scrollTop = chatEl.scrollHeight; userScrolledUp = false; }
	}

	$effect(() => {
		if (events.length > prevCount && !userScrolledUp && chatEl) {
			requestAnimationFrame(() => { if (chatEl) chatEl.scrollTop = chatEl.scrollHeight; });
		}
		prevCount = events.length;
	});

	function toggleError(id: string) {
		const next = new Set(expandedErrors);
		if (next.has(id)) next.delete(id); else next.add(id);
		expandedErrors = next;
	}

	function toggleTool(id: string) {
		const next = new Set(expandedTools);
		if (next.has(id)) next.delete(id); else next.add(id);
		expandedTools = next;
	}

	function toggleGroup(idx: number) {
		const next = new Set(expandedGroups);
		if (next.has(idx)) next.delete(idx); else next.add(idx);
		expandedGroups = next;
	}

	// ── Parse events into conversation blocks ──
	type BlockType = 'user' | 'assistant' | 'tool' | 'kit' | 'agent-start' | 'agent-stop' | 'error' | 'system';

	interface ChatBlock {
		id: string;
		type: BlockType;
		timestamp: string;
		promptText?: string;
		assistantText?: string;
		toolName?: string;
		toolIcon?: string;
		toolSummary?: string;
		toolDetail?: string;
		isError?: boolean;
		kitLabel?: string;
		kitDetail?: string;
		kitColor?: string;
		agentType?: string;
		agentDesc?: string;
		errorMsg?: string;
		systemText?: string;
		payload?: Record<string, unknown>;
	}

	function parseInputPreview(p: Record<string, unknown>): Record<string, string> {
		const raw = (p.input_preview as string) ?? '';
		if (!raw || !raw.startsWith('{')) return {};
		try { return JSON.parse(raw); } catch { return {}; }
	}

	const TOOL_COLORS: Record<string, string> = {
		Bash: '#34d399', Read: '#14b8a6', Write: '#8b5cf6', Edit: '#8b5cf6',
		Grep: '#f97316', Glob: '#fbbf24', WebFetch: '#60a5fa', WebSearch: '#60a5fa',
	};

	function buildBlocks(evts: TelemetryEvent[]): ChatBlock[] {
		const blocks: ChatBlock[] = [];
		for (const ev of evts) {
			const p = ev.payload;
			const base = { id: ev.id, timestamp: ev.timestamp, payload: p };

			switch (ev.event_type) {
				case 'prompt.submitted':
					blocks.push({ ...base, type: 'user', promptText: (p.text as string) ?? (p.prompt_text as string) ?? (p.prompt as string) ?? '' });
					break;

				case 'message.assistant': {
					const text = (p.text as string) ?? (p.content_preview as string) ?? '';
					if (text) blocks.push({ ...base, type: 'assistant', assistantText: text });
					break;
				}

				case 'tool.used': {
					const name = (p.tool_name as string) ?? (p.name as string) ?? '';
					const inp = parseInputPreview(p);
					const isErr = !!(p.error || p.is_error);

					if (name === 'Skill') {
						const raw = (p.input_preview as string) ?? '';
						const m = raw.match(/"skill"\s*:\s*"([^"]+)"/);
						blocks.push({ ...base, type: 'kit', kitLabel: 'routed', kitDetail: m ? m[1] : 'skill', kitColor: '#fbbf24' });
					} else if (name === 'Agent') {
						const raw = (p.input_preview as string) ?? '';
						const dm = raw.match(/"description"\s*:\s*"([^"]+)"/);
						const tm = raw.match(/"subagent_type"\s*:\s*"([^"]+)"/);
						blocks.push({ ...base, type: 'agent-start', agentType: tm ? tm[1] : '', agentDesc: dm ? dm[1] : '' });
					} else {
						const command = (p.command as string) ?? (inp.command as string) ?? '';
						const path = (p.file_path as string) ?? (inp.file_path as string) ?? (p.path as string) ?? '';
						const pattern = (p.pattern as string) ?? (inp.pattern as string) ?? '';
						const result = (p.result_preview as string) ?? (p.result as string) ?? (p.output as string) ?? '';
						let summary = '';
						if (name === 'Bash') summary = command;
						else if (name === 'Read' || name === 'Write' || name === 'Edit') summary = path;
						else if (name === 'Grep' || name === 'Glob') summary = pattern;
						else summary = command || path || pattern;

						blocks.push({
							...base, type: 'tool', toolName: name,
							toolSummary: summary.slice(0, 200), toolDetail: result.slice(0, 500),
							isError: isErr,
						});
					}
					break;
				}

				case 'tool.result': {
					const isErr = !!(p.is_error);
					const text = (p.error as string) ?? (p.result as string) ?? (p.output as string) ?? '';
					if (isErr && text) blocks.push({ ...base, type: 'error', errorMsg: text.slice(0, 500) });
					break;
				}

				case 'plugin.loaded': {
					const name = (p.plugin as string) ?? (p.name as string) ?? '';
					blocks.push({ ...base, type: 'kit', kitLabel: 'loaded', kitDetail: name, kitColor: '#64748b' });
					break;
				}

				case 'skill.invoked':
				case 'autorouter.match': {
					const skill = (p.skill as string) ?? (p.target as string) ?? (p.name as string) ?? '';
					const intent = (p.intent as string) ?? '';
					blocks.push({ ...base, type: 'kit', kitLabel: 'routed', kitDetail: intent ? `"${intent}" \u2192 ${skill}` : skill, kitColor: '#fbbf24' });
					break;
				}

				case 'hook.fired': {
					const hook = (p.event as string) ?? (p.hook as string) ?? '';
					blocks.push({ ...base, type: 'kit', kitLabel: 'hook', kitDetail: hook, kitColor: '#f97316' });
					break;
				}

				case 'subagent.start': {
					const at = (p.agent_type as string) ?? '';
					blocks.push({ ...base, type: 'agent-start', agentType: at, agentDesc: '' });
					break;
				}

				case 'subagent.stop': {
					const at = (p.agent_type as string) ?? '';
					blocks.push({ ...base, type: 'agent-stop', agentType: at, agentDesc: '' });
					break;
				}

				case 'session.error': {
					const msg = (p.message as string) ?? (p.error as string) ?? 'unknown error';
					blocks.push({ ...base, type: 'error', errorMsg: msg });
					break;
				}

				case 'session.compact':
					blocks.push({ ...base, type: 'system', systemText: 'Context window compacted' });
					break;

				case 'turn.completed':
				case 'session.start':
				case 'session.end':
				case 'message.system':
					break;

				default:
					break;
			}
		}
		return blocks;
	}

	let blocks = $derived(buildBlocks(events));

	// ── Group display blocks: collapse plugins + consecutive tool calls ──
	interface DisplayBlock {
		type: 'single' | 'plugin-group' | 'tool-group';
		block?: ChatBlock;
		plugins?: string[];
		tools?: ChatBlock[];
		timestamp?: string;
	}

	let displayBlocks = $derived.by(() => {
		const result: DisplayBlock[] = [];
		let pluginBuf: string[] = [];
		let pluginTs = '';
		let toolBuf: ChatBlock[] = [];
		let toolTs = '';

		function flushPlugins() {
			if (pluginBuf.length > 0) {
				result.push({ type: 'plugin-group', plugins: [...pluginBuf], timestamp: pluginTs });
				pluginBuf = [];
			}
		}
		function flushTools() {
			if (toolBuf.length > 0) {
				if (toolBuf.length <= 2) {
					toolBuf.forEach(b => result.push({ type: 'single', block: b }));
				} else {
					result.push({ type: 'tool-group', tools: [...toolBuf], timestamp: toolTs });
				}
				toolBuf = [];
			}
		}

		for (const b of blocks) {
			if (b.type === 'kit' && b.kitLabel === 'loaded') {
				flushTools();
				if (pluginBuf.length === 0) pluginTs = b.timestamp;
				pluginBuf.push(b.kitDetail ?? '');
				continue;
			}
			if (b.type === 'tool') {
				flushPlugins();
				if (toolBuf.length === 0) toolTs = b.timestamp;
				toolBuf.push(b);
				continue;
			}
			// Non-tool, non-plugin — flush both buffers
			flushPlugins();
			flushTools();
			result.push({ type: 'single', block: b });
		}
		flushPlugins();
		flushTools();
		return result;
	});

	// ── Extract tasks from tool.used events ──
	interface TaskItem { id: string; subject: string; status: 'pending' | 'in_progress' | 'completed'; }

	let tasks = $derived.by(() => {
		const taskMap = new Map<string, TaskItem>();
		for (const ev of events) {
			if (ev.event_type !== 'tool.used') continue;
			const name = (ev.payload.tool_name as string) ?? (ev.payload.name as string) ?? '';
			if (name !== 'TaskCreate' && name !== 'TaskUpdate' && name !== 'TodoWrite') continue;
			const inp = parseInputPreview(ev.payload);
			if (name === 'TaskCreate') {
				const id = inp.taskId ?? ev.id;
				taskMap.set(id, { id, subject: inp.subject ?? inp.content ?? '(task)', status: 'pending' });
			} else if (name === 'TaskUpdate') {
				const id = inp.taskId ?? '';
				const existing = taskMap.get(id);
				if (existing) {
					if (inp.status === 'completed' || inp.status === 'in_progress') existing.status = inp.status;
					if (inp.subject) existing.subject = inp.subject;
				}
			}
		}
		return [...taskMap.values()];
	});

	let hasTasks = $derived(tasks.length > 0);

	function toolColor(name: string): string {
		return TOOL_COLORS[name] ?? '#8b5cf6';
	}

	function toolCountSummary(tools: ChatBlock[]): string {
		const counts: Record<string, number> = {};
		for (const t of tools) { counts[t.toolName ?? ''] = (counts[t.toolName ?? ''] || 0) + 1; }
		return Object.entries(counts).map(([n, c]) => `${c} ${n}`).join(', ');
	}

	function renderText(text: string): string {
		return text
			.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
			.replace(/```([\s\S]*?)```/g, '<pre class="chat-code-block">$1</pre>')
			.replace(/`([^`]+)`/g, '<code class="chat-inline-code">$1</code>')
			.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
			.replace(/^## (.+)$/gm, '<div class="chat-h2">$1</div>')
			.replace(/^### (.+)$/gm, '<div class="chat-h3">$1</div>')
			.replace(/^- (.+)$/gm, '<div class="chat-li">\u2022 $1</div>')
			.replace(/^\| .+$/gm, (line: string) => `<div class="chat-table-row">${line}</div>`)
			.replace(/\n/g, '<br/>');
	}
</script>

<div class="flex gap-3" style="height: calc(100vh - 480px); min-height: 400px;">
	<!-- Chat panel -->
	<div class="flex flex-1 flex-col glass-card p-0 overflow-hidden" style="position: relative;">
		<!-- Chat header -->
		<div class="flex items-center gap-2 px-4 py-2.5" style="border-bottom: 1px solid var(--color-border-subtle); background: rgba(255,255,255,0.02);">
			<span class="font-mono text-[11px] font-bold" style="color: var(--color-text-secondary)">
				{sessionId.slice(0, 8)}
			</span>
			<span class="font-mono text-[10px]" style="color: var(--color-text-muted)">{events.length} events</span>
			{#if isLive}
				<span class="ml-auto inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-bold uppercase" style="background: var(--color-success-light); color: var(--color-success)">
					<span class="live-dot"></span> live
				</span>
			{/if}
		</div>

		<!-- Chat body -->
		<div class="chat-body flex-1 overflow-y-auto px-5 py-4" bind:this={chatEl} onscroll={onScroll}>
			{#each displayBlocks as db, idx}
				{#if db.type === 'plugin-group'}
					<!-- Collapsed plugin load group -->
					<div class="my-3 flex items-center gap-2 justify-center">
						<div class="h-px flex-1" style="background: var(--color-border-subtle);"></div>
						<span class="rounded-full px-3 py-1 font-mono text-[9px] font-semibold" style="background: rgba(100,116,139,0.1); color: #94a3b8;">
							{db.plugins?.length} plugins loaded
						</span>
						<div class="h-px flex-1" style="background: var(--color-border-subtle);"></div>
					</div>

				{:else if db.type === 'tool-group'}
					<!-- Collapsed tool call group -->
					<div class="my-2 ml-7">
						<button
							class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left cursor-pointer transition-all"
							style="background: rgba(139,92,246,0.04); border: 1px solid rgba(139,92,246,0.1);"
							onclick={() => toggleGroup(idx)}
						>
							<span class="shrink-0 text-[10px] transition-transform" style="color: #8b5cf6; transform: rotate({expandedGroups.has(idx) ? '90deg' : '0deg'});">{'\u25B8'}</span>
							<span class="font-mono text-[11px] font-semibold" style="color: #8b5cf6;">
								{db.tools?.length} tool calls
							</span>
							<span class="font-mono text-[10px] truncate" style="color: var(--color-text-muted);">
								{toolCountSummary(db.tools ?? [])}
							</span>
							<span class="ml-auto font-mono text-[9px]" style="color: var(--color-text-muted);">
								{fmtTime(db.timestamp ?? '')}
							</span>
						</button>
						{#if expandedGroups.has(idx)}
							<div class="mt-1 space-y-0.5 rounded-lg p-1.5" style="background: rgba(0,0,0,0.15); border: 1px solid var(--color-border-subtle);">
								{#each db.tools ?? [] as t}
									<div class="tool-row">
										<button
											class="flex w-full items-center gap-2 rounded-md px-2.5 py-1 text-left cursor-pointer"
											style="background: {t.isError ? 'rgba(244,63,94,0.06)' : 'transparent'};"
											onclick={() => toggleTool(t.id)}
										>
											<span class="shrink-0 w-1 h-1 rounded-full" style="background: {toolColor(t.toolName ?? '')}"></span>
											<span class="shrink-0 font-mono text-[10px] font-semibold" style="color: {t.isError ? '#f43f5e' : toolColor(t.toolName ?? '')}; min-width: 36px;">
												{t.toolName}
											</span>
											<span class="truncate font-mono text-[10px]" style="color: var(--color-text-muted);">
												{t.toolSummary}
											</span>
											{#if t.isError}
												<span class="ml-auto shrink-0 rounded px-1 py-0.5 text-[7px] font-bold" style="background: rgba(244,63,94,0.15); color: #f43f5e;">ERR</span>
											{/if}
										</button>
										{#if expandedTools.has(t.id) && (t.toolDetail || t.payload)}
											<div class="mx-2 mb-1 rounded-md p-2 font-mono text-[10px]" style="background: rgba(0,0,0,0.3); color: var(--color-text-muted); max-height: 150px; overflow-y: auto; white-space: pre-wrap; word-break: break-all;">
												{t.toolDetail || JSON.stringify(t.payload, null, 2)}
											</div>
										{/if}
									</div>
								{/each}
							</div>
						{/if}
					</div>

				{:else if db.block}
					{@const b = db.block}

					{#if b.type === 'user'}
						<!-- User message — right aligned bubble -->
						<div class="mt-5 mb-3 flex justify-end">
							<div class="max-w-[70%]">
								<div class="rounded-2xl rounded-br-sm px-4 py-3" style="background: var(--color-accent); color: white;">
									<div class="text-[13px] leading-relaxed whitespace-pre-wrap">{b.promptText}</div>
								</div>
								<div class="mt-1 text-right font-mono text-[9px]" style="color: var(--color-text-muted)">{fmtTime(b.timestamp)}</div>
							</div>
						</div>

					{:else if b.type === 'assistant'}
						<!-- Claude response — left aligned -->
						<div class="mt-4 mb-3 flex justify-start">
							<div class="max-w-[85%]">
								<div class="flex items-center gap-2 mb-1.5">
									<span class="inline-flex items-center justify-center rounded-full text-[10px] font-bold" style="width: 22px; height: 22px; background: linear-gradient(135deg, #8b5cf6, #60a5fa); color: white;">C</span>
									<span class="font-mono text-[10px] font-semibold" style="color: var(--color-text-secondary)">Claude</span>
									<span class="font-mono text-[9px]" style="color: var(--color-text-muted)">{fmtTime(b.timestamp)}</span>
								</div>
								<div class="chat-assistant-msg rounded-2xl rounded-tl-sm px-4 py-3" style="background: rgba(255,255,255,0.03); border: 1px solid var(--color-border-subtle);">
									<div class="chat-content text-[13px] leading-relaxed" style="color: var(--color-text)">
										{@html renderText(b.assistantText ?? '')}
									</div>
								</div>
							</div>
						</div>

					{:else if b.type === 'tool'}
						<!-- Single tool call (only when 1-2 in a row) -->
						<div class="my-1 ml-7">
							<button
								class="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-left cursor-pointer"
								style="background: {b.isError ? 'rgba(244,63,94,0.04)' : 'rgba(255,255,255,0.015)'}; border: 1px solid {b.isError ? 'rgba(244,63,94,0.15)' : 'var(--color-border-subtle)'};"
								onclick={() => toggleTool(b.id)}
							>
								<span class="shrink-0 w-1.5 h-1.5 rounded-full" style="background: {toolColor(b.toolName ?? '')}"></span>
								<span class="shrink-0 font-mono text-[11px] font-semibold" style="color: {b.isError ? '#f43f5e' : toolColor(b.toolName ?? '')};">
									{b.toolName}
								</span>
								<span class="truncate font-mono text-[11px]" style="color: var(--color-text-muted);">
									{b.toolSummary}
								</span>
								{#if b.isError}
									<span class="ml-auto shrink-0 rounded px-1.5 py-0.5 text-[8px] font-bold" style="background: rgba(244,63,94,0.15); color: #f43f5e;">ERR</span>
								{/if}
								<span class="ml-auto shrink-0 text-[10px]" style="color: var(--color-text-muted); transform: rotate({expandedTools.has(b.id) ? '90deg' : '0deg'}); transition: transform 0.15s;">{'\u25B8'}</span>
							</button>
							{#if expandedTools.has(b.id) && (b.toolDetail || b.payload)}
								<div class="mt-1 ml-5 rounded-md p-2.5 font-mono text-[10px]" style="background: rgba(0,0,0,0.25); color: var(--color-text-muted); border: 1px solid var(--color-border-subtle); max-height: 200px; overflow-y: auto; white-space: pre-wrap; word-break: break-all;">
									{b.toolDetail || JSON.stringify(b.payload, null, 2)}
								</div>
							{/if}
						</div>

					{:else if b.type === 'kit'}
						<!-- Kit event — subtle centered divider -->
						<div class="my-2 flex items-center gap-2 justify-center">
							<div class="h-px flex-1" style="background: var(--color-border-subtle);"></div>
							<span class="rounded-full px-2.5 py-0.5 font-mono text-[9px] font-semibold" style="background: color-mix(in srgb, {b.kitColor ?? '#f97316'} 10%, transparent); color: {b.kitColor ?? '#f97316'};">
								{b.kitLabel}: {b.kitDetail}
							</span>
							<div class="h-px flex-1" style="background: var(--color-border-subtle);"></div>
						</div>

					{:else if b.type === 'agent-start'}
						<div class="my-2.5 ml-5 flex items-center gap-2 rounded-lg px-3 py-2" style="background: rgba(167,139,250,0.05); border-left: 3px solid #a78bfa;">
							<span class="text-[11px]" style="color: #a78bfa;">{'\u25B8'}</span>
							<span class="font-mono text-[11px] font-semibold" style="color: #a78bfa;">agent</span>
							<span class="font-mono text-[11px]" style="color: var(--color-text-secondary);">{b.agentType}</span>
							{#if b.agentDesc}
								<span class="font-mono text-[10px]" style="color: var(--color-text-muted);">{'\u2014'} {b.agentDesc}</span>
							{/if}
						</div>

					{:else if b.type === 'agent-stop'}
						<div class="my-1.5 ml-5 flex items-center gap-2 rounded-lg px-3 py-1.5" style="background: rgba(167,139,250,0.03); border-left: 3px solid rgba(167,139,250,0.25);">
							<span class="text-[11px]" style="color: rgba(167,139,250,0.4);">{'\u25C2'}</span>
							<span class="font-mono text-[10px]" style="color: var(--color-text-muted);">{b.agentType} finished</span>
						</div>

					{:else if b.type === 'error'}
						<div class="my-2 ml-5 rounded-lg overflow-hidden" style="background: rgba(244,63,94,0.04); border: 1px solid rgba(244,63,94,0.12);">
							<button class="flex w-full items-center gap-2 px-3 py-1.5 text-left cursor-pointer" onclick={() => toggleError(b.id)}>
								<span class="text-[9px] font-bold shrink-0" style="color: #f43f5e;">ERR</span>
								<span class="font-mono text-[10px] truncate" style="color: #fca5a5;">{(b.errorMsg ?? '').slice(0, 120)}</span>
								<span class="ml-auto shrink-0 text-[10px]" style="color: var(--color-text-muted); transform: rotate({expandedErrors.has(b.id) ? '90deg' : '0deg'}); transition: transform 0.15s;">{'\u25B8'}</span>
							</button>
							{#if expandedErrors.has(b.id)}
								<div class="px-3 pb-2 font-mono text-[10px]" style="color: #fca5a5; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto;">
									{b.errorMsg}
								</div>
							{/if}
						</div>

					{:else if b.type === 'system'}
						<div class="my-2 flex items-center gap-2 justify-center">
							<div class="h-px flex-1" style="background: var(--color-border-subtle);"></div>
							<span class="font-mono text-[9px]" style="color: var(--color-text-muted);">{b.systemText}</span>
							<div class="h-px flex-1" style="background: var(--color-border-subtle);"></div>
						</div>
					{/if}
				{/if}
			{/each}

			{#if events.length === 0}
				<div class="flex items-center justify-center py-16" style="color: var(--color-text-muted)">
					Waiting for events{'\u2026'}
				</div>
			{/if}
		</div>

		<!-- Scroll to bottom -->
		{#if userScrolledUp}
			<button
				onclick={scrollToBottom}
				class="absolute bottom-4 right-4 cursor-pointer rounded-full px-3 py-1.5 text-xs font-medium shadow-lg"
				style="background: var(--color-accent); color: white; z-index: 10;"
			>
				{'\u2193'} latest
			</button>
		{/if}
	</div>

	<!-- Side panel: Tasks -->
	{#if hasTasks}
		<div class="glass-card w-64 shrink-0 p-0 overflow-hidden flex flex-col">
			<div class="px-3 py-2.5" style="border-bottom: 1px solid var(--color-border-subtle); background: rgba(255,255,255,0.02);">
				<span class="font-mono text-[11px] font-bold" style="color: var(--color-text-secondary);">Tasks</span>
				<span class="font-mono text-[10px] ml-1.5" style="color: var(--color-text-muted);">
					{tasks.filter(t => t.status === 'completed').length}/{tasks.length}
				</span>
			</div>
			<div class="flex-1 overflow-y-auto px-3 py-2">
				{#each tasks as task}
					<div class="flex items-start gap-2 py-2" style="border-bottom: 1px solid rgba(255,255,255,0.03);">
						<span class="shrink-0 mt-0.5 text-[12px]" style="color: {task.status === 'completed' ? '#34d399' : task.status === 'in_progress' ? '#fbbf24' : 'var(--color-text-muted)'};">
							{task.status === 'completed' ? '\u2713' : '\u25CB'}
						</span>
						<span class="text-[11px] leading-snug" style="color: {task.status === 'completed' ? 'var(--color-text-muted)' : 'var(--color-text-secondary)'}; {task.status === 'completed' ? 'text-decoration: line-through;' : ''}">
							{task.subject}
						</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
