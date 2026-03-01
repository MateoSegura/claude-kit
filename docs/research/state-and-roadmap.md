# claude-kit: Current State and Roadmap

> Living document — last updated: 2026-02-27
> Companion to `overview.md`. Where overview.md defines the north star,
> this document maps the distance between today and that destination.

**Date:** 2026-02-28

---

## Table of Contents

1. [How claude-kit Works Today](#1-how-claude-kit-works-today)
2. [Problems It Already Solves](#2-problems-it-already-solves)
3. [The Gaps](#3-the-gaps)
4. [The Vision: Autonomous Mode with Transparent Execution](#4-the-vision-autonomous-mode-with-transparent-execution)
5. [Architecture of the Vision](#5-architecture-of-the-vision)
6. [The Transparency Layer](#6-the-transparency-layer)
7. [Benchmarking Design](#7-benchmarking-design)
8. [Roadmap: From Here to There](#8-roadmap-from-here-to-there)

---

## 1. How claude-kit Works Today

### 1.1 The Core Mechanism

claude-kit is a **plugin orchestration layer** on top of Claude Code CLI. Its job
is to construct the right plugin configuration and hand it to `claude`. Every
session starts the same way:

```
claude-kit --kit cloud-python --yolo
     │
     ▼
expand_kit("cloud-python")
  → [cloud-python-engineer, cloud-python-grader, cloud-python-tester,
     cloud-python-debugger, cloud-python-knowledge, core-kit, core-spec,
     core-ai, ...]          ← companions + core auto-loading
     │
     ▼
For each plugin: --plugin-dir <path>
     │
     ▼
os.execvp("claude", ["claude",
    "--plugin-dir", "/path/to/cloud-python-engineer",
    "--plugin-dir", "/path/to/cloud-python-knowledge",
    "--plugin-dir", "/path/to/core-kit",
    "--model", "opus",
    "--dangerously-skip-permissions"
])
```

Claude Code then loads each plugin directory, which injects that plugin's skills,
agents, commands, and hooks into the session. claude-kit does not touch the session
after launch — it is purely a pre-launch orchestrator.

### 1.2 What a Plugin Is

A plugin is a directory with a specific structure that Claude Code understands:

```
plugins/<name>/
  .claude-plugin/
    plugin.json       # name, description, version — what Claude Code reads
    ctl.json          # role, domain, companions — what claude-kit reads
  agents/
    engineer.md       # frontmatter (tools:, description:) + role instructions
    plan.md
  commands/
    engineer.md       # slash command: /cloud-python-engineer:engineer
  skills/
    python-backend/
      SKILL.md        # domain knowledge injected into agent contexts
    distributed-systems/
      SKILL.md
  hooks/
    hooks.json        # event bindings: SessionStart, PreToolUse, PostToolUse, Stop
  scripts/
    block-dangerous-commands.sh
    lint-python.sh
    run-tests-async.sh
    check-environment.sh
```

**Skills** are the knowledge layer — markdown files injected into agent context
windows. They act as procedural memory: how to write FastAPI endpoints, what
Alembic migration patterns look like, which Pydantic v2 APIs to use.

**Agents** are role definitions — they tell Claude who it is, what tools it has,
and how to behave for a specific role (engineer vs. grader vs. debugger).

**Hooks** are the enforcement layer — shell scripts that fire on Claude Code events:
- `SessionStart`: environment validation (Python version, required tools)
- `PreToolUse`: block dangerous commands before execution
- `PostToolUse`: lint and test after every file write
- `Stop`: (used in some plugins) spawn validation before session ends

**Commands** are slash commands that orchestrate multi-step workflows — the
`/cloud-python-engineer:engineer` command, for example, reads the project,
classifies the request, and dispatches to the right subagent.

### 1.3 The Auto-Routing Layer

`claude-kit setup` installs two things into `~/.claude/`:

1. **`rules/claude-kit-autoroute.md`** — binding routing rules that tell Claude
   to map natural language intents to skill invocations without requiring `/command`
   syntax. This is the only mechanism that injects binding instructions into the
   main conversation context (not agent subcontexts).

2. **Status line** — a shell script that shows context usage, token count, and
   model name in the Claude Code footer.

`claude-kit debug on` additionally installs **`rules/claude-kit-debug.md`** which
instructs Claude to print `[claude-kit:route]`, `[claude-kit:agent]`, `[claude-kit:hook]`, and
`[claude-kit:skill]` blocks before every routing decision, agent spawn, and hook trigger.
This is the existing observability mechanism.

### 1.4 The Companion System

When a team plugin is loaded via `--kit`, claude-kit automatically loads:
1. The explicitly requested plugin(s)
2. Their declared companions (in `ctl.json` → `companions[]`)
3. Core plugins matching the team's domain
4. Universal core plugins (always loaded)

This means `claude-kit --kit cloud-python-engineer` automatically brings in
`cloud-python-knowledge`, `core-kit`, `core-spec`, `core-ai`, and any
domain-matching core plugins — giving the engineer agent access to all relevant
knowledge without the user needing to specify each one.

### 1.5 Two Modes of Operation

**Dev mode** (`CK_MODE = "dev"`): Plugins are loaded directly from the repo's
`plugins/` directory as plaintext. Used during plugin development.

**User mode** (`CK_MODE = "user"`): Plugins are AES-256-CBC encrypted at rest in
`local/plugins/`. On launch, needed plugins are decrypted to a temp directory,
passed to `claude`, and the temp dir is cleaned up on exit. This protects
proprietary plugin content during distribution.

---

## 2. Problems It Already Solves

### 2.1 LLM Non-Determinism (Partial)

**What it does:** Skill injection narrows the output probability distribution
before sampling. When the `cloud-python-knowledge` plugin loads skills like
`python-backend` (FastAPI patterns), `distributed-systems` (queue/cache patterns),
and `containers-orchestration` (Docker/Helm), the agent's outputs converge toward
domain-correct code because contextual knowledge overrides uncertain parametric memory.

**Evidence:** This is the foundational claim of `theory-context-cache.md` — each
well-chosen skill reduces posterior variance exponentially. The agent knows to use
`DEVICE_DT_GET()` not `device_get_binding()` because the skill says so, not
because the model happens to remember.

**What's missing:** No temperature declarations in frontmatter. No structured output
schemas enforced via PostToolUse hooks. No grader auto-spawn on Stop.

### 2.2 Domain Knowledge Injection (Strong)

**What it does:** Knowledge plugins provide authoritative, curated domain knowledge
that replaces the model's potentially-stale or wrong parametric memory. Skills cover
API signatures, hardware constraints, coding patterns, anti-patterns, and design
decisions specific to the domain.

**What's missing:** No `valid_until` or `drift_indicators` in skill frontmatter —
skills can become stale without any signal. No RAG tier for large knowledge domains.
No per-skill changelog for tracking knowledge evolution.

### 2.3 Role Specialization (Strong)

**What it does:** The 5-role team architecture (engineer, grader, tester, debugger,
knowledge) gives each role exactly the tools, knowledge, and context it needs.
The engineer has write access; the grader is read-only; the debugger focuses on
logs and traces. This prevents context dilution and reduces the blast radius of
any single agent's errors.

**What's missing:** No formal handoff protocol between roles. No structured output
format that the grader expects from the engineer. No session trace that the
debugger can consume to understand cross-agent failures.

### 2.4 Runtime Enforcement (Moderate)

**What it does:** PreToolUse hooks block dangerous operations:
- `rm -rf` targeting sensitive paths (`/home`, `/etc`, `/var`, project root)
- `git push --force` without `--force-with-lease`
- `git reset --hard`
- `DROP TABLE` in raw SQL
- `kubectl delete namespace`

PostToolUse hooks run linting and async test execution after every file write,
catching errors immediately rather than at the end of the session.

**What's missing:** No reversibility classification per tool type. No semantic
contracts (postcondition checking). No human-in-the-loop approval gates for
irreversible-but-bounded operations. Hooks are primarily format/safety enforcement,
not behavioral governance.

### 2.5 Natural Language Routing (Strong)

**What it does:** core-kit's auto-routing rules map natural language intents to
skill invocations. "implement the BLE peripheral" auto-invokes
`embedded-zephyr-engineer:engineer`. "review my code" auto-invokes the grader.
This eliminates the need to memorize slash commands.

**What's missing:** Routing is pattern-matching on natural language — no typed
intent schemas, no precondition checking, no routing confidence scores. The
`intent-map.md` skill is manually maintained rather than generated from typed
command interfaces.

### 2.6 Session Observability (Basic)

**What it does:** `claude-kit debug on` installs rules that cause Claude to print
`[claude-kit:*]` blocks before routing decisions, agent spawns, and hook triggers. This
gives visual insight into what the system is doing.

**What's missing:** The debug output is Claude-generated text (probabilistic, can
be omitted or vary). It's not structured data. There's no way to measure how
accurately the debug output reflects actual system behavior. No session logs are
persisted. No benchmarking infrastructure exists.

---

## 3. The Gaps

Problems from the research that claude-kit does not yet address:

| Gap | Impact | Relevant Research |
|-----|--------|-------------------|
| No `--prompt` autonomous mode | Can't run black-box sessions | Vision section below |
| No structured session state | Context switching costs 40% productivity | `human-agent-orchestration.md` |
| No `claude-kit status` | Can't see what active sessions are doing | `human-agent-orchestration.md` |
| No agent-friendliness scoring | Can't assess codebase before autonomous operation | `agent-friendly-codebases.md` |
| No workflow definitions | Can't define multi-agent pipelines with checkpoints | `multi-agent-architecture.md` |
| No typed command interfaces | Intent ambiguity degrades agent behavior | `intent-formalization.md` |
| No skill staleness metadata | Outdated skills silently override correct knowledge | `memory-architecture.md` |
| No reversibility gates | Irreversible actions can happen without approval | `runtime-governance.md` |
| No temperature declarations | Grader and architect run at the same entropy level | `llm-non-determinism.md` |
| No benchmarking infrastructure | Can't measure if the tool is actually helping | Vision section below |
| No `invariants:` frontmatter | Symbolic constraints aren't machine-readable | `symbolic-scaffolding.md` |
| No grader auto-spawn on Stop | Engineer outputs aren't automatically validated | `llm-non-determinism.md` |

---

## 4. The Vision: Autonomous Mode with Transparent Execution

### 4.1 The Target Experience

```bash
claude-kit -y -k core -k cloud-python --prompt "implement the auth service spec"
```

This command should:

1. **Launch normally** — open the Claude Code terminal interface the user already
   knows and trusts. No new UI to learn.

2. **Inject the prompt autonomously** — drive the session with the given prompt as
   if the user typed it. The session self-directs: it reads the spec, plans the
   implementation, writes the code, runs lint and tests, and validates its own output.

3. **Stay visible** — the user can watch the terminal in real time, see every
   tool call, every hook firing, every agent spawn. Not a black box — a glass box.

4. **Show debug context** — with `claude-kit debug on`, the session shows what was
   loaded, what routing decisions were made, what constraints are active. The user
   can see the machinery without being required to operate it.

5. **Emit structured session data** — every session writes a structured log to
   `~/.claude-kit/sessions/<timestamp>/`. This log is the benchmarking substrate:
   what was asked, what was done, what was validated, whether it passed.

6. **Be fully resumable** — if the session stalls, the user can step in, answer
   a question, and step back out. Or they can let it continue and come back to
   a completed session.

### 4.2 The Three Modes in Practice

```
─────────────────────────────────────────────────────────────────
Mode            Command                           Human role
─────────────────────────────────────────────────────────────────
Full autonomy   claude-kit -y -k cloud-python     Watch, don't touch
                --prompt "implement auth service"

Collaborative   claude-kit -k cloud-python        Co-pilot; human
                                                  reviews each step

Controlled      claude-kit -k cloud-python        Human approves
                --checkpoint                      each action
─────────────────────────────────────────────────────────────────
```

The same underlying plugin infrastructure serves all three. The difference is:
- `--prompt` + `-y` = autonomous seed + skip permissions = full autonomy
- No `--prompt` = normal interactive session = collaborative
- `--checkpoint` (future flag) = approval gates on irreversible actions = controlled

### 4.3 Why "Glass Box" Matters

The goal is not just to build an autonomous tool — it is to build a tool that
**earns trust through visibility**. The user should be able to:

- Watch the session run and develop an intuition for when it's doing well vs.
  when it's about to go off the rails
- See the debug output and understand what knowledge was loaded and why
- Look at session logs after the fact and understand what happened
- Run the same prompt multiple times and compare the outputs

This "glass box" approach has two concrete benefits:

1. **Trust calibration** — the user develops taste for what good agent behavior
   looks like. Over time they learn when to trust full autonomy and when to step in.

2. **Benchmarking** — structured session logs make it possible to ask: "Is having
   the cloud-python team loaded actually producing better code than raw Claude?"
   This question is currently unanswerable. It shouldn't be.

---

## 5. Architecture of the Vision

### 5.1 The `--prompt` Flag

**Today:** `cmd_run` assembles a `claude` invocation and either `os.execvp`s
(dev mode) or `subprocess.run`s (encrypted mode). All flags after the known ones
are passed through to `claude` as `passthrough`.

**The change:** Claude Code already supports `--print` (non-interactive, print
response and exit) and implicit stdin prompting. The `--prompt` flag in claude-kit
needs to do something different: **seed an interactive session with an initial
prompt** and let it run autonomously.

Two implementation paths:

**Path A — Passthrough to Claude Code:**
Claude Code may already support something close to this via undocumented flags or
future features. If `claude --prompt "..."` works, claude-kit just passes it through.
This is the preferred path — zero new infrastructure, full compatibility.

**Path B — Session Seeding via Stdin/Pipe:**
Pipe the initial prompt to claude's stdin, then hand the terminal back to the user
for observation. This requires claude to behave interactively after consuming the
piped input, which may or may not work depending on how claude handles stdin.

**Path C — Automated Input via expect/pexpect (last resort):**
Use a pty wrapper to type the prompt programmatically, then release the terminal.
This is fragile and should be avoided unless Paths A and B are not viable.

```python
# In cmd_run — new --prompt flag handling
elif a in ("--prompt",):
    i += 1
    if i >= len(args):
        print("Error: --prompt requires a value"); sys.exit(1)
    initial_prompt = args[i]

# At launch time:
if initial_prompt:
    claude_args.extend(["--message", initial_prompt])  # Path A
    # OR: pipe via stdin (Path B)
    # OR: pty automation (Path C)
```

### 5.2 The Session Log

Every session should emit a structured log. This requires minimal instrumentation
because most of the data already flows through hooks:

```
~/.claude-kit/
  sessions/
    2026-02-27T14-32-00_cloud-python/
      session.json          # metadata: plugins, model, prompt, duration
      events.jsonl          # newline-delimited JSON: one event per hook fire
      summary.md            # human-readable summary (generated at Stop)
```

**`session.json`** (written at launch):
```json
{
  "id": "2026-02-27T14-32-00",
  "plugins": ["cloud-python-engineer", "cloud-python-knowledge", "core-kit"],
  "model": "opus",
  "mode": "autonomous",
  "initial_prompt": "implement the auth service spec",
  "started_at": "2026-02-27T14:32:00Z",
  "cwd": "/home/mateo/my-project"
}
```

**`events.jsonl`** (appended by hooks throughout the session):
```jsonl
{"ts":"14:32:01","event":"SessionStart","plugin":"cloud-python-engineer","status":"ok"}
{"ts":"14:32:03","event":"PreToolUse","tool":"Bash","command":"pip install ...","status":"allowed"}
{"ts":"14:32:05","event":"PostToolUse","tool":"Write","file":"src/auth/router.py","lint":"pass","tests":"running"}
{"ts":"14:32:10","event":"PostToolUse","tool":"Write","file":"src/auth/models.py","lint":"pass","tests":"pass"}
{"ts":"14:35:22","event":"Stop","grader_spawned":true,"score":8.5,"issues":2}
```

**`summary.md`** (generated by Stop hook or grader):
```markdown
# Session Summary — 2026-02-27T14:32:00

**Prompt:** implement the auth service spec
**Duration:** 3m 22s  **Model:** opus  **Team:** cloud-python

## What happened
- Read spec from docs/auth-service-spec.md
- Scaffolded src/auth/ with router, models, schemas, dependencies
- Wrote 4 files, 312 lines added
- All lint checks passed
- 18/18 tests passing

## Grader assessment
Score: 8.5/10 — 2 issues found
- WARNING: Missing rate limiting on /auth/token endpoint
- INFO: Consider extracting token expiry config to settings
```

### 5.3 The Logging Hook (New Script)

A new script `scripts/session-logger.sh` fires on every hook event and appends
to the `events.jsonl` file. It receives the same structured JSON that all hooks
receive via stdin.

```bash
#!/usr/bin/env bash
set -euo pipefail

SESSION_DIR="${CLAUDE_KIT_SESSION_DIR:-}"
if [[ -z "$SESSION_DIR" ]]; then
  exit 0  # Logging disabled if no session dir set
fi

EVENT_TYPE="${CLAUDE_HOOK_EVENT:-unknown}"
TIMESTAMP=$(date -u +%H:%M:%S)
INPUT=$(cat)

# Append structured event to the session log
echo "{\"ts\":\"$TIMESTAMP\",\"event\":\"$EVENT_TYPE\",$(echo "$INPUT" | jq -c .)}" \
  >> "$SESSION_DIR/events.jsonl"

exit 0  # Never block — logging is observational only
```

This hook is added to every plugin's `hooks.json` as a passive observer:
```json
{
  "PreToolUse": [{ "matcher": "", "hooks": [
    { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/session-logger.sh" }
  ]}],
  "PostToolUse": [{ "matcher": "", "hooks": [
    { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/session-logger.sh" }
  ]}]
}
```

---

## 6. The Transparency Layer

### 6.1 What Debug Mode Does Today

`claude-kit debug on` installs `~/.claude/rules/claude-kit-debug.md` which contains
instructions that tell Claude to print `[claude-kit:*]` blocks before routing decisions,
agent spawns, and hook triggers.

**The limitation:** This output is generated by Claude Code's language model — it
is probabilistic. Claude may omit the block, abbreviate it, or vary its format.
The debug output is a best-effort narrative, not a reliable log.

### 6.2 Two-Layer Transparency: Deterministic + Narrative

The vision requires both layers working together:

**Layer 1 — Deterministic (hooks, reliable):**
The session log (`events.jsonl`) is written by shell scripts — purely deterministic.
Every hook fire, every tool call, every lint result is recorded exactly as it
happened. This is ground truth.

**Layer 2 — Narrative (debug mode, approximate):**
The `[claude-kit:*]` blocks from debug mode give the human a readable narrative of what
the agent is "thinking" — what routing decision it made, which agent it spawned,
why. This is helpful for building intuition but is not the source of truth.

The combination: **you watch the narrative in the terminal, the log captures the
truth, and over time you calibrate how accurately the narrative reflects reality.**
That calibration is itself a form of benchmarking.

### 6.3 What Debug Mode Should Show

Extend `claude-kit-debug.md` to instruct Claude to emit richer debug blocks:

```
[claude-kit:session] plugins: cloud-python-engineer, cloud-python-knowledge, core-kit
              model: opus  mode: autonomous  debug: on
              skills loaded: python-backend, distributed-systems, containers-orchestration,
                             grpc-protocols, design-patterns, core-kit:routing, core-kit:identity

[claude-kit:route] "implement the auth service spec" → cloud-python-engineer:engineer
            match: "implement" + "service" → engineer:develop workflow
            confidence: high (explicit implementation request)

[claude-kit:agent] spawning endpoint-writer
            skills: python-backend, grpc-protocols
            tools: Read, Write, Glob, Grep, Bash
            mode: bypassPermissions (--yolo active)

[claude-kit:hook] PostToolUse(Write) → lint-python.sh
           file: src/auth/router.py
           result: allowed (lint passed, 0 warnings)

[claude-kit:hook] PostToolUse(Write) → run-tests-async.sh
           result: running async (timeout: 300s)

[claude-kit:constraint] checking invariants for cloud-python-engineer
                 active: no-raw-sql, no-force-push, no-drop-table, python-type-hints-required
                 status: all clear
```

The `[claude-kit:session]` block at the start of every session (not just on actions) gives
the user immediate confirmation that the right plugins and skills are active. This
is the "feel" the user described — without needing to understand the internals,
they can see "yes, the python-backend skill is loaded" and develop confidence in
the session.

### 6.4 A `--debug` Flag on Launch

Currently debug mode is a persistent setting (on/off via `claude-kit debug on`).
Add a per-session flag:

```bash
claude-kit -y -k cloud-python --prompt "implement auth" --debug
```

This activates debug mode for the current session only, without modifying the
persistent rules file. Implemented by adding the debug rules file to a temp
location and passing it as an additional `--plugin-dir` or equivalent.

---

## 7. Benchmarking Design

### 7.1 What We Want to Measure

The core question: **Is having claude-kit loaded actually producing better output
than raw Claude?**

Secondary questions:
- Which plugins contribute most to output quality?
- Does skill quality correlate with output quality?
- Is the grader catching real issues or producing noise?
- Do hooks prevent real errors or just create friction?

### 7.2 The Benchmark Session Format

A benchmark session is a normal session run with a fixed prompt against a fixed
codebase state, with output captured and scored:

```bash
# Run the same prompt with different configurations
claude-kit benchmark --config cloud-python --prompt "add a /health endpoint to the auth service"
claude-kit benchmark --config raw-claude   --prompt "add a /health endpoint to the auth service"
claude-kit benchmark --config core-only    --prompt "add a /health endpoint to the auth service"
```

Each run:
1. Resets the codebase to a known state (git stash/checkout)
2. Launches with the specified configuration
3. Captures the session log
4. Scores the output (lint, tests, grader score, manual review criteria)
5. Appends to `~/.claude-kit/benchmarks/<benchmark-id>/results.json`

### 7.3 Automatic Scoring Dimensions

| Dimension | Measurement | Source |
|-----------|-------------|--------|
| **Correctness** | Tests pass? (yes/no + count) | `run-tests-async.sh` output in events.jsonl |
| **Style conformance** | Lint warnings (count + severity) | `lint-python.sh` output |
| **Grader score** | 0–10 score from grader agent | Stop hook grader output |
| **Type coverage** | `mypy --strict` passes? `any` count? | New PostToolUse hook |
| **Consistency** | Same output structure across N runs? | Structural comparison via AST |
| **Session efficiency** | Token count, tool calls, duration | session.json |

### 7.4 The "Feel" Interface

The user said: *"I can use it and over time 'feel' if it's actually helping."*

This requires surfacing trends, not raw numbers. After a few sessions, `claude-kit
stats` should show:

```
claude-kit stats

  Sessions (last 7 days): 12
  ─────────────────────────────────────────────
  Team                  Grader avg    Tests pass
  cloud-python          8.2 / 10      94%
  embedded-zephyr       7.8 / 10      88%
  ─────────────────────────────────────────────
  Hooks fired: 47    Blocked: 3    Allowed: 44
  Most blocked: git push --force (2x), rm -rf (1x)
  ─────────────────────────────────────────────
  Compared to 5 raw-claude sessions last week:
  Grader score:  +1.4 pts    Tests: +11%    Lint: -3 warnings/session
```

This is the concrete "feel" signal — not a dashboard with charts, but a simple
weekly comparison that answers "is this making me better?"

---

## 8. Roadmap: From Here to There

The roadmap is sequenced by: (1) leverage — what enables the most downstream value,
(2) coherence — what fits naturally with the existing architecture, (3) reversibility
— smaller changes before architectural ones.

### Phase 1 — Foundation (Now → v0.12)
*Make the existing system measurable and the glass box real.*

| Feature | What it is | Existing code it touches |
|---------|-----------|--------------------------|
| Session log infrastructure | `~/.claude-kit/sessions/` directory, `session.json`, `events.jsonl` | `cmd_run` (set `CLAUDE_KIT_SESSION_DIR` env var before launch) |
| Session logger hook script | Passive `session-logger.sh` in every plugin | New script, `hooks.json` in all plugins |
| `--debug` per-session flag | Activates debug rules for one session only | `cmd_run` flag parsing, temp rules injection |
| Richer `[claude-kit:session]` block | Shows all loaded skills at session start | `claude-kit-debug.md` rules file |
| `claude-kit sessions` command | List recent sessions with summary stats | New `cmd_sessions`, reads `~/.claude-kit/sessions/` |
| Grader auto-spawn on Stop | Stop hook that spawns grader if not already run | Stop hook script in team plugins |

### Phase 2 — Autonomous Mode (v0.12 → v0.14)
*Make `--prompt` work and make autonomous sessions reliable.*

| Feature | What it is | Notes |
|---------|-----------|-------|
| `--prompt` flag | Seeds an interactive session with an initial message | Depends on Claude Code API support; Path A preferred |
| Reversibility classification | 4-level gate (allow/log/confirm/block) per tool type | New PreToolUse hook logic in all plugins |
| Invariants frontmatter | `invariants:` YAML field in skill frontmatter | Schema change to skill format + validator update |
| Temperature declarations | `temperature:` field in agent frontmatter | Schema change + (when Claude Code supports it) passthrough |
| `core-kit:audit` command | Scores codebase agent-friendliness before autonomous run | New command in core-kit |

### Phase 3 — Multi-Session Orchestration (v0.14 → v0.17)
*Support the "manager of agents" workflow.*

| Feature | What it is | Notes |
|---------|-----------|-------|
| `claude-kit status` | Show all running sessions with task, files changed, blockers | New command, reads active session dirs |
| Session state schema | Structured 8-field state emitted periodically by running sessions | New hook + session state file format |
| Resume context injection | When attaching to a session, inject state summary as context | New `--resume <session-id>` flag |
| CHECKPOINT protocol | Formal pause-and-review points in command definitions | New frontmatter syntax in `commands/*.md` |
| `claude-kit stats` | Weekly summary comparing sessions with vs. without kit | New command, reads sessions + benchmark results |

### Phase 4 — Workflow Definitions (v0.17 → v0.20)
*Multi-agent pipelines as first-class citizens.*

| Feature | What it is | Notes |
|---------|-----------|-------|
| Workflow plugin type | New plugin role (`"role": "workflow"`) with DAG task definitions | New plugin category, new schema |
| Typed command interfaces | `input:`, `preconditions:`, `postconditions:` in command frontmatter | Schema extension, validator update |
| Context bridge handoff | Structured format for passing agent 1 output to agent 2 | New convention in workflow definitions |
| Three-tier knowledge | Static skills + RAG-selected extended + on-demand reference | Architectural extension to skill loading |
| `claude-kit benchmark` | Formal benchmark runs with repeatable codebase state | New command, git integration |

### Phase 5 — Ecosystem (v0.20+)
*The ESLint path — community, composability, standards.*

| Feature | What it is | Notes |
|---------|-----------|-------|
| Plugin registry | Public index of community plugins with quality gating | External infrastructure |
| `extends` pattern | Plugins that build on other plugins (like ESLint configs) | Metadata + resolution change |
| `team.json` org config | Organization-level plugin and rule configuration | New config format |
| `claude-kit learn` | Onboarding experience for AI-native engineers | New interactive command |
| AGENTS.md export | Generate cross-tool compatible AGENTS.md from instrumentation | Extension to `core-kit:instrument` |

---

### The North Star Command

When the roadmap is complete, this should work:

```bash
claude-kit -y -k core -k cloud-python --prompt "implement the auth service per docs/auth-spec.md" --debug
```

And the user should see:

```
  ┌─────────────────────────────────────────────────────────────┐
  │  claude-kit v0.20.0   cloud-python team   opus   autonomous  │
  │  debug: on   session: 2026-02-27T14-32   log: ~/.ck/...      │
  └─────────────────────────────────────────────────────────────┘

  [claude-kit:session] cloud-python-engineer + cloud-python-knowledge + core-kit
                skills: python-backend, distributed-systems, design-patterns (+4)
                invariants: 8 active   hooks: 6 active   mode: autonomous

  [claude-kit:route] "implement the auth service per docs/auth-spec.md"
              → cloud-python-engineer:engineer
              match: implement + service + spec reference → engineer workflow

> ...Claude starts working, tools fire, code gets written, hooks validate...

  [claude-kit:hook] Stop → grader (auto-spawned)
             score: 8.5/10   issues: 2 warnings
             session logged → ~/.claude-kit/sessions/2026-02-27T14-32/
```

The developer watched it happen. The log captured it. The grader scored it.
Next week, `claude-kit stats` shows whether that 8.5 is trending up.

That's the glass box.
