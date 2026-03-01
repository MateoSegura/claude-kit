# LLM Non-Determinism: Causes, Measurement, and Mitigation

> A research document examining the fundamental sources of non-deterministic behavior
> in large language models, techniques for measuring and controlling it, and the
> specific implications for claude-kit as a context engineering framework.

**Date:** 2026-02-28

---

## Table of Contents

1. [The Foundational Problem](#1-the-foundational-problem)
2. [Root Causes of LLM Non-Determinism](#2-root-causes-of-llm-non-determinism)
   - 2.1 [Sampling Randomness: The Obvious Layer](#21-sampling-randomness-the-obvious-layer)
   - 2.2 [Floating-Point Non-Associativity: The Hidden Layer](#22-floating-point-non-associativity-the-hidden-layer)
   - 2.3 [Multi-GPU Parallelism and Batch Dynamics](#23-multi-gpu-parallelism-and-batch-dynamics)
   - 2.4 [Mixture-of-Experts Token Competition](#24-mixture-of-experts-token-competition)
   - 2.5 [KV Cache and Attention Mask Interactions](#25-kv-cache-and-attention-mask-interactions)
   - 2.6 [Precision Format Effects](#26-precision-format-effects)
   - 2.7 [The Autoregressive Compounding Effect](#27-the-autoregressive-compounding-effect)
3. [Measuring Non-Determinism](#3-measuring-non-determinism)
   - 3.1 [Why Standard Metrics Are Insufficient](#31-why-standard-metrics-are-insufficient)
   - 3.2 [Structural Cross-Entropy on ASTs](#32-structural-cross-entropy-on-asts)
   - 3.3 [Jensen-Shannon Divergence Over Token Distributions](#33-jensen-shannon-divergence-over-token-distributions)
   - 3.4 [Self-Consistency Rate](#34-self-consistency-rate)
   - 3.5 [pass@k and the pass@1 vs pass@k Gap](#35-passk-and-the-pass1-vs-passk-gap)
   - 3.6 [A Practical Measurement Framework](#36-a-practical-measurement-framework)
4. [Mitigation Techniques](#4-mitigation-techniques)
   - 4.1 [Sampling Controls](#41-sampling-controls)
   - 4.2 [Structured Outputs and JSON Schema Enforcement](#42-structured-outputs-and-json-schema-enforcement)
   - 4.3 [Constrained Decoding: Grammar-Level Control](#43-constrained-decoding-grammar-level-control)
   - 4.4 [Self-Consistency: Voting Over Multiple Samples](#44-self-consistency-voting-over-multiple-samples)
   - 4.5 [Context Engineering: Narrowing the Prior](#45-context-engineering-narrowing-the-prior)
   - 4.6 [System-Level Determinism: Batch-Invariant Kernels](#46-system-level-determinism-batch-invariant-kernels)
5. [The Deep Tension: Determinism vs. Stochasticity](#5-the-deep-tension-determinism-vs-stochasticity)
   - 5.1 [The Quality-Yield Tradeoff](#51-the-quality-yield-tradeoff)
   - 5.2 [Greedy Decoding Is Not Always Best](#52-greedy-decoding-is-not-always-best)
   - 5.3 [Temperature Is Not a Creativity Dial](#53-temperature-is-not-a-creativity-dial)
   - 5.4 [What the Podcast Claim Gets Right and Wrong](#54-what-the-podcast-claim-gets-right-and-wrong)
   - 5.5 [The Right Balance for Software Engineering](#55-the-right-balance-for-software-engineering)
6. [Practical Tooling Landscape](#6-practical-tooling-landscape)
   - 6.1 [Constrained Decoding Engines](#61-constrained-decoding-engines)
   - 6.2 [Validation and Retry Libraries](#62-validation-and-retry-libraries)
   - 6.3 [Serving-Level Determinism](#63-serving-level-determinism)
7. [Implications for claude-kit](#7-implications-for-claude-kit)
   - 7.1 [What claude-kit Already Does](#71-what-claude-kit-already-does)
   - 7.2 [Recommendation 1: Temperature Declarations in Agent Frontmatter](#72-recommendation-1-temperature-declarations-in-agent-frontmatter)
   - 7.3 [Recommendation 2: PostToolUse Output Validation Hooks](#73-recommendation-2-posttooluse-output-validation-hooks)
   - 7.4 [Recommendation 3: Structured Grader Output Schemas](#74-recommendation-3-structured-grader-output-schemas)
   - 7.5 [Recommendation 4: Self-Consistency via Grader-as-Validator](#75-recommendation-4-self-consistency-via-grader-as-validator)
   - 7.6 [Recommendation 5: Determinism Budget per Task Class](#76-recommendation-5-determinism-budget-per-task-class)
   - 7.7 [Recommendation 6: Skill Specificity as the Primary Control](#77-recommendation-6-skill-specificity-as-the-primary-control)
   - 7.8 [Summary: Non-Determinism Control Stack](#78-summary-non-determinism-control-stack)
8. [Sources](#8-sources)

---

## 1. The Foundational Problem

A podcast transcript frames the challenge precisely: *"Modern AI, especially large language models in these advanced agents, show non-deterministic emergent behaviors. They can and often do surprise us. It's an intrinsic property."*

This is technically accurate but incomplete. Non-determinism in LLMs is not a single phenomenon — it is a stack of overlapping causes that operate at different layers of the system, from token-level sampling to GPU arithmetic to serving infrastructure. Understanding each layer is essential before any mitigation strategy can be properly designed.

The practical stakes for software engineering are high. An LLM agent that consistently produces correct code is useful. An agent that produces correct code 70% of the time and subtly wrong code 30% of the time is a liability — the variance is what makes it dangerous. Reducing that variance without eliminating the model's generative capability is the core challenge claude-kit must address.

This document examines non-determinism from first principles, covers what can be measured, surveys the mitigation landscape from sampling controls to grammar-constrained decoding, and closes with concrete, actionable recommendations for claude-kit's architecture.

---

## 2. Root Causes of LLM Non-Determinism

### 2.1 Sampling Randomness: The Obvious Layer

The most visible source of non-determinism is the sampling process. At each generation step, the transformer outputs a raw logit vector over the vocabulary. These logits are converted to probabilities via softmax and then modified by several hyperparameters:

**Temperature** scales the logit distribution before softmax:

```
P(token_i | context) = softmax(logit_i / T)
```

- **T → 0**: Distribution collapses toward a point mass on the argmax token (greedy decoding). Theoretically deterministic.
- **T = 1**: Standard softmax — distribution reflects training-time confidence.
- **T > 1**: Distribution flattens — lower-probability tokens become more competitive.

**Top-p (nucleus) sampling** restricts sampling to the minimal set of tokens whose cumulative probability exceeds p. At p=0.9, the model samples only from the top-90% probability mass, discarding the long tail of low-probability alternatives.

**Top-k sampling** restricts to only the k most probable tokens at each step. Unlike top-p, it applies a fixed budget regardless of how concentrated or spread the distribution is.

**Min-p sampling** (2024) is a newer approach that removes tokens whose probability falls below a minimum fraction of the top token's probability. This dynamically adapts the cutoff based on the current distribution's sharpness, outperforming top-p on reasoning tasks in recent evaluations.

All three nucleus-type methods introduce deliberate stochasticity to increase diversity. Setting temperature to 0 and top-p to 1 (no nucleus) produces nominally greedy decoding — the theoretically most deterministic regime. But this is where the widespread misconception begins.

### 2.2 Floating-Point Non-Associativity: The Hidden Layer

Even at temperature=0, LLM outputs are frequently non-deterministic. The dominant underlying cause is **floating-point non-associativity** — a fundamental property of IEEE 754 arithmetic.

For floating-point numbers, addition is not associative:

```
(a + b) + c  ≠  a + (b + c)
```

This is not a software bug — it is mathematically guaranteed by finite-precision representation and rounding rules. The error per operation is tiny (on the order of machine epsilon, ~10⁻⁷ for float32), but in neural networks with billions of parameters, these errors accumulate across matrix multiplications, attention computations, and softmax normalizations.

The critical interaction: **GPU reduction order is not guaranteed to be consistent across runs.** When a GPU computes the sum of a large vector (e.g., an attention weight accumulation), the parallel reduction order depends on hardware scheduling. Identical inputs may produce slightly different floating-point sums depending on which thread finished first.

These tiny numerical differences are then amplified by the softmax:

```
softmax(x_i) = exp(x_i) / Σ exp(x_j)
```

Softmax is not a linear function — small perturbations near a decision boundary (where two tokens have nearly identical logits) can flip which token is selected under greedy decoding. The result: **identical prompts, same temperature=0, same hardware — different outputs on different runs.**

Research from 2025 demonstrated that with a 235-billion-parameter model at temperature=0, without batch-invariant kernels, 1000 identical runs produced 80 unique completions. The variation was entirely attributable to floating-point non-associativity.

### 2.3 Multi-GPU Parallelism and Batch Dynamics

Modern LLM serving uses two primary parallelism strategies:

**Tensor parallelism** shards weight matrices across GPUs, with each GPU computing a slice of the attention mechanism. The results are all-reduced across devices. The all-reduce operation involves a tree-structured summation across GPUs — and the order of this summation affects the floating-point result due to non-associativity.

**Dynamic batching** is the practice of grouping multiple user requests into a single GPU batch to maximize hardware utilization. This is where the most impactful non-determinism arises: **the result for a given request changes based on what other requests are in the same batch.**

The mechanism is subtle. When batch size changes:

1. Matrix multiplication dimensions change, triggering different GPU kernel dispatch paths.
2. Different kernel variants use different reduction strategies with different floating-point reduction orders.
3. The final logit values for any given request shift by tiny amounts — but enough to flip argmax decisions at token boundaries.

This means that the same query, submitted at different times of day when server load differs, can produce different outputs even at temperature=0. The non-determinism is introduced by the infrastructure, not the user's sampling parameters.

This is what the 2024 Thinking Machines Lab research called "batch invariance" — the property that inference results should not change based on what other requests happen to be processed simultaneously. Most production serving systems historically lacked this property.

### 2.4 Mixture-of-Experts Token Competition

Sparse Mixture-of-Experts (MoE) models (like many frontier models) add another source of non-determinism. In MoE architectures, each token is routed to a subset of expert networks based on a routing function.

Under capacity constraints (when more tokens are routed to an expert than its buffer capacity allows), tokens compete for buffer slots. The competition outcome can depend on:

- **Processing order**: Which tokens arrive at the router first.
- **Batch composition**: Tokens from different sequences in the same batch may compete for the same expert, and the outcome affects both sequences.

This means MoE non-determinism is **sequence-cross-contaminating**: the presence of other users' requests in the same batch can alter the routing decisions for your request, changing the computational path and therefore the output. Even with temperature=0 and deterministic hardware, MoE routing under capacity constraints introduces stochastic variation.

### 2.5 KV Cache and Attention Mask Interactions

KV (key-value) caches store the attention computation results for previously generated tokens, enabling efficient autoregressive generation without recomputing the full attention over the growing context at each step.

Non-determinism enters through several mechanisms:

**Cache eviction and re-computation**: When context exceeds the serving system's memory budget, older KV entries may be evicted. Re-computing evicted entries may produce slightly different floating-point values than the original computation (due to non-associativity), subtly shifting subsequent generation.

**Attention mask variations**: In speculative decoding (where a smaller draft model proposes tokens that a larger model verifies), accepted tokens affect how the KV cache grows. The acceptance pattern is stochastic at the draft model level, meaning the cache state can diverge across runs even when the final verified tokens are identical.

**Prefix caching**: Many serving systems cache computation for common prefixes (system prompts, few-shot examples). If a prefix is cached from a computation with a different batch composition, the floating-point values may differ slightly from a fresh computation — introducing cache-origin non-determinism.

### 2.6 Precision Format Effects

The numeric format used for model weights and activations dramatically affects how much non-determinism accumulates:

| Format | Mantissa bits | Effective precision | Observed determinism |
|--------|--------------|---------------------|---------------------|
| FP32 | 23 bits | ~7 decimal digits | Near-perfect |
| BF16 | 7 bits | ~2-3 decimal digits | Substantial variance |
| FP8 | 3-4 bits | <2 decimal digits | High variance |
| INT8 | 8 bits (integer) | Exact for fixed ops | Deterministic for quantized ops |

BF16 is the dominant format for production LLM inference due to its speed and memory advantages — but it provides only ~3 decimal digits of precision. At softmax decision boundaries, this precision loss can consistently flip token selections.

The 2025 NeurIPS paper "Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference" (arXiv:2506.09501) showed that FP32 achieves near-perfect determinism under controlled conditions, while BF16 with dynamic batching exhibits the most variance.

### 2.7 The Autoregressive Compounding Effect

Autoregressive generation means each token conditions the next. Non-determinism at token position `t` propagates through the remainder of the sequence:

```
Token_1 varies slightly
  → Token_2 computed on a slightly different prefix
    → Token_3 computed on an increasingly diverged prefix
      → Full output has compounded all variations
```

This is why a single bit flip in a floating-point addition early in the sequence can produce structurally different code by the end of a 500-line generation. The early token sets the direction; divergence compounds.

For software engineering tasks, this has a concrete implication: the first few tokens of a function signature determine the overall structure. If those tokens are uncertain (near decision boundaries), the entire body of the function can vary substantially across runs.

**Summary of root causes by layer:**

| Layer | Cause | Controllable by user? |
|-------|-------|-----------------------|
| Sampling | Temperature, top-p, top-k randomness | Yes — set T=0 |
| Arithmetic | Floating-point non-associativity in GPU kernels | No — hardware property |
| Infrastructure | Dynamic batching changes reduction order | No — depends on server load |
| Architecture | MoE expert competition under capacity | No — model architecture |
| Cache | KV cache eviction, prefix cache origin | Partially — avoid speculative decoding |
| Precision | BF16 mantissa truncation | Sometimes — request FP32 if API allows |
| Autoregressive | Early token variation compounds | No — fundamental property |

---

## 3. Measuring Non-Determinism

### 3.1 Why Standard Metrics Are Insufficient

The standard evaluation toolkit for LLMs was designed for accuracy, not variance:

- **BLEU / ROUGE**: Measure surface-level similarity to a reference. Cannot quantify variance across runs without a reference, and fail to distinguish structurally equivalent code with different identifiers.
- **CodeBLEU**: Adds AST and dataflow considerations but is still reference-dependent.
- **Accuracy / pass@1**: A binary correctness signal on a single sample — by definition, it ignores variance.

None of these metrics answer the question that matters for reliability engineering: *given this prompt, how much does the model's output vary across repeated invocations?* A model that produces correct code 80% of the time and near-correct code 20% of the time has very different reliability characteristics from a model that produces correct code 80% of the time and completely wrong code 20% of the time — yet these scenarios may produce identical BLEU scores if the wrong code is lexically similar.

### 3.2 Structural Cross-Entropy on ASTs

The most principled metric for code generation stability is **Structural Cross-Entropy (SCE)**, introduced in arXiv:2508.14288 (2025). The approach:

1. **Generate N outputs** for the same prompt.
2. **Parse each output into an Abstract Syntax Tree (AST)**.
3. **Extract depth-bounded subtrees** (subtrees up to depth d) from each AST.
4. **Treat subtree frequencies as a probability distribution** over structural patterns.
5. **Compute cross-entropy** between the distributions from different runs.

This produces a **reference-free** measure of structural variance. A model that always generates the same control flow structure (same loop patterns, same conditional structure, same function decomposition) will have low SCE regardless of surface-level lexical differences. A model that sometimes generates iteration and sometimes recursion for the same logical task will have high SCE.

The metric has two variants:
- **Structure-only SCE**: Ignores identifier names, focuses purely on control flow shape.
- **Token-aware SCE**: Includes identifier names and literals, capturing semantic variance as well.

The key property that makes SCE useful for claude-kit's purposes: it is **execution-independent**. It does not require running code, compiling, or having a test suite. It quantifies structural variance at parse time.

### 3.3 Jensen-Shannon Divergence Over Token Distributions

For measuring variance at the token distribution level, **Jensen-Shannon Divergence (JSD)** provides a symmetric, bounded metric:

```
JSD(P || Q) = (1/2) KL(P || M) + (1/2) KL(Q || M)
where M = (P + Q) / 2
```

JSD ranges from 0 (identical distributions) to log(2) ≈ 0.693 (completely disjoint distributions) when using natural logarithms, or 0 to 1 when using base-2 logarithms.

Applied to LLM output variance:

1. **At token level**: Treat the empirical token-frequency distribution from N runs as P and Q. JSD measures how much the vocabulary usage varies.
2. **At AST subtree level**: Treat the subtree-frequency distributions as P and Q. This is effectively the JSD variant of SCE, offering an alternate distance measure.

The advantage of JSD over SCE for practical use: JSD gives a single scalar per prompt, making it easy to rank prompts by variability and track stability improvements over time.

### 3.4 Self-Consistency Rate

**Self-consistency rate** measures the fraction of N outputs that agree with the majority response. For a task with a well-defined correct answer (a function that passes a test suite, a JSON that satisfies a schema), the metric is:

```
SCR = (count of outputs matching the modal output) / N
```

A SCR of 1.0 means all runs produce identical outputs — perfect consistency. A SCR of 0.2 means only 1 in 5 runs agrees with the majority — high variance.

The self-consistency rate is conceptually simple and directly measurable for claude-kit's software engineering tasks, since code either compiles and passes tests or it does not. It provides an operationalizable proxy for reliability.

Research from NAACL 2025 ("The Good, The Bad, and The Greedy") found that LLMs under sampling conditions can exhibit SCR as low as 0.11 on tasks where greedy decoding gets the answer correct — meaning 89% of sampled runs failed on questions the model "knew" the answer to in greedy mode. This demonstrates that variance reduction is not merely an academic concern.

### 3.5 pass@k and the pass@1 vs pass@k Gap

**pass@k** (Chen et al., 2021) measures the probability that at least one of k independently sampled solutions passes a test suite:

```
pass@k ≈ 1 - C(n-c, k) / C(n, k)
```

where n is the total number of samples, c is the number of correct samples, and C(·,·) is the binomial coefficient. This is an unbiased estimator that avoids the need to run k separate evaluations per prompt.

The **pass@1 vs pass@k gap** is a key non-determinism indicator. A large gap (high pass@k, low pass@1) means the model knows how to solve the problem but cannot consistently produce the correct solution on the first try. This is precisely the failure mode that makes LLM agents unreliable in production.

From arXiv:2508.14288, Qwen-2.5-Coder shows pass@1=0.373 and pass@5=0.517 — a gap that implies substantial per-run variance. A reliable production agent needs pass@1 to approach pass@k; the gap is a direct measure of variance that context engineering should close.

### 3.6 A Practical Measurement Framework

For evaluating claude-kit's effectiveness at reducing non-determinism, the following measurement protocol is recommended:

| Metric | Measurement method | Frequency |
|--------|-------------------|-----------|
| **pass@1** | Run the task once, check if output passes tests | Per task |
| **pass@5** | Run the task 5 times, check if any output passes | Per task |
| **pass@1 / pass@5 gap** | Subtract — measures exploitable variance | Per task |
| **Self-consistency rate** | Count modal outputs in 5 runs | Per task |
| **Structural SCE** | Parse ASTs from 5 runs, compute cross-entropy | Per task |
| **JSD over AST subtrees** | Pairwise JSD across 5 run outputs | Per task |

Running these across the 6-level ablation study proposed in `theory-context-cache.md` would produce a complete variance profile at each level, validating the hypothesis that context injection monotonically reduces non-determinism.

---

## 4. Mitigation Techniques

### 4.1 Sampling Controls

The most direct interventions operate on the sampling hyperparameters:

**Temperature = 0 (greedy decoding)**

Setting temperature to zero theoretically eliminates sampling randomness by always selecting the argmax token. In practice, it eliminates one source of non-determinism while leaving the hardware and infrastructure sources intact (see sections 2.2 and 2.3).

*When to use*: Tasks where a single correct answer exists and creativity is counterproductive — code compilation, JSON generation, deterministic data transformation.

*Limitation*: Greedy decoding is not always better. It can produce locally optimal but globally suboptimal outputs — a greedy decoder commits to the first plausible token without exploring alternatives. For complex reasoning chains, a slightly non-greedy exploration at critical decision points can improve global correctness.

**Seed parameters**

Some APIs allow specifying a random seed to control the sampling RNG. This eliminates sampling randomness (equivalent to making top-p/top-k deterministic given the logit values), but does not address floating-point non-associativity from batch dynamics. The same seed with a different batch composition still produces different logit values, and thus potentially different outputs.

**Top-p and top-k tightening**

Reducing top-p (e.g., from 0.95 to 0.7) reduces the number of candidate tokens, concentrating probability mass on high-confidence predictions. This reduces variance without fully eliminating it. The tradeoff is reduced diversity in cases where multiple valid responses exist.

**Min-p sampling (2024)**

Min-p dynamically adjusts the token cutoff based on the top token's probability:

```
threshold = min_p × max(probabilities)
eligible_tokens = {t : P(t) >= threshold}
```

This adapts intelligently: when the model is very confident (a clear token winner), min-p becomes very restrictive. When the model is uncertain, the threshold relaxes to allow more exploration. This achieves higher accuracy and diversity than top-p on self-consistency benchmarks while avoiding the fixed-cutoff problems of top-k.

**Decoding strategy comparison:**

| Strategy | Determinism | Diversity | Best for |
|----------|------------|-----------|----------|
| Greedy (T=0) | Highest (conditional on batch) | Lowest | Structured tasks, single correct answer |
| Beam search | High (deterministic beam) | Low | Translation, summarization |
| Top-k | Moderate | Moderate | General generation |
| Top-p (nucleus) | Moderate | Moderate-high | Open-ended tasks |
| Min-p | Moderate | Higher than top-p | Reasoning, creative |
| Temperature > 1 | Lowest | Highest | Brainstorming |

### 4.2 Structured Outputs and JSON Schema Enforcement

API-level structured output enforcement (released by OpenAI in August 2024; available through Anthropic's tool use) guarantees that outputs conform to a specified JSON Schema. Rather than asking the model to produce JSON and hoping it complies, schema enforcement modifies the generation process to physically prohibit non-conforming tokens.

This is a distribution-narrowing technique: instead of sampling from the full vocabulary at each position, the model samples only from tokens that could appear in a valid JSON object matching the schema.

**How it works at the API level**: The server maintains a finite automaton representing the JSON Schema grammar. At each generation step, the automaton determines the set of valid next tokens. The model's logit vector is masked — logits for invalid tokens are set to -infinity before softmax — ensuring the sampled token is always schema-valid.

**Practical impact**: For tasks where the output should be a structured report, an evaluation JSON, or a configuration object, schema enforcement eliminates the entire class of malformed-output failures. The model cannot produce `{"score": "high"}` when the schema requires `{"score": integer}`.

**Limitation**: Schema enforcement addresses the structure of the output, not its semantic content. A model can produce perfectly valid JSON `{"build_command": "wrong_command"}` — the structure is correct but the content is wrong. Schema enforcement is necessary but not sufficient for semantic correctness.

### 4.3 Constrained Decoding: Grammar-Level Control

Grammar-constrained decoding (GCD) generalizes JSON schema enforcement to arbitrary context-free grammars (CFGs). Where JSON schema handles the structure of JSON documents, CFG-constrained decoding can handle any formal language — Python syntax, Zephyr devicetree overlay format, regex patterns, domain-specific languages.

**The mechanism**: A GCD engine maintains a parse state representing where in the grammar the current generation is. At each step, it computes the set of tokens that could legally extend the current parse, then masks the logit vector accordingly.

The core challenge is performance: computing the valid token set naively requires checking all ~128,000 vocabulary tokens against the grammar at each step, which can be prohibitively slow.

**Modern solutions (2024-2025)**:

**XGrammar** (arXiv:2411.15100, 2024) achieves near-zero overhead by recognizing that approximately 99% of vocabulary tokens are **context-independent** — their validity depends only on the current grammar position, not on the full parse stack. These tokens can be precomputed once at grammar compilation time. Only the remaining ~1% (context-dependent tokens requiring stack inspection) need runtime evaluation. The result: token mask generation in under 40 microseconds, with performance up to 100x better than traditional grammar-constrained methods and up to 10x better than alternatives on CFG-guided tasks.

**llguidance** (Microsoft, 2024) is a Rust-based engine that uses a derivative-based regex lexer combined with an Earley parser for CFG rules. It achieves approximately 50 microseconds CPU time per token for 128K-token vocabularies, with negligible startup costs. The Earley parser handles ambiguous grammars and arbitrary CFGs, making it more expressive than automaton-based approaches.

**Grammar-Aligned Decoding (GAD)** (arXiv:2405.21047, 2024) identifies a limitation of standard GCD: masking invalid tokens distorts the model's probability distribution. A token that is grammatically valid but semantically nonsensical may receive inflated probability because all the probability mass from filtered tokens redistributes to the valid set. GAD addresses this by reweighting the sampling distribution so the model behaves as if it had been trained with the grammar constraint — producing grammatically valid outputs with minimal distortion of the model's semantic probabilities.

**IterGen** (ICLR 2025) introduces forward/backward generation tied to grammar symbols, with KV-cache reuse making "undo and redo" efficient. This enables controllable backtracking when a partial generation becomes irrecoverable under the grammar.

**Applicability to claude-kit's domains**:

| Task | Grammar type | GCD benefit |
|------|-------------|-------------|
| Zephyr devicetree overlays | CFG (DTS format) | Eliminate malformed overlay syntax |
| Kconfig fragments | CFG (Kconfig grammar) | Prevent invalid configuration |
| Grader reports | JSON Schema | Enforce score ranges, required fields |
| Build commands | Regex whitelist | Block injection-prone patterns |
| Python code | Python CFG | Guarantee syntactically valid code |

For claude-kit's API-based agents that cannot use local model serving with GCD, the equivalent mechanism is **PostToolUse hook validation** — generate the output, then validate and block if malformed. This is discussed in section 7.3.

### 4.4 Self-Consistency: Voting Over Multiple Samples

**Self-consistency** (Wang et al., 2023) generates multiple independent completions for the same prompt and selects the most frequent answer as the final output. Originally applied to chain-of-thought reasoning tasks, it extends naturally to code generation.

The approach exploits the statistical property that if the correct answer has higher probability than any individual wrong answer, the majority of samples will converge on it — even when no individual sample is guaranteed to be correct.

**Workflow**:
1. Generate N responses at temperature T > 0 (higher than for single-shot, to ensure diversity).
2. Execute each response (for code: compile and run tests).
3. Select the response that passes the most tests, or apply majority voting over categorical outcomes.

**pass@k as an upper bound**: Self-consistency effectively approximates pass@k performance in scenarios where you can score outputs programmatically. If pass@5 >> pass@1, self-consistency with k=5 should substantially outperform single-shot generation.

**Practical tradeoffs**:

| Self-consistency variant | Compute cost | Quality gain |
|--------------------------|-------------|-------------|
| N=3, majority vote | 3x | Moderate |
| N=5, execution-based ranking | 5x | Significant |
| N=10, weighted by test pass rate | 10x | Near-optimal |
| Best-of-N with reward model | Nx + scoring | Near-oracle |

Research from NAACL 2025 found that Best-of-N sampling allows smaller models to match or exceed GPT-4-Turbo performance on coding benchmarks — the compute overhead is justified when correctness is critical.

**The "self-correction" distinction**: A common misconception is that showing the model its own output and asking it to fix errors (self-correction) is equivalent to self-consistency. It is not. Research consistently finds that self-correction without external feedback slightly *degrades* performance — the model tends to overthink correct answers. Self-consistency works because it exploits diversity across independent samples; self-correction works only when the correction signal comes from an external oracle (test suite, grader).

### 4.5 Context Engineering: Narrowing the Prior

Context engineering is the most fundamental non-determinism mitigation because it operates before any sampling occurs. By narrowing the model's prior distribution over outputs through carefully crafted context, it reduces the entropy of the output distribution at the source.

The mechanism, formalized in `theory-context-cache.md`:

```
H(output | context) = -Σ P(token_i | context) × log P(token_i | context)
```

Each layer of injected context reduces this entropy. When the model is given the exact API signature, the exact hardware constraints, and the exact conventions it must follow, the output space narrows from "all plausible code" to "code that uses this specific API correctly for this specific hardware." That narrowing is not sampling-based — it shifts the probability mass before any random token is drawn.

**Why this is the primary mechanism for claude-kit**:

The other mitigation techniques (sampling controls, GCD, self-consistency) are post-hoc or parametric: they constrain, filter, or select after the model has computed its distribution. Context engineering changes what distribution the model computes. It is the only mechanism that can reduce variance by increasing the model's knowledge.

Specifically, context engineering addresses the **parametric knowledge failure mode**: when the model's training-time knowledge about an API, a hardware target, or a convention is stale, compressed, or contradicted by newer information, it will hallucinate with high confidence. No amount of temperature reduction prevents this — you can greedily decode a confidently wrong answer.

Arora et al. (2025) proved that posterior variance from task uncertainty vanishes exponentially with in-context examples. Each well-chosen skill in claude-kit functions as an in-context example that contributes to this exponential variance reduction.

**The specificity principle**: More specific context produces more consistent outputs. Wang et al. (2023) showed this empirically — prompts that precisely specify the expected output format, the relevant API functions, and the domain constraints produce significantly higher self-consistency rates. This is the theoretical justification for claude-kit's skill design guidelines (500-line max, focused scope, authoritative content).

The 2025 survey "A Survey of Context Engineering for Large Language Models" (arXiv:2507.13334) formalizes this, describing context engineering as "a formal discipline that transcends simple prompt design to encompass the systematic optimization of information payloads for LLMs" — exactly what claude-kit implements through its hierarchical skill architecture.

### 4.6 System-Level Determinism: Batch-Invariant Kernels

For operators running their own inference infrastructure, system-level determinism is achievable through batch-invariant kernel design.

**Token Batch-Invariant Kernels (TBIK)** align intra- and inter-GPU reduction orders through a unified binary tree topology. Instead of allowing the reduction tree to vary with batch composition, TBIK enforces a fixed reduction order regardless of batch size. This adds computational overhead but guarantees reproducible results.

Research demonstrated the impact: with a 235B-parameter model, temperature-0 completions yield 80 unique completions out of 1000 runs without batch-invariant kernels; with batch-invariant kernels, 1000/1000 completions match exactly.

**Performance cost**: Achieving full determinism through batch-invariant kernels typically incurs 25-45% throughput overhead (average ~34%). For most production systems, this tradeoff is not worth it.

**SGLang deterministic mode** (LMSYS, 2025) and vLLM's deterministic scheduling mode support explicit reproducibility at the cost of throughput, suitable for offline evaluation and research.

**The practical conclusion for claude-kit users**: Claude-kit operates on top of the Anthropic API, where system-level determinism is not user-controllable. This makes context engineering and hook-based validation even more important — they provide variance reduction at layers the user can control.

---

## 5. The Deep Tension: Determinism vs. Stochasticity

### 5.1 The Quality-Yield Tradeoff

The most important empirical finding in LLM evaluation research is that determinism and quality are not monotonically related. The NAACL 2025 paper "The Good, The Bad, and The Greedy" formally demonstrates a **quality-yield tradeoff**:

> *Deterministic sampling achieves suboptimal quality while stochastic sampling achieves better quality at the cost of solving fewer problems, revealing a trade-off between quality and yield.*

Concretely: greedy decoding tends to produce the correct answer *more often* (higher pass@1) but can get "stuck" on locally plausible but globally wrong solutions. Stochastic sampling explores more of the solution space (higher pass@k gap) but any single sample is less likely to be correct.

This is the core tension: the mechanism that makes outputs more consistent (determinism) also makes them less explorative, and exploration is sometimes necessary to find the correct answer.

### 5.2 Greedy Decoding Is Not Always Best

A counterintuitive result: greedy decoding can fail on problems that stochastic sampling solves reliably. This happens when the correct solution path requires a "less obvious" first token — the argmax token at position t leads to a dead end, while a slightly lower-probability token leads to the correct solution.

For code generation, this manifests as:
- The greedy decoder selects the most common function name for a task, but that function has the wrong signature for this specific hardware target.
- Stochastic sampling occasionally picks the correct but less common function name.

This is why beam search (maintaining multiple candidate sequences) was the dominant approach before sampling — it explores multiple paths simultaneously without full stochasticity. Modern practice has largely moved to sampling with self-consistency or best-of-N, which achieves similar exploration benefits more efficiently.

The "The Good, The Bad, and The Greedy" paper explicitly demonstrates that Best-of-N sampling from smaller models can match or surpass larger models under greedy decoding on coding benchmarks — exploration compensates for model size. This has direct implications for claude-kit's choice of model per agent role.

### 5.3 Temperature Is Not a Creativity Dial

A common mischaracterization — including in much practitioner documentation — is that temperature controls "creativity." Research from 2024 (arXiv:2402.05201) examined this claim empirically:

> *The influence of temperature on LLM performance is far more nuanced and weak than suggested by the "creativity parameter" claim.*

Key findings:
- Changes in temperature from 0.0 to 1.0 do not have statistically significant impact on problem-solving performance across many tasks.
- Temperature increases slightly the novelty of outputs, but the effect size is small.
- For GPT-4, low temperature (0.1) with high top-p (0.9) yields the best coding performance — suggesting determinism in sampling combined with a broad candidate pool.

What temperature actually controls is the **sharpness of the probability distribution**. Low temperature makes it harder for low-probability tokens to compete with high-probability ones. This is useful for tasks with clear correct answers, but it does not inherently "enable" or "disable" creativity — that depends on whether the model's training distribution contains creative solutions.

The practical implication: **temperature is a variance control, not a creativity switch.** For software engineering tasks where there are many valid solutions, lower temperature produces more consistent solutions from among the most probable responses, not necessarily the best solutions overall.

### 5.4 What the Podcast Claim Gets Right and Wrong

*"Non-determinism is not a bug, it's a feature of their complexity."*

**What this gets right**: Non-determinism is genuinely intrinsic to transformer generation in a way that cannot be fully eliminated without sacrificing model capability. The stochastic exploration that produces non-determinism also enables the model to find creative solutions that greedy decoding misses. Forcing full determinism (temperature=0 plus batch-invariant kernels) produces models that are reliable but brittle — they consistently produce the argmax sequence, which is not always the best sequence.

Additionally, emergent behaviors in large models — the unexpected capabilities that appear at scale — appear to be partly a consequence of the stochastic nature of the training process itself. A fully deterministic training process would likely produce less capable but more predictable models.

**What this gets wrong**: The implicit conclusion that non-determinism is therefore uncontrollable or must be simply accepted. Non-determinism has multiple causes at different layers. The sampling randomness layer is fully controllable. The context engineering layer can narrow the distribution dramatically before any sampling occurs. Hook-based validation can catch non-deterministic failures before they reach the user. The question is not "to be deterministic or not" but "where in the stack to apply which controls."

**The deeper insight**: The goal is not to eliminate non-determinism but to confine it. In a well-designed agent system, non-determinism should be concentrated in the exploratory phases (brainstorming, proposal generation) and minimized in the execution phases (code writing, command invocation, file editing). This is achievable through careful agent role design — which is exactly what claude-kit's role separation already provides.

### 5.5 The Right Balance for Software Engineering

Software engineering tasks fall on a spectrum from fully deterministic (correct answer exists and is verifiable) to fully open-ended (no single correct answer):

| Task type | Determinism need | Stochasticity benefit | Recommended regime |
|-----------|-----------------|----------------------|-------------------|
| Build command construction | High | None | T=0, schema-enforced |
| API call implementation | High | Low | T=0 to 0.2, domain skill loaded |
| Algorithm implementation | Moderate | Moderate | T=0.2 to 0.5, verified by test |
| Architecture design | Low | High | T=0.7 to 1.0, self-consistency |
| Code review commentary | Moderate | Moderate | T=0.3 to 0.5, structured output |
| Debugging hypothesis generation | Moderate | High | T=0.5 to 0.8, multiple candidates |
| Documentation | Low | High | T=0.7 to 1.0 |

The key insight: **different agent roles in claude-kit should operate in different temperature regimes.** The engineer executing build commands needs near-determinism. The engineer designing architecture needs explorative stochasticity. The grader evaluating correctness against a rubric needs determinism to be reproducible. These are different tasks with different optimal configurations — and they should be encoded in agent frontmatter rather than left to implicit defaults.

---

## 6. Practical Tooling Landscape

### 6.1 Constrained Decoding Engines

The following tools implement grammar-constrained decoding and are production-ready as of early 2026:

**XGrammar** (MLC, arXiv:2411.15100)
- Language: C++ with Python/Rust bindings
- Grammar support: JSON Schema, EBNF, regex
- Performance: <40μs per token mask generation; up to 100x faster than traditional methods
- Integration: Native in vLLM, SGLang, TensorRT-LLM
- Use case: Production serving of structured outputs
- Repository: `mlc-ai/xgrammar`

**llguidance** (Microsoft)
- Language: Rust with Python bindings
- Grammar support: Arbitrary CFG, regex, JSON Schema, Lark grammars
- Performance: ~50μs per token, negligible startup cost
- Approach: Derivative-based regex lexer + Earley parser
- Use case: Expressive CFG constraints, production serving
- Repository: `guidance-ai/llguidance`

**Outlines** (dottxt.ai)
- Language: Python
- Grammar support: Pydantic, JSON Schema, regex, EBNF, choice
- Performance: Precomputes full FSM at startup; fast per-step masking
- Integration: vLLM, LlamaCpp, Transformers, mlx-lm
- Use case: Local model serving, research, prototyping
- Repository: `dottxt-ai/outlines`

**Guidance** (Microsoft)
- Language: Python
- Approach: Constrained generation interleaved with program control flow
- Performance: Negligible startup cost for JSON Schema via llguidance backend
- Use case: Complex conditional generation programs with interleaved logic
- Repository: `guidance-ai/guidance`

**LMQL** (ETH Zurich)
- Language: Python DSL
- Approach: Full programmability — constraints, variables, control flow in LLM programs
- Focus: Programmable LLM queries rather than pure structured output
- Use case: Research, complex multi-step constrained generation

### 6.2 Validation and Retry Libraries

**Instructor** (567-labs)
- Wraps any LLM API with Pydantic-based output parsing and automatic retry
- On validation failure, re-sends the prompt with error context appended
- Supports 15+ providers including Anthropic Claude
- Handles streaming, partial parsing, and nested models
- Repository: `567-labs/instructor`

The validation-and-retry pattern is distinct from grammar-constrained decoding:
- **GCD**: Prevents non-conforming tokens from being generated (proactive, zero post-processing cost)
- **Validation + retry**: Generates freely, validates the result, re-prompts if invalid (reactive, costs extra inference per failure)

For claude-kit agents that use the Anthropic API (where GCD is not directly available to users), the validation + retry approach via PostToolUse hooks is the architecturally correct equivalent.

### 6.3 Serving-Level Determinism

**SGLang deterministic mode** (LMSYS, 2025)
- Disables dynamic batching to ensure consistent reduction order
- Enables seed-based reproducibility
- Cost: 25-45% throughput overhead
- Suitable for offline evaluation, not production serving

**LLM-42** (arXiv:2601.17768, 2025)
- Verified speculation approach: uses formal verification to guarantee that speculative decoding produces bit-exact results
- Research-stage, not yet production-deployed

These tools are relevant for teams running self-hosted inference and do not apply directly to claude-kit users on the Anthropic API.

---

## 7. Implications for claude-kit

### 7.1 What claude-kit Already Does

The existing claude-kit architecture addresses non-determinism at the context level (addressing the sampling and knowledge causes from the root cause taxonomy):

1. **Skill injection** reduces output entropy by providing authoritative domain knowledge, eliminating the need for the model to rely on compressed parametric memory.
2. **Identity skills** enforce consistent methodological priors across sessions.
3. **Multi-agent specialization** narrows each agent's output space — an engineer agent's distribution is narrower than a generalist agent's because its role, tools, and skills are more constrained.
4. **PreToolUse hooks** prevent non-deterministically unsafe tool calls before execution.
5. **The `theory-context-cache.md` framework** provides the theoretical basis for understanding why these interventions work.

What claude-kit does not currently address:
- Sampling configuration per agent role
- Structured output schemas for agent outputs
- PostToolUse validation of generated content
- Explicit self-consistency through multi-agent grading as an automatic step
- Measurement of non-determinism at each configuration level

The following recommendations fill these gaps.

### 7.2 Recommendation 1: Temperature Declarations in Agent Frontmatter

Add a `temperature` field to agent frontmatter that specifies the recommended sampling regime for that agent's role. This encodes the task-type analysis from section 5.5 into machine-readable configuration.

**Proposed frontmatter extension:**

```yaml
---
name: Embedded Zephyr Engineer
description: Implements firmware features for nRF52840 targets using Zephyr RTOS
model: claude-sonnet-4-6
temperature: 0.2
tools:
  - Read
  - Write
  - Edit
  - Bash
skills:
  - embedded-zephyr-knowledge:zephyr-rtos
  - embedded-zephyr-knowledge:devicetree-kconfig
  - core-kit:routing
---
```

**Temperature guidelines by role:**

| Agent role | Recommended temperature | Rationale |
|-----------|------------------------|-----------|
| Engineer (implementation) | 0.1 to 0.3 | Code correctness is verifiable; minimize variance |
| Engineer (architecture/design) | 0.5 to 0.7 | Multiple valid solutions; exploration beneficial |
| Grader | 0.1 to 0.2 | Rubric evaluation should be reproducible |
| Tester | 0.2 to 0.4 | Test generation benefits from coverage diversity |
| Debugger | 0.3 to 0.5 | Hypothesis generation benefits from exploration |
| Repo analyzer | 0.0 to 0.1 | Detection tasks have ground truth; minimize drift |

**Implementation path**: Claude Code's agent system reads YAML frontmatter from agent files. The `temperature` field can be passed through to the API call. The `system-maker` and `system-updater` plugins should include this field in generated agent templates with role-appropriate defaults.

**Impact**: Encoding temperature recommendations in frontmatter makes the non-determinism control strategy visible, reviewable, and transferable across teams. Developers can see that the grader is configured for reproducibility and the architect for exploration, and modify these settings with understanding rather than guessing.

### 7.3 Recommendation 2: PostToolUse Output Validation Hooks

PostToolUse hooks can validate the content of files written or edited by agents before the session proceeds. This implements the structural validation layer from section 4.2 without requiring grammar-constrained decoding infrastructure — it is the API-level equivalent of GCD.

**Hook configuration pattern:**

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "event": "Write",
      "matcher": "*.c|*.h",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate-c-syntax.sh"
    },
    {
      "type": "PostToolUse",
      "event": "Write",
      "matcher": "*.overlay",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate-overlay.sh"
    }
  ]
}
```

**`validate-c-syntax.sh` pattern:**

```bash
#!/usr/bin/env bash
set -euo pipefail

FILE=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.path')

if ! gcc -fsyntax-only -x c - < "$FILE" 2>/dev/null; then
  echo "Syntax error in generated C file: $FILE" >&2
  echo "Correct the syntax error before proceeding." >&2
  exit 2  # Block and request correction
fi
```

**`validate-overlay.sh` pattern:**

```bash
#!/usr/bin/env bash
set -euo pipefail

FILE=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.path')

if ! dtc -I dts -O dts "$FILE" > /dev/null 2>&1; then
  echo "Invalid devicetree overlay syntax in: $FILE" >&2
  exit 2
fi
```

**Using PostToolUse `additionalContext`** (for non-blocking feedback):

When the output is plausible but warrants a note, PostToolUse hooks can append context rather than block:

```bash
# Return additionalContext via JSON stdout instead of exit 2
echo '{"additionalContext": "Warning: UART0 alias conflicts with SPI0 on nRF52840. Verify pin assignment before flashing."}'
```

This enriches the agent's context for subsequent decisions without interrupting the workflow.

**Why this matters for non-determinism**: Syntax validation hooks catch the most expensive class of non-deterministic failures — code that compiles on one run and doesn't on another due to a structural variation. By catching syntax errors immediately, they eliminate re-work and ensure the working context is always grounded in syntactically valid code.

### 7.4 Recommendation 3: Structured Grader Output Schemas

The grader agent currently produces human-readable markdown reports. For maximum reproducibility and programmatic processing, grader output should be schema-enforced JSON alongside the human-readable report.

**Proposed grader output schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema",
  "type": "object",
  "required": ["score", "grade", "checks", "critical_failures"],
  "properties": {
    "score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100
    },
    "grade": {
      "type": "string",
      "enum": ["S", "A", "B", "C", "D", "F"]
    },
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "status", "notes"],
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "status": {"enum": ["PASS", "FAIL", "WARN", "SKIP"]},
          "notes": {"type": "string"}
        }
      }
    },
    "critical_failures": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

A PostToolUse hook on the grader's JSON report file validates schema conformance:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPORT_FILE=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.path')

python3 -c "
import json, sys
with open('$REPORT_FILE') as f:
    data = json.load(f)
assert 'score' in data and isinstance(data['score'], int), 'score must be integer'
assert 'grade' in data and data['grade'] in ['S','A','B','C','D','F'], 'invalid grade'
assert 0 <= data['score'] <= 100, 'score out of range'
assert 'critical_failures' in data, 'critical_failures required'
" 2>&1 || { echo "Grader report does not conform to required schema" >&2; exit 2; }
```

**Why this matters for non-determinism**: Graders that produce unstructured text exhibit high output variance — the same code may receive a "7/10" one run and a "B+" another, described in incompatible terms. A structured schema forces the grader to map its assessment to fixed categories, making grades reproducible and comparable across runs. This directly implements the "constrained output space" principle from section 4.2 at the grader level.

### 7.5 Recommendation 4: Self-Consistency via Grader-as-Validator

Claude-kit's multi-agent architecture already separates the engineer (generates code) from the grader (evaluates code). This is structurally equivalent to a self-consistency mechanism where majority voting is replaced by an expert evaluation.

The enhancement is to make this validation **automatic** rather than user-initiated — the engineer's completion should trigger the grader as a Stop hook subagent:

**Stop hook pattern in engineer agent hooks:**

```json
{
  "hooks": [
    {
      "type": "Stop",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/auto-grade.sh",
      "description": "Grade engineer output before session ends"
    }
  ]
}
```

**`auto-grade.sh` pattern:**

```bash
#!/usr/bin/env bash
set -euo pipefail

CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null | grep -E '\.(c|h|overlay|conf)$' || true)

if [[ -z "$CHANGED_FILES" ]]; then
  exit 0  # Nothing to grade
fi

claude --model claude-haiku-4-6 \
  -k embedded-zephyr-grader \
  -p "Grade the following changed files and output a report.json per schema.
     Exit 2 if grade is F or any critical_failures exist.
     Files: $CHANGED_FILES"

GRADE_EXIT=$?

if [[ $GRADE_EXIT -eq 2 ]]; then
  echo "Grade F — engineer must fix critical failures before stopping." >&2
  exit 2
fi
```

**The grader as an external oracle**: This directly addresses the self-correction failure mode noted in section 4.4. The engineer cannot self-correct reliably (it tends to overthink correct code). But the grader, as an independent agent with its own context and role, provides genuine external feedback rather than the model evaluating its own output. This mirrors the "external oracle" that makes self-consistency effective — the oracle is the grader's rubric, not the model's own preferences.

**Cost consideration**: This doubles the compute per engineering session (one engineer + one grader pass). The Stop hook fires once per session, not once per file write, keeping the overhead manageable. For high-stakes firmware where a hardware bug means a physical device is damaged, this cost is trivially justified.

### 7.6 Recommendation 5: Determinism Budget per Task Class

Not all non-determinism is equal in cost. A framework for assigning **determinism budgets** by task class helps allocate control effort appropriately:

| Task class | Non-determinism cost | Control effort | Recommended controls |
|-----------|---------------------|----------------|---------------------|
| Safety-critical operations (flash, erase) | Catastrophic | Maximum | PreToolUse block + human confirmation |
| Build command construction | High | High | T=0, schema output, PostToolUse verify |
| Driver implementation | High | High | T=0.2, skills loaded, PostToolUse compile-check |
| Test scaffold generation | Moderate | Moderate | T=0.3, verify compilation |
| Code review comments | Low | Low | T=0.3, no validation needed |
| Architecture brainstorming | Low | Minimal | T=0.7, pure generation |
| Documentation | Low | Minimal | T=0.7, no validation |

**Encoding this in skill content**: Each domain skill should declare the task classes it covers and their associated determinism requirements. This makes the framework explicit and teachable to future agents:

```markdown
<!-- In embedded-zephyr-knowledge/zephyr-rtos/SKILL.md -->

## Task Determinism Requirements

| Task | Determinism tier | Validation |
|------|-----------------|------------|
| Peripheral initialization | High | Compile-check mandatory |
| RTOS thread creation | High | Data races are silent — verify thoroughly |
| Kconfig fragment | High | DTC validation mandatory |
| West build commands | High | Exact syntax — PostToolUse verify |
| Logging configuration | Low | Minor variation acceptable |
```

### 7.7 Recommendation 6: Skill Specificity as the Primary Control

The most impactful recommendation requires no new infrastructure: **continue deepening skill specificity as the dominant variance reduction strategy.**

The research is unequivocal: contextual knowledge overrides parametric knowledge (section 3.3 of `theory-context-cache.md`), and each specific fact in a skill exponentially reduces posterior variance (Arora et al., 2025). The practical implication:

**Every piece of implicit knowledge that currently lives in a developer's head should be in a skill.**

Specific patterns for skill content that most effectively reduce variance:

1. **Negative examples with reasons**: "Do NOT use `device_get_binding()` — this function is deprecated as of Zephyr 2.6. Always use `DEVICE_DT_GET()`. The deprecated function compiles but silently fails at runtime on newer kernels." Negative examples specifically suppress high-frequency wrong answers from the parametric distribution — the model's parametric memory is biased toward common patterns, and negative examples directly counter the most common mistakes.

2. **Exact API signatures**: Paste the full function signature including parameter types, return values, and error codes. Avoid prose descriptions like "takes a device struct and a callback." The model's parametric memory of API signatures degrades with time; explicit signatures prevent hallucinated parameter orders.

3. **Hardware constraints**: Pin conflicts, resource sharing, peripheral-exclusive relationships. These are high-entropy failure modes (many wrong configurations exist, only a few are correct) that skills can collapse to zero variance.

4. **Working code examples with exact syntax**: Examples that can be directly attended to during generation. Each example narrows the output distribution toward structurally similar outputs through the attention mechanism's preference for contextual over parametric knowledge.

5. **Enumerated valid options**: "Valid clock sources for UART are: HFCLK, PCLK, and LFCLK. Use HFCLK for baud rates above 9600." Bounded option sets eliminate the long tail of wrong answers that the model might plausibly generate from parametric memory.

**Quantifying the impact**: A skill that contains 20 specific, well-chosen facts provides exponential variance reduction across all tasks that involve those facts. At scale, a library of high-quality skills is more valuable for variance reduction than any sampling parameter configuration — because it addresses the root cause (wrong knowledge) rather than the symptom (varied outputs from wrong knowledge).

### 7.8 Summary: Non-Determinism Control Stack

The complete non-determinism control stack for claude-kit, ordered from most to least fundamental:

| Layer | Mechanism | Where in claude-kit | Status |
|-------|-----------|--------------------|----|
| **Context** | Skill injection narrows prior distribution | Knowledge plugins | Implemented |
| **Role** | Agent specialization narrows output space | Multi-agent architecture | Implemented |
| **Enforcement** | PreToolUse blocks unsafe operations | Plugin hooks | Implemented |
| **Sampling** | Temperature recommendations per role | Agent frontmatter field | Recommended (§7.2) |
| **Structural validation** | PostToolUse hooks validate syntax | Plugin hooks | Recommended (§7.3) |
| **Schema enforcement** | Structured grader output | Grader schema + hook | Recommended (§7.4) |
| **External consistency** | Grader-as-validator on Stop | Stop hook auto-grading | Recommended (§7.5) |
| **Task budgeting** | Determinism effort by task class | Skill content declarations | Recommended (§7.6) |
| **Knowledge depth** | Deeper, more specific skill content | Skill authoring discipline | Ongoing |
| **Measurement** | SCE/JSD/pass@k tracking | Test suite (proposed) | Not yet implemented |

**Where to start**: Of the recommendations above, §7.3 (PostToolUse output validation) provides the highest variance-reduction-to-implementation-effort ratio. Syntax validation scripts are simple to write, immediately catch the most common failure modes (syntactically invalid code that wastes human review time), and compose well with existing hook infrastructure. A single `validate-c-syntax.sh` script in the embedded-zephyr-engineer plugin would be immediately useful.

**The ceiling**: Even with all recommendations implemented, some irreducible non-determinism remains — the hardware and infrastructure sources described in sections 2.2 through 2.6 are outside user control when using API-based inference. The goal is not zero variance but **managed variance** — variance that is concentrated in low-stakes decisions and minimized for high-stakes ones. Claude-kit's layered control stack achieves exactly this, addressing non-determinism at every layer the user can control.

---

---

## 8. Sources

### Non-Determinism: Root Causes and Measurement

- Song, Yifan et al. (2025). "The Good, The Bad, and The Greedy: Evaluation of LLMs Should Not Ignore Non-Determinism." NAACL 2025. [ACL Anthology](https://aclanthology.org/2025.naacl-long.211/)

- Thinking Machines Lab (2025). "Defeating Nondeterminism in LLM Inference." [Blog post](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/); OpenAI Community discussion [here](https://community.openai.com/t/defeating-nondeterminism-in-llm-inference/1358623)

- arXiv:2506.09501 (2025). "Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference." [NeurIPS 2025 poster](https://neurips.cc/virtual/2025/poster/118169); [arXiv](https://arxiv.org/abs/2506.09501); [OpenReview](https://openreview.net/forum?id=Q3qAsZAEZw)

- arXiv:2408.04667 (2024). "Non-Determinism of 'Deterministic' LLM Settings." [arXiv HTML](https://arxiv.org/html/2408.04667v5); ACL Anthology version [here](https://aclanthology.org/2025.eval4nlp-1.12/)

- arXiv:2508.14288 (2025). "Measuring LLM Code Generation Stability via Structural Entropy." [arXiv](https://arxiv.org/abs/2508.14288); [HTML](https://arxiv.org/html/2508.14288v1)

- arXiv:2601.17768 (2025). "LLM-42: Enabling Determinism in LLM Inference with Verified Speculation." [arXiv HTML](https://arxiv.org/html/2601.17768)

- arXiv:2511.17826 (2025). Nondeterminism and batch invariance analysis. [arXiv](https://arxiv.org/html/2511.17826)

- LMSYS Org (2025). "Towards Deterministic Inference in SGLang and Reproducible RL Training." [LMSYS blog](https://lmsys.org/blog/2025-09-22-sglang-deterministic/)

- arXiv:2509.09705 (2025). "The Non-Determinism of Small LLMs: Evidence of Low Answer Consistency in Repetition Trials of Standard Multiple-Choice Benchmarks." [arXiv HTML](https://arxiv.org/html/2509.09705v1)

- Mikulski, Bartosz (2024). "The Temperature=0 Myth: Why Your LLM Still Isn't Deterministic." [Blog](https://mikulskibartosz.name/why-temperature-0-isnt-deterministic)

- Schmalbach, Vincent (2024). "Does Temperature 0 Guarantee Deterministic LLM Outputs?" [Blog](https://www.vincentschmalbach.com/does-temperature-0-guarantee-deterministic-llm-outputs/)

- Sugiv Blog (2024). "Unmasking the True Culprit: Why Temperature=0 Doesn't Mean Deterministic LLM Inference." [Blog](https://blog.sugiv.fyi/temperature-determinism-llm-inference)

### Constrained Decoding and Structured Outputs

- arXiv:2411.15100 (2024). "XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models." [arXiv](https://arxiv.org/abs/2411.15100); [PDF](https://arxiv.org/pdf/2411.15100); [MLC blog](https://blog.mlc.ai/2024/11/22/achieving-efficient-flexible-portable-structured-generation-with-xgrammar); [GitHub](https://github.com/mlc-ai/xgrammar)

- guidance-ai/llguidance (2024). "Super-fast Structured Outputs." [GitHub](https://github.com/guidance-ai/llguidance)

- arXiv:2405.21047 (2024). "Grammar-Aligned Decoding." [arXiv](https://arxiv.org/abs/2405.21047); [OpenReview](https://openreview.net/forum?id=5G7ve8E1Lu)

- ICML 2025. "Flexible and Efficient Grammar-Constrained Decoding." [ICML virtual poster](https://icml.cc/virtual/2025/poster/45613); [OpenReview](https://openreview.net/forum?id=L6CYAzpO1k)

- arXiv:2305.13971 (2023). "Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning." [arXiv](https://arxiv.org/abs/2305.13971)

- arXiv:2501.10868 (2025). "Generating Structured Outputs from Language Models: Benchmark and Studies." [arXiv HTML](https://arxiv.org/html/2501.10868v1)

- dottxt-ai/outlines. "Structured Outputs." [GitHub](https://github.com/dottxt-ai/outlines)

- Cooper, Aidan (2024). "A Guide to Structured Generation Using Constrained Decoding." [Blog](https://www.aidancooper.co.uk/constrained-decoding/)

- Nambiar, Brijesh (2024). "Beyond Free-Form Text: How Constrained Decoding is Reshaping Structured Generation in LLMs." [Medium](https://medium.com/@brijeshrn/beyond-free-form-text-how-constrained-decoding-is-reshaping-structured-generation-in-llms-5f7a38bef259)

- Saibo-creator. "Awesome-LLM-Constrained-Decoding." [GitHub curated list](https://github.com/Saibo-creator/Awesome-LLM-Constrained-Decoding)

- SqueezeBits (2024). "Guided Decoding Performance on vLLM and SGLang." [Blog](https://blog.squeezebits.com/guided-decoding-performance-vllm-sglang)

### Self-Consistency and Evaluation

- Wang et al. (2023). "Self-Consistency Improves Chain of Thought Reasoning in Language Models." ICLR 2023. [Proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/file/8b4add8b0aa8749d80a34ca5d941c355-Paper-Conference.pdf)

- arXiv:2505.10772 (2025). "Ranked Voting based Self-Consistency of Large Language Models." [arXiv HTML](https://arxiv.org/html/2505.10772v1); [ACL Anthology](https://aclanthology.org/2025.findings-acl.744.pdf)

- ACL Anthology (2024). "Mirror-Consistency: Harnessing Inconsistency in Majority Voting." EMNLP 2024. [PDF](https://aclanthology.org/2024.findings-emnlp.135.pdf)

- ACL Anthology (2025). "Leveraging Reasoning Paths for Efficient LLM Sampling." NAACL 2025. [PDF](https://aclanthology.org/2025.naacl-long.184.pdf)

- arXiv:2510.17472 (2025). "Certified Self-Consistency: Statistical Guarantees and Test-Time Compute." [arXiv](https://arxiv.org/pdf/2510.17472)

- Chen et al. (2021). "Evaluating Large Language Models Trained on Code" (HumanEval, pass@k). arXiv:2107.03374

- arXiv:2310.14053 (2023). "Evaluating Self-Consistency of Code Large Language Models." [NSF](https://par.nsf.gov/servlets/purl/10523084); [arXiv](https://arxiv.org/pdf/2310.14053)

### Temperature, Sampling, and Decoding Strategies

- arXiv:2402.05201 (2024). "The Effect of Sampling Temperature on Problem Solving in Large Language Models." [PDF](https://arxiv.org/pdf/2402.05201)

- arXiv:2402.06925 (2024). "A Thorough Examination of Decoding Methods in the Era of LLMs." [arXiv HTML](https://arxiv.org/html/2402.06925v3)

- arXiv:2407.1082 (2024). "Min-p Sampling for Creative and Coherent LLM Outputs." [PDF](https://arxiv.org/pdf/2407.1082); [ICLR 2025 version](https://arxiv.org/pdf/2402.05864)

- Mlabonne (2024). "Decoding Strategies in Large Language Models." [Hugging Face blog](https://huggingface.co/blog/mlabonne/decoding-strategies)

- Promptfoo (2024). "How to Choose the Right LLM Temperature Setting." [Docs](https://www.promptfoo.dev/docs/guides/evaluate-llm-temperature/)

### Context Engineering

- arXiv:2507.13334 (2025). "A Survey of Context Engineering for Large Language Models." [arXiv](https://arxiv.org/abs/2507.13334); [HTML](https://arxiv.org/html/2507.13334v1)

- arXiv:2510.04618 (2025). "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models." [arXiv](https://arxiv.org/abs/2510.04618); [HTML](https://arxiv.org/html/2510.04618v1)

- Arora et al. (2025). "In-Context Learning Is Provably Bayesian Inference." arXiv:2510.10981

- arXiv:2503.20561 (2025). "Theoretical Framework for Prompt Engineering: Transformers as Configurable Computational Systems."

### Validation Libraries

- 567-labs/instructor (2024). "Structured Outputs for LLMs." [GitHub](https://github.com/567-labs/instructor); [Docs](https://python.useinstructor.com/); [Retry mechanisms](https://python.useinstructor.com/learning/validation/retry_mechanisms/)

- Pydantic AI (2024). Pydantic-native structured extraction. [Pydantic docs](https://pydantic.dev/articles/llm-intro)

### Claude Code Hooks

- Anthropic (2025). "Automate workflows with hooks." [Claude Code Docs](https://code.claude.com/docs/en/hooks-guide)

- Anthropic (2025). "Intercept and control agent behavior with hooks." [Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/hooks)

- Kinney, Steve (2025). "Claude Code Hook Control Flow." [Course notes](https://stevekinney.com/courses/ai-development/claude-code-hook-control-flow)

### Agent Evaluation

- DEV Community (2026). "Deterministic vs. LLM Evaluators: A 2026 Technical Trade-off Study." [Dev.to](https://dev.to/anshd_12/deterministic-vs-llm-evaluators-a-2026-technical-trade-off-study-11h)

- arXiv:2507.21504 (2025). "Evaluation and Benchmarking of LLM Agents: A Survey." [arXiv HTML](https://arxiv.org/html/2507.21504v1)

- arXiv:2506.18824 (2025). "Understanding Software Engineering Agents: A Study of Thought-Action-Result Trajectories." [arXiv HTML](https://arxiv.org/html/2506.18824v1)
