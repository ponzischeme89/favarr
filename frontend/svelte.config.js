import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const isSvelteCheck = process.env.SVELTE_CHECK === 'true';

export default {
  // Skip Vite preprocessing when running svelte-check to avoid esbuild spawn on Windows.
  preprocess: isSvelteCheck ? [] : vitePreprocess()
};
