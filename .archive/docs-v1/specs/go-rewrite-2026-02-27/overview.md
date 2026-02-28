# claude-kit Go Rewrite — Full Product Architecture

## Context

**Original request:** Ground-up redesign of claude-kit from a Python CLI launcher into a full commercial Go product. Includes: Go CLI binary, Go backend API, SvelteKit web dashboard, user authentication (accounts + API keys), telemetry pipeline (usage tracking, error reporting, conversation upload), autonomous mode (ghost-driving Claude's terminal via PTY with Bubble Tea TUI), encrypted binary distribution via GoReleaser (alpha/beta/stable channels), Kubernetes deployment with IaC in the monorepo, and comprehensive testing/benchmarking infrastructure.

**Conversation state:** The current claude-kit is a single-file Python CLI (~1,800 lines) that decrypts plugins, resolves companions/domains, assembles `claude --plugin-dir` arguments, and `os.execvp`s into Claude Code. A prior research session evaluated Python, Go, Rust, TypeScript, and hybrid approaches. Go was selected for: best terminal UI ecosystem (Charm/Bubble Tea), native PTY support with goroutines, single static binary, GoReleaser distribution, and reasonable IP protection via garble obfuscation.

**Key decisions made:**
- Monorepo structure with `apps/`, `deploy/`, `tools/`, `docs/` top-level directories
- SvelteKit + TypeScript for the web dashboard (leveraging existing frontend-svelte team plugin)
- Kubernetes deployment with infrastructure-as-code in the repo
- PTY driver approach for autonomous mode (spawn Claude in pseudo-terminal, read/inject)

## Requirements

- **R1**: Single Go binary replaces the Python CLI with all existing subcommands (`list`, `update`, `validate`, `setup`, `restore`, `debug`, `feedback`, `version`, `uninstall`, `help`) and launch modes (`--kit`, `--plugin`), producing identical plugin loading behavior
- **R2**: Plugin system in Go — prefix expansion, companion resolution, domain auto-loading, deduplication, and ordering — produces identical plugin sets to the current Python implementation
- **R3**: AES-256-CBC plugin encryption/decryption using Go's `crypto/aes` and `crypto/cipher` stdlib packages, eliminating the `openssl` runtime dependency; decrypted plugins exist only in memory-backed filesystems (tmpfs on Linux, RAM disk on macOS, ACL-protected temp on Windows) with automatic cleanup on process exit
- **R4**: Cross-platform binary distribution via GoReleaser — macOS (arm64, amd64), Linux (arm64, amd64), Windows (amd64) — with Homebrew tap, Scoop manifest, and direct binary downloads
- **R5**: Pre-release channels — alpha, beta, RC, stable — with separate Homebrew taps (`tap-unstable`, `tap`) and clear upgrade paths between channels
- **R6**: CLI self-update mechanism that checks for and installs new versions without requiring external tools (`gh`, `curl`)
- **R7**: User authentication — account creation, email/password login, JWT access tokens (short-lived), refresh token rotation (long-lived), password reset flow
- **R8**: API key management — users generate named API keys with configurable scopes, keys authenticate CLI sessions, keys are hashed at rest (bcrypt or argon2)
- **R9**: Go backend API server with PostgreSQL — user management, session storage, telemetry ingestion, API key validation, health checks, structured logging
- **R10**: Client-side telemetry collection — CLI runs a local HTTP hook server that receives real-time events from Claude Code's hook system (16 events: PreToolUse, PostToolUse, SubagentStart/Stop, PreCompact, Stop, Notification, etc.) and enriches them with session context before batched upload to the backend with offline queuing
- **R11**: Error and crash reporting — unhandled panics captured with stack trace, OS info, CLI version, and plugin set; uploaded automatically with user opt-in consent on first run
- **R12**: Conversation capture — claude-kit parses Claude Code's JSONL transcript files (`~/.claude/projects/<path>/<session>.jsonl`) to extract token usage, cost data, tool call history, and full conversation content for upload to the backend for session history, replay, and analytics
- **R13**: Autonomous mode — PTY driver spawns Claude Code in a pseudo-terminal, reads output stream, injects input programmatically; user sees the real Claude ASCII interface rendered through a Bubble Tea full-screen TUI with status overlay
- **R14**: Spec enforcement in autonomous mode — the autonomous driver reads project specs (`docs/specs/`), validates Claude's tool outputs against requirements, prevents drift, and logs compliance events
- **R15**: Web dashboard (SvelteKit + TypeScript) — user signup/login, session history browser, usage analytics (charts, trends), plugin configuration, API key management UI
- **R16**: Live session monitoring — dashboard streams real-time output from active autonomous sessions via WebSocket, showing Claude's terminal output and claude-kit overlay status
- **R17**: Kubernetes deployment — API server and dashboard containerized with multi-stage Docker builds, deployed via Helm charts with health checks, resource limits, HPA autoscaling, and ingress configuration
- **R18**: Infrastructure as code — all Kubernetes manifests, Helm charts, Dockerfiles, and CI/CD pipelines live in the `deploy/` directory of the monorepo
- **R19**: Testing infrastructure — Go unit tests (`go test`), integration tests (testcontainers for Postgres), E2E CLI tests (binary black-box tests), API endpoint tests, SvelteKit component tests, and performance benchmarks (`go test -bench`)
- **R20**: Security model — garble binary obfuscation (`-literals -tiny`), anti-debugging detection (ptrace/P_TRACED/IsDebuggerPresent), binary self-hash integrity verification, memory-only plugin decryption, OS keychain key storage via `go-keyring`, machine-bound key derivation (HKDF), minimized `~/.claude/` injection footprint, bcrypt/argon2 API key hashing, JWT signing with RS256, rate limiting, CORS policy, input validation, and crash report sanitization
- **R21**: Claude Code hook integration — the CLI registers HTTP hooks for all 16 Claude Code events (PreToolUse, PostToolUse, PostToolUseFailure, SubagentStart/Stop, PreCompact, Stop, Notification, UserPromptSubmit, etc.) to capture granular session telemetry including tool usage, file operations, agent teams, and compaction triggers
- **R22**: Tiered telemetry consent — four privacy levels: Level 0 (disabled), Level 1 (anonymous metrics: event counts, durations, OS/arch), Level 2 (+ file paths, plugin names, model selections), Level 3 (+ full conversation transcripts); user selects level on first run and can change via `claude-kit telemetry level`
- **R23**: JSONL transcript parsing — the CLI parses Claude Code's session transcript files to extract per-message token usage, cumulative cost, tool call sequences, and conversation content; data granularity respects the user's telemetry consent level

## Acceptance Criteria

- [ ] [R1] `claude-kit --kit embedded-zephyr-engineer` launches Claude with identical plugin set to the Python version
- [ ] [R1] All subcommands (`list`, `validate`, `setup`, etc.) produce equivalent output
- [ ] [R2, R3] Plugins encrypted by Go CLI can be decrypted and loaded correctly; encrypted plugins from the Python era are also loadable (backwards compatibility)
- [ ] [R4, R5] `goreleaser release --snapshot` produces binaries for all 5 platform targets; pre-release tags create GitHub pre-releases
- [ ] [R6] `claude-kit update` downloads and replaces the running binary with the latest version for the current channel
- [ ] [R7, R8] A new user can sign up, log in, generate an API key, and use that key to authenticate a CLI session
- [ ] [R9] Backend API serves authenticated requests at <100ms p95 latency for CRUD operations
- [ ] [R10, R11] CLI sends telemetry events that appear in the user's dashboard within 30 seconds
- [ ] [R12] A completed session's conversation log is viewable in the dashboard
- [ ] [R13] `claude-kit autonomous --kit <name> --goal "implement feature X"` launches a full-screen TUI showing Claude's real terminal output with a ghost driving it
- [ ] [R14] Autonomous mode refuses to proceed when Claude's output contradicts the active spec's requirements
- [ ] [R15, R16] Dashboard shows live session output streaming via WebSocket with <1s latency
- [ ] [R17, R18] `helm install claude-kit deploy/backend/helm/` deploys a working API + dashboard stack to a Kubernetes cluster
- [ ] [R19] `go test ./...` passes with >80% coverage on `internal/` packages; `go test -bench ./...` produces reproducible benchmark results
- [ ] [R20] Release binaries pass `garble -literals -tiny` obfuscation; API keys are never stored in plaintext; crash reports contain no secrets; anti-debug detection blocks debugger attachment on all platforms
- [ ] [R20] Decrypted plugins only exist in memory-backed filesystems; `ls /proc/<pid>/fd/` (Linux) and `lsof` (macOS) confirm no plaintext plugin files on persistent storage during a session
- [ ] [R20] Encryption key is stored in OS keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service) — never on disk in plaintext
- [ ] [R21] All 16 Claude Code hook events are captured by the CLI's HTTP hook server and appear in the telemetry pipeline
- [ ] [R22] `claude-kit telemetry level 0` stops all data collection; levels 1-3 capture progressively more data; `claude-kit telemetry level` shows current setting
- [ ] [R23] After a session ends, `claude-kit` parses the JSONL transcript and extracts token counts, cost, and tool call data for upload (respecting consent level)

