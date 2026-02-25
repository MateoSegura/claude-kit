---
name: core-testing:identity
description: "Domain overview for general-purpose testing knowledge base"
user-invocable: false
---

# General-Purpose Testing — Domain Knowledge

This plugin provides shared domain reference material for software testing concepts that apply across all languages, frameworks, and platforms. It is a **knowledge companion** — loaded alongside role-specific plugins (engineer, grader, tester) to provide consistent testing expertise.

## Domain Scope

- **Test philosophy**: Test pyramid, testing trophy, cost-benefit analysis, what to test and what not to test, property-based testing concepts
- **Test doubles**: Mocks, stubs, fakes, spies — when to use each, over-mocking dangers, dependency injection for testability, isolation strategies
- **Coverage strategy**: Line vs branch vs path coverage, mutation testing, coverage as a tool not a target, risk-based coverage allocation
- **TDD/BDD**: Red-green-refactor, outside-in vs inside-out TDD, Given-When-Then, acceptance test driven development

## What This Plugin Contains

This plugin contains **skills only** — no agents, no commands. Skills are loaded by companion role plugins that reference them in agent frontmatter. Each skill directory contains:

- `SKILL.md` — Entry point with overview and quick-reference (auto-loaded)
- Reference files — Detailed patterns, examples, and decision guides (loaded on demand via Read)

## What This Plugin Does NOT Contain

- No agents (role plugins provide those)
- No commands (role plugins provide those)
- No role-specific identity or persona
- No framework-specific or language-specific testing patterns
