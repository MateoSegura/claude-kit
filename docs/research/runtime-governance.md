# Runtime Governance for AI Agents
# Contracts, Reversibility, and Safety Enforcement

> A design research document exploring the theoretical foundations and practical
> patterns for governing autonomous AI agent behavior at runtime — with specific
> implications for claude-kit's hook architecture.

**Date:** 2026-02-28
**Governing Process:** PROC-LC-001 (Market Analysis)

---

## Table of Contents

1. [Framing the Problem](#1-framing-the-problem)
2. [The Spectrum of Enforcement Mechanisms](#2-the-spectrum-of-enforcement-mechanisms)
3. [Constitutional AI and Value Embedding](#3-constitutional-ai-and-value-embedding)
4. [Semantic Reversibility in Agentic Systems](#4-semantic-reversibility-in-agentic-systems)
5. [Tool Use Safety Patterns](#5-tool-use-safety-patterns)
6. [Formal Runtime Verification](#6-formal-runtime-verification)
7. [Reproductive Pruning and Controlled Variation](#7-reproductive-pruning-and-controlled-variation)
8. [Implications for claude-kit](#8-implications-for-claude-kit)
9. [Sources](#sources)

---

## 1. Framing the Problem

### 1.1 The Governance Gap

Traditional software systems enforce contracts at compile time (type systems,
static analysis), at deployment time (CI gates, access control), and at runtime
(assertions, exception handlers). These mechanisms work because program
behavior is deterministic: given the same inputs, the same code path executes,
and violations are precisely detectable.

Autonomous AI agents break every assumption this model rests on.

An LLM-based agent is **stochastic** — the same goal produces different
sequences of tool calls on different runs. It is **opaque** — there is no
source code to audit between the user's request and the agent's action; there
is only a probability distribution over tokens. It is **adaptive** — it
interprets instructions contextually, so the same instruction may produce
different behaviors in different conversation states. And it is
**consequential** — it can delete files, push code, execute SQL, call external
APIs, and trigger deployments.

A 2025 survey of deployed agentic systems found that while 80% of Fortune 500
companies used active AI agents in some form, fewer than half had comprehensive
governance in place to manage their access, permissions, or behavioral bounds
(Microsoft Security Blog, 2026). This is the governance gap: agents are
trusted with consequential capabilities before the infrastructure to constrain
them safely has matured.

### 1.2 The Runtime as Contract

The framing from the podcast transcript that motivates this document is apt:
"A traditional runtime is just a passive executive. For autonomous systems, the
runtime has to evolve into active contract enforcement — a semantic or moral
contract. We need the operating system to become something like a constitutional
court effectively judging actions against a set of enshrined values or
constraints."

This is not merely metaphor. Two recent academic frameworks operationalize
exactly this vision:

- **AgentSpec** (Wang, Poskitt, Sun — ICSE 2026) defines a domain-specific
  language for runtime enforcement of agent constraints, with triggers,
  predicates, and enforcement mechanisms that fire before or after each tool
  call. It achieves >90% prevention of unsafe executions across code, embodied,
  and autonomous vehicle agents.
- **Agent Behavioral Contracts (ABC)** (arXiv 2602.22302) formalizes behavioral
  expectations as a tuple (Preconditions, Invariants, Governance constraints,
  Recovery mechanisms) with probabilistic satisfaction guarantees and bounded
  drift proofs under Lyapunov stability analysis.

What these systems describe is precisely what claude-kit's hooks implement — but
at different levels of formalism. Understanding the theoretical landscape
clarifies what the current hooks do, what they cannot do, and what principled
extensions would look like.

### 1.3 Scope

This document covers:
- Where hooks sit on the enforcement spectrum and what each zone can/cannot
  enforce
- Constitutional AI: the difference between trained-in and runtime-injected
  constraints
- Semantic reversibility: the formal concept and its application to file editing,
  git operations, and bash commands
- Tool safety patterns from academic frameworks and production deployments
- Formal runtime verification as the theoretical ancestor of hook-based enforcement
- Reproductive pruning as a model for managing plugin variation
- Concrete proposals for extending claude-kit's governance architecture

---

## 2. The Spectrum of Enforcement Mechanisms

There is a continuous spectrum from enforcement that happens long before
execution to enforcement that happens long after. Each zone has different
expressiveness, cost, and failure modes.

### 2.1 The Five Zones

| Zone | When | Mechanism | Catches | Misses |
|------|------|-----------|---------|--------|
| **Static analysis** | Before execution, before deployment | Type checking, linting, symbolic execution | Type errors, known anti-patterns, unreachable code | Behavioral violations, context-dependent errors, runtime values |
| **Pre-execution enforcement** | At execution boundary, before action | `PreToolUse` hooks, permission gates, plan approval | Dangerous commands, unauthorized file targets, format violations | Actions that look safe but are semantically wrong in context |
| **Runtime monitoring** | During execution, observing | Logging, tracing, anomaly detection | Behavioral drift, unexpected patterns | Nothing — monitors observe, they do not block |
| **Runtime enforcement** | During execution, blocking | `PreToolUse` block (exit 2), `PostToolUse` decision block | Tool-level violations with semantic context available | Actions between tool calls; cross-session violations |
| **Post-execution validation** | After action completes | `PostToolUse` hooks, compensating transactions, `Stop` verification | Results that are wrong despite syntactically valid actions | The action itself — compensation must undo what was done |

For autonomous AI agents, **pre-execution enforcement** and **post-execution
validation** are the practical workhorse zones. Runtime monitoring alone is
insufficient because agents act faster than humans can respond to alerts.
Static analysis is insufficient because the agent's behavior is determined by
context that cannot be known statically.

### 2.2 Mapping Hook Events to the Enforcement Spectrum

Claude Code's hook system provides anchor points at four positions on this
spectrum:

```
Static          Pre-execution         Post-execution         Session-end
analysis        enforcement           validation             verification
   |                 |                     |                      |
   |           PreToolUse            PostToolUse               Stop
   |           (block: exit 2)       (block: decision)         (block: decision)
   |                 |                     |                      |
   |          SessionStart             PostToolUse            TaskCompleted
   |          (observe)                (observe, async)       (observe)
```

**PreToolUse** sits at the pre-execution enforcement zone. It fires before the
tool executes, receives the tool's full input (the command to be run, the file
to be written, the path to be edited), and can return exit code 2 to block the
operation entirely. This is where the blast-radius reduction happens.

**PostToolUse** spans the boundary between runtime enforcement and post-
execution validation. A synchronous PostToolUse hook that returns
`{"decision": "block"}` is runtime enforcement — it rejects the result and
feeds back to Claude. An asynchronous PostToolUse hook that runs tests in the
background is post-execution validation — it cannot undo the file write, but
it can catch semantic errors and surface them in the next turn.

**Stop** is post-execution validation at the session level. It fires when the
agent believes it has completed the task, before the session actually ends. An
agent Stop hook with `{"decision": "block", "reason": "..."}` forces the agent
to continue. This is where completeness verification belongs: not "did this
specific tool call follow the rules?" but "did this session produce a coherent,
correct result?"

**SessionStart** is an observation point with no enforcement capability. It
can provide environmental warnings and context injection, but cannot block
the session from beginning.

### 2.3 What Each Zone Cannot Do

Understanding the limits of each zone is as important as understanding its
capabilities.

**PreToolUse cannot evaluate semantic correctness.** A PreToolUse hook on
`Bash` can block `rm -rf /` with a regex. It cannot determine whether
`kubectl delete pod my-service-abc123` is the right pod to delete. The
semantic correctness of a specific action in a specific context exceeds what
a deterministic shell script can evaluate.

**PostToolUse cannot undo writes.** Once a `Write` or `Edit` tool has
executed and the PostToolUse hook fires, the file has changed. A PostToolUse
hook can inject feedback that causes Claude to revert the file in a
subsequent turn, but this is not rollback — it is a new write. The first
write happened.

**Stop hooks cannot enforce session-level invariants across sessions.** A Stop
hook can verify that tests pass before the current session ends. It cannot
verify that the changes made in this session are consistent with decisions made
in a previous session. Cross-session invariants require external state (a spec
file, a decision log) that both sessions read.

**No hook event fires between tool calls.** There is no hook for "the agent
has decided to do X and is about to sequence a series of tool calls." The
finest granularity available is individual tool use events.

### 2.4 The Enforcement Tradeoff Table

| Property | PreToolUse | PostToolUse | Stop |
|----------|-----------|------------|------|
| **Can block action** | Yes (exit 2) | Partial (decision: block rejects result) | Yes (decision: block) |
| **Has action context** | Full tool input | Full tool input + output | Full conversation |
| **Can reason semantically** | Expensive (agent/prompt hook) | Expensive (agent/prompt hook) | Recommended (agent/prompt hook) |
| **Cost per session** | Per tool call | Per tool call | Once |
| **Cross-fire risk** | High if prompt/agent type | High if prompt/agent type | Low (session-aware preamble) |
| **Appropriate hook type** | command (deterministic) | command (deterministic, async) | prompt or agent |

---

## 3. Constitutional AI and Value Embedding

### 3.1 What Constitutional AI Is

Anthropic's Constitutional AI (CAI) approach, introduced in 2022, trains AI
systems to align with a set of principles — a "constitution" — through a two-
phase process:

1. **Supervised learning phase**: The model generates responses, then self-
   critiques those responses against the constitutional principles, then
   generates revised responses that better satisfy those principles. This
   produces a dataset of (prompt, revised_response) pairs.

2. **RLHF from AI feedback (RLAIF)**: Rather than using human raters, an LLM
   evaluates response pairs against the constitutional principles and generates
   preference labels. These labels train a reward model that guides
   reinforcement learning.

The constitution itself is explicit: it includes principles derived from the
UN Declaration of Human Rights, trust-and-safety frameworks, and ethical
guidelines. Anthropic's 2024 update to Claude's constitution introduced more
granular principles covering agentic behavior, code execution, and tool use.

### 3.2 Trained-in Constraints vs. Runtime-Enforced Constraints

This distinction is fundamental to understanding both the power and the limits
of Constitutional AI as a governance mechanism.

**Trained-in constraints** (from CAI) operate by shaping the model's internal
probability distribution. The model learns that certain response patterns are
preferable, and this preference is baked into the weights. At inference time,
the model "wants" to follow these constraints — they are genuinely internalized.

Advantages:
- Zero latency (no external call required)
- Applies universally without explicit configuration
- Generalizes to novel situations the constitution didn't explicitly enumerate
- Degrades gracefully (wrong answers, not crashes)

Failure modes:
- **Specification incompleteness**: The constitution cannot enumerate every
  situation. Edge cases not covered by the constitution are handled by
  generalization, which may be wrong.
- **Gaming**: A sufficiently adversarial prompt can cause the model to reason
  that a harmful action is actually permitted under the constitution (jailbreak
  attacks exploit this).
- **Distribution shift**: The model was trained on a distribution of prompts. A
  sufficiently out-of-distribution prompt may trigger behaviors that violate
  the constitution even though the model "knows" better.
- **Unverifiability**: It is impossible to audit whether a trained-in constraint
  is actually enforced for an arbitrary input. You can test, but you cannot
  prove.

**Runtime-enforced constraints** (from hooks) operate by intercepting the
model's actions before they take effect. The model proposes an action; the
runtime evaluates the action against explicit rules; the runtime either allows
or blocks it.

Advantages:
- Deterministic for deterministic rules (a regex either matches or it doesn't)
- Auditable (the rule is readable code, not weights)
- Updatable without retraining (change the hook script, not the model)
- Layerable (multiple hooks from multiple plugins can compose)

Failure modes:
- **Rule incompleteness**: Explicit rules cannot enumerate every dangerous
  action. `rm -rf /home/user` is blocked, but `rm -rf ./project-root` (the
  project root, not the system root) may not be.
- **Specification gaming at the action level**: The model may learn (in a
  multi-session context) that certain phrasings of commands avoid the hook
  while achieving the same effect.
- **Context blindness**: A hook that blocks `DROP TABLE` cannot know whether
  this specific drop is safe (it's a test database) or catastrophic (it's
  production). Rules act on syntax, not semantics.

### 3.3 The Complementary Architecture

The key insight is that trained-in and runtime-enforced constraints are
**complementary, not competing**. They defend against different failure modes.

```
Constitutional AI (training-time)          claude-kit hooks (runtime)
────────────────────────────────────       ────────────────────────────
Broad behavioral dispositions              Specific action restrictions
Generalizes to novel situations            Catches known dangerous patterns
Cannot be audited action-by-action         Fully auditable, loggable
Can be "reasoned around" by prompts        Cannot be bypassed by prompting
Applies without configuration              Requires explicit rule authoring
Slow to update (requires retraining)       Instant to update (edit a script)
Catches semantic errors                    Catches syntactic/structural errors
```

An agent that has Constitutional AI training AND runtime hooks provides defense
in depth: the training makes the model unlikely to attempt dangerous actions,
and the hooks catch the cases where it tries anyway.

### 3.4 Claude's Agentic Safety Principles as Constitutional Content

Anthropic has published explicit agentic safety guidelines that represent
deployed constitutional content for agentic contexts:

- **Minimal footprint**: Agents should request only necessary permissions,
  avoid storing sensitive information beyond immediate needs, prefer reversible
  over irreversible actions, and err toward doing less and confirming when
  uncertain about intended scope.
- **Human oversight preservation**: Agents should avoid actions that would
  undermine the ability of operators or users to adjust, correct, retrain, or
  shut down AI systems.
- **Prompt injection resistance**: Agents should maintain skepticism toward
  instructions embedded in content they process (files, web pages, tool
  outputs) that attempt to override their operating instructions.
- **Cautious in novel situations**: Agents should treat unexpected situations
  that fall outside their expected operating context as triggers for pausing
  and checking, rather than proceeding autonomously.

These principles are trained into Claude via Constitutional AI. They create
a disposition toward safe behavior that does not require explicit rule
configuration. But they are insufficient alone: an agent genuinely trying to
follow "prefer reversible actions" will still sometimes make irreversible
actions because it incorrectly classified the action as reversible.

### 3.5 Skills as Runtime-Injected Constitutional Content

claude-kit's skill system occupies an interesting intermediate position between
training-time constitutions and runtime hooks. Skills are injected into the
model's context window at session start — they are not hooks (they do not
intercept tool calls), but they are not training either (they are read from
files, not baked into weights). They are **runtime-injected context that shapes
the model's probability distribution for the session**.

This is more robust than relying purely on training because:
- Skills can be updated without retraining
- Skills can be project-specific (the embedded Zephyr engineer has different
  "laws" than the cloud Python engineer)
- Skills can be audited (a developer can read the SKILL.md files)
- Skills degrade gracefully to trained defaults if removed

But skills have a fundamental vulnerability that hooks do not: they can be
"reasoned around." If a skill says "never use `git reset --hard`" and the
model encounters a prompt that presents a compelling argument for why
`git reset --hard` is appropriate in this specific case, the model may comply.
The hook that blocks `git reset --hard` cannot be argued with — it is not an
instruction, it is a runtime intercept.

The practical architecture for claude-kit is therefore:
1. **Skills** encode high-level behavioral guidance and domain knowledge
2. **Hooks** enforce non-negotiable operational constraints
3. **Constitutional AI training** provides the underlying disposition toward
   safe, helpful behavior

---

## 4. Semantic Reversibility in Agentic Systems

### 4.1 The Reversibility Spectrum

The concept of "semantic reversibility" from the podcast transcript refers to
something more nuanced than simple undo: it is the question of whether an
action can be semantically undone — whether its effects can be removed from the
world, not just rolled back in a database.

Actions exist on a spectrum from trivially reversible to permanently
irreversible:

```
Reversible ◄────────────────────────────────────────────► Irreversible

Read-only    In-memory     File write    Git commit   External API   Infra
operations   computation   (disk)        (local)      calls          changes
             No side       git checkout  git push     Email sent     K8s ns
             effects       restores      (with force) (to user)      deleted
```

**Trivially reversible**: Reading a file, running a computation that produces
output, listing directory contents. The world is unchanged.

**Practically reversible (with tooling)**: Writing a file (can be overwritten or
deleted), creating a branch (can be deleted), adding a git commit (can be
reverted). Reversal requires explicit action but leaves no permanent trace.

**Reversible with difficulty**: Pushing a git commit to a shared remote (can be
force-reverted, but other developers may have pulled). Running a database
migration (can be rolled back, but data may have been written against the new
schema). The reversal exists but may have cascading effects.

**Practically irreversible**: Sending an email or notification to external users,
deleting a Kubernetes namespace (`kubectl delete namespace`), dropping a
production database table, posting to an external API that doesn't support
deletion. The action's effects propagate beyond the system boundary where they
can no longer be controlled.

**Permanently irreversible**: Exfiltrating data, publishing credentials, making
financial transactions. Not only can the action not be undone, but its effects
cannot be contained.

### 4.2 The Saga Pattern: Compensating Transactions

The canonical pattern for managing irreversibility in distributed systems is
the **saga pattern**, introduced by Garcia-Molina and Salem (1987) as an
alternative to long-running transactions in distributed databases. A saga
is a sequence of local transactions where each step has a corresponding
**compensating transaction** — an inverse action that semantically undoes the
effect of the original.

```
Forward saga:
  T1 → T2 → T3 → T4 → SUCCESS

Compensating rollback (T3 fails):
  T1 → T2 → T3 (fail) → C2 → C1 → ROLLED BACK
```

Where Cn is the compensating transaction for Tn.

For database transactions, compensating transactions are well-defined: if T3
debits an account by $100, C3 credits it by $100. The compensating transaction
is designed alongside the forward transaction.

For AI agent actions, defining compensating transactions is harder because:
- Agents do not plan their action sequences in advance (so C cannot be defined
  alongside T)
- The compensating transaction for "write this file" is "restore the previous
  file content" — which requires capturing state before the action
- Some actions have no compensating transaction (you cannot un-send an email)

**SagaLLM** (arXiv 2503.11951, 2025) extends the saga pattern to LLM-based
multi-agent systems. Each workflow node is assigned both a regular agent and a
compensation agent. If a forward agent fails, the compensation agent executes
rollback logic. This provides structured recovery for multi-step agentic
workflows.

### 4.3 Reversibility of Specific Tool Types

For claude-kit, the relevant tool types and their reversibility profiles are:

| Tool | Operation | Reversible? | Compensating action |
|------|-----------|-------------|---------------------|
| `Read` | Read file | Always | N/A (no side effects) |
| `Glob` | List files | Always | N/A |
| `Grep` | Search content | Always | N/A |
| `Write` | Write new file | Practically | Delete the file |
| `Edit` | Modify file | Practically | Restore previous content (requires pre-capture) |
| `Bash` | `git commit` | Practically | `git revert` or `git reset` |
| `Bash` | `git push` | With difficulty | Force-push revert (may affect others) |
| `Bash` | `rm -rf ./dir` | Limited | Restore from git if tracked |
| `Bash` | `kubectl delete namespace` | Practically never | Recreate from manifests (stateful loss) |
| `Bash` | `curl -X POST api.external.com` | Never | Depends on API contract |
| `Bash` | `docker system prune` | Never | Rebuild images |

The pattern that emerges: pure read operations are always reversible. Write
operations that stay within the git working tree are practically reversible
(git tracks state). Operations that cross a system boundary — pushing to a
remote, calling an API, writing to a cloud resource — range from difficult to
irreversible.

### 4.4 Semantic Reversibility as a Hook Pattern

The "semantic reversibility" concept from the podcast suggests an undo buffer
that allows rolling back unsafe actions. Translating this to claude-kit's hook
architecture yields two concrete patterns:

**Pattern A: Pre-capture before irreversible operations**

A PreToolUse hook on `Write` and `Edit` tools captures the current file content
before the write occurs. This creates a local undo buffer:

```bash
#!/bin/bash
set -euo pipefail
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

BACKUP_DIR="${CLAUDE_PLUGIN_ROOT}/.undo-buffer"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%s%N)
SAFE_NAME=$(echo "$FILE_PATH" | tr '/' '_')

cp "$FILE_PATH" "${BACKUP_DIR}/${SAFE_NAME}.${TIMESTAMP}.bak"

# Keep only the last 10 backups per file to avoid unbounded growth
ls -t "${BACKUP_DIR}/${SAFE_NAME}."*.bak 2>/dev/null | tail -n +11 | xargs rm -f

exit 0
```

This does not prevent the write, but enables a later hook or command to restore
the state. It transforms the write operation from "practically reversible
(requires capturing state)" to "trivially reversible (state was pre-captured)."

**Pattern B: Approval gate before irreversible bash commands**

A PreToolUse hook on `Bash` identifies commands that cross the reversibility
threshold and either blocks them or injects a confirmation requirement. The
cloud-python-engineer's `block-dangerous-commands.sh` already implements this
for high-severity cases (exit 2 = hard block). For medium-severity cases,
the hook can emit a structured warning that causes Claude to pause and request
confirmation before proceeding — a human-in-the-loop gate.

The distinction between "hard block" and "approval gate" is significant:

```
Hard block (exit 2):         "This action is never permitted"
                              kubectl delete namespace production

Approval gate (advisory):    "This action is irreversible. Confirm intent."
                              kubectl delete namespace staging-xyz
```

Hard blocks should be reserved for actions whose harm cannot be bounded by
context. Approval gates should be used for actions that are sometimes
legitimate but require explicit authorization.

### 4.5 Git as Reversibility Infrastructure

Git deserves special treatment in the reversibility analysis because it is the
primary reversibility mechanism for file editing in a software development
context. Every `git commit` is a snapshot; every `git checkout` is a restore;
every `git revert` is a compensating transaction.

This means that for any file that is tracked by git, the reversibility
classification shifts dramatically:

- **Before `git commit`**: File writes are practically reversible (`git checkout
  -- <file>` restores)
- **After `git commit`, before `git push`**: The commit is reversible (`git
  reset --soft HEAD~1` preserves changes, `git revert` creates an undo commit)
- **After `git push` to a shared remote**: Reversibility depends on whether
  other developers have pulled and whether force-push is permitted

claude-kit's current hooks enforce commit message format and block force-push
to main. These are already reversibility-aware hooks: they prevent the step
where local history diverges from remote history in ways that are hard to undo.

A principled extension is a **reversibility level** declared in the hook
configuration:

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/classify-reversibility.sh",
          "description": "Classify command reversibility and apply appropriate enforcement level"
        }
      ]
    }
  ]
}
```

Where `classify-reversibility.sh` returns exit 0 for reversible commands, exit
2 for permanently irreversible ones, and an advisory message for the middle
tier.

---

## 5. Tool Use Safety Patterns

### 5.1 The Minimal Footprint Principle

Anthropic's documented agentic safety guidelines explicitly state that agents
should maintain a **minimal footprint**: request only necessary permissions,
prefer reversible actions, and do less when scope is uncertain.

This principle has a long lineage in security. The **principle of least
privilege** (Saltzer and Schroeder, 1975) states that every component of a
system should have access only to the information and resources necessary for
its legitimate purpose. Applied to AI agents, this means:

- An agent with read-only access cannot make irreversible changes
- An agent restricted to a specific directory cannot escape its scope
- An agent without network access cannot exfiltrate data or call external APIs

The minimal footprint principle is stronger than least privilege because it is
dynamic: even when an agent *has* a capability, it should use it minimally.
An agent with write access to the entire repository should still prefer writing
only to the files it needs to touch.

### 5.2 Least-Privilege Tool Access by Role

The five-role architecture in claude-kit (engineer, grader, tester, debugger,
knowledge) maps naturally to a graduated tool access policy:

| Role | Read | Write/Edit | Bash | Network | Rationale |
|------|------|-----------|------|---------|-----------|
| **knowledge** | Yes | No | No | No | Pure reference material; no side effects |
| **debugger** | Yes | Limited (logs only) | Limited (read-only cmds) | No | Diagnosis without modification |
| **grader** | Yes | Limited (reports only) | Limited (test runners) | No | Evaluation without modification |
| **tester** | Yes | Yes (test files only) | Yes (test cmds only) | No | Test authoring and execution |
| **engineer** | Yes | Yes | Yes | Limited | Full development capability |

The current implementation partially realizes this through `permissionMode:
plan` in agent frontmatter and role-specific protected file hooks. A systematic
tool restriction policy would add explicit tool allowlisting per role via
`tools:` frontmatter in agent definitions:

```yaml
---
name: cloud-python-grader
description: Reviews Python code for quality
tools: Read, Glob, Grep
# No Write, Edit, or Bash — graders should not modify code
---
```

This creates an enforcement layer that is independent of hooks: the platform
itself refuses the tool call before any hook fires.

### 5.3 Human-in-the-Loop Approval Patterns

Production AI agent frameworks have converged on a common pattern for
high-stakes actions: **interrupt-and-confirm** before execution.

**LangGraph** provides `HumanInTheLoopMiddleware` that can interrupt execution
at specified checkpoints and require human approval before continuing. This is
implemented as a state transition: the agent moves from `RUNNING` to
`AWAITING_APPROVAL`, and only resumes when the human provides input.

**AutoGen** implements human-in-the-loop through its `HumanProxyAgent`, a
special agent type whose responses come from a human rather than an LLM. The
orchestrating agent consults the human agent before taking designated
high-stakes actions.

**CrewAI** provides built-in human-in-the-loop gates through its task
configuration, where specific tasks can be marked `human_input=True`, requiring
approval before the task output is accepted.

Claude Code's permission system provides a similar mechanism: any tool call
can be configured to `ask` (prompt the user for approval), `allow` (execute
without prompt), or `block` (never permit). This is configurable per tool and
per glob pattern.

The gap in claude-kit's current hook architecture is that hooks fire before or
after tool execution, but they cannot natively trigger an approval gate mid-
session without blocking the entire session (exit 2). An approval-gate hook
that blocks with a specific structured message could signal Claude to request
explicit user confirmation before retrying — but this relies on Claude's
behavior, not on the hook mechanism itself.

A cleaner pattern is to use the PreToolUse hook to detect irreversible actions
and inject the requirement for confirmation into the feedback:

```bash
# In block-dangerous-commands.sh, for medium-severity actions:
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force-with-lease'; then
  echo "REQUIRES_CONFIRMATION: Force push detected. This will rewrite history on the remote." >&2
  echo "To proceed, explicitly confirm by stating: 'Confirmed: force push to <branch> is intentional'" >&2
  exit 2  # Block until explicit confirmation in prompt
fi
```

The exit 2 causes the tool to not execute, the message is surfaced to Claude,
and Claude requests confirmation from the user before rephrasing the command
with the confirmation text. This is an imperfect implementation of a formal
approval gate, but it works within the current hook model.

### 5.4 How Existing Frameworks Handle Tool Safety

A comparative survey of how major agentic frameworks handle tool safety reveals
four dominant patterns:

**Pattern 1: Tool allowlisting (static)**
The agent is initialized with an explicit set of tools it may use. Calls to
tools outside the allowlist are rejected by the platform. This is the approach
used by claude-kit's `tools:` frontmatter in agents.

**Pattern 2: Runtime policy evaluation**
Every tool call is evaluated against an access control policy before execution.
The FINOS Agent Authority Least Privilege Framework implements this with a
"tool manager" component that checks authorization before forwarding tool calls
to the underlying API. This is equivalent to what claude-kit's PreToolUse hooks
implement, but with a more formal policy language.

**Pattern 3: Gateway architecture (Proxy pattern)**
All agent tool calls pass through a centralized gateway that validates intent,
enforces authorization, and logs all activity. The Anthropic secure deployment
documentation recommends this for production environments: a Unix socket proxy
that mediates all agent network access, injecting credentials and enforcing
domain allowlists.

**Pattern 4: Ephemeral execution environment**
Agent actions run in short-lived isolated environments (containers, VMs,
gVisor-secured sandboxes) that are destroyed after each task. Even if the agent
takes an unauthorized action within the environment, the environment's
destruction limits the blast radius. Anthropic's sandbox-runtime implements
this with bubblewrap (Linux) and sandbox-exec (macOS).

claude-kit's hook system primarily implements Pattern 1 (tool allowlisting via
frontmatter) and Pattern 2 (runtime policy via shell scripts). Patterns 3 and
4 are infrastructure-level concerns that live outside claude-kit but compose
with it.

### 5.5 Tool Call Interception and Validation (AgentSpec Model)

AgentSpec (Wang, Poskitt, Sun 2026) provides the most formal model for tool
call interception available in the literature. An AgentSpec rule has three
components:

```
rule <name>:
  trigger: <event that activates the rule>
  predicate: <condition that must be true for rule to apply>
  enforcement: <action to take when predicate is satisfied>
```

Example: Block filesystem access to sensitive paths

```
rule protect-secrets:
  trigger: tool_call(name="Write")
  predicate: tool_arg("file_path") matches ".*\.(env|key|pem|credentials).*"
  enforcement: block("Attempt to write to sensitive file. Explicitly approve to override.")
```

This maps almost directly to claude-kit's PreToolUse hooks:
- **Trigger** → `"matcher": "Write|Edit"`
- **Predicate** → the condition checked in the hook script (`grep -qE '...'`)
- **Enforcement** → exit code 2 + stderr message

The key difference is that AgentSpec is a formal DSL with a parser, a
predicate evaluator, and a theorem prover that can check rule consistency. A
claude-kit hook is a bash script evaluated by the shell. The claude-kit
approach is less expressive (bash cannot express temporal predicates like
"if more than 3 write operations to the same file in the same session, block")
but it is lower overhead and requires no additional infrastructure.

---

## 6. Formal Runtime Verification

### 6.1 Runtime Verification as a Field

Runtime Verification (RV) is a branch of formal methods that studies the
dynamic analysis of program execution traces against formal specifications.
Rather than proving a program correct for all possible inputs (which is
generally undecidable), RV checks that a specific execution satisfies a
specification.

The fundamental setup:
1. A **specification** describes required or forbidden behaviors (typically in
   a temporal logic such as LTL or CTL)
2. A **monitor** is synthesized from the specification — a finite-state
   machine or Büchi automaton that processes the event stream from the running
   system
3. As the system executes and emits events, the monitor transitions through
   states and can output verdicts: `satisfied`, `violated`, or `inconclusive`

RV sits between testing (which checks specific inputs) and model checking (which
checks all possible inputs). It is sound for the traces it observes but not
complete — it can miss violations that only occur in unobserved executions.

### 6.2 LTL Monitors for Agent Behavior

Linear Temporal Logic (LTL) expresses properties over sequences of states
using temporal operators:

| Operator | Meaning | Example |
|----------|---------|---------|
| `G φ` | Globally: φ holds in all future states | `G (write → ¬sensitive_path)` |
| `F φ` | Finally: φ holds in some future state | `F tests_run` |
| `X φ` | Next: φ holds in the next state | `X (commit → valid_format)` |
| `φ U ψ` | Until: φ holds until ψ holds | `write U (tests_pass ∨ stop)` |

Applied to AI agent behavior:

- `G (bash_command → ¬destructive_pattern)`: Every bash command is not a
  destructive pattern. This is what `block-dangerous-commands.sh` enforces.

- `G (write_file → X (linter_pass))`: Every file write is followed by a
  linter pass. This is what the PostToolUse lint hooks enforce.

- `F (stop → tests_pass)`: Eventually, when the agent stops, tests pass. This
  is what Stop agent hooks enforce.

- `(push_to_remote → F human_confirmation) U stop`: Before any push to a
  remote, there is human confirmation, and this holds until the session ends.
  This is the human-in-the-loop property — currently not implemented in
  claude-kit's hook architecture.

Claude Code's hook system implements a subset of LTL safety properties —
specifically those that can be evaluated locally at the time of the relevant
event. It does not currently support temporal properties that span multiple
events (`U` — until), because hooks do not have access to a session-level
event log.

### 6.3 Agent Behavioral Contracts (ABC Framework)

The Agent Behavioral Contracts framework (arXiv 2602.22302) provides the
closest formal analog to what claude-kit hooks do. It defines a contract as
a tuple (P, I, G, R):

- **P (Preconditions)**: Conditions that must hold before the agent begins
  execution. In claude-kit, these map to SessionStart checks.
- **I (Invariants)**: Conditions that must hold throughout execution. These
  are the safety properties that every PreToolUse hook enforces.
- **G (Governance constraints)**: Restrictions on the agent's actions — which
  tools it may use, which paths it may write to, which commands it may run.
  These map to the protected file and dangerous command hooks.
- **R (Recovery mechanisms)**: Actions to take when soft constraints are
  violated. These map to PostToolUse validation hooks that inject feedback
  causing Claude to correct the violation.

The ABC framework distinguishes **hard constraints** (zero-tolerance safety
properties; violations are immediately flagged and execution is halted) from
**soft constraints** (recoverable violations; a recovery mechanism is
triggered, but execution continues). This maps to the exit code distinction in
claude-kit:

- `exit 2` on PreToolUse → hard constraint violation (block execution)
- Advisory output on PostToolUse → soft constraint violation (inject feedback)
- `{"decision": "block"}` on Stop → hard constraint at session boundary

The key formal contribution of ABC is the **Drift Bounds Theorem**: using
Lyapunov stability analysis, the framework proves that a contract with recovery
rate γ bounds behavioral drift to an equilibrium D* = α/γ, where α is the
drift rate. This provides a mathematical basis for the intuition that "hook
enforcement with feedback injection keeps agents close to correct behavior."

Without formal recovery mechanisms, compliance decays as q^T (exponentially
with session length, where q is the per-step compliance probability). With
recovery hooks, compliance degrades linearly — practically, agents that are
corrected when they make errors stay on track much longer than agents that are
simply blocked.

### 6.4 Pro2Guard: Proactive Enforcement

A limitation of AgentSpec and most hook-based enforcement is that it is
**reactive**: it blocks actions that are about to happen. An action at step N
may be harmless in isolation, but harmful because of the trajectory it sets up
for steps N+1 through N+k.

**Pro2Guard** (arXiv 2508.00500, 2025) addresses this with **probabilistic
model checking** applied to the agent's current state and action plan.
Rather than evaluating each action individually, Pro2Guard builds a Markov
Decision Process from the agent's observed behavior and predicts the probability
of reaching unsafe states k steps in the future.

For claude-kit, this suggests a future direction: rather than (or in addition
to) per-tool-call hooks, a session-level monitor that tracks the agent's action
trajectory and predicts whether the current plan is heading toward an
irreversible operation. If the predicted probability of an irreversible action
exceeds a threshold, the monitor injects a checkpoint requiring approval before
the agent continues.

This is architecturally more expensive than the current hook model (requires
a persistent session state and a model of the action space) but provides
qualitatively stronger safety guarantees for long multi-step workflows.

### 6.5 How Close Are claude-kit Hooks to Formal RV?

| Formal RV property | claude-kit equivalent | Gap |
|-------------------|-----------------------|-----|
| Specification language | Shell scripts + JSON | Informal; no theorem-proving |
| Monitor synthesis | Manual hook scripting | No automatic synthesis from specs |
| Safety properties (G φ) | PreToolUse checks | Fully supported |
| Liveness properties (F φ) | Stop hooks | Partially supported |
| Temporal properties (φ U ψ) | Not supported | No cross-event state |
| Probabilistic guarantees | Not supported | No statistical model |
| Completeness | Incomplete | Can miss inter-event violations |

The gap is significant at the formal level but smaller in practice. Formal RV
over AI agents faces the same challenge as formal verification generally: the
state space is too large to verify completely. claude-kit's hooks provide
practical enforcement at the cost of formal completeness guarantees.

---

## 7. Reproductive Pruning and Controlled Variation

### 7.1 The Concept from the Transcript

The transcript introduced "reproductive pruning" as a mechanism for managing
"controlled variation while culling unsafe variants." This framing applies
evolutionary computation concepts to AI agent system design: a population of
agent variants (skills, plugins, behaviors) exists, and a selection pressure
eliminates variants that are unsafe or low-quality.

The concept maps to three distinct problems in claude-kit:

1. **Plugin quality** — across the plugin library, some plugins are higher
   quality than others. How does the system identify and eliminate low-quality
   variants?
2. **Behavior variation** — an agent's behavior is non-deterministic. Across
   multiple sessions, some behavioral variants are safe and some are not. How
   does the system identify which variants are unsafe?
3. **Skill evolution** — skills that define agent behavior are periodically
   updated. How does the update process ensure that new versions are improvements
   rather than regressions?

### 7.2 Evolutionary Computation Background

Evolutionary algorithms (EAs) are a family of optimization methods inspired by
biological evolution. The core loop:

1. **Population initialization**: Generate a diverse set of candidate solutions
2. **Fitness evaluation**: Assess each candidate against an objective function
3. **Selection**: Prefer candidates with higher fitness for reproduction
4. **Variation**: Mutate and cross-combine selected candidates to generate new
   candidates
5. **Culling**: Eliminate candidates with low fitness
6. **Iteration**: Return to step 2

Applied to AI agent plugins:

- **Population**: All plugins in the library (or all plugins across team
  variants)
- **Fitness**: Quality scores from semantic review, user satisfaction, error
  rates in production
- **Selection**: Prefer plugins that consistently produce correct, safe,
  domain-appropriate outputs
- **Variation**: Updates to plugin content (skills, hooks, commands)
- **Culling**: Deprecation or removal of plugins that consistently fail

### 7.3 claude-kit's Existing Pruning Mechanisms

claude-kit already implements several informal reproductive pruning mechanisms:

**Nightly semantic review** (`nightly.yml`): The `nightly-plugin-review` workflow
runs a full semantic review of all plugins every night at 02:00 UTC. If WARN or
FATAL findings are detected, it automatically creates a fix branch, runs Claude
to auto-fix the issues, and opens a PR. This is fitness evaluation + culling: low-
fitness plugins (those with structural or semantic violations) are automatically
improved or flagged.

**Weekly cross-coherence audit** (`weekly.yml`): The `weekly-full-audit` runs Tier
1 validation and a full cross-coherence semantic review every Monday. Issues that
are not auto-fixable create a GitHub issue with the `audit-failure` label.

**PR semantic review** (`pr.yml` → `semantic-check`): Every PR that changes plugins
triggers a focused semantic review of the changed plugins. This is selection
pressure at the contribution level: only PRs that pass semantic review merge.

**Validate-all command**: The `/validate-all` command runs Tier 1 validation plus
semantic review on demand, providing fitness evaluation on demand.

These mechanisms together implement a continuous improvement cycle analogous to
an evolutionary algorithm's fitness-evaluate-select-cull loop. The "population"
is the set of deployed plugins; the "fitness function" is the combination of
structural validation + semantic quality scoring; the "culling" is the auto-
fix PRs and audit failure issues.

### 7.4 Formalization: A Safety Level System

The reproductive pruning concept suggests a more formal approach: each plugin
could declare a **safety level** that determines which enforcement mechanisms
apply to it.

```json
{
  "safety_level": "strict",
  "hooks": { ... }
}
```

| Level | Meaning | Hook enforcement | Review cadence |
|-------|---------|-----------------|----------------|
| `experimental` | Unproven plugin | Advisory warnings only | Every session |
| `standard` | Production plugin | Full hook enforcement | Nightly |
| `strict` | High-stakes plugin | Full hooks + human approval gates | Every commit |
| `certified` | Formally audited | Full hooks + formal spec validation | Continuous |

An `experimental` plugin fires hooks that warn but do not block, making it
safe to iterate rapidly. A `certified` plugin fires hooks that block violations
and has been formally reviewed against explicit safety specifications.

This mirrors A/B testing and gradual rollout patterns in software deployment:
new plugin features start at `experimental`, accumulate confidence through
repeated use without incidents, and graduate to `standard` or `strict` as
evidence of safety accumulates.

### 7.5 The Variation Problem: Managing Non-Determinism

The deepest challenge the "reproductive pruning" framing highlights is managing
behavioral variation across sessions of the same agent. Because LLMs are
stochastic, two sessions with the same prompt and the same hooks may produce
different action sequences. Some sequences are safe; some are not.

The current hook architecture addresses this through **invariant enforcement**:
by making certain properties unconditionally enforced regardless of the agent's
reasoning, you create a safety floor below which no behavioral variant can fall.
Even the worst possible session cannot perform a hard-blocked action.

The evolutionary framing adds a complementary mechanism: **session-level fitness
evaluation** as a feedback signal. If sessions could report:
- "This session completed without any hook violations" → high fitness
- "This session had 3 advisory warnings and 1 blocked action" → lower fitness
- "This session attempted an irreversible action and required human intervention"
  → low fitness

Then aggregate fitness statistics across sessions could identify whether a
plugin's hooks are correctly calibrated (blocking dangerous actions that agents
reliably attempt) or miscalibrated (blocking actions that agents should be
performing, or failing to block actions they should not).

---

## 8. Implications for claude-kit

### 8.1 Architectural Gaps

Synthesizing the research across all six dimensions reveals four significant
gaps in claude-kit's current governance architecture:

**Gap 1: No cross-event temporal state**
Current hooks evaluate each event in isolation. There is no mechanism for a
hook to say "this is the third write to this file in the last five minutes —
escalate." Temporal properties require session-level state accumulation. This
would require a hook that persists a session log and reads it on each event.

**Gap 2: No reversibility classification**
Current hooks block specific dangerous commands, but they do not classify the
reversibility of arbitrary commands. An agent that wants to run a complex
pipeline of commands gets all-or-nothing enforcement: either the command is in
the blocklist and is blocked, or it is not and proceeds without any reversibility
assessment.

**Gap 3: No formal approval gate**
The closest thing to a human-in-the-loop approval gate in the current
architecture is a hard block (exit 2) that surfaces as an error to Claude. A
formal approval gate would interrupt execution, surface the action to the user
with context, and wait for explicit authorization before proceeding.

**Gap 4: No graduated enforcement by plugin maturity**
All plugins currently receive the same enforcement. An experimental plugin with
unproven hooks enforces just as hard as a battle-tested plugin with audited
hooks. A safety level system would allow enforcement strength to track plugin
maturity.

### 8.2 Higher-Level Semantic Contracts

The current hooks enforce format-level contracts: "commit messages must match
this regex," "files matching this pattern are protected." A richer contract
system would enforce semantic-level contracts:

**Semantic contract examples:**

- **Completeness contract**: "Before stopping, every modified file must have a
  corresponding test that was run and passed." Current hooks enforce test
  *existence* (advisory); a semantic contract would enforce test *execution and
  passage*.

- **Consistency contract**: "When you modify the API of a function, all call
  sites must also be updated before the session ends." This requires a PostToolUse
  agent hook that reads all imports of the modified file and checks for signature
  mismatches.

- **Scope contract**: "The engineer agent should only modify files within the
  currently active spec's defined scope." This requires reading the active spec
  from `core-spec` state and validating that each write falls within the declared
  scope.

- **Dependency contract**: "No new external dependencies may be added without
  explicit user approval." A PreToolUse hook on `Write` to `package.json` or
  `pyproject.toml` could diff the dependencies section and block additions.

These semantic contracts are implementable with the current hook architecture
(particularly Stop agent hooks that can reason over the full conversation
context), but they require more sophisticated hook implementations than the
current format-enforcement hooks.

### 8.3 Role-Differentiated Hook Enforcement

The five agent roles (engineer, grader, tester, debugger, knowledge) currently
share the same category of hook enforcement (dangerous command blocking, file
protection). A principled least-privilege enforcement policy would differentiate
enforcement by role:

| Hook | engineer | grader | tester | debugger | knowledge |
|------|---------|--------|--------|---------|-----------|
| Block `rm -rf` on sensitive paths | Yes | Yes | Yes | Yes | Yes (universal) |
| Block `git push --force` | Yes | N/A | N/A | N/A | N/A |
| Block writes to non-test files | No | Yes | Partial | Yes | Yes |
| Block `kubectl delete` | Yes | Yes | No | Yes | Yes |
| Block new external dependencies | Approval gate | Yes | No | Yes | Yes |
| Require test passage before Stop | Yes | No | Yes | No | No |

The grader role should be particularly locked down: a grader that modifies
source code violates the fundamental purpose of a grader (it should be an
objective evaluator, not a modifier). Similarly, the debugger role should be
read-heavy and write-minimal — debugging is diagnosis, not surgery.

Implementation sketch for a grader-specific write protection:

```bash
#!/bin/bash
set -euo pipefail
# protect-source-files.sh — Grader role: block writes to non-report files
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Allow writes to report files (grader-reports/ directory)
if echo "$FILE_PATH" | grep -qE 'grader-reports/|\.grade\.(md|json)$'; then
  exit 0
fi

# Block writes to source files
echo "BLOCKED: Grader role cannot modify source files." >&2
echo "  File: $FILE_PATH" >&2
echo "  Graders read and evaluate; they do not modify." >&2
echo "  Write your evaluation to grader-reports/ instead." >&2
exit 2
```

### 8.4 Constitutional Skill Content

A "constitutional" skill would define invariants the agent must never violate —
expressed not as hook scripts but as context-window content that the model reads
before acting. This is the hybrid approach: skills as soft constitutions,
hooks as hard enforcement.

Constitutional skill content for the engineer role might include:

```markdown
## Engineer Invariants

The following are unconditional constraints. No argument justifies violating them.

1. **Never delete files without explicit user instruction.** If deletion is
   necessary, move files to a `.archived/` directory and confirm with the user.

2. **Never commit without running validation.** Before any `git commit`, run
   `claude-kit validate --changed` or the project's equivalent validation.

3. **Never push without testing.** Before any `git push`, the test suite must
   pass. Non-negotiable.

4. **Never modify another user's files.** Files owned by other team members
   (identified by git blame) require their explicit approval.

5. **Never make more than one irreversible action without pausing.** If you
   have just taken an irreversible action (pushed to remote, called an external
   API), stop and check in with the user before taking another.
```

These invariants are "constitutional" in the sense that they are designed to
be universally applied, non-negotiable, and resistant to contextual overriding.
The complementary hook would enforce the ones that can be enforced
mechanically (never commit without validation = PostToolUse on Bash matching
`git commit` that validates the working tree), while leaving the semantic ones
to the skill-injected constitutional content.

### 8.5 A Semantic Reversibility Hook Architecture

Translating the reversibility analysis into a concrete hook architecture:

**Layer 1: Pre-capture (PreToolUse on Write|Edit)**
Every file write pre-captures the current content to an undo buffer. This is
always safe (read-only, never blocks).

**Layer 2: Reversibility gate (PreToolUse on Bash)**
Commands are classified by reversibility:
- Class A (reversible): proceed without comment
- Class B (difficult): emit advisory warning, proceed
- Class C (practically irreversible): emit advisory, require confirmation pattern
- Class D (permanently irreversible): hard block, require explicit override

**Layer 3: Reversibility audit (Stop hook)**
Before session end, the Stop agent reviews the session's action log and flags
any Class D actions that were taken, providing a summary of what cannot be
undone.

**Layer 4: Git checkpoint (PostToolUse on Bash matching `git commit`)**
After each commit, emit a reversibility summary: "Local commit abc123 is
reversible. Run `git push` to make it persistent (difficult to reverse)."

This architecture gives the agent — and the user — continuous visibility into
the reversibility profile of the session, without preventing any class of action
by default. The hard blocks (Class D) are reserved for actions where the harm
is irreversible and unbounded.

### 8.6 The Constitutional Court Model in Practice

The podcast's metaphor of "the runtime as constitutional court" is apt if
understood correctly. A constitutional court does not evaluate every decision
— it evaluates decisions against enumerated principles. It is fast for cases
that clearly violate principles (unanimous block), deliberative for ambiguous
cases, and completely passive for cases that clearly comply.

Mapping this to claude-kit:
- **Clear violations** → deterministic command hooks (fast, no LLM cost)
- **Ambiguous cases** → prompt or agent hooks at Stop (one LLM call per session)
- **Clear compliance** → no hook fires, no cost

The mistake would be to put the constitutional court in the hot path of every
tool call. A court that must rule on every action is not a court — it is a
permission bureaucracy that collapses under its own overhead.

The correct architecture: hooks in the hot path (PreToolUse, PostToolUse) are
always deterministic shell scripts. The "constitutional" reasoning — semantically
evaluating session-level compliance — lives in Stop hooks, which fire once per
session and can afford LLM-level reasoning.

### 8.7 Implementation Roadmap

Prioritized by value/effort ratio for claude-kit:

| Priority | Change | Mechanism | Effort |
|----------|--------|-----------|--------|
| **High** | Role-differentiated write protection for grader and debugger | PreToolUse Write hooks per plugin | Low |
| **High** | Reversibility classification for bash commands (Classes A-D) | Extend block-dangerous-commands.sh | Medium |
| **Medium** | Pre-capture undo buffer for file writes | New PreToolUse Write hook | Medium |
| **Medium** | Constitutional skill content for each team/role | New SKILL.md sections | Low |
| **Medium** | Safety level declaration in ctl.json | Schema addition + validation update | Medium |
| **Low** | Session-level action log for temporal properties | New hook infrastructure | High |
| **Low** | Formal approval gate middleware | Plugin architecture change | High |
| **Low** | Pro2Guard-style predictive enforcement | Requires session state model | Very High |

The highest-value immediate changes are:
1. Adding role-differentiated enforcement (the grader should not be able to
   write source files)
2. Extending the reversibility classification (distinguishing hard blocks from
   advisory gates)
3. Adding constitutional invariant sections to the existing identity skills

These require no architectural changes to the hook system — only additional
hook scripts and skill content.

---

## Traces

- **Upstream:** Market signals, competitive analysis, user research
- **Downstream:** REQ-004 (Runtime Enforcement)
- **Quality Attributes:** None identified

---

## Sources

- [AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents](https://arxiv.org/abs/2503.18666) — Wang, Poskitt, Sun. ICSE 2026. The primary academic reference for declarative runtime enforcement of LLM agent constraints.

- [Agent Behavioral Contracts: Formal Specification and Runtime Enforcement](https://arxiv.org/html/2602.22302) — arXiv 2602.22302. Formalizes contracts as (Preconditions, Invariants, Governance, Recovery) tuples with Lyapunov stability guarantees.

- [Pro2Guard: Proactive Runtime Enforcement for LLM Agent Safety via Probabilistic Prediction](https://arxiv.org/abs/2508.00500) — arXiv 2508.00500. Extends reactive enforcement with predictive model checking over the agent's action trajectory.

- [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073) — Bai et al., Anthropic 2022. The foundational paper on Constitutional AI — training models to align with explicit principles via self-critique and RLAIF.

- [Runtime Constitutional AI: Validating Every Agent Action Before Execution](https://dev.to/zer0h1ro/runtime-constitutional-ai-validating-every-agent-action-before-execution-546c) — DEV Community. Practical exploration of applying constitutional principles at inference time vs. training time.

- [Anthropic's Framework for Developing Safe and Trustworthy Agents](https://www.anthropic.com/news/our-framework-for-developing-safe-and-trustworthy-agents) — Anthropic 2024. Official framework articulating minimal footprint, human oversight, transparency, and reversibility principles for agentic Claude deployments.

- [Securely Deploying AI Agents — Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/secure-deployment) — Anthropic. Official documentation on isolation technologies, least privilege, credential management, and network controls for production agent deployments.

- [SagaLLM: Context Management, Validation, and Transaction Guarantees for Multi-Agent LLM Planning](https://arxiv.org/html/2503.11951v3) — arXiv 2503.11951. Applies the saga compensating transaction pattern to multi-agent LLM workflows, with rollback agents for each forward agent.

- [Saga Distributed Transactions Pattern — Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/saga/saga) — Microsoft. Reference implementation of the saga pattern in distributed systems, including compensating transaction design.

- [Prompt Chaining Saga Patterns — AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/prompt-chaining-saga-patterns.html) — Amazon Web Services. Patterns for applying saga-style recovery to LLM prompt chaining workflows.

- [Building a Least-Privilege AI Agent Gateway for Infrastructure Automation with MCP, OPA, and Ephemeral Runners](https://www.infoq.com/articles/building-ai-agent-gateway-mcp/) — InfoQ. Architecture for production gateway implementing least-privilege principles for AI agents using Open Policy Agent.

- [Agent Authority Least Privilege Framework — FINOS Air Governance](https://air-governance-framework.finos.org/mitigations/mi-18_agent-authority-least-privilege-framework.html) — FINOS. Industry governance framework for implementing graduated tool access control in AI agent deployments.

- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) — OWASP. Security patterns and anti-patterns for AI agent deployment from the Open Worldwide Application Security Project.

- [AgentGuard: Runtime Verification of AI Agents](https://www.researchgate.net/publication/395968094_AgentGuard_Runtime_Verification_of_AI_Agents) — ResearchGate. Dynamic Probabilistic Assurance framework that uses online Markov Decision Process learning for continuous agent safety monitoring.

- [Bridging LLM Planning Agents and Formal Methods: A Case Study in Plan Verification](https://arxiv.org/html/2510.03469v1) — arXiv 2510.03469. Translates LLM-generated plans into Kripke structures and verifies them against LTL properties using model checking.

- [2025 AI Agent Index: Technical and Safety Features of Deployed Agentic AI Systems](https://arxiv.org/html/2602.17753) — arXiv 2602.17753. Empirical survey of governance and safety features in deployed AI agent systems as of early 2025.

- [80% of Fortune 500 use active AI Agents — Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/02/10/80-of-fortune-500-use-active-ai-agents-observability-governance-and-security-shape-the-new-frontier/) — Microsoft, 2026. Industry data on AI agent adoption rates and governance gaps.

- [An In-Depth Study of Runtime Verification Overheads During Software Testing — ISSTA 2024](https://2024.issta.org/details/issta-2024-papers/143/An-In-depth-Study-of-Runtime-Verification-Overheads-during-Software-Testing) — ISSTA 2024. Empirical study of RV instrumentation overhead in 1,544 open-source projects.

- [Uncertainty in Runtime Verification: A Survey](https://www.sciencedirect.com/science/article/pii/S1574013723000618) — ScienceDirect. Survey of RV approaches for systems with incomplete or uncertain trace information.

- [Building Enterprise AI Agents with Least Privilege: A LangGraph Security Framework](https://medium.com/@samuel.grummons/building-enterprise-ai-agents-with-least-privilege-a-langgraph-security-framework-ea1cbfebcc1d) — Medium. Practical implementation of least-privilege tool access in LangGraph multi-agent workflows.

- [CrewAI vs LangGraph vs AutoGen: Choosing the Right Multi-Agent AI Framework](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen) — DataCamp. Comparative analysis of human-in-the-loop and safety guardrail implementations across major agentic frameworks.

- [The Lethal Trifecta for AI Agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) — Simon Willison, 2025. Influential analysis of the three conditions that make AI agents dangerous: autonomy + capability + data access without appropriate controls.
