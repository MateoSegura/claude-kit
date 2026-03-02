/** claude-kit API client — typed fetch wrapper for the telemetry backend. */

const BASE = '/api/v1';

function headers(): Record<string, string> {
	const h: Record<string, string> = { 'Content-Type': 'application/json' };
	const token = localStorage.getItem('ck_token');
	if (token) h['Authorization'] = `Bearer ${token}`;
	const apiKey = localStorage.getItem('ck_api_key');
	if (apiKey) h['X-API-Key'] = apiKey;
	return h;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE}${path}`, { headers: headers(), ...init });
	if (res.status === 401) {
		localStorage.removeItem('ck_token');
		window.location.href = '/login';
		throw new Error('Unauthorized');
	}
	if (!res.ok) {
		const body = await res.json().catch(() => ({ detail: res.statusText }));
		const detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
		throw new Error(detail || `HTTP ${res.status}`);
	}
	return res.json();
}

// ── Auth ──

export interface TokenResponse {
	access_token: string;
	refresh_token: string;
	expires_in: number;
}

export interface UserResponse {
	id: string;
	email: string;
	display_name: string | null;
}

export async function register(
	email: string,
	password: string,
	displayName?: string
): Promise<TokenResponse> {
	return request('/auth/register', {
		method: 'POST',
		body: JSON.stringify({ email, password, display_name: displayName })
	});
}

export async function login(email: string, password: string): Promise<TokenResponse> {
	return request('/auth/login', {
		method: 'POST',
		body: JSON.stringify({ email, password })
	});
}

export async function getMe(): Promise<UserResponse> {
	return request('/auth/me');
}

export interface ApiKeyResponse {
	id: string;
	name: string;
	key_prefix: string;
	raw_key: string;
	is_test: boolean;
	created_at: string;
}

export async function createApiKey(name: string): Promise<ApiKeyResponse> {
	return request('/auth/api-keys', {
		method: 'POST',
		body: JSON.stringify({ name, is_test: false })
	});
}

// ── Telemetry ──

export interface SessionSummary {
	session_id: string;
	start_time: string;
	end_time: string | null;
	duration_s: number | null;
	plugins_loaded: string[];
	skills_invoked: Record<string, number>;
	hooks_fired: Record<string, number>;
	autorouter_matches: number;
	autorouter_misses: number;
	total_tokens_in: number;
	total_tokens_out: number;
	estimated_cost_usd: number;
	tool_uses: Record<string, number>;
	compact_count: number;
	model: string | null;
	cost_usd: number | null;
	total_turns: number;
}

export interface SessionListResponse {
	sessions: SessionSummary[];
	total: number;
	page: number;
	per_page: number;
}

export interface MetricsSummary {
	period: string;
	from_date: string;
	to_date: string;
	total_sessions: number;
	total_tokens_in: number;
	total_tokens_out: number;
	total_cost_usd: number;
	avg_session_duration_s: number;
	autorouter_hit_rate: number;
	top_skills: { skill: string; count: number }[];
}

export interface TokenBucket {
	bucket: string;
	tokens_in: number;
	tokens_out: number;
}

export interface CostBucket {
	bucket: string;
	cost_usd: number;
	session_count: number;
}

export interface PluginMetric {
	plugin: string;
	session_count: number;
	avg_tokens_in: number;
	avg_tokens_out: number;
	avg_cost_usd: number;
	avg_duration_s: number;
}

export async function getSessions(page = 1, perPage = 20): Promise<SessionListResponse> {
	return request(`/telemetry/sessions?page=${page}&per_page=${perPage}`);
}

export async function getSession(id: string): Promise<SessionSummary & { event_count: number }> {
	return request(`/telemetry/sessions/${id}`);
}

export async function getMetricsSummary(
	period = 'week'
): Promise<MetricsSummary> {
	return request(`/telemetry/metrics/summary?period=${period}`);
}

export async function getTokenUsage(
	period = 'day'
): Promise<{ buckets: TokenBucket[]; period: string }> {
	return request(`/telemetry/metrics/tokens?period=${period}`);
}

export async function getCostOverTime(
	period = 'day'
): Promise<{ buckets: CostBucket[]; total_cost_usd: number; period: string }> {
	return request(`/telemetry/metrics/cost?period=${period}`);
}

export async function getPluginMetrics(): Promise<{
	plugins: PluginMetric[];
	period: string;
}> {
	return request('/telemetry/metrics/plugins');
}

// ── Events ──

export interface TelemetryEvent {
	id: string;
	event_type: string;
	timestamp: string;
	payload: Record<string, unknown>;
}

export interface EventListResponse {
	events: TelemetryEvent[];
	total: number;
	page: number;
	per_page: number;
}

export async function getSessionEvents(
	sessionId: string,
	page = 1,
	perPage = 200
): Promise<EventListResponse> {
	return request(`/telemetry/sessions/${sessionId}/events?page=${page}&per_page=${perPage}`);
}

export async function getSessionEventsStream(
	sessionId: string,
	after?: string,
	perPage = 1000
): Promise<EventListResponse> {
	let url = `/telemetry/sessions/${sessionId}/events/stream?per_page=${perPage}`;
	if (after) url += `&after=${encodeURIComponent(after)}`;
	return request(url);
}

// ── Health ──

export async function checkHealth(): Promise<boolean> {
	try {
		const res = await fetch('/healthz');
		return res.ok;
	} catch {
		return false;
	}
}
