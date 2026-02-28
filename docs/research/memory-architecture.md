# Memory Architecture for LLM Agents
## Governance, Provenance, and Forgetting

> A design research document for claude-kit. Explores the full memory stack for
> LLM-based agent systems — from the transient context window through persistent
> external stores — and derives concrete architectural implications for how
> claude-kit manages skill injection, knowledge drift, and policy-driven
> forgetting.

---

## Table of Contents

1. [The Core Tension](#1-the-core-tension)
2. [A Taxonomy of Agent Memory](#2-a-taxonomy-of-agent-memory)
   - 2.1 In-Context Memory
   - 2.2 Episodic Memory
   - 2.3 Semantic Memory
   - 2.4 Procedural Memory
   - 2.5 External / Archival Memory
   - 2.6 Failure Mode Summary
3. [Context Window Management](#3-context-window-management)
   - 3.1 The Lost-in-the-Middle Problem
   - 3.2 Token Budget Management
   - 3.3 Compression Techniques
   - 3.4 The MemGPT / Virtual Paging Model
4. [Policy-Driven Forgetting](#4-policy-driven-forgetting)
   - 4.1 Why Forgetting Is a Feature
   - 4.2 Machine Unlearning in LLMs
   - 4.3 Selective Context Pruning
   - 4.4 Contamination Detection
   - 4.5 Privacy-Preserving Memory Management
5. [Versioned Semantic Memory](#5-versioned-semantic-memory)
   - 5.1 Knowledge Graph Versioning
   - 5.2 Provenance Tracking
   - 5.3 Causal Linkage
   - 5.4 Temporal Validity
   - 5.5 The Zep / Graphiti Architecture
6. [RAG vs. In-Context Injection](#6-rag-vs-in-context-injection)
   - 6.1 The Fundamental Tradeoff
   - 6.2 When Long Context Wins
   - 6.3 When RAG Wins
   - 6.4 Hybrid Approaches
   - 6.5 The RAPTOR Middle Ground
7. [Practical Memory Systems Survey](#7-practical-memory-systems-survey)
   - 7.1 LangChain Memory Types
   - 7.2 LlamaIndex Memory Modules
   - 7.3 MemGPT / Letta Architecture
   - 7.4 MIRIX: Six-Component Memory
   - 7.5 A-MEM: Agentic Zettelkasten Memory
8. [Implications for claude-kit](#8-implications-for-claude-kit)
   - 8.1 Skill Size and the 500-Line Cap
   - 8.2 Handling Knowledge That Becomes Outdated
   - 8.3 Versioned Skills with Changelogs
   - 8.4 RAG as a Complement to Skill Injection
   - 8.5 Knowledge Drift Detection in system-updater
   - 8.6 Policy-Driven Forgetting for Skill Content
   - 8.7 Concrete Recommendations
9. [Sources](#sources)

---

## 1. The Core Tension

A podcast summary captures the problem precisely: *"Memory has to move from being
passive storage — just simple data retrieval — to an active governed semantic
graph. LLMs today maintain context but they often lack governance to ensure
memories stay truthful, relevant, and aligned with human values. The challenge is
implementing versioned semantic graphs that support provenance, causal linkage,
and crucially policy-driven forgetting."*

This is not a niche concern. It sits at the center of every design decision in
agent memory architecture. The tension has three axes:

| Axis | Pressure A | Pressure B |
|------|-----------|-----------|
| **Fidelity vs. Capacity** | Exact recall requires keeping everything | Context windows are finite; external storage is noisy |
| **Freshness vs. Stability** | Knowledge must update as the world changes | Updating memory risks corrupting correct beliefs |
| **Accessibility vs. Governance** | Agents need fast, broad access to knowledge | Unbounded access enables misinformation, privacy leakage, staleness |

Claude-kit currently resolves this tension by injecting curated, human-authored
skill files directly into the context window. This is a deliberately simple
model — but one that carries specific failure modes as the knowledge base grows,
ages, and diverges from reality. Understanding the full research landscape
allows us to see exactly where that simplicity breaks down, and where it holds.

---

## 2. A Taxonomy of Agent Memory

Research has converged on a five-type taxonomy that maps closely to cognitive
neuroscience's distinction between declarative and non-declarative memory
systems. The analogy is not perfect — LLMs are statistical text predictors, not
brains — but it provides useful vocabulary for architectural decisions.

### 2.1 In-Context Memory

**Definition:** The active context window — everything currently visible to the
model during inference. This includes the system prompt, injected skill content,
conversation history, tool results, and the current user turn.

**Properties:**
- Finite: bounded by the model's context limit (typically 128K–200K tokens
  for frontier models as of early 2026)
- Transient: lost at session end unless explicitly persisted
- High-fidelity: everything in context is attended to directly, not
  compressed or retrieved through a retrieval step
- Ordered: position within the window affects how strongly content is attended
  to (see Section 3.1)

**Failure modes:**
- **Context overflow:** The window fills; something must be dropped. Without
  a principled eviction policy, useful content is lost arbitrarily.
- **Lost-in-the-middle degradation:** Content placed in the middle of a long
  context receives significantly less attention than content at the beginning
  or end (Liu et al., 2023/2024 — see Section 3.1).
- **Context poisoning:** Injecting incorrect, outdated, or adversarially
  crafted content into context can override correct parametric knowledge.
  The model preferentially attends to contextual over parametric knowledge
  (arXiv 2410.08414), making context quality paramount.
- **Attention dilution:** Extremely long contexts reduce the effective
  attention each piece of information receives. More tokens = less attention
  per token for any given fact.

**What claude-kit does here:** Skill injection is pure in-context memory.
Skills live in the context window for the duration of the session. This is the
system's primary knowledge delivery mechanism.

---

### 2.2 Episodic Memory

**Definition:** A record of specific past interactions, conversations, task
logs, and events — time-stamped, situational experiences. Named by analogy to
human episodic memory (Tulving, 1972): memory for "what happened, when, where."

**Properties:**
- Time-indexed: each episode has a timestamp and optionally a causal chain
- Instance-specific: stores particulars, not generalizations
- Can be consolidated: episodic memories can be promoted to semantic memory
  through summarization or abstraction
- Supports single-shot learning: a single episode can be retrieved and used
  to guide future behavior

**Failure modes:**
- **Episode overload:** Naive storage of every interaction creates unbounded
  logs. Retrieval degrades as the corpus grows unless indexed well.
- **Temporal drift:** Old episodes reference stale states of the world. An
  episode from six months ago may contain facts that have since been
  superseded.
- **Retrieval noise:** Retrieving the wrong episode (similar embedding but
  different context) can actively mislead the agent.
- **Missing consolidation:** Without periodic consolidation from episodic to
  semantic memory, useful patterns remain buried in raw event logs rather
  than extracted into usable knowledge.

A 2025 position paper argues that episodic memory is "the missing piece for
long-term LLM agents" — current architectures focus heavily on semantic and
procedural memory but largely ignore the single-shot, instance-specific recall
that episodic memory enables (arXiv 2502.06975).

---

### 2.3 Semantic Memory

**Definition:** General world knowledge, facts, concepts, rules, and
relationships — stored in a structured, queryable form. By analogy to human
semantic memory: context-free factual knowledge ("Paris is the capital of
France") as opposed to the memory of learning that fact.

**Properties:**
- Declarative: can be stated as explicit propositions
- Context-independent: valid across sessions, not tied to specific episodes
- Queryable: can be retrieved by concept, relationship, or keyword
- Updateable: facts can be revised when the world changes

**Failure modes:**
- **Knowledge drift:** Semantic stores become stale as the domain evolves.
  Code APIs change, library versions ship, hardware specifications update.
  Without active freshness tracking, agents cite outdated facts confidently.
- **Conflicting facts:** Two facts in the semantic store may contradict each
  other if they were ingested at different times or from different sources.
  Without conflict resolution, the agent retrieves whichever matches the
  query better — not necessarily the correct one.
- **Missing provenance:** If a fact is stored without a source and validity
  date, there is no basis for deciding whether to trust or update it.
- **Concept drift:** The meaning of terms changes over time (a "serverless
  function" in 2016 means something different in 2026). Semantic stores
  anchored to older terminology fail on modern queries.

**What claude-kit does here:** Skills are the semantic memory layer. The
`zephyr-kernel` skill stores facts about the Zephyr RTOS API, device model,
and configuration system. This is semantic memory delivered via in-context
injection.

---

### 2.4 Procedural Memory

**Definition:** Knowledge about *how* to perform tasks — encoded skills,
behavioral patterns, tool use sequences, and heuristics. By analogy to human
procedural memory: riding a bike (implicit skill) vs. recalling a bike's
mechanics (declarative knowledge).

**Properties:**
- Action-oriented: describes processes, not facts
- Often implicit in LLMs: encoded in model weights through training on
  examples (code generation, tool calling)
- Can be made explicit: skill files that describe *how to* do something are
  explicit procedural memory
- Compositional: complex procedures are built from simpler ones

**Failure modes:**
- **Outdated procedures:** A skill that describes the procedure for "deploying
  to Kubernetes" becomes wrong when the cluster migrates from GKE to EKS.
- **Conflicting procedures:** Two skills may encode contradictory approaches
  to the same task if they were authored at different times by different
  people.
- **Overfitting to past patterns:** Procedural memory can encode patterns
  that were correct in past contexts but are suboptimal or wrong in new
  contexts. The agent applies a learned procedure without recognizing that
  the situation has changed.
- **Missing preconditions:** A procedure stored without the conditions under
  which it applies will be applied in situations where it should not be.

**What claude-kit does here:** Role-specific agent files (the `engineer.md`,
`grader.md`, etc.) encode procedural memory — not just what to know, but how
to act. The grader's rubric is explicit procedural memory: "If you see X, do
Y." This is the most direct analogy to claude-kit's architecture.

---

### 2.5 External / Archival Memory

**Definition:** Knowledge stored outside the context window in persistent
external systems — vector databases, knowledge graphs, relational databases,
document stores. Retrieved on demand via search, embedding similarity, or
graph traversal.

**Properties:**
- Unbounded capacity: not constrained by context window size
- Persistent: survives across sessions
- Retrieved, not injected: content enters context via a retrieval step
  (RAG), introducing retrieval noise and latency
- Requires indexing infrastructure: must be indexed to be searchable

**Failure modes:**
- **Retrieval miss:** Relevant content is not retrieved because the query
  does not match the stored representation well (vocabulary mismatch,
  embedding drift).
- **Hard negatives:** Retrieved content looks semantically similar to the
  query but is actually irrelevant or misleading. Research shows irrelevant
  retrieved passages actively harm LLM performance (arXiv 2501.01880).
- **Stale index:** The external store is updated but the index lags, causing
  stale content to be retrieved for recent queries.
- **Memory poisoning:** Malicious content injected into the external store
  can corrupt future agent behavior at scale. MemoryGraft (arXiv 2512.16962)
  demonstrated that even a small number of poisoned records can dominate
  retrieval results for targeted queries.

---

### 2.6 Failure Mode Summary

| Memory Type | Primary Failure | Secondary Failure | Governance Need |
|-------------|----------------|-------------------|-----------------|
| In-context | Overflow, dilution | Poisoning, position effects | Eviction policy, load-order control |
| Episodic | Episode overload, temporal drift | Wrong retrieval | Consolidation, time-indexing |
| Semantic | Knowledge drift, conflicting facts | Missing provenance | Versioning, freshness tracking |
| Procedural | Outdated procedures, overfitting | Missing preconditions | Conditional scoping, deprecation |
| External / Archival | Retrieval miss, hard negatives | Memory poisoning, stale index | Validation, access control |

---

## 3. Context Window Management

### 3.1 The Lost-in-the-Middle Problem

The most operationally significant finding in context window research is the
**U-shaped performance curve** identified by Liu et al. (2023), published in
the Transactions of the Association for Computational Linguistics (2024).

The finding: LLM performance on tasks requiring retrieval of specific
information from context peaks when relevant information appears at the
**beginning** (primacy effect) or **end** (recency effect) of the context
window. Performance degrades significantly — sometimes catastrophically — when
relevant information is placed in the **middle** of a long context, even for
models explicitly trained for long-context operation.

```
Performance
    ▲
    │████                                    ████
    │████                                    ████
    │████          ░░░░░░░░░░░░              ████
    │████      ░░░░░░░░░░░░░░░░░░░░          ████
    │████  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    ████
    └────────────────────────────────────────────▶
    Start                                     End
                  Context Position
```

A subsequent OpenReview paper proposed that this is not a defect but an
emergent property from pre-training: some pre-training tasks reward uniform
recall across context (long-term memory demand) while others reward recency
(short-term memory demand). The U-shape reflects the superposition of both
patterns.

**Primacy effect magnitude:** Studies show a ~15-25% performance drop for
information placed in the middle versus the beginning of a 32K token context,
even for state-of-the-art models. The effect is observed consistently across
GPT-4, Claude, and open-source models.

**Practical consequence for skill-based systems:** Skill content injected
early (high in the system prompt) receives maximal attention. Content injected
late (just before the user turn) also receives elevated attention due to
recency. Content buried deep in a long system prompt — especially if many
skills are stacked — receives the weakest attention.

---

### 3.2 Token Budget Management

Context windows are a shared, finite resource. A session with:
- 2,000 tokens of identity/system prompt
- 5 skills × 3,000 tokens each = 15,000 tokens
- 10 turns of conversation × 2,000 tokens each = 20,000 tokens
- 10 tool results × 3,000 tokens each = 30,000 tokens

...already occupies 67,000 tokens before any new generation. For a 128K
context model, this leaves 61K for future turns; for a 200K model, 133K.

Research from Factory.ai's evaluation of context compression approaches
identifies three budget strategies:

1. **Fixed eviction window:** Keep the last N turns verbatim; discard older
   turns. Simple but loses important early context.
2. **Hybrid retention:** Keep verbatim turns above a threshold; summarize
   older turns. This is Claude Code's documented approach.
3. **Selective retention by relevance:** Score each piece of context against
   the current task; retain high-scoring items regardless of position.
   Requires a relevance scorer, which adds latency.

Anthropic's own documentation for Claude Code describes a hybrid approach:
when context approaches limits, the model is instructed to summarize
conversation history, preserving "architectural decisions, unresolved bugs,
and implementation details while discarding redundant tool outputs or
messages," then continues with the compressed context plus the five most
recently accessed files.

---

### 3.3 Compression Techniques

**LLM summarization:** A separate model (or the main model in a separate
call) compresses older interaction history into a condensed summary. The
summary replaces raw exchanges in the context. This allows theoretically
infinite conversation length at the cost of information loss and computational
overhead.

The ACON framework (arXiv 2510.00615, October 2025) is the most rigorous
recent work on compression for agentic contexts. Key results:
- **26–54% reduction in peak token usage** across AppWorld, OfficeBench, and
  multi-objective QA benchmarks
- **Task performance preservation:** Full accuracy maintained with large
  models; 95%+ accuracy retained when distilled to smaller compressor models
- **Key insight:** Naive compression loses critical details like "email
  identifier, file version, or API format." The ACON approach uses
  *failure-driven* compression guideline optimization — analyzing pairs of
  trajectories where full context succeeds but compressed context fails to
  identify what the compressor must preserve.

**Observation masking:** Compress only the environment observation component
(tool outputs, search results), not the action/reasoning history. Preserves
reasoning chains but not raw data. This is often the right tradeoff for
agentic tasks where the reasoning steps matter more than the raw tool output.

**Hierarchical summarization:** Multiple rounds of progressively coarser
summarization as content ages. Recent turns are verbatim; turns from 30
minutes ago are a paragraph summary; turns from two hours ago are a
sentence. JetBrains Research (2025) describes this as a "recency-weighted
fidelity gradient."

**Selective retention by content type:** Architectural decisions and unresolved
bugs are retained verbatim; boilerplate tool outputs (e.g., "file written
successfully") are dropped immediately. This requires classifying each piece
of context by type — not all systems do this.

---

### 3.4 The MemGPT / Virtual Paging Model

MemGPT (Packer et al., 2023, arXiv 2310.08560) introduced the most
architecturally complete solution to the context limit problem: treat the
context window as RAM and implement OS-style virtual memory paging.

The MemGPT architecture defines three tiers:

| Tier | Analogy | Contents | Accessibility |
|------|---------|----------|---------------|
| **Main context** | RAM | Active conversation, core memory blocks, current task | Always in context |
| **Recall memory** | Disk (fast) | Full conversation history, searchable by embedding | Retrieved on demand via search |
| **Archival memory** | Cold storage | Processed knowledge, documents, past tasks | Retrieved on demand via search |

The LLM is given tools to manage its own memory: it can read from and write to
recall and archival stores, choose what to promote into main context, and
decide what to evict. This gives the *model* control over memory management
rather than hard-coding a policy.

MemGPT evolved into Letta (announced September 2024), which retains the
three-tier model but modernizes the agent loop: "In-context memory blocks that
can be managed by the agent itself or by other agents" (Letta documentation).
Letta's Graphiti integration (see Section 5.5) adds a temporal knowledge graph
as a fourth tier.

**Key lesson for claude-kit:** MemGPT demonstrates that memory management
can itself be a learned, agentic behavior rather than a hardcoded system
policy. An agent with well-designed memory management tools will develop
implicit heuristics about what to keep, compress, and evict.

---

## 4. Policy-Driven Forgetting

### 4.1 Why Forgetting Is a Feature

In traditional database systems, forgetting is failure. In cognitive systems —
biological or artificial — selective forgetting is essential to healthy
function. The reasons are fundamental:

1. **Truth maintenance:** A fact that was true becomes false. An agent that
   never forgets will confidently cite a deprecated API, a dissolved
   organization, or a retracted scientific finding.

2. **Privacy and compliance:** GDPR's "right to be forgotten," CCPA deletion
   requirements, and similar regulations create legal obligations to remove
   specific information from AI systems.

3. **Cognitive load reduction:** Retaining everything increases retrieval
   noise. A memory store containing both current and outdated versions of the
   same fact will retrieve both — and the agent must then determine which is
   correct, or worse, conflate them.

4. **Security:** Knowledge of exploits, attack patterns, or sensitive
   configurations should be purged when no longer needed. An agent that
   retains a now-patched vulnerability's exploit code is a security liability.

5. **Alignment maintenance:** Beliefs and behavioral patterns that were
   reinforced but are now considered undesirable (e.g., a skill that encoded
   a deprecated coding practice) must be removable without retraining the
   entire model.

---

### 4.2 Machine Unlearning in LLMs

Machine unlearning is the formal study of removing specific knowledge from
trained model weights. A 2025 survey (arXiv 2503.01854) catalogues four
primary approach families:

**1. Direct Fine-Tuning (Gradient Ascent):**
Apply gradient *ascent* on the "forget set" — maximizing loss on examples to
be forgotten. This runs training backward. The approach achieves "high robust
forgetting" but "severely degrades model utility, producing uniform, low-quality
outputs" on retained knowledge.

**2. Localized Parameter Modification:**
Identify and modify only the specific neurons or layers that encode the target
knowledge. The "locate-then-unlearn" approach is strong on both utility and
robustness but computationally expensive (requires interpretability tools to
locate relevant circuits).

**3. Auxiliary Models:**
Use helper models — via contrastive decoding, knowledge distillation, or task
vector subtraction — to suppress target knowledge at inference time without
modifying the base model weights. Higher accuracy but added inference complexity.

**4. Input/Output-Based Unlearning:**
Prompt engineering and post-processing: refuse to answer certain questions,
filter outputs containing target content. Does not modify weights; is
circumventable. Most practical for operational systems that cannot afford
retraining.

**Critical challenge — quantization reversibility:** A disturbing 2024
finding shows that supposedly "unlearned" knowledge can be recovered by
quantizing the unlearned model. Reducing precision partially or fully
recovers forgotten content. This means unlearning at the weight level may
be inherently fragile for deployed quantized models.

**Critical challenge — relearning:** "Purportedly forgotten knowledge can be
recovered by sophisticated interventions such as model weight editing or
additional fine-tuning." Unlearning via gradient ascent appears to *suppress*
activations rather than *erase* representations. The underlying knowledge
may persist in latent form.

**Implication for skill-based systems:** These findings suggest that *weight-
level* forgetting is unreliable. For a system like claude-kit that uses
in-context injection rather than fine-tuning, the analogy to machine unlearning
is **skill deprecation and removal** — removing a skill from the load list
is functionally equivalent to context-level unlearning. This is substantially
more reliable than weight-level approaches because context exclusion is
deterministic: if a skill file is not loaded, its content is simply absent.

---

### 4.3 Selective Context Pruning

For in-context memory specifically, "forgetting" means not loading certain
content into the context window for the current session. This is the practical
equivalent of machine unlearning for systems that rely on context injection.

Selective context pruning strategies:

**Explicit deprecation:** Mark a skill as deprecated in its frontmatter.
The loader skips deprecated skills. Deprecated skills can remain on disk for
audit purposes without being injected into live sessions.

**Conditional loading:** Load skills only when certain preconditions are met
(the task involves a specific technology, the user has a certain role, the
project has certain dependencies). This prevents stale domain knowledge from
being loaded for irrelevant tasks.

**TTL-based expiration:** Skills carry a `expires:` field. After the TTL
expires, the skill is automatically excluded from loading until reviewed and
renewed. This enforces a freshness review cycle.

**Relevance scoring:** Before loading a skill, score it against the current
task/project context. Load only skills above a relevance threshold. This is
the RAG approach applied to skill selection.

---

### 4.4 Contamination Detection

Knowledge contamination occurs when a memory system contains false, outdated,
or misleading information that the agent will retrieve and use. Detection is
harder than it sounds because the system cannot know what it doesn't know.

**Staleness detection approaches:**

*Time-based:* Every fact in the knowledge store carries an ingestion timestamp
and a source timestamp. Facts older than a configurable TTL are flagged for
review. Simple but crude — some facts are stable for decades; others are stale
within weeks.

*Conflict detection:* When a new fact is ingested that contradicts an existing
fact, flag both for resolution. Zep/Graphiti (Section 5.5) does this
automatically via its edge invalidation mechanism: when a new fact contradicts
an existing graph edge, the old edge is marked invalid and the new edge is
added with a t_valid timestamp.

*Override rate monitoring:* Track how often an agent's outputs based on a
skill are corrected or overridden. High override rates for content sourced from
a specific skill signal that the skill may contain contaminated or outdated
information. DataGrid (2025) identifies "override frequency" as a key staleness
metric for knowledge curation systems.

*Semantic drift detection:* Embed all facts in a skill at ingestion time. At
periodic review, re-embed the current state of the source domain and compare.
Large embedding distance between old and new representations signals conceptual
drift in that area.

*Version mismatch detection:* Cross-reference skill content against
authoritative versioned sources. A Zephyr skill that references RTOS APIs
should be tagged with the RTOS version it was authored against. When a new
RTOS version ships, skills authored against older versions are automatically
flagged for review.

---

### 4.5 Privacy-Preserving Memory Management

Privacy in agent memory is a relatively new research area but rapidly maturing.
A 2025 ACL paper "Unveiling Privacy Risks in LLM Agent Memory"
(aclanthology.org/2025.acl-long.1227) demonstrated a Memory Extraction Attack
(MEXTRA) that can extract private user data from agent memory stores in a
black-box setting using adversarially crafted prompts.

The MemoryGraft attack (arXiv 2512.16962, December 2024) showed that an
attacker can persistently compromise an agent by injecting malicious "successful
experiences" into its long-term memory through ordinary documentation.
The agent then autonomously retrieves and follows those poisoned records, adopting
"unsafe shortcuts such as skipping validation, reusing stale results, or
executing risky automation."

**Governance principles for private memory:**

| Principle | Description |
|-----------|-------------|
| **Data minimization** | Store only what is necessary for the task; purge the rest |
| **Access isolation** | Per-user memory partitions; cross-user queries are blocked |
| **Retention limits** | Explicit TTL on all stored interactions |
| **Audit logs** | Track what was stored, when, and by whom |
| **Deletion verification** | After a deletion request, verify the content is absent from all indexes, not just the primary store |
| **Ingestion validation** | Validate new memory entries against known-good patterns before persisting |

---

## 5. Versioned Semantic Memory

### 5.1 Knowledge Graph Versioning

A knowledge graph is a directed labeled graph: nodes are entities, edges are
relationships, and both can carry properties (including temporal ones). For
knowledge to be *versioned*, the graph must track not just the current state
of each edge but its full history of states.

Knowledge graph versioning requires:

1. **Edge history:** Every edge carries a history of all values it has held,
   each with a valid-time interval.
2. **Schema versioning:** The ontology (set of allowed edge types and their
   semantics) must itself be versioned, with backward-compatibility rules
   that allow older graph states to be queried using older schemas.
3. **Transaction logging:** Every write to the graph is recorded with a
   transaction timestamp, enabling "time travel" queries: "What did the graph
   believe about entity X at time T?"

Temporal knowledge graphs add a second time axis beyond transaction time:
**valid time** — the real-world period during which a fact is true, which may
differ from when it was recorded.

---

### 5.2 Provenance Tracking

Provenance answers: "Where did this fact come from?" For AI agent memory, this
means:

- **Source attribution:** Which document, conversation, or external API did
  this fact originate from?
- **Derivation chain:** If this fact was inferred from other facts, what were
  those facts and what inference rules were applied?
- **Agent attribution:** Which agent (or human) asserted this fact?
- **Confidence score:** With what confidence was this fact asserted?

Without provenance, a knowledge store is a bag of unverifiable assertions.
With provenance, each fact can be:
- Traced back to its source for verification
- Weighted by source reliability
- Invalidated when its source is discredited
- Audited for compliance purposes

Zep's Graphiti engine maintains "bidirectional indices between semantic edges
and source episodes, enabling citation and traceability... semantic artifacts
can be traced to their sources for citation or quotation, while episodes can
quickly retrieve their relevant entities and facts." (arXiv 2501.13956)

---

### 5.3 Causal Linkage

Causal linkage extends provenance from "where did this fact come from" to
"why do we believe this fact is true — and what depends on it being true?"

In a causally linked knowledge store:

- Fact B that was derived from Fact A carries a `derived_from` edge to A
- If A is invalidated, the system can propagate invalidation to all B, C, D
  that depended on A
- An agent tasked with reviewing knowledge drift can follow causal chains
  rather than checking each fact independently

This is especially important for skill-based systems where a foundational
assumption ("Zephyr 3.x uses the `CONFIG_` prefix for all Kconfig options")
underlies dozens of concrete examples throughout a skill file. When that
assumption changes, all downstream examples become suspect — but without
causal linkage, there is no way to identify which ones.

---

### 5.4 Temporal Validity

Not all facts are eternal. Temporal validity is the formal representation of
a fact's real-world lifespan:

```
FACT: "nRF52840 GPIO max source current is 4 mA"
  valid_from: 2018-01-01
  valid_until: null  (still true, as of ingestion date)
  source: Nordic Semiconductor Product Specification v1.6
  source_date: 2023-06-15
  reviewed: 2025-01-10
```

Temporal validity enables:
- **Point-in-time queries:** "What were the correct Zephyr APIs at the time
  this codebase was written?"
- **Expiration alerts:** Facts where `valid_until` has passed, or where
  `source_date` exceeds a configured TTL, are automatically flagged.
- **Retroactive correction:** When a fact is found to have been wrong for a
  past period, the historical record can be corrected while preserving
  the full audit trail.

The bi-temporal model (Zep/Graphiti, arXiv 2501.13956) tracks two time axes:
- **T (event timeline):** When the real-world fact was true
- **T' (transaction timeline):** When the fact was ingested into the system

This distinction matters: a document published in 2022 describing a 2019 API
was *ingested* in 2025 but describes facts that were *valid* in 2019.
Conflating ingestion time with valid time causes spurious staleness alerts
and incorrect temporal reasoning.

---

### 5.5 The Zep / Graphiti Architecture

Zep (research.memgpt.ai adjacent; arXiv 2501.13956, January 2025) is the most
mature production implementation of versioned semantic memory for AI agents.
Its core engine, Graphiti, represents the current state of the art for
agent-oriented knowledge graph management.

**Architecture:**

Three-tier knowledge graph:

| Tier | Contents | Purpose |
|------|----------|---------|
| **Episode Subgraph** | Raw conversational data, documents | Source of truth for provenance |
| **Semantic Entity Subgraph** | Extracted entities and relationships with temporal edges | Queryable semantic memory |
| **Community Subgraph** | Clustered entity groups with summaries | High-level navigation and coarse retrieval |

**Bitemporal data model:**

Every graph edge carries four timestamps:
- `t'_created` — when this edge was added to the graph (transaction time)
- `t'_expired` — when this edge was removed from the graph (transaction time)
- `t_valid` — when the represented fact became true in the real world
- `t_invalid` — when the represented fact ceased to be true in the real world

When a new fact contradicts an existing edge: "the system invalidates the
affected edges by setting their t_invalid to the t_valid of the invalidating
edge, prioritizing newer information while preserving historical records."

**Retrieval pipeline:**

```
f(α) = χ(ρ(φ(α)))
```

Where:
- φ = search: cosine similarity + BM25 full-text + breadth-first graph search
- ρ = reranking: Reciprocal Rank Fusion + Maximal Marginal Relevance + cross-encoder
- χ = construction: formats results into context strings with temporal metadata

**Performance benchmarks:**
- 94.8% accuracy on Deep Memory Retrieval (vs. 93.4% for MemGPT)
- 18.5% improvement on LongMemEval with 90% latency reduction
- P95 retrieval latency: 300ms

---

## 6. RAG vs. In-Context Injection

### 6.1 The Fundamental Tradeoff

Claude-kit uses **in-context injection** as its memory mechanism: skill files
are loaded wholesale into the context window at session start. This is the
simplest possible approach — no retrieval infrastructure, no embedding, no
index — but it trades capacity for reliability.

RAG (Retrieval-Augmented Generation) retrieves relevant passages from an
external store at query time. This allows unlimited knowledge capacity but
introduces retrieval noise and latency.

| Dimension | In-Context Injection (claude-kit) | RAG |
|-----------|----------------------------------|-----|
| **Capacity** | Limited by context window | Unlimited |
| **Retrieval noise** | None — all content is present | Yes — wrong chunks can be retrieved |
| **Latency** | Zero (all content loaded at start) | Retrieval latency per query (typically 100–500ms) |
| **Infrastructure** | None — markdown files only | Vector database, embedding model, index |
| **Freshness** | Updated by editing skill files | Updated by re-indexing the source |
| **Governance** | Explicit — exact files loaded | Implicit — depends on retrieval quality |
| **Position effects** | Yes — subject to lost-in-middle | Partially — retrieved content placed at end |
| **Hard negatives** | None — curated content only | Yes — retrieval can return misleading context |

---

### 6.2 When Long Context Wins

The most comprehensive 2025 comparison (arXiv 2501.01880, "Long Context vs.
RAG for LLMs: An Evaluation and Revisits") evaluated both approaches across
13,628 questions. Key findings:

- Long Context (LC) correctly answers **56.3%** vs. RAG's **49.0%** overall
- LC produces **2,287 exclusive correct answers** that RAG misses
- LC particularly dominates on: Wikipedia-based content, fact-specific
  questions ("Who," "Where," "Which"), self-contained dense documents,
  and research papers in natural structure

Long context wins when:
- The knowledge corpus is small enough to fit in context
- Relevant information is hard to isolate without reading the full document
- Query types require comprehensive document understanding
- Source documents are dense and not easily segmented

**The model capacity limit:** Performance begins declining after ~32K tokens
for Llama-3.1-405B and after ~64K tokens for GPT-4. Context length is not
free — more tokens past a threshold actually *hurt* performance.

---

### 6.3 When RAG Wins

RAG outperforms long context for:
- **Dialogue-based contexts** with natural segmentation
- **Open-ended synthesis questions** ("How do I...") requiring multi-source
  assembly
- **Large knowledge bases** where the relevant fraction is small
- **Cost-constrained deployments:** RAG is "undoubtedly far more cost-
  efficient" than filling a long context (arXiv 2501.01880)

RAG also exclusively answers ~10% of questions that LC misses — particularly
in MultiDoc2Dial (dialogue), where RAG achieved 29 vs. LC's 5 correct answers.

The critical finding on retrieval quality: **"the detrimental effect of
irrelevant retrieved passages ('hard negatives') on LLMs' performance is
underscored by the discrepancy between retrieval recall and RAG accuracy."**
More retrieved passages does not consistently improve performance; it often
degrades it.

---

### 6.4 Hybrid Approaches

The field is converging on context-aware hybrid strategies rather than
committing to either approach universally.

**Tier-based hybrid:** Use in-context injection for core, high-relevance
knowledge (always needed) and RAG for large reference material (needed
occasionally). This is exactly what claude-kit's L2/L3 cache hierarchy
describes: skills are always-loaded L2; reference files linked from skills
are loaded on demand.

**Agentic RAG:** The agent decides at runtime whether to retrieve additional
context and what query to use. Rather than pre-fetching all potentially
relevant content, the agent retrieves only when it determines it lacks
sufficient context. This requires the agent to have accurate self-knowledge
about its own knowledge gaps.

**RAG over skills:** Instead of loading all skills at session start, maintain
a skill index and retrieve the most relevant skills for the current task at
session initialization. This preserves the "no retrieval noise during task
execution" property of in-context injection while adding skill-level relevance
filtering.

**RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval):**
Summarization-based retrieval that builds a tree of summaries at multiple
granularities. RAPTOR achieved **38.5% correctness** vs. chunk-based dense
retrieval at 20–21% in the long-context evaluation (arXiv 2501.01880). The
hierarchical structure allows retrieval at the appropriate granularity for
each query.

---

### 6.5 The RAPTOR Middle Ground

RAPTOR's strong performance suggests an important insight: **the unit of
retrieval matters enormously.** Retrieving raw text chunks is naive;
retrieving structured summaries at multiple granularities is substantially
better.

Applied to claude-kit's skill architecture:
- A skill file is analogous to a RAPTOR leaf node (high-detail, specific)
- A skill's frontmatter summary is analogous to a RAPTOR intermediate node
  (medium-detail, topical)
- A skill category summary would be a RAPTOR root node (low-detail, domain)

A retrieval-augmented skill loader would use this hierarchy: first check
category summaries to identify which skill domains are relevant, then load
full skill files for the relevant domains. This is the structural analog of
RAPTOR-style retrieval for skill-based agents.

---

## 7. Practical Memory Systems Survey

### 7.1 LangChain Memory Types

LangChain provides a practical taxonomy of in-context conversation memory
strategies, each representing a different point on the fidelity-capacity curve:

| Memory Type | Mechanism | Token Growth | Best For |
|-------------|-----------|-------------|----------|
| `ConversationBufferMemory` | All turns verbatim | Linear, unbounded | Short sessions |
| `ConversationBufferWindowMemory` | Last K turns verbatim | Capped at K×turn_size | Recency-focused tasks |
| `ConversationTokenBufferMemory` | Retain up to N tokens | Capped at N | Token-budget-aware apps |
| `ConversationSummaryMemory` | Summarize all past turns | Sublinear (summary grows slowly) | Long sessions, lower fidelity acceptable |
| `ConversationSummaryBufferMemory` | Summarize old + verbatim recent | Hybrid | Long sessions requiring recent fidelity |
| `VectorStoreRetrieverMemory` | Retrieve relevant past turns | Constant per turn | Very long sessions, topic-sparse |

The `ConversationSummaryBufferMemory` is the pragmatic best-of-both: old
context is compressed into a rolling summary, while recent context is kept
verbatim. The summary captures the "what" at the cost of losing exact phrasing
and low-level details.

LangChain has largely deprecated these in-memory classes in newer versions in
favor of LangGraph's persistent state management, but the conceptual taxonomy
remains instructive.

---

### 7.2 LlamaIndex Memory Modules

LlamaIndex frames memory as a context engineering problem: the question is
not "how do we store things" but "what tokens enter the context window and
when."

Key modules:
- **SimpleComposableMemory:** Combines working memory (context window) with
  external long-term memory stores
- **VectorMemory:** Embeds past interactions and retrieves semantically
  similar memories for each new query
- **ChatSummaryMemoryBuffer:** Hybrid buffer + summary analogous to
  LangChain's SummaryBufferMemory
- **SemanticSplitterMemory:** Splits context by semantic coherence rather
  than token count, producing more meaningful summaries

The LlamaIndex approach emphasizes that memory management is not orthogonal
to the RAG pipeline — the same retrieval infrastructure that serves document
queries can serve conversation history queries.

---

### 7.3 MemGPT / Letta Architecture

MemGPT (arXiv 2310.08560) introduced virtual context management by analogy
to OS virtual memory. The agent manages its own memory tiers through explicit
function calls:

```
Core Memory       ← In-context blocks (always loaded, agent-editable)
Recall Memory     ← Conversation history (searchable, retrieved on demand)
Archival Memory   ← Long-term knowledge store (retrieved on demand)
```

Key innovation: the agent itself decides what to promote from recall to core,
what to archive, and what to retrieve. This is **memory management as an
agentic skill** rather than a hardcoded system policy.

Letta (MemGPT's production evolution, September 2024) adds:
- **Shared memory blocks:** Multiple agents can read/write the same core
  memory block, enabling multi-agent knowledge coordination
- **Graphiti integration:** Temporal knowledge graph for semantic memory
  (see Section 5.5)
- **Perpetual threads:** Sessions survive indefinitely; recall memory is
  automatically managed

Letta's DeepLearning.AI course (2025) frames agent memory design as
"essentially context engineering: determining which tokens enter the context
window and how they're organized."

---

### 7.4 MIRIX: Six-Component Memory

MIRIX (arXiv 2507.07957, July 2025) represents the most granular memory
decomposition in the current literature. It decomposes agent memory into
six distinct components, each managed by a specialized sub-agent:

| Component | Contents | Analogous Human Memory |
|-----------|----------|----------------------|
| **Core Memory** | Essential identity facts, user preferences | Working memory / implicit self-model |
| **Episodic Memory** | Time-stamped events, specific interactions | Episodic memory |
| **Semantic Memory** | General knowledge, domain facts | Semantic memory |
| **Procedural Memory** | Learned habits, task patterns | Procedural / implicit memory |
| **Resource Memory** | Files, code, documents — indexed by content | External symbolic memory |
| **Knowledge Vault** | Verified high-confidence long-term knowledge | Crystallized intelligence |

Performance: MIRIX achieves **35% higher accuracy than RAG baseline** on
ScreenshotVQA while reducing storage by **99.9%** through intelligent
consolidation rather than raw storage.

The six-component model is important for claude-kit because it suggests that
the monolithic "skill file" concept can be decomposed: a skill about Zephyr
RTOS might legitimately contain semantic memory (API facts), procedural memory
(how to structure a device driver), and resource memory (links to reference
files). These different components have different update rates and different
validity periods.

---

### 7.5 A-MEM: Agentic Zettelkasten Memory

A-MEM (agiresearch/A-mem, 2025) applies the Zettelkasten note-taking
methodology to agent memory. The Zettelkasten principle: each note is atomic,
linked to related notes, and indexed by concept — not by topic or time.

A-MEM features:
- **Dynamic memory organization:** Each memory note is analyzed at ingestion,
  contextual keywords are extracted, and links to related existing notes are
  established
- **ChromaDB indexing:** Notes are embedded and stored for semantic retrieval
- **Network effects:** As more memories are added, the link structure becomes
  richer, enabling navigation by association rather than just keyword search

The Zettelkasten model is compelling for knowledge systems because it naturally
represents causal linkage (each note links to the notes it depends on) and
supports provenance (each note records its source). It also supports
policy-driven forgetting: when a note is deleted, the system can identify all
notes that linked to it and flag them for review.

---

## 8. Implications for claude-kit

### 8.1 Skill Size and the 500-Line Cap

The existing 500-line cap on skill files is well-motivated by the lost-in-the-
middle research. A skill longer than 500 lines (~3,500–4,000 tokens at typical
prose density) would occupy a substantial "middle blob" in the context,
receiving diluted attention from the model.

However, the research suggests the cap should be understood more precisely:

**The relevant metric is not line count but attention-effective token count.**
A 300-line skill dense with code examples may be as attention-demanding as a
700-line skill written in sparse prose. The cap should ideally be expressed in
terms of a token budget per skill (e.g., 3,000 tokens) rather than line count.

**The position of the skill in the context matters as much as its size.**
A 600-line skill loaded first (primacy position) will receive more attention
than a 300-line skill loaded fifth. The loading order should prioritize the
most critical skills: identity and behavioral constraints first, then domain
knowledge, then reference material.

**Recommendation:** Retain the 500-line cap as a practical proxy, but add
guidance that:
1. Critical behavioral rules (don't use deprecated APIs, always cite
   sources) should appear at the top of the skill, not buried in a long
   example section
2. Skills with large example sections should move examples to linked
   reference files (L3 cache), keeping the skill itself focused on
   rules and patterns (L2 cache)
3. A skill's first 50 lines should function as a "summary" of the skill's
   most important points, exploiting both primacy within the skill and
   the primacy of early-context content

---

### 8.2 Handling Knowledge That Becomes Outdated

The current system has no explicit mechanism for skill staleness detection.
A skill authored in January 2025 for Zephyr 3.6 will still be loaded unchanged
in December 2026, even if Zephyr 4.x has shipped with breaking API changes.

**Proposed additions to skill frontmatter:**

```yaml
---
name: zephyr-kernel
description: "Zephyr RTOS kernel APIs, threading, and device model"
domain: embedded
version: 0.3.0
# NEW: Staleness governance fields
authored: 2025-01-15
reviewed: 2025-09-20
valid_until: 2026-03-01       # TTL: review required before this date
source_version: "zephyr==3.7" # The versioned source this skill was authored against
stability: stable             # stable | evolving | volatile
drift_indicators:             # Signals that this skill may be outdated
  - "zephyr release notes"
  - "Nordic Semiconductor changelog"
---
```

The `valid_until` field enables **TTL-based expiration**: the nightly review
job can flag skills whose TTL has expired and create review tasks.

The `source_version` field enables **version mismatch detection**: when Zephyr
4.0 releases, skills with `source_version: "zephyr==3.x"` are automatically
flagged for review.

The `stability` field enables **review frequency calibration**: volatile skills
(rapidly changing domain) need monthly review; stable skills (hardware
specifications, mathematical constants) may be valid for years.

---

### 8.3 Versioned Skills with Changelogs

Each skill should maintain a changelog analogous to software changelogs.
This serves three purposes:

1. **Audit trail:** When something goes wrong (an agent uses a deprecated API
   despite the skill), the changelog shows when the skill was last reviewed
   and what changed.
2. **Rollback capability:** If a skill update introduces a regression, the
   previous version is recoverable.
3. **Diff-based review:** The `system-updater` plugin can review diffs rather
   than full skill files, reducing the review surface area.

**Proposed convention:** Each skill directory adds an optional `CHANGELOG.md`:

```markdown
# zephyr-kernel Skill Changelog

## [0.3.0] — 2025-09-20
### Updated
- Added `zephyr_work` API section for workqueue usage
- Corrected `k_thread_create` signature (removed deprecated `delay` parameter)

## [0.2.0] — 2025-04-10
### Added
- Full devicetree property accessor reference
### Deprecated
- `device_get_binding()` removed; `DEVICE_DT_GET()` is the canonical form

## [0.1.0] — 2025-01-15
- Initial skill creation
```

The validator (`validate-plugins.py`) can optionally check that the skill's
version in frontmatter matches the latest entry in `CHANGELOG.md`, enforcing
consistency between metadata and documented history.

---

### 8.4 RAG as a Complement to Skill Injection

The in-context injection approach has a natural ceiling: as a team's knowledge
domain grows, the number of skills exceeds what can reasonably be loaded into
a single context window without dilution.

For large, well-structured knowledge domains, a **RAG-over-skills** layer
could complement the current approach:

**Tier 0: Identity skills** — Always loaded; never subject to RAG filtering.
These are the behavioral constraints that must be present in every session.

**Tier 1: Core skills (current L2 cache)** — Loaded by agent declaration.
Skills that are almost always relevant for a given role. No change from
current behavior.

**Tier 2: Extended knowledge (RAG-selected)** — A larger skill library that
is too large to load wholesale. At session start, the agent's initial task
description is used to retrieve the most relevant skills from this library
via embedding similarity. Only the top-K retrieved skills are loaded into
context.

**Tier 3: Reference files (current L3 cache)** — Loaded on demand; no change.

This architecture preserves the zero-retrieval-noise property for Tier 0/1
content (critical rules, always-needed domain knowledge) while adding
scalable knowledge coverage for Tier 2 content (specialized reference
material, niche API documentation).

The critical constraint from the RAG research: **curate the skill library
carefully before indexing it**. RAG performance degrades sharply with
"hard negatives" — skills that look relevant but aren't. The same curation
discipline that makes individual skills valuable applies to the skill index.

---

### 8.5 Knowledge Drift Detection in system-updater

The `system-updater` plugin currently performs semantic review of plugin
content quality. It should be extended to detect and flag **knowledge drift**
— cases where skill content has diverged from current reality.

**Drift detection strategies for system-updater:**

**1. TTL scanning:** On each review cycle, identify all skills where
`valid_until` has passed or `reviewed` date is older than the skill's
`stability`-based review interval. Create review tasks for these skills.

**2. Version mismatch detection:** Query authoritative version sources
(e.g., Zephyr GitHub releases, Python PyPI, npm registry) and compare
against skills' `source_version` fields. Flag skills that reference outdated
source versions.

**3. Semantic drift via embedding comparison:** At each review cycle,
re-embed the skill content and compare against embeddings of authoritative
documentation for the same domain (scraped from official sources). Large
embedding distance signals conceptual drift.

**4. Cross-reference integrity:** Skills often reference specific APIs,
configuration options, or file paths. These references can be programmatically
validated against authoritative sources. A skill that references
`CONFIG_NET_L2_ETHERNET` should be validated against the current Zephyr
Kconfig reference to confirm the option still exists and has the described
semantics.

**5. Override rate tracking:** When an engineer agent overrides or corrects
content that was sourced from a specific skill (traceable via conversation
logs), record the override. Skills with high override rates are candidates
for review.

---

### 8.6 Policy-Driven Forgetting for Skill Content

"Policy-driven forgetting" in a skill-based system means: **given a policy
about what knowledge should be present in a session, systematically exclude
knowledge that violates that policy.**

Four policy categories are relevant for claude-kit:

**1. Temporal policy:** Knowledge older than a TTL is excluded unless
explicitly renewed. This prevents stale knowledge from silently persisting.

*Implementation:* Skills with expired `valid_until` are automatically
excluded from loading until the `reviewed` date is updated past the `valid_until`.

**2. Relevance policy:** Knowledge irrelevant to the current task or project
is excluded. This prevents domain knowledge from a different project from
polluting the current context.

*Implementation:* Conditional skill loading via project-context matching.
A Zephyr skill should not load when the active project is a Python web service.
The `domain` field in `ctl.json` already implements a coarse form of this.

**3. Conflict policy:** When two skills contain contradictory assertions about
the same topic, the older or lower-confidence skill is excluded.

*Implementation:* Skill validation (`validate-plugins.py`) should detect
intra-plugin contradictions. Cross-plugin contradictions require semantic
analysis — a task for `system-updater`.

**4. Deprecation policy:** Skills marked deprecated are excluded from all
loading. They remain on disk for audit purposes but do not enter any context.

*Implementation:* A `status: deprecated` frontmatter field that the loader
treats as an exclusion signal. Deprecated skills are archived in a
`skills/.deprecated/` directory after a configurable grace period.

The combination of these four policies implements the governance layer that
the podcast identified as the gap between "passive storage" and "active
governed semantic graph." For claude-kit, this governance layer does not
require a knowledge graph — it can be implemented as frontmatter-based
metadata evaluated by the loader and the `system-updater` review process.

---

### 8.7 Concrete Recommendations

The following recommendations are derived directly from the research surveyed
in this document. They are ordered by estimated implementation cost and impact.

| Priority | Recommendation | Research Basis | Effort |
|----------|---------------|----------------|--------|
| **High** | Add `valid_until` and `source_version` frontmatter fields to all skills | Temporal validity, knowledge drift | Low |
| **High** | Enforce skill loading order: identity → behavioral constraints → domain knowledge → reference | Lost-in-the-middle primacy effect | Low |
| **High** | Add `status: deprecated` frontmatter field; loader excludes deprecated skills | Policy-driven forgetting | Low |
| **Medium** | Add per-skill `CHANGELOG.md` convention; validator checks version consistency | Versioned semantic memory, audit trail | Medium |
| **Medium** | Extend `system-updater` to flag skills past `valid_until` TTL | Knowledge drift detection | Medium |
| **Medium** | Restructure skills: first 50 lines = summary of critical rules (exploit primacy) | Lost-in-the-middle, attention optimization | Medium |
| **Medium** | Replace line cap with token budget cap (3,000 tokens per skill) | Attention-effective context management | Medium |
| **Low** | Prototype RAG-over-skills for Tier 2 extended knowledge | Long context vs. RAG tradeoffs | High |
| **Low** | Add embedding-based semantic drift detection to `system-updater` | Contamination detection | High |
| **Low** | Implement cross-reference integrity validation for skills (API/config option existence checks) | Staleness detection | High |

**On the 500-line cap specifically:** Retain it as a practical heuristic but
add the explicit goal it is serving: "Keep each skill under the attention
dilution threshold." When the field matures and token-based tooling is more
accessible, migrate to a token budget (approximately 3,000 tokens = ~500 lines
of prose, but the conversion is content-dependent).

**On the long-context vs. RAG question:** For the foreseeable future, claude-kit's
in-context injection approach is correct for its use case. The skills are curated
(no hard negatives), small (below the attention dilution threshold), and cover a
bounded domain (embedded/firmware/backend/frontend engineering). RAG becomes
attractive when the skill count exceeds approximately 20–30 per domain — beyond
that point, context dilution from loading all skills likely outweighs the
retrieval noise from RAG-based skill selection.

---

## Sources

### Memory Architecture Surveys

- Wang et al. (2025). "A Survey on the Memory Mechanism of Large Language
  Model-based Agents." ACM Transactions on Information Systems.
  doi:10.1145/3748302
- Liu et al. (2024). "Memory in LLM-based Multi-agent Systems: Mechanisms,
  Challenges, and Collective." techrxiv.org/articles/1367390
- arXiv 2512.23343 (2024). "AI Meets Brain: A Unified Survey on Memory
  Systems from Cognitive Neuroscience to Autonomous Agents."
- arXiv 2504.15965 (2025). "From Human Memory to AI Memory: A Survey on
  Memory Mechanisms in the Era of LLMs."
- arXiv 2504.02441 (2025). "Cognitive Memory in Large Language Models."
- OpenReview 2026 Workshop. "MemAgents: Memory for LLM-Based Agentic
  Systems." openreview.net/forum?id=U51WxL382H

### In-Context Memory and Context Windows

- Liu et al. (2023/2024). "Lost in the Middle: How Language Models Use
  Long Contexts." Transactions of the Association for Computational
  Linguistics. doi:10.1162/tacl_a_00638. arXiv:2307.03172
- OpenReview (2025). "Lost in the Middle: An Emergent Property from
  Information Retrieval Demands in LLMs." openreview.net/forum?id=XSHP62BCXN
- Kang et al. (2025). "ACON: Optimizing Context Compression for Long-
  horizon LLM Agents." arXiv:2510.00615
- Anthropic (2025). "Effective Context Engineering for AI Agents."
  anthropic.com/engineering/effective-context-engineering-for-ai-agents
- JetBrains Research (2025). "Cutting Through the Noise: Smarter Context
  Management for LLM-Powered Agents."
  blog.jetbrains.com/research/2025/12/efficient-context-management

### MemGPT and Letta

- Packer et al. (2023). "MemGPT: Towards LLMs as Operating Systems."
  arXiv:2310.08560
- Letta (2024). "Agent Memory: How to Build Agents that Learn and Remember."
  letta.com/blog/agent-memory
- Letta (2024). "MemGPT is now part of Letta."
  letta.com/blog/memgpt-and-letta
- Letta (2025). "Benchmarking AI Agent Memory: Is a Filesystem All You Need?"
  letta.com/blog/benchmarking-ai-agent-memory
- Letta (2025). "Rearchitecting Letta's Agent Loop: Lessons from ReAct,
  MemGPT, & Claude Code." letta.com/blog/letta-v1-agent

### Versioned Semantic Memory and Knowledge Graphs

- Rasmussen et al. (2025). "Zep: A Temporal Knowledge Graph Architecture
  for Agent Memory." arXiv:2501.13956
- getzep/graphiti (2025). "Build Real-Time Knowledge Graphs for AI Agents."
  github.com/getzep/graphiti
- Neo4j (2025). "Graphiti: Knowledge Graph Memory for an Agentic World."
  neo4j.com/blog/developer/graphiti-knowledge-graph-memory
- OpenAI Cookbook (2025). "Temporal Agents with Knowledge Graphs."
  cookbook.openai.com/examples/partners/temporal_agents_with_knowledge_graphs
- arXiv 2409.04572 (2024). "Temporal Reasoning over Evolving Knowledge
  Graphs."

### Machine Unlearning and Forgetting

- arXiv 2503.01854 (2025). "A Survey of Machine Unlearning in Large Language
  Models: Methods, Challenges and Future Directions."
- ICLR 2025. "LLM Unlearning via Loss Adjustment."
  proceedings.iclr.cc/paper_files/paper/2025/file/6b315c0b736711b56f33cbacfb6d5d67
- IBM Research (2025). "Machine Unlearning for LLMs."
  research.ibm.com/blog/llm-unlearning
- Springer Nature (2024). "Digital forgetting in large language models:
  a survey of unlearning methods." Artificial Intelligence Review.
  doi:10.1007/s10462-024-11078-6
- Alan Turing Institute (2024). "Selective Forgetting in LLMs."
  turing.ac.uk/sites/default/files/2025-07/arc_selective_forgetting_in_llms.pdf
- arXiv 2509.24675 (2025). "Understanding the Dilemma of Unlearning for
  Large Language Models."

### Privacy and Memory Security

- ACL Anthology (2025). "Unveiling Privacy Risks in LLM Agent Memory."
  aclanthology.org/2025.acl-long.1227
- arXiv 2512.16962 (2024). "MemoryGraft: Persistent Compromise of LLM
  Agents via Poisoned Experience Retrieval."
- arXiv 2410.14931 (2024). "Ghost of the past: Identifying and Resolving
  Privacy Leakage of LLM's Memory Through Proactive User Interaction."
- Straiker (2025). "What Is Memory in LLMs and Why It Matters for
  Securing AI Agents." straiker.ai/blog/what-is-memory-in-llms

### RAG vs. Long Context

- arXiv 2501.01880 (2025). "Long Context vs. RAG for LLMs: An Evaluation
  and Revisits."
- arXiv 2410.05983 / ICLR 2025. "Long-Context LLMs Meet RAG: Overcoming
  Challenges for Long Inputs in RAG."
- Databricks (2024). "Long Context RAG Performance of LLMs."
  databricks.com/blog/long-context-rag-performance-llms
- LlamaIndex (2024). "Long Context RAG: New Architectures and Tradeoffs."
  llamaindex.ai/blog/towards-long-context-rag

### Modular Memory Systems

- Wang & Chen (2025). "MIRIX: Multi-Agent Memory System for LLM-Based
  Agents." arXiv:2507.07957
- AGI Research (2025). "A-MEM: Agentic Memory for LLM Agents."
  github.com/agiresearch/A-mem
- arXiv 2502.06975 (2025). "Position: Episodic Memory is the Missing Piece
  for Long-Term LLM Agents."

### LangChain and LlamaIndex Memory

- LangChain Documentation (2024). "Memory Overview."
  docs.langchain.com/oss/python/langgraph/memory
- Aurelio AI (2024). "Conversational Memory in LangChain."
  aurelio.ai/learn/langchain-conversational-memory
- Pinecone (2024). "Conversational Memory for LLMs with Langchain."
  pinecone.io/learn/series/langchain/langchain-conversational-memory

### Knowledge Drift and Freshness

- DataGrid (2025). "How to Stop Knowledge Drift Before It Breaks Your AI
  Agents." datagrid.com/blog/automated-knowledge-curation-ai
- Evidently AI (2024). "Machine Learning Monitoring, Part 5: Why You Should
  Care About Data and Concept Drift."
  evidentlyai.com/blog/machine-learning-monitoring-data-and-concept-drift

### Context Engineering and Skill Design

- arXiv 2410.08414 (2024). "Understanding Parametric vs. Contextual
  Knowledge in LLMs."
- Factory.ai (2025). "Evaluating Context Compression for AI Agents."
  factory.ai/news/evaluating-compression
- Alex Ewerlöf (2025). "RAG vs SKILL vs MCP vs RLM."
  blog.alexewerlof.com/p/rag-vs-skill-vs-mcp-vs-rlm
