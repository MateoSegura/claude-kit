import type { TelemetryEvent } from '$lib/api';

export const CLAUDE_EVENTS = [
	'turn.completed',
	'tool.used',
	'tool.result',
	'message.assistant',
	'message.system',
	'session.compact',
	'session.result',
	'session.error',
	'prompt.submitted',
	'subagent.start',
	'subagent.stop'
];

export const KIT_EVENTS = [
	'plugin.loaded',
	'skill.invoked',
	'hook.fired',
	'autorouter.match',
	'autorouter.miss',
	'validation.result',
	'session.start',
	'session.end'
];

export function isClaudeEvent(e: { event_type: string }): boolean {
	return CLAUDE_EVENTS.includes(e.event_type);
}

export function isKitEvent(e: { event_type: string }): boolean {
	return KIT_EVENTS.includes(e.event_type);
}

export function eventColor(type: string): string {
	if (type === 'prompt.submitted') return '#e2e8f0';
	if (type === 'session.start' || type === 'session.end') return '#14b8a6';
	if (type === 'session.error') return '#f43f5e';
	if (type === 'session.compact') return '#fbbf24';
	if (type.startsWith('tool.')) return '#8b5cf6';
	if (type.startsWith('message.')) return '#60a5fa';
	if (type === 'turn.completed') return '#34d399';
	if (type === 'plugin.loaded') return 'var(--color-text-muted)';
	if (type.startsWith('autorouter.')) return '#f97316';
	if (type === 'skill.invoked') return '#fbbf24';
	if (type === 'hook.fired') return '#f43f5e';
	if (type.startsWith('subagent.')) return '#a78bfa';
	return 'var(--color-text-secondary)';
}

export function fmtTime(iso: string): string {
	return new Date(iso).toLocaleTimeString('en-US', {
		hour: '2-digit',
		minute: '2-digit',
		second: '2-digit',
		fractionalSecondDigits: 3
	});
}

export function fmtDate(iso: string): string {
	return new Date(iso).toLocaleDateString('en-US', {
		month: 'short',
		day: 'numeric',
		year: 'numeric',
		hour: '2-digit',
		minute: '2-digit'
	});
}

export function dur(s: number | null): string {
	if (!s) return '—';
	if (s < 60) return `${Math.round(s)}s`;
	return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
}

export function tokens(n: number): string {
	if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
	if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
	return String(n);
}

export interface EventCounts {
	tools: number;
	prompts: number;
	errors: number;
	tokensIn: number;
	tokensOut: number;
	kitEvents: number;
}

export function countEvents(events: TelemetryEvent[]): EventCounts {
	const counts: EventCounts = { tools: 0, prompts: 0, errors: 0, tokensIn: 0, tokensOut: 0, kitEvents: 0 };
	for (const e of events) {
		switch (e.event_type) {
			case 'tool.used':
				counts.tools++;
				if (e.payload.error || e.payload.is_error) counts.errors++;
				break;
			case 'prompt.submitted':
				counts.prompts++;
				break;
			case 'session.error':
				counts.errors++;
				break;
			case 'turn.completed':
				counts.tokensIn += (e.payload.tokens_in as number) ?? 0;
				counts.tokensOut += (e.payload.tokens_out as number) ?? 0;
				break;
			default:
				if (isKitEvent(e)) counts.kitEvents++;
		}
	}
	return counts;
}

export function fmtTimeShort(ms: number): string {
	return new Date(ms).toLocaleTimeString('en-US', {
		hour: '2-digit',
		minute: '2-digit',
		second: '2-digit'
	});
}

export function payloadPreview(payload: Record<string, unknown>): string {
	const entries = Object.entries(payload);
	if (!entries.length) return '';
	return entries
		.slice(0, 4)
		.map(([k, v]) => {
			if (Array.isArray(v)) return `${k}: [${v.length}]`;
			if (typeof v === 'object' && v !== null) return `${k}: {…}`;
			const s = String(v);
			return `${k}: ${s.length > 50 ? s.slice(0, 47) + '…' : s}`;
		})
		.join('  ·  ');
}
