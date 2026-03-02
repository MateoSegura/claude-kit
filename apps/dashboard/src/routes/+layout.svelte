<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { initAuth, user, isAuthenticated, logout, loading } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';

	let { children } = $props();

	onMount(() => {
		initAuth();
	});

	$effect(() => {
		if (!$loading && !$isAuthenticated && $page.url.pathname !== '/login') {
			goto('/login');
		}
	});

	function handleLogout() {
		logout();
		goto('/login');
	}

	const navItems = [
		{ href: '/', label: 'Overview', icon: '◎' },
		{ href: '/sessions', label: 'Sessions', icon: '▤' },
		{ href: '/settings', label: 'Settings', icon: '⚙' }
	];
</script>

{#if $loading}
	<div class="flex items-center justify-center min-h-screen" transition:fade={{ duration: 300 }}>
		<div class="text-sm tracking-wide animate-pulse" style="color: var(--color-text-muted)">Loading…</div>
	</div>
{:else if !$isAuthenticated && $page.url.pathname !== '/login'}
	<!-- Redirect handled by effect -->
{:else if $page.url.pathname === '/login'}
	{@render children()}
{:else}
	<div class="aurora-bg min-h-screen">
		<!-- Top bar -->
		<header
			class="sticky top-0 z-50 border-b backdrop-blur-xl"
			style="background: rgba(10, 14, 26, 0.8); border-color: var(--color-border)"
		>
			<div class="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
				<div class="flex items-center gap-8">
					<!-- Logo -->
					<a href="/" class="flex items-center gap-2.5 no-underline">
						<div
							class="flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold text-white"
							style="background: linear-gradient(135deg, var(--color-aurora-teal), var(--color-aurora-violet))"
						>
							ck
						</div>
						<span
							class="text-sm font-semibold"
							style="font-family: var(--font-display); color: var(--color-text)"
						>
							claude-kit
						</span>
					</a>

					<!-- Nav -->
					<nav class="flex gap-1">
						{#each navItems as item}
							<a
								href={item.href}
								class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[13px] font-medium no-underline transition-all"
								style="color: {$page.url.pathname === item.href
									? 'var(--color-aurora-teal)'
									: 'var(--color-text-secondary)'}; background: {$page.url.pathname === item.href
									? 'rgba(20, 184, 166, 0.1)'
									: 'transparent'}; {$page.url.pathname === item.href
									? 'box-shadow: 0 0 12px rgba(20, 184, 166, 0.15)'
									: ''}"
							>
								<span class="text-xs">{item.icon}</span>
								{item.label}
							</a>
						{/each}
					</nav>
				</div>

				<div class="flex items-center gap-4">
					{#if $user}
						<span class="text-xs" style="color: var(--color-text-muted)">
							{$user.email}
						</span>
					{/if}
					<button
						onclick={handleLogout}
						class="cursor-pointer rounded-md border px-3 py-1 text-xs font-medium transition-colors hover:bg-white/5"
						style="border-color: var(--color-border); color: var(--color-text-secondary); background: transparent"
					>
						Sign out
					</button>
				</div>
			</div>
		</header>

		<!-- Main content -->
		<main class="relative z-10 mx-auto max-w-7xl px-6 py-8">
			{@render children()}
		</main>
	</div>
{/if}
