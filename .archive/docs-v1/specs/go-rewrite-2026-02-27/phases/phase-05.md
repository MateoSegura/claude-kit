# Phase 05: Autonomous Mode

## Objective

Build the autonomous mode — a PTY driver that spawns Claude Code in a pseudo-terminal, reads its output stream, injects input programmatically ("ghost driving"), renders the real Claude ASCII interface through a Bubble Tea full-screen TUI with status overlay, and enforces project specs during execution.

## Satisfies

- R13: PTY driver ghost-drives Claude's terminal, Bubble Tea TUI renders real Claude output with overlay
- R14: Spec enforcement — autonomous driver validates Claude's outputs against requirements, prevents drift

## Steps

1. [ ] Implement PTY driver — `internal/pty/driver.go` using `creack/pty` to spawn `claude` in a pseudo-terminal with configurable size; goroutines for concurrent read/write
2. [ ] Implement output parser — `internal/pty/parser.go` that processes raw PTY byte stream, handles ANSI escape sequences, tracks cursor position, detects Claude's prompt boundaries (ready for input vs. still outputting)
3. [ ] Implement input injector — `internal/pty/injector.go` that writes to the PTY's stdin at controlled pace (simulating human typing speed for the "ghost" effect), handles special keys (Enter, Ctrl+C, etc.)
4. [ ] Build Bubble Tea application — `internal/tui/app.go` with the main model: receives PTY output events, routes to viewport, handles key bindings (quit, pause, resume, manual override)
5. [ ] Build Claude viewport component — `internal/tui/claude_viewport.go` that renders Claude's raw terminal output in a scrollable viewport, preserving ANSI colors and formatting
6. [ ] Build status bar component — `internal/tui/status_bar.go` showing: mode (autonomous/paused/manual), spec phase, requirement being addressed, session duration, compact count, telemetry status
7. [ ] Build session info panel — `internal/tui/session_info.go` togglable side panel showing: loaded plugins, goal, current step, files modified, compliance log
8. [ ] Implement spec reader — `internal/spec/reader.go` that parses `overview.md` and `phase-NN.md` files, extracts requirements (R1, R2, ...), acceptance criteria, and current phase steps
9. [ ] Implement spec enforcer — `internal/spec/enforcer.go` that monitors Claude's tool outputs (file writes, bash commands) and validates they align with the active phase's steps and requirements; logs compliance events; raises warnings on drift
10. [ ] Implement goal engine — `internal/autonomous/engine.go` that takes a user-provided goal, maps it to spec requirements, generates a sequence of prompts to feed Claude, monitors progress, decides when to intervene
11. [ ] Implement session recorder — `internal/autonomous/recorder.go` that captures the full PTY stream (timestamped) for replay and conversation upload (integrates with Phase 04 telemetry)
12. [ ] Wire autonomous mode to CLI — `apps/cli/cmd/autonomous.go` with flags: `--kit`, `--goal`, `--spec`, `--max-turns`, `--dry-run`, `--manual-approve` (require human approval before each input injection)
13. [ ] Implement WebSocket streaming — `internal/autonomous/stream.go` that broadcasts PTY output to connected WebSocket clients (for dashboard live monitoring in Phase 06)
14. [ ] Write comprehensive tests — unit tests for parser, injector, enforcer; integration test that spawns a mock process in a PTY and drives it

## Files to Create/Modify

### Create
- `internal/pty/driver.go` — PTY spawn, read/write goroutines, resize handling
- `internal/pty/parser.go` — ANSI escape sequence processing, prompt detection
- `internal/pty/injector.go` — controlled input writing, typing simulation
- `internal/pty/driver_test.go` — PTY tests with mock processes
- `internal/tui/app.go` — main Bubble Tea model (Init, Update, View)
- `internal/tui/claude_viewport.go` — raw terminal output viewport
- `internal/tui/status_bar.go` — status overlay bar
- `internal/tui/session_info.go` — togglable info panel
- `internal/tui/styles.go` — lipgloss style definitions
- `internal/tui/keybindings.go` — key binding definitions
- `internal/spec/reader.go` — spec file parser
- `internal/spec/enforcer.go` — requirement compliance checker
- `internal/spec/spec_test.go` — spec parsing and enforcement tests
- `internal/autonomous/engine.go` — goal-to-prompt engine
- `internal/autonomous/recorder.go` — session recording (PTY stream capture)
- `internal/autonomous/stream.go` — WebSocket broadcast for live monitoring
- `apps/cli/cmd/autonomous.go` — `claude-kit autonomous` command

