# Multi-Agent Architecture Patterns: Specialization, Coordination, and Coherence

> A design research document examining the theoretical and practical foundations
> of multi-agent LLM systems — with direct implications for the 5-role team
> architecture of claude-kit.

**Date:** 2026-02-28
**Governing Process:** PROC-LC-001 (Market Analysis)

---

## Table of Contents

1. [Motivation: The Siloed-Component Problem](#1-motivation-the-siloed-component-problem)
2. [Multi-Agent Architecture Taxonomy](#2-multi-agent-architecture-taxonomy)
3. [Specialization vs. Generalization Tradeoffs](#3-specialization-vs-generalization-tradeoffs)
4. [Agent Coordination Patterns](#4-agent-coordination-patterns)
5. [Context Coherence Across Agents](#5-context-coherence-across-agents)
6. [Quality Gates and Review Loops](#6-quality-gates-and-review-loops)
7. [Failure Modes in Multi-Agent Systems](#7-failure-modes-in-multi-agent-systems)
8. [Observability and Debugging](#8-observability-and-debugging)
9. [Implications for claude-kit](#9-implications-for-claude-kit)
10. [Sources](#sources)

---

## 1. Motivation: The Siloed-Component Problem

A recurring theme in complex systems research is the tension between
*modular isolation* (which enables specialization and replaceability) and
*integrated coupling* (which enables coherence and emergent quality). In
classical software architecture, this manifests as the debate between
microservices and monoliths. In AI systems, it surfaces as the design question
for every multi-agent framework: how many agents, how specialized, and how tightly
coupled?

A podcast transcript quoted in the brief for this document captures the tension
precisely: traditional architectures separate learning, training, inference,
memory, and execution — they are loosely coupled, siloed components. Cognitive
systems, by contrast, integrate these into *continuous feedback loops* where
memory affects inference, inference triggers modification, and the runtime shapes
learning.

The danger the same transcript identifies is equally real: seamless integration
means that a change in one system instantly propagates and modifies all the
others. Tight coupling enables coherence but amplifies error. This is not a
new tension — it is the fundamental design challenge of every distributed system,
and multi-agent LLM architectures have made it newly urgent.

claude-kit's 5-role team model (engineer, grader, tester, debugger, knowledge)
is a direct attempt to find a stable point in this design space. This document
surveys the research landscape to understand whether that decomposition is
theoretically grounded, where it is likely to succeed, and where it will require
architectural evolution.

---

## 2. Multi-Agent Architecture Taxonomy

Multi-agent systems (MAS) have been studied since the 1980s in classical AI,
but the emergence of LLM-based agents has renewed interest and introduced new
design constraints. The following taxonomy covers the dominant coordination
architectures, with annotations for how each applies to modern LLM frameworks.

### 2.1 Hierarchical (Orchestrator + Workers)

An orchestrator agent decomposes a task and dispatches subtasks to worker
agents, then integrates their results. The orchestrator retains global state;
workers are stateless or narrowly stateful.

**Strengths:**
- Clear locus of responsibility — the orchestrator is accountable for the plan
- Workers can be highly specialized without needing global awareness
- Failure isolation: a worker failure is contained unless the orchestrator
  propagates the error

**Weaknesses:**
- Orchestrator becomes a single point of failure
- The orchestrator must understand all worker capabilities well enough to
  decompose correctly — this requires a meta-level model of the system
- Bottleneck at the orchestrator for all inter-worker communication

**LLM implementations:** MetaGPT's Software Company model, where the Product
Manager, Architect, and Project Manager form a de facto hierarchical tier above
engineers and QA agents. Microsoft's Magentic-One (AutoGen) implements a
"manager agent" that builds a dynamic task ledger and orchestrates specialists.

### 2.2 Peer-to-Peer (Flat Coordination)

Agents operate as equals, directly messaging each other to negotiate task
assignment, share findings, and coordinate output. There is no orchestrator.

**Strengths:**
- Resilient — no single point of failure
- Agents can form ad hoc coalitions for specific tasks
- Scales naturally if the communication protocol is well-defined

**Weaknesses:**
- Coordination overhead grows quadratically with agent count
- Without a designated integrator, results may be inconsistent or redundant
- Convergence is not guaranteed — agents may deadlock or loop

**LLM implementations:** ChatDev's Chat Chain model partially approaches this:
role pairs (CEO+CTO, Programmer+Reviewer) conduct bilateral dialogues in
sequence rather than true peer-to-peer. True peer-to-peer is rare in LLM MAS
because LLMs lack the reliable termination conditions needed to prevent loops.

### 2.3 Pipeline (Sequential Agents)

Agents are arranged in a fixed sequence. Each agent receives the output of the
previous agent, processes it, and passes its output to the next.

**Strengths:**
- Simple to reason about — the state space is linear
- Easy to implement, monitor, and debug
- Well-suited for processes that have natural sequential phases (plan → code →
  test → review)

**Weaknesses:**
- No parallelism — total latency is the sum of all agent latencies
- Errors propagate forward without correction unless checkpoints exist
- The pipeline is rigid — real tasks often require looping back

**LLM implementations:** Early ChatDev (2023) was a strict pipeline with phases:
Designing → Coding → Testing → Documenting. MetaGPT evolved away from strict
pipelines toward a hybrid with feedback loops. Most tool-calling chains in
LangChain/LangGraph begin as pipelines and add conditional edges for iteration.

### 2.4 Blackboard (Shared Knowledge Base)

All agents read from and write to a shared data structure — the "blackboard."
An independent control component selects which agent acts next based on
blackboard state. Agents do not communicate directly with each other.

**Strengths:**
- Agents are fully decoupled from each other — they need only understand the
  blackboard schema, not other agents' internals
- Highly extensible: new agents can be added without modifying existing ones
- Natural audit trail — all intermediate state is in the blackboard

**Weaknesses:**
- The blackboard can become a coordination bottleneck
- Concurrency conflicts if multiple agents write simultaneously without
  transactional semantics
- Control logic (which agent runs when) can become complex

**LLM implementations:** The blackboard pattern has renewed relevance for LLM
MAS. A 2025 paper ([arxiv.org/html/2507.01701](https://arxiv.org/html/2507.01701))
formalizes LLM-based blackboard systems where agents post structured entries
(findings, proposals, critiques) and a selector model chooses the next
contributor. Confluent's multi-agent event-driven architecture blog describes
a similar pattern using Kafka as the blackboard.

### 2.5 Market-Based (Agent Bidding)

Agents bid for tasks based on their current load, capabilities, and confidence.
A market mechanism allocates tasks to the most suitable (or cheapest) available
agent.

**Strengths:**
- Natural load balancing
- Handles heterogeneous agent capabilities gracefully
- Adaptive — task allocation adjusts dynamically

**Weaknesses:**
- Significant implementation complexity
- Requires well-calibrated bid functions (LLMs struggle with accurate
  self-assessment)
- Suboptimal under adversarial or misaligned agent incentives

**LLM implementations:** Market-based coordination is rare in current LLM MAS.
The main challenge is that LLMs cannot reliably estimate their own competence
on specific tasks. Research on agent self-assessment remains an open problem.

### 2.6 Where claude-kit Fits

claude-kit's 5-role team model is a **hybrid pipeline + hierarchical** system
with elements of the **blackboard** pattern:

| Architectural element | claude-kit equivalent |
|----------------------|-----------------------|
| Pipeline phases | engineer → grader → tester sequence for development workflows |
| Hierarchical control | Commands act as orchestrators, spawning role agents as workers |
| Blackboard | The filesystem and conversation state serve as a shared blackboard; the knowledge plugin provides a static sub-blackboard of domain reference material |
| Peer review | Grader and engineer interact as near-peers in review loops |

The coordination model is currently **command-driven sequential delegation**:
a slash command (e.g., `/develop`) orchestrates one or more subagent spawns
in a defined sequence, with handoffs mediated by explicit prompts rather than
a formal protocol. This is simple and debuggable, but it lacks the feedback
loops that make hierarchical and blackboard systems adaptive.

---

## 3. Specialization vs. Generalization Tradeoffs

### 3.1 The Case for Specialization

The foundational argument for specialization in multi-agent systems is
**context efficiency**: a specialized agent loads only the context relevant to
its role, keeping its effective context window uncontaminated by concerns
outside its scope.

MetaGPT (Hong et al., 2023; ICLR 2024 oral) provides the strongest empirical
case. By encoding Standardized Operating Procedures (SOPs) into role-specific
prompt sequences, MetaGPT agents act as software professionals (Product Manager,
Architect, Engineer, QA) with role-specific constraints on what they produce.
This structured decomposition outperforms chat-based multi-agent systems on
collaborative software engineering benchmarks because role specialization
prevents the "logic inconsistencies due to cascading hallucinations" that arise
when a single agent must hold the entire problem in scope.

AgentCoder (Huang et al., 2023) demonstrates role specialization at a micro
level: separating code generation (Programmer agent), test case design (Test
Designer agent), and test execution feedback (Test Executor agent) achieves
96.3% pass@1 on HumanEval with GPT-4 — a benchmark then close to human
performance. The key finding is that the *feedback loop between roles* (executor
reporting to programmer) is what drives quality, not specialization alone.

MapCoder (Islam et al., ACL 2024) maps the human developer mental model into
four agents: example recall, planning, code generation, and debugging. Each
corresponds to a distinct cognitive phase that humans apply when solving
competitive programming problems. The specialization follows the *grain of the
task* rather than organizational convention, achieving state-of-the-art results
on HumanEval (93.9%), MBPP (83.1%), and CodeContests (28.5%).

### 3.2 The Case Against Over-Specialization

Over-specialization produces agents that are brittle at their boundaries:

**Edge case blindness.** An agent specialized to write implementation code may
have no model of testability, making it systematically produce code that is
correct but untestable. Specialization that is too fine-grained creates gaps
at every handoff boundary.

**Inability to escalate.** When a specialized agent encounters a task that
spans its boundary (e.g., a grader that identifies a design flaw, not just a
code quality issue), it has no mechanism to escalate. It either silently
ignores the out-of-scope problem or produces an out-of-role response that
confuses downstream agents.

**Redundant context.** Highly specialized agents may each independently
reconstruct the same global understanding of the codebase, wasting tokens and
creating divergent interpretations.

**The Degeneration-of-Thought (DoT) problem**, identified in multi-agent debate
research, is a form of over-specialization pathology: once a specialized agent
has committed to a framing, it cannot escape it even when evidence demands
revision. The agent's identity constraint prevents the intellectual flexibility
needed for correct self-correction.

### 3.3 The Case Against Under-Specialization

A single powerful generalist agent competing with a multi-agent specialized
system faces the **context dilution** problem: all concerns — architecture,
implementation, test strategy, review criteria — must coexist in a single
context window, reducing the signal-to-noise ratio for each concern.

Under-specialization also means the agent cannot apply role-appropriate
heuristics. A generalist reviewing code and writing code simultaneously is
likely to be sycophantic toward its own output, because no identity shift
signals that it should adopt a critical stance.

### 3.4 The Ensemble Effect

Multi-agent systems produce an ensemble effect analogous to model ensembling
in classical ML: diverse agents with partially overlapping but not identical
views of a problem can correct each other's errors, reducing the variance of
the final output.

The ensemble effect is strongest when:
1. Agents have genuinely different perspectives (different roles, different
   sampling temperatures, or different context injections)
2. There is a mechanism for agents to disagree and reconcile (debate, voting,
   or a designated integrator)
3. The task has sufficient ambiguity that multiple valid approaches exist

Research on multi-agent debate (Du et al., 2023; EMNLP 2024) shows improvements
in factual accuracy and reasoning quality when agents argue for different
positions and revise based on counterarguments. However, the same research
identifies a critical caveat: if all agents are prompted identically, the
ensemble effect disappears — the system collapses into a monoculture.

### 3.5 The Optimal Grain of Specialization

| Specialization grain | Risk | Benefit |
|---------------------|------|---------|
| Too coarse (2 agents: planner + executor) | Edge cases between plan and execution | Low coordination overhead |
| Natural task phases (4-6 agents) | Boundary brittleness | Strong focus per phase, manageable coordination |
| Fine-grained (10+ agents) | Quadratic coordination overhead, DoT risk | Maximum context isolation |

The research consensus, from MetaGPT, ChatDev, and AgentCoder, is that 4-6
role-specialized agents aligned with *natural phase boundaries* of the task
represent the sweet spot. This aligns with claude-kit's 5-role model (engineer,
grader, tester, debugger, knowledge), though the knowledge role differs in kind —
it is a passive context provider, not an active task executor.

---

## 4. Agent Coordination Patterns

### 4.1 Direct Message Passing

The simplest coordination model: agents send structured messages to each other
through a defined channel. The message schema defines what each agent can
communicate.

ChatDev's "communicative dehallucination" mechanism operates through direct
bilateral dialogue — two agents (e.g., Programmer and Reviewer) conduct explicit
back-and-forth with role-reversal and thought instruction to surface and correct
hallucinations. This is direct message passing with a structured protocol.

**Limitations in LLM systems:** Direct message passing requires agents to be
simultaneously available (synchronous) or to support an async message queue.
Claude Code's subagent model currently supports sequential spawning, not
concurrent messaging.

### 4.2 Shared State / Shared Memory

Agents coordinate through a shared data structure — a file, a database, or an
in-memory store — rather than direct messages. Agents read the current state,
perform their work, and write updated state.

The filesystem in claude-kit functions as shared state: the engineer writes
code to the filesystem; the tester reads that code and writes test results;
the grader reads both. This is implicit shared state coordination, relying on
the filesystem as the blackboard.

**Advantages:** No coordination protocol needed. Agents are naturally decoupled.
Audit trail is automatic (git history). Easy to inspect intermediate state.

**Disadvantages:** No notification mechanism. Agents must be externally
orchestrated to run in the right order. Concurrent writes can conflict.

### 4.3 Event-Driven Coordination

An event from one agent (completing a task, failing a check, producing output)
automatically triggers the next agent. The system is reactive rather than
procedurally scripted.

Confluent's multi-agent event-driven pattern uses Kafka topics as the
coordination backbone: an agent's output event triggers the next agent's
processing subscription. Microsoft AutoGen v0.4 adopted an asynchronous,
event-driven architecture specifically to enable this coordination style, with
agents communicating through typed messages in an actor model.

**Advantages:** Natural parallelism — non-dependent agents can process
simultaneously. Decoupled — agents don't know about each other, only about
event types. Resilient — failed agents can retry without restarting the pipeline.

**Disadvantages:** Harder to debug — the execution graph is implicit in the
event subscriptions. Requires an event broker, adding operational complexity.

### 4.4 Async Parallel vs. Synchronous Sequential

| Dimension | Synchronous Sequential | Async Parallel |
|-----------|----------------------|----------------|
| Latency | Sum of all agent latencies | Max of independent agent latencies |
| Complexity | Low — linear control flow | High — requires coordination for dependent results |
| Error handling | Simple — stop on first failure | Complex — partial failures need reconciliation |
| Context sharing | Natural — each agent gets full prior output | Requires explicit merge of parallel results |
| Debuggability | High — deterministic execution order | Low — non-deterministic interleaving |

For creative and generative tasks (coding, documentation, architecture), the
research suggests that **synchronous sequential with well-defined feedback
loops** is more reliable than async parallel. The reason is that LLM outputs
are highly sensitive to context, and parallel agents working from the same
partial context often produce redundant or contradictory outputs that are
expensive to reconcile.

Async parallel excels for independent subtasks: searching multiple sources,
generating multiple candidate solutions for a selection step, or running
independent validation checks.

### 4.5 How claude-kit Handles Coordination

Currently, claude-kit uses **synchronous sequential delegation** mediated by
command files. A command (e.g., `/develop`) defines an orchestration script that
spawns subagents in a fixed sequence, passing outputs via conversation context
or filesystem. This is:

- **Predictable** — the execution order is defined in the command file
- **Debuggable** — failures are localized to a specific agent spawn
- **Limited** — no feedback loops between agents unless explicitly scripted;
  no parallelism; coordination logic is mixed into the command narrative

The gap between this model and what research suggests is optimal (event-driven,
feedback-loop-capable coordination) is one of the key architectural questions
this document addresses in [Section 9](#9-implications-for-claude-kit).

---

## 5. Context Coherence Across Agents

### 5.1 The Cache Coherence Problem

In distributed computer systems, cache coherence refers to the guarantee that
all processors reading from a shared memory location see the same value at
any given time. Without coherence protocols, processors develop divergent views
of the same data, producing incorrect results that are extremely difficult to
debug.

The same problem exists in multi-agent LLM systems. Each agent builds a local
"model" of the codebase, the task, and the relevant context. Without an
explicit coherence mechanism, these local models diverge. The divergence is
invisible — agents don't report when their understanding conflicts with another
agent's understanding; they simply act on their local model.

### 5.2 The Chinese Whispers Problem

In sequential agent pipelines, information degrades with each hop. Each agent
compresses the input it receives (via summarization, selective attention, or
token limits) and adds its own interpretation. By the time a downstream agent
receives the context, it may be significantly different from what the upstream
agent intended.

Research on multi-turn LLM performance (Ouyang et al., 2025) documents severe
degradation: LLMs show an average 39% drop in performance in multi-turn
conversations compared to single-turn, and once the model "takes a wrong turn"
in a conversation, it fails to recover. In a sequential agent pipeline, this
failure mode amplifies at each handoff: the third agent in a chain is working
from context that has been compressed and reinterpreted twice.

Practical mitigations:
- **Persistent structured output.** Agents write structured artifacts (YAML,
  JSON, structured markdown) rather than natural-language summaries. Downstream
  agents parse the structure rather than interpreting free text.
- **Pass-through of original artifacts.** Critical inputs (the original spec,
  the original code file) are passed to each agent directly, not reconstructed
  from summaries.
- **Explicit handoff documents.** Each agent produces a structured handoff
  document that the next agent must acknowledge before proceeding.

### 5.3 Shared Context / Knowledge Graphs

Several research directions address context coherence through shared knowledge
structures:

**Shared vector databases.** M-RAG (Wang et al., 2024) coordinates distributed
retrievers and generators via shared memory with task-specific roles. Agents
query and write to a shared vector store, ensuring that knowledge discoveries
made by one agent are available to others.

**Agentic RAG.** The "Agentic RAG" paradigm (Agentic RAG Survey, 2025) extends
classic retrieval-augmented generation to multi-agent settings, where agents
dynamically decide when to retrieve, what to retrieve, and how to share
retrieved knowledge with sibling agents. AU-RAG (Jang and Li, 2024) agents
decide dynamically between retrieved and parametric knowledge based on
generation uncertainty.

**Knowledge graphs.** Some multi-agent architectures use structured knowledge
graphs as the coherence mechanism — agents write their findings as graph nodes
and edges, and downstream agents query the graph rather than reading free-text
conversation history. This provides stronger coherence guarantees than text-based
shared state.

### 5.4 How Companion Plugins Address This in claude-kit

claude-kit's companion plugin mechanism provides a form of **static context
coherence**: the knowledge plugin for a team injects the same domain reference
material into all agents within the team. This ensures that, for example, the
engineer, grader, and tester agents all share the same understanding of Zephyr
RTOS APIs, coding conventions, and project structure — the knowledge plugin is
a read-only shared context.

This solves the static knowledge coherence problem but does not address
**dynamic coherence**: knowledge generated during a task (e.g., a design
decision made by the engineer) is not automatically propagated to the grader
or tester. The handoff between agents is mediated by conversation context,
which is subject to the Chinese Whispers degradation described above.

---

## 6. Quality Gates and Review Loops

### 6.1 The Critic Agent Pattern

The critic agent pattern — a separate agent whose role is to evaluate and
criticize the output of a producer agent — is one of the most well-supported
patterns in the LLM multi-agent literature. The pattern directly addresses
the sycophancy problem: a producer LLM tends to be satisfied with its own
output, but a critic agent with a distinct identity and explicit critique mandate
can surface problems the producer would not catch.

The pattern manifests in several architectural forms:

**Actor-Critic:** The actor produces output; the critic evaluates it and returns
a critique; the actor revises. Iterations continue until the critic is satisfied
or a maximum revision count is reached. This is the architecture used by
AgentCoder's programmer-executor feedback loop.

**Debate:** Multiple agents independently produce answers, then argue for their
positions while critiquing others'. A judge agent synthesizes the debate into
a final answer. Du et al. (2023) show this improves factual accuracy
significantly over single-agent generation.

**Panel Review:** Multiple critic agents, each with a distinct evaluation
persona (correctness, style, performance, security), independently evaluate the
producer's output. A coordinator synthesizes the critiques. ChatEval (2024)
demonstrates that diversity of critic personas is essential — a homogeneous
panel of critics converges on the same blind spots as a single critic.

### 6.2 LLM-as-a-Judge

The "LLM-as-a-Judge" paradigm (Zheng et al., 2023; reviewed extensively in
2024-2025 surveys) formalizes the use of one LLM to evaluate the output of
another. Key findings relevant to the grader role in claude-kit:

**Evaluation formats:**
- *Pairwise:* Judge selects between two outputs. Higher reliability but requires
  a reference output.
- *Pointwise:* Judge assigns a score or grade to a single output. More flexible
  but more susceptible to absolute-scale calibration errors.
- *Criteria-referenced:* Judge evaluates against an explicit rubric. Most
  reliable for tasks with well-defined quality criteria.

**Known failure modes of LLM judges:**
- *Position bias:* Judges prefer the first response in pairwise evaluation
- *Verbosity bias:* Judges favor longer, more elaborate responses even when
  they are not more correct
- *Self-enhancement bias:* Judges trained on similar data as the producer
  share its blind spots
- *Criteria interpretation drift:* The judge's understanding of a criterion
  shifts subtly across evaluations, producing inconsistent scores

**Mitigation:** The most effective mitigation for judge failure modes is
**independent judge identity** — ensuring the judge is prompted with a
distinct role, distinct criteria, and no knowledge of the producer's identity.
A grader that shares context with the engineer it is grading loses independence.

**Meta-judge architecture:** Recent research (arXiv 2504.17087, 2025) explores
meta-judges — LLMs that evaluate the quality of judge LLMs. This produces
a hierarchical review structure: Producer → Judge → Meta-judge. The meta-judge
acts as a quality control layer on the quality control layer, improving
calibration in high-stakes evaluation settings.

### 6.3 Self-Reflection vs. Peer Review

| Dimension | Self-reflection | Peer review (separate agent) |
|-----------|----------------|------------------------------|
| Cost | Low — one agent call | Higher — two agent calls |
| Independence | None — same model, same priors | High if critic has distinct context |
| Effectiveness | Moderate for surface errors | High for substantive errors |
| DoT risk | High — agent doubles down on wrong answers | Lower — critic identity interrupts the loop |
| Implementation | Simple | Requires coordination |

Self-reflection (also called self-refine) is valuable for surface-level
improvements — formatting, obvious logical errors, completeness checks. It fails
for the same class of errors that caused the original mistake, because the
model's prior that led to the error is unchanged.

Peer review by a separate agent with distinct context injection is more
effective for substantive critique but requires that the critic's identity
is genuinely independent. Research shows that using the same model with
the same base prompt as both producer and critic captures only a fraction
of the benefit of a truly distinct critic.

### 6.4 Optimal Review Cycles

How many review iterations are optimal? The research gives a nuanced answer:

- **1-2 cycles** are almost always beneficial — the first critique surfaces
  obvious errors the producer missed.
- **3-5 cycles** show diminishing returns. Each cycle adds latency and cost
  with smaller quality improvements.
- **5+ cycles** risk DoT: agents reinforce their commitments rather than
  revising them. The system gets stuck in a local optimum.

The Degeneration-of-Thought (DoT) problem (Liang et al., 2023) is the key
failure mode: agents that initially commit to an incorrect answer become more
confident in it as the debate continues, rather than correcting. The implication
for claude-kit is that grader-engineer cycles should have a hard cap (2-3
iterations maximum) and should produce an artifact (not a conversation loop)
to prevent drift.

### 6.5 When Does the Grader Pattern Degrade?

The grader role in claude-kit is subject to two distinct degradation risks:

**Context contamination.** If the grader reads the same companion plugins as
the engineer and operates in the same conversation context, their evaluative
independence is compromised. The grader will tend to evaluate the engineer's
output against the same assumptions the engineer used to produce it — which
means it cannot catch assumption-level errors, only implementation errors.

**Role confusion.** If the grader is asked to produce both a critique and a
fix, it is no longer functioning as an independent reviewer. The act of
fixing activates the engineer mindset and suppresses the critic mindset.
Grader commands should produce evaluation artifacts only; fixes should be
delegated back to the engineer via a structured handoff.

**Grade inflation.** Without explicit calibration criteria (a rubric), grader
agents tend toward generous evaluation. The verbosity bias and self-enhancement
bias compound this: elaborate, long outputs from the engineer look thorough, and
the grader — sharing the engineer's base priors — tends to score them highly.

---

## 7. Failure Modes in Multi-Agent Systems

The first comprehensive taxonomy of multi-agent LLM system failures was
published in the MAST dataset (Cemri et al., 2025), covering 1,600+ annotated
failure traces across 7 MAS frameworks, yielding 14 unique failure modes in
three categories.

### 7.1 Taxonomy of Failure Modes

| Category | Failure mode | Description |
|----------|-------------|-------------|
| **System design** | Over-specification | The task spec is too rigid; agents cannot adapt to edge cases |
| **System design** | Under-specification | The task spec is too vague; agents make incompatible assumptions |
| **System design** | Tool misalignment | Agents are given tools they cannot use correctly |
| **System design** | Monoculture | All agents use the same model/prompts, sharing the same blind spots |
| **Inter-agent** | Cascading failure | One agent's bad output is accepted as valid by downstream agents |
| **Inter-agent** | Conformity bias (sycophancy) | Agents reinforce each other's errors rather than providing independent evaluation |
| **Inter-agent** | Context pollution | Irrelevant or incorrect context from one phase contaminates the next |
| **Inter-agent** | Role confusion | Agents drift outside their role boundaries, producing out-of-scope output |
| **Inter-agent** | Coordination overhead | Communication cost exceeds the benefit of parallelism |
| **Task verification** | Hallucinated success | Agents report task completion without verification |
| **Task verification** | Evaluation drift | Grading criteria shift subtly across evaluation rounds |
| **Task verification** | Missing ground truth | No reference output exists; quality cannot be assessed |
| **Task verification** | Timeout / loop | Agents cycle without terminating |
| **Task verification** | Partial failure | One agent in a required chain fails; the system has no recovery path |

### 7.2 Agent Sycophancy

Sycophancy in single-agent LLM systems — the tendency to agree with user
assertions even when they are incorrect — is well-documented. In multi-agent
systems, it manifests as *conformity bias*: agents update their position toward
the group consensus regardless of the evidence quality of that consensus.

The MAST research identifies this as a primary bottleneck. When a critic agent
observes that the producer seems confident, it tends to moderate its critique —
even when the producer's confidence is itself a hallucination. The conformity
bias is stronger when:
- Agents share a base model (same training distribution)
- The orchestrator signals authority ("the senior engineer says...")
- The critic is prompted after seeing the producer's output without independent
  scaffolding

**Mitigation:** Prompt the critic agent before it sees the producer's output
(generate an independent assessment first, then compare). Use diverse base
models or temperatures. Use structured rubrics that force the critic to assess
specific criteria rather than making holistic judgments.

### 7.3 Cascading Failures

Cascading failures occur when an erroneous output is passed to downstream agents
as valid input, and those agents — lacking the holistic context to recognize the
error — propagate and amplify it.

The Galileo research blog documents the mechanism precisely: LLM agents typically
accept flawed inputs uncritically as valid premises. They lack the "holistic
context-aware intuition" to challenge peer-provided information. This is not
an intelligence failure but a design failure — the agents are designed to treat
their input as reliable, because that is the only reasonable assumption in a
well-functioning pipeline.

**Mitigation:** Validate intermediate outputs before they enter the next pipeline
stage. Use schema validation (not just LLM review) for structured outputs.
Insert explicit sanity-check agents at high-risk handoff points (e.g., after
code generation, before test execution).

### 7.4 Context Pollution

Context pollution is the accumulation of irrelevant, incorrect, or
contradictory information in the shared context that agents use for subsequent
decisions. Each agent that writes to shared context risks adding noise that
future agents will have to reason around.

Context pollution is particularly dangerous in long pipelines because the
"lost in the middle" phenomenon causes LLMs to weight recent and earliest
context more heavily than middle context. Earlier correct information can be
effectively deleted by later incorrect additions.

**Mitigation:** Partition context by role and phase. The engineer's scratchpad
should not be visible to the tester as-is; a structured summary or handoff
artifact should mediate the transition. Compress context aggressively at phase
boundaries.

### 7.5 Coordination Overhead

As agent count increases, coordination cost grows. The break-even point — where
the quality gains from specialization exceed the cost of coordination — is
empirically around 4-6 agents for coding tasks. Beyond this, coordination
overhead dominates.

ChatDev's benchmark performance is illustrative: despite significant
architectural sophistication, it achieves a correctness rate of approximately
25% on complex tasks. The coordination machinery introduces failure points that
individually are rare but cumulatively are common.

### 7.6 Fault-Tolerant Multi-Agent Architecture

Research on fault tolerance in multi-agent LLM systems is nascent but points
to several practical patterns:

**Checkpoint-based recovery.** Persist agent outputs to durable storage at each
phase boundary. If a downstream agent fails, restart from the last checkpoint
rather than from scratch.

**Graceful degradation.** Define for each agent: what is the minimum viable
output that allows the pipeline to continue? If the full output is not
achievable, produce the degraded version and flag it explicitly.

**Retry budgets.** Give each agent a bounded retry count. After N failures,
escalate to a human or to an orchestrator agent rather than retrying in an
infinite loop.

**Independent validation.** Run a separate validation agent after each
high-risk step. The validation agent checks only structural and schema
properties (not semantic quality), because structural errors are cheap to
detect and expensive to propagate.

---

## 8. Observability and Debugging

### 8.1 The Problem Space

Debugging a multi-agent LLM system is fundamentally different from debugging
a conventional distributed system. In conventional systems, the failure is
deterministic: given the same inputs, the same failure occurs. In LLM systems,
failures are stochastic: the same pipeline run may succeed or fail based on
sampling randomness. This makes reproduction difficult and root-cause analysis
uncertain.

Additionally, the "logic" of an LLM agent is not in code — it is in the prompt
and the model weights. Tracing a failure back through a multi-agent pipeline
requires reconstructing not just what each agent received and produced, but
*why* it produced what it did — which requires understanding the model's
internal reasoning, not just its inputs and outputs.

### 8.2 The OpenTelemetry GenAI Standard

In 2024-2025, OpenTelemetry emerged as the consensus observability standard for
LLM systems, with the GenAI Semantic Conventions providing a standard schema
for tracing agent execution.

Key concepts:

**Spans.** Each agent execution is a span with a defined start time, end time,
and attribute set. Multi-agent pipelines produce a trace — a directed acyclic
graph of spans linked by parent-child relationships.

**Attributes.** The GenAI semantic conventions define standard attributes for
LLM spans:
- `gen_ai.request.model` — the model used
- `gen_ai.request.max_tokens` — token budget
- `gen_ai.usage.prompt_tokens` — tokens consumed by input
- `gen_ai.usage.completion_tokens` — tokens consumed by output
- `gen_ai.agent.id` — the agent identity
- `gen_ai.tool.name` — tool calls made

**Events.** Agent events (tool calls, sub-agent spawns, retrievals) are logged
as span events with structured payloads.

**Tracing multi-agent pipelines.** When an orchestrator spawns a subagent,
the subagent's span is a child of the orchestrator's span. This preserves the
causal chain: a failure in a leaf agent is traceable back through the parent
spans to the orchestrating command that initiated the workflow.

Microsoft has led the integration effort, contributing GenAI semantic conventions
to OpenTelemetry and implementing them in AutoGen v0.4, Semantic Kernel, and
Azure AI packages for LangChain and LangGraph. AG2 (the community fork of
AutoGen) ships with built-in OpenTelemetry tracing that provides full visibility
into multi-agent workflow execution.

### 8.3 What Each Agent Should Emit

For a multi-agent system to be debuggable, each agent should emit structured
telemetry at minimum covering:

| Telemetry category | Required fields | Purpose |
|-------------------|----------------|---------|
| **Identity** | Agent role, agent version, session ID | Identify which agent failed |
| **Input** | Prompt hash, context length, tool list | Understand what the agent received |
| **Output** | Output length, output schema, validation result | Identify what the agent produced |
| **Tools called** | Tool name, tool input hash, tool result code | Trace tool failures |
| **Subagent spawns** | Spawned agent ID, spawn prompt | Link parent and child spans |
| **Decisions** | Key reasoning branches (if extractable) | Understand why the agent acted as it did |
| **Duration** | Start time, end time | Identify performance bottlenecks |
| **Errors** | Error type, error message, retry count | Root-cause failures |

### 8.4 Trace-Based Root Cause Analysis

Given a multi-agent trace, root cause analysis follows a pattern:

1. **Find the leaf failure.** The first span to fail (non-zero exit, error
   event, or schema validation failure) is the primary failure point.
2. **Walk the parent chain.** Each parent span reveals what context was
   passed to the failing agent. Check for context pollution or missing
   inputs.
3. **Check the sibling spans.** If a sibling agent (running in the same
   orchestration step) succeeded, compare inputs. The difference between
   the successful and failing inputs is the root cause.
4. **Check the input hash.** If the same input hash previously succeeded
   (in a prior run), the failure is non-deterministic (model stochasticity
   or transient tool error). If it consistently fails, it is a systematic
   issue.

### 8.5 The Debugger Role in Claude-Kit

The debugger agent's function — diagnosing failures across the multi-agent
pipeline — maps naturally onto trace-based root cause analysis. To be
effective, the debugger needs:

- Access to the structured output of each preceding agent (the equivalent
  of the trace)
- The ability to query intermediate artifacts (code written by the engineer,
  test results from the tester)
- A mental model of the normal expected output of each role, so it can
  identify anomalies

Currently, the debugger agent in claude-kit has access to the filesystem and
conversation context but does not have structured telemetry from prior agents.
Failures are described in natural language rather than structured trace data.
This limits the debugger's diagnostic precision — it must infer what each
agent received and produced from prose rather than reading structured logs.

A structured handoff artifact (see [Section 9](#9-implications-for-claude-kit))
would partially address this, giving the debugger a structured record of what
each agent produced, even without full OpenTelemetry instrumentation.

---

## 9. Implications for claude-kit

This section synthesizes the research findings into concrete architectural
questions and recommendations for the claude-kit plugin system.

### 9.1 Is the 5-Role Decomposition Correct?

The research supports the 5-role model as broadly correct. Role counts in the
4-6 range match the optimal grain of specialization identified by MetaGPT,
AgentCoder, and MapCoder. The decomposition into engineer, grader, tester,
debugger, and knowledge maps onto natural task phases with defensible boundaries.

**The knowledge role is different in kind.** Unlike the other four roles, the
knowledge plugin is a passive context provider — it does not execute tasks or
produce artifacts. This is architecturally sound (it implements a static
blackboard for domain reference material) but should not be counted alongside
the active roles when assessing agent coverage.

**Missing roles to consider:**

| Potential role | Rationale | Risk |
|---------------|-----------|------|
| **Architect/Planner** | High-level task decomposition before the engineer writes code | May overlap with engineer; adds coordination overhead |
| **Reviewer/Integrator** | Cross-cutting review that spans engineer, grader, and tester outputs | May duplicate grader; risks role confusion |
| **Orchestrator** | Explicit coordination agent that sequences the active roles | Adds hierarchy; addresses the coordination gap identified in Section 4.5 |

The strongest case is for a lightweight **Orchestrator** role — a coordination
agent that sequences engineer → grader → tester → debugger workflows, manages
feedback loops, and handles partial failures. This is currently handled by
command files, but as workflows become more complex, command files become
unwieldy coordination scripts. A dedicated orchestrator agent with knowledge
of the team structure and workflow state would be more robust.

### 9.2 Grader-Engineer Interaction Protocol

The research on LLM-as-a-Judge and critic agent patterns identifies a clear
best practice: critic independence requires context partitioning. The grader
should not share the engineer's planning context when evaluating the engineer's
output.

**Recommended protocol:**

```
Engineer → produces code + structured handoff artifact
           {
             "files_modified": [...],
             "design_decisions": [...],
             "known_limitations": [...],
             "confidence": "high|medium|low"
           }

Grader → receives only:
           - The code itself
           - The original task spec
           - The grading rubric (from knowledge plugin)
           NOT the engineer's reasoning or planning context
```

This partitioning ensures the grader evaluates the output as a user or
reviewer would see it — against the specification, not against the
engineer's intentions. The grader's output should be a structured review
artifact, not a prose critique:

```
{
  "verdict": "pass|conditional|fail",
  "findings": [...],  // specific, actionable items
  "rubric_scores": {...},  // per-criterion scores
  "escalation": null | "design" | "architecture"  // if the problem exceeds the grader's scope
}
```

The `escalation` field is important: it gives the grader a mechanism to
flag problems that are beyond code quality — design flaws, architecture
violations — without requiring the grader to attempt to fix them. This
addresses the over-specialization edge case problem described in Section 3.2.

### 9.3 Cross-Team Consistency Automation

The current cross-team consistency rule requires human review of all sibling
plugins when a bug is fixed in one. This is correct in principle but difficult
to enforce consistently.

The research on agentic RAG and blackboard architectures suggests a concrete
solution: a **consistency agent** that runs as part of the CI pipeline when any
plugin is modified. The consistency agent:

1. Receives the diff for the modified plugin
2. Retrieves the analogous sections from all sibling plugins (same role,
   different teams)
3. Identifies structural and content divergences
4. Generates a structured report of inconsistencies
5. Optionally generates proposed patches for sibling plugins

This maps onto the nightly-plugin-review workflow that already exists in
claude-kit, but specialized for cross-team structural consistency rather than
general quality review.

### 9.4 The Orchestrator Question

Should there be an explicit orchestrator role that coordinates the other four
active roles?

**Arguments for an orchestrator:**
- Commands are currently acting as implicit orchestrators, but they are static
  scripts, not adaptive coordinators
- An orchestrator agent can handle partial failures gracefully (if the tester
  fails, it can retry, escalate, or continue without blocking)
- An orchestrator can maintain workflow state across agent spawns, enabling
  feedback loops without manual scripting
- AutoGen's Magentic-One demonstrates that a dynamic task ledger orchestrator
  significantly outperforms static pipeline definitions on complex tasks

**Arguments against an orchestrator:**
- Adds hierarchy and complexity to the system
- The orchestrator becomes a new single point of failure
- For the majority of use cases (single role, single task), an orchestrator
  is overhead without benefit

**Recommendation:** Implement orchestration as an optional mode rather than
a mandatory role. For simple use cases, the current command-driven sequential
model is appropriate. For complex multi-phase workflows (plan → implement →
test → grade → iterate), expose a workflow command that spawns an orchestrator
agent responsible for sequencing and coordinating the team.

### 9.5 Evolving the Knowledge Plugin: Static Injection vs. Dynamic RAG

The current knowledge plugin provides static context injection — a fixed set
of skills that are loaded into the agent's context at startup. This is simple,
predictable, and efficient for well-defined domains with stable reference
material.

The research on Agentic RAG (2025 survey) identifies the limitations of static
injection: as the knowledge base grows, injecting everything at startup bloats
the context window and reduces signal-to-noise. Dynamic retrieval — where the
agent fetches only the knowledge relevant to the current task — is more scalable.

**Hybrid architecture for knowledge plugins:**

| Knowledge type | Loading strategy | Rationale |
|----------------|-----------------|-----------|
| Core conventions (coding standards, architecture rules) | Static injection | Always relevant; small; foundational |
| API references (SDK docs, library signatures) | Dynamic RAG | Large; only relevant portions needed |
| Project-specific context (recent decisions, open issues) | Dynamic RAG | Changes frequently; must be fresh |
| Historical examples (prior grader reports, test patterns) | Dynamic RAG | Valuable for calibration; large corpus |

Implementing dynamic RAG within claude-kit would require either integrating
with an external vector store (ChromaDB, Pinecone) or using the filesystem as
a simple retrieval backend (ripgrep for keyword search, structured directories
for category-based retrieval). The latter is more aligned with claude-kit's
current dependency model (no external services required).

### 9.6 Workflow Plugins: Multi-Agent Pipelines as First-Class Constructs

The current command architecture defines single-phase workflows. Complex
multi-phase workflows (feature development: plan → implement → test → grade →
iterate) are scripted in prose within command files, which becomes unwieldy
as feedback loops are added.

A dedicated **workflow plugin type** would address this. A workflow plugin
defines:

```yaml
# Example workflow definition (proposed format)
name: develop-feature
description: Full development cycle for a new feature
phases:
  - role: engineer
    command: plan
    output: plan-artifact
  - role: engineer
    command: implement
    input: plan-artifact
    output: code-artifact
  - role: tester
    command: test
    input: code-artifact
    output: test-results
  - role: grader
    command: grade
    input: [code-artifact, test-results]
    output: grade-report
  - condition: grade-report.verdict == "fail"
    loop_back_to: implement
    max_iterations: 3
  - role: debugger
    command: diagnose
    condition: test-results.failures > 0
    input: test-results
    output: debug-report
```

This separates the *what* (the workflow structure) from the *how* (the
individual agent implementations), enabling:
- Reuse of individual role agents across different workflows
- Formal loop and condition semantics (replacing prose scripting)
- Structured partial failure handling (the `condition` fields make failure
  paths explicit)

This would represent a significant architectural evolution — a new plugin
category alongside core, team, and system plugins.

### 9.7 Partial Failure Handling

The research on fault-tolerant multi-agent architectures identifies graceful
degradation as a first-class design requirement. Currently, claude-kit has no
formal partial failure model — if an agent in a command sequence fails, the
command fails.

**Practical patterns for claude-kit:**

**Checkpoint artifacts.** Each agent in a workflow writes its output to a named
artifact file before returning. If the workflow is restarted, it can detect
which artifacts already exist and skip those phases.

**Graceful degradation contracts.** Each agent role defines a minimum viable
output — the lowest-fidelity output that still allows the workflow to continue.
For the tester, for example: if the full test suite cannot run, at minimum
produce a syntax check result. The workflow can flag degraded output but continue.

**Bounded retry with escalation.** If an agent fails, retry up to N times
(configurable per role). After N failures, produce a structured failure artifact
and escalate to the debugger role rather than exiting the workflow.

**Explicit skip semantics.** Allow a workflow to continue without a role's
output if that role's contribution is optional for the specific task. Currently,
every agent spawn is implicitly required.

### 9.8 Observability for claude-kit

Given the OpenTelemetry GenAI standard's emergence, a concrete observability
model for claude-kit is feasible without building custom infrastructure.

**Minimum viable observability:**

Each agent spawn should produce a structured log entry covering:
- Agent role, command, and plugin version
- Input context length (tokens)
- Output artifact name and size
- Tool calls made and results
- Duration
- Success/failure and error message if failed

This log could be written to a session artifact file (e.g.,
`local/sessions/<timestamp>/trace.jsonl`) that the debugger agent can
query when diagnosing failures. This is a file-system-based trace — simpler
than full OpenTelemetry but providing the structured data needed for
trace-based root cause analysis.

**For the debugger role specifically:** The debugger should be prompted to
begin by reading the session trace file rather than relying on the user's
natural-language description of the failure. The structured trace gives the
debugger the same information a distributed tracing system would provide —
which agent failed, what it received, what it produced, and when.

---

## Summary

| Research finding | Implication for claude-kit |
|-----------------|---------------------------|
| 4-6 specialized agents is the optimal range | The 5-role model is correctly sized |
| Context partitioning is essential for critic independence | Grader must not share engineer's planning context |
| DoT risk limits review cycles to 2-3 | Grader-engineer feedback loops need a hard cap |
| Cascading failures require validation at handoffs | Structured handoff artifacts at every phase boundary |
| Knowledge plugins should support dynamic RAG as they grow | Hybrid static/dynamic knowledge architecture |
| Workflow complexity will outgrow command-file scripting | Workflow plugin type with formal loop/condition semantics |
| OpenTelemetry GenAI is the emerging standard | Session trace files for debugger role |
| Orchestration as a dedicated role improves complex workflows | Optional orchestrator agent for multi-phase workflows |
| Conformity bias degrades multi-agent quality | Diverse base prompts and rubric-based grading |

The 5-role team architecture of claude-kit is well-grounded in the multi-agent
LLM research literature. The most significant gaps are in coordination
formalism (commands as implicit orchestrators), inter-agent handoff structure
(prose-mediated context vs. structured artifacts), and observability (no
structured trace for debugger consumption). These are solvable within the
existing plugin architecture without fundamental redesign.

---

## Traces

- **Upstream:** Market signals, competitive analysis, user research
- **Downstream:** REQ-003 (Role Specialization)
- **Quality Attributes:** None identified

---

## Sources

**Multi-Agent Architecture and Frameworks:**
- [MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework (ICLR 2024)](https://arxiv.org/abs/2308.00352)
- [ChatDev: Communicative Agents for Software Development (ACL 2024)](https://arxiv.org/abs/2307.07924)
- [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation (Microsoft Research)](https://arxiv.org/abs/2308.08155)
- [AutoGen v0.4: Reimagining the foundation of agentic AI (Microsoft Research)](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/)
- [Semantic Kernel Multi-Agent Orchestration (Microsoft, 2025)](https://devblogs.microsoft.com/semantic-kernel/semantic-kernel-multi-agent-orchestration/)
- [Exploring Advanced LLM Multi-Agent Systems Based on Blackboard Architecture (2025)](https://arxiv.org/html/2507.01701v1)
- [LLM-based Multi-Agent Blackboard System (2025)](https://arxiv.org/pdf/2510.01285)
- [Four Design Patterns for Event-Driven, Multi-Agent Systems (Confluent)](https://www.confluent.io/blog/event-driven-multi-agent-systems/)

**Specialization and Code Generation:**
- [AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation](https://arxiv.org/abs/2312.13010)
- [MapCoder: Multi-Agent Code Generation for Competitive Problem Solving (ACL 2024)](https://arxiv.org/abs/2405.11403)
- [Code in Harmony: Evaluating Multi-Agent Frameworks (OpenReview)](https://openreview.net/pdf?id=URUMBfrHFy)

**LLM-as-a-Judge and Quality Gates:**
- [LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluation Methods (2024)](https://arxiv.org/html/2412.05579v2)
- [When AIs Judge AIs: The Rise of Agent-as-a-Judge Evaluation for LLMs (2025)](https://arxiv.org/html/2508.02994v1)
- [Leveraging LLMs as Meta-Judges: A Multi-Agent Framework (2025)](https://arxiv.org/html/2504.17087v1)
- [LLM-as-a-judge: a complete guide (Evidently AI)](https://www.evidentlyai.com/llm-guide/llm-as-a-judge)

**Multi-Agent Debate and Reflection:**
- [Improving Factuality and Reasoning in Language Models with Multiagent Debate (Du et al., 2023)](https://composable-models.github.io/llm_debate/)
- [Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate (EMNLP 2024)](https://aclanthology.org/2024.emnlp-main.992/)
- [Multi-LLM-Agents Debate - Performance, Efficiency, and Scaling Challenges (ICLR Blogposts 2025)](https://d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/)
- [SID: Multi-LLM Debate Driven by Self Signals (2025)](https://arxiv.org/html/2510.06843)

**Failure Modes:**
- [Why Do Multi-Agent LLM Systems Fail? MAST Taxonomy (Cemri et al., 2025)](https://arxiv.org/abs/2503.13657)
- [Risk Analysis Techniques for Governed LLM-based Multi-Agent Systems (Gradient Institute)](https://www.gradientinstitute.org/assets/gradient_multiagent_report.pdf)
- [Why Multi-Agent LLM Systems Fail and How to Fix Them (Augment Code)](https://www.augmentcode.com/guides/why-multi-agent-llm-systems-fail-and-how-to-fix-them)
- [Why Do Multi-Agent LLM Systems Fail? (Galileo)](https://galileo.ai/blog/multi-agent-llm-systems-fail)

**Observability:**
- [AI Agent Observability: Evolving Standards and Best Practices (OpenTelemetry, 2025)](https://opentelemetry.io/blog/2025/ai-agent-observability/)
- [An Introduction to Observability for LLM-based applications using OpenTelemetry (2024)](https://opentelemetry.io/blog/2024/llm-observability/)
- [AI Observability in Multi-Agent Systems Using OpenTelemetry (Cisco Outshift)](https://outshift.cisco.com/blog/ai-observability-multi-agent-systems-opentelemetry)
- [OpenTelemetry for GenAI and the OpenLLMetry project](https://horovits.medium.com/opentelemetry-for-genai-and-the-openllmetry-project-81b9cea6a771)

**RAG and Knowledge Architectures:**
- [Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG (2025)](https://arxiv.org/abs/2501.09136)
- [LLMs Get Lost In Multi-Turn Conversation (2025)](https://arxiv.org/pdf/2505.06120)
- [Context Engineering in LLM-Based Agents (Ruan, 2024)](https://jtanruan.medium.com/context-engineering-in-llm-based-agents-d670d6b439bc)

**Framework Comparisons:**
- [CrewAI vs LangGraph vs AutoGen: Choosing the Right Multi-Agent AI Framework (DataCamp)](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
- [The AI Agent Framework Landscape in 2025: What Changed and What Matters (Medium)](https://medium.com/@hieutrantrung.it/the-ai-agent-framework-landscape-in-2025-what-changed-and-what-matters-3cd9b07ef2c3)
- [Exploration of LLM Multi-Agent Application Implementation Based on LangGraph+CrewAI (arXiv 2411.18241)](https://arxiv.org/html/2411.18241)
