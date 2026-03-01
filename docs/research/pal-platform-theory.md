# PAL as a Platform Service: From Process Documents to Product Development Infrastructure

> A vision document for evolving the Process Asset Library from a collection of
> markdown files into a self-hosted platform that manages the full product
> development lifecycle — requirements, traceability, quality gates, and AI agent
> integration — across organizations and products.

**Date:** 2026-03-01
**Governing Process:** PROC-LC-001 (Market Analysis)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Problem with PAL Today](#2-the-problem-with-pal-today)
   - 2.1 [What PAL Is](#21-what-pal-is)
   - 2.2 [Where It Breaks Down](#22-where-it-breaks-down)
   - 2.3 [The Fundamental Category Error](#23-the-fundamental-category-error)
3. [The Three-Level Architecture](#3-the-three-level-architecture)
   - 3.1 [Platform Level: The Operating System for Product Development](#31-platform-level-the-operating-system-for-product-development)
   - 3.2 [Process Level: The Rulebook as a Service](#32-process-level-the-rulebook-as-a-service)
   - 3.3 [Product Level: Repos That Reference, Not Contain](#33-product-level-repos-that-reference-not-contain)
   - 3.4 [How the Levels Interact](#34-how-the-levels-interact)
4. [Seamless Without Compromise](#4-seamless-without-compromise)
   - 4.1 [Requirements as Living Objects](#41-requirements-as-living-objects)
   - 4.2 [Automated Traceability](#42-automated-traceability)
   - 4.3 [Test Evidence from CI, Not Markdown](#43-test-evidence-from-ci-not-markdown)
   - 4.4 [ADRs Stay in Repos](#44-adrs-stay-in-repos)
   - 4.5 [Invisible Process Enforcement](#45-invisible-process-enforcement)
5. [The Integration Model](#5-the-integration-model)
   - 5.1 [VCS Agnosticism](#51-vcs-agnosticism)
   - 5.2 [Project Management Agnosticism](#52-project-management-agnosticism)
   - 5.3 [Authentication and Identity](#53-authentication-and-identity)
   - 5.4 [Bidirectional Sync, Not Data Ownership](#54-bidirectional-sync-not-data-ownership)
6. [AI-Native Development Cycle](#6-ai-native-development-cycle)
   - 6.1 [AI Agents as First-Class Participants](#61-ai-agents-as-first-class-participants)
   - 6.2 [Full Observability](#62-full-observability)
   - 6.3 [Autonomy Boundaries](#63-autonomy-boundaries)
   - 6.4 [Process Rules as API Context](#64-process-rules-as-api-context)
7. [Self-Hosted Architecture](#7-self-hosted-architecture)
   - 7.1 [Kubernetes-Native Deployment](#71-kubernetes-native-deployment)
   - 7.2 [Multi-Tenancy Model](#72-multi-tenancy-model)
   - 7.3 [The Platform as Its Own Product](#73-the-platform-as-its-own-product)
8. [Component Architecture](#8-component-architecture)
   - 8.1 [Auth Service](#81-auth-service)
   - 8.2 [Organization and User Management](#82-organization-and-user-management)
   - 8.3 [Product Registry](#83-product-registry)
   - 8.4 [Requirements Engine](#84-requirements-engine)
   - 8.5 [Process Configurator](#85-process-configurator)
   - 8.6 [Integration Layer](#86-integration-layer)
   - 8.7 [CI/CD Hooks](#87-cicd-hooks)
   - 8.8 [Dashboard and UI](#88-dashboard-and-ui)
   - 8.9 [AI Agent Gateway](#89-ai-agent-gateway)
   - 8.10 [Notification System](#810-notification-system)
9. [Licensing and Business Model](#9-licensing-and-business-model)
10. [Incremental Build Strategy](#10-incremental-build-strategy)
    - 10.1 [What Not to Build First](#101-what-not-to-build-first)
    - 10.2 [The Standing-Start MVP](#102-the-standing-start-mvp)
    - 10.3 [Layered Expansion](#103-layered-expansion)
11. [Product-Platform Relationship](#11-product-platform-relationship)
    - 11.1 [claude-kit as the First Managed Product](#111-claude-kit-as-the-first-managed-product)
    - 11.2 [The Platform Managing Itself](#112-the-platform-managing-itself)
    - 11.3 [From Submodule to Webhook](#113-from-submodule-to-webhook)
12. [Open Questions and Design Decisions](#12-open-questions-and-design-decisions)
13. [Sources and Prior Art](#13-sources-and-prior-art)

---

## 1. Executive Summary

The Process Asset Library (PAL) was created to solve a real problem: product
development needs structure, traceability, and quality enforcement. The current
implementation — 37 markdown documents installed as a git submodule, validated by
bash scripts — proves the concepts are sound. But the implementation model is
wrong.

Process documents that nobody reads end-to-end are not governance. Template
compliance enforced by shell scripts is bureaucracy. Manual cross-references
typed by hand will drift. Requirements stored inside individual repos live at the
wrong level of abstraction. A submodule that gets installed into every repo is
coupling without benefit.

This paper proposes a different architecture: PAL as a **platform service**. A
self-hosted, Kubernetes-native system that manages organizations, products,
requirements, and the full development lifecycle. Process enforcement becomes
invisible infrastructure — CI checks, PR templates, webhook validations,
dashboard queries — not INDEX.md files. Requirements live in the platform and
cascade from strategic vision down to implementation tasks. Traceability is
computed from commit metadata, PR fields, and CI output, not written by hand in
`## Traces` sections.

The platform operates at three levels: a **platform level** (auth, orgs,
products, the operating system for development), a **process level** (the
rulebook, configured not installed), and a **product level** (individual repos
connected via lightweight integrations). This architecture lets the platform
serve multiple organizations, multiple products per organization, and multiple
repos per product — all while enforcing tailored process rules without requiring
any repo to carry process infrastructure.

The vision is ambitious. The incremental path is not. The current docs/ layer in
repos like claude-kit is a fine stand-in until platform components exist. The
process framework itself — the concepts PAL encodes — remains valid regardless of
delivery mechanism. The build strategy starts narrow: requirements management,
GitHub integration, authentication. Everything else layers on incrementally.

---

## 2. The Problem with PAL Today

### 2.1 What PAL Is

PAL (Process Asset Library) is a collection of process documents that define how
software products should be developed. It currently lives at
`MateoSegura/process-asset-library` and is consumed by product repos as a git
submodule. Its contents include:

- **Process definitions** (PROC-LC-*, PROC-SP-*, PROC-ORG-*, PROC-GOV-*) that
  describe lifecycle phases, support activities, organizational standards, and
  governance overlays.
- **Templates** for requirements, architecture decisions, specs, test evidence,
  and other document types.
- **Validation scripts** that check structural compliance — do INDEX.md files
  exist, are document IDs unique, do cross-references resolve, are status fields
  valid.
- **A MkDocs Material documentation site** for browsing the process library.

The intent is sound: every product should follow consistent processes, produce
traceable artifacts, and meet quality standards. The implementation choices are
where problems emerge.

### 2.2 Where It Breaks Down

**37 process documents that nobody reads end-to-end.** A process document is
useful at the moment it applies — when you are writing a requirement, when you
are making an architecture decision, when you are creating test evidence. A
monolithic library of 37 documents is not useful as a reference. Engineers do not
read PROC-LC-002 before writing a requirement. They either already know the
format or they copy from an example. The documents exist to satisfy a governance
model, not to help engineers work.

**Template compliance enforced by bash scripts.** `validate-docs.sh` checks
that INDEX.md files exist, that document IDs follow naming patterns, that
cross-references resolve. This is structure validation, and structure is the
easiest thing to get right and the least important thing to enforce. A perfectly
structured document with shallow content passes validation. A deep, thoughtful
analysis with a missing `## Traces` section fails. The scripts check what is
easy to check, not what matters.

**Manual cross-references that humans type by hand.** The `## Traces` section
in every document expects humans to manually list related documents:
`See REQ-001 (Domain Knowledge Injection)`. These references are typed, not
computed. They drift immediately. A requirement gets renamed, and every document
that references it silently points at a stale name. The validation script checks
that referenced IDs resolve to files — but it cannot check that the semantic
relationship is still accurate.

**Requirements in the repo.** Requirements like REQ-001, REQ-002 live inside
`docs/requirements/` in the product repo. This is the wrong level of
abstraction. Requirements describe *what the product should do* — they are a
product-level concern that spans the entire product lifecycle. Storing them
inside one repo (among potentially many repos that compose a product) creates an
ownership problem. Which repo is the source of truth? What happens when a
requirement spans multiple repos? The answer today is "pick a repo and put them
there." That does not scale.

**A submodule that gets installed into repos.** PAL is consumed via
`git submodule add`. This means every product repo carries a copy of the entire
process library. Updates require `git submodule update --remote`. Developers
who do not regularly update the submodule work against stale processes. The
submodule adds cognitive overhead to every `git clone` (the `--recurse-submodules`
flag), pollutes the repo with process infrastructure that is not product code,
and creates merge conflicts when the submodule pointer changes.

**Validation scripts checking structure, not quality.** The most important
question about a requirement is: *is it complete, clear, testable, and
correctly prioritized?* No bash script can answer that. The validation layer
spends its time on whether files exist in the right directories and follow the
right naming convention. These are prerequisites to quality, not quality itself.
Structural validation creates the illusion of rigor without delivering it.

### 2.3 The Fundamental Category Error

The root problem is a **category error**: treating process governance as a
documentation problem. PAL's current model says "write documents that describe
your processes, store them in a repo, validate their structure." But process
governance is not about documents. It is about **behavior** — ensuring that the
right things happen at the right time, that decisions are traceable, that
quality gates are enforced, that nothing falls through cracks.

Documents can describe desired behavior. They cannot enforce it. Bash scripts can
enforce structural rules about documents. They cannot enforce behavioral rules
about development. The gap between "we have process documents" and "our processes
are followed" is the gap that a platform service closes.

---

## 3. The Three-Level Architecture

The platform vision separates concerns into three levels, each with distinct
responsibilities, data ownership, and interaction patterns.

### 3.1 Platform Level: The Operating System for Product Development

The platform level is the centralized, self-hosted system that everything else
connects to. Think of it as the operating system for product development — it
provides identity, access control, organizational structure, and the runtime
services that all products and processes depend on.

**Responsibilities:**

- **Authentication and authorization.** Users sign in via GitHub, Google, or
  custom SSO. The platform manages roles (org admin, product owner, developer,
  auditor) and permissions (who can create requirements, who can approve
  releases, who can view dashboards).

- **Organization management.** Multi-tenant by design. Each organization is an
  isolated unit with its own users, products, process configurations, and data.
  An organization might be a company, a team, or an individual developer with
  multiple products.

- **Product registry.** Every product is registered in the platform. A product
  has a name, a description, one or more linked repositories, a requirement
  tree, and a configured process profile. The registry is the single source of
  truth for "what products exist and what state are they in."

- **Cross-cutting services.** Notifications, audit logs, API keys, webhook
  management, integration credentials. The platform provides these to all
  other levels.

The platform level does not contain product code, process definitions, or domain
knowledge. It is infrastructure — the substrate on which processes and products
operate.

### 3.2 Process Level: The Rulebook as a Service

The process level is where PAL's concepts live — but as service configuration,
not markdown files. Instead of 37 documents describing how work should be done,
the platform offers a **process configurator** where organizations define their
development workflow.

**What changes from today:**

| Today (PAL as files) | Tomorrow (PAL as service) |
|---|---|
| PROC-LC-002 describes how to write requirements | The requirements engine enforces a schema, fields, and approval workflow |
| Templates in `templates/` define document structure | The platform provides forms with validation, not blank markdown files |
| `validate-docs.sh` checks structural compliance | CI checks validate that PRs reference valid requirements and have approval |
| `## Traces` sections list related documents manually | Traceability is computed from PR metadata, commit messages, and CI output |
| Process documents are versioned in git | Process configurations are versioned in the platform with audit trails |
| Updating processes means merging a PR to the PAL repo | Updating processes means changing configuration in the platform UI |

**What stays the same conceptually:**

- The lifecycle phases (research, requirements, architecture, specs, testing,
  operations) still exist as conceptual stages.
- Quality gates between phases still enforce that work meets standards before
  advancing.
- Traceability from vision to implementation to verification is still the
  core governance model.
- The process framework is still opinionated about what artifacts matter and
  how they relate.

The difference is the delivery mechanism. Processes are **configured** in the
platform, not **installed** into repos. They **enforce through infrastructure**
(CI checks, PR templates, approval workflows), not through **documentation
compliance** (bash scripts validating markdown structure).

### 3.3 Product Level: Repos That Reference, Not Contain

The product level is where actual code lives — repositories like claude-kit.
The critical shift is that product repos become **lighter**. They no longer carry
process infrastructure, requirements documents, or validation scripts for
governance artifacts.

**What stays in the repo:**

- Source code.
- Architecture Decision Records (ADRs) — these are code-coupled by nature.
  The decision to use a specific data structure, adopt a dependency, or change
  an API design is meaningfully tied to the codebase. ADRs stay local, but
  simplified: decision, context, alternatives considered, outcome.
- Technical specs and design documents that are implementation-specific.
- Tests and test configuration.
- CI/CD pipeline definitions.

**What moves to the platform:**

- Requirements (REQ-*). They live in the platform's requirements engine and
  are referenced from PRs and commits, not stored as files.
- Process definitions. No more submodule. No more `pal/` directory.
- Quality metrics and compliance status. Computed by the platform from CI
  output and PR metadata, not maintained as documents.
- Test evidence as structured data. CI produces test results; the platform
  ingests and links them to specs and requirements.
- Cross-product traceability. When multiple repos compose a product, the
  platform tracks which requirements are addressed by which repos.

**The integration mechanism** is a webhook plus a CI check, not a submodule:

1. The repo registers with the platform (a one-time setup).
2. PRs include a `Requirement:` field in the description (enforced by a CI
   check provided by the platform).
3. Commits optionally reference requirements in their messages using
   conventional-commit-style scopes: `feat(REQ-012): add encryption support`.
4. The platform's CI check validates that referenced requirements exist, are
   in the correct status, and that the PR has necessary approvals.
5. On merge, the platform updates requirement status, computes traceability
   links, and generates release note fragments.

This is a lightweight touch. The repo does not need to know about the platform's
internals. It sends webhooks and receives CI check results. That is the entire
integration surface.

### 3.4 How the Levels Interact

```
Platform Level (self-hosted Kubernetes)
├── Auth, Orgs, Users, Roles
├── Product Registry
├── Requirements Engine
├── Process Configurator
├── Integration Layer ─────────────────── webhooks ──┐
├── Dashboard / UI                                    │
└── AI Agent Gateway                                  │
                                                      │
         ┌────────────────────────────────────────────┘
         │
Product Level (git repos)                Process Level (platform config)
├── Source code                           ├── Lifecycle phases (configured)
├── ADRs (local)                          ├── Quality gate rules
├── Tech specs (local)                    ├── Approval workflows
├── Tests                                 ├── Template schemas
├── CI/CD pipelines                       ├── Enforcement rules
│   └── Platform CI check ◄──────────────┤   (applied via CI checks)
└── .platform.yml (integration config)    └── Audit trail
```

The arrows are intentionally one-directional for data flow: the platform reads
from repos (via webhooks) and writes back (via CI checks and status updates).
The repo never needs to query the platform at build time — the CI check is a
GitHub/GitLab check run that the platform posts asynchronously.

---

## 4. Seamless Without Compromise

The title of this section is aspirational and precise. The goal is process rigor
that does not feel like process rigor. Engineers should experience the platform
as helpful infrastructure, not as bureaucratic overhead. Every enforcement
mechanism should be invisible during normal workflow and visible only when
something is actually wrong.

### 4.1 Requirements as Living Objects

In the current model, a requirement is a markdown file in `docs/requirements/`
with a YAML frontmatter block. It has a status field that someone manually
updates. It has a `## Traces` section where someone manually lists related
documents. It exists in one repo even if the requirement spans the entire
product.

In the platform model, a requirement is a **living object** in the requirements
engine:

- **Hierarchical.** A CEO defines product vision ("Build an AI-native developer
  productivity platform"). That vision decomposes into strategic goals ("Support
  multi-team plugin development"). Strategic goals decompose into features
  ("Plugin validation with semantic review"). Features decompose into
  implementation requirements ("CLI validates plugin frontmatter structure").
  This hierarchy is explicit and navigable, not implied by naming conventions.

- **Stateful.** Requirements move through lifecycle states: `draft` ->
  `approved` -> `in-progress` -> `implemented` -> `verified`. State transitions
  are triggered by events: a PR is opened (draft -> in-progress), tests pass
  (implemented -> verified). Some transitions require human approval. The
  platform enforces the state machine — you cannot mark a requirement as
  verified if no test evidence exists.

- **Connected.** Every requirement knows which PRs reference it, which commits
  touch it, which test runs verify it, which releases include it. These
  connections are computed from real events, not typed by hand.

- **Owned.** Each requirement has an owner — the person responsible for its
  completeness and correctness. Ownership is visible in the dashboard. When a
  requirement is blocked or stale, the owner gets notified.

### 4.2 Automated Traceability

Traceability in the current model is a manual exercise. Developers type
`See REQ-001 (Domain Knowledge Injection)` in `## Traces` sections. This is
labor-intensive, error-prone, and impossible to keep current across many
documents.

In the platform model, traceability is computed from three sources:

1. **PR metadata.** PR descriptions include a `Requirement:` field (e.g.,
   `Requirement: REQ-012`). The platform's CI check validates this field and
   records the link. PR templates generated by the platform pre-populate this
   field with suggested requirements based on the changed files.

2. **Commit messages.** Commits using conventional commit syntax with
   requirement scopes (`feat(REQ-012): add encryption support`) create links
   automatically. The platform parses commit messages on webhook events.

3. **CI output.** Test suites produce structured output (JUnit XML, TAP, or
   JSON). The platform ingests test results and links them to the specs they
   verify. A spec references which test suites cover it (configured once); the
   platform checks whether those suites passed in the latest CI run.

The result is a traceability matrix that updates itself:

```
Requirement REQ-012: Plugin encryption support
├── Architecture: ADR-007 (in repo: claude-kit)
├── Spec: SPEC-015 (in repo: claude-kit)
├── Implementation:
│   ├── PR #47: feat(REQ-012): add encryption support (merged)
│   ├── PR #52: fix(REQ-012): handle empty plugin dirs (merged)
│   └── 14 commits across 2 PRs
├── Verification:
│   ├── test-cli.sh: 3/3 encryption tests passing
│   └── validate-plugins.py: encryption roundtrip check passing
└── Status: verified (auto-computed)
```

No human wrote this. It was assembled from PR metadata, commit messages, and CI
output. When PR #52 merged, the platform updated the implementation section
automatically. When the CI run passed, the verification section updated. The
status transitioned to `verified` because all required evidence was present.

### 4.3 Test Evidence from CI, Not Markdown

Today, test evidence is a markdown file in `docs/testing/evidence/` with a
prefix like TEST-001. Someone writes this file, describes what was tested, and
links to the spec it covers. This is documentation *about* testing, not testing
itself.

In the platform model, test evidence **is CI output**. Tests run in CI, produce
results, and the platform ingests those results as structured data. A spec's
verification status is determined by whether the linked test suites pass — not
by whether someone wrote a markdown file saying they tested it.

This eliminates an entire category of work: maintaining test evidence documents.
It also eliminates the failure mode where a test evidence document says
"all tests pass" but the actual CI has been failing for a week.

The platform still supports narrative test documentation for cases that require
it — exploratory testing notes, manual verification checklists, performance
testing analysis. But these are supplements to CI evidence, not replacements.

### 4.4 ADRs Stay in Repos

Architecture Decision Records are the one artifact type that belongs in the
repo. An ADR about "why we chose SQLite over PostgreSQL for local storage" is
meaningfully coupled to the codebase that uses SQLite. Moving it to an external
platform would sever that coupling.

However, ADRs in the platform model are simplified:

- **Fewer required fields.** Decision, context, alternatives considered, outcome.
  No `## Traces` section (the platform computes traces). No status management
  (an ADR is either current or superseded — the immutability rule still applies).
- **Platform awareness.** The platform knows about ADRs because the repo's CI
  check reports them. The platform can index ADRs across all repos in a product,
  making it possible to search "what architectural decisions have been made
  across the entire product" without opening each repo individually.
- **Lightweight linking.** An ADR can reference a requirement by ID
  (`Requirement: REQ-012`). The platform picks up this reference and adds it to
  the traceability graph. The ADR author does not need to maintain bidirectional
  links.

### 4.5 Invisible Process Enforcement

The litmus test for process enforcement is: **does the engineer feel like they
are following a process, or does the process just happen?**

Examples of invisible enforcement:

- A PR is opened. The platform's CI check fires. It validates that the
  `Requirement:` field references a valid, approved requirement. If not, the
  check fails with a clear message: "Referenced requirement REQ-999 does not
  exist. Did you mean REQ-099?" The developer fixes it and pushes. The check
  passes. Total friction: one failed CI check, one commit to fix it.

- A release is tagged. The platform computes requirement coverage: which
  requirements are marked for this release, which have been implemented, which
  have been verified. If coverage is below the configured threshold, the release
  pipeline pauses and notifies the product owner. The developer does not need to
  manually check coverage — it is computed.

- A requirement is approved. The platform generates a PR template for repos
  linked to that requirement, pre-populated with the requirement reference,
  acceptance criteria, and links to related ADRs. The developer creates a PR
  from the template and starts coding. The scaffolding is done.

Examples of what is NOT invisible (and should not be):

- Quality review. A human reviews the requirement's completeness. A human
  reviews the ADR's reasoning. A human reviews the PR's code. These are
  judgment calls that belong to humans. The platform facilitates them
  (assignments, notifications, checklists) but does not automate the judgment.

- Architectural decisions. The platform does not decide which database to use.
  It provides context (related ADRs, team patterns, prior decisions) and
  records the outcome.

---

## 5. The Integration Model

### 5.1 VCS Agnosticism

The platform must work with GitHub, GitLab, and Bitbucket. This is not about
supporting every edge case of every platform — it is about not hard-coding
GitHub assumptions into the architecture.

The integration surface for a VCS is:

1. **Webhook events.** Push, PR opened/updated/merged, tag created, CI status
   changed. Every major VCS platform provides these.
2. **CI check reporting.** The ability to post a check/status on a PR. GitHub
   has Check Runs, GitLab has Commit Statuses, Bitbucket has Build Statuses.
   The semantics are equivalent.
3. **PR/MR metadata.** Reading the description, labels, and comments of a
   PR/MR. All platforms provide APIs for this.

The platform implements a VCS adapter interface. The GitHub adapter is built
first (because it is the primary use case). GitLab and Bitbucket adapters follow
the same interface. Adding a new VCS means implementing the adapter, not
changing the platform core.

### 5.2 Project Management Agnosticism

Teams use different project management tools: GitHub Projects, Asana, Linear,
Jira, Notion. The platform integrates with these but does not replace them.

The integration model is **bidirectional sync at defined touch points**:

- When a requirement transitions to `in-progress` in the platform, the
  corresponding task in the PM tool is updated (if linked).
- When a task is marked done in the PM tool, the platform is notified (if a
  webhook is configured) and can trigger downstream checks.
- The platform does not attempt to replicate the PM tool's UI, workflow, or
  data model. It synchronizes status at transition boundaries.

This means engineers continue using their preferred PM tool. The platform is
not another tool to check — it is the system that keeps the tools in sync.

### 5.3 Authentication and Identity

The platform supports multiple auth providers out of the box:

- **GitHub OAuth.** Natural fit for developer-centric organizations. User
  identity maps to GitHub username. Repository access permissions can be
  inherited from GitHub org membership.
- **Google OAuth.** Common in enterprise environments. User identity maps to
  Google Workspace email.
- **Custom SSO/SAML.** For organizations with existing identity providers.
  The platform acts as a service provider in the SAML flow.

Roles within the platform are independent of VCS roles:

| Platform Role | Capabilities |
|---|---|
| Org Admin | Manage users, configure processes, manage integrations |
| Product Owner | Create/approve requirements, configure releases, view dashboards |
| Developer | Reference requirements, create ADRs, view dashboards |
| Auditor | Read-only access to all traceability data and audit logs |

Role assignment is per-organization. A user can be an admin in one org and a
developer in another.

### 5.4 Bidirectional Sync, Not Data Ownership

A critical architectural principle: **the platform does not own the data in
external tools**. It creates sync points.

- The platform does not own the code in GitHub repos. It reads webhook events
  and posts CI checks.
- The platform does not own the tasks in Asana or Linear. It syncs status at
  transition points.
- The platform does not own the CI/CD pipeline. It consumes CI output and
  provides CI checks.

The platform **does** own:

- Requirements and their hierarchy.
- Process configurations.
- Traceability data (computed from external events).
- Audit logs and compliance reports.
- User identity and role assignments within the platform.

This distinction matters because it defines the blast radius of a platform
outage. If the platform is down, repos continue to function. CI pipelines
continue to run (minus the platform's CI check). PM tools continue to work.
The platform is an enhancement layer, not a dependency for basic operations.

---

## 6. AI-Native Development Cycle

### 6.1 AI Agents as First-Class Participants

The platform is designed from the start to support AI agents as participants in
the development lifecycle — not as an afterthought or integration.

What this means concretely:

- **API-first design.** Every capability the platform offers through its UI is
  also available through its API. AI agents interact with the platform via API
  calls, not by scraping web pages or parsing HTML.

- **Structured context endpoints.** An AI agent working on a PR can query the
  platform: "What requirements does this repo implement? What is the current
  coverage? What ADRs are relevant to this area of the codebase?" The platform
  returns structured JSON, not markdown documents for the agent to parse.

- **Agent identity.** AI agents authenticate to the platform with their own
  credentials (API keys or service accounts). Actions taken by agents are
  attributed to the agent, not to the human who triggered the agent session.
  This creates a clear audit trail: "Claude Agent (triggered by @mateo) marked
  REQ-012 as implemented based on PR #47 merge."

- **Agent-specific views.** The dashboard shows agent activity alongside human
  activity. An org admin can see: how many PRs were created by agents, what
  percentage of commits were agent-authored, which requirements were addressed
  by agent work, and what the quality metrics look like for agent-produced code
  versus human-produced code.

### 6.2 Full Observability

When an AI agent works on a codebase managed by the platform, the platform
captures:

- **What the agent did.** Files created, modified, deleted. Commands run.
  Tests executed. PRs opened.
- **Why the agent did it.** The requirement or task that triggered the agent
  session. The process rules the agent was following. The skill/knowledge
  context that was loaded.
- **What it referenced.** Which platform APIs the agent called. Which
  requirements it looked up. Which ADRs it consulted.
- **What it changed.** Full diff of all modifications, linked to the
  triggering requirement and the applicable process rules.

This observability serves two purposes: **trust** (humans can verify that the
agent did reasonable things for reasonable reasons) and **improvement** (patterns
in agent behavior inform better process rules and skill definitions).

### 6.3 Autonomy Boundaries

Not everything should be automated. The platform defines explicit boundaries
between autonomous and human-in-the-loop actions:

| Action | Autonomy Level | Rationale |
|---|---|---|
| CI checks (lint, format, test) | Fully autonomous | Deterministic, low-risk, reversible |
| PR creation from requirement | Autonomous with notification | Structured task, reviewable output |
| Requirement status transition | Autonomous when evidence-based | Computed from CI output, not judgment |
| Code review | Human-in-the-loop | Judgment call requiring context |
| Architecture decisions | Human-required | Strategic, non-reversible |
| Release approval | Human-required | Business decision |
| Security-sensitive changes | Human-required | Risk threshold |

These boundaries are configurable per organization. A solo developer might allow
agents to auto-merge PRs that pass all checks. An enterprise team might require
human approval for every merge. The platform supports both.

### 6.4 Process Rules as API Context

Today, claude-kit plugins encode process rules as markdown files that are
injected into the agent's context window. This works because claude-kit's plugin
system is designed for exactly this use case. But it has limitations:

- The rules are static files. Changing a process rule means updating a plugin,
  releasing a new version, and updating every environment that uses it.
- The rules are repo-scoped. A plugin loaded in one repo does not know about
  process configurations for other repos in the same product.
- The rules cannot reference live data. A skill can say "always reference
  requirements" but it cannot provide the current requirement list because the
  skill is a static document.

In the platform model, AI agents get process rules from the **platform API**:

```
GET /api/v1/products/{product-id}/process-context
```

Returns:
```json
{
  "lifecycle_phase": "implementation",
  "active_requirements": ["REQ-012", "REQ-015"],
  "quality_gates": {
    "pr_must_reference_requirement": true,
    "tests_must_pass": true,
    "minimum_coverage": 80
  },
  "applicable_adrs": ["ADR-007", "ADR-009"],
  "team_conventions": {
    "commit_format": "conventional-commits",
    "branch_naming": "<type>/<description>"
  }
}
```

The agent receives live, product-specific process context — not a static
markdown file that might be outdated. The platform is the source of truth for
"how should work be done on this product right now."

This does not replace claude-kit plugins. Domain knowledge (Zephyr RTOS APIs,
Python best practices, SvelteKit patterns) still belongs in plugins. Process
governance context (which requirements exist, what quality gates apply, what
the team's conventions are) comes from the platform.

---

## 7. Self-Hosted Architecture

### 7.1 Kubernetes-Native Deployment

The platform is deployed on Kubernetes. This is a deliberate choice, not a
default. The reasons:

- **Scaling.** Individual services can be scaled independently. The webhook
  ingestion service might need many replicas during peak development hours;
  the process configurator might need one.
- **Isolation.** Multi-tenant data isolation is enforced at the infrastructure
  level (namespaces, network policies, separate databases) in addition to the
  application level.
- **Portability.** Kubernetes runs on any cloud provider and on bare metal.
  A self-hosted deployment is not locked to AWS, GCP, or Azure.
- **Operational maturity.** Kubernetes provides health checks, rolling
  deployments, secret management, and observability primitives out of the box.

The deployment model:

```
Ingress (auth proxy: OAuth2 Proxy or similar)
├── API Gateway
│   ├── Auth Service
│   ├── Organization Service
│   ├── Product Registry
│   ├── Requirements Engine
│   ├── Process Configurator
│   ├── Integration Service
│   ├── AI Agent Gateway
│   └── Notification Service
├── Dashboard UI (static SPA served via ingress)
├── Webhook Receiver (separate ingress path, no auth)
└── Background Workers
    ├── Traceability Computer
    ├── CI Check Poster
    ├── PM Sync Worker
    └── Notification Dispatcher
```

All services communicate via internal APIs (gRPC or HTTP). An event bus (NATS,
Redis Streams, or similar) handles asynchronous communication between webhook
ingestion and background workers.

### 7.2 Multi-Tenancy Model

Each organization is a tenant. Tenants are isolated at the data level:

- **Database isolation.** Each tenant gets its own database (or schema within a
  shared database, depending on scale). No query from tenant A can access
  tenant B's data, even if a bug bypasses application-level checks.
- **API isolation.** All API calls include the organization context (derived
  from the authenticated user's org membership). Cross-org operations are not
  possible through the API.
- **Integration isolation.** Webhook endpoints, API keys, and integration
  credentials are scoped to a single organization.

The platform admin (the person running the Kubernetes cluster) can see all
tenants for operational purposes but does not have access to tenant data
through the application layer.

### 7.3 The Platform as Its Own Product

The platform website is not just a dashboard — it is a product:

- **Documentation.** How to use the platform, how to configure processes, how
  to set up integrations. Searchable, versioned, with examples.
- **Process catalog.** Browse available process templates. Organizations can
  start from a template (based on PAL's current process definitions) and
  customize.
- **Requirement trees.** Visual hierarchy of requirements for each product.
  Drill down from strategic vision to implementation tasks. See coverage,
  status, and ownership at every level.
- **Dashboards.** Product health, requirement coverage, release readiness,
  team velocity, agent activity. All computed from real data, not self-reported
  status updates.
- **Admin console.** User management, role assignment, integration configuration,
  process customization.

---

## 8. Component Architecture

This section describes each discrete service that composes the platform. These
are logical components — some may be deployed as a single service early on and
split later as complexity warrants.

### 8.1 Auth Service

**Responsibility:** User authentication, session management, API key issuance.

- OAuth2 flows for GitHub, Google, and custom SAML providers.
- JWT-based sessions with configurable expiry.
- API keys for programmatic access (AI agents, CI integrations).
- Rate limiting per API key and per user session.

**Data owned:** User credentials (hashed), OAuth tokens (encrypted), sessions,
API keys.

**Open questions:** Whether to build custom or use an existing solution like
Keycloak, Ory Kratos, or Authentik. See Section 12.

### 8.2 Organization and User Management

**Responsibility:** Organization CRUD, user membership, role assignment,
invitations.

- Create organizations. Invite users by email or VCS username.
- Assign roles per organization (admin, product owner, developer, auditor).
- Organization settings: default process profile, integration configuration,
  notification preferences.

**Data owned:** Organizations, memberships, roles, invitations, org-level
settings.

### 8.3 Product Registry

**Responsibility:** Track what products exist, what repos compose them, and
what their current state is.

- Register a product with a name, description, and owner.
- Link one or more repositories to a product.
- Configure which process profile applies to this product.
- Track product lifecycle phase (concept, development, production, sunset).

**Data owned:** Products, product-repo links, process profile assignments,
lifecycle states.

### 8.4 Requirements Engine

**Responsibility:** Manage requirements hierarchically, enforce lifecycle
state machines, compute coverage.

This is the most complex component and the core value proposition of the
platform.

- **Hierarchical requirements.** Vision -> goals -> features -> implementation
  requirements. The hierarchy is explicit and navigable. Each level has
  appropriate detail: vision is a sentence, an implementation requirement is
  a structured document with acceptance criteria.

- **Lifecycle state machine.** Each requirement moves through states:
  `draft` -> `review` -> `approved` -> `in-progress` -> `implemented` ->
  `verified` -> `released`. Transitions have preconditions: `approved` requires
  an approver; `verified` requires passing test evidence; `released` requires
  inclusion in a tagged release.

- **Coverage computation.** For each requirement, the engine knows: which PRs
  reference it, which commits touch it, which test suites cover it, whether
  those suites pass. Coverage is a computed metric, not a self-reported field.

- **Release planning.** Requirements are assigned to milestones/releases. The
  engine computes release readiness: which requirements are verified, which
  are still in progress, what is the coverage percentage.

**Data owned:** Requirements (all fields), state transitions, coverage data,
release assignments.

### 8.5 Process Configurator

**Responsibility:** Replace PAL's 37 markdown files with configurable process
profiles.

- Define lifecycle phases and the quality gates between them.
- Configure which artifacts are required at each phase (e.g., "architecture
  phase requires at least one ADR").
- Define PR templates with required fields per product.
- Set approval requirements: who must approve what, how many approvals are
  needed, which roles can approve.
- Configure notification rules: who gets notified on which events.

The configurator ships with a default profile based on PAL's current process
definitions. Organizations can use it as-is or customize.

**Data owned:** Process profiles, gate definitions, template configurations,
approval rules.

### 8.6 Integration Layer

**Responsibility:** Connect the platform to external tools (VCS, PM tools,
CI systems).

- **VCS adapters.** GitHub (first), GitLab, Bitbucket. Webhook registration,
  event parsing, CI check posting, PR/MR metadata reading.
- **PM adapters.** Asana, GitHub Projects, Linear, Jira. Task status sync,
  requirement-to-task linking.
- **CI adapters.** GitHub Actions, GitLab CI, Jenkins. Test result ingestion,
  pipeline status monitoring.

Each adapter implements a common interface. Adding a new integration means
implementing the interface, not changing the platform core.

**Data owned:** Integration credentials (encrypted), webhook subscriptions,
sync state (last-synced timestamps, entity mappings).

### 8.7 CI/CD Hooks

**Responsibility:** Enforce process rules in repository CI pipelines.

The platform provides two types of CI hooks:

1. **CI checks.** Posted as GitHub Check Runs (or equivalent on other
   platforms). These validate:
   - PR description has a `Requirement:` field referencing a valid requirement.
   - Referenced requirement is in the correct status (approved or in-progress).
   - Required approvals have been obtained per the process profile.
   - Commit messages follow the configured convention.

2. **Reusable actions/steps.** GitHub Actions, GitLab CI templates, or generic
   scripts that repos can include in their pipelines:
   - Report test results to the platform.
   - Post deployment status.
   - Trigger release readiness checks.

CI hooks are the primary enforcement mechanism. They turn process rules into
pipeline gates.

**Data owned:** Check run history, validation results, enforcement audit logs.

### 8.8 Dashboard and UI

**Responsibility:** Provide visual interfaces for all platform capabilities.

- **Product dashboard.** Requirement coverage, release readiness, recent
  activity, open issues. A product owner opens this daily.
- **Requirement tree.** Visual hierarchy of requirements. Click to drill down.
  Color-coded by status. Filterable by release milestone.
- **Traceability view.** For any requirement, show the full chain: vision ->
  goal -> feature -> requirement -> PRs -> commits -> tests -> release.
- **Team activity.** Who is working on what. Agent activity alongside human
  activity. Velocity metrics over time.
- **Process configuration UI.** Drag-and-drop lifecycle phase configuration.
  Quality gate editors. Template designers.
- **Admin console.** User management, integration setup, audit logs.

The UI is a single-page application served by the platform's ingress. It
communicates with the platform API — it has no direct database access.

### 8.9 AI Agent Gateway

**Responsibility:** Provide process context and platform capabilities to AI
agents through a dedicated API surface.

- **Process context endpoint.** Returns the applicable process rules, active
  requirements, quality gates, and team conventions for a given product/repo.
  This replaces static markdown process files in agent context.
- **Requirement query endpoint.** Agents can search requirements by keyword,
  status, or hierarchy level. Used when an agent needs to link its work to the
  correct requirement.
- **Evidence submission endpoint.** Agents can submit structured evidence
  (test results, analysis reports) that the platform links to requirements.
- **Action endpoint.** Agents can transition requirement status, post comments,
  and trigger notifications — with appropriate permission checks.

The gateway enforces the same permission model as the UI. An agent operating
with a developer's API key can do what a developer can do. An agent with a
product owner's key can do more.

### 8.10 Notification System

**Responsibility:** Deliver alerts, reviews, and approvals to the right people
at the right time.

- **Event-driven.** Notifications are triggered by platform events: requirement
  status change, CI check failure, release readiness threshold crossed, review
  requested.
- **Channel-agnostic.** Email, Slack, Discord, in-platform notifications. Each
  user configures their preferred channels.
- **Role-based.** A product owner gets requirement coverage alerts. A developer
  gets review requests. An auditor gets compliance threshold notifications.
- **Configurable per organization.** Which events trigger notifications, who
  receives them, what channels are used — all configurable in the process
  profile.

**Data owned:** Notification templates, delivery state, user preferences,
channel configurations.

---

## 9. Licensing and Business Model

The platform serves a dual purpose:

1. **Personal infrastructure.** The author uses it to manage their own products
   (claude-kit and future products). This is the primary use case and the
   driver for building it. Every design decision is made by asking "does this
   help me build better products faster?"

2. **Licensed product.** The platform can be licensed to other companies —
   starting with the author's employer. This creates a revenue stream and
   validates the platform against real enterprise needs.

The licensing model:

| Tier | What | For whom |
|---|---|---|
| Self-hosted open core | Core platform with basic process profiles | Individual developers, small teams |
| Enterprise license | Advanced process configurator, SSO/SAML, audit logging, SLA support | Companies |
| Managed hosting | The platform hosted and operated by the author | Teams that do not want to run Kubernetes |

The open core is genuinely useful on its own. The enterprise features address
compliance, audit, and integration needs that small teams do not have. Managed
hosting is a convenience tier.

**Dogfooding is mandatory.** The platform itself is a product managed by the
platform. Before any feature is offered to licensees, it must be used
internally. The author's own products are the first and most demanding
customers.

---

## 10. Incremental Build Strategy

### 10.1 What Not to Build First

The vision described in this document is a multi-year effort. Attempting to
build the full platform before shipping products would be a classic mistake:
over-investing in infrastructure at the expense of the products that justify
the infrastructure.

**Do not build first:**

- Full VCS agnosticism. GitHub is the only VCS that matters initially. GitLab
  and Bitbucket adapters are a post-1.0 concern.
- Full PM integration. Start with no PM integration — requirements live in the
  platform only. PM sync is a convenience feature, not a core requirement.
- Managed hosting. Self-hosted Kubernetes is the deployment model. Managed
  hosting requires operational investment (monitoring, SLA, support) that is
  premature.
- The complete dashboard. Start with a minimal dashboard: product list,
  requirement tree, coverage summary. Advanced views can be added iteratively.
- AI agent gateway. The gateway is powerful but not necessary for v1.
  Agents can use the same API as the dashboard.

### 10.2 The Standing-Start MVP

The minimum viable platform consists of three components:

1. **Auth service.** GitHub OAuth login. User sessions. Org creation. Basic
   RBAC (admin, developer).

2. **Requirements engine.** Create requirements with hierarchy. Lifecycle
   state machine. Basic coverage computation from PR metadata.

3. **GitHub integration.** Webhook receiver for PR events. CI check that
   validates `Requirement:` field. Commit message parsing for requirement
   references.

With these three components:

- A developer can create an organization and register a product.
- They can define requirements in the platform.
- They can reference requirements from PRs and commits.
- The platform validates references and computes basic coverage.
- A minimal dashboard shows the product's requirement tree and coverage.

This is already more valuable than PAL's 37 markdown files. It provides living
traceability instead of manual cross-references. It enforces process at the
point of work (PRs) instead of through structural validation of documents.

**The current docs/ layer in repos like claude-kit is a fine stand-in until
this MVP exists.** There is no urgency to rip out the existing system. The
process framework — the concepts PAL encodes — remains valid regardless of
delivery mechanism. When the platform MVP is ready, migration is incremental:
move requirements to the platform, add the CI check to repos, remove the docs/
requirement files. Each step is independent.

### 10.3 Layered Expansion

After the MVP, additional capabilities are added in priority order:

| Phase | Components | Value Added |
|---|---|---|
| **MVP** | Auth, Requirements, GitHub integration | Living traceability, PR enforcement |
| **Phase 2** | Process configurator, Notification system | Customizable processes, proactive alerts |
| **Phase 3** | Dashboard expansion, Test evidence ingestion | Comprehensive visibility, automated verification |
| **Phase 4** | AI agent gateway, PM integration (Asana) | Agent-native workflow, PM sync |
| **Phase 5** | GitLab adapter, additional PM integrations | Multi-VCS, multi-PM support |
| **Phase 6** | Enterprise features (SSO/SAML, audit logs) | Licensing readiness |
| **Phase 7** | Managed hosting infrastructure | Operational offering |

Each phase delivers standalone value. No phase depends on a future phase to
be useful. The MVP is usable on day one.

---

## 11. Product-Platform Relationship

### 11.1 claude-kit as the First Managed Product

claude-kit is the first product managed by the platform. This means:

- claude-kit's requirements move from `docs/requirements/` to the platform.
- claude-kit's PRs include `Requirement:` fields validated by the platform.
- claude-kit's test results are ingested by the platform and linked to specs.
- claude-kit's release readiness is computed by the platform, not by manually
  checking CHANGELOG.md.

claude-kit is also a tool that AI agents use. The platform provides process
context to agents working on claude-kit. The agents use claude-kit's plugins
for domain knowledge and the platform's API for process governance. These are
complementary, not competing.

### 11.2 The Platform Managing Itself

Once the platform reaches sufficient maturity, it manages its own development:

- Platform requirements live in the platform.
- Platform PRs are validated by the platform's CI checks.
- Platform release readiness is computed by the platform itself.

This is recursive dogfooding. It creates a virtuous cycle: every improvement
to the platform immediately benefits the platform's own development process.
It also creates a constraint: the platform cannot ship features that do not
work well enough to use on itself.

### 11.3 From Submodule to Webhook

The migration path from the current model to the platform model:

| Current state | Migration step | End state |
|---|---|---|
| PAL is a git submodule in repos | Remove submodule dependency | Repos have no PAL dependency |
| Requirements live in `docs/requirements/` | Create requirements in the platform, archive the files | Requirements are platform objects |
| Process rules are markdown files | Configure equivalent rules in the process configurator | Processes are platform configuration |
| Validation is bash scripts | Platform CI checks replace structural validation | Enforcement is infrastructure |
| Traceability is `## Traces` sections | Computed from PR metadata and commit messages | Traceability is automated |
| Test evidence is markdown files | CI output is ingested by the platform | Evidence is real data |
| ADRs are in `docs/architecture/decisions/` | ADRs stay in repos, platform indexes them | ADRs are local + indexed |

Each row is an independent migration step. They can be done in any order,
though the natural sequence is: requirements first (the most impactful change),
then process rules, then traceability, then test evidence.

---

## 12. Open Questions and Design Decisions

These are unresolved design decisions that need answers before or during
implementation. They are captured here to prevent premature closure and to
document the decision space.

### 12.1 Build vs. Buy: Auth

**Question:** Build a custom auth service or use an existing solution (Keycloak,
Ory Kratos, Authentik, Zitadel)?

**Arguments for building:**
- Full control over the UX, token format, and session management.
- No dependency on a project that might change direction.
- The auth surface is relatively small (OAuth2 with two providers + API keys).

**Arguments for buying:**
- Auth is a solved problem. Building it is time spent not building unique value.
- Security-sensitive code benefits from being well-tested by a large community.
- Features like password reset, MFA, session management are complex to implement
  correctly.

**Leaning:** Use Ory Kratos or Authentik. The platform's unique value is
requirements and process governance, not auth flows.

### 12.2 Database Architecture

**Question:** One database per tenant, one schema per tenant, or shared tables
with tenant_id columns?

**Arguments for database-per-tenant:**
- Strongest isolation. A query cannot accidentally cross tenants.
- Easy to back up, restore, or delete a single tenant's data.
- Performance issues in one tenant do not affect others.

**Arguments for shared tables:**
- Operationally simpler. One database to manage, back up, monitor.
- Schema migrations apply once, not N times.
- Better resource utilization at small scale.

**Leaning:** Start with shared tables (tenant_id) for the MVP. Migrate to
schema-per-tenant when multi-tenant usage grows beyond a handful of
organizations. Database-per-tenant is overkill until the enterprise tier.

### 12.3 Technology Stack

**Question:** What languages and frameworks for each component?

**Considerations:**
- The platform should use a statically typed language for core services (type
  safety in a multi-service system reduces a class of integration bugs).
- The dashboard is a web application — standard frontend stack.
- Background workers need reliable async processing.

**Options being considered:**
- Go for backend services (strong Kubernetes ecosystem, good performance,
  simple deployment — single binary per service).
- TypeScript/React or SvelteKit for the dashboard.
- PostgreSQL for the database (mature, reliable, strong JSON support for
  flexible schemas).
- NATS or Redis Streams for the event bus.

**Leaning:** Go + PostgreSQL + SvelteKit. Go for the same reasons the broader
cloud-native ecosystem chose it. SvelteKit because it aligns with existing
frontend team knowledge. PostgreSQL because it is the default right answer for
relational data.

### 12.4 Requirement Schema Design

**Question:** How structured should requirements be? Free-form text with
metadata, or a rigid schema with defined fields?

**Arguments for rigid schema:**
- Forces completeness. A requirement without acceptance criteria is not a
  requirement.
- Enables computation. Coverage, readiness, and priority can be computed from
  structured fields.
- Machine-readable for AI agents.

**Arguments for flexible schema:**
- Different products have different requirement styles.
- Overly rigid schemas become bureaucratic — people game the fields.
- Early-stage requirements are inherently vague and resist structure.

**Leaning:** Tiered structure. Vision and goal levels are lightly structured
(title + description + priority). Feature and implementation levels are rigidly
structured (title, description, acceptance criteria, priority, effort estimate,
dependencies). The tier enforces appropriate rigor at each level of the
hierarchy.

### 12.5 Event Bus vs. Direct Calls

**Question:** Should services communicate via direct API calls or an event bus?

**Arguments for event bus:**
- Loose coupling. The webhook receiver does not need to know which services
  care about PR events.
- Retry semantics. Failed processing can be retried without the sender knowing.
- Audit trail. All events are logged in the bus.

**Arguments for direct calls:**
- Simpler to debug. Request-response is easier to trace than event chains.
- Fewer moving parts in the MVP.
- Latency is more predictable.

**Leaning:** Direct calls for synchronous operations (API requests, CI check
posting). Event bus for asynchronous operations (webhook processing, traceability
computation, notification dispatch). The MVP can start with direct calls
everywhere and introduce the event bus when async processing becomes a
bottleneck.

### 12.6 Offline / Disconnected Mode

**Question:** What happens when a developer is working without connectivity to
the platform?

**Arguments for supporting offline mode:**
- Developers should not be blocked by platform availability.
- CI checks can fail gracefully (skip rather than block) when the platform is
  unreachable.

**Arguments against investing in offline mode early:**
- The platform is self-hosted within the same network as the dev environment.
- Offline support adds significant complexity (caching, conflict resolution,
  sync queues).
- The blast radius of platform downtime is limited (see Section 5.4).

**Leaning:** No offline mode in MVP. CI checks fail open (post a warning
instead of blocking) when the platform is unreachable. Full offline support
is a Phase 6+ concern.

### 12.7 Migration Tooling

**Question:** Should the platform provide automated migration tools for
existing docs/-based repos?

**Considerations:**
- claude-kit has existing requirements, ADRs, and specs in docs/.
- Other repos that adopted PAL's structure would also need migration.
- A migration tool could parse existing markdown artifacts and create
  corresponding platform objects.

**Leaning:** Yes, but as a CLI tool, not a platform feature. A one-time
migration script that reads docs/requirements/*.md and creates requirements
in the platform via API. This is a dev tool, not a product feature.

### 12.8 Versioning of Process Configurations

**Question:** Should process configurations be versioned? If so, how?

**Considerations:**
- A process change mid-release could invalidate prior work.
- Auditors need to know which process rules were in effect when a decision
  was made.
- Frequent process changes create instability.

**Leaning:** Yes, versioned. Each process profile has a version number.
Products pin to a process version. Upgrading to a new process version is an
explicit action. The platform retains all historical versions for audit.

### 12.9 Granularity of CI Checks

**Question:** One CI check that validates everything, or multiple checks for
different aspects?

**Arguments for one check:**
- Simpler CI configuration in repos.
- One green check means "everything is OK."

**Arguments for multiple checks:**
- Granular feedback. "Requirement reference is valid" vs. "Commit message
  format is wrong" are different problems with different fixes.
- Independent checks can be made required or optional independently.
- Faster feedback — a check can report as soon as its specific validation
  completes.

**Leaning:** Multiple checks, grouped by concern. Three initial checks:
1. `platform/requirement` — validates requirement reference.
2. `platform/convention` — validates commit messages and PR format.
3. `platform/approval` — validates that required approvals are present.

### 12.10 Data Retention and Archival

**Question:** How long does the platform retain traceability data, and what
happens to data for deleted products or orgs?

**Considerations:**
- Compliance may require long retention periods.
- Storage costs grow with history.
- GDPR and data sovereignty apply when managing data for other organizations.

**Leaning:** Configurable per organization. Default: retain all data for
active products, archive (cold storage) for sunset products, delete on explicit
org deletion with a 30-day grace period. Enterprise tier adds configurable
retention policies and data export.

---

## 13. Sources and Prior Art

This vision draws on several existing systems and ideas:

- **Jama Connect, Doors (IBM), Polarion.** Enterprise requirements management
  tools. They prove the market for structured requirements management exists.
  Their weakness is complexity and cost — they are designed for regulated
  industries (aerospace, automotive, medical) and carry that overhead into every
  use case.

- **Linear, Height, Shortcut.** Modern project management tools that prove
  developer experience matters. Their weakness is that they manage tasks, not
  requirements. The gap between "a task is done" and "a requirement is
  satisfied" is the gap the platform fills.

- **GitHub Actions, GitLab CI.** Prove that CI is the right enforcement layer.
  If a check is red, developers fix it. If a process document says "you should
  do X" — they might not.

- **Backstage (Spotify).** An internal developer portal that provides a product
  catalog, documentation, and CI/CD visibility. Backstage validates the "portal
  as product" model. Its weakness is that it does not enforce processes — it
  surfaces information.

- **claude-kit itself.** Proves that encoding process knowledge as structured
  context for AI agents creates measurably better outcomes. The platform
  generalizes this from "plugin files loaded into Claude" to "API endpoints
  consumed by any AI agent."

- **PAL (current).** Proves that the concepts are right: lifecycle phases,
  quality gates, traceability, process governance. The implementation model
  (markdown files, bash validation, git submodules) is what needs to evolve.

---

*This document is a vision paper, not a specification. It captures the direction
and design space. Concrete specifications will be created as requirements in the
platform itself — once the platform exists to hold them. Until then, this paper
serves as the north star for incremental decisions about what to build and in
what order.*
