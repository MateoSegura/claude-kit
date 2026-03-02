import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		proxy: {
			'/api': {
				target: process.env.API_URL || 'http://172.17.0.1:8000',
				changeOrigin: true
			},
			'/healthz': {
				target: process.env.API_URL || 'http://172.17.0.1:8000',
				changeOrigin: true
			}
		}
	}
});
