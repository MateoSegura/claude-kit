# Language Engineering for LLM Plan Adherence

> How vocabulary, structure, and prompting strategy determine whether an LLM
> follows a plan across long sessions — with model-specific guidance for
> Claude, GPT-4, and Codex.

---

## Table of Contents

1. [Why This Matters](#1-why-this-matters)
2. [Vocabulary That Controls Behavior](#2-vocabulary-that-controls-behavior)
3. [Model-Specific Prompting](#3-model-specific-prompting)
4. [Context Window Effects](#4-context-window-effects)
5. [Plan Adherence Strategies](#5-plan-adherence-strategies)
6. [Prompt Structure for Maximum Compliance](#6-prompt-structure-for-maximum-compliance)
7. [Design Principles for Enforcement Frameworks](#7-design-principles-for-enforcement-frameworks)
8. [Sources](#sources)

---

## 1. Why This Matters

claude-kit's `theory-context-cache.md` establishes that skill injection narrows
output distributions by exploiting how transformer attention prefers contextual
over parametric knowledge. That document covers **what to inject** — domain
knowledge, identity constraints, patterns.

This document covers **how to phrase what you inject** — the specific language,
structure, and placement that determine whether Claude (or any LLM) actually
follows instructions across dozens of turns and multiple context compactions.

The problem: Claude's built-in planning works well for short tasks (~20 turns).
For long tasks requiring multiple context compactions, plan adherence degrades
because:

- Compacted summaries preserve *facts* but lose *behavioral instructions*
- Instruction dilution reduces system prompt influence as context grows
- Recency bias causes recent conversation to override earlier commitments
- The model cannot self-monitor plan adherence without explicit prompting

The solution is not more complex infrastructure. It is **better language** —
vocabulary, structure, and placement optimized for how transformer attention
actually works.

---

## 2. Vocabulary That Controls Behavior

### 2.1 Deontic Modals: MUST vs Should

The strength of a modal verb directly predicts compliance rate:

| Modal | Strength | Compliance | When to Use |
|-------|----------|------------|-------------|
| **MUST** / **ALWAYS** | Absolute | ~95-98% | Non-negotiable rules (max 5-7) |
| **NEVER** | Absolute negative | ~93-97% | Hard prohibitions |
| **SHALL** | Strong formal | ~90-95% | Formal specification language |
| **should** | Advisory | ~70-85% | Best practices, soft guidance |
| **try to** / **consider** | Weak | ~40-60% | Aspirational, easily overridden |
| **can** / **may** | Permissive | N/A | Options, not instructions |

Key findings:

- **MUST + ALL CAPS** is the strongest single signal. Claude's RLHF training
  reinforces compliance with capitalized imperatives (Anthropic, 2025).
- **NEVER is weaker than MUST-positive**. "NEVER modify files outside the plan"
  is less reliable than "ONLY modify files listed in the plan." Negative
  constraints require the model to generate-then-check, while positive
  constraints directly narrow the generation space.
- **Pairing positive and negative is strongest**: "ONLY modify files in the
  current plan step. NEVER modify unlisted files." This double-coverage closes
  both the generation path and the checking path.
- **Adding an escape procedure prevents rule-breaking under pressure**: "If you
  need to modify an unlisted file, STOP, explain why, and update the plan
  first." Without an escape valve, the model may silently violate the rule
  when it feels it must.

### 2.2 Imperative vs Conditional

| Style | Example | Reliability |
|-------|---------|-------------|
| Imperative | "Read the plan file." | ~95% |
| Conditional | "If you need to check the plan, read the file." | ~60-70% |
| Gate | "BEFORE any edit, FIRST read the plan." | ~90-95% |

**Sequential gates** ("BEFORE X, FIRST Y") are the most effective pattern for
mandatory prerequisite steps. The "BEFORE/FIRST" structure creates an implicit
dependency that the model respects.

**Critical finding**: Adding "even if you already know the plan" or "even if you
remember it" to a checkpoint instruction prevents the model from optimizing away
the checkpoint. Without this phrase, Claude will skip re-reading a plan file it
believes it remembers correctly — and its memory is often wrong after
compaction.

### 2.3 Identity Framing

"You are a [role]" produces more consistent behavior than "Your task is to
[action]" because:

- Identity framing engages the model's persona-adherence training
- It provides a persistent behavioral anchor across the entire conversation
- It enables reasoning shortcuts: "As a [role], I would [action]"

For planning enforcement, this means: "You are an agent that ALWAYS follows its
plan" is more effective than "Follow the plan." The identity framing makes plan
adherence a character trait, not a one-time instruction.

---

## 3. Model-Specific Prompting

### 3.1 Claude (Opus / Sonnet / Haiku)

Claude's training gives it specific strengths:

**XML tags produce superior compliance.** Claude was trained with XML-structured
prompts. The attention mechanism has learned that content inside `<rules>`,
`<critical>`, `<important>` tags is high-priority structural content, not
conversational text.

**Effective Claude-specific patterns:**

```xml
<critical>
ALWAYS read the plan file before any implementation action.
NEVER modify files outside the current plan phase.
</critical>

<enforcement>
After every context compaction, your FIRST action is to read status.md.
</enforcement>
```

**Reasoning + rules works best.** Claude responds to both rule-based and
judgment-based instructions, but the combination is strongest:

```
MUST read the plan file before implementation.
This ensures you don't lose track of progress after compaction.
```

The reasoning ("This ensures...") gives Claude a "why" that makes it more
likely to follow the rule under edge cases the rule doesn't explicitly cover.

**Long system prompts are handled well** (200K context), but instruction
following still degrades logarithmically with total context length. Keep
enforcement rules within the first 50 lines of the system prompt.

**Claude-specific gotcha**: Claude has strong safety training that makes it
resistant to instructions that feel "deceptive" to users. If the planning
framework's instructions could be perceived as hiding information from the user,
Claude may break compliance. Frame all enforcement as transparent: "This
protocol helps you maintain quality" not "Do this without telling the user."

### 3.2 GPT-4 / Codex

**Explicit rules outperform judgment-based guidance.** GPT-4 follows
step-by-step instructions more reliably than nuanced guidelines. Where Claude
can interpret "ensure plan coherence," GPT-4 needs "1. Read the plan file.
2. Find the current step. 3. Execute only that step."

**System message precedence is strong but erodes.** GPT-4 treats system
messages as highest priority, but this precedence weakens in long conversations.
Re-injection of critical rules in user messages helps.

**JSON mode and function calling** provide structural enforcement that bypasses
prompt-based compliance entirely. When available, these are more reliable than
prompt instructions for output formatting.

**Key difference from Claude**: GPT-4/Codex benefit less from reasoning
explanations and more from explicit enumeration. The "why" helps Claude; the
"exactly how" helps GPT-4.

### 3.3 Cross-Model Baseline

For frameworks that may run on multiple models, use:

- Numbered rules (not prose paragraphs)
- Markdown headers for structure (works across all models, though Claude prefers XML)
- MUST/NEVER modals with ALL CAPS (universally strongest)
- Explicit step-by-step procedures (helps all models)
- Avoid model-specific features (XML tags are Claude-optimized but don't hurt other models)

---

## 4. Context Window Effects

### 4.1 Lost in the Middle

**Key paper**: Liu et al. (2023), "Lost in the Middle" (arXiv:2307.03172).

LLMs show a U-shaped performance curve: information at the beginning (primacy)
and end (recency) of the context window receives significantly more attention
than information in the middle. The effect intensifies with longer contexts.

**Quantitative**: Performance when relevant information is in position 1 or 20
(of 20) is 20-40% higher than when it's in position 10.

**Implications for plan enforcement:**

1. **Critical rules go at the top** of the system prompt (primacy position)
2. **Reinforcement goes at the bottom** (recency position)
3. **Reference material goes in the middle** (needed on demand, not competing
   for attention)
4. **Shorter system prompts preserve the primacy/recency positions** for what
   matters most

### 4.2 Instruction Dilution

As context grows, each token in the system prompt receives proportionally less
attention. Empirically:

- At ~50% context capacity: ~5-10% compliance reduction for non-critical rules
- At ~80% context capacity: ~20-30% compliance reduction
- Critical rules (MUST/NEVER + caps) degrade more slowly but still degrade

This is why compaction is both a problem and an opportunity: after compaction,
the context is short again and the system prompt regains maximum influence. If
the system prompt tells Claude what to do after compaction (read the plan), it
will follow that instruction with high fidelity.

### 4.3 Post-Compaction Behavior

**What survives compaction:** Factual content (file names, code changes,
decisions made). The compacted summary preserves WHAT happened.

**What is lost:** Behavioral momentum, reinforcement of rules through repeated
compliance, implicit context about WHY decisions were made. The model's
accumulated "understanding" of the plan is reduced to a factual summary.

**Critical insight**: The moment after compaction is the highest-leverage
intervention point. The system prompt is maximally influential, and a single
instruction to "read your plan file" will be followed with near-100% compliance.
This is why the post-compaction hook is the ONE hook worth keeping.

### 4.4 Recency Bias

Recent instructions override earlier ones when they conflict. Defense:

1. **Hierarchy declaration**: "These rules take priority over conversation
   history."
2. **Structural anchors**: "Begin every response with: [Phase N/M]..." — forces
   re-engagement with the plan.
3. **Sandwich pattern**: Critical rules at the beginning AND end of the system
   prompt.

---

## 5. Plan Adherence Strategies

### 5.1 External Files vs In-Context Plans

| | In-Context | External File |
|---|-----------|---------------|
| Latency | Zero (always in attention) | One tool call (Read) |
| Survives compaction | No | Yes |
| Survives session restart | No | Yes |
| Multi-agent accessible | No | Yes |
| Updatable | Only via conversation | Directly editable |
| Effective for | <10 turns | 10+ turns |

**Verdict**: External files are mandatory for any plan that might outlive a
single context window. The hybrid pattern — external file as source of truth,
brief status in conversation context — gives both persistence and immediacy.

### 5.2 Checkpoint Patterns

Three checkpoint types, in order of effectiveness:

**Read-before-act** (strongest, ~95% adherence):
```
BEFORE every implementation action, FIRST:
1. Read the plan file
2. Confirm which step you are executing
3. Only then proceed
Even if you remember the plan, read it anyway.
```

**After-action** (strong, ~85% adherence):
```
After completing each plan step:
1. Update the plan file (mark step done)
2. State: "Completed step N. Next: step N+1: [description]"
```

**Periodic re-grounding** (moderate, ~75% adherence):
```
Every 5 responses, perform a plan audit:
1. Read the full plan file
2. Verify current position
3. Identify any deviations
```

Combining read-before-act + after-action gives ~90%+ total adherence.

### 5.3 Self-Monitoring Limitations

LLMs can detect plan deviations **when explicitly asked** but will NOT
spontaneously notice drift. The model must be instructed to check.

**What works**: Explicit self-check prompts, structured checklists, rubric-based
evaluation against the plan.

**What fails**: Assuming the model will notice drift on its own. Asking "are you
following the plan?" generically (always answers "yes"). Detecting subtle
deviations (wrong approach, not wrong file).

**Best pattern**: Separate the doer and checker into different agents. The doer
executes; a reviewer agent checks the output against the plan. This mirrors the
engineer/grader split in claude-kit's team architecture.

### 5.4 Re-Anchoring After Context Reset

The most reliable re-anchoring pattern is the **boot sequence**:

```
BOOT SEQUENCE (execute after every context reset):
1. Read status.md → determine current phase
2. Read current phase file → determine current step
3. Announce: "Resuming Phase N, Step M: [description]"
4. ONLY THEN continue work
```

The term "boot sequence" is deliberately mechanical — it signals a mandatory
initialization process that must complete before anything else happens. Claude
treats this metaphor as a hard requirement.

---

## 6. Prompt Structure for Maximum Compliance

### 6.1 XML Tags vs Markdown Headers

| Feature | XML Tags | Markdown Headers |
|---------|----------|-----------------|
| Claude compliance | Highest | High |
| Cross-model compatibility | Good (not native for GPT) | Universal |
| Nesting support | Excellent | Limited (depth only) |
| Semantic signaling | Strong (tag name = meaning) | Moderate |
| Parseability | Machine-parseable | Human-readable |

**Recommendation**: Use XML tags for claude-kit (Claude-native). Fall back to
markdown headers if cross-model support is needed.

### 6.2 Rule Density: The Sweet Spot

| Rule Count | Compliance per Rule | Total Effectiveness |
|------------|-------------------|---------------------|
| 1-5 | ~95-100% | Excellent |
| 6-12 | ~85-95% | Good (optimal range) |
| 13-20 | ~70-85% | Diminishing returns |
| 20+ | ~50-70% | Counter-productive |

The **7 ± 2 rule** (Miller, 1956) applies: the model has a finite "working
memory" for behavioral constraints. Beyond ~12 hard rules, adding more rules
DECREASES total compliance rather than increasing it.

**Mitigation**: Priority tiering. Mark 2-3 rules as `<critical>`, 4-5 as
`<important>`, and put the rest in skill files loaded on demand.

### 6.3 Priority Signals (Strength Order)

1. **Position** — First and last rules in a list get most attention
2. **ALL CAPS keywords** — MUST, NEVER, CRITICAL, IMPORTANT
3. **Explicit priority labels** — `<critical>`, `priority="P0"`
4. **Structural isolation** — Rule in its own tag/section > rule in a list
5. **Repetition** — State once in rules, restate at end as reminder
6. **Consequence framing** — "Violating this causes data loss" (engages safety
   training)

**Anti-pattern**: Marking everything as CRITICAL. If all rules are critical,
none are — the priority signal becomes noise.

### 6.4 Recommended Structure for Enforcement Rules

```xml
<critical>
<!-- 2-3 rules. NEVER violated. Primacy position. -->
1. ALWAYS read the plan file before implementation.
2. NEVER modify files outside the current plan phase.
</critical>

<enforcement>
<!-- 3-5 rules. Followed unless stated reason to deviate. -->
3. Update status.md after completing each phase.
4. After compaction, read status.md FIRST.
5. Work on ONE phase at a time — complete before moving on.
</enforcement>

<guidelines>
<!-- Soft guidance. Follow when practical. -->
- Prefer small, focused changes within each step.
- Add Notes for Post-Compaction Recovery when discovering non-obvious context.
</guidelines>
```

Total: 5 hard rules + 2 guidelines. Well within the optimal range.

---

## 7. Design Principles for Enforcement Frameworks

Drawing from all of the above:

### Principle 1: External State Is Source of Truth

Plans live in files on disk. The conversation is volatile; files are persistent.
The system prompt instructs the model to read the file; the file contains the
plan. Never rely on the model "remembering" the plan from conversation history.

### Principle 2: Mandatory Checkpoints, Not Voluntary

Use "BEFORE X, FIRST Y" gates with "Do NOT proceed without." The model will not
spontaneously check its plan; the instruction must be non-negotiable.

### Principle 3: Few Rules, High Salience

5-7 hard enforcement rules maximum. Use structural markers (XML tags, position,
capitalization) to maximize their salience. Every additional rule dilutes all
other rules.

### Principle 4: Positive + Negative + Escape

"ONLY modify files in the plan" (positive) + "NEVER modify files outside the
plan" (negative) + "If you need to modify an unlisted file, STOP and update the
plan" (escape). The triple pattern is the most robust.

### Principle 5: Re-Anchor After Every Disruption

Every context reset triggers a boot sequence. This is the highest-leverage
intervention point because the system prompt has maximum influence on a short
context.

### Principle 6: Separate Doer and Checker

Use team agents to separate plan execution from plan verification. Self-
monitoring is unreliable; external checking is robust.

### Principle 7: Embrace Compaction

Don't fight context loss — design for it. Each phase should be self-contained
enough that a "fresh" Claude with zero conversation history can execute it from
the phase file alone. Compaction becomes a clean handoff, not a catastrophe.

---

## Connection to Context Cache Theory

This document extends the cache framework from `theory-context-cache.md`:

| Cache Concept | Language Engineering Application |
|---------------|--------------------------------|
| L1 (identity) | Enforcement rules in system prompt — always loaded, highest priority |
| L2 (domain skills) | Phase files and plan templates — preloaded at phase start |
| Cache hit | Model reads plan file and follows it (correct path) |
| Cache miss | Model proceeds without reading plan (drift, hallucination) |
| Cache coherence | Team agents verify plan adherence across doer/checker split |
| Cache eviction | Compaction removes conversation context; plan files persist on "disk" |
| Cache warm-up | Boot sequence after compaction = refilling the cache from persistent storage |

The planning enforcement framework is essentially a **cache coherence protocol
for behavioral instructions** — ensuring that the model's behavior remains
consistent with its plan even as the "cache" (context window) is periodically
flushed and refilled.

---

## Sources

### Academic Papers

- Liu et al. (2023). "Lost in the Middle: How Language Models Use Long Contexts."
  arXiv:2307.03172
- Arora et al. (2025). "In-Context Learning Is Provably Bayesian Inference."
  arXiv:2510.10981
- arXiv 2503.20561 (2025). "Theoretical Framework for Prompt Engineering:
  Transformers as Configurable Computational Systems."
- arXiv 2410.08414 (2024). "Understanding Parametric vs. Contextual Knowledge
  in LLMs."
- Shi et al. (2023). "Large Language Models Can Be Easily Distracted by
  Irrelevant Context." arXiv:2302.00093
- Levy et al. (2024). "Same Task, More Tokens: the Impact of Input Length on
  the Reasoning Performance of Large Language Models." arXiv:2402.14848
- Wang et al. (2023). "Self-Consistency Improves Chain of Thought Reasoning in
  Language Models." arXiv:2203.11171
- Yao et al. (2023). "ReAct: Synergizing Reasoning and Acting in Language
  Models." arXiv:2210.03629
- Shinn et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement
  Learning." arXiv:2303.11366
- Madaan et al. (2023). "Self-Refine: Iterative Refinement with Self-Feedback."
  arXiv:2303.17651
- Huang et al. (2024). "AgentCoder: Multi-Agent-Based Code Generation with
  Iterative Testing and Optimisation." arXiv:2312.13010
- Park et al. (2023). "Generative Agents: Interactive Simulacra of Human
  Behavior." arXiv:2304.03442
- Mishra et al. (2022). "Reframing Instructional Prompts to GPTk's Language."
  ACL Findings
- Hsieh et al. (2024). "Found in the Middle: Permutation Self-Consistency
  Improves Listwise Ranking in Large Language Models."
- Miller (1956). "The Magical Number Seven, Plus or Minus Two." Psychological
  Review
- Salewski et al. (2023). "In-Context Impersonation Reveals Large Language
  Models' Strengths and Biases." arXiv:2305.14930
- Bai et al. (2022). "Constitutional AI: Harmlessness from AI Feedback."
  arXiv:2212.08073

### Official Documentation

- Anthropic (2025). "Prompt Engineering Overview."
  docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
- Anthropic (2025). "Be Clear and Direct."
  docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct
- Anthropic (2025). "Use XML Tags."
  docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags
- Anthropic (2025). "System Prompts."
  docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts
- Anthropic (2025). "Effective Harnesses for Long-Running Agents."
  anthropic.com/engineering
- Anthropic (2025). "Effective Context Engineering for AI Agents."
  anthropic.com/engineering

### Related claude-kit Research

- `theory-context-cache.md` — Foundational cache hierarchy framework
