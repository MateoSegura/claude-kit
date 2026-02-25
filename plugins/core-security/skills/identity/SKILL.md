---
name: core-security:identity
description: "Domain overview for general-purpose secure software development knowledge base"
user-invocable: false
---

# Secure Software Development — Domain Knowledge

This plugin provides shared domain reference material for secure software development practices applicable to any technology stack. It is a **knowledge companion** — loaded alongside role-specific plugins to provide consistent security expertise.

## Domain Scope

- **Secure coding**: OWASP Top 10 awareness, input validation, output encoding, injection prevention, authentication and authorization patterns
- **Secrets management**: Environment variables, vault systems, credential rotation, CI/CD secrets handling, .gitignore hygiene
- **Dependency scanning**: Supply chain security, SCA tooling concepts, SBOM basics, vulnerability severity assessment, update strategies
- **Threat modeling**: STRIDE methodology, attack surface analysis, trust boundaries, data flow diagrams, risk assessment, secure boot chain of trust

## What This Plugin Contains

This plugin contains **skills only** — no agents, no commands. Skills are loaded by companion role plugins that reference them in agent frontmatter. Each skill directory contains:

- `SKILL.md` — Entry point with overview and quick-reference (auto-loaded)
- Reference files — Detailed checklists, pattern catalogs, examples (loaded on demand via Read)

## What This Plugin Does NOT Contain

- No agents (role plugins provide those)
- No commands (role plugins provide those)
- No role-specific identity or persona
- No framework-specific or language-specific guidance (see domain-specific knowledge plugins for that)
