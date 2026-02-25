---
name: frontend-svelte-engineer:project-scaffolding
description: "Project and module scaffolding patterns for SvelteKit. Covers src/lib directory structure, file naming conventions (+ prefix SvelteKit files), route organization (groups, parameters, optional/rest), component library layout, and module scaffolding checklists. Load this when creating a new project, adding routes, or organizing a component library."
user-invocable: false
---

# Project Scaffolding — SvelteKit Structure Templates

Quick reference for directory layout, file naming, and route organization. See [reference.md](reference.md) for complete svelte.config.js templates, tsconfig, Tailwind config, ESLint/Prettier, Docker, and testing setup per deployment target.

## Standard Project Structure

```
src/
├── app.html                    # HTML shell (edit carefully)
├── app.css                     # Global CSS, @font-face, CSS custom properties
├── app.d.ts                    # App-wide TypeScript types (App namespace)
├── lib/
│   ├── components/
│   │   ├── ui/                 # Primitive UI components (Button, Input, Modal)
│   │   ├── layout/             # Layout components (Header, Sidebar, Footer)
│   │   └── forms/              # Form-specific components (Field, Select, Datepicker)
│   ├── server/                 # Server-only modules (never imported client-side)
│   │   ├── db/                 # Database clients and queries
│   │   └── auth/               # Authentication logic
│   ├── stores/                 # Module-level $state singletons (*.svelte.ts)
│   ├── utils/                  # Pure utility functions
│   ├── types/                  # Shared TypeScript types/interfaces
│   └── index.ts                # Barrel export for public $lib API
├── routes/
│   ├── +layout.svelte          # Root layout (applies to all routes)
│   ├── +layout.ts              # Universal root load (runs client + server)
│   ├── +layout.server.ts       # Server-only root load (cookies, auth)
│   ├── +error.svelte           # Root error boundary
│   └── [route-dirs]/
static/
│   ├── fonts/                  # Web fonts
│   ├── icons/                  # Favicon variants
│   └── images/                 # Static images not processed by Vite
```

## SvelteKit File Naming Conventions

| File | Purpose | Server/Client |
|------|---------|---------------|
| `+page.svelte` | Page component | Client |
| `+page.ts` | Universal page load | Both |
| `+page.server.ts` | Server-only page load + form actions | Server only |
| `+layout.svelte` | Layout component for route group | Client |
| `+layout.ts` | Universal layout load | Both |
| `+layout.server.ts` | Server-only layout load | Server only |
| `+error.svelte` | Error boundary for route group | Client |
| `+server.ts` | API endpoint (GET/POST/PUT/DELETE) | Server only |

**Rule**: If the file accesses DB, cookies, or secrets — use `+page.server.ts` (not `+page.ts`). If it needs to run on client for interactivity — use `+page.ts`.

## Route Organization Patterns

```
src/routes/
├── +layout.svelte              # Root layout (nav, footer)
│
├── (marketing)/                # Group: shared layout, no URL segment
│   ├── +layout.svelte          # Marketing-specific layout (hero, CTAs)
│   ├── +page.svelte            # Homepage (/)
│   ├── about/
│   │   └── +page.svelte        # /about
│   └── pricing/
│       └── +page.svelte        # /pricing
│
├── (app)/                      # Group: auth-gated app layout
│   ├── +layout.server.ts       # Auth check: redirect if not logged in
│   ├── +layout.svelte          # App shell (sidebar, topbar)
│   ├── dashboard/
│   │   └── +page.svelte        # /dashboard
│   └── settings/
│       ├── +page.svelte        # /settings
│       ├── profile/
│       │   └── +page.svelte    # /settings/profile
│       └── billing/
│           └── +page.svelte    # /settings/billing
│
├── blog/
│   ├── +page.svelte            # /blog (list)
│   └── [slug]/                 # Dynamic: /blog/my-post
│       └── +page.svelte
│
├── products/
│   ├── [id]/                   # Required param: /products/123
│   │   └── +page.svelte
│   └── [[category]]/           # Optional param: /products or /products/shoes
│       └── +page.svelte
│
├── api/
│   ├── auth/
│   │   └── +server.ts          # POST /api/auth
│   └── products/
│       ├── +server.ts          # GET/POST /api/products
│       └── [id]/
│           └── +server.ts      # GET/PUT/DELETE /api/products/[id]
│
└── [...path]/                  # Catch-all: matches any unmatched path
    └── +page.svelte
```

## Route Parameter Types

| Pattern | Example URL | `params` value |
|---------|-------------|----------------|
| `[id]` | `/users/42` | `{ id: '42' }` |
| `[[optional]]` | `/items` or `/items/shirts` | `{ optional: undefined }` or `{ optional: 'shirts' }` |
| `[...rest]` | `/docs/a/b/c` | `{ rest: 'a/b/c' }` |
| `(group)` | `/about` (not `/group/about`) | Route grouping only, no param |

## Component Library Structure

```
src/lib/components/
├── ui/                         # Primitive design system components
│   ├── Button.svelte           # Props: variant, size, disabled, onclick
│   ├── Input.svelte            # Props: value (bindable), type, label, error
│   ├── Modal.svelte            # Props: open (bindable), title, onclose
│   ├── Badge.svelte
│   ├── Card.svelte
│   ├── Spinner.svelte
│   └── index.ts                # Re-export all UI components
│
├── layout/                     # App structure components
│   ├── Header.svelte
│   ├── Sidebar.svelte
│   ├── Footer.svelte
│   └── PageContainer.svelte
│
├── forms/                      # Form-specific components
│   ├── FormField.svelte        # Label + Input + Error wrapper
│   ├── Select.svelte
│   ├── Combobox.svelte
│   └── Datepicker.svelte
│
└── [feature]/                  # Feature-specific components
    └── ProductCard.svelte      # Grouped by domain, not type
```

## Module Scaffolding Checklist

When adding a new feature module, create these files:

```
src/routes/(app)/[feature]/
├── +page.svelte               # UI: list/index view
├── +page.ts                   # Universal load (or +page.server.ts if auth/DB)
├── [id]/
│   ├── +page.svelte           # UI: detail view
│   └── +page.server.ts        # Server load + form actions
└── new/
    ├── +page.svelte           # UI: create form
    └── +page.server.ts        # Form action: POST to create

src/lib/components/[feature]/
├── [Feature]Card.svelte       # Display component
└── [Feature]Form.svelte       # Form component

src/lib/server/[feature]/
└── queries.ts                 # DB queries, no HTTP (server-only)

src/lib/types/
└── [feature].ts               # TypeScript interfaces for this feature
```

## New Project Initialization

```bash
# Create project
pnpm create svelte@latest my-app
# Choose: SvelteKit (full)
# TypeScript: Yes
# ESLint: Yes
# Prettier: Yes
# Playwright: Yes (e2e tests)
# Vitest: Yes (unit tests)

cd my-app
pnpm install

# Add Tailwind
pnpm add -D tailwindcss postcss autoprefixer
pnpm tailwindcss init -p

# Add enhanced image support
pnpm add -D @sveltejs/enhanced-img

# Add web-vitals for monitoring
pnpm add web-vitals
```

## Additional Resources

- [reference.md](reference.md) — Complete config templates for each deployment target (svelte.config.js, tsconfig.json, tailwind.config.ts, vite.config.ts, ESLint config, .env.example), testing infrastructure (Vitest, Playwright), and Docker configs
