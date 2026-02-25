# Build Errors — SvelteKit / Vite

Patterns for diagnosing Vite plugin errors, adapter configuration mistakes, dependency resolution failures, and circular import issues.

---

## Vite Plugin Ordering

### Symptom: Svelte component transforms fail / unexpected token errors

**Cause**: A Vite plugin that transforms `.svelte` files (e.g., a PostCSS plugin, a custom transform) is ordered before `@sveltejs/vite-plugin-svelte`, intercepting `.svelte` files before the Svelte compiler processes them.

**Diagnosis**: Check `vite.config.ts` plugin array order.

**Fix**: Ensure `@sveltejs/vite-plugin-svelte` is listed before other transform plugins:

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [
    sveltekit(),      // FIRST: handles .svelte compilation
    // other plugins after
  ]
});
```

---

### Symptom: "Plugin 'vite-plugin-X' failed to resolve"

**Cause**: Plugin listed in `vite.config.ts` is not installed, or is installed in the wrong dependency group (e.g., `dependencies` instead of `devDependencies` in a Node environment that does not bundle `devDependencies`).

**Fix**:
```bash
npm install --save-dev vite-plugin-x
# or
npm install vite-plugin-x  # if needed at runtime
```

---

## Adapter Configuration Mistakes

### Symptom: Build succeeds but deployed app returns 404 or 500 for all routes

**Cause**: Wrong adapter imported in `svelte.config.js` for the deployment target.

| Deployment | Correct Adapter | Common Mistake |
|-----------|----------------|----------------|
| Node.js server | `@sveltejs/adapter-node` | Using adapter-auto with misconfigured env |
| Static/CDN | `@sveltejs/adapter-static` | Using adapter-node (generates server files) |
| Vercel | `@sveltejs/adapter-vercel` | Using adapter-node (wrong output structure) |
| Cloudflare Pages | `@sveltejs/adapter-cloudflare` | Using adapter-static (no edge functions) |

**Diagnosis**:
```bash
# Check what adapter is configured
grep 'adapter' svelte.config.js

# Check what files are in the build output
ls -la build/
```

---

### Symptom: adapter-static build fails for page with `+page.server.ts`

**Cause**: `adapter-static` cannot generate pages that require a server at request time. Pages with `+page.server.ts`, form actions, or API routes cannot be prerendered.

**Fix**:
1. Move server logic to a separate API service, OR
2. Set `prerender = false` for that specific route and use `fallback` for SPA routing, OR
3. Switch to `adapter-node` if server-rendered routes are required

---

## Dependency Resolution Failures

### Symptom: "Cannot find module 'X'" at build time (but it exists in node_modules)

**Cause A — Package exports misconfiguration**: The package has a `"exports"` field in its `package.json` that doesn't include a path matching the import.

**Cause B — Missing `ssr.noExternal`**: Some packages that use ES module syntax are not pre-bundled for SSR and fail at runtime.

**Fix for Cause B** (`vite.config.ts`):
```typescript
export default defineConfig({
  ssr: {
    noExternal: ['problematic-package-name']
  }
});
```

---

### Symptom: "ERR_PACKAGE_PATH_NOT_EXPORTED"

**Cause**: Importing a subpath from a package that has strict `exports` map and the subpath is not exported.

**Diagnostic**: Read the package's `package.json` → `"exports"` field to see what paths are available.

**Fix**: Either import from a path listed in `exports`, or open an issue with the package maintainer to export the needed subpath.

---

### Symptom: "[vite] ✨ optimized dependencies changed. reloading" on every save

**Cause**: A dependency's imports are being discovered incrementally rather than all at once. Common with large libraries that use dynamic imports.

**Fix** (`vite.config.ts`):
```typescript
export default defineConfig({
  optimizeDeps: {
    include: [
      'large-library',
      'large-library/submodule'  // explicitly include known submodules
    ]
  }
});
```

---

## Circular Dependencies

### Symptom: Module fails to initialize / variable is `undefined` at import time

**Cause**: Two or more modules import from each other, creating a cycle. In ESM, the module that is imported first in the cycle may receive an incomplete (partially-initialized) version of the other module's exports.

**Diagnostic**:
```bash
# Install detection tool
npm install --save-dev vite-plugin-circular-dependency

# Or use madge (static analysis)
npx madge --circular src/
```

---

### Symptom: SvelteKit dev server freezes on save

**Cause**: HMR (Hot Module Replacement) detected a circular dependency and is caught in an infinite reload loop.

**Diagnostic**: Run `vite --debug hmr` to log the cycle path.

**Fix — Break the cycle**:
```typescript
// Before: A imports B, B imports A
// a.ts
import { bValue } from './b.ts';

// b.ts
import { aValue } from './a.ts';

// After: extract shared types to a third module
// shared.ts
export type SharedType = { ... };

// a.ts — imports from shared only
import type { SharedType } from './shared.ts';

// b.ts — imports from shared only
import type { SharedType } from './shared.ts';
```

Use `import type` for type-only imports — Vite ignores these in HMR analysis.

---

## TypeScript / tsconfig Build Errors

### Symptom: Build fails with TS errors that dev mode ignores

**Cause**: Vite dev mode does not type-check (it transpiles only). `vite build` runs Rollup, which may surface type errors if `tsc` is part of the build pipeline.

**Diagnosis**: Run `npx tsc --noEmit` separately to check TypeScript errors before building.

**Fix**: Add to build script to catch TS errors early:
```json
{
  "scripts": {
    "check": "svelte-check --tsconfig ./tsconfig.json",
    "build": "npm run check && vite build"
  }
}
```

---

## Build Error Quick Reference

| Error Pattern | Domain | First Check |
|--------------|--------|-------------|
| `Unexpected token` in `.svelte` | Plugin ordering | `vite.config.ts` plugin array |
| `Cannot find module` (node_modules exists) | Dependency | Package `exports` field, `ssr.noExternal` |
| `ERR_PACKAGE_PATH_NOT_EXPORTED` | Dependency | Package's `exports` in `package.json` |
| `[vite] circular dependency` | Circular dep | `madge --circular src/` output |
| Adapter 404 in production | Adapter config | `svelte.config.js` adapter selection |
| TS errors in build only | TypeScript | Run `npx tsc --noEmit` |
