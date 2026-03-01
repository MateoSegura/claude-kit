# claude-kit as a Deterministic Context Cache

> A theoretical framework for understanding how hierarchical skill injection
> narrows LLM output distributions toward domain-specific, reliable responses.

**Date:** 2026-02-28

---

## Table of Contents

1. [The Core Claim](#1-the-core-claim)
2. [The Cache Analogy — Made Rigorous](#2-the-cache-analogy--made-rigorous)
3. [Theoretical Foundation: Why This Works](#3-theoretical-foundation-why-this-works)
4. [Multi-Agent Architecture as Cache Coherence](#4-multi-agent-architecture-as-cache-coherence)
5. [Levels of LLM-Assisted Engineering](#5-levels-of-llm-assisted-engineering)
6. [Experimental Validation](#6-experimental-validation)
7. [Synthesis](#7-synthesis)
8. [Sources](#sources)

---

## 1. The Core Claim

claude-kit is a **hierarchical context cache** that narrows the LLM's output
probability distribution toward domain-specific, deterministic responses —
analogous to how CPU caches reduce memory access latency by keeping
frequently-needed data close to the processor.

Instead of caching *data for computation*, we cache *context for inference*.
Instead of reducing *latency*, we reduce *output entropy* (uncertainty).

---

## 2. The Cache Analogy — Made Rigorous

### 2.1 CPU Cache to LLM Context Mapping

| CPU Concept | claude-kit Equivalent | What It Holds | Access Pattern |
|---|---|---|---|
| **L1 Cache** (~4 KB, fastest) | System prompt + identity skill | Role definition, non-negotiables, methodology | Always loaded; every token attends to it |
| **L2 Cache** (~256 KB, fast) | Preloaded skills via agent `skills:` frontmatter | Domain APIs, patterns, hardware targets, coding standards | Injected at agent launch; full SKILL.md body in context |
| **L3 Cache** (~8 MB, slower) | Reference files linked from SKILL.md | Exhaustive API signatures, worked examples, edge cases | Loaded on-demand when the agent follows markdown links via Read |
| **RAM** | Full context window (~200K tokens) | System prompt + skills + conversation + tool results | Active working memory; finite; degrades with length |
| **Disk** | External docs, web search, MCP servers | Unbounded knowledge (Zephyr docs, Nordic DevZone, datasheets) | High-latency retrieval via WebSearch / WebFetch / MCP tools |

### 2.2 Why "Cache" and Not Just "Prompt Engineering"

A cache is not just "storing things nearby." A cache has three defining
properties:

1. **Locality exploitation** — stores what is *likely to be needed*, not
   everything.
2. **Hierarchical eviction** — less-needed content lives further from the
   processor.
3. **Hit rate determines performance** — the ratio of cache hits to misses
   determines throughput.

claude-kit exhibits all three.

**Locality.** Skills are curated domain knowledge — not random docs dumped into
context. Each skill targets a specific subsystem (zephyr-kernel,
devicetree-kconfig, hardware-nordic). An agent declares exactly which skills it
needs via `skills:` frontmatter. Irrelevant knowledge is never loaded.

**Hierarchy.** Identity (L1) is always present. Domain skills (L2) are
preloaded per agent. Reference files (L3) are loaded on demand. External
knowledge (Disk) requires tool use. Each layer trades access speed for
capacity.

**Hit rate.** When a Zephyr engineer agent needs to write a devicetree overlay,
the `devicetree-kconfig` skill is already in L2 — a cache hit. Without
claude-kit, Claude relies on parametric memory (compressed, potentially wrong)
— a cache miss that falls through to "disk" (hallucination or web search).

---

## 3. Theoretical Foundation: Why This Works

### 3.1 Distribution Narrowing

At each generation step, an LLM produces a probability distribution over its
vocabulary. The entropy of this distribution measures how "uncertain" the model
is:

```
H(output | context) = -Σ P(token_i | context) × log P(token_i | context)
```

Each layer of injected context reduces this entropy:

| Context State | Entropy Level | Example Failure Mode |
|---|---|---|
| No context (raw Claude) | Maximum | Wrong APIs, deprecated patterns, non-existent functions |
| + Identity skill | Moderate reduction | Correct methodology, but may misremember API details |
| + Domain skills | Significant reduction | Correct API signatures, board-specific pinouts, validated patterns |
| + Hooks (enforcement) | Hard floor | Even if the model generates dangerous code, PreToolUse hooks block execution |

Arora et al. (2025) proved that posterior variance from task uncertainty
**"vanishes exponentially fast with only a few in-context examples."** Each
well-chosen skill acts like an in-context example that exponentially reduces
the model's uncertainty about what constitutes correct domain code.

### 3.2 Soft Fine-Tuning via Attention

The transformer attention mechanism computes, for each token:

```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
```

Every token in the context window — system prompt, skill content, user query,
tool result — participates in this computation. The model has no hardcoded
architectural distinction between "system prompt" and "user input" at the
attention level. The distinction is created through training (RLHF) and special
delimiter tokens, not through architectural separation.

A 2025 theoretical framework (arXiv 2503.20561) formally proved that
**"transformer models, when provided with carefully designed prompts, can act
as a configurable computational system"** by emulating a virtual neural network
during inference. Input prompts function as network configuration parameters,
allowing dynamic adjustment of the model's internal computations.

This means skill injection is not just "giving the model information." It is
**reprogramming its computation** for the specific domain. When an identity
skill says "Never use deprecated `device_get_binding()` — always use
`DEVICE_DT_GET()`", the attention mechanism routes computation through patterns
that suppress the deprecated API and elevate the correct one.

This is functionally equivalent to fine-tuning, but:

- **Cheaper** — no training run, no GPU hours
- **More flexible** — change a skill file, next session uses it
- **More transparent** — you can read exactly what the model "knows"
- **Composable** — mix and match skills per agent role

### 3.3 Parametric vs Contextual Knowledge

Research shows LLMs have a strong bias: **they preferentially attend to
contextual knowledge over parametric knowledge** (arXiv 2410.08414). When a
skill states "nRF52840 has 48 GPIO pins across P0 and P1", the model will use
that fact even if its parametric memory (training data) contains a different
number.

This is exactly what makes the cache analogy work:

| Knowledge Type | Cache Equivalent | Properties |
|---|---|---|
| Parametric memory (weights) | Main memory | Compressed, static, probabilistic, interference-prone |
| Contextual knowledge (prompt) | Cache | Explicit, current, high-fidelity, attention-dependent |

The model's architecture naturally **prefers the cache** over main memory.

A 2024 EMNLP study comparing RAG and fine-tuning for knowledge injection found
that **"RAG consistently outperforms fine-tuning for both existing and new
knowledge"** — context-based knowledge injection is often more effective than
weight-based injection for domain-specific tasks.

However, this bias is a double-edged sword: injecting incorrect or irrelevant
context can actively override correct parametric knowledge. **Context quality
is paramount.** This is why claude-kit's skills are curated, reviewed, and
validated — not auto-generated from scraped docs.

### 3.4 The "Lost in the Middle" Problem and Skill Design

Liu et al. (2023) demonstrated that LLMs perform best when relevant
information appears at the **beginning** or **end** of the context window, with
significant degradation for information placed in the middle (U-shaped
performance curve).

claude-kit's architecture exploits this:

- **Identity skills** (most critical behavioral rules) are loaded first —
  primacy effect.
- **Agent `skills:` list** determines load order — the architect controls what
  gets primacy.
- **SKILL.md capped at 500 lines** — prevents any single skill from becoming a
  "middle blob" that dilutes attention.
- **Reference files loaded on demand** — keeps the main context lean and
  high-signal.

This is **cache-line optimization for LLMs**.

### 3.5 Compounding Determinism

In autoregressive generation, each token conditions the next. When the first
several tokens are highly determined by context, they anchor the rest of the
sequence:

```
Specific context → determined first token
  → more determined second token
    → more determined third token
      → highly consistent output sequence
```

Wang et al. (2023) showed that more specific prompts produce higher
**self-consistency** — multiple samples converge on the same answer more
frequently. This is direct empirical evidence that context specificity narrows
the output distribution across the entire generation sequence, not just at
individual token positions.

---

## 4. Multi-Agent Architecture as Cache Coherence

In CPU architecture, when multiple cores share a cache, a **cache coherence
protocol** ensures cores don't work with stale data. claude-kit's multi-agent
architecture solves the same problem.

| CPU Coherence Concept | claude-kit Equivalent |
|---|---|
| Cache coherence protocol (MESI) | Companion plugins — shared knowledge loaded once, referenced by all role agents |
| Core specialization (P-core vs E-core) | Role specialization — engineer (P-core: full compute), grader (E-core: read-only eval) |
| Write-back vs write-through | Hooks — PostToolUse validates immediately after writes (write-through) |
| Cache invalidation | `system-updater` — propagates knowledge changes across all team members |
| Shared L3 cache | Knowledge plugin — `embedded-zephyr-knowledge` shared by engineer, grader, tester, debugger |

The `cross-team-consistency.md` rule is literally a **cache coherence
protocol**: when you fix a bug in one plugin, you must propagate the fix to all
equivalent plugins across teams. Without this, knowledge diverges — the
equivalent of cache incoherence causing data corruption.

### 4.1 Agent Specialization as Core Topology

Each agent role has fundamentally different compute characteristics:

| Role | CPU Analogy | Tools | Permission | Purpose |
|---|---|---|---|---|
| Engineer | P-core (performance) | Full read/write/execute | acceptEdits | Writes code, builds features |
| Grader | E-core (efficiency) | Read-only | plan | Evaluates code against rubrics |
| Tester | Specialized core | Write (tests only) | default | Writes and runs test suites |
| Debugger | Analysis core | Read-only + inspect | plan | Diagnoses failures from logs/traces |

This prevents **context dilution** — each agent has exactly the instructions,
skills, and tools it needs. A grader that can also write code is like a CPU
core with unnecessary instruction sets consuming die area.

---

## 5. Levels of LLM-Assisted Engineering

### 5.1 Existing Taxonomies

Two published frameworks address levels of AI-assisted development:

**ASDLC Autonomy Levels** (adapted from SAE autonomous driving):

| Level | Name | Description |
|---|---|---|
| L1 | Assistive | Basic suggestions; human drives all decisions |
| L2 | Guarded Autonomy | Agent executes bounded tasks; human validates all outputs |
| L3 | Proposal-First | Agent proposes complete solutions; human approves or rejects |
| L4 | Supervised Autonomy | Agent operates independently; human intervenes on exceptions |
| L5 | Full Autonomy | Agent handles entire lifecycle with minimal oversight |

**Hyperact 7-Level Framework:**

| Level | Name | Key Characteristic |
|---|---|---|
| 1 | Manual Prompting | Copy-paste to/from ChatGPT |
| 2 | IDE-Level Assistance | Inline completions, editor-integrated |
| 3 | Autonomous Codebase Access | Model has repo + shell access |
| 4 | Autonomy + Deterministic Tooling | Connected to docs, build pipelines, MCP |
| 5 | Autonomy + Engineering Context | Anchored in team standards and architecture |
| 6 | Specialized, Parallelized Workflows | Sub-agents for security, QA; parallel execution |
| 7 | Spec-Driven Development | Code is transient; specifications are the durable artifact |

Neither taxonomy explicitly models **quality enforcement** as a capability
level.

### 5.2 The Context Cache Level Framework

The following framework maps claude-kit's architecture to measurable capability
levels, with each level reducing the output entropy of the system:

| Level | Name | What's Added | claude-kit Layer | Entropy Effect |
|---|---|---|---|---|
| **L0** | Raw LLM | Nothing — base model | None | Maximum entropy; model relies on parametric memory |
| **L1** | LLM + Tools | File access, code execution, web search | `claude` CLI with tool access | Moderate reduction; can read actual code, verify against reality |
| **L2** | LLM + Tools + Identity | Persistent role, methodology, coding standards | Identity skill + CLAUDE.md rules | Significant reduction; consistent behavioral constraints |
| **L3** | LLM + Tools + Identity + Domain Knowledge | Curated API references, patterns, hardware targets | Knowledge plugin skills (L2 cache) | Major reduction; authoritative domain facts replace parametric guesses |
| **L4** | L3 + Multi-Agent Specialization | Role-specific agents with tailored tools/skills/permissions | Engineer / Grader / Tester / Debugger split | Further reduction; each agent has a narrower output space |
| **L5** | L4 + Deterministic Enforcement | Hooks block bad outputs, graders score quality, CI validates | Hooks + grader agents + validators | Near-minimum entropy; incorrect outputs blocked before reaching the user |

### 5.3 What Each Level Buys You — Concretely

**L0 → L1 (Tools):** Claude can read your actual `prj.conf` instead of
guessing. Reduces factual errors about project state.

**L1 → L2 (Identity):** Claude knows it must use `DEVICE_DT_GET()` not
`device_get_binding()`. Reduces API misuse from stale parametric memory.

**L2 → L3 (Domain Knowledge):** Claude has the exact nRF52840 peripheral map,
knows that `NRF_TWIM0` and `NRF_SPIM0` share the same ID and can't be used
simultaneously. Reduces hardware-specific errors.

**L3 → L4 (Multi-Agent):** The grader reviews code blind against a 25+ check
rubric. The debugger reads crash logs with full knowledge of Zephyr's fault
handler format. Each agent does one thing well instead of one agent doing
everything mediocrely.

**L4 → L5 (Enforcement):** Even if the engineer writes `west build` without
`--sysbuild`, the PreToolUse hook blocks it. Even if code compiles, the
PostToolUse hook validates devicetree overlay syntax. Even if the agent tries
to stop, the Stop hook spawns a verification subagent. Bad outputs are
physically prevented, not just discouraged.

### 5.4 The Purpose at Each Level

| Level | Engineering Purpose | Hardware Analogy |
|---|---|---|
| L0 | Baseline — measure raw model capability | Bare-metal CPU, no cache |
| L1 | Grounded — model can verify against reality | CPU with RAM access, no cache |
| L2 | Consistent — model follows a coherent methodology | CPU with L1 cache (instruction fetch) |
| L3 | Accurate — model has authoritative domain knowledge | CPU with L1 + L2 + L3 cache (data locality) |
| L4 | Specialized — each task handled by the right expert | Multi-core with heterogeneous cores |
| L5 | Reliable — incorrect outputs physically blocked | Multi-core with ECC memory and checksums |

---

## 6. Experimental Validation

### 6.1 What to Measure

| Metric | What It Tests | Measurement Method |
|---|---|---|
| **Output Consistency** (self-agreement) | Does the same prompt produce the same code structure across N runs? | Run identical prompts N times at each level; compute pairwise AST similarity via Jensen-Shannon Divergence |
| **Factual Accuracy** (cache hit rate) | Does the model use correct APIs, pin assignments, peripheral addresses? | Create a test set of domain-specific questions with known correct answers; score at each level |
| **Idiomaticity** (domain conformance) | Does the code follow Zephyr conventions vs generic C? | Human-scored rubric OR automated grader agent scoring at each level |
| **Error Prevention Rate** (hook effectiveness) | How many dangerous operations are caught before execution? | Log all hook invocations; count blocks (exit 2) vs allows (exit 0) |
| **Task Completion Rate** (pass@1) | Does the code compile, flash, and pass tests? | SWE-bench-style: issue → patch → test suite |
| **Variance Reduction** (entropy proxy) | How much does output variance decrease at each level? | Structural Cross-Entropy (SCE) on ASTs across repeated runs |

### 6.2 Experimental Design: The Level Ablation Study

For a fixed set of 20 Zephyr firmware tasks of varying complexity:

1. **L0 baseline** — Raw `claude` with no plugins, no CLAUDE.md, no tools
   beyond basic chat
2. **L1** — `claude` with full tool access (Read, Write, Bash, etc.) but no
   plugins
3. **L2** — `claude` with identity skill only
4. **L3** — `claude` with full knowledge plugin loaded
5. **L4** — `claude` with full team (engineer + grader + knowledge)
6. **L5** — Full `claude-kit` invocation with hooks enabled

At each level, run each task 5 times. Measure:

- **Pass@1** — does it compile and pass tests on the first run?
- **Pass@5** — does at least one of 5 runs pass?
- **Self-consistency** — do all 5 runs produce structurally similar code?
- **Factual accuracy** — correct APIs, correct hardware constants?
- **Time to completion** — wall-clock time per task
- **Token usage** — total tokens consumed per task

### 6.3 Expected Results (Theoretical Prediction)

Based on the research:

- Domain-specific code generation without domain knowledge shows a **51%
  CodeBLEU degradation** (ACM TOSEM, 2024)
- Posterior variance from task uncertainty **vanishes exponentially** with
  in-context examples (Arora et al., 2025)
- Even at temperature zero, LLM code review responses **vary across runs**
  (arXiv 2502.20747)
- Specialized multi-agent systems achieve **91.5% pass@1** vs **86.8%** for
  generalist approaches (AgentCoder, 2024)

Predicted outcomes:

```
Level  | Pass@1   | Self-Consistency | Factual Accuracy
-------|----------|------------------|------------------
L0     |  15-25%  |      20-30%      |      40-50%
L1     |  30-40%  |      30-40%      |      55-65%
L2     |  40-50%  |      50-60%      |      65-75%
L3     |  60-75%  |      70-80%      |      85-95%
L4     |  70-85%  |      80-90%      |      90-95%
L5     |  80-90%  |      85-95%      |      92-98%
```

The largest jump should be **L2 → L3** (adding domain knowledge), consistent
with the exponential posterior variance reduction and the 51% degradation
without domain context.

### 6.4 Control Variables

To isolate the effect of each level:

- **Model**: Hold constant (e.g., Claude Sonnet 4.6 for all levels)
- **Temperature**: 0 for determinism measurement; 1.0 for variance measurement
- **Tasks**: Same 20 tasks across all levels; tasks should span:
  - Simple (GPIO toggle, UART echo)
  - Medium (BLE peripheral with custom GATT service)
  - Complex (multi-threaded sensor fusion with power management)
- **Evaluation**: Automated where possible (compilation, test pass); human
  review for idiomaticity
- **Repetitions**: 5 runs per task per level (600 total runs for statistical
  significance)

---

## 7. Synthesis

claude-kit is a **context engineering framework** that implements a
hierarchical domain knowledge cache for LLMs. It exploits three fundamental
properties of transformer attention:

1. **Context injection reconfigures the model's computation** — prompts
   function as configuration parameters for a virtual neural network emulated
   during inference (soft fine-tuning).

2. **Models prefer contextual over parametric knowledge** — the attention
   mechanism naturally prioritizes explicitly provided facts over compressed
   training-time memories (cache hit preference).

3. **Structured context exponentially reduces output uncertainty** — each
   well-chosen skill acts as an in-context example whose contribution to
   variance reduction follows an exponential decay curve (entropy narrowing).

Combined with multi-agent specialization (each agent is a specialized processor
with its own L1/L2 cache) and deterministic enforcement (hooks act as hardware
error correction), the system creates a **domain-specialized virtual machine**
on top of a general-purpose LLM.

The result is measurably more deterministic, more accurate, and more reliable
outputs for domain-specific tasks — not through fine-tuning (permanent,
expensive, inflexible) but through **structured context architecture**
(composable, transparent, instantly updatable).

**In one sentence:** claude-kit turns Claude from a generalist who might know
your domain into a domain specialist who definitely does — and proves it at
every step.

---

---

## Sources

### Foundational Transformer Research

- Vaswani et al. (2017). "Attention Is All You Need." arXiv:1706.03762
- Brown et al. (2020). "Language Models are Few-Shot Learners" (GPT-3).
  arXiv:2005.14165

### In-Context Learning Theory

- Xie et al. (2022). "An Explanation of In-Context Learning as Implicit
  Bayesian Inference." arXiv:2111.02080
- Akyurek et al. (2023). "What Learning Algorithm is In-Context Learning?
  Investigations with Linear Models." ICLR 2023
- Arora et al. (2025). "In-Context Learning Is Provably Bayesian Inference."
  arXiv:2510.10981
- arXiv 2503.20561 (2025). "Theoretical Framework for Prompt Engineering:
  Transformers as Configurable Computational Systems."

### Attention and Positional Effects

- Liu et al. (2023). "Lost in the Middle: How Language Models Use Long
  Contexts." arXiv:2307.03172
- Olsson et al. (2022). "In-Context Learning and Induction Heads." Anthropic
  research

### Knowledge and Context Injection

- Lewis et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive
  NLP Tasks." arXiv:2005.11401
- arXiv 2410.08414 (2024). "Understanding Parametric vs. Contextual Knowledge
  in LLMs."
- EMNLP 2024. "Fine-Tuning or Retrieval? Comparing Knowledge Injection in
  LLMs." aclanthology.org/2024.emnlp-main.15

### Output Determinism and Consistency

- arXiv 2502.20747 (2025). "Measuring Determinism in Large Language Models for
  Software Code Review."
- arXiv 2508.14288 (2025). "Measuring LLM Code Generation Stability via
  Structural Entropy."
- Wang et al. (2023). "Self-Consistency Improves Chain of Thought Reasoning in
  Language Models."
- Holtzman et al. (2020). "The Curious Case of Neural Text Degeneration."

### Multi-Agent Code Generation

- Huang et al. (2024). "AgentCoder: Multi-Agent-Based Code Generation with
  Iterative Testing and Optimisation." arXiv:2312.13010
- Pramanik et al. (2024). "MapCoder: Multi-Agent Code Generation for
  Competitive Problem Solving." ACL 2024
- ACM TOSEM (2025). "LLM-Based Multi-Agent Systems for Software Engineering:
  Literature Review." doi:10.1145/3712003

### Benchmarks and Metrics

- SWE-bench. swebench.com — Real-world software engineering benchmark
- Chen et al. (2021). "Evaluating Large Language Models Trained on Code"
  (pass@k). arXiv:2107.03374
- ENAMEL benchmark (2025). "Enhancing LLM-Generated Code Beyond Correctness."
  arXiv:2508.14419
- arXiv 2502.01853 (2025). "Security and Quality in LLM-Generated Code"
  (ISO/IEC 25010)

### Engineering Taxonomy and Industry Data

- ASDLC.io. "Levels of Autonomy in AI Software Development." asdlc.io
- Hyperact. "7 Levels of AI-Assisted Development." hyperact.co.uk
- DORA (2025). "State of AI-Assisted Software Development." dora.dev

### Context Engineering Practice

- Anthropic (2025). "Effective Context Engineering for AI Agents."
  anthropic.com/engineering
- Karpathy (2025). "Think of an LLM like a CPU, its context window as RAM."
  x.com/karpathy
- Anthropic (2025). "Effective Harnesses for Long-Running Agents."
  anthropic.com/engineering

### Constrained Decoding

- ACL 2025. "Grammar-Constrained Decoding for Structured NLP Tasks."
  aclanthology.org/2025.acl-industry.34
- ICML 2025. "Flexible and Efficient Grammar-Constrained Decoding."

### RAG and Hallucination

- Shuster et al. (2021). "Retrieval Augmentation Reduces Hallucination in
  Conversation."
- NAACL 2024. "Reducing Hallucination in Structured Outputs via RAG."
  aclanthology.org/2024.naacl-industry.19
- arXiv 2412.14964 (2024). "Knowledge Injection via Prompt Distillation."
