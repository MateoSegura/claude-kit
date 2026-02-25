---
name: core-git:identity
description: "Domain overview for universal git knowledge base"
user-invocable: false
---

# Git Mastery -- Universal Knowledge

This plugin provides shared git reference material applicable to ANY software project regardless of language, framework, or domain. It is a **knowledge companion** -- loaded alongside every team to provide consistent git expertise.

## Domain Scope

- **Branching strategies**: Trunk-based development, GitHub Flow, GitFlow, release branching, environment branching
- **Commit conventions**: Conventional Commits, semantic messages, atomic commits, squash vs merge vs rebase
- **Advanced operations**: Interactive rebase, cherry-pick, bisect, reflog recovery, stash management, worktrees, submodules vs subtrees
- **Monorepo patterns**: Sparse checkout, path-based ownership, affected-only CI, dependency graph strategies

## What This Plugin Contains

This plugin contains **skills only** -- no agents, no commands. Skills are loaded by companion role plugins that reference them in agent frontmatter. Each skill directory contains:

- `SKILL.md` -- Entry point with overview and quick-reference (auto-loaded)
- Reference files -- Detailed patterns, examples, and decision frameworks (loaded on demand via Read)

## What This Plugin Does NOT Contain

- No agents (role plugins provide those)
- No commands (role plugins provide those)
- No role-specific identity or persona
- No language-specific or framework-specific git workflows
