# REQ-010: Plugin Ecosystem

**Status:** active
**Priority:** should-have
**Created:** 2026-02-28
**Governing Process:** PROC-LC-002 (Requirements Engineering)

## Context

The developer-tools-landscape research analyzes plugin ecosystem success cases
(ESLint, VS Code, Terraform, Webpack) and identifies the properties that make
ecosystems sticky: composable configurations, community contribution paths,
organizational governance, and network effects where each new plugin increases
the value of the platform for all users.

ESLint's trajectory is particularly instructive. It began as a standalone
linter, grew through shareable configs (extending other configs), built a
community registry (npm), added organizational governance (scoped packages,
company-specific configs), and became the de facto standard not because it was
the best linter but because it had the richest ecosystem. The tool's moat was
its community, not its technology.

claude-kit's plugin architecture already supports the primitives: discrete
plugin units, composable loading via companions, role-based specialization,
and domain scoping. What it lacks is the ecosystem infrastructure: a registry
for discovery, a contribution model for community plugins, an extension
mechanism for building on existing plugins, and governance tooling for
organizations.

## Requirement

The system shall support an extensible plugin ecosystem where:

1. **Composability** — Plugins can declare dependencies on other plugins and
   inherit or extend their knowledge, hooks, and behavioral constraints.
2. **Community contribution** — Third parties can create, publish, and share
   plugins through a public registry with quality gating.
3. **Organizational governance** — Organizations can define approved plugin
   sets, enforce plugin versions, and layer org-specific configurations on
   top of community plugins.
4. **Discovery** — A registry or index allows users to find plugins by domain,
   role, and quality rating.
5. **Extension** — Plugins can extend other plugins (analogous to ESLint's
   `extends` pattern) so that domain-specific configurations build on
   domain-general foundations.

## Acceptance Criteria

- [ ] Plugins can declare dependencies on other plugins in their metadata
- [ ] An `extends` or inheritance mechanism allows plugins to build on others
- [ ] A public registry exists for plugin discovery and installation
- [ ] Registry plugins undergo automated quality validation before listing
- [ ] Organizations can define and enforce approved plugin configurations
- [ ] The `claude-kit update` command can install community plugins from the
      registry
- [ ] Plugin authors can publish updates that propagate to installed users

## Traces

- **Upstream:** developer-tools-landscape.md (ESLint ecosystem analysis, plugin
  stickiness factors, community contribution patterns)
- **Downstream:** ADR-008 (ESLint trajectory — composable configs, registry, governance)
- **Quality Attributes:** None identified
