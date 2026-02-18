# Agent Profile Architecture - Creating "Taste"

## What Creates Consistent Output ("Taste")

When a senior engineer writes code, their output is consistent because of:

| Human Behavior | Claude Code Primitive |
|---|---|
| Patterns they always reach for | Instructions + examples (rules, identity.md) |
| Things they always check first | Hooks (PreToolUse: must read docs before writing) |
| Things they refuse to do | Hooks (PreToolUse: block anti-patterns) |
| The order they work in | Skills (step-by-step workflows) |
| Where they look for answers | MCP servers (live doc fetching, GitHub search) |

An agent is not a prompt. **An agent is a configuration surface:**

```
agent = identity + rules + hooks + skills + MCP tools + examples
```

## The Identity File

The most important part. Not generic instructions - the personality and methodology:

```markdown
## Who You Are
You are a senior embedded systems engineer with 15 years of Zephyr RTOS experience.

## Your Methodology (Always Follow This Order)
1. UNDERSTAND: Read API docs and datasheets BEFORE writing code
2. INTERFACE: Define the public API first (header file)
3. STUB: Create compilable stub, verify it builds
4. IMPLEMENT: Fill in implementation following examples
5. TEST: Write ztest tests, run with twister

## Non-Negotiables
- NEVER allocate heap in ISR context
- NEVER busy-wait
- ALWAYS use Zephyr device driver model
- ALWAYS check return codes

## When Stuck
1. Search docs (MCP tool)
2. Search vendor SDK (MCP tool)
3. Read the datasheet (MCP tool)
4. NEVER guess API signatures
```

## What Makes This Different From "Just a Good Prompt"

| Just a Prompt | Profile Framework |
|---|---|
| "You're an embedded expert" | identity.md with methodology, non-negotiables, patterns |
| Knows things generally | MCP servers fetch live, current API docs before coding |
| Might follow patterns | Hooks block code writes until docs are read |
| Might test | Hooks run test framework after every edit |
| Different output every time | Examples give concrete reference for consistent style |
| No way to measure | Benchmarks with prompts + rubric + automated scoring |
| Can't switch contexts | Plugin install/activation per domain |
| Generic for everyone | Profile encodes YOUR org's patterns, APIs, conventions |

## The Measurement Framework

### Benchmark Structure
```jsonl
{"id": "driver-tmp117", "prompt": "Implement a Zephyr sensor driver for the TI TMP117 I2C temperature sensor.", "difficulty": "medium"}
{"id": "ble-hrs", "prompt": "Create a BLE heart rate service peripheral using Zephyr Bluetooth APIs.", "difficulty": "medium"}
{"id": "tls-mqtt", "prompt": "Write an MQTT client using Zephyr TLS socket API with reconnect logic.", "difficulty": "hard"}
```

### Scoring Rubric Dimensions
1. **Correctness** (1-10): Compiles, runs, handles edge cases
2. **API Adherence** (1-10): Uses correct Zephyr APIs with correct signatures
3. **Pattern Consistency** (1-10): Matches org examples and conventions
4. **Safety** (1-10): No heap in ISR, no busy-wait, return codes checked
5. **Completeness** (1-10): Error handling, edge cases, documentation

### A/B Testing Process
1. Run each benchmark prompt WITH profile active
2. Run same prompt WITHOUT profile (vanilla Claude)
3. Score both outputs against rubric
4. Use LLM judge or automated tests for scoring
5. Compare aggregated scores

## Profile Composition

Profiles can share rules:
```
embedded-zephyr plugin ──→ inherits from security-baseline plugin
cloud-k8s plugin ──────→ inherits from security-baseline plugin
```

Shared rules (security, git conventions, testing philosophy) live in a separate base plugin or in the org's managed CLAUDE.md.

## The Implementation Path

See [09-plugin-system.md](./09-plugin-system.md) for how profiles map to Claude Code plugins.
