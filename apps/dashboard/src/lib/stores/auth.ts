/** Reactive auth state for the dashboard. */
import { writable, derived } from 'svelte/store';
import { getMe, type UserResponse } from '$lib/api';

export const user = writable<UserResponse | null>(null);
export const isAuthenticated = derived(user, ($u) => $u !== null);
export const loading = writable(true);

export async function initAuth(): Promise<void> {
	const token = localStorage.getItem('ck_token');
	if (!token) {
		loading.set(false);
		return;
	}
	try {
		const me = await getMe();
		user.set(me);
	} catch {
		localStorage.removeItem('ck_token');
		localStorage.removeItem('ck_refresh');
	} finally {
		loading.set(false);
	}
}

export function setTokens(access: string, refresh: string): void {
	localStorage.setItem('ck_token', access);
	localStorage.setItem('ck_refresh', refresh);
}

export function logout(): void {
	localStorage.removeItem('ck_token');
	localStorage.removeItem('ck_refresh');
	user.set(null);
}
