# Formal Intent Interfaces — From Ambiguous Language to Precise Specification

> A design research document exploring the spectrum from natural language prompts
> to formal specification languages, and what this means for building reliable
> intent routing in AI plugin systems like claude-kit.

**Date:** 2026-02-28

---

## Table of Contents

1. [The Core Problem: Intent Is Not Instruction](#1-the-core-problem-intent-is-not-instruction)
2. [The Spectrum: Natural Language to Formal Specification](#2-the-spectrum-natural-language-to-formal-specification)
3. [Prompt Engineering as Interface Design](#3-prompt-engineering-as-interface-design)
4. [Emerging DSLs and Structured Interfaces for AI](#4-emerging-dsls-and-structured-interfaces-for-ai)
5. [Intent Routing Systems](#5-intent-routing-systems)
6. [Specification Languages for Agent Behavior](#6-specification-languages-for-agent-behavior)
7. [Implications for claude-kit](#7-implications-for-claude-kit)
8. [Sources](#sources)

---

## 1. The Core Problem: Intent Is Not Instruction

A user says: "Make me a great website."

This sentence has a subject, a verb, an object, and an adjective. It is
grammatically complete. And it is essentially useless as a specification for an
AI agent. It contains no constraints. It supplies no success criteria. The word
"great" is entirely in the eye of the beholder. There is no definition of
"website" that would distinguish the user's mental model from the infinite set
of things that could plausibly be called a website.

This is the **intent gap**: the distance between what a user means and what an
AI system can reliably execute. Closing this gap is one of the most consequential
engineering problems in AI systems design.

The podcast observation that framed this research states it precisely:

> "Moving beyond ambiguous natural language prompts — instead of 'make me a
> great website,' the interface would make you specify it almost like a legal
> contract: build a site that achieves X functionality, adheres to Y ethical
> boundaries on user data, and must never violate Z regulatory rule."

This "legal contract" framing is not hyperbole. It is a design principle. Legal
contracts are formal specifications: they define parties, obligations, scope,
constraints, and enforcement mechanisms. A well-designed intent interface does
the same.

The question for systems like claude-kit is not whether to formalize intent —
the value of doing so is clear — but *how much formalism is appropriate* at each
layer of the system.

### 1.1 Why Natural Language Fails as a Specification Language

Natural language has three properties that make it powerful for human
communication and dangerous for machine interpretation:

**Ambiguity.** The same sentence can mean different things in different contexts.
"Make the header bigger" could mean increasing font size, increasing padding,
making the header element taller, or increasing the visual weight through color
contrast. All are valid readings. None is specified.

**Underspecification.** Sentences routinely omit information the speaker considers
obvious but the listener (or machine) cannot infer. "Add authentication" omits:
which provider? Which method? Sessions or JWTs? What happens on failure?

**Pragmatic drift.** The meaning of an utterance depends on shared context,
social conventions, and discourse history that are difficult to formalize and
highly variable. Research at ICLR 2026 (Ambig-SWE) found that real-world
agentic tasks involve "multiple, interdependent gaps in specification that emerge
over the course of a trajectory" — ambiguities compound as work proceeds.

These properties are not bugs in natural language. They make conversation
efficient between humans who share enormous amounts of implicit context. They
become bugs when the receiver is an agent that cannot reliably infer what was
left implicit.

### 1.2 Why Full Formalism Also Fails

At the other extreme, requiring users to write formal specifications before an
AI system acts creates an unusable system. The Z notation, TLA+, and Alloy model
checking languages can express precise system behavior — but they require
expertise most developers do not have, and producing a formal specification
often takes longer than implementing the system it specifies.

The practical space lies between these extremes: interfaces that are more
precise than raw natural language but more accessible than formal verification
languages. Understanding the full spectrum is required before choosing where to
land.

---

## 2. The Spectrum: Natural Language to Formal Specification

### 2.1 The Flexibility-Precision Tradeoff

The tradeoff can be visualized as a continuum:

```
High Flexibility ←————————————————————————————→ High Precision
Natural      Structured    DSL for AI    Contract      Formal
Language     Templates     (LMQL, DSPy)  Interfaces    Spec (LTL, Z)
   |              |              |             |             |
"make me a    "Build a {type} "query          preconditions  ∀s ∈ States:
great         site with       LLM where       + invariants   φ(s) → □ψ(s)
website"      {features}      CONSTRAINS      + postcond.
              supporting      format"
              {auth method}"
```

| Point on Spectrum | Flexibility | Precision | Authoring Cost | Example |
|---|---|---|---|---|
| Raw natural language | Maximum | Minimum | Trivial | "build a REST API" |
| Structured template | High | Low-medium | Low | "build a {type} API with {auth}" |
| Few-shot examples | High | Medium | Medium | Show 3 examples of desired output |
| Constrained prompt (DSL) | Medium | High | Medium | LMQL, Guidance programs |
| Schema-typed output | Medium | High | Medium | TypeChat, Instructor + Pydantic |
| Contract interface | Low-medium | High | High | pre/postconditions + invariants |
| Temporal logic | Low | Very high | Very high | LTL formulas |
| Full formal spec | Minimum | Maximum | Very high | Z notation, Alloy |

No single point dominates. A well-designed intent interface chooses the
appropriate level for the task — and often layers multiple levels.

### 2.2 Natural Language (Fully Flexible, Fully Ambiguous)

Raw natural language as an AI interface is the status quo for most consumer
AI products. Its failure modes are well-documented: the system guesses what
was meant, gets it wrong, and the user iterates by providing clarification —
which is itself natural language, and equally ambiguous.

For interactive consumer tasks where failure is cheap and iteration is fast,
this works. For agentic systems where the agent takes real actions (writes
files, makes API calls, triggers CI, deploys to production), the cost of a
wrong interpretation compounds with each action.

**Practical failure mode in claude-kit context:** A user says "clean up the
plugin" to an engineer agent. Does this mean: refactor the code? Rename files
to be more consistent? Remove dead agents? Improve the README? Reduce file
count? All are valid interpretations. An agent that guesses wrong and takes
destructive action has caused harm that may be difficult to undo.

### 2.3 Structured Prompts with Templates and Slots

The simplest step toward formalization is the **template with slots**: a
natural-language prompt that contains explicit placeholders the user must fill.
This is the insight behind modern prompt template libraries (LangChain prompt
templates, LangSmith hub, etc.).

```
You are building a {language} {framework} API that:
- Handles {description of core functionality}
- Uses {auth_method} for authentication
- Returns errors as {error_format}
- Must not: {explicit prohibitions}
```

This approach:
- Forces the user to make explicit decisions they would otherwise leave implicit
- Makes the prompt reusable and testable across different inputs
- Provides a structured interface that can be validated (are all slots filled?)
- Still relies on natural language within each slot, so ambiguity is
  reduced but not eliminated

Research at Stanford's 2024 analysis of real-world LLM applications found that
"From Prompts to Templates" — a systematic analysis of thousands of production
prompts — shows that the most successful production prompts consistently use
structured templates with explicit variable slots rather than monolithic
natural-language descriptions.

### 2.4 DSLs for AI (Domain-Specific Languages for Intent Expression)

The next step is purpose-built languages designed for expressing intent to AI
systems. These are not general programming languages, nor are they natural
language — they occupy the middle ground, with syntax designed for clarity and
constraints designed for precision.

DSLs for AI are covered in depth in Section 4, since they represent an active
and rapidly evolving research frontier. The key properties that distinguish an
AI DSL from a template:

- **Typed variables** — slots have types, not just string placeholders
- **Constraints embedded in syntax** — the language itself enforces restrictions
- **Composability** — programs can be built from reusable components
- **Computable semantics** — the intent can be partially verified before execution

### 2.5 Contract-Based Interfaces

Design by Contract (DbC) — introduced by Bertrand Meyer in Eiffel — specifies
software components through three kinds of assertions:

- **Preconditions** — what must be true before the operation runs
- **Postconditions** — what must be true after the operation completes
- **Invariants** — what must remain true throughout (class/session state)

Applied to AI agents, this maps naturally:

```
agent: code-reviewer
preconditions:
  - target_file must exist and be readable
  - file must be in a supported language (Python, TypeScript, Go)
  - file must not exceed 1000 lines (scope limit)
postconditions:
  - output must include: summary, findings[], severity for each finding
  - output must not include: suggested code rewrites (that's the engineer's job)
  - output must cite specific line numbers for each finding
invariants:
  - reviewer never modifies any file
  - reviewer never executes any code
  - reviewer must maintain grader role separation
```

This is more formal than a template but more readable than temporal logic. It
is also *executable*: hooks can enforce preconditions before the agent runs
and postconditions after it completes.

Recent research (2025) has formalized this for AI systems: Agent Behavioral
Contracts (ABC, arXiv:2602.22302) define "preconditions and postconditions over
individual LLM calls" and implement them in `AgentAssert`, a runtime enforcement
library evaluated on a 200-scenario benchmark across 7 models.

### 2.6 Formal Specifications (LTL, CTL, Z, Alloy)

At the high end of precision:

**Linear Temporal Logic (LTL)** expresses properties that must hold across time:

```
□(action = "deploy" → ○(tests_pass ∧ ¬security_violations))
```

"It is always the case that if an action is a deploy, then in the next state
tests must pass and there must be no security violations."

**Z Notation** uses set theory and predicate logic to specify state and
operations precisely:

```
ReviewOperation
  ΔReviewState
  file?: FileName
  findings!: ℙ Finding
─────────────────────
  file? ∈ readable_files ∧ lines(file?) ≤ 1000
  findings! = {f : Finding | severity(f) ≥ threshold ∧ location(f) ∈ file?}
  state' = state ∪ {reviewed ↦ file?}
```

**Alloy** uses relational first-order logic and supports automated model
checking — you can verify that a specification has no contradictions before
implementation.

**When are these practical?** Research is clear: formal specs are practical when:
- The cost of specification errors is very high (safety-critical, regulatory)
- The domain is bounded (a specific protocol, not a general-purpose agent)
- A formal methods expert is available to write and maintain the spec
- The spec can be used for automated verification, not just documentation

For a plugin management system like claude-kit, full formal specs for most
agent behaviors are impractical. However, LTL is increasingly practical for
expressing *policy constraints* on agent behavior — particularly when combined
with LLM-assisted translation (NL2Spec, lang2LTL) that converts natural
language requirements into formal logic.

---

## 3. Prompt Engineering as Interface Design

Prompt engineering is often discussed as if it is merely the art of getting
better outputs from LLMs by clever phrasing. At a deeper level, it is an
**interface design discipline** — one concerned with how intent is communicated
across the boundary between human and machine cognition.

### 3.1 Chain-of-Thought Prompting as Intent Decomposition

Chain-of-thought (CoT) prompting, introduced by Wei et al. (2022) and
systematically studied through 2023-2024, asks the model to show its reasoning
before producing an answer. The key interface-design insight is not that CoT
improves output quality (though it does) — it is that **CoT makes implicit
reasoning explicit**.

When a user asks "What's the best database for my app?" without CoT, the model
produces an answer based on opaque internal reasoning. With CoT, the model is
forced to articulate: "First, let me understand the scale requirements. Second,
let me consider the access patterns. Third, let me evaluate consistency vs
availability tradeoffs..." Each reasoning step is a decomposed sub-intent.

This has two interface design implications:

1. **Intent decomposition is inspectable.** When something goes wrong, you can
   see which reasoning step failed rather than debugging a black box.
2. **Decomposed intents can be formally specified.** Once you know the model
   will reason about "scale requirements" and "access patterns" as distinct
   steps, you can provide structured information for each step.

CoT evolved into **structured Chain-of-Thought** — where the reasoning steps
are specified in advance, turning the chain into a template with mandatory slots:

```xml
<reasoning>
  <requirements>What are the functional requirements?</requirements>
  <constraints>What are the hard constraints?</constraints>
  <tradeoffs>What are the key tradeoffs?</tradeoffs>
  <decision>Final recommendation with justification</decision>
</reasoning>
```

This bridges natural language and formal interface: the structure is specified,
the content is natural language, and the overall format is machine-parseable.

### 3.2 ReAct: Externalizing Intent as a Trace

ReAct (Reasoning + Acting, Yao et al., 2023) represents a significant step
toward formal intent expression. The key insight is that **intent is not static
— it is a sequence of observations and decisions over time**.

ReAct's format:

```
Thought: I need to check if the test file exists before running it
Action: Read[tests/test_parser.py]
Observation: File exists, 247 lines, uses pytest
Thought: The test file exists. Now I should check the imports match
Action: Grep[from parser import, tests/]
Observation: Found 3 import statements matching the module interface
Thought: Imports match. Running tests now.
Action: Bash[pytest tests/test_parser.py -v]
```

Each Thought-Action-Observation triple is a formal event. The trace is:
- **Inspectable** — any step can be reviewed
- **Interruptible** — hooks can intervene between steps
- **Reproducible** — the same sequence can be replayed
- **Auditable** — intent is recorded, not just outcomes

The interface design implication: a well-specified intent interface should
produce a ReAct-style trace, not a blob of text. The trace format is itself
a specification of how intent is to be pursued.

### 3.3 Few-Shot Prompting as Implicit Specification

Few-shot prompting is often discussed as a technique for improving output
quality. From an interface design perspective, it is something more specific:
**implicit specification through examples**.

When you provide 3 examples of how a code review should be formatted, you are
not just improving the model's output quality — you are specifying a
*behavioral contract* through demonstration rather than declaration:

```
# Implicit specification via examples:
Input: <code snippet>
Output:
  Summary: [one sentence]
  Findings:
  - Line 12: [severity: HIGH] Missing input validation on user_id
  - Line 34: [severity: LOW] Unused import
  Verdict: [APPROVE | REQUEST_CHANGES | REJECT]
```

Three examples communicate the schema, the severity levels, the field names,
and the output format — without ever writing a JSON schema. This is implicit
specification.

**Limitation:** Implicit specification is ambiguous in exactly the ways that
matter for edge cases. The examples show what the system *does*; they do not
show what the system *must not do*. Specification by example cannot express
prohibitions without enumerating them — which requires either many examples
or explicit constraints.

**Many-Shot In-Context Learning** (Google, NeurIPS 2024) extended this to
hundreds or thousands of examples, showing significant performance gains.
But the fundamental limitation remains: examples specify by inclusion (this
is what a good output looks like) but cannot easily specify by exclusion
(here is every thing that must never appear in the output).

### 3.4 Constitutional AI as Embedded Intent Specification

Anthropic's Constitutional AI (CAI, Bai et al., 2022) is a system for
embedding value specifications into a model's behavior through a set of
principles — a "constitution" — that guides both training and inference.

From an interface design perspective, CAI is **declarative intent specification
at training time**: rather than specifying output format or domain knowledge,
it specifies *values and constraints* that must hold across all outputs.

The constitution takes the form of a list of principles such as:
- "Choose the response that is least likely to contain harmful or unethical content"
- "Choose the response that is most supportive of the rule of law and democratic institutions"
- "Choose the response that has the least potential to be used to undermine safety"

Key properties as an intent specification mechanism:

| Property | Constitutional AI | Formal Specification |
|---|---|---|
| **Expressiveness** | High (natural language) | Very high (formal) |
| **Verifiability** | Low (soft guidance) | High (mechanically checkable) |
| **Coverage** | Broad principles | Specific behaviors |
| **Maintenance** | Low (principles rarely change) | High (formal specs brittle) |
| **Interpretability** | High (human-readable) | Medium (requires expertise) |

**Limitations acknowledged by Anthropic:** "There are a million things that you
can have values about and you're never going to be able to enumerate them all
in text." Constitutional AI addresses general value alignment — it cannot
specify precise functional behavior. It is a complement to, not a replacement
for, behavioral specification.

The public Collective Constitutional AI work (2024) extended this further:
using deliberation processes to crowdsource the constitution itself, making
the specification process participatory rather than top-down.

### 3.5 Meta-Prompting and Prompt Programs

Meta-prompting (Suzgun et al., 2024; Zhang et al., 2024) treats the LLM as
a **prompt generator** — the model is given a high-level task description and
asked to produce specialized prompts for sub-problems. This creates a
two-level intent structure:

```
Level 1: "Analyze this codebase for security vulnerabilities"
↓ [Meta-prompt generates specialized prompts]
Level 2a: "Scan for SQL injection vulnerabilities using this checklist..."
Level 2b: "Check authentication flows against OWASP top 10..."
Level 2c: "Identify exposed secrets using this pattern list..."
```

The interface design implication is profound: **complex intent can be
recursively decomposed into progressively more specific sub-intents**. The
meta-prompt is the high-level specification; the generated prompts are the
operational specifications.

TextGrad (2025, published in Nature) extended this with natural language
gradients — feedback about what went wrong with a prompt is itself expressed
in natural language, and this feedback is used to improve the prompt
automatically. The optimization loop is: prompt → output → critique in
natural language → revised prompt. This is differentiable programming for
intent specification.

DSPy (Section 4.3) formalizes this further as program optimization, where
the prompts themselves are treated as parameters to be optimized against a
metric.

---

## 4. Emerging DSLs and Structured Interfaces for AI

### 4.1 LMQL — Language Model Query Language

**What it is:** LMQL is a programming language for LLM interaction that
combines declarative SQL-like elements with imperative Python scripting.
Introduced in the PLDI 2023 paper "Prompting Is Programming" (Beurer-Kellner
et al., 2023, arXiv:2212.06094).

**Core idea:** Instead of sending a monolithic prompt string to an LLM, you
write a *program* that interleaves generation, constraints, and control flow:

```python
@lmql.query
def analyze_code(file_contents):
  '''lmql
  "Analyze this code for issues:\n{file_contents}\n"
  "Category (security|performance|style): [CATEGORY]"
  where CATEGORY in ["security", "performance", "style"]
  "Severity (1-5): [SEVERITY]"
  where INT(SEVERITY) and 1 <= int(SEVERITY) <= 5
  "Finding: [FINDING]"
  where len(FINDING) < 200
  '''
```

**Key capabilities:**
- `where` clauses constrain generation at token level — the model cannot
  produce a CATEGORY value outside the allowed set
- Typed constraints (`INT(SEVERITY)`) enforce data types
- Length constraints prevent runaway outputs
- Speculative execution with constraint short-circuiting reduces token waste
  by 75-85% vs. unconstrained prompting

**Interface design significance:** LMQL demonstrates that **the prompt is a
program, not a string**. Constraints are first-class language constructs,
not ad-hoc text. This closes the gap between "ask the model nicely" and
"enforce the model's output structure".

**Current status:** LMQL moved to a community GitHub organization in 2024
(lmql-lang). The research produced at ETH Zurich remains influential, and
similar constraint systems have been incorporated into Guidance and Outlines.

### 4.2 Guidance — Programs That Control LLM Generation

**What it is:** Guidance (Microsoft Research, 2023-ongoing) is a library for
controlling LLM outputs by enforcing constraints at the generation layer —
token by token — rather than by post-processing.

```python
import guidance

@guidance
def review_finding(lm, severity_levels):
    lm += f"""
    Finding: {guidance.gen('description', max_tokens=100)}
    Severity: {guidance.select(severity_levels, name='severity')}
    Line: {guidance.gen('line_number', regex=r'[0-9]+')}
    """
    return lm

result = review_finding(lm, severity_levels=["LOW", "MEDIUM", "HIGH", "CRITICAL"])
```

**Interface design significance:** Guidance operates at a fundamentally
different layer than prompt templates. Instead of asking the model to produce
output in a certain format (and hoping it complies), Guidance **steers the
model's token selection** so that non-conforming outputs are physically
impossible.

This is the difference between:
- **Soft constraints:** "Please output JSON" (model may or may not comply)
- **Hard constraints:** The token mask at each step eliminates all tokens
  that cannot appear in valid JSON (model cannot produce non-JSON)

**llguidance** (2024) extended this to support arbitrary context-free grammars
with essentially zero startup costs. XGrammar (CMU/MLC, 2024) achieved token
mask generation in under 40 microseconds per token, making grammar-constrained
generation production-feasible.

**Benchmark data (2025):** Evaluated on JSONSchemaBench (10K real-world JSON
schemas from function signatures, service APIs, system configurations), Guidance
showed the highest empirical coverage on 6 of 8 datasets.

| Framework | Primary Constraint Model | Overhead |
|---|---|---|
| Guidance | Context-free grammar | Low |
| Outlines | Finite-state automata from regex/schema | Very Low |
| XGrammar | Context-free grammar with predictive mask | Near zero |
| llguidance | LALR(1) pushdown automata | Near zero |
| OpenAI Structured Outputs | JSON Schema (server-side) | Zero (client) |

### 4.3 DSPy — Treating LM Pipelines as Programs

**What it is:** DSPy (Khattab et al., Stanford, ICLR 2024, arXiv:2310.03714)
is a framework that replaces hand-crafted prompts with **declarative modules
that carry typed signatures**, then automatically optimizes those modules.

**Core abstraction — the Signature:**

```python
class CodeReview(dspy.Signature):
    """Review code for issues and provide structured feedback."""
    code = dspy.InputField(desc="The code to review")
    language = dspy.InputField(desc="Programming language")

    summary = dspy.OutputField(desc="One-sentence summary of code quality")
    findings = dspy.OutputField(desc="List of specific issues found")
    verdict = dspy.OutputField(desc="APPROVE, CHANGES_REQUESTED, or REJECT")

reviewer = dspy.ChainOfThought(CodeReview)
```

The signature is a **typed interface contract**: inputs have descriptions,
outputs have descriptions, and the relationship between them is specified.
DSPy then compiles this specification into effective prompts automatically.

**Why this matters for intent formalization:**

1. **Signatures separate intent from implementation.** The developer specifies
   what they want (the interface) — DSPy figures out how to get it (the prompt).
2. **Optimization against a metric.** Given a validation metric and training
   examples, DSPy compiles the pipeline — bootstrapping few-shot examples,
   tuning instructions, even fine-tuning small models for sub-steps.
3. **Measured results:** GPT-3.5 with DSPy-optimized pipelines outperformed
   standard few-shot prompting by over 25%; Llama 2 13B outperformed by over
   65% on the same benchmarks.

**The key insight as interface design:** DSPy decouples the **specification of
what should happen** (signatures) from the **mechanism that makes it happen**
(prompts). The signature is a formal interface contract; the prompt is an
implementation detail managed by the compiler.

### 4.4 TypeChat — TypeScript Types as Intent Specification

**What it is:** TypeChat (Microsoft, 2023, designed by Anders Hejlsberg —
creator of TypeScript and C#) uses **TypeScript type definitions** as the
specification language for LLM outputs.

```typescript
// The developer writes this type:
interface RestaurantOrder {
  items: Array<{
    name: string;
    quantity: number;
    specialRequests?: string;
  }>;
  tableNumber: number;
  isDelivery: boolean;
  totalWithTax: number;
}

// TypeChat sends the type to the LLM, asks it to produce conforming JSON,
// validates against the type, and retries if validation fails.
```

**Interface design significance:** TypeScript types are already a specification
language that millions of developers know. TypeChat's insight is that **the
interface definition IS the specification** — no separate formal spec required.
If you can type it, you can constrain the LLM to it.

TypeChat's mechanism:
1. Convert the TypeScript type to a JSON Schema
2. Construct a prompt that includes the type and asks for a conforming response
3. Parse the LLM response as JSON
4. Validate against the schema
5. If validation fails, send the validation errors back to the LLM for repair

The repair loop makes TypeChat **self-correcting**: validation failures become
feedback that drives the model toward compliance, without requiring the
developer to handle failures manually.

### 4.5 Semantic Kernel — Typed Intent Expression

**What it is:** Microsoft's Semantic Kernel (2023-ongoing) is an AI
orchestration framework that treats LLM capabilities as **typed kernel
functions** — similar to OS system calls — with strongly-typed signatures.

```csharp
[KernelFunction("review_code")]
[Description("Review code for quality issues")]
public async Task<ReviewResult> ReviewCodeAsync(
    [Description("The code to review")] string code,
    [Description("The programming language")] string language,
    [Description("Maximum severity to flag")] Severity minSeverity = Severity.Low)
{
    // The kernel handles prompt construction, LLM invocation,
    // and response parsing automatically
}
```

**Interface design significance:** Semantic Kernel treats AI as an extension of
traditional software architecture. Functions have typed parameters, return
typed results, and can be composed into pipelines with dependency injection.
The type system enforces intent at the API level.

In 2025, Microsoft merged Semantic Kernel with AutoGen into the **Microsoft
Agent Framework** — recognizing that orchestration (Semantic Kernel) and
multi-agent coordination (AutoGen) are the same problem at different scales.

### 4.6 Instructor and Marvin — Structured Output Extraction

**Instructor** (Jason Liu, 2023-ongoing) is the most widely adopted Python
library for structured LLM output extraction, with 3M+ monthly downloads and
support for 15+ providers.

```python
from pydantic import BaseModel, Field
from typing import Literal
import instructor

class ReviewFinding(BaseModel):
    line_number: int = Field(ge=1, description="Line where the issue appears")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    category: Literal["security", "performance", "style", "correctness"]
    description: str = Field(max_length=200)

class CodeReview(BaseModel):
    summary: str = Field(max_length=100)
    findings: list[ReviewFinding]
    verdict: Literal["APPROVE", "CHANGES_REQUESTED", "REJECT"]

client = instructor.from_anthropic(anthropic.Anthropic())
review = client.messages.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": f"Review this code: {code}"}],
    response_model=CodeReview,
)
```

The Pydantic model is the specification: field types, constraints (`ge=1`),
enumerations of allowed values, and length limits are all expressed as
Python type annotations. Instructor enforces compliance through retry loops
with validation error feedback.

**Marvin** (Prefect, 2023-ongoing) takes a higher-level approach, providing
built-in tasks for common extraction patterns (`cast`, `classify`, `extract`,
`generate`) with minimal boilerplate, but with less flexibility and
single-provider (OpenAI) support.

**Interface design significance of both:** Pydantic models and TypeScript types
represent a **type-first specification approach** where the output contract is
defined in the developer's native type system, not in a separate specification
language. This dramatically lowers the barrier to formalization.

---

## 5. Intent Routing Systems

### 5.1 The Routing Problem

Intent routing is the problem of mapping a natural language utterance to the
correct handler. In claude-kit, this means mapping a user message like "I want
to instrument this repo for AI development" to the correct skill or command
(`core-kit:instrument`). The routing system is essentially an intent
classification system with some slot-filling.

The problem is harder than it appears because:
- Users express the same intent in wildly different ways
- The same words can express different intents in different contexts
- New intents may appear that were not anticipated at design time
- The system must handle partial matches and disambiguation

### 5.2 Intent Classification Approaches

Research on joint intent detection and slot filling (ACM Computing Surveys,
2022; Springer Neural Computing 2025) identifies three main paradigms:

**Fine-tuning approach:** Train a specialized classifier on labeled (intent,
utterance) pairs. High accuracy when you have labeled data and a closed intent
set. Poor generalization to unseen intents.

```
Intent: install_plugin
Utterance: "add the embedded team to my setup"
Confidence: 0.94
```

**Few-shot prompting approach:** Provide the LLM with a few labeled examples
and ask it to classify new utterances. Generalizes well but accuracy varies
with example quality.

**Embedding-based approach:** Embed both the user's utterance and the intent
descriptions using a semantic similarity model. Find the nearest intent. Scales
to large intent libraries without fine-tuning.

| Approach | Accuracy (known intents) | Accuracy (novel intents) | Maintenance |
|---|---|---|---|
| Fine-tuned classifier | Very High | Poor | High |
| Few-shot LLM | High | Good | Low |
| Embedding similarity | High | Good | Medium |
| Hybrid (embed + LLM verify) | Very High | Very Good | Medium |

The current claude-kit approach — natural language intent matching via the
`intent-map.md` skill — is closest to the few-shot LLM paradigm: the intent
map provides labeled examples, and Claude's reasoning matches new utterances
to the closest example.

### 5.3 Slot Filling and Entity Extraction

Once intent is identified, **slot filling** extracts the specific values the
intent requires. This is the difference between identifying that a user wants
to "run tests" and knowing *which tests* (all? affected? specific project?).

Classic NLU slot filling uses sequence labeling (BIO tagging):

```
"run the [B-TARGET]zephyr[I-TARGET] [B-TEST_TYPE]unit[I-TEST_TYPE] tests"
Intent: run_tests
Slots: {target: "zephyr", test_type: "unit"}
```

For LLM-based systems, slot filling is increasingly done through structured
output extraction (Instructor, TypeChat) or through direct prompting with a
schema:

```
User: "run the zephyr unit tests"
Extract into: {target?: string, test_type?: "unit"|"integration"|"all", scope?: "affected"|"all"}
Result: {target: "zephyr", test_type: "unit", scope: null}
```

The extracted slots then drive command construction. This turns natural language
into a structured, executable specification.

### 5.4 Tool Use and Function Calling as Intent Formalization

The most consequential development in intent formalization for AI systems is
not a research paper — it is **OpenAI function calling** (2023) and **Anthropic
tool use** (2023), which introduced a standard pattern: the developer defines
a schema for each capability, and the model selects which capability to invoke
and what arguments to supply.

```json
{
  "name": "run_plugin_validation",
  "description": "Validate one or more plugins against the Tier 1 schema",
  "input_schema": {
    "type": "object",
    "properties": {
      "target": {
        "type": "string",
        "enum": ["--all", "--changed"],
        "description": "Which plugins to validate"
      },
      "strict": {
        "type": "boolean",
        "description": "Run in strict mode (blocks warnings)"
      }
    },
    "required": ["target"]
  }
}
```

**Why this is a formal intent interface:**

- The `name` is the intent identifier
- The `description` is the natural-language specification
- The `input_schema` is a JSON Schema contract for arguments
- The `required` field specifies mandatory vs. optional parameters
- The `enum` constraints restrict valid argument values

Function calling / tool use is the **most widely deployed formal intent
interface in production AI systems** because it sits at the right point on
the flexibility-precision spectrum: natural language descriptions for
discoverability, JSON Schema for argument structure, enumerations for
constraint expression.

OpenAI's August 2024 Structured Outputs feature strengthened this further:
`strict: true` guarantees that function arguments exactly match the provided
JSON Schema, with no invalid properties or missing required fields.

### 5.5 The Semantic Gap and How It Gets Bridged

The semantic gap between what users say and what systems can do has three
components:

**Vocabulary gap:** The user says "make the thing faster" — the system knows
about "run_benchmarks", "optimize_query", and "enable_caching". The mapping
requires semantic understanding, not just keyword matching.

**Granularity gap:** The user expresses intent at a high level ("deploy this
feature") while the system operates at a low level (bump version, update
changelog, create PR, merge, tag, create release). Intent decomposition is
required.

**Constraint gap:** The user expresses desired outcome ("deploy to production")
without specifying mandatory constraints ("never deploy on Friday", "requires
two approvals", "must have green CI"). Constraint elicitation is required.

Modern systems address each gap:

| Gap Type | Bridging Mechanism |
|---|---|
| Vocabulary | Semantic embedding similarity, LLM reformulation |
| Granularity | Multi-step reasoning, task decomposition (CoT, ReAct) |
| Constraint | Slot filling, clarification questions, precondition checking |

Research (arXiv:2502.09101, 2025, "Bridging the Gap Between LLMs and Human
Intentions") identifies that models face challenges in "accurately capturing
and comprehending human instructions" specifically around constraint
satisfaction — knowing what must be true at completion, not just what action
to take.

---

## 6. Specification Languages for Agent Behavior

### 6.1 How Do You Formally Specify What an Agent Should and Shouldn't Do?

This is the hardest problem in the space. Specifying *functional behavior*
(what the agent should produce) is tractable. Specifying *behavioral
constraints* (what the agent must never do, regardless of context) is much
harder.

Three paradigms address this at different levels:

**Value alignment** (Constitutional AI, RLHF) — embed constraints in the model
through training. High coverage, low precision, not verifiable.

**Runtime enforcement** (hooks, middleware, contract checkers) — intercept
actions and verify constraints before or after execution. Moderate coverage,
high precision for what's checked, inspectable.

**Formal verification** (model checking, LTL) — prove mathematically that a
specification is satisfied. Very high precision, requires formal spec, impractical
for most behaviors.

No single approach is sufficient. The best-designed systems layer all three.

### 6.2 Constitutional AI and Its Limitations

Constitutional AI (Bai et al., Anthropic, 2022) embeds a set of principles
into an RLHF training process. The model learns to critique and revise its
outputs based on the principles, producing a model that self-enforces the
constitution.

This is impressive as a training-time alignment technique. Its limitations as
a *specification* mechanism are equally important to understand:

**Coverage limitation:** The constitution specifies values and principles, not
functional contracts. "Be helpful, harmless, and honest" does not specify what
the agent should do when asked to write a database migration in a codebase it
has never seen.

**Precision limitation:** Natural language principles have inherent ambiguity.
Two readers of "choose the response that is most supportive of rule of law" may
reach different conclusions in specific cases.

**Stability limitation:** Constitutional compliance cannot be mechanically
verified. You can sample outputs and evaluate them against the constitution, but
you cannot prove that all possible outputs comply.

**Domain limitation:** Constitutional AI targets value alignment for general AI
systems. For domain-specific agents (a Zephyr firmware engineer, a PR reviewer),
domain-specific behavioral constraints require domain-specific specifications
that a constitution cannot provide.

For claude-kit, constitutional AI is relevant as the foundation on which Claude
operates — it provides baseline safety constraints. But the skill system, hooks,
and agent role definitions are the mechanism for domain-specific behavioral
specification.

### 6.3 Linear Temporal Logic for Agent Policies

Linear Temporal Logic (LTL) has a rich history in formal verification of
concurrent systems and robot motion planning. Recently, it has been applied
to AI agent behavior specification with promising results.

**Basic LTL operators:**

| Operator | Symbol | Meaning |
|---|---|---|
| Globally | □ | φ holds at all future states |
| Finally | ◇ | φ holds at some future state |
| Next | ○ | φ holds at the next state |
| Until | U | φ holds until ψ holds |

**Applied to agent behavior:**

```
# A deploy agent must never deploy if tests are failing
□(action = "deploy" → tests_passing)

# After a file write, a validation step must eventually occur
□(action = "write_file" → ◇ action = "validate_output")

# A reviewer must never write to source files (only read)
□(¬(action = "write" ∧ file_type = "source"))
```

**Recent research (2024-2025):**

*LTLCrit / LogicGuard* (arXiv:2507.03293): A framework where an LLM planner
is guided by an LTL-based critic. The critic intercepts planned actions, checks
them against LTL safety constraints, and blocks or redirects unsafe actions.
Results show strict adherence to safety constraints with good scalability to
complex constraint sets.

*AutoSafeLTL* (arXiv:2503.15840): Self-supervised LTL generation from
safety requirements, using counterexample-guided feedback loops to achieve
a 0% safety violation rate.

*LTL-Constrained Policy Optimization* (NSF/ICLR 2024): Reinforcement learning
where the reward function is constrained by LTL formulas, preventing the agent
from optimizing proxy rewards in ways that violate temporal safety constraints.

**Practical status for claude-kit:** Raw LTL formula authoring is impractical
for most developers. But LLM-assisted translation (NL2Spec, lang2LTL) makes
LTL increasingly accessible — you describe the constraint in natural language,
the system produces the LTL formula, and you review/edit the formula before
deploying it. This is the direction in which the field is moving.

### 6.4 Reward Modeling and Goodhart's Law

Reward modeling — where a model learns a proxy reward function from human
feedback (RLHF) — is the most widely deployed mechanism for aligning AI system
behavior with human intent. It is also subject to systematic failure in ways
that are directly relevant to intent specification.

**Goodhart's Law** states: "When a measure becomes a target, it ceases to be
a good measure." In the RLHF context, the proxy reward (human rater approval)
diverges from the true objective (actual helpfulness) under optimization pressure.

Research evidence:
- ICLR 2024 paper "Goodhart's Law in Reinforcement Learning": "Goodhart's law
  is a robust phenomenon across a wide range of environments in RL."
- In summarization tasks, models start to "game" the reward around 10 nats of
  KL divergence from the base model — at this point, the true objective starts
  to decrease even as the proxy reward continues to rise.
- LLM fine-tuned for human approval often produces responses that sound
  authoritative and confident even when wrong — because confidence correlates
  with approval even when it does not correlate with accuracy.

**Implications for intent specification:**

Reward modeling as intent specification has an inherent flaw: **optimizing any
finite proxy specification will eventually find ways to satisfy the proxy without
satisfying the true intent**. This is not a failure of a specific implementation
— it is a mathematical consequence of the relationship between specification
and optimization.

The solution is not to abandon reward modeling but to layer it with constraints
that are not subject to Goodhart's Law because they are not optimized —
they are enforced:

| Mechanism | Subject to Goodhart's Law? | Reason |
|---|---|---|
| RLHF reward | Yes | Optimized; proxy diverges under pressure |
| Constitutional AI | Partially | Soft enforcement; optimization can find workarounds |
| Runtime hooks (hard blocks) | No | Not optimized; binary enforce/permit |
| JSON Schema validation | No | Not optimized; mechanically checked |
| LTL policy enforcement | No | Not optimized; formally verified |

Claude-kit's hooks implement the rightmost column: they are not optimized
away because they are not in the optimization loop at all.

### 6.5 NL2Spec: From Natural Language to Formal Specifications

NL2Spec (Cosler et al., CAV 2023, arXiv:2303.04864) demonstrated that LLMs
can translate natural language system requirements into temporal logic formulas
with interactive disambiguation. The user provides natural language
requirements; the system produces LTL formulas; ambiguous mappings are
surfaced for user resolution.

This is the **specification bridge** that makes formal methods accessible:

```
User: "The system must always check authorization before accessing user data"
↓ NL2Spec
LTL: □(access_user_data → ○authorization_checked)
     // "Globally: whenever user data is accessed,
     //  in the next state authorization must have been checked"
```

The Stanford FMCAD 2024 follow-up showed improved industrial requirement
translation accuracy, with binary accuracy around 90% and BLEU scores near
0.93 for well-formed requirements.

**Lang2LTL** (CoRL 2023) applied this specifically to robotics: natural
language commands are translated into LTL specifications that can be used
directly by motion planners, grounding spatial and temporal language to
formal constraints.

The emerging pattern: natural language → LLM translation → formal spec →
mechanical verification. The LLM serves as the bridge between human expressivity
and machine precision, with formal methods providing the verifiability.

---

## 7. Implications for claude-kit

This section synthesizes the research into concrete architectural implications
for claude-kit's intent routing, skill declaration, command structure, and
the possible design of a formal intent layer.

### 7.1 The Current Routing System: Strengths and Gaps

The current routing system in claude-kit uses `routing/intent-map.md` — a
natural language mapping from user intents to skills and commands. This is
essentially a **few-shot classification approach**: the intent map provides
labeled examples, and Claude matches new utterances to the closest example.

**Strengths of the current approach:**
- Zero friction for routing definition — add a row to a markdown table
- Handles natural variation well (LLM reasoning handles paraphrase)
- No schema to maintain, no format to validate
- Extensible by any plugin author without tooling knowledge

**Gaps revealed by the research:**
- **No typed inputs** — a command that requires a `target` (plugin name) and
  a `scope` (--all | --changed) cannot specify this in the routing map;
  the agent must infer it from context
- **No slot filling** — once an intent is matched, there is no structured
  mechanism to extract the required parameters
- **No constraint declaration** — commands cannot express preconditions ("this
  command requires a clean git working tree") that the router could check before
  dispatching
- **No confidence scoring** — the system does not quantify routing certainty;
  ambiguous matches either pick one or fail
- **No negative examples** — the intent map specifies what commands do; it
  does not specify what they must never do

### 7.2 Should Commands Have Typed Input Schemas?

The research strongly supports adding typed input schemas to commands. The
evidence is overwhelming that **schema-typed interfaces produce more reliable
behavior** than natural language descriptions alone — from TypeChat's type-to-JSON
mechanism, to Instructor's Pydantic models, to OpenAI function calling's JSON
Schema.

**Proposed command frontmatter extension:**

Currently, commands have minimal structured metadata:

```yaml
---
description: Validate plugins against the Tier 1 schema
allowed-tools: [Bash, Read]
---
```

A formal intent interface would add:

```yaml
---
description: Validate plugins against the Tier 1 schema
allowed-tools: [Bash, Read]
input:
  target:
    type: enum
    values: [--all, --changed, plugin_name]
    required: true
    description: Which plugins to validate
  strict:
    type: boolean
    required: false
    default: false
    description: Run in strict mode (warnings become failures)
preconditions:
  - "Current directory is the claude-kit repository root"
  - "plugins/ directory exists"
postconditions:
  - "Validation results are reported for each target plugin"
  - "Exit code is 0 if all validations pass, non-zero otherwise"
---
```

This schema serves multiple purposes:
1. **Routing** — the router can match user intents more precisely because
   it knows what inputs the command accepts
2. **Slot filling** — the schema drives structured extraction of required
   parameters from the user's utterance
3. **Precondition checking** — hooks can verify preconditions before dispatch
4. **Documentation** — the schema is self-documenting in a machine-readable way
5. **Validation** — input can be validated before the command runs

The cost is additional frontmatter maintenance. The benefit is fewer
"wrong interpretation" errors — exactly the Goodhart's Law failure mode
that natural-language-only interfaces are subject to.

### 7.3 A DSL or Structured Format for Skill Queries

Skills in claude-kit are currently loaded by name: `skills: [core-kit:routing]`.
The agent loads the entire SKILL.md and uses it as context. This is efficient
and flexible, but provides no structure for how the skill should be used.

Research on DSPy signatures suggests a more structured alternative:

```yaml
# In an agent's frontmatter:
skills:
  - name: core-kit:routing
    use_for: "determining which skill or command matches a user intent"
    query_pattern: "Given intent: {intent_text}, which skill best matches?"
    output_fields: [matched_skill, confidence, reasoning]
```

This turns skill invocation from "load context and hope" into a typed query:
the agent knows what it is asking the skill, what fields it expects in
response, and can validate that the response is complete.

The DSPy `Signature` concept is directly applicable: each skill has a typed
interface that the agent uses to construct its query and validate the response.
The SKILL.md content provides the context; the signature provides the contract.

### 7.4 How the core-spec Plugin Benefits from Formal Intent Interfaces

The `core-spec` plugin generates project specifications — it is the part of
claude-kit most directly concerned with formalizing intent. Currently, specs
are generated from conversation: the user describes their project, and the
agent produces a markdown specification document.

Formal intent interfaces could improve this in several ways:

**Typed spec structure:** A generated spec currently has free-form sections.
A typed schema would ensure every spec has the required fields:

```python
class ProjectSpec(BaseModel):
    goal: str = Field(description="Core purpose in one sentence")
    target_users: list[str]
    functional_requirements: list[FunctionalRequirement]
    non_functional_requirements: NonFunctionalRequirements
    constraints: list[Constraint]  # Explicit prohibitions
    success_criteria: list[MeasurableCriterion]

class Constraint(BaseModel):
    description: str
    category: Literal["security", "regulatory", "ethical", "technical"]
    enforcement: Literal["must_never", "should_avoid", "requires_approval"]

class MeasurableCriterion(BaseModel):
    criterion: str
    measurement_method: str
    threshold: str
```

This is exactly the "legal contract" framing from the podcast: constraints
have categories and enforcement levels; success criteria are measurable; the
spec cannot be considered complete until all required fields are present.

**Intent validation at spec creation time:** Before an engineer agent begins
work, the spec can be checked for:
- Are all required fields present?
- Are constraints explicitly stated (not implicit)?
- Are success criteria measurable (not just "good" or "great")?
- Are ethical/regulatory constraints covered?

This is pre-flight intent validation — catching underspecification before it
causes costly misaligned implementation.

**NL2Spec integration for constraint formalization:** When a spec includes
safety or behavioral constraints ("the system must always encrypt user data
in transit"), NL2Spec could translate these into LTL or JSON Schema constraints
that downstream enforcement can use mechanically.

### 7.5 What a Formal Intent Layer Would Look Like

Based on the research, a new core plugin — `core-intent` — could provide
formal intent interfaces for claude-kit. Its architecture:

```
plugins/core-intent/
  .claude-plugin/
    plugin.json     # name: "core-intent", role: "system"
    ctl.json        # domain: "universal"
  skills/
    intent-schema/
      SKILL.md      # Theory: how intent schemas work
    slot-filling/
      SKILL.md      # How to extract slots from natural language
    validation/
      SKILL.md      # How to validate intent against preconditions
  agents/
    intent-parser.md    # Extracts typed intent + slots from user utterances
    precond-checker.md  # Validates preconditions before dispatch
  commands/
    define-intent.md    # /core-intent:define — scaffold a new command schema
    validate-intent.md  # /core-intent:validate — check an intent declaration
  hooks/
    hooks.json          # PreToolUse: validate intent before command dispatch
```

**The intent parser agent** would take a user utterance and a catalog of
command schemas, and produce:

```json
{
  "matched_command": "validate-plugins",
  "confidence": 0.94,
  "slots": {
    "target": "--changed",
    "strict": false
  },
  "unresolved_slots": [],
  "precondition_status": "unchecked"
}
```

**The precondition checker agent** would then verify that the required
preconditions are satisfied before dispatching.

**The define-intent command** would scaffold a typed command schema from
a natural language description of a new command, producing the frontmatter
extension described in Section 7.2.

### 7.6 Should Skill Declarations Be Typed?

Currently, the `skills:` list in agent frontmatter is an array of name strings:

```yaml
skills:
  - embedded-zephyr-knowledge:zephyr-rtos
  - core-kit:routing
```

The research on DSPy signatures and TypeChat suggests that typed skill
declarations would improve precision:

```yaml
skills:
  - name: embedded-zephyr-knowledge:zephyr-rtos
    role: reference    # This skill provides factual reference material
    query_when: "generating Zephyr RTOS code or configuration"

  - name: core-kit:routing
    role: operational  # This skill provides operational instructions
    query_when: "determining which command to dispatch"
    provides: [skill_name, confidence_score, reasoning]
```

The `role` field distinguishes **reference skills** (domain knowledge to draw
on) from **operational skills** (instructions to follow). The `provides` field
declares what structured information can be extracted from the skill, enabling
downstream agents to validate that they received what they expected.

This typed declaration is more verbose but more precise — it turns a name
reference into a typed interface contract, consistent with the TypeScript-types
approach of TypeChat.

### 7.7 Practical Recommendations

Ranked by implementation cost and expected benefit:

**High benefit, low cost:**

1. **Add `preconditions:` to command frontmatter** — a list of plain-language
   preconditions the routing system can surface to the user before a command
   runs. Zero machinery required; adds clarity immediately.

2. **Add `input:` schemas to the 10 most-used commands** — follow the
   OpenAI function calling schema pattern. Enables better slot filling and
   routing precision.

3. **Add `output_contract:` to commands** — a brief structured description of
   what the command guarantees to produce. Helps graders validate output.

**Medium benefit, medium cost:**

4. **Implement typed slot filling in the intent parser** — when a matched
   command has an `input:` schema, extract and validate slots from the
   user's utterance before dispatching. Use Instructor-style validation.

5. **Add schema-typed spec structure to `core-spec`** — ensure generated specs
   include explicit constraints, measurable success criteria, and prohibition
   statements. Use a Pydantic-equivalent in the agent prompt.

6. **Add `constraint:` declarations to agent frontmatter** — behavioral
   invariants that the agent must maintain throughout its session, enforced
   by hooks.

**High benefit, high cost:**

7. **Develop `core-intent` plugin** — the full formal intent layer described
   in Section 7.5. This is a significant architectural addition but provides
   the most systematic improvement to routing precision.

8. **Integrate NL2Spec-style translation for safety constraints** — when
   commands or specs declare safety constraints in natural language, translate
   them to verifiable formal assertions. Requires LTL runtime enforcement.

9. **DSPy-style signature compilation** — treat the `input:` schemas as DSPy
   signatures and auto-optimize the prompts that drive command execution
   against a quality metric.

### 7.8 Synthesis: The Right Level for claude-kit

The research suggests that claude-kit sits correctly in the middle of the
spectrum — more structured than raw natural language, less formal than LTL.
The improvements identified above are all moves toward the right (more precise)
without crossing into the formal methods zone that requires specialist knowledge.

The architectural principle is:

**Natural language for discovery. Schemas for dispatch. Contracts for enforcement.**

- Users express intent in natural language (high flexibility)
- The routing system matches to typed command schemas (structured dispatch)
- Preconditions and hooks enforce invariants mechanically (hard constraints)

This layering — identical in spirit to how OpenAI function calling works —
produces systems that are both usable (natural language entry) and reliable
(formal constraints on execution). The insight from ConstitutionalAI,
Goodhart's Law research, and LTL enforcement all converge on the same
conclusion: **you cannot rely on the model to self-enforce constraints under
optimization pressure — you must enforce them outside the optimization loop.**

Hooks are claude-kit's mechanism for exactly this. Adding typed command
schemas and structured slot filling would extend the same principle to the
routing layer, closing the remaining gap between what users say and what
agents reliably do.

---

---

## Sources

### Foundational Prompting and Reasoning

- Wei, J. et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in
  Large Language Models." NeurIPS 2022. arXiv:2201.11903
- Yao, S. et al. (2023). "ReAct: Synergizing Reasoning and Acting in Language
  Models." ICLR 2023. arXiv:2210.03629. [react-lm.github.io](https://react-lm.github.io/)
- Brown, T. et al. (2020). "Language Models are Few-Shot Learners" (GPT-3).
  arXiv:2005.14165
- Yao et al. (NAACL 2024). "More Samples or More Prompts? Exploring Effective
  Few-Shot In-Context Learning." [ACL Anthology](https://aclanthology.org/2024.findings-naacl.115/)

### Constitutional AI and Value Alignment

- Bai, Y. et al. (2022). "Constitutional AI: Harmlessness from AI Feedback."
  Anthropic. arXiv:2212.08073.
  [anthropic.com](https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback)
- Anthropic (2024). "Collective Constitutional AI: Aligning a Language Model
  with Public Input." [anthropic.com](https://www.anthropic.com/research/collective-constitutional-ai-aligning-a-language-model-with-public-input)
- Anthropic (2026). "Claude's Constitution." [anthropic.com/news](https://www.anthropic.com/news/claudes-constitution)
- C3AI (WWW 2025). "Crafting and Evaluating Constitutions for Constitutional
  AI." ACM. [dl.acm.org](https://dl.acm.org/doi/10.1145/3696410.3714705)

### DSLs and Structured Interfaces for AI

- Beurer-Kellner, L. et al. (2023). "Prompting Is Programming: A Query Language
  for Large Language Models" (LMQL). PLDI 2023. arXiv:2212.06094.
  [lmql.ai](https://lmql.ai/)
- Khattab, O. et al. (2024). "DSPy: Compiling Declarative Language Model Calls
  into Self-Improving Pipelines." ICLR 2024. arXiv:2310.03714.
  [dspy.ai](https://dspy.ai/)
- Microsoft Research (2023). "TypeChat: Building Natural Language Interfaces
  Using Types." [microsoft.github.io/TypeChat](https://microsoft.github.io/TypeChat/docs/introduction/)
- Microsoft Research (2023-2025). "Guidance: A Guidance Language for
  Controlling Large Language Models."
  [github.com/guidance-ai/guidance](https://github.com/guidance-ai/guidance)
- Dong et al. (2024). "XGrammar: Flexible and Efficient Structured Generation
  Engine for Large Language Models." arXiv:2411.15100.
  [mlc.ai](https://blog.mlc.ai/2024/11/22/achieving-efficient-flexible-portable-structured-generation-with-xgrammar)
- Liu, J. (2023-2025). Instructor: Structured LLM Outputs.
  [useinstructor.com](https://useinstructor.com/)
- Generating Structured Outputs from Language Models: Benchmark and Studies
  (2025). arXiv:2501.10868. [arxiv.org](https://arxiv.org/html/2501.10868v1)

### Semantic Kernel and Microsoft Agent Framework

- Microsoft Learn (2024-2025). "Semantic Kernel Overview."
  [learn.microsoft.com/semantic-kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
- Microsoft (2025). "Microsoft Agent Framework." Semantic Kernel + AutoGen.
  [devblogs.microsoft.com](https://devblogs.microsoft.com/semantic-kernel/semantic-kernel-and-microsoft-agent-framework/)

### Meta-Prompting and Prompt Programs

- Suzgun, M. et al. (2024). "Meta-Prompting: Enhancing Language Models with
  Task-Agnostic Scaffolding." arXiv:2311.11482.
  [github.com/meta-prompting](https://github.com/meta-prompting/meta-prompting)
- Yuksekgonul et al. (2025). "TextGrad: Automatic Differentiation via Text."
  Nature 2025.
- Prompt Engineering Guide. "Meta Prompting."
  [promptingguide.ai](https://www.promptingguide.ai/techniques/meta-prompting)

### Intent Classification and Slot Filling

- Weld, H. et al. (2022). "A Survey of Joint Intent Detection and Slot Filling
  Models." ACM Computing Surveys. [dl.acm.org](https://dl.acm.org/doi/10.1145/3547138)
- Springer (2025). "Joint learning for intent detection and slot filling from
  classical to deep learning: a review." Neural Computing and Applications.
  [link.springer.com](https://link.springer.com/article/10.1007/s00521-025-11329-9)
- arXiv (2025). "Bridging the Gap Between LLMs and Human Intentions."
  arXiv:2502.09101. [arxiv.org](https://arxiv.org/html/2502.09101v1)
- Ambig-SWE (ICLR 2026). "Interactive Agents to Overcome Underspecification
  in Agentic Tasks." arXiv:2502.13069

### Function Calling and Tool Use

- OpenAI (2023-2024). "Function Calling." OpenAI API.
  [platform.openai.com](https://platform.openai.com/docs/guides/function-calling)
- OpenAI (August 2024). "Structured Outputs with strict JSON Schema."
- Vellum (2024). "When to Use Function Calling vs Structured Outputs."
  [vellum.ai](https://www.vellum.ai/blog/when-should-i-use-function-calling-structured-outputs-or-json-mode)
- ACM CIKM 2024. "Bridging Knowledge Gaps in LLMs via Function Calls."
  [dl.acm.org](https://dl.acm.org/doi/10.1145/3627673.3679070)

### Formal Methods and Agent Specification

- Cosler, M. et al. (2023). "nl2spec: Interactively Translating Natural
  Language to Temporal Logics." CAV 2023. arXiv:2303.04864.
  [arxiv.org](https://arxiv.org/abs/2303.04864)
- Mendoza et al. (2024). "Translating Natural Language to Temporal Logics
  with Large Language Models." FMCAD 2024.
  [cs.stanford.edu](https://cs.stanford.edu/~trippel/pubs/mendoza_FMCAD24.pdf)
- Liu, J. et al. (2023). "LTLCrit / LogicGuard: Improving Embodied LLM Agents
  through Temporal Logic-Based Critics." arXiv:2507.03293.
  [arxiv.org](https://arxiv.org/html/2507.03293v1)
- Zhang et al. (2025). "AutoSafeLTL: Automatic Generation of Safety-Compliant
  LTL via LLM." arXiv:2503.15840.
- Transforming Natural Language into Formal Specifications (AgenticSE 2025).
  [conf.researchr.org](https://conf.researchr.org/details/ase-2025/agenticse-2025-papers/6/Transforming-Natural-Language-into-Formal-Specifications)

### Agent Behavioral Contracts

- Leoveanu-Condrei et al. (2025). "Agent Behavioral Contracts: Formal
  Specification and Runtime Enforcement for Reliable Autonomous AI Agents."
  arXiv:2602.22302. [arxiv.org](https://arxiv.org/html/2602.22302)
- Agent Contracts (2025). "A Formal Framework for Resource-Bounded Autonomous
  AI Systems." arXiv:2601.08815.
- LLM API Contracts (2024). "A Formal Probabilistic Contract Model for the
  LLM Domain." [tanzimhromel.com](https://tanzimhromel.com/assets/pdf/llm-api-contracts.pdf)
- IEEE (2025). "Preconditions and Postconditions as Design Constraints for LLM
  Code Generation." [ieeexplore.ieee.org](https://ieeexplore.ieee.org/document/11218044/)

### Reward Modeling and Goodhart's Law

- Skalse et al. (ICLR 2024). "Goodhart's Law in Reinforcement Learning."
  [proceedings.iclr.cc](https://proceedings.iclr.cc/paper_files/paper/2024/file/6ad68a54eaa8f9bf6ac698b02ec05048-Paper-Conference.pdf)
- Weng, L. (2024). "Reward Hacking in Reinforcement Learning." Lil'Log.
  [lilianweng.github.io](https://lilianweng.github.io/posts/2024-11-28-reward-hacking/)
- arXiv (2025). "Take Goodhart Seriously: Principled Limit on General-Purpose
  AI Optimization." arXiv:2510.02840.
- LessWrong (2024). "AI Safety 101: Reward Misspecification."
  [lesswrong.com](https://www.lesswrong.com/posts/mMBoPnFrFqQJKzDsZ/ai-safety-101-reward-misspecification)

### Natural Language Ambiguity in Agentic Systems

- arXiv (2025). "Automated Repair of Ambiguous Natural Language Requirements."
  arXiv:2505.07270.
- Brooker, M. (2025). "On the Success of Natural Language Programming."
  [brooker.co.za](https://brooker.co.za/blog/2025/12/16/natural-language.html)
- Requirements Ambiguity Detection with LLMs: An Industrial Study.
  [ipr.mdu.se](https://www.ipr.mdu.se/pdf_publications/7221.pdf)

### Prompt Templates and Interface Design

- arXiv (2025). "From Prompts to Templates: A Systematic Prompt Template
  Analysis for Real-world LLMapps." arXiv:2504.02052.
- Prompt Engineering Guide. "Few-Shot Prompting."
  [promptingguide.ai](https://www.promptingguide.ai/techniques/fewshot)