## Goal

Transform claude-kit from a single-file Python CLI launcher into a full commercial Go product with three pillars: (1) a Go CLI binary that handles plugin management, encrypted distribution, and autonomous mode via PTY driver, (2) a Go backend API server that manages authentication, telemetry, and conversation storage, and (3) a SvelteKit web dashboard that provides signup/login, session monitoring, usage analytics, and plugin configuration. The system deploys to Kubernetes with infrastructure-as-code, distributes via GoReleaser with pre-release channels, and maintains the existing plugin ecosystem without breaking changes.

## Architecture Decisions

- **AD-1: Go as primary language** — Go was chosen over Rust (faster dev velocity, better TUI ecosystem) and TypeScript (zero IP protection via bun-decompile). Garble obfuscation provides reasonable IP protection. Single static binary eliminates runtime dependencies.
- **AD-2: Monorepo with apps/deploy/tools/docs structure** — CLI, API, and dashboard share internal packages (auth, crypto, plugin types). Deploy configs live alongside the code they deploy. Shared Go module for CLI and API.
- **AD-3: SvelteKit for dashboard** — Selected over Next.js because the existing `frontend-svelte` team plugin provides domain expertise. Lighter framework, excellent DX, growing ecosystem.
- **AD-4: PTY driver for autonomous mode** — Selected over direct API calls (would lose Claude Code's tool ecosystem) and SDK approach (not available). `creack/pty` + goroutines provide concurrent PTY I/O with Bubble Tea TUI rendering.
- **AD-5: Kubernetes deployment** — Selected for production scalability. Helm charts for templated deploys. HPA for autoscaling. Infrastructure code lives in `deploy/infra/`.
- **AD-6: PostgreSQL for primary storage** — User accounts, API keys, session metadata, telemetry events. S3-compatible object storage for conversation logs (large blobs).
- **AD-6a: ent (entgo.io) as ORM** — Schema-first Go ORM with code generation, built-in migrations, graph traversal, and privacy layer. Selected over Prisma Go (archived July 2025, no Prisma v7 support), sqlc (too low-level for rapid iteration), and GORM (reflection-based, weaker type safety). Schema defined in `ent/schema/` at the monorepo root.
- **AD-7: Backwards-compatible encryption** — Go CLI must decrypt plugins encrypted by the Python/openssl pipeline. Both use AES-256-CBC with PBKDF2. The Go implementation uses `crypto/aes` + `crypto/cipher` + `golang.org/x/crypto/pbkdf2`.
- **AD-8: Offline-first telemetry** — CLI queues events locally when offline and batch-uploads when connectivity returns. No telemetry failure should block the user's workflow.
- **AD-9: Memory-only plugin decryption** — Decrypted plugins never touch persistent storage. Linux: user-namespace tmpfs mount (no root since Linux 5.11, `unshare --user --map-root-user mount -t tmpfs`). macOS: `hdiutil attach -type UDIF -nomount ram://` + `diskutil eraseVolume`. Windows: ACL-protected temp directory under `%LOCALAPPDATA%\Temp` with restrictive DACL. Cleanup via `defer` + signal handlers (SIGTERM/SIGINT). Fallback: `os.MkdirTemp` with `0700` permissions and `mlock` where possible.
- **AD-10: OS keychain + machine-bound key derivation** — Encryption master key stored in OS keychain via `zalando/go-keyring` (macOS Keychain, Windows Credential Manager, Linux Secret Service/kwallet). On first run: generate 32-byte random master key → store in keychain under service `claude-kit`. Plugin decryption key derived via HKDF: `HKDF-SHA256(master_key, salt=machine_id || hardware_serial, info="plugin-decrypt")`. Machine-binding prevents key portability if keychain is exported. The split-key assembly pattern (`_get_key()`) is preserved as a fallback for environments without keychain access.
- **AD-11: HTTP hooks for telemetry capture** — Claude Code supports HTTP hooks that POST JSON payloads to a local endpoint. The CLI spawns a lightweight HTTP server on `localhost:<random-port>` before launching Claude, registers hooks in `settings.json` for all 16 events, receives structured event payloads (tool name, file paths, token counts, timing), and buffers them for batch upload. HTTP hooks are strongly preferred over command hooks (which spawn a process per event, causing 50ms+ overhead per tool call).
- **AD-12: JSONL transcript parsing** — Claude Code stores full session transcripts at `~/.claude/projects/<base64-encoded-path>/<session-uuid>.jsonl`. Each line is a JSON object containing message role, content, tool calls/results, and token usage (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`). On session end, the CLI locates and parses this file to extract: total token usage, cumulative cost, tool call sequence, files read/written, and conversation content (at consent Level 3 only).
- **AD-13: Tiered telemetry consent model** — Four privacy levels inspired by VS Code's model. Level 0: no telemetry. Level 1: anonymous metrics only (event counts, session duration, OS/arch, CLI version — no identifying data). Level 2: adds file paths, plugin names, model selections, tool usage patterns. Level 3: adds full conversation transcripts and JSONL parsing. User selects on first run via interactive prompt; stored in `~/.config/claude-kit/config.json`. PII scrubbing applied at each level: Level 1 hashes all paths, Level 2 preserves relative paths but strips home directory. Data retention configurable per tier (default: 30/90/365 days).

## Constraints

- Plugin content format and structure must not change — existing plugins must work without modification
- The `claude` CLI (Claude Code) must remain the execution engine — claude-kit wraps it, never replaces it
- No third-party Go dependencies in the crypto path — stdlib `crypto/*` only (except `golang.org/x/crypto` for PBKDF2)
- Python validation scripts (`validate-plugins.py`, `test-plugin-consistency.sh`) are kept as-is in `tools/` — they are dev-only and work
- The encryption key assembly pattern (`_get_key()` equivalent) must be preserved — split key parts, runtime assembly, never logged
- All existing CI checks must continue to pass during and after the migration

## Phase Summary

| Phase | Title | Status | Satisfies | Description |
|-------|-------|--------|-----------|-------------|
| 1 | Go CLI Core & Plugin System | pending | R1, R2, R3, R20 | Port Python CLI to Go — all subcommands, plugin loading, memory-only decryption, OS keychain key storage, anti-tamper |
| 2 | Distribution & Self-Update | pending | R4, R5, R6, R20 | GoReleaser setup, garble obfuscation, anti-debugging, binary integrity, cross-platform builds, self-update |
| 3 | Backend API & Authentication | pending | R7, R8, R9 | Go HTTP server, PostgreSQL, user accounts, JWT auth, API key management, containerization |
| 4 | Telemetry & Conversation Pipeline | pending | R10, R11, R12, R21, R22, R23 | HTTP hook server, Claude Code event capture, JSONL parsing, tiered consent, conversation upload |
| 5 | Autonomous Mode | pending | R13, R14 | PTY driver, Bubble Tea TUI, ghost input injection, spec enforcement, session recording |
| 6 | Dashboard, Infrastructure & Production | pending | R15, R16, R17, R18, R19, R20 | SvelteKit dashboard, Kubernetes Helm charts, CI/CD pipelines, testing infrastructure, security hardening |

## Key Files

### Monorepo Structure (Target)

```
claude-kit/                          # monorepo root
├── apps/
│   ├── cli/                         # Go CLI binary
│   │   ├── main.go                  # CLI entry point
│   │   ├── cmd/                     # cobra commands
│   │   │   ├── root.go              # root command, flag parsing
│   │   │   ├── run.go               # --kit / --plugin launch
│   │   │   ├── list.go              # list subcommand
│   │   │   ├── validate.go          # validate subcommand
│   │   │   ├── update.go            # self-update
│   │   │   ├── setup.go             # setup / restore
│   │   │   ├── login.go             # auth: login
│   │   │   ├── logout.go            # auth: logout
│   │   │   ├── autonomous.go        # autonomous mode entry
│   │   │   └── ...                  # remaining subcommands
│   │   └── cmd_test.go              # CLI integration tests
│   │
│   ├── backend/                     # Go API server
│   │   ├── main.go                  # server entry point
│   │   ├── routes/                  # HTTP route definitions
│   │   │   ├── auth.go              # /auth/signup, /auth/login, /auth/refresh
│   │   │   ├── users.go             # /users/me, /users/api-keys
│   │   │   ├── telemetry.go         # /telemetry/events, /telemetry/sessions
│   │   │   ├── conversations.go     # /conversations/upload, /conversations/{id}
│   │   │   └── health.go            # /health, /ready
│   │   ├── middleware/              # auth, rate limiting, CORS, logging
│   │   └── routes_test.go           # API endpoint tests
│   │
│   └── web/                         # SvelteKit dashboard
│       ├── src/
│       │   ├── routes/              # SvelteKit pages
│       │   │   ├── (auth)/          # login, signup, forgot-password
│       │   │   ├── dashboard/       # main dashboard
│       │   │   ├── sessions/        # session history, live view
│       │   │   ├── settings/        # API keys, preferences
│       │   │   └── analytics/       # usage charts, trends
│       │   ├── lib/
│       │   │   ├── components/      # reusable Svelte components
│       │   │   ├── stores/          # Svelte stores (auth, sessions)
│       │   │   └── api/             # API client functions
│       │   └── app.html
│       ├── package.json
│       ├── svelte.config.js
│       ├── tailwind.config.js
│       └── vite.config.ts
│
├── internal/                        # shared Go packages (CLI + API)
│   ├── auth/                        # JWT generation/validation, password hashing
│   │   ├── jwt.go
│   │   ├── apikey.go
│   │   └── auth_test.go
│   ├── crypto/                      # AES-256-CBC encryption/decryption
│   │   ├── encrypt.go
│   │   ├── decrypt.go
│   │   ├── key.go                   # split key assembly (fallback)
│   │   ├── keychain.go              # OS keychain storage via go-keyring
│   │   ├── derive.go                # HKDF machine-bound key derivation
│   │   ├── memfs.go                 # memory-backed filesystem (tmpfs/ramdisk)
│   │   └── crypto_test.go
│   ├── plugins/                     # plugin loading, resolution, companion logic
│   │   ├── loader.go                # find, expand, deduplicate plugins
│   │   ├── resolver.go              # companion + domain auto-loading
│   │   ├── types.go                 # Plugin, CtlConfig, PluginConfig structs
│   │   └── loader_test.go
│   ├── telemetry/                   # client-side event collection + offline queue
│   │   ├── collector.go
│   │   ├── hookserver.go            # local HTTP hook server for Claude Code events
│   │   ├── transcript.go            # JSONL transcript parser
│   │   ├── consent.go               # tiered consent model (L0-L3)
│   │   ├── scrubber.go              # PII scrubbing per consent level
│   │   ├── queue.go                 # SQLite local queue for offline events
│   │   ├── uploader.go
│   │   └── telemetry_test.go
│   ├── antitamper/                  # binary integrity + anti-debug
│   │   ├── debug_linux.go           # ptrace detection
│   │   ├── debug_darwin.go          # P_TRACED sysctl check
│   │   ├── debug_windows.go         # IsDebuggerPresent
│   │   ├── integrity.go             # binary self-hash verification
│   │   └── antitamper_test.go
│   ├── pty/                         # PTY driver for autonomous mode
│   │   ├── driver.go                # spawn Claude, read/write PTY
│   │   ├── parser.go                # parse Claude's terminal output
│   │   └── driver_test.go
│   ├── tui/                         # Bubble Tea components
│   │   ├── app.go                   # main TUI application model
│   │   ├── claude_viewport.go       # renders Claude's PTY output
│   │   ├── status_bar.go            # overlay status bar
│   │   ├── session_info.go          # session metadata panel
│   │   └── styles.go                # lipgloss styles
│   ├── spec/                        # spec enforcement engine
│   │   ├── reader.go                # parse overview.md, phase files
│   │   ├── enforcer.go              # validate Claude output against reqs
│   │   └── spec_test.go
│   ├── db/                          # database layer (API server only)
│   │   ├── db.go                    # connection pool setup
│   │   └── migrate.go               # migration runner (ent auto-migration)
│
├── ent/                             # ent ORM schema (top-level, shared)
│   ├── schema/                      # entity definitions
│   │   ├── user.go                  # User entity
│   │   ├── apikey.go                # APIKey entity
│   │   ├── session.go               # Session entity
│   │   ├── telemetryevent.go        # TelemetryEvent entity
│   │   ├── crashreport.go           # CrashReport entity
│   │   ├── conversation.go          # Conversation entity
│   │   └── refreshtoken.go          # RefreshToken entity
│   ├── generate.go                  # go:generate directive
│   └── ...                          # generated client code (auto by ent)
│   ├── config/                      # configuration loading
│   │   ├── cli.go                   # CLI config (XDG paths, defaults)
│   │   └── server.go                # server config (env vars, secrets)
│   └── version/                     # version info (embedded at build)
│       └── version.go
│
├── deploy/
│   ├── cli/                         # CLI distribution
│   │   ├── .goreleaser.yml          # GoReleaser config
│   │   ├── homebrew/                # Homebrew formula templates
│   │   │   ├── claude-kit.rb        # stable tap formula
│   │   │   └── claude-kit-beta.rb   # unstable tap formula
│   │   └── scoop/                   # Scoop manifest
│   │       └── claude-kit.json
│   ├── backend/                     # API server deployment
│   │   ├── Dockerfile               # multi-stage Go build
│   │   ├── helm/                    # Helm chart
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   ├── values.production.yaml
│   │   │   └── templates/
│   │   │       ├── deployment.yaml
│   │   │       ├── service.yaml
│   │   │       ├── ingress.yaml
│   │   │       ├── hpa.yaml
│   │   │       ├── configmap.yaml
│   │   │       ├── secret.yaml
│   │   │       └── migration-job.yaml
│   │   └── docker-compose.yml       # local development stack
│   ├── web/                         # Dashboard deployment
│   │   ├── Dockerfile               # multi-stage Node build
│   │   └── helm/                    # Helm chart for dashboard
│   └── infra/                       # Shared infrastructure
│       ├── namespace.yaml
│       ├── cert-manager/            # TLS certificate automation
│       ├── monitoring/              # Prometheus + Grafana manifests
│       └── storage/                 # PVC definitions, S3 config
│
├── tools/                           # Development and CI tooling
│   ├── validate-plugins.py          # Tier 1 structural validation (existing)
│   ├── test-plugin-consistency.sh   # cross-reference checks (existing)
│   ├── validate-docs.sh             # docs structure validation (existing)
│   ├── encrypt-plugins.sh           # encryption script (existing)
│   ├── test-cli.sh                  # CLI smoke tests (rewritten for Go)
│   ├── build-semantic-prompt.py     # PR review prompt builder (existing)
│   ├── build-nightly-prompt.py      # nightly review prompt (existing)
│   ├── build-autofix-prompt.py      # autofix prompt (existing)
│   └── benchmark/                   # performance benchmarking
│       ├── bench_plugin_load.go     # plugin loading benchmark
│       ├── bench_encryption.go      # crypto benchmark
│       └── bench_pty.go             # PTY throughput benchmark
│
├── plugins/                         # plugin content (unchanged)
├── templates/                       # plugin scaffolding templates (unchanged)
├── docs/                            # documentation + specs
│   ├── specs/                       # spec files
│   ├── research/                    # theoretical research
│   ├── architecture/                # ADRs
│   └── ...
│
├── go.mod                           # Go module definition
├── go.sum                           # Go dependency lock
├── .goreleaser.yml                  # symlink to deploy/cli/.goreleaser.yml
├── .github/workflows/               # CI/CD pipelines
│   ├── push.yml                     # fast-validate (updated for Go)
│   ├── pr.yml                       # PR validation (updated for Go)
│   ├── pr-autofix.yml               # auto-fix on failure
│   ├── release-cli.yml              # GoReleaser CLI release
│   ├── release-backend.yml          # Build + push API container
│   ├── release-web.yml              # Build + push dashboard container
│   ├── nightly.yml                  # nightly plugin review
│   ├── weekly.yml                   # weekly audit
│   └── deploy.yml                   # Kubernetes deployment
└── CHANGELOG.md
```

### Current Files That Move

| Current Location | New Location | Notes |
|-----------------|-------------|-------|
| `claude-kit` (Python) | `apps/cli/main.go` | Full rewrite in Go |
| `install.sh` | `deploy/cli/install.sh` | Updated for Go binary |
| `scripts/validate-plugins.py` | `tools/validate-plugins.py` | Unchanged |
| `scripts/test-cli.sh` | `tools/test-cli.sh` | Rewritten for Go binary |
| `scripts/test-plugin-consistency.sh` | `tools/test-plugin-consistency.sh` | Unchanged |
| `scripts/validate-docs.sh` | `tools/validate-docs.sh` | Unchanged |
| `scripts/encrypt-plugins.sh` | `tools/encrypt-plugins.sh` | Unchanged (dev-only) |
| `scripts/build-semantic-prompt.py` | `tools/build-semantic-prompt.py` | Unchanged |
| `scripts/build-nightly-prompt.py` | `tools/build-nightly-prompt.py` | Unchanged |
| `scripts/build-autofix-prompt.py` | `tools/build-autofix-prompt.py` | Unchanged |
| `plugins/` | `plugins/` | Unchanged |
| `templates/` | `templates/` | Unchanged |
| `docs/` | `docs/` | Unchanged |

### Go Dependencies (Expected)

| Package | Purpose | Category |
|---------|---------|----------|
| `github.com/spf13/cobra` | CLI framework | CLI |
| `github.com/charmbracelet/bubbletea` | TUI framework | TUI |
| `github.com/charmbracelet/lipgloss` | TUI styling | TUI |
| `github.com/charmbracelet/bubbles` | TUI components | TUI |
| `github.com/creack/pty` | PTY driver | Autonomous |
| `github.com/go-chi/chi/v5` | HTTP router | API |
| `entgo.io/ent` | Schema-first ORM + code generation | API |
| `github.com/jackc/pgx/v5` | PostgreSQL driver (used by ent) | API |
| `github.com/golang-jwt/jwt/v5` | JWT tokens | Auth |
| `golang.org/x/crypto` | PBKDF2, bcrypt, argon2 | Crypto |
| `github.com/gorilla/websocket` | WebSocket (live sessions) | API |
| `github.com/rs/zerolog` | Structured logging | Observability |
| `github.com/prometheus/client_golang` | Metrics exposition | Observability |
| `github.com/minio/minio-go/v7` | S3-compatible storage | Storage |
| `github.com/mattn/go-sqlite3` | Local telemetry queue | Telemetry |
| `github.com/zalando/go-keyring` | OS keychain access (macOS/Win/Linux) | Security |
| `golang.org/x/sys` | Platform syscalls (tmpfs, ptrace, mlock) | Security |
