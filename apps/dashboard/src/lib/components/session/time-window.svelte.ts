export type TimeMode = 'live' | 'history';
export type Interval = '1m' | '5m' | '20m' | '1h' | 'all';

const INTERVAL_MS: Record<string, number> = {
	'1m': 60_000,
	'5m': 300_000,
	'20m': 1_200_000,
	'1h': 3_600_000
};

function intervalToMs(i: Interval, sessionStart: number, sessionEnd: number): number {
	if (i === 'all') return sessionEnd - sessionStart;
	return INTERVAL_MS[i] ?? sessionEnd - sessionStart;
}

export class TimeWindow {
	mode: TimeMode = $state('history');
	interval: Interval = $state('all');
	windowStart: number = $state(0);
	windowEnd: number = $state(0);
	sessionStart: number = $state(0);
	sessionEnd: number = $state(0);
	paused: boolean = $state(false);

	windowMs = $derived(intervalToMs(this.interval, this.sessionStart, this.sessionEnd));
	canStepBack = $derived(this.windowStart > this.sessionStart);
	canStepForward = $derived(this.windowEnd < this.sessionEnd);

	setInterval(i: Interval): void {
		this.interval = i;
		if (i === 'all') {
			this.windowStart = this.sessionStart;
			this.windowEnd = this.sessionEnd;
			return;
		}
		const ms = INTERVAL_MS[i] ?? 0;
		if (this.mode === 'live' && !this.paused) {
			// Live: right edge = sessionEnd, width = interval
			this.windowEnd = this.sessionEnd;
			this.windowStart = Math.max(this.sessionStart, this.sessionEnd - ms);
		} else {
			// History: right-align to current windowEnd (or sessionEnd)
			const end = Math.min(this.windowEnd, this.sessionEnd);
			this.windowEnd = end;
			this.windowStart = Math.max(this.sessionStart, end - ms);
		}
	}

	stepForward(): void {
		if (!this.canStepForward) return;
		const step = this.windowMs / 2;
		const newEnd = Math.min(this.sessionEnd, this.windowEnd + step);
		const width = this.windowEnd - this.windowStart;
		this.windowEnd = newEnd;
		this.windowStart = Math.max(this.sessionStart, newEnd - width);
	}

	stepBackward(): void {
		if (!this.canStepBack) return;
		const step = this.windowMs / 2;
		const width = this.windowEnd - this.windowStart;
		const newStart = Math.max(this.sessionStart, this.windowStart - step);
		this.windowStart = newStart;
		this.windowEnd = Math.min(this.sessionEnd, newStart + width);
	}

	togglePause(): void {
		this.paused = !this.paused;
		if (!this.paused && this.mode === 'live') {
			// Resuming: snap to live edge
			const width = this.windowEnd - this.windowStart;
			this.windowEnd = this.sessionEnd;
			this.windowStart = Math.max(this.sessionStart, this.sessionEnd - width);
		}
	}

	setSessionBounds(start: number, end: number | null): void {
		this.sessionStart = start;
		this.sessionEnd = end ?? Date.now();
		// Initialize window to full session on first call
		if (this.windowStart === 0 && this.windowEnd === 0) {
			this.windowStart = this.sessionStart;
			this.windowEnd = this.sessionEnd;
		}
	}

	setWindowFromScrubber(start: number, end: number): void {
		this.windowStart = Math.max(this.sessionStart, start);
		this.windowEnd = Math.min(this.sessionEnd, end);

		// Try to snap to a preset interval if within 10% tolerance
		const width = this.windowEnd - this.windowStart;
		for (const [key, ms] of Object.entries(INTERVAL_MS)) {
			if (Math.abs(width - ms) / ms < 0.1) {
				this.interval = key as Interval;
				return;
			}
		}
		// Check if it covers the full session
		const sessionSpan = this.sessionEnd - this.sessionStart;
		if (sessionSpan > 0 && Math.abs(width - sessionSpan) / sessionSpan < 0.05) {
			this.interval = 'all';
			return;
		}
		// Custom range: keep interval as-is (visual indicator will show active pill deselected)
	}

	tick(): void {
		if (this.mode !== 'live' || this.paused) return;
		const now = Date.now();
		this.sessionEnd = now;
		if (this.interval === 'all') {
			this.windowEnd = now;
		} else {
			const ms = INTERVAL_MS[this.interval] ?? 0;
			this.windowEnd = now;
			this.windowStart = Math.max(this.sessionStart, now - ms);
		}
	}
}

export function createTimeWindow(): TimeWindow {
	return new TimeWindow();
}
