# Project Scaffolding Reference — Complete Configuration Templates

## svelte.config.js Templates per Target

### Web (SSR / Vercel / Cloudflare)

```javascript
// svelte.config.js
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import adapter from '@sveltejs/adapter-auto';

/** @type {import('@sveltejs/kit').Config} */
export default {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter(),

    alias: {
      $components: 'src/lib/components',
      $server:     'src/lib/server',
      $utils:      'src/lib/utils',
      $types:      'src/lib/types',
      $stores:     'src/lib/stores',
    },

    env: {
      dir:    process.cwd(),
      publicPrefix: 'PUBLIC_',
    }
  }
};
```

### Static Site (GitHub Pages, S3, Netlify CDN)

```javascript
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: undefined,
      precompress: true,
      strict: true,
    }),
    prerender: {
      crawl: true,
      entries: ['*'],
    },
    paths: {
      // Required if not deploying to domain root (e.g., GitHub Pages subdirectory)
      // base: '/my-repo',
    }
  }
};
```

### Tauri 2 / Electron (Desktop SPA)

```javascript
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter({
      fallback: '200.html',  // SPA routing fallback
      precompress: false,    // Desktop app handles no compression
    })
  }
};
```

```typescript
// src/routes/+layout.ts
export const ssr = false;
export const prerender = false;
```

## tsconfig.json (Strict TypeScript)

```json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "sourceMap": true,

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,

    "target": "ESNext",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "verbatimModuleSyntax": true,

    "paths": {
      "$lib": ["./src/lib"],
      "$lib/*": ["./src/lib/*"],
      "$components": ["./src/lib/components"],
      "$components/*": ["./src/lib/components/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.svelte", "tests/**/*.ts"]
}
```

## tailwind.config.ts

```typescript
import type { Config } from 'tailwindcss';
import { fontFamily } from 'tailwindcss/defaultTheme';

export default {
  content: [
    './src/**/*.{html,js,svelte,ts}',
  ],

  darkMode: 'class',  // 'media' for OS preference, 'class' for manual toggle

  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter Variable', ...fontFamily.sans],
        mono: ['JetBrains Mono Variable', ...fontFamily.mono],
      },

      colors: {
        // Use CSS custom properties for runtime theming
        primary: {
          50:  'hsl(var(--color-primary-50) / <alpha-value>)',
          100: 'hsl(var(--color-primary-100) / <alpha-value>)',
          500: 'hsl(var(--color-primary-500) / <alpha-value>)',
          600: 'hsl(var(--color-primary-600) / <alpha-value>)',
          900: 'hsl(var(--color-primary-900) / <alpha-value>)',
        },
        surface: {
          50:  'hsl(var(--color-surface-50) / <alpha-value>)',
          100: 'hsl(var(--color-surface-100) / <alpha-value>)',
          200: 'hsl(var(--color-surface-200) / <alpha-value>)',
          700: 'hsl(var(--color-surface-700) / <alpha-value>)',
          800: 'hsl(var(--color-surface-800) / <alpha-value>)',
          900: 'hsl(var(--color-surface-900) / <alpha-value>)',
        },
      },

      borderRadius: {
        card: 'var(--radius-card)',
        input: 'var(--radius-input)',
      }
    }
  },

  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ]
} satisfies Config;
```

## CSS Custom Properties (Design Tokens)

```css
/* src/app.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  /* Primary brand color (HSL without hsl() wrapper for Tailwind opacity) */
  --color-primary-50:  216 100% 97%;
  --color-primary-100: 216 100% 93%;
  --color-primary-500: 216 100% 54%;
  --color-primary-600: 216 100% 45%;
  --color-primary-900: 216 100% 13%;

  /* Neutral surface colors */
  --color-surface-50:  0 0% 98%;
  --color-surface-100: 0 0% 95%;
  --color-surface-200: 0 0% 90%;
  --color-surface-700: 0 0% 35%;
  --color-surface-800: 0 0% 20%;
  --color-surface-900: 0 0% 10%;

  /* Component tokens */
  --radius-card:  0.75rem;
  --radius-input: 0.375rem;
}

.dark {
  --color-surface-50:  222 22% 10%;
  --color-surface-100: 222 22% 14%;
  --color-surface-200: 222 22% 18%;
  --color-surface-700: 222 22% 65%;
  --color-surface-800: 222 22% 80%;
  --color-surface-900: 222 22% 95%;
}
```

