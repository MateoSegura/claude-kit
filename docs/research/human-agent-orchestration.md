# Human-Agent Orchestration: UX Patterns, Cognitive Load, and Workflow Design

> Research document for the **claude-kit** plugin management system.
> Explores how UX and workflow design should evolve as developers manage multiple simultaneous AI agent sessions.

**Date:** 2026-02-28
**Governing Process:** PROC-LC-001 (Market Analysis)

---

## Table of Contents

1. [The Core Challenge](#1-the-core-challenge)
2. [Cognitive Science of Context Switching](#2-cognitive-science-of-context-switching)
3. [Human-in-the-Loop Design Patterns](#3-human-in-the-loop-design-patterns)
4. [Mental Models for Agent Management](#4-mental-models-for-agent-management)
5. [UX Patterns for Multi-Agent Workflows](#5-ux-patterns-for-multi-agent-workflows)
6. [Task Decomposition as a Skill](#6-task-decomposition-as-a-skill)
7. [Error Recovery and Failure Handling](#7-error-recovery-and-failure-handling)
8. [The Iterative Agent Addition Pattern](#8-the-iterative-agent-addition-pattern)
9. [Implications for claude-kit](#9-implications-for-claude-kit)
10. [References](#10-references)

---

## 1. The Core Challenge

A Stanford researcher on AI agent workflows framed the central problem precisely:

> "The second thing that is really really important is knowing how to context switch. In practice, what you're doing is kicking off these eager, savvy interns — these agents — and they're doing a thing and you're just watching them in the terminal or IDE, seeing them do work and contribute code. But sometimes they get stuck. How do you go from one to another to another — understanding that agent 1 was working on this task, agent 2 on another, agent 3 on another — and constantly switch back and forth? It's very difficult even as a human to know how to remember what the last thing was working on but still have enough context to meaningfully push that task forward. That switching is probably one of the core skills of getting multi-agent workflows to work really well."

This is not a new problem dressed in new clothes. It is a version of the oldest problem in human performance research: how do people maintain effective oversight of multiple concurrent work streams without collapsing under the cognitive weight of context accumulation?

The answer, as the researcher also noted, maps almost exactly onto what organizational behavior research has learned about effective human managers. The transition from individual contributor to multi-agent orchestrator is structurally identical to the transition from engineer to engineering manager — and it carries the same cognitive costs, the same mental model shifts, and the same failure modes.

This document synthesizes research across cognitive science, human factors engineering, UX design, and practitioner writing to provide a foundation for designing claude-kit's multi-agent orchestration UX.

---

## 2. Cognitive Science of Context Switching

### 2.1 Task-Switching Costs: What the Research Shows

The cognitive cost of task switching — often called the **switch cost effect** — is one of the most robustly replicated findings in experimental psychology. When a person switches from one task to another, performance degrades in two measurable ways:

- **Switch cost**: The additional reaction time and error rate on the first trial after a switch, compared to continuing the same task.
- **Residual switch cost**: Even with extended preparation time before a switch, some cost remains — the prior task's mental set is not fully cleared.

Research published in the *Journal of Experimental Psychology* demonstrates that task switching induces measurable working memory costs: recall performance decreases as a function of the number of task switches performed in a session (Mayr & Keele, 2000; Oberauer, 2009). This is not merely anecdotal — working memory capacity is finite, and each switch event consumes a portion of it for reconfiguration.

The productivity literature has popularized these findings: task switching may cost up to **40% of a person's productive time** due to cognitive reconfiguration overhead (American Psychological Association). A 2024 Wake Forest study reinforced that the "switch cost" is real and measurable even in everyday digital work contexts.

For agent orchestration specifically, this means:

- Every time a developer moves from Agent A's session to Agent B's, they pay a switch cost.
- If Agent B immediately asks a clarifying question, the developer answers it while still mentally reconfiguring — producing lower-quality responses.
- If Agent C gets stuck while the developer is already attending to Agent B, triage becomes a compounding cognitive burden.

### 2.2 Working Memory and Task-Set Reconfiguration

Working memory is the cognitive workspace where task-relevant information is held and manipulated. When a person switches tasks, they must:

1. Inhibit the mental set of the prior task (suppress its goals, rules, and active representations).
2. Retrieve and activate the mental set of the new task.
3. Reload task-relevant context into working memory.

Step 3 is where agent session management is most costly. Unlike switching between two software windows, switching between agent sessions requires reconstructing a **narrative**: what was the agent doing, why, what decisions were made, and where is it now? This is not perceptual reconfiguration — it is episodic memory retrieval, which is slower and more error-prone.

Research by Dodhia and Dismukes (2009) established that **interruptions create prospective memory tasks** — the interrupted person must form a subgoal to return to the primary task and resume it. Without deliberate encoding of resumption cues at the moment of interruption, the failure rate for resumed tasks increases significantly. In high-stakes environments like nursing and aviation, where similar multi-task management is required, this failure mode is well-documented.

### 2.3 Prospective Memory: Remembering to Resume

**Prospective memory** (PM) is the cognitive ability to remember to perform intended actions at a future time or event. It is distinct from retrospective memory (remembering past events) in that it requires self-initiated retrieval — no external cue prompts recall; the person must remember to remember.

Research by Altmann and Trafton (2002, "Preparing to Resume an Interrupted Task") found that:

- People who receive a warning before an interruption (giving them time to encode a resumption cue) resume tasks significantly faster than those interrupted abruptly.
- Prospective memory for task resumption decays over time — the longer the interruption, the more likely the sub-goal is to be forgotten.
- **Implementation intentions** ("When I finish this, I will return to X because it needs Y") dramatically improve PM performance.

For agent orchestration, the implications are direct. When a developer leaves an agent session, they need a moment — and a structured prompt — to encode what "done" looks like and what they will need when they return. Without this encoding, resumption is slower and more error-prone.

### 2.4 The "Manager Not Maker" Mental Model Shift

The transition from individual contributor to manager is one of the most studied role transitions in organizational psychology. The Leadership Pipeline Model (Charan, Drotter & Noel) identifies this as one of six critical "passage points" in professional development — not merely doing different work, but **valuing different outcomes**.

Key research findings on this transition:

- Individual contributors measure their success by personal output. Managers must shift to measuring success through team output.
- New managers who fail to make this mental shift "jump in and do the work themselves" — reducing team autonomy and creating bottlenecks.
- The cognitive load of managing others is distinct from the cognitive load of executing work: it is primarily attentional (monitoring multiple streams) rather than operational (executing complex tasks).

For developer-to-agent-orchestrator transitions, the parallel is precise. A developer managing five Claude Code agents is no longer a coder; they are a technical director. Their job is to:

1. Ensure each agent has clear, isolated, well-specified tasks.
2. Unblock agents when they get stuck.
3. Review outputs and integrate them.
4. Maintain a mental model of overall project state.

The failure mode for developers new to agent orchestration is the same as for new managers: they want to take over the work themselves when an agent struggles, rather than providing clearer direction and letting the agent continue.

---

## 3. Human-in-the-Loop Design Patterns

### 3.1 The HITL Spectrum

Human-in-the-loop (HITL) AI design exists on a spectrum from full human control to full autonomy. Research from Stanford's Human-Centered AI Institute identifies the key question as not "should there be a human in the loop?" but rather "at which decision points, in which roles?"

Four distinct human roles in HITL systems:

| Role | Description | When Needed |
|------|-------------|-------------|
| **Validator** | Checks output before it is acted on | High-stakes or irreversible actions |
| **Editor** | Improves or contextualizes output | Ambiguous requirements, subjective quality |
| **Decider** | Makes a judgment call the system cannot safely make | Novel situations, ethical decisions |
| **Teacher** | Provides feedback that shapes future behavior | After errors, for calibration |

### 3.2 Decision Points Requiring Human Review

Research on when HITL checkpoints are most valuable identifies three primary criteria:

**Irreversibility**: Any action that cannot be easily undone (destructive file operations, external API calls, database writes, deployment actions) should require explicit human approval. The cost of interruption is lower than the cost of recovery.

**Ambiguity**: When task requirements are underspecified or could be interpreted multiple ways, an autonomous agent will make a choice — often one the developer did not intend. Human review at ambiguity points prevents costly rework.

**Compounding risk**: In multi-step workflows, if step 3 is wrong, steps 4-10 build on a flawed foundation. Human validation at the transition between phases (planning to execution, implementation to integration) catches errors before they compound.

The EU AI Act (2024) now mandates human oversight for all high-risk AI systems, which provides a regulatory framework that reinforces what human factors research has long recommended.

### 3.3 Approval Patterns: Three Models

Three primary HITL approval patterns have emerged in production AI systems:

#### Synchronous (Block-and-Wait)
The agent stops, requests approval, and cannot proceed until it receives it. This maximizes human control but creates a new cognitive burden: the developer must now monitor multiple agents, each of which may block at different times, requiring constant attention.

**Best for**: Irreversible actions, security-sensitive operations, first use of a new capability.

**Risk**: Blocks become interruptions that arrive at unpredictable times, maximizing switch costs.

#### Asynchronous (Proceed-and-Notify)
The agent takes the action and notifies the human after the fact, with a window to reverse if needed. This minimizes interruptions but requires that actions be reversible or low-risk.

**Best for**: Routine operations where the agent has high reliability, exploratory tasks in sandboxed environments.

**Risk**: Automation bias — developers stop checking notifications and fail to catch errors.

#### Checkpointed (Batch Approval)
The agent accumulates a set of proposed actions to a review queue. The developer reviews them in batch at a time of their choosing. This aligns human review with the developer's attention, not the agent's execution pace.

**Best for**: Long-running tasks, workflows where the developer needs to stay in flow on other work, situations where review requires context that is best accumulated before evaluation.

**Risk**: Requires well-designed review UX; if the queue grows large, review fatigue sets in.

The checkpointed pattern most closely mirrors how effective managers review team work — not monitoring every commit in real time, but reviewing PR summaries at the end of the day.

### 3.4 Automation Bias: The Over-Trust Problem

**Automation bias** is the tendency for humans to over-rely on automated recommendations, accepting them without sufficient scrutiny. Research published in *AI & Society* (2025) identifies it as one of the most significant challenges in human-AI collaboration.

Key findings:

- When supervising automated systems, humans demonstrate loss of situational awareness — they stop actively monitoring and instead passively observe.
- Automation bias is strongest when the system has been reliable for an extended period — humans calibrate trust upward based on past performance and fail to notice when reliability decreases.
- **Complacency** in automation monitoring is the primary failure mode: the human becomes a passive observer rather than an active supervisor.

For agent orchestration, this manifests as:

- Approving agent actions without reading them carefully, because "it's usually right."
- Failing to notice when an agent has gone off-course in a long session.
- Assuming that silence from an agent means success, when it may mean the agent is confidently pursuing the wrong approach.

Countering automation bias requires UX design that maintains appropriate friction: making it easy to review but requiring deliberate engagement rather than one-click approval.

---

## 4. Mental Models for Agent Management

### 4.1 The "Intern Manager" Metaphor

The intern manager metaphor — treating AI agents as capable but inexperienced human interns — is the most widely cited mental model in practitioner writing on agent workflows. Its utility is real but bounded.

**What makes it useful:**
- It calibrates appropriate trust: interns are capable but need supervision, clear briefs, and defined boundaries.
- It suggests appropriate delegation patterns: give the intern a well-scoped task with clear acceptance criteria, not open-ended latitude.
- It frames the human's role as oversight and direction, not execution.

**Where it breaks down:**
- Interns learn and remember; current agents do not. Each session starts fresh.
- Interns will push back when a task is unclear; agents may confidently proceed on ambiguous instructions.
- Interns can be held accountable for mistakes; agents cannot. The accountability remains with the developer.
- An intern's judgment improves over time through the relationship; an agent's judgment is static within a session.

The intern metaphor is useful for establishing the right emotional relationship with agents (trusting but supervisory), but it can mislead developers into expecting agents to accumulate context across sessions or to self-correct based on experience.

### 4.2 The "Git Branch" Metaphor

Each agent as a parallel branch of work is a metaphor that emerged directly from practitioner workflows using git worktrees. It maps well onto the technical architecture:

- Each agent works on an isolated branch with its own files.
- Branches are eventually merged (or discarded).
- Conflicts are resolved at merge time, not during parallel execution.
- The main branch represents validated, integrated work.

**What makes it useful:**
- It reinforces the isolation principle: branches should not depend on each other's in-progress work.
- It provides a mental model for conflict resolution: review before merge, not during parallel execution.
- Developers already understand branches as a risk management pattern.

**Where it breaks down:**
- Git branches don't have goals or intent — they don't get stuck or confused.
- The metaphor doesn't capture the interactive, conversational nature of agent sessions.
- It may underemphasize the importance of mid-session human intervention (you don't "interrupt" a branch).

### 4.3 The "Microservice" Metaphor

Each agent as an isolated service with defined inputs, outputs, and interfaces draws from software architecture principles.

**What makes it useful:**
- It emphasizes well-defined contracts between agents: clear inputs, clear expected outputs.
- It encourages thinking about agent-to-agent handoff as an API call: structured data, not informal narrative.
- It naturally raises questions about fault tolerance: what happens if this service fails? Who depends on it?

**Where it breaks down:**
- Microservices are deterministic and testable in isolation; agents are non-deterministic and context-sensitive.
- The metaphor may lead developers to over-engineer agent interfaces, losing the flexibility that makes LLM agents valuable.
- It underemphasizes the human's role: microservices don't need a manager, they need an architect and an operator.

### 4.4 What Experienced Practitioners Actually Use

Reviewing practitioner writing from developers who regularly run 5-20 parallel agent sessions, several patterns emerge:

1. **The campaign planner mental model**: Before starting, draw out the entire task graph — all the work that needs to happen, its dependencies, and which parts can run in parallel. Think of each agent as a campaign resource to be allocated.

2. **The assembly line mental model**: Sequential agents where each agent's output is the next agent's input — useful for pipeline-style workflows (plan → implement → test → review).

3. **The project board mental model**: Each agent has a "card" with status (working / blocked / waiting for review / done). The developer's job is to keep cards moving, not to do the work on the cards.

The most effective practitioners blend all three: plan the campaign, structure the assembly line, and track it on the project board.

### 4.5 Designing UX to Reinforce Good Mental Models

UX research on mental model alignment (Norman, 1988; "The Design of Everyday Things") establishes that the system image — what the UI shows — directly shapes the user's mental model of how the system works. If the UI shows agents as passive code-runners, users will treat them as such. If it shows them as active collaborators with goals and status, users will engage with them differently.

Design principles for mental model alignment in agent UX:

- **Show intent, not just activity**: Display what the agent is trying to accomplish, not just what it is currently doing.
- **Show blocks explicitly**: If an agent is stuck or needs input, this should be visually distinct from "working."
- **Show the task graph**: Make the dependency structure visible so developers understand what is blocking what.
- **Use familiar metaphors consistently**: Choose one primary metaphor and design the UI around it. Mixing metaphors in the same UI creates cognitive dissonance.

---

## 5. UX Patterns for Multi-Agent Workflows

### 5.1 Situation Awareness in Complex Systems

Mica Endsley's three-level model of **Situation Awareness** (1995) is the most cited framework in human factors for understanding operator performance in dynamic, complex systems. It was developed for aviation but has been applied to air traffic control, military operations, ICU nursing, and industrial process control.

The three levels:

| Level | Description | Failure Mode |
|-------|-------------|--------------|
| **Level 1: Perception** | Detecting the status of relevant elements in the environment | Missing a signal (agent blocked, error occurred) |
| **Level 2: Comprehension** | Understanding what the perceived data means in context | Misinterpreting an agent's current state |
| **Level 3: Projection** | Anticipating how the situation will evolve | Failing to predict that Agent A's delay will block Agent B |

Endsley's research identifies the primary cause of SA loss as **attentional tunneling**: the operator focuses on one part of the system in detail while losing awareness of others. In agent orchestration, this manifests as a developer spending an hour debugging Agent B's output while Agents A and C hit unattended blocks.

Dashboard design for complex systems should be optimized for all three levels:
- Level 1: Clear status indicators — at a glance, which agents are working, blocked, or waiting?
- Level 2: Compact context — what is each agent trying to do, and what was its last action?
- Level 3: Dependency visualization — if this agent is delayed, what else is affected?

### 5.2 Dashboard Design for Multi-Agent Systems

Research on control room design (nuclear, aviation, industrial) and more recently on DevOps observability dashboards converges on several principles:

**Information hierarchy**: The most critical information must be visible without scanning. Use visual salience (color, position, size) to rank information by urgency.

**Status vs. detail**: The primary view should be status (5-10 agents at a glance). Detail should be one click away, not primary. This is the progressive disclosure principle applied to dashboard design.

**Alert design**: Alerts should be specific and actionable. "Agent 3 needs input" is actionable. "Agent 3 is running" is not. Alert fatigue (too many non-urgent notifications) causes operators to disable alerting, eliminating the benefit.

**Temporal context**: Show recent history, not just current state. An agent that has been "working" for 5 minutes is different from one that has been "working" for 45 minutes with no output. Time-since-last-activity is a critical signal.

Practitioner Marc Nuri documented building an AI coding agent dashboard that provides cross-device visibility into multiple Claude Code sessions: "Running 5 to 10 Claude Code sessions across multiple machines quickly became unmanageable. Terminal tabs and tmux solve local organization but do not solve cross-device visibility."

### 5.3 Terminal and CLI UX for Concurrent Processes

The Unix ecosystem has decades of tooling for managing concurrent processes, and the patterns it has developed are instructive:

**tmux / screen**: Session persistence and multiplexing. The key innovation is that sessions outlive the terminal connection — they can be detached and resumed. For agent management, this is the critical primitive: an agent session that can be paused and resumed is a fundamentally more manageable artifact than one that must run continuously in view.

**kubectl**: The Kubernetes CLI models a cluster-as-database: you declare desired state (`kubectl apply`), query current state (`kubectl get pods`), and observe events (`kubectl describe`). The operator never directly manages individual processes; they manage declarative state. This pattern could translate to agent orchestration: declare what you want each agent to do, query their current status, and observe their event streams.

**supervisord**: Process supervision with automatic restart, log aggregation, and status reporting. The `supervisorctl status` command provides a clean multi-process status view that influenced later DevOps tooling. The key principle: the supervisor knows about all processes; the operator doesn't need to track them manually.

**Lessons for agent CLI UX:**
- Sessions should be detachable (the agent continues running even when the developer's terminal is closed).
- Status queries should be fast, read-only, and available without attaching to the session.
- Log streams should be aggregatable across sessions.
- The primary workflow should be: `status → inspect → interact → detach`, not `attach → work → detach`.

### 5.4 Session State: What Needs to Be Captured

When a developer switches away from an agent session, the cognitive burden of resumption comes from reconstructing session context. The question is: what is the minimum state that, if captured and re-presented at resume time, would allow a developer to re-engage meaningfully within 30 seconds?

Based on the prospective memory research (Altmann & Trafton, 2002) and practitioner experience, the essential session state components are:

| Component | Description | Priority |
|-----------|-------------|----------|
| **Current goal** | What is the agent trying to accomplish right now? | Critical |
| **Last completed action** | What did the agent last do successfully? | Critical |
| **Current blocker** | If stuck, what is the agent blocked on? | Critical |
| **Files changed** | Which files have been modified in this session? | High |
| **Decisions made** | Key choices the agent made (and why, if documented) | High |
| **Pending questions** | Any questions the agent has surfaced for the developer | High |
| **Progress against task** | Estimated % complete, or phase within task | Medium |
| **Time in session** | How long has this session been running? | Low |

The goal is not a complete log (that is the conversation history) but an **executive summary** that re-activates the developer's mental model of the session in seconds, not minutes.

### 5.5 Notification and Interruption Design

Research on interruption management (Bailey & Iqbal, 2008; "On the need for attention-aware systems") establishes that the cost of an interruption is not just the time to handle it — it is also the time to re-engage with the interrupted task. Interruptions during cognitively demanding work (deep focus) are significantly more costly than during transitional periods (between tasks).

**Design principles for agent interruptions:**

1. **Interrupt at natural breakpoints, not at agent events**: If the developer is reviewing Agent B's output, hold Agent A's "I need input" notification until the review is complete. Batch interruptions to natural transitions.

2. **Differentiate urgency clearly**: Not all agent states require immediate intervention. "Blocked and cannot proceed" is urgent. "Completed a phase and awaiting review" can wait for a batch review cycle.

3. **Make silence meaningful**: If an agent has not produced output in N minutes, this should be visible. Silence should be informative, not invisible.

4. **Give agents a "try something and tell me what you did" escape hatch**: Rather than interrupting for every ambiguity, agents should be able to make a best-effort attempt and document it for async review. This is the "proceed-and-notify" pattern applied to ambiguity resolution.

### 5.6 Progressive Disclosure in Complex Workflow UX

Progressive disclosure is a UX pattern that reduces cognitive load by revealing complexity incrementally as the user needs it. For a multi-agent CLI or dashboard:

- **Level 1 (default view)**: Names, statuses, and one-line descriptions. Enough to answer "is everything running?"
- **Level 2 (on request)**: Session summary, recent actions, files changed, pending questions.
- **Level 3 (deep dive)**: Full conversation history, file diffs, detailed logs.

Nielsen Norman Group research establishes that progressive disclosure reduces errors and cognitive load when users face unfamiliar complexity. For a developer new to running 5 agents in parallel, showing Level 3 information by default would be overwhelming and paralyzing. Starting at Level 1 and letting them drill down maintains orientation.

The NN/g guideline: keep progressive disclosure to **three levels or fewer**, with clear, intuitive navigation between levels.

---

## 6. Task Decomposition as a Skill

### 6.1 The Core Decomposition Problem

The Stanford researcher's recommended approach — understand the tasks, find the lines between them, assign isolated chunks — is a description of **work breakdown structure** (WBS) methodology applied to agentic workflows.

The key insight is that effective decomposition is a skill that precedes agent deployment. An agent given a poorly decomposed task will either:
- Ask many clarifying questions (interrupting the developer frequently), or
- Make implicit choices about scope and approach (potentially diverging from intent), or
- Get stuck when encountering the first genuine ambiguity (blocking indefinitely).

None of these outcomes are the agent's fault. They are decomposition failures.

### 6.2 Work Breakdown Structure Principles Applied to Agent Tasks

WBS methodology (PMBOK standard) decomposes project scope into hierarchical deliverables. The **100% rule** states that the WBS must include 100% of the work — nothing is assumed to be "handled elsewhere."

Applied to agent task design:

- **Define deliverables, not activities**: Tell the agent what done looks like, not step-by-step how to get there. Agents are capable of figuring out steps; they struggle with undefined acceptance criteria.
- **Explicit scope boundaries**: What is explicitly in scope, and what is explicitly out of scope? Without both, agents may expand scope ("while I'm in this file, let me also fix...") in ways that create conflicts with other agents.
- **Dependencies made explicit**: If Agent B's task requires Agent A's output, this must be stated — not assumed. Agents do not maintain awareness of each other.

### 6.3 What Makes a Task "Agent-Sized"?

Practitioner writing and the emerging literature on agentic coding identify several heuristics for right-sizing agent tasks:

**Good agent task characteristics:**
- Can be completed within a single conversation context (roughly: a few hundred lines of code, one module, one feature)
- Has clear acceptance criteria that can be verified programmatically or by inspection
- Does not require human judgment at intermediate steps (front-load decisions into the task brief)
- Is isolated: changes in this task do not conflict with changes in parallel tasks
- Has a defined start state (the files/codebase the agent should work from) and end state (what should be different)

**Signs a task is too large:**
- It touches many files across many modules
- It requires decisions that depend on the developer's architectural preferences (which haven't been specified)
- It has multiple logically independent sub-deliverables that could be validated separately
- Estimated completion time exceeds the developer's comfortable "hands-off" period

**Signs a task is too small:**
- The task brief is longer than the expected output
- The agent will spend more time on setup/teardown than on actual work
- The result cannot be meaningfully evaluated in isolation (it only makes sense as part of a larger piece)

### 6.4 Identifying Parallel Execution Boundaries

The critical question in decomposition for parallel agents is: **which tasks can run simultaneously without interfering with each other?**

Interference occurs when:
- Two agents modify the same file
- One agent's output is the other's input (sequential dependency)
- Two agents make conflicting architectural decisions
- Two agents both create new abstractions that overlap

Safe parallelism exists when:
- Tasks operate on different, non-overlapping file sets
- Tasks are at the same level of the dependency graph (neither depends on the other)
- Tasks have the same architectural constraints (set upfront) so independent decisions will be consistent

The git worktree pattern enforces file-level isolation structurally: each agent gets its own working directory and branch. This prevents file-level conflicts but does not prevent semantic conflicts (two agents making different decisions about the same interface that they each independently define).

### 6.5 Dependency Graphs for Task Planning

Directed Acyclic Graphs (DAGs) provide the formal foundation for representing task dependencies in multi-agent workflows. In a DAG:

- Each node is a task
- Each directed edge represents a dependency (A → B means "B depends on A's output")
- The acyclic constraint prevents circular dependencies (which would create deadlocks)

The practical value of thinking in DAGs:
- Nodes with no incoming edges can run immediately (in parallel)
- Critical path analysis reveals which task chain determines the total workflow duration
- If a node (agent) fails, all downstream dependents are known immediately

Tools like Apache Airflow, Prefect, and Dagster have built production workflow systems on DAG models. The patterns they use — retry with exponential backoff, checkpoint-based recovery, dependent task cancellation on upstream failure — are directly applicable to multi-agent orchestration.

DAG-Plan (2024 arxiv paper) demonstrates using LLMs to auto-generate DAG-structured task plans from high-level goals, enabling dynamic task decomposition that is dependency-aware from the start.

---

## 7. Error Recovery and Failure Handling in Orchestrated Workflows

### 7.1 The Compounding Error Problem

The most dangerous failure mode in multi-agent workflows is compounding errors: an incorrect assumption in step 3 propagates to steps 4, 5, and 6, each of which builds on the flawed foundation.

The math is instructive: if a five-step workflow has 95% reliability per step, the overall success rate is 0.95^5 = 77.4%. At 10 steps, it drops to 59.9%. As practitioner analysis documents:

> "A big challenge is error compounding across multiple steps in high-degrees-of-freedom environments — you need to succeed many times to succeed at the task, but you only need to hit a dead end once to fail at the task."

The implication: error recovery capability is not a nice-to-have but a fundamental determinant of whether a multi-step agentic workflow can succeed at all.

### 7.2 Early Detection: What the Developer Needs to See

When an agent goes off-course, early detection requires the developer to have visibility into **intermediate outputs**, not just final results. The signals that indicate potential compounding errors:

- **Scope creep**: The agent is modifying files it was not assigned to modify.
- **Novel abstractions**: The agent is creating new functions/classes/modules that were not in the brief.
- **Unexpected questions**: The agent is asking questions that suggest it misunderstood the task.
- **Silence with low velocity**: Long periods without output when the task should be progressing.
- **Inconsistency with prior sessions**: The agent's approach contradicts decisions made in an earlier session.

Research on failure transparency in distributed systems (OSDI 2000, University of Michigan) distinguishes:

- **Transparent failures**: The failure is visible and explicitly reported — the best case.
- **Silent failures**: The system continues operating while producing incorrect results — the worst case.

For agent workflows, silent failures are most dangerous. An agent that hallucinates a plausible-looking implementation, commits it, and reports success creates a silent failure that may not surface until integration or testing. The human detection mechanism must be designed for this case specifically: don't just check that the agent finished, verify that the output is correct.

### 7.3 Recovery Patterns

When an agent does fail or get stuck, four recovery patterns are applicable:

**Restart from checkpoint**: If the agent session has been checkpointed at intermediate states (Claude's file checkpointing provides this), roll back to the last known-good state and retry with revised instructions. This is analogous to git reset to a prior commit.

**Provide additional context**: The agent is stuck because it lacks information. The developer intervenes to provide the missing context (a design decision, an API reference, a clarification of scope) and lets the agent continue.

**Escalate to different agent**: Some tasks benefit from a different agent role (a planning agent if the execution agent is confused about goals; a debugging agent if the implementation agent is stuck on an error). Hand off the session context to a more appropriate agent.

**Human takeover**: The agent has gone far enough off-course that the fastest path forward is for the developer to complete the task directly, then use a new agent session for the next task. This should not be seen as failure — it is appropriate triage.

### 7.4 Designing for Good Handoffs

When a developer needs to take over from an agent, the quality of the handoff determines how much work is lost. A good agent handoff includes:

- What was completed (verified, working)
- What is in progress (and at what state)
- What was attempted and abandoned (and why)
- What the agent would have done next (its plan)
- Open questions or unresolved decisions

This is structurally identical to what a departing engineer writes in a handoff document when going on vacation. The agent should be able to produce this summary on request; the UX should make requesting it trivially easy.

---

## 8. The Iterative Agent Addition Pattern

### 8.1 The "Start with One" Principle

The Stanford researcher's recommendation is explicit and matches what industrial automation research has found:

> "I would build it up piece by piece. Start with one agent, get it working really well, add a second for an isolated task, then a third. Rather than 10 agents at once."

This principle — establish competence at n before adding n+1 — is called **incremental automation adoption** in human factors research and **staged rollout** in software engineering. It is not timidity; it is the most reliable path to a working multi-agent system.

The failure mode of starting with many agents simultaneously:

- The developer cannot distinguish agent-specific failure modes from orchestration failure modes.
- Trust cannot be calibrated because there is no baseline for individual agent performance.
- Recovery is difficult because failures are entangled across sessions.
- The cognitive load of monitoring many agents simultaneously prevents effective intervention.

### 8.2 Trust Calibration in Human-Automation Teaming

Research on trust in automation (Lee & See, 2004; Parasuraman & Riley, 1997) establishes that **calibrated trust** — trust that accurately reflects system reliability — is the goal. Both under-trust (using the automation less than its reliability warrants) and over-trust (using it more) lead to worse outcomes than appropriate trust.

Key findings from Frontiers in Robotics and AI (2021):

- Trust in automation develops incrementally through experience with the system.
- Trust calibration is particularly sensitive to **early failures** — a failure early in use produces more distrust than the same failure later.
- Trust does not recover symmetrically: a trust decrease from a failure is steeper and more durable than the trust increase from equivalent positive experiences.

For agent adoption, this means:
- Start with tasks where the agent can reliably succeed — build positive trust calibration first.
- Don't test agent limits with high-stakes tasks early. Use low-stakes tasks to calibrate trust.
- When an agent fails, address the failure explicitly and visibly — do not minimize it. Unaddressed failures create miscalibrated trust.
- As trust is established for specific task types, expand to adjacent, slightly more complex tasks.

Research from PMC (2024, "Calibrating workers' trust in intelligent automated systems") found that workers who received **transparency about system reliability** (including explicit acknowledgment of the system's known limitations) developed better-calibrated trust than those who were not informed.

### 8.3 Validation Criteria Before Adding Another Agent

Before adding agent n+1 to a workflow, the following should be true:

| Criterion | Question | Why It Matters |
|-----------|----------|----------------|
| **Task isolation verified** | Can agent n's task be fully completed without interfering with the planned agent n+1 task? | Prevents merge conflicts and semantic interference |
| **Monitoring established** | Can you observe agent n's status at a glance while also attending to agent n+1? | Prevents attentional tunneling |
| **Recovery tested** | Have you experienced and recovered from at least one failure of agent n? | Ensures recovery paths are known before they are needed in a more complex system |
| **Handoff protocol defined** | Is the output format of agent n defined well enough to be agent n+1's input? | Prevents context transfer failures |
| **Human overhead measured** | How much human time per hour does managing agent n require? | Validates that adding another agent is sustainable |

### 8.4 Incremental Automation in Industrial Systems: The Analogous Pattern

Factory automation adoption followed a similar pattern over decades. Manufacturing plants that introduced automation incrementally — one process at a time, with human expertise maintained alongside the automation — outperformed plants that attempted wholesale replacement of human processes.

The NASA/USAF "levels of automation" framework (Parasuraman, Sheridan & Wickens, 2000) provides a scale from fully manual to fully automatic, with research showing that optimal outcomes occur at intermediate levels — where the automation handles routine, well-specified work and the human handles exceptions, novel situations, and oversight.

For agent orchestration, the analogous levels are:

1. **Human does, agent observes** — agent watches and learns the task structure (not yet practical with current agents)
2. **Human does, agent assists** — agent suggests, human decides and executes
3. **Agent does, human reviews** — agent executes, human reviews before output is accepted
4. **Agent does, human spot-checks** — agent executes and outputs are accepted, with periodic human sampling
5. **Agent does autonomously** — human reviews only on exception

Most current developer-agent workflows should operate at level 3 for new task types, graduating to level 4 as trust is calibrated.

---

## 9. Implications for claude-kit

### 9.1 Current State and the Gap

claude-kit currently launches individual agent sessions via specialized team plugins. Each session is a discrete event: the developer starts a session, works with the agent, and the session ends. There is no cross-session state, no visibility into multiple concurrent sessions, and no protocol for structured handoffs between sessions or agents.

As developers begin running multiple simultaneous agent sessions — a pattern already common among advanced practitioners — this architecture creates specific friction points:

- No way to see all running sessions without attaching to each one individually.
- No session state captured at detach time; resumption requires reconstructing context from conversation history.
- No structured handoff when an agent completes work that another agent depends on.
- No enforcement of task isolation to prevent agents from interfering with each other's work.

The following recommendations address each friction point.

### 9.2 Session State Capture: The Auto-Summary Protocol

When a developer detaches from an agent session (or when a session reaches a natural checkpoint), claude-kit should automatically generate and persist a session summary. This addresses the prospective memory problem: the developer needs resumption cues encoded before the switch, not reconstructed after.

**Recommended session summary schema:**

```yaml
session:
  id: "auth-service-refactor-001"
  team: "backend-engineer"
  started_at: "2026-02-27T09:14:00Z"
  last_active: "2026-02-27T11:42:00Z"

task:
  goal: "Refactor authentication service to use JWT tokens, replacing session cookies"
  phase: "implementation"   # planning | implementation | testing | review
  progress: "65%"

last_action:
  description: "Implemented token issuance in auth.service.ts"
  files_changed:
    - "src/auth/auth.service.ts"
    - "src/auth/auth.module.ts"

next_action:
  description: "Implement token validation middleware"
  files_planned:
    - "src/auth/jwt.middleware.ts"

blockers:
  - "Needs decision: should token refresh be silent or require re-authentication?"

decisions_made:
  - "Used RS256 algorithm for token signing (not HS256) for security"
  - "Token TTL set to 15 minutes; refresh token TTL set to 7 days"

files_changed_this_session:
  - "src/auth/auth.service.ts"
  - "src/auth/auth.module.ts"
  - "src/auth/dto/login.dto.ts"
```

This summary is:
- Small enough to re-read in under 30 seconds.
- Specific enough to reconstruct working memory context.
- Structured enough to be machine-readable (for dashboard display and context injection).

### 9.3 Resume Handoff: Context Injection on Return

When a developer resumes a session, claude-kit should inject the session summary into the conversation context before the developer's first message. This mirrors the "implementation intention" pattern from prospective memory research: the developer's mental model is re-activated by re-presenting the context, not by requiring them to reconstruct it.

**Recommended resume prompt injection:**

```
[Resuming session: auth-service-refactor-001]

You last completed: Implementation of token issuance in auth.service.ts.
Your next planned action: Implement token validation middleware (src/auth/jwt.middleware.ts).
Blocker pending decision: Should token refresh be silent or require re-authentication?

Files changed this session: src/auth/auth.service.ts, src/auth/auth.module.ts, src/auth/dto/login.dto.ts.

Key decisions already made:
- RS256 algorithm for token signing
- 15-minute TTL for access tokens, 7-day TTL for refresh tokens

What would you like to do first?
```

This injection means the developer can return to a session after 2 hours on other work and be productive within 30 seconds.

### 9.4 Agent Status Dashboard: `claude-kit status`

A new `claude-kit status` command should provide a live view of all running and paused agent sessions, optimized for Endsley Level 1 and Level 2 situation awareness.

**Recommended output format (Level 1 — at a glance):**

```
claude-kit status

  ID                          TEAM               STATUS       LAST ACTIVE
  auth-service-refactor-001   backend-engineer   working      2 min ago
  payment-api-integration     backend-engineer   BLOCKED      47 min ago   [needs input]
  frontend-login-ui           frontend-engineer  review       18 min ago   [awaiting review]
  database-migration-v2       data-engineer      done         1 hr ago
```

**Level 2 detail (on `claude-kit status --detail <id>`):**

```
Session: payment-api-integration
Team: backend-engineer
Status: BLOCKED — Needs developer input

Blocker: Unable to determine the correct Stripe API version to target.
         The project has both stripe@12 and stripe@14 in package.json
         (likely a merge artifact). Which version should I use?

Last action: Implemented charge creation endpoint.
Next planned: Implement webhook handling.

Files changed: src/payments/payments.service.ts (142 lines added)
Running time: 1h 23min
```

This is the progressive disclosure pattern applied to session management: scan all agents in 5 seconds at Level 1; drill to a specific session in 10 seconds at Level 2; attach for full interaction at Level 3.

### 9.5 Checkpoint Commands: Explicit Handoff Points

claude-kit should support explicit **checkpoint declarations** in team plugin prompts — moments where the agent stops and requests human review before continuing.

**Proposed CLAUDE.md checkpoint syntax:**

```markdown
## Checkpoints

After completing each phase, emit:
CHECKPOINT: <phase-name>
Summary: <what was completed>
Validation needed: <what the developer should verify>
Next phase: <what happens after approval>
```

**Example checkpoint output from the agent:**

```
CHECKPOINT: implementation-complete

Summary: JWT authentication is implemented. Token issuance and storage
are complete. All unit tests pass locally.

Validation needed:
- Review src/auth/auth.service.ts for correctness
- Verify token TTL values match security requirements
- Confirm refresh token rotation strategy is acceptable

Next phase: Integration testing with existing API endpoints.
Type 'continue' to proceed, or provide corrections.
```

claude-kit detects this CHECKPOINT pattern, records it in the session state, surfaces it in `claude-kit status`, and holds the session until the developer responds. This implements the **checkpointed approval pattern** — batch review at natural phase boundaries rather than ad-hoc interruption.

### 9.6 Workflow Definitions: Multi-Agent Pipelines

For recurring multi-agent workflows (implement → test → review → integrate), claude-kit should support a **workflow plugin** that defines the sequence of agent sessions with explicit dependencies.

**Proposed workflow schema (`claude-kit/workflows/feature-development.yaml`):**

```yaml
workflow: feature-development
description: Standard feature implementation with testing and review

steps:
  - id: plan
    team: backend-engineer
    role: planner
    output: plan.md
    checkpoint: always   # always require human review before proceeding

  - id: implement
    team: backend-engineer
    role: engineer
    depends_on: [plan]
    input: plan.md
    isolation: worktree  # use git worktree isolation
    checkpoint: on-completion

  - id: test
    team: backend-engineer
    role: tester
    depends_on: [implement]
    input: implement.summary
    checkpoint: on-failure

  - id: review
    team: backend-engineer
    role: reviewer
    depends_on: [implement, test]
    checkpoint: always

  - id: integrate
    team: devops
    depends_on: [review]
    requires_human_approval: true   # never automate merges
```

This workflow definition:
- Makes dependencies explicit (DAG structure).
- Defines what information flows between steps (context bridging).
- Specifies checkpoint policies per step.
- Enforces that certain steps (integration) always require human approval.
- Enables `claude-kit run workflow feature-development` to orchestrate the entire pipeline.

### 9.7 Context Bridging: Agent-to-Agent Handoff Protocol

When Agent A's output becomes Agent B's input, the handoff quality determines whether Agent B starts with the right understanding or has to reconstruct it from raw files.

**Recommended context bridge format:**

```
[Handoff from: implement → test]
[Session: auth-service-refactor-001]

Completed work:
- JWT authentication implementation is complete.
- All functions are in src/auth/auth.service.ts and src/auth/jwt.middleware.ts.
- Token issuance, validation, and refresh are implemented.
- Unit tests written: src/auth/auth.service.spec.ts (18 tests, all passing).

What needs testing:
- Integration tests for the full authentication flow.
- Edge cases: expired tokens, invalid signatures, revoked tokens.
- Load behavior under concurrent authentication requests.

Known issues / TODOs:
- Refresh token rotation is not yet implemented (deferred to next session).
- Token revocation requires a Redis cache that is not yet set up.

Acceptance criteria for this phase:
- All integration tests pass.
- Token refresh flow works end-to-end in the test environment.
```

This bridges the context gap without requiring Agent B to read all of Agent A's conversation history or all modified files — it gives Agent B the same "executive summary" that a good engineer handoff would provide.

### 9.8 Enforcing Task Isolation

claude-kit's architecture should make task isolation structural, not aspirational. Several mechanisms:

**Worktree isolation by default**: Any session declared as part of a workflow with parallel peers should automatically use a git worktree. This is already supported in Claude Code's native tooling and should be the default for claude-kit workflows, not an opt-in.

**File scope declaration**: Team plugins for parallel tasks should declare which directories/files they are allowed to modify. claude-kit can surface a warning (not a block) if the agent modifies out-of-scope files.

**Shared state via explicit artifacts**: Agents that need to share information should do so through explicit, versioned artifacts (plan.md, spec.yaml, test-results.json) in defined handoff directories — not via direct file modification of each other's working trees. This enforces the microservice input/output contract pattern.

**Pre-run conflict check**: Before launching a parallel session, `claude-kit run` should check whether the new session's declared file scope overlaps with any running session's scope. If it does, warn before proceeding.

### 9.9 Summary: Feature Roadmap Priority

Translating the research into a prioritized feature list for claude-kit's multi-agent evolution:

| Priority | Feature | Research Basis |
|----------|---------|---------------|
| P0 | Session state auto-capture on detach | Prospective memory research; resumption costs |
| P0 | `claude-kit status` multi-session dashboard | Situation awareness; Level 1 SA design |
| P1 | Resume context injection | Implementation intentions; PM encoding |
| P1 | CHECKPOINT protocol in team plugins | Checkpointed approval pattern; HITL design |
| P1 | Worktree isolation as workflow default | Git branch metaphor; interference prevention |
| P2 | Workflow YAML definitions with DAG dependencies | DAG task planning; dependency graph design |
| P2 | Context bridge format for agent-to-agent handoff | Context transfer; handoff protocol |
| P2 | `claude-kit status --detail` Level 2 view | Progressive disclosure; SA Level 2 |
| P3 | File scope declaration and overlap detection | Task isolation; conflict prevention |
| P3 | Workflow execution engine (`claude-kit run workflow`) | Pipeline automation; incremental adoption |

The P0 items address the most immediate cognitive burden — the context switching cost on every session switch. The P1 items reduce the human overhead of maintaining oversight. The P2 and P3 items build toward a fully orchestrated multi-agent system.

### 9.10 The North Star

The north star for claude-kit's multi-agent UX is enabling a developer to manage five concurrent agent sessions with the same cognitive overhead they currently spend managing one. This requires:

- **Instant orientation**: Resume any session in under 30 seconds.
- **Ambient awareness**: Know the status of all sessions without attaching to any of them.
- **Structured intervention**: When an agent needs input, provide it in a structured, low-friction way that doesn't break flow.
- **Confident isolation**: Know that parallel agents are not interfering with each other, structurally.
- **Incremental trust**: Start with one, validate, expand — with tooling that makes each step visible.

This is, ultimately, what the researcher said: the skills of a good human manager, applied to agents. claude-kit's job is to make those skills easier to exercise — to be the tooling infrastructure that lets the developer's management judgment, not their memory and attention, be the binding constraint.

---

## Traces

- **Upstream:** Market signals, competitive analysis, user research
- **Downstream:** REQ-002 (Scope-Aware Planning), REQ-005 (Transparent Execution), REQ-006 (Autonomous Operation), REQ-009 (Cloud Platform)
- **Quality Attributes:** None identified

---

## 10. References

### Cognitive Science and Psychology

- Mayr, U., & Keele, S. W. (2000). Changing internal constraints on action: The role of backward inhibition. *Journal of Experimental Psychology: General*, 129(1), 4–26.
- Dodhia, R. M., & Dismukes, R. K. (2009). [Interruptions create prospective memory tasks.](https://onlinelibrary.wiley.com/doi/abs/10.1002/acp.1441) *Applied Cognitive Psychology*, 23(1), 73–89.
- Altmann, E. M., & Trafton, J. G. (2002). [Preparing to resume an interrupted task: Effects of prospective goal encoding and retrospective rehearsal.](https://www.sciencedirect.com/article/abs/pii/S1071581903000235) *International Journal of Human-Computer Studies*, 58(5), 583–603.
- Oberauer, K. (2009). Working Memory Costs of Task Switching. *Journal of Experimental Psychology: Learning, Memory, and Cognition*, 34(3), 478–494. [Abstract.](https://www.ovid.com/journals/jeplm/abstract/10.1037/0278-7393.34.3.478~working-memory-costs-of-task-switching)
- Switching between different cognitive strategies induces switch costs. *Scientific Reports* (2024). [Nature.](https://www.nature.com/articles/s41598-024-56836-2)
- Task Switching: On the Relation of Cognitive Flexibility with Cognitive Capacity. *PMC* (2023). [PMC.](https://pmc.ncbi.nlm.nih.gov/articles/PMC10140903/)
- The 'switch cost' of multitasking. Wake Forest News (2024). [WFU.](https://news.wfu.edu/2024/04/16/the-switch-cost-of-multitasking/)
- Digital multitasking and hyperactivity: unveiling the hidden costs to brain health. *PMC* (2024). [PMC.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11543232/)
- Prospective memory research overview. [ScienceDirect Topics.](https://www.sciencedirect.com/topics/neuroscience/prospective-memory)
- Grundgeiger, T., et al. (2009). [Distributed Prospective Memory: Understanding how Nurses Remember Tasks.](https://journals.sagepub.com/doi/10.1177/154193120905301127) *Proceedings of the Human Factors and Ergonomics Society Annual Meeting.*

### Human Factors and Automation

- Endsley, M. R. (1995). [Toward a Theory of Situation Awareness in Dynamic Systems.](https://journals.sagepub.com/doi/10.1518/001872095779049543) *Human Factors*, 37(1), 32–64.
- Endsley, M. R. (2015). [Situation Awareness Misconceptions and Misunderstandings.](https://journals.sagepub.com/doi/10.1177/1555343415572631) *Journal of Cognitive Engineering and Decision Making*, 9(1), 4–32.
- Parasuraman, R., Sheridan, T. B., & Wickens, C. D. (2000). A model for types and levels of human interaction with automation. *IEEE Transactions on Systems, Man, and Cybernetics*.
- Fitts, P. M. (Ed.) (1951). Why the Fitts list has persisted throughout the history of function allocation. [Springer.](https://link.springer.com/article/10.1007/s10111-011-0188-1)
- Roth, E. M., et al. (2019). [Function Allocation Considerations in the Era of Human Autonomy Teaming.](https://journals.sagepub.com/doi/full/10.1177/1555343419878038) *Journal of Cognitive Engineering and Decision Making.*
- Adaptive Cognitive Mechanisms to Maintain Calibrated Trust. *Frontiers in Robotics and AI* (2021). [Frontiers.](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.652776/full)
- Calibrating workers' trust in intelligent automated systems. *PMC* (2024). [PMC.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11573890/)
- Measuring and Understanding Trust Calibrations for Automated Systems. *CHI 2023*. [ACM DL.](https://dl.acm.org/doi/fullHtml/10.1145/3544548.3581197)
- Calibrating Trust, Reliance and Dependence in Variable-Reliability Automation. *PMC* (2024). [PMC.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11655268/)
- Overreliance on AI: Literature review. Microsoft Research (2022). [Microsoft.](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/06/Aether-Overreliance-on-AI-Review-Final-6.21.22.pdf)
- Exploring automation bias in human–AI collaboration. *AI & Society* (2025). [Springer.](https://link.springer.com/article/10.1007/s00146-025-02422-7)

### Human-in-the-Loop AI Design

- Humans in the Loop: The Design of Interactive AI Systems. Stanford HAI. [Stanford HAI.](https://hai.stanford.edu/news/humans-loop-design-interactive-ai-systems)
- Human-in-the-loop in AI workflows: Meaning and patterns. [Zapier Blog.](https://zapier.com/blog/human-in-the-loop/)
- How to Design a Human in the Loop Agent Flow Without Killing Velocity. [Medium / Rose Digital.](https://medium.com/rose-digital/how-to-design-a-human-in-the-loop-agent-flow-without-killing-velocity-fe96a893525e)

### UX Design and Progressive Disclosure

- Progressive Disclosure. Nielsen Norman Group. [NN/g.](https://www.nngroup.com/articles/progressive-disclosure/)
- Norman, D. (1988). *The Design of Everyday Things.* Basic Books.
- Progressive disclosure in UX design: Types and use cases. [LogRocket Blog.](https://blog.logrocket.com/ux-design/progressive-disclosure-ux-types-use-cases/)

### Project Management and Task Decomposition

- Work breakdown structure (WBS) in project management: Full guide. [Wrike.](https://www.wrike.com/project-management-guide/faq/what-is-work-breakdown-structure-in-project-management/)
- What Is a DAG? Directed Acyclic Graph Explained. [Databricks Glossary.](https://www.databricks.com/glossary/dag)
- DAG-Plan: Generating Directed Acyclic Dependency Graphs (2024). [arXiv.](https://arxiv.org/pdf/2406.09953)
- Agentic AI workflows in Directed Acyclic Graphs. [Medium.](https://medium.com/@siddhardha/agentic-ai-workflows-in-directed-acyclic-graphs-dags-intro-5d00444124dd)
- Directed Acyclic Graphs: The Backbone of Modern Multi-Agent AI. [Medium.](https://santanub.medium.com/directed-acyclic-graphs-the-backbone-of-modern-multi-agent-ai-d9a0fe842780)

### Manager / IC Transition Research

- Break Free from the Individual Contributor Mindset. *Towards Data Science.* [TDS.](https://towardsdatascience.com/break-free-from-the-ic-mindset-you-are-a-manager-now-b3890f0bfce2/)
- The Mental Shift From Individual Contributor to Manager. *Great Manager / Jhana.* [Medium.](https://greatmanager.co/the-mental-shift-from-individual-contributor-to-manager-df89b4421713)
- Charan, R., Drotter, S., & Noel, J. (2001). *The Leadership Pipeline.* Jossey-Bass.

### Multi-Agent Orchestration: Architecture and Practitioner Writing

- AI Agent Orchestration Patterns. Microsoft Azure Architecture Center. [Microsoft Learn.](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- Design Patterns for AI Agents: Orchestration & Handoffs. [Skywork AI Blog.](https://skywork.ai/blog/ai-agent-orchestration-best-practices-handoffs/)
- Multi-agent workflows often fail. Here's how to engineer ones that don't. *GitHub Blog.* [GitHub.](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/)
- Conductors to Orchestrators: The Future of Agentic Coding. *O'Reilly Radar.* [O'Reilly.](https://www.oreilly.com/radar/conductors-to-orchestrators-the-future-of-agentic-coding/)
- How to Run Coding Agents in Parallel. *Towards Data Science.* [TDS.](https://towardsdatascience.com/how-to-run-coding-agents-in-parallell/)
- Multi-Agent Orchestration: Running 10+ Claude Instances in Parallel. *DEV Community.* [DEV.](https://dev.to/bredmond1019/multi-agent-orchestration-running-10-claude-instances-in-parallel-part-3-29da)

### Practitioner Tools and Tooling Research

- ccswitch: Run Multiple Claude Code Sessions Without Conflicts. [ksred.com.](https://www.ksred.com/building-ccswitch-managing-multiple-claude-code-sessions-without-the-chaos/)
- Claude Squad — Manage multiple AI terminal agents. [GitHub.](https://github.com/smtg-ai/claude-squad)
- claude-flow — Agent orchestration platform. [GitHub.](https://github.com/ruvnet/claude-flow)
- AI Coding Agent Dashboard: Orchestrating Claude Code Across Devices. *Marc Nuri Blog.* [blog.marcnuri.com.](https://blog.marcnuri.com/ai-coding-agent-dashboard)
- Mastering Git Worktrees with Claude Code for Parallel Development. [Medium.](https://medium.com/@dtunai/mastering-git-worktrees-with-claude-code-for-parallel-development-workflow-41dc91e645fe)
- How we're shipping faster with Claude Code and Git Worktrees. *incident.io.* [incident.io.](https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees)
- Note to a Friend — How I Run Claude Code Agents in Parallel. [WorksForNow.](https://worksfornow.pika.page/posts/note-to-a-friend-how-i-run-claude-code-agents-in-parallel)
- Rewind file changes with checkpointing. Claude Platform Docs. [Anthropic.](https://platform.claude.com/docs/en/agent-sdk/file-checkpointing)
- Agent Failure Modes: Compounding Errors and Invisible Failures. [Substack.](https://pleasebringstrangethings.substack.com/p/agent-failure-modes-compounding-errors)
- When agents fail: compounding errors in organisational systems. [Substack.](https://chrispedder.substack.com/p/when-agents-fail-compounding-errors)
- Failure transparency. [Wikipedia.](https://en.wikipedia.org/wiki/Failure_transparency)
- Exploring Failure Transparency and the Limits of Generic Recovery. OSDI 2000. [USENIX.](https://www.usenix.org/conference/osdi-2000/exploring-failure-transparency-and-limits-generic-recovery)
