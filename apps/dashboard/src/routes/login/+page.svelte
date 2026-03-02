<script lang="ts">
	import '../../app.css';
	import { login, register } from '$lib/api';
	import { setTokens, initAuth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { fly, scale } from 'svelte/transition';

	let mode: 'login' | 'register' = $state('login');
	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let error = $state('');
	let submitting = $state(false);

	async function handleSubmit() {
		error = '';
		submitting = true;
		try {
			const res =
				mode === 'login'
					? await login(email, password)
					: await register(email, password, displayName || undefined);
			setTokens(res.access_token, res.refresh_token);
			await initAuth();
			goto('/');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Something went wrong';
		} finally {
			submitting = false;
		}
	}
</script>

<div class="relative flex min-h-screen items-center justify-center overflow-hidden" style="background: var(--color-bg)">
	<!-- Aurora orbs -->
	<div
		class="pointer-events-none fixed rounded-full"
		style="width: 500px; height: 500px; top: -150px; right: -100px; background: var(--color-aurora-teal); filter: blur(140px); opacity: 0.1; animation: aurora-drift 20s ease-in-out infinite"
	></div>
	<div
		class="pointer-events-none fixed rounded-full"
		style="width: 400px; height: 400px; bottom: -100px; left: -80px; background: var(--color-aurora-violet); filter: blur(140px); opacity: 0.08; animation: aurora-drift 20s ease-in-out infinite; animation-delay: -7s"
	></div>
	<div
		class="pointer-events-none fixed rounded-full"
		style="width: 300px; height: 300px; top: 50%; left: 60%; background: var(--color-aurora-rose); filter: blur(140px); opacity: 0.06; animation: aurora-drift 20s ease-in-out infinite; animation-delay: -14s"
	></div>

	<div class="relative z-10 w-full max-w-sm">
		<!-- Logo -->
		<div class="mb-10 text-center" in:scale={{ duration: 600, start: 0.8 }}>
			<div
				class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl text-lg font-bold text-white"
				style="background: linear-gradient(135deg, var(--color-aurora-teal), var(--color-aurora-violet))"
			>
				ck
			</div>
			<h1
				class="text-xl text-aurora"
				style="font-family: var(--font-display)"
			>
				claude-kit
			</h1>
			<p class="mt-1 text-sm" style="color: var(--color-text-muted)">Telemetry Dashboard</p>
		</div>

		<!-- Card -->
		<div class="glass-card p-8" in:fly={{ y: 30, duration: 500, delay: 200 }}>
			<!-- Tabs -->
			<div class="mb-6 flex gap-1 rounded-lg p-1" style="background: rgba(255, 255, 255, 0.04)">
				<button
					class="flex-1 cursor-pointer rounded-md py-2 text-[13px] font-medium transition-all"
					style="background: {mode === 'login'
						? 'rgba(255, 255, 255, 0.08)'
						: 'transparent'}; color: {mode === 'login'
						? 'var(--color-text)'
						: 'var(--color-text-muted)'}"
					onclick={() => (mode = 'login')}
				>
					Sign in
				</button>
				<button
					class="flex-1 cursor-pointer rounded-md py-2 text-[13px] font-medium transition-all"
					style="background: {mode === 'register'
						? 'rgba(255, 255, 255, 0.08)'
						: 'transparent'}; color: {mode === 'register'
						? 'var(--color-text)'
						: 'var(--color-text-muted)'}"
					onclick={() => (mode = 'register')}
				>
					Create account
				</button>
			</div>

			<form onsubmit={handleSubmit} class="space-y-4">
				{#if mode === 'register'}
					<div>
						<label for="name" class="mb-1.5 block text-xs font-medium" style="color: var(--color-text-secondary)">
							Name
						</label>
						<input
							id="name"
							type="text"
							bind:value={displayName}
							placeholder="Your name"
							class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
						/>
					</div>
				{/if}

				<div>
					<label for="email" class="mb-1.5 block text-xs font-medium" style="color: var(--color-text-secondary)">
						Email
					</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						placeholder="you@company.com"
						required
						class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
					/>
				</div>

				<div>
					<label for="password" class="mb-1.5 block text-xs font-medium" style="color: var(--color-text-secondary)">
						Password
					</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						placeholder="••••••••"
						required
						minlength="8"
						class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
					/>
				</div>

				{#if error}
					<div
						class="rounded-lg px-3 py-2 text-xs font-medium"
						style="background: var(--color-error-light); color: var(--color-error)"
					>
						{error}
					</div>
				{/if}

				<button
					type="submit"
					disabled={submitting}
					class="w-full cursor-pointer rounded-lg py-2.5 text-sm font-semibold text-white transition-colors disabled:opacity-50"
					style="background: linear-gradient(135deg, var(--color-aurora-teal), var(--color-aurora-violet))"
				>
					{submitting ? '…' : mode === 'login' ? 'Sign in' : 'Create account'}
				</button>
			</form>
		</div>

		<p class="mt-6 text-center text-xs" style="color: var(--color-text-muted)">
			Telemetry data stays local until you opt in.
		</p>
	</div>
</div>