## ESLint Configuration

```javascript
// eslint.config.js
import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import ts from 'typescript-eslint';

export default ts.config(
  js.configs.recommended,
  ...ts.configs.strictTypeChecked,
  ...svelte.configs['flat/recommended'],
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
        extraFileExtensions: ['.svelte'],
      }
    },
  },
  {
    files: ['**/*.svelte', '**/*.svelte.ts'],
    languageOptions: {
      parserOptions: {
        parser: ts.parser,
      }
    }
  },
  {
    rules: {
      // Disallow any type
      '@typescript-eslint/no-explicit-any': 'error',
      // Require explicit return types on exported functions
      '@typescript-eslint/explicit-module-boundary-types': 'error',
      // Prefer const
      'prefer-const': 'error',
      // No unused variables
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    }
  },
  {
    ignores: ['build/', '.svelte-kit/', 'dist/']
  }
);
```

## Prettier Configuration

```json
{
  "useTabs": false,
  "tabWidth": 2,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "semi": true,
  "plugins": ["prettier-plugin-svelte", "prettier-plugin-tailwindcss"],
  "overrides": [
    {
      "files": "*.svelte",
      "options": { "parser": "svelte" }
    }
  ]
}
```

## .env.example Template

```bash
# .env.example — commit this, never .env

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/mydb"

# Auth
AUTH_SECRET="generate-with: openssl rand -base64 32"
GITHUB_CLIENT_ID=""
GITHUB_CLIENT_SECRET=""

# Public (safe for client)
PUBLIC_APP_URL="http://localhost:5173"
PUBLIC_API_BASE="http://localhost:5173/api"

# Optional: analytics
# PUBLIC_POSTHOG_KEY=""
# PUBLIC_POSTHOG_HOST="https://app.posthog.com"
```

## Vitest Unit Testing Setup

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ['src/**/*.{test,spec}.{js,ts}'],
    environment: 'jsdom',
    globals: true,
    setupFiles: ['src/tests/setup.ts'],
    coverage: {
      reporter: ['text', 'html'],
      include: ['src/lib/**'],
      exclude: ['src/lib/**/*.test.ts', 'src/lib/**/*.spec.ts'],
    }
  }
});
```

```typescript
// src/tests/setup.ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/svelte';
import { afterEach } from 'vitest';

afterEach(cleanup);
```

## Playwright E2E Setup

```typescript
// playwright.config.ts
import type { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  webServer: {
    command: 'pnpm build && pnpm preview',
    port: 4173,
    reuseExistingServer: !process.env.CI,
  },
  testDir: 'tests/e2e',
  testMatch: /(.+\.)?(test|spec)\.[jt]s/,
  use: {
    baseURL: 'http://localhost:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } },
  ]
};

export default config;
```

## .gitignore Template

```gitignore
# Build outputs
build/
.svelte-kit/
dist/

# Dependencies
node_modules/

# Environment variables (never commit)
.env
.env.local
.env.*.local

# Logs
*.log
npm-debug.log*
pnpm-debug.log*

# Editor
.vscode/*
!.vscode/extensions.json
!.vscode/settings.json
.idea/
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# OS
.DS_Store
Thumbs.db

# Type generation (auto-generated by SvelteKit)
# Note: .svelte-kit/tsconfig.json and types are needed for the IDE
# but the build outputs are gitignored above

# Test outputs
test-results/
playwright-report/
coverage/
stats.html
```
