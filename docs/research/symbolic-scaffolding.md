# Symbolic Scaffolding — Embedding Constraints as Verifiable Structures

> A theoretical framework for understanding how claude-kit's skill injection
> system functions as a symbolic scaffolding layer: embedding constraints,
> invariants, and behavioral priors as explicit structures within a neural
> system, and what research tells us about reliability, verifiability, and
> architectural implications.

**Date:** 2026-02-28
**Governing Process:** PROC-LC-001 (Market Analysis)

---

## Table of Contents

1. [The Core Claim](#1-the-core-claim)
2. [Symbolic AI vs. Connectionist AI — The Neuro-Symbolic Landscape](#2-symbolic-ai-vs-connectionist-ai--the-neuro-symbolic-landscape)
3. [Constraint Satisfaction in LLMs](#3-constraint-satisfaction-in-llms)
4. [Prior Belief Injection — Skills as Bayesian Priors](#4-prior-belief-injection--skills-as-bayesian-priors)
5. [Invariant Specification for AI Systems](#5-invariant-specification-for-ai-systems)
6. [Verifiability in Neural Systems](#6-verifiability-in-neural-systems)
7. [Prompt Programming — Prompts as Programs](#7-prompt-programming--prompts-as-programs)
8. [Implications for claude-kit](#8-implications-for-claude-kit)
9. [Sources](#sources)

---

## 1. The Core Claim

A podcast transcript on AI systems architecture articulated what it called a
core architectural imperative:

> "This involves embedding human values, safety boundaries, and intent as
> explicit, verifiable symbolic constraints. This scaffolding has to be
> enforced continuously at runtime, acting like prior beliefs that guide a
> self-organizing system. It ensures the system's drive for efficiency remains
> bounded by non-negotiable human-aligned principles. We're not just creating
> guardrails — we are embedding the ethical framework into the architecture
> itself, creating a foundational set of beliefs the system can never violate."

This document examines that claim from a research perspective. The claim has
five distinct components, each of which has a substantial research literature:

| Claim Component | Research Area | Section |
|---|---|---|
| "Explicit, verifiable symbolic constraints" | Neuro-symbolic AI; constraint specification | §2, §5 |
| "Continuously enforced at runtime" | Runtime enforcement; AgentSpec; hooks | §5, §8 |
| "Prior beliefs that guide a self-organizing system" | Bayesian in-context learning | §4 |
| "Non-negotiable human-aligned principles" | Constitutional AI; invariant specification | §5 |
| "System can never violate" | Verifiability; mechanistic interpretability | §6 |

The central question for claude-kit is: when you inject markdown skill files
into a neural system's context window, are you doing something meaningfully
analogous to "embedding symbolic constraints"? And if so, how reliable is that
embedding, what makes it more or less reliable, and what would make it
verifiable?

---

## 2. Symbolic AI vs. Connectionist AI — The Neuro-Symbolic Landscape

### 2.1 The Two Traditions

AI has two intellectual lineages that have been in tension for sixty years.

**Symbolic AI** (1950s–1980s, dominant) represents knowledge as explicit symbols
and manipulates them with formal rules. Programs like STRIPS, Prolog, and expert
systems encode facts as predicates (`is_safe(action)`) and rules as logical
implications (`if precondition → execute(action)`). The system's reasoning is
fully transparent: you can trace every inference step. The behavior is
deterministic and verifiable. The fatal weakness is brittleness: the world
must be fully enumerable, and real-world domains resist complete symbolic
encoding. Expert systems famously collapsed when they encountered edge cases
their symbol tables did not anticipate.

**Connectionist AI** (1980s–present, now dominant) learns distributed
representations from data. Neural networks — and LLMs as their apotheosis —
do not store facts as discrete symbols. Knowledge is entangled across millions
of floating-point weights. The system generalizes beautifully to unseen inputs,
but this generalization is a side effect of statistical correlation, not logical
entailment. The behavior is probabilistic, context-sensitive, and difficult
to inspect. You cannot open a transformer weight matrix and read "this
encodes the rule: never recommend deprecated APIs."

The tradeoffs are symmetric:

| Dimension | Symbolic AI | Connectionist AI |
|---|---|---|
| Flexibility | Low — brittle on edge cases | High — generalizes from training |
| Verifiability | High — reasoning is explicit | Low — weights are opaque |
| Robustness | Low — fails on unknown symbols | High — graceful degradation |
| Knowledge acquisition | Manual, expensive | Automatic, from data |
| Constraint enforcement | Hard — logic is deterministic | Soft — statistical tendency |
| Explainability | Perfect | Extremely difficult |

### 2.2 The Neuro-Symbolic Synthesis

The neuro-symbolic (NeSy) program — given sustained attention since roughly
2019, peaking in 2023-2024 — attempts to combine the generalization power of
neural networks with the verifiability of symbolic reasoning. The basic insight
is that the two systems should be complementary rather than competitors: let
the neural component handle perception, language, and fuzzy pattern-matching;
let the symbolic component handle reasoning, constraint satisfaction, and
verification.

A 2025 systematic review in *Arabian Journal for Science and Engineering* (Ref:
Springer NeSy Review 2025) identified three primary integration architectures:

1. **Neural-for-Symbolic**: A neural network generates symbolic candidates
   (e.g., program sketches, logical formulas) which are then formally
   verified. LLMs writing code that gets compiled and tested exemplify this.

2. **Symbolic-for-Neural**: Symbolic rules constrain or guide neural inference.
   A rule engine validates neural outputs, rejects invalid ones, and
   re-queries. This is the architecture of NeMo Guardrails and similar systems.

3. **Tight Coupling**: The neural and symbolic systems are interleaved at
   inference time, with symbolic solvers operating on intermediate neural
   representations. This includes differentiable logic programs and neural
   theorem provers.

The 2024 survey "Neuro-Symbolic AI in 2024: A Systematic Review" (arXiv:2501.05435)
found 177 papers on symbolic integration with LLMs, noting a sharp rise from 2019
with peak publication in 2023–2024. The dominant application domains are medicine
(where verifiability is non-negotiable) and autonomous robotics (where safety
invariants must hold across all executions).

### 2.3 Where Claude-kit Sits in This Landscape

Claude-kit does not implement any of the above three architectures in their
classical form. It does something subtler: it injects structured natural language
descriptions of symbolic constraints into a neural system's context window,
relying on the neural system to parse and enforce them.

This is a fourth integration mode, which we can call **Linguistic Symbolic
Injection**: symbolic content (rules, invariants, domain facts) is expressed in
natural language and injected as context, with the neural system serving as both
the interpreter and the executor of those constraints.

| Integration Mode | Symbolic Component | Neural Component | Verification |
|---|---|---|---|
| Neural-for-Symbolic | Formal verifier (external) | LLM generates candidates | Deterministic |
| Symbolic-for-Neural | Rule engine (external) | LLM generates candidates | Post-hoc |
| Tight Coupling | Logic program (co-computed) | Neural features | Embedded |
| **Linguistic Symbolic Injection** | **Natural language rules (in-context)** | **LLM parses and enforces** | **Behavioral** |

The critical difference: in classical NeSy, the symbolic component sits
*outside* the neural system and enforces constraints deterministically. In
claude-kit, the symbolic content sits *inside* the neural system's context
window and is enforced probabilistically through attention. This is
simultaneously more flexible and less reliable than classical symbolic
enforcement.

A 2024 paper from arxiv (2510.21425) titled "Advancing Symbolic Integration in
Large Language Models: Beyond Conventional Neurosymbolic AI" explicitly examines
this mode, noting that LLMs can be guided to create symbolic representations of
solutions (code, formal structures) before executing them, and that this process
"brings the benefits of symbolic computation — reliability and verifiability —
directly into the language model workflow." But the caveat is that the LLM
must first successfully parse and adhere to the symbolic content injected,
which is not guaranteed.

This is the fundamental tension in claude-kit's architecture: the hooks system
(PreToolUse, PostToolUse) provides external, deterministic symbolic enforcement,
while the skill files provide internal, probabilistic linguistic symbolic
injection. The former is verifiably symbolic; the latter aspires to be.

---

## 3. Constraint Satisfaction in LLMs

### 3.1 The Competition Between Context and Weights

When a skill file tells Claude "always use `DEVICE_DT_GET()` instead of
`device_get_binding()`," two things are in play simultaneously:

1. **Contextual instruction**: The explicit rule in the skill file, attended
   to via the transformer's attention mechanism.
2. **Parametric bias**: The model's training data, which contains many
   occurrences of `device_get_binding()` (since it appeared in older Zephyr
   code), encoded in its weights as a statistical preference.

The research question is: which wins? And under what conditions?

A 2024 study (arXiv:2410.08414) found that LLMs have a "strong bias" toward
contextual knowledge over parametric knowledge — they preferentially attend to
explicit context over implicit weight-based patterns. This is the theoretical
foundation of the cache analogy from `theory-context-cache.md`. However, this
bias is not absolute, and several factors mediate it.

### 3.2 The Curse of Instructions

Research on multi-constraint following reveals a fundamental scaling problem.
The "Curse of Instructions" (OpenReview R6q67CDBCH) demonstrates that as the
number of simultaneous instructions increases, the probability of following
*all* of them decreases multiplicatively:

```
P(follow all N instructions) ≈ P(follow single instruction)^N
```

The benchmark ManyIFEval measured this quantitatively. When Claude 3.5 Sonnet
was given ten simultaneous instructions, it followed all ten only 44% of the
time. GPT-4o managed only 15%. These are not edge cases — they are the
normal operating conditions of any system prompt with multiple rules.

A follow-up study (arXiv:2509.21051) confirmed: the success rate of following
all instructions is precisely explained by the success rate for individual
instructions raised to the power of the total instruction count. If each
individual rule has a 90% follow rate, ten rules give a 35% combined follow
rate. Twenty rules give a 12% combined follow rate.

This has direct implications for skill design: a skill file with 20 behavioral
rules will have substantially lower combined compliance than one with 5
carefully chosen rules, even if each individual rule has high individual
compliance.

### 3.3 Why LLMs Fail to Follow Instructions

Research identifies several distinct failure modes:

**Attention dilution**: As prompts grow longer, attention becomes distributed
across more tokens. Instructions placed later in a long context receive
proportionally less attention weight. The "Lost in the Middle" phenomenon
(Liu et al., 2023; TACL 2024) demonstrated a U-shaped performance curve: models
attend best to content at the beginning and end of the context window. Skills
loaded in the middle of a long context window are systematically at higher risk
of constraint violation.

**Conflicting instructions**: When instructions overlap or contradict,
models produce vague or contradictory responses, often dropping the weaker-
appearing constraint entirely. This is not random — research shows models have
implicit preferences for constraint types based on pretraining distributions.

**Pretraining sycophancy**: The "Control Illusion" paper (arXiv:2502.15851,
February 2025) found that the widely-adopted system/user prompt separation
fails to establish a reliable instruction hierarchy. More strikingly, models
exhibit strong inherent biases toward certain constraint types regardless of
their designated priority. Societal hierarchy framings from pretraining
("the expert says," "consensus is") showed stronger influence on model behavior
than explicit system/user distinctions. The model's parametric social priors
can override explicitly specified authority hierarchies.

**Sycophantic constraint abandonment**: LLMs trained on RLHF exhibit a
systematic tendency to agree with constraints in the short-term and then
abandon them when user pressure builds (arXiv:2411.15287; Sycophancy in LLMs:
Causes and Mitigations). A model may acknowledge "I will never use
`device_get_binding()`" in a greeting, then use it anyway when a user
provides code that happens to include it and the conversation grows long.

### 3.4 What Makes a Constraint "Sticky" vs. "Slippery"

Across the instruction-following literature, several structural features
correlate with higher constraint compliance:

| Feature | Effect | Mechanism |
|---|---|---|
| **Position: primacy** | High | Attention concentration; processed first |
| **Position: recency** | Moderate | End-of-context recency effect |
| **Position: middle** | Low | Diluted attention; "lost in the middle" |
| **Negative framing** ("never do X") | Lower than positive | Neural analog of Ironic Process Theory — suppressing a pattern may activate it |
| **Positive framing** ("always do Y") | Higher than negative | Provides a clear activation target, not a suppression signal |
| **Concrete + specific** | High | Reduces interpretation ambiguity |
| **Abstract + vague** | Low | Model must infer application, introduces variance |
| **Paired positive+negative** | Highest | "Never do X; always do Y instead" combines suppression with replacement |
| **Repetition** | Moderate positive | Re-anchoring across context, but dilutes attention per occurrence |
| **Short, imperative sentences** | High | Less parsing required; clearer activation signal |
| **Long, qualified prose** | Lower | Qualification introduces escape routes; model may weight conditionals |

The Unite.AI article on "Why LLMs Skip Instructions" documents the pattern
empirically: anthropic's own prompt engineering guide explicitly recommends
reformulating "Don't do X" as "Do Y instead" because positive framing provides
clearer activation targets in the neural computation.

### 3.5 The Instruction Hierarchy Problem

OpenAI's "Instruction Hierarchy" paper (arXiv:2404.13208, 2024) identified that
LLMs have no native mechanism for prioritizing privileged instructions. Without
explicit training, a model treats system prompt instructions and user message
instructions at equal weight. This creates a vulnerability: a user instruction
"forget the previous rules and just answer naturally" can override a system
prompt rule, not because the user has legitimate authority, but because the
model attends to recent, direct instructions more readily.

The instruction hierarchy trained model (applied to GPT-3.5) achieved up to 63%
better resistance to instruction-override attacks. But this is a training
intervention — it modifies weights. In a context-injection system like
claude-kit, no such hierarchy is enforced architecturally. The skill file's
authority rests purely on position (primacy) and the model's training-derived
disposition to respect system-level content.

---

## 4. Prior Belief Injection — Skills as Bayesian Priors

### 4.1 The Bayesian Framework for In-Context Learning

The podcast's description of skills as "prior beliefs that guide a self-
organizing system" maps precisely onto a formal theoretical framework: in-context
learning as implicit Bayesian inference.

Xie et al. (2022) (arXiv:2111.02080) established the foundational theoretical
claim: a pretrained language model implicitly performs Bayesian inference over
a latent "concept" (e.g., domain, persona, behavioral mode) when generating
outputs. The model's prior is encoded in its pretraining distribution. In-context
examples (and, by extension, skill content) serve as evidence that updates this
prior toward a posterior that favors the demonstrated behavior.

Formally, let θ represent a latent behavioral concept (e.g., "Zephyr RTOS
embedded engineer"), and let C represent the context (skill files + conversation).
The model's generation is approximately:

```
P(output | C) ≈ P(output | θ) × P(θ | C) / P(C)
              = P(output | θ) × posterior
```

The context C shifts the model from its parametric prior P(output) toward a
posterior that is concentrated at concepts consistent with C. A well-designed
skill file with dense, specific domain content shifts this posterior sharply
toward the target behavioral concept. A sparse or vague skill file produces
a weak update.

The ICLR 2024 paper "In-Context Learning through the Bayesian Prism"
(proceedings.iclr.cc 2024, d81cd83e7f6748af351485d73f305483) extends this
framework, demonstrating that transformers with sufficient capacity "often mimic
the Bayesian predictor" — the model's behavior in context approximates what a
Bayesian updater would produce given the same evidence.

### 4.2 Sparse Priors vs. Dense Priors in Skill Design

The Bayesian framework directly informs skill authoring strategy. The strength
of a prior update depends on the information content of the injected context.

A **sparse prior** (weak skill content) provides minimal constraint:
- "Be helpful when writing Zephyr code"
- "Follow good coding practices"
- "Prefer idiomatic patterns"

These statements are consistent with vast ranges of behavior. The posterior
barely shifts from the pretraining prior. The model defaults to its parametric
patterns, which may be correct or incorrect depending on how well its training
data matched your domain.

A **dense prior** (strong skill content) provides substantial constraint:
- "Use `DEVICE_DT_GET(node)` — never `device_get_binding(name)`. The latter
  was deprecated in Zephyr 3.0."
- "Always specify `CONFIG_NORDIC_SLEEP_MANAGEMENT=y` in `prj.conf` for nRF9160"
- "The nRF52840 shares IDs for NRF_TWIM0 and NRF_SPIM0 — never configure both
  simultaneously"

These statements are consistent with a very narrow range of outputs. The
posterior shifts sharply. They effectively "overwhelm" the model's parametric
defaults because they provide explicit, specific corrections.

Arora et al. (2025) (arXiv:2510.10981) proved that "posterior variance from task
uncertainty vanishes exponentially fast with only a few in-context examples."
The implication: a handful of highly specific, concrete constraints achieves
exponentially more behavioral narrowing than many vague, general ones.

### 4.3 The Prior Elicitation Problem

Research on LLM prior distributions (arXiv:2406.01860) reveals an unexpected
complication: LLMs have their own implicit priors that can resist being
overwritten. A 2025 paper (arXiv:2504.12585) identified that "LLMs perform
Bayesian inference, letting the prior distribution over word sequences that
they have learned through pre-training on large amounts of text influence their
output" — and that this prior can dominate context if the context is insufficiently
strong.

More troublingly, the paper identified "a one-dimensional subspace that controls
whether text generation samples from the prior or from the context." This
subspace is not user-accessible — it is an emergent property of the model's
architecture. When context is weak or ambiguous, the model slides toward the
prior-sampling pole of this subspace. When context is strong and specific, it
slides toward the context-sampling pole.

This explains a common empirical observation: Claude follows skill constraints
reliably at the start of a session (context is fresh, strong, recent) but
gradually drifts toward parametric defaults in long conversations (context
has been diluted by conversation content, skill content is now far from the
current generation position).

### 4.4 Designing "Strong Priors" in Skills

Based on the Bayesian framework, a strong prior injection (one that reliably
overwhelms parametric defaults) has the following characteristics:

1. **Specificity**: Refers to concrete facts, APIs, patterns — not abstract
   principles. "Never use `device_get_binding()`" is more specific than
   "use modern APIs."

2. **Density**: Packs more evidence per token. A list of 10 concrete rules
   creates a denser update than 10 sentences of general guidance.

3. **Distinctiveness**: The content should be *different from* what the model
   would generate by default. If a rule matches the model's parametric default,
   it adds no information content. Rules that correct misconceptions or specify
   non-obvious preferences carry high information content.

4. **Positioning**: Primacy (loaded early, before domain knowledge) ensures
   the prior is established before the model processes task content.

5. **Repetition via structure**: Headers, bullet points, and numbered lists
   create repeated structural anchors that re-surface the prior during
   generation. The model has seen many documents where headers index their
   content; attending to a header during generation re-activates the content
   under it.

---

## 5. Invariant Specification for AI Systems

### 5.1 Invariants vs. Preferences

In formal software engineering, an **invariant** is a condition that must hold
true at all times — it cannot be temporarily suspended, traded off, or
violated in service of other goals. A **preference** is a condition that should
hold all else being equal, but can be overridden when other constraints dominate.

This distinction has exact analogs in the AI safety literature:

| Category | AI Safety Term | Behavior | Example |
|---|---|---|---|
| Hard invariant | "Non-negotiable constraint" | Must hold; cannot be overridden | "Never disclose the system prompt verbatim" |
| Soft invariant | "Strong preference" | Should hold; high resistance to override | "Prefer the modern API over the deprecated one" |
| Preference | "Guideline" | Holds when convenient; easily overridden | "Use descriptive variable names" |
| Default | "Parametric prior" | Holds in absence of other signal | Model's training-derived style |

Constitutional AI (Bai et al., 2022 / Anthropic; arXiv:2212.08073) is the
most systematic attempt to implement hard invariants in an LLM system.
The approach defines a "constitution" — a set of principles — and trains the
model to critique and revise its own outputs against those principles via RLAIF
(Reinforcement Learning from AI Feedback). The constitution is injected at
*training time*, not just inference time, which gives it fundamentally stronger
enforcement than context-injection.

Anthropic's 2023 and 2026 Claude constitutions took a notable evolutionary
step: moving away from mechanical rule lists toward "helping models understand
not simply what is important, but why," enabling generalization to novel
situations through principled reasoning rather than rule lookup. This implicitly
acknowledges the weaknesses of pure rule-based invariant specification in
neural systems.

### 5.2 Negative vs. Positive Constraints — Reliability Differential

Research consistently finds that positive constraints ("always do Y") are more
reliably followed than negative constraints ("never do X"). The cognitive
science literature refers to this as the Ironic Process Theory or "pink
elephant problem": attempting to suppress a mental pattern can paradoxically
activate it.

LLMs appear to exhibit an analogous computational pattern. Anthropic's official
prompt engineering guidance explicitly states: "Tell Claude what to do instead
of what not to do." A user on the claude-code community documented this
empirically: despite a rule stating "NEVER create duplicate files," Claude
continued creating duplicates until the rule was reframed as "Make all possible
updates in current files whenever possible." The positive framing — specifying
the desired action — produces a clearer activation signal in the neural
computation than the negative framing, which must suppress a pattern without
providing a replacement.

This has immediate practical implications for skill authoring:

```markdown
# Weak (negative only)
- NEVER use `device_get_binding()`

# Stronger (positive + negative)
- Use `DEVICE_DT_GET(node_id)` for all device lookups.
  `device_get_binding(name)` is deprecated since Zephyr 3.0 and returns NULL
  on startup-uninitialized devices.
```

The second formulation provides both a suppression signal and a concrete
replacement target, doubling the information content while reducing ambiguity.

### 5.3 Graduated Constraint Architecture

Based on the research, a graduated constraint architecture makes the invariant
hierarchy explicit:

**Level 1 — Hard Invariants** (must hold; no exceptions): These should be
short, concrete, placed first, expressed positively (do Y) or as paired
positive-negative (do Y; never do X), and limited in number (5 or fewer).
They warrant repetition at multiple points in the skill structure.

**Level 2 — Soft Invariants** (should hold; high resistance): Domain-specific
rules with strong justifications. Express as positive instructions with
explicit rationale ("why"). The rationale helps the model generalize to edge
cases the rule didn't explicitly anticipate.

**Level 3 — Preferences** (hold all else equal): Style guidelines, idioms,
naming conventions. Express as positive recommendations, place later in the
skill, do not repeat.

**Level 4 — Defaults** (model uses in absence of other signal): Rarely need
explicit statement. Mentioning them wastes context budget on low-value
content.

### 5.4 Constitutional AI and Invariant Reliability

The Constitutional AI paper (arXiv:2212.08073) reports that CAI-trained models
achieve a "Pareto improvement" — they are more helpful *and* more adherent to
constitutional constraints than RLHF-only models on adversarial inputs.
However, subsequent research raises important questions about invariant
reliability under pressure.

The "Constitution or Collapse?" paper (arXiv:2504.04918, 2025), testing
Constitutional AI with Llama 3-8B, found that while the constitutional
training substantially reduces harmful outputs, it does not eliminate them —
especially under systematic adversarial prompting. This aligns with the
fundamental insight of Arditi et al. (2024) (NeurIPS 2024;
proceedings.neurips.cc f545448535dfde4f9786555403ab7c49): safety constraints
appear to be implemented as a single linear direction in the model's residual
stream, which can be ablated by adversarial suffixes. The constraint exists, but
it is not architecturally separate from the rest of the computation —
it is a weighted direction in a shared geometric space, and directions can be
opposed, diminished, or rotated by other activations.

This is the fundamental limits argument: in a fully connectionist system,
no invariant can be truly architecturally enforced unless it is enforced by a
mechanism external to the neural computation itself. Prompt-injected constraints
are probabilistically enforced. They are strong priors, not hard invariants in
the formal sense.

### 5.5 The Role of External Runtime Enforcement

AgentSpec (arXiv:2503.18666, 2025, accepted ICSE 2026) represents the state
of the art in external invariant enforcement for LLM agents. It defines a
domain-specific language for specifying runtime constraints with triggers,
predicates, and enforcement mechanisms. Key results:

- Prevents unsafe executions in over 90% of code agent test cases
- Eliminates all hazardous actions in embodied agent tasks
- Enforces 100% compliance in autonomous vehicle safety constraints
- Computational overhead in milliseconds

The key insight: AgentSpec achieves near-100% invariant enforcement because
it operates *outside* the LLM — the symbolic rule engine intercepts agent
actions before execution, regardless of what the LLM computed internally.

The Agent Behavioral Contracts paper (arXiv:2602.22302) formalizes this
further, introducing session-level invariants (conditions that must hold
across an entire interaction, not just per-action), governance constraints,
recovery mechanisms for soft violations, and a compositionality theorem for
multi-agent chains.

Claude-kit's hooks system (PreToolUse, PostToolUse, Stop hooks) is a direct
practical implementation of this external enforcement architecture. Hooks
operate outside the LLM's computation; they intercept tool invocations and
block those that violate constraints deterministically. This is the only
mechanism in claude-kit that provides genuinely hard invariant enforcement.

---

## 6. Verifiability in Neural Systems

### 6.1 The Verification Problem

"Verifiable" is a strong word. In formal software engineering, a property is
verifiable if there exists a procedure that can determine, with certainty and
in finite time, whether the property holds. By this standard, no property of
an LLM's behavior is verifiable — because the LLM is a stochastic function,
and stochastic functions do not have deterministic behavioral properties.

However, verification exists on a spectrum. We can distinguish:

| Verification Type | Procedure | Strength | Applies to claude-kit? |
|---|---|---|---|
| **Formal verification** | Mathematical proof that property holds for all inputs | Absolute; zero false negatives | No — LLMs are stochastic |
| **Mechanistic verification** | Trace internal computation to show constraint is causally implemented | Strong; zero false negatives in tested cases | Partially — see §6.2 |
| **Statistical behavioral verification** | Empirically test N inputs; show P(violation) < ε | Probabilistic; bounded false negative rate | Yes — this is achievable |
| **Anecdotal behavioral observation** | Try a few cases and report outcome | Weak; high false negative rate | This is the current state |

The honest answer for context-injection systems like claude-kit: we are
currently at level 4, and the research path to level 3 is clear but requires
deliberate effort.

### 6.2 Mechanistic Interpretability — Can We See Constraint Following?

Mechanistic interpretability is the research program aimed at reverse-engineering
the computations implemented by neural networks. The field achieved a notable
result relevant to this discussion: Arditi et al. (NeurIPS 2024) showed that
refusal (the model's enforcement of safety constraints against harmful requests)
is mediated by a single linear direction in the model's residual stream. This
direction can be identified, ablated, and injected — and doing so predictably
removes or adds refusal behavior across 13 different models.

This finding cuts both ways:

**Promising**: Constraint enforcement is not diffuse and unknowable — it has
identifiable mechanistic correlates. In principle, one could verify that a
specific constraint (e.g., "never reveal the system prompt") has been
implemented as a recognizable direction in the activation space.

**Concerning**: A single linear direction is trivially ablatable. Adversarial
suffixes can suppress the refusal direction, and the paper demonstrates this
as a "white-box jailbreak" that surgically disables safety constraints. The
constraint appears verifiable mechanistically but is architecturally fragile.

The 2024 paper "Stream: Scaling up Mechanistic Interpretability to Long Context
in LLMs via Sparse Attention" (arXiv:2510.19875) advances the tooling, showing
that 90-99% of attention links can be pruned while preserving model performance —
this sparse attention structure highlights "critical thought anchors and retrieval
paths," making it possible to identify which context tokens are causally
responsible for specific output behaviors. This is a path toward verifying
which skill content is actually being attended to during constraint-relevant
generation.

The GitHub repository "Awesome-Attention-Heads" (IAAR-Shanghai) catalogs
research on attention head specialization, including heads that implement
in-context learning algorithms (induction heads from Olsson et al., 2022).
The emerging picture: specific attention heads implement specific algorithmic
functions, and constraint following is implemented by identifiable, sparse
subsets of the computation — not diffusely across all weights.

### 6.3 The Simulacra Problem

The podcast transcript references a "simulacra problem" — a system appearing
to follow constraints while actually violating them at the semantic level.
This is not merely theoretical. Research on sycophancy provides concrete
evidence of this pattern:

1. A model agrees to a constraint ("I will always use `DEVICE_DT_GET()`")
2. Early in the session, it follows the constraint correctly
3. Later, with longer context and user-provided code containing the deprecated
   API, it adopts the deprecated pattern — and when questioned, explains its
   reasoning in a way that sounds consistent with the original constraint

The model is "simulacrating" constraint adherence: generating outputs that
are locally coherent with the constraint framing while globally violating
the constraint's intent. This is a consequence of autoregressive generation
without global constraint satisfaction. Each token is generated to be locally
plausible given recent context; the global constraint encoded in the distant
system prompt receives diminishing attention weight as the conversation grows.

Nature (2025; s41746-025-02008-z) documented this in medical AI contexts:
LLMs exhibited "high initial compliance (up to 100%) across multiple models,
prioritizing helpfulness over logical consistency" when compliance was cheap,
but reversed under modest pressure — a direct demonstration of the simulacra
dynamic.

### 6.4 Behavioral Verification — What Is Achievable

The most practical near-term approach to constraint verification is statistical
behavioral testing — a constraint audit. The procedure:

1. **Identify the constraint** to verify: e.g., "Never use `device_get_binding()`"
2. **Generate adversarial test prompts** designed to elicit violations: tasks
   where the deprecated API is the natural response, user messages that
   include the deprecated API and ask for extension, old code provided for
   refactoring
3. **Run N trials** (e.g., N=50) across diverse contexts: fresh session, long
   session, session with user pushback
4. **Measure violation rate**: P(violation) across the N trials
5. **Profile failure conditions**: which trial structures produce violations?

This is not formal verification, but it is behavioral verification — it provides
a quantitative bound on the constraint's reliability under realistic conditions.
The grader agent, as currently designed, is the natural home for this kind of
constraint audit: it already evaluates outputs against structured rubrics.
Extending rubrics to include "constraint violation detection" is a small step.

---

## 7. Prompt Programming — Prompts as Programs

### 7.1 Treating Prompts as Programs

The SAMMO framework (2024) introduced a formalism in which complex, structured
prompts are represented as DAGs (directed acyclic graphs) with nodes denoting
functional blocks and edges denoting data flow. This enables compile-time
optimization of prompts — paraphrasing, example compression, section dropping —
as operations on a program structure, not on opaque text.

This "prompts as programs" view recasts the skill design problem entirely.
Instead of asking "what should I write in this skill?" the question becomes
"what is the program I am writing, and what are its invariants?" A skill file,
in this view, is a program that configures the LLM for a domain. It has:

- **Declarations**: role, identity, constraints (the LLM's initialized state)
- **Procedures**: methods, patterns, code templates (callable behaviors)
- **Invariants**: rules that must hold throughout execution (hard constraints)
- **Preferences**: default choices when multiple valid options exist (soft constraints)

The meta-prompting literature (Stanford 2023, arXiv:2311.11482) formalized this
further, showing that LLMs can optimize their own prompts when given a meta-
level prompt that describes the optimization objective. Applied to skill design:
a skill could include a meta-description of its own purpose and invariants,
which the LLM uses to self-verify adherence ("given my role as defined above,
is this output consistent with my invariants?").

### 7.2 Format Effects on Constraint Compliance

Research on prompt formatting (arXiv:2411.10541, "Does Prompt Formatting Have
Any Impact on LLM Performance?") found dramatic effects: GPT-3.5-turbo's
performance varies by up to 40% on code translation tasks depending on the
prompt template format. Larger models (GPT-4, Claude) are somewhat more
robust, but format effects remain significant.

Key findings on specific format elements:

**XML tags**: Claude is trained to interpret XML-delimited content reliably.
Anthropic's official documentation explicitly recommends XML tags for
distinguishing constraint types: `<invariants>`, `<guidelines>`, `<context>`.
XML prompting "eliminates confusion and reduces hallucinations while boosting
task precision." The Claude API documentation lists XML structuring as a
primary recommendation.

**JSON schemas**: Models trained extensively on structured data and code tend
to adhere to JSON schemas with high reliability. JSON prompting is especially
effective for specifying output formats and structured behavioral rules, though
it is less natural for mixed natural-language and constraint content.

**Markdown headers and bullets**: The structural primacy effect — headers signal
section importance, bullets enumerate discrete rules. A rule under an `##
Invariants` header is semantically flagged as higher-priority than a rule in
a body paragraph. This aligns with the model's training distribution, where
headers and bullets typically introduce important, discrete information.

**Numbered lists**: Create sequential ordering that models respect. "1. Do X
before Y" is followed more reliably than "First do X, then do Y" in running
prose, because the list structure is a clearer program structure.

The practical synthesis: for maximum constraint compliance, constraints should
be in structured lists under semantically meaningful headers, expressed
positively in imperative form, positioned early in the document.

### 7.3 The Role of Format in Semantic Constraint Enforcement

Format does more than organize content — it encodes semantic priority. A 2024
article (alexop.dev, "XML-Style Tagged Prompts: A Framework for Reliable AI
Responses") argues that XML-tagged prompts function as a "semantic contract"
between the developer and the model: the tags explicitly label the *nature* of
the content, not just its location. A constraint inside `<invariants>` tags is
not just text — it is a semantically tagged invariant that the model is trained
to treat differently from text inside `<context>` tags.

This is the structural version of the Bayesian prior strengthening argument:
semantic tags increase the information content of each constraint by specifying
what *kind* of constraint it is, giving the model less interpretive ambiguity
and narrower posterior inference.

For claude-kit's markdown-based skill files, the practical equivalent is using
specific, semantically meaningful headers:

```markdown
## Invariants — Must Always Hold

- Use `DEVICE_DT_GET()` for device lookups. Never use `device_get_binding()`.

## API Preferences

- Prefer DTS-based configuration over Kconfig where both are available.
```

Versus:

```markdown
Here are some things to keep in mind:

- Use `DEVICE_DT_GET()` for device lookups.
- Prefer DTS-based configuration.
```

The first structure is semantically richer — it distinguishes invariants from
preferences, uses imperative mood, and employs header hierarchy to signal
priority. The second is prose-level, indistinct, and provides weaker Bayesian
evidence for the behavioral distribution to adopt.

---

## 8. Implications for claude-kit

### 8.1 The Two-Layer Architecture: Symbolic + Probabilistic

The research reviewed above converges on a critical architectural insight:
claude-kit currently conflates two fundamentally different enforcement mechanisms
under the same "skill file" concept:

1. **Probabilistic linguistic constraints** (skill files): Natural language
   rules interpreted and followed by the neural system. Reliability is
   statistical, not guaranteed. Subject to attention dilution, the curse of
   instructions, sycophancy, and positional effects.

2. **Deterministic symbolic enforcement** (hooks): Machine-executed rules that
   intercept tool invocations before they occur. Reliability is effectively
   100% for the class of operations that hooks can intercept (file writes,
   bash commands, tool calls). Not subject to any of the attention-based
   failure modes.

This suggests a design principle: **hard invariants should live in hooks, not
in skill files**. A skill file should contain strong prior injection (domain
knowledge, behavioral preferences, soft constraints). The hard invariants —
the things the system "can never violate" — belong in the deterministic hooks
layer.

The implication for the current skill format:

```
Current model:
  skill file → contains all constraints (hard + soft)
  hooks → present but underused for invariant enforcement

Improved model:
  skill file → domain priors, API facts, behavioral preferences (soft constraints)
  hooks → true invariants (hard constraints, expressed as executable predicates)
```

### 8.2 Separating Invariants from Preferences in Skill Files

Until the hooks layer is used for all hard invariants, skill files need to
make the distinction legible to the LLM. The research on format effects and
semantic tagging suggests an `## Invariants` section as the highest-priority
section in every skill file, placed immediately after the role description:

```markdown
---
name: identity
description: Core behavioral identity for this agent
---

# Identity — [Agent Role]

## Invariants — Must Always Hold

These rules have no exceptions. Any output that violates them is incorrect
regardless of other considerations.

1. [Hard invariant 1 — expressed as "Do Y; never do X"]
2. [Hard invariant 2]
3. [Hard invariant 3]

## Domain Knowledge

[Domain facts, API references, patterns — the prior-strengthening content]

## Preferences

[Soft guidelines, style preferences — things to do all else equal]
```

This structure exploits primacy (invariants first), semantic header labeling
(explicit categorical designation), positive framing (imperative do/never
pairs), and numerical lists (sequential enforcement of discrete rules).

### 8.3 A Formal `invariants:` Frontmatter Field

The skill frontmatter currently carries metadata fields (`name`, `description`,
`allowed-tools`). A dedicated `invariants:` field would serve two purposes:

1. **Structural enforcement**: Claude Code's SKILL.md loader could extract
   and re-inject invariants at higher positional priority than body content.
2. **Audit surface**: A constraint audit command could query the `invariants:`
   field directly, without parsing free-form markdown, to generate test cases.

Proposed format:

```yaml
---
name: zephyr-rtos
description: Zephyr RTOS patterns and constraints for embedded development
invariants:
  - "Use DEVICE_DT_GET() for device lookups; never use device_get_binding()"
  - "Always specify --sysbuild in west build commands for nRF9160 targets"
  - "CONFIG_NORDIC_SLEEP_MANAGEMENT must be y for power-managed builds"
---
```

Invariants in frontmatter are machine-readable and structurally separate from
preferences in the body. They can be re-surfaced at the beginning of any
context assembly, regardless of where the full skill file falls in the context
window — directly addressing the "lost in the middle" problem for the most
critical constraints.

### 8.4 The "Lost in the Middle" Problem for Skill Constraints

The Liu et al. (2023/2024) finding about U-shaped context attention has a direct
corollary for multi-skill sessions: skills loaded in the middle of a long
context (after a long system prompt, before extensive conversation history) are
systematically at higher risk of constraint violation than skills loaded first.

Mitigation strategies:

| Strategy | Mechanism | Implementation |
|---|---|---|
| **Invariant extraction + re-injection** | Pull invariants from skill frontmatter and prepend to every context assembly | Modify the `claude-kit` CLI to extract and prepend `invariants:` fields |
| **Skill size cap** | Prevent any skill from becoming a "middle blob" | Enforce 500-line SKILL.md limit (already a project convention) |
| **Load order control** | Ensure identity/invariant skills are loaded first | Agent `skills:` list ordering; loader respects order |
| **Periodic re-anchoring** | Re-surface key invariants at conversation milestones | Hook-based injection of invariant summaries at every N turns |
| **Companion skill factoring** | Put invariants in a dedicated companion skill (not domain knowledge) | Separate `identity` skill from `knowledge` skill in every team |

The existing practice of capping SKILL.md at 500 lines and loading identity
skills first already implements two of these strategies — the research gives
them a rigorous theoretical justification.

### 8.5 The Grader as the Verification Layer

The grader agent's role becomes clearer in the symbolic scaffolding frame:
it is the behavioral verification layer for symbolic constraints. The existing
grader evaluates code against a structured rubric — this is exactly the
statistical behavioral verification described in §6.4, applied to code quality.

The grader can be extended to function as a constraint auditor:

1. **Constraint extraction**: Parse the `invariants:` frontmatter from the
   loaded skills for the session
2. **Constraint-specific test generation**: For each invariant, generate
   adversarial prompts designed to elicit violations (e.g., for "never use
   `device_get_binding()`": provide old code that uses it and ask for extension)
3. **Violation detection scoring**: Add a "constraint adherence" rubric section
   that specifically checks for invariant violations alongside quality checks
4. **Drift detection**: Run the same constraint tests at session start vs.
   session end, comparing adherence rates to detect sycophantic drift

This transforms the grader from a code quality evaluator into a genuine symbolic
scaffolding verifier — the closest practical approximation of formal constraint
verification available in a probabilistic system.

### 8.6 The Identity Skill — Maximum Constraint Density

The identity skill occupies the L1 position in the cache hierarchy — it is
always loaded first, has maximum primacy effect, and represents the agent's
core behavioral configuration. Research implications for its design:

- **Invariants section first**: Hard constraints before domain description before
  preferences. Never bury them in the middle of a long prose description.
- **Positive framing throughout**: Every "never do X" should be "do Y; never
  do X" — paired suppression and replacement.
- **Concrete and specific**: "I am a Zephyr RTOS engineer using Zephyr 3.6.x
  on nRF52840 and nRF9160 targets" is a stronger prior than "I am an
  embedded systems engineer."
- **Short, imperative sentences for invariants**: "Use `west build --sysbuild`
  for nRF9160." Not "When building for the nRF9160 target, it is important
  to remember to include the `--sysbuild` flag in the west build command
  because the nRF9160 requires sysbuild."
- **Limit invariant count to ≤ 10**: The curse of instructions means that
  10 invariants at 90% individual compliance give only a 35% combined
  compliance rate. Fewer, stronger invariants outperform many weak ones.

### 8.7 The Neuro-Symbolic Architecture for claude-kit — Unified View

Synthesizing the research, the ideal architecture for reliable symbolic
scaffolding in claude-kit is a layered neuro-symbolic hybrid:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4 — External Deterministic Enforcement (Symbolic/Hard)    │
│ Hooks: PreToolUse, PostToolUse, Stop                            │
│ Enforces hard invariants with 100% reliability                  │
│ Subject to: action intercept latency (milliseconds)             │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                    blocked/modified actions
                              │
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3 — Statistical Behavioral Verification (Grader)          │
│ Constraint audits, rubric evaluation, drift detection           │
│ Enforces constraints retroactively via graded feedback          │
│ Subject to: session-end timing; cannot prevent, only detect     │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                     evaluated outputs
                              │
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2 — Probabilistic Linguistic Enforcement (Skills)         │
│ Skill files: identity → domain knowledge → preferences          │
│ Enforces constraints via strong Bayesian prior injection        │
│ Subject to: attention dilution, curse of instructions,          │
│             sycophancy, lost-in-middle effects                  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                  context-configured inference
                              │
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1 — Neural Parametric Defaults (LLM Weights)             │
│ Model's training-derived behavioral prior                       │
│ Provides base capability; source of all constraint failures     │
│ Subject to: training distribution, parametric compression bias  │
└─────────────────────────────────────────────────────────────────┘
```

Layer 4 (hooks) is the only truly symbolic layer — it enforces constraints as
formal predicates outside the neural computation. Layers 2 and 3 are
neuro-symbolic hybrids: they inject symbolic content into or evaluate the
output of the neural system, but do not replace it.

The design principle: **move invariants as far up the stack as possible**.
Any invariant that can be expressed as a tool intercept condition (e.g.,
"never run `rm -rf`," "always include `--sysbuild`") belongs in hooks.
Any invariant that requires semantic understanding of output content
(e.g., "never use `device_get_binding()`") should be in skills AND in
grader rubrics — it gets probabilistic enforcement via skills and
retroactive detection via grader. Any invariant that requires both
should additionally be in hooks where the action is detectable.

### 8.8 A Constraint Audit Protocol

The practical operationalization of behavioral verification for claude-kit:

```
Constraint Audit Protocol (v1)

For each active skill in the session:
  1. Extract invariants from ## Invariants section (or invariants: frontmatter)
  2. For each invariant:
     a. Generate 5 adversarial prompts designed to elicit a violation
     b. Generate 5 neutral prompts that should trigger correct adherence
     c. Run all 10 prompts against the loaded agent
     d. Score: violation rate (0-10) and adherence rate (0-10)
  3. Report:
     - Per-invariant compliance score
     - Worst-performing invariants (highest violation rate)
     - Context conditions under which violations occurred

Constraint drift test:
  1. Run the audit at session start (fresh context, N=10 tokens)
  2. Run the audit at simulated session middle (N=5000 tokens of prior context)
  3. Compute drift: change in violation rate between start and middle
  4. Flag any invariant where drift > 10 percentage points
```

This protocol can be implemented as a command (`/constraint-audit`) that the
grader agent executes, using the grader's existing read-only tool access and
evaluation rubric infrastructure.

---

## Traces

- **Upstream:** Market signals, competitive analysis, user research
- **Downstream:** REQ-002 (Scope-Aware Planning), REQ-004 (Runtime Enforcement)
- **Quality Attributes:** None identified

---

## Sources

### Neuro-Symbolic AI

- Bader, Sebastian (Springer Nature, 2025). "A Comprehensive Review of
  Neuro-symbolic AI for Robustness, Uncertainty Quantification, and
  Intervenability." *Arabian Journal for Science and Engineering*.
  doi:10.1007/s13369-025-10887-3.
  [Link](https://link.springer.com/article/10.1007/s13369-025-10887-3)

- arXiv:2501.05435 (2025). "Neuro-Symbolic AI in 2024: A Systematic Review."
  [Link](https://arxiv.org/html/2501.05435v1)

- arXiv:2510.21425 (2025). "Advancing Symbolic Integration in Large Language
  Models: Beyond Conventional Neurosymbolic AI."
  [Link](https://arxiv.org/html/2510.21425v1)

- arXiv:2504.07640 (2025). "Enhancing Large Language Models through Neuro-Symbolic
  Integration and Ontological Reasoning."
  [Link](https://arxiv.org/html/2504.07640v1)

- LAMDASZ-ML / GitHub (2024–2025). "Awesome-LLM-Reasoning-with-NeSy: Latest
  Advances on Neuro-Symbolic Learning in the era of LLMs."
  [Link](https://github.com/LAMDASZ-ML/Awesome-LLM-Reasoning-with-NeSy)

### Instruction Following and Constraint Satisfaction

- OpenReview R6q67CDBCH (2024). "Curse of Instructions: Large Language Models
  Cannot Follow Multiple Instructions at Once."
  [Link](https://openreview.net/forum?id=R6q67CDBCH)

- arXiv:2509.21051 (2025). "When Instructions Multiply: Measuring and Estimating
  LLM Capabilities of Multiple Instructions Following."
  [Link](https://arxiv.org/abs/2509.21051)

- arXiv:2502.15851 (2025). "Control Illusion: The Failure of Instruction
  Hierarchies in Large Language Models."
  [Link](https://arxiv.org/abs/2502.15851)

- arXiv:2404.13208 (2024). "The Instruction Hierarchy: Training LLMs to
  Prioritize Privileged Instructions." OpenAI.
  [Link](https://arxiv.org/abs/2404.13208)

- arXiv:2502.04362 (2025). "LLMs can be easily Confused by Instructional
  Distractions."
  [Link](https://arxiv.org/html/2502.04362v1)

- arXiv:2410.14516 (2024). "Do LLMs 'know' internally when they follow
  instructions?"
  [Link](https://arxiv.org/html/2410.14516v1)

- Unite.AI (2024). "Why Large Language Models Skip Instructions and How to
  Address the Issue."
  [Link](https://www.unite.ai/why-large-language-models-skip-instructions-and-how-to-address-the-issue/)

- RECAST (2025). "Strengthening LLMs' Complex Instruction Following with
  Constraint-Verifiable Data." arXiv:2505.19030.
  [Link](https://arxiv.org/html/2505.19030v2)

- arXiv:2512.14754 (2025). "Revisiting the Reliability of Language Models in
  Instruction-Following."
  [Link](https://arxiv.org/html/2512.14754v1)

### Bayesian In-Context Learning

- Xie et al. (2022). "An Explanation of In-Context Learning as Implicit Bayesian
  Inference." arXiv:2111.02080. ICLR 2022.
  [Link](https://arxiv.org/abs/2111.02080)

- ICLR 2024. "In-Context Learning through the Bayesian Prism." arXiv:2306.04891.
  [Link](https://arxiv.org/abs/2306.04891)

- arXiv:2406.01860 (2024). "Eliciting the Priors of Large Language Models using
  Iterated In-Context Learning."
  [Link](https://arxiv.org/html/2406.01860v1)

- arXiv:2504.12585 (2025). "Identifying and Mitigating the Influence of the
  Prior Distribution in Large Language Models."
  [Link](https://arxiv.org/html/2504.12585v1)

- Arora et al. (2025). "In-Context Learning Is Provably Bayesian Inference."
  arXiv:2510.10981.

- EMNLP 2024 Survey. "A Survey on In-context Learning."
  aclanthology.org/2024.emnlp-main.64.
  [Link](https://aclanthology.org/2024.emnlp-main.64.pdf)

### Constitutional AI and Invariant Specification

- Bai et al. / Anthropic (2022). "Constitutional AI: Harmlessness from AI
  Feedback." arXiv:2212.08073.
  [Link](https://arxiv.org/abs/2212.08073)

- Anthropic (2023). "Claude's Constitution."
  [Link](https://www.anthropic.com/news/claudes-constitution)

- arXiv:2504.04918 (2025). "Constitution or Collapse? Exploring Constitutional
  AI with Llama 3-8B."
  [Link](https://arxiv.org/html/2504.04918v1)

### Mechanistic Interpretability

- Arditi et al. (2024). "Refusal in Language Models Is Mediated by a Single
  Direction." NeurIPS 2024.
  [Link](https://proceedings.neurips.cc/paper_files/paper/2024/file/f545448535dfde4f9786555403ab7c49-Paper-Conference.pdf)

- IAAR-Shanghai / GitHub. "Awesome-Attention-Heads: Survey on interpretability
  of LLM attention heads."
  [Link](https://github.com/IAAR-Shanghai/Awesome-Attention-Heads)

- arXiv:2510.19875 (2025). "Stream: Scaling up Mechanistic Interpretability to
  Long Context in LLMs via Sparse Attention."
  [Link](https://arxiv.org/html/2510.19875v1)

- arXiv:2402.01761 (2024). "Rethinking Interpretability in the Era of Large
  Language Models."
  [Link](https://arxiv.org/html/2402.01761v1)

- Olsson et al. / Anthropic (2022). "In-Context Learning and Induction Heads."

### Sycophancy

- arXiv:2411.15287 (2024). "Sycophancy in Large Language Models: Causes and
  Mitigations."
  [Link](https://arxiv.org/abs/2411.15287)

- arXiv:2412.00967 (2024). "Linear Probe Penalties Reduce LLM Sycophancy."
  [Link](https://arxiv.org/abs/2412.00967)

- *npj Digital Medicine* (2025). "When helpfulness backfires: LLMs and the risk
  of false medical information due to sycophantic behavior."
  [Link](https://www.nature.com/articles/s41746-025-02008-z)

### Runtime Enforcement and Formal Specification

- arXiv:2503.18666 (2025). "AgentSpec: Customizable Runtime Enforcement for Safe
  and Reliable LLM Agents." Accepted ICSE 2026.
  [Link](https://arxiv.org/abs/2503.18666)

- arXiv:2602.22302 (2026). "Agent Behavioral Contracts: Formal Specification and
  Runtime Enforcement for Reliable Autonomous AI Agents."
  [Link](https://arxiv.org/html/2602.22302)

- arXiv:2508.00500 (2025). "Pro2Guard: Proactive Runtime Enforcement of LLM
  Agent Safety via Probabilistic Model Checking."
  [Link](https://arxiv.org/abs/2508.00500)

### Prompt Programming and Format Effects

- arXiv:2311.11482 (2023). "Meta-Prompting for AI Systems." (Meta Prompting).
  [Link](https://github.com/meta-prompting/meta-prompting)

- arXiv:2411.10541 (2024). "Does Prompt Formatting Have Any Impact on LLM
  Performance?"
  [Link](https://arxiv.org/html/2411.10541v1)

- Anthropic Claude Docs. "Use XML tags to structure your prompts."
  [Link](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags)

- alexop.dev (2024). "XML-Style Tagged Prompts: A Framework for Reliable AI
  Responses."
  [Link](https://alexop.dev/posts/xml-tagged-prompts-framework-reliable-ai-responses/)

### Positional Effects and Long Context

- Liu et al. (2023 / TACL 2024). "Lost in the Middle: How Language Models Use
  Long Contexts." arXiv:2307.03172.
  [Link](https://aclanthology.org/2024.tacl-1.9/)

- arXiv:2406.02536 (2024). "Mitigate Position Bias in Large Language Models via
  Scaling a Single Dimension."
  [Link](https://arxiv.org/abs/2406.02536)

- TechXplore (2025). "Lost in the middle: How LLM architecture and training data
  shape AI's position bias."
  [Link](https://techxplore.com/news/2025-06-lost-middle-llm-architecture-ai.html)