### Modify
- `apps/cli/cmd/root.go` — register `autonomous` subcommand
- `internal/telemetry/collector.go` — add autonomous-specific events (goal progress, spec compliance, interventions)

## Autonomous Mode Architecture

```
┌─────────────────────────────────────────────────────────┐
│  claude-kit autonomous --kit <name> --goal "..."        │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Bubble Tea TUI (full-screen)                      │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Claude Viewport (85% height)                │  │  │
│  │  │  ┌────────────────────────────────────────┐  │  │  │
│  │  │  │  [Real Claude Code ASCII output]       │  │  │  │
│  │  │  │  > user message appears here            │  │  │  │
│  │  │  │  Claude is thinking...                  │  │  │  │
│  │  │  │  [tool calls, file edits, etc.]         │  │  │  │
│  │  │  └────────────────────────────────────────┘  │  │  │
│  │  ├──────────────────────────────────────────────┤  │  │
│  │  │  Status Bar                                  │  │  │
│  │  │  🤖 AUTONOMOUS │ Phase 2/6 │ R3,R4 │ 12:34  │  │  │
│  │  │  Compacts: 2 │ Plugins: 5 │ Spec: compliant  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ Background Goroutines ─────────────────────────────┐ │
│  │                                                      │ │
│  │  PTY Driver ─── reads output ──► TUI viewport       │ │
│  │       │                                              │ │
│  │       └─── writes input ◄── Goal Engine              │ │
│  │                                │                     │ │
│  │                         Spec Enforcer                │ │
│  │                                │                     │ │
│  │                         Session Recorder             │ │
│  │                                │                     │ │
│  │                         WebSocket Stream             │ │
│  │                                                      │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Key Bindings

| Key | Action |
|-----|--------|
| `q` / `Ctrl+C` | Quit (sends SIGTERM to Claude, cleans up) |
| `p` | Pause autonomous mode (stop injecting input) |
| `r` | Resume autonomous mode |
| `m` | Enter manual mode (user types directly to Claude) |
| `a` | Return to autonomous mode from manual |
| `i` | Toggle session info panel |
| `s` | Show/hide status bar |
| `↑` / `↓` | Scroll Claude viewport |

## Spec Enforcement Rules

The enforcer monitors Claude's actions and checks:

1. **File scope** — Claude should only modify files listed in the current phase's "Files to Create/Modify" section. Warn if it touches unexpected files.
2. **Requirement alignment** — After each tool call batch, check if the changes advance the phase's requirements. Log compliance events.
3. **Step tracking** — Match Claude's actions to the phase's step checklist. Auto-check steps as they're completed.
4. **Drift detection** — If Claude starts working on something not in the current phase, raise a warning and optionally inject a corrective prompt.
5. **Completion detection** — When all phase acceptance criteria are met, advance to the next phase or stop.

## Acceptance Criteria

- [ ] `claude-kit autonomous --kit <name> --goal "implement feature X"` launches a full-screen TUI showing Claude's real output
- [ ] The "ghost" types input into Claude at human-readable speed (configurable: `--typing-speed fast|medium|slow`)
- [ ] Pressing `p` pauses input injection; pressing `r` resumes; pressing `m` allows manual typing
- [ ] The status bar shows current phase, requirements being addressed, session duration, and compact count
- [ ] With `--spec docs/specs/my-spec-2026-01-01`, the enforcer logs compliance events for each Claude action
- [ ] Spec drift (Claude modifying files not listed in the current phase) triggers a visible warning in the status bar
- [ ] `--dry-run` mode shows what prompts would be injected without actually starting Claude
- [ ] `--manual-approve` mode pauses before each input injection and waits for user confirmation
- [ ] The session recorder captures the full PTY stream and uploads it as a conversation log (Phase 04 integration)
- [ ] WebSocket stream is available at `ws://localhost:PORT/sessions/{id}/stream` for live monitoring
- [ ] Pressing `q` gracefully terminates Claude (SIGTERM → wait → SIGKILL) and cleans up temp files
- [ ] Autonomous mode works with encrypted plugins (decryption happens before PTY spawn)

## Dependencies

- Requires: Phase 01 (plugin loading, crypto, CLI framework)
- Blocks: Phase 06 (dashboard live monitoring needs WebSocket stream)
