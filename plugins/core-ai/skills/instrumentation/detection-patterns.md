# Detection Patterns Reference

Comprehensive reference for what the repo-analyzer scans, where to look, and what each signal means for instrumentation.

## File System Signals

### Language and Framework Detection

| Signal file | What to extract | What it means |
|------------|-----------------|---------------|
| `package.json` | `dependencies`, `devDependencies`, `scripts`, `type`, `engines` | Node.js/JS/TS project. Framework from deps (react, vue, svelte, express, fastify). Scripts reveal build/test/lint commands. |
| `tsconfig.json` / `jsconfig.json` | `compilerOptions.strict`, `paths`, `target`, `module` | TypeScript config. Path aliases affect import conventions. Strict mode signals code quality standards. |
| `Cargo.toml` | `[dependencies]`, `[workspace]`, `edition` | Rust project. Workspace = monorepo. Edition determines language features. |
| `go.mod` | `module`, `go` version, `require` | Go project. Module path reveals project structure. |
| `pyproject.toml` / `setup.py` / `setup.cfg` | `[tool.poetry]`, `[project]`, `[tool.setuptools]` | Python project. Tool section reveals package manager (poetry, setuptools, hatch). |
| `Gemfile` | `source`, `gem` entries | Ruby project. Gems reveal framework (rails, sinatra). |
| `*.csproj` / `*.sln` | `TargetFramework`, `PackageReference` | .NET project. Framework version and dependencies. |

### Build and Test Tools

| Signal file | What to extract | What it means |
|------------|-----------------|---------------|
| `Makefile` / `CMakeLists.txt` | Build targets, test targets | Build system. Targets reveal standard commands. |
| `jest.config.*` / `vitest.config.*` | `testMatch`, `collectCoverage`, `coverageThreshold` | JS test framework and coverage settings. |
| `pytest.ini` / `pyproject.toml [tool.pytest]` | `testpaths`, `addopts`, markers | Python test config and conventions. |
| `.mocharc.*` | Test runner config | Mocha test framework. |
| `cypress.config.*` / `playwright.config.*` | E2E test config | E2E testing framework and patterns. |

### Linting and Formatting

| Signal file | What to extract | What it means |
|------------|-----------------|---------------|
| `.eslintrc*` / `eslint.config.*` | Rules, extends, plugins | JS/TS linting rules. Extends reveals style (airbnb, standard, etc). |
| `.prettierrc*` | Format options | Code formatting preferences (tabs vs spaces, semicolons, quotes). |
| `rustfmt.toml` | Format options | Rust formatting preferences. |
| `.clang-format` | Format options | C/C++ formatting preferences. |
| `.editorconfig` | Indent style/size, charset | Cross-editor formatting baseline. |
| `biome.json` | Linter + formatter config | Biome (Rust-based JS/TS toolchain). |

### CI/CD System

| Signal file | What to extract | What it means |
|------------|-----------------|---------------|
| `.github/workflows/*.yml` | Jobs, steps, triggers, env vars | GitHub Actions. Workflow names reveal process (test, build, deploy, release). |
| `.gitlab-ci.yml` | Stages, jobs | GitLab CI. |
| `Jenkinsfile` | Pipeline stages | Jenkins CI. |
| `.circleci/config.yml` | Jobs, workflows | CircleCI. |
| `.travis.yml` | Language, script | Travis CI. |

### Container and Environment

| Signal file | What to extract | What it means |
|------------|-----------------|---------------|
| `Dockerfile` | Base image, stages | Containerized deployment. Multi-stage = production build pattern. |
| `.devcontainer/devcontainer.json` | Features, extensions, ports | Dev container setup. Reveals standard dev environment. |
| `docker-compose.yml` | Services, volumes, networks | Multi-service architecture. Service names reveal dependencies. |

### Monorepo Tooling

| Signal file | What to extract | What it means |
|------------|-----------------|---------------|
| `nx.json` | `targetDefaults`, `defaultBase`, `namedInputs` | Nx monorepo. Target defaults reveal build conventions. |
| `turbo.json` | `pipeline`, `globalDependencies` | Turborepo monorepo. |
| `pnpm-workspace.yaml` | `packages` globs | pnpm workspace (may or may not use Nx/Turbo). |
| `lerna.json` | `packages`, `version` | Lerna monorepo (legacy but still common). |

### Package Manager Detection

| Signal file | Package manager |
|------------|----------------|
| `pnpm-lock.yaml` | pnpm |
| `yarn.lock` | yarn |
| `package-lock.json` | npm |
| `bun.lockb` / `bun.lock` | bun |
| `Cargo.lock` | cargo |
| `poetry.lock` | poetry |
| `Pipfile.lock` | pipenv |
| `go.sum` | go modules |
| `Gemfile.lock` | bundler |

### Existing AI Configuration

| Signal file | What it means |
|------------|---------------|
| `.claude/rules/*.md` | Existing Claude Code rules — parse for coverage analysis |
| `.claude/commands/*.md` | Existing Claude Code commands |
| `.claude/hooks.json` | Existing Claude Code hooks |
| `CLAUDE.md` | Main Claude Code instruction file |
| `.cursor/rules/*.mdc` | Cursor rules — indicates multi-tool usage |
| `AGENTS.md` | Cross-tool agent instructions |
| `.github/copilot-instructions.md` | Copilot configuration |

## Git History Signals

### Commit Message Patterns

Analyze the last 50 commits using `git log --oneline -50`:

| Pattern | Signal |
|---------|--------|
| `feat:`, `fix:`, `chore:`, `docs:` prefixes | Conventional Commits adopted |
| `[PROJ-123]` prefixes | Jira/issue tracker integration |
| Mixed formats | No commit convention enforced |
| Co-author trailers | Pair programming or AI-assisted |

### Branch Naming

Analyze branches using `git branch -a --format='%(refname:short)'`:

| Pattern | Signal |
|---------|--------|
| `feature/`, `feat/`, `fix/`, `chore/` | Branch naming convention enforced |
| `release/vX.Y.Z` | Release branch workflow |
| Only `main`/`master` | Trunk-based development or solo project |

### Merge Strategy

Analyze merge history using `git log --merges --oneline -20`:

| Pattern | Signal |
|---------|--------|
| "Squash and merge" / single-commit merges | Squash merge strategy |
| Merge commits with two parents | Merge commit strategy |
| Linear history (no merges) | Rebase strategy |

### Tag Patterns

Analyze tags using `git tag --sort=-creatordate | head -10`:

| Pattern | Signal |
|---------|--------|
| `v1.2.3`, `v0.1.0` | Semantic versioning |
| `2026.02.1` | Calendar versioning |
| No tags | No release process or informal releases |

## Code Structure Signals

### Directory Layout

| Pattern | Signal |
|---------|--------|
| `src/` flat | Simple single-package project |
| `src/components/`, `src/pages/`, `src/lib/` | Frontend SPA structure |
| `apps/`, `libs/`, `packages/` | Monorepo with domain separation |
| `cmd/`, `internal/`, `pkg/` | Go project structure |
| `tests/` separate directory | Tests separate from source |
| `*.test.*` / `*.spec.*` next to source | Co-located test files |

### Import Patterns

| Pattern | Signal |
|---------|--------|
| `@/` or `~/` path aliases | Path aliases configured (check tsconfig) |
| `../../../` deep relative imports | No path aliases — candidate for rule |
| Barrel files (`index.ts` re-exports) | Module boundary pattern |
