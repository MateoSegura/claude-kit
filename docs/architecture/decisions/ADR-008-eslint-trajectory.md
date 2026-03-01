# ADR-008: The ESLint Trajectory — Ecosystem as Competitive Moat

**Status:** accepted
**Date:** 2026-02-28
**Governing Process:** PROC-LC-003 (Architecture Design)

## Context

The developer-tools-landscape research analyzes historical plugin ecosystem
success cases to identify patterns that create sustainable competitive
advantage. ESLint's trajectory is the most instructive analogy for claude-kit:

**ESLint's evolution:**
1. **Standalone tool** — A JavaScript linter with built-in rules
2. **Configurable rules** — Users could enable/disable individual rules
3. **Shareable configs** — `extends: ["eslint:recommended"]` allowed
   configs to build on other configs
4. **Plugin system** — Third parties created rule packages (`eslint-plugin-react`)
5. **Community registry** — npm became the de facto plugin registry
6. **Organizational configs** — Companies published scoped packages
   (`@company/eslint-config`) that codified team standards
7. **De facto standard** — ESLint won not by being the best linter but by
   having the richest ecosystem

The key insight: ESLint's technical quality was necessary but insufficient.
Its moat was the ecosystem — the thousands of community plugins, shareable
configs, and organizational standards that created switching costs exceeding
any technical advantage a competitor could offer.

The developer-tools-landscape research identifies four properties that make
plugin ecosystems sticky: composability (plugins build on plugins),
contribution accessibility (low barrier to creating plugins), organizational
governance (enterprise config management), and network effects (each new
plugin increases platform value for all users).

## Decision

claude-kit's long-term competitive strategy follows the ESLint trajectory:

**Phase 1 — Standalone value (current):**
The system provides value as a standalone CLI with proprietary plugins.
The value proposition is domain-specific AI agent quality improvement.

**Phase 2 — Composable configurations:**
Plugins can declare dependencies on other plugins (`companions` in
`ctl.json`). Domain-specific plugins build on universal core plugins.
Organizations can layer company-specific skills on top of community
domain knowledge.

**Phase 3 — Community registry:**
A public registry allows third parties to discover, install, and publish
plugins. Quality gating ensures published plugins meet structural and
semantic standards (validated by the same tooling used internally).

**Phase 4 — Organizational governance:**
Enterprise features allow organizations to define approved plugin sets,
enforce versions, and manage configurations across teams. A `team.json`
configuration specifies which plugins, hooks, and constraints apply to
each team within an organization.

**Phase 5 — Network effects:**
Each community plugin increases the platform's value for all users. Each
organizational deployment increases the switching cost. The ecosystem
becomes the moat.

## Consequences

### Positive

- Clear strategic roadmap — each phase builds on the previous and is
  independently valuable
- The plugin architecture already supports composability via companions
- Quality gating infrastructure already exists (validate-plugins.py,
  system-maker:validate, system-updater:review-all)
- The five-role team structure provides a consistent template for community
  plugin creation

### Negative

- Ecosystem building is slow — community adoption requires critical mass
  before network effects activate
- Registry infrastructure requires significant investment (hosting, auth,
  quality automation, abuse prevention)
- Organizational governance features require enterprise sales and support
  capabilities
- Community plugins may not meet quality standards, creating a curation
  burden
- The strategy requires the product to be successful enough in Phase 1 to
  fund Phases 2-5

### Neutral

- No neutral consequences identified.

## Alternatives Considered

See Context section above for the alternatives evaluated during this decision.

## Traces

- **Upstream:** REQ-009 (Cloud Platform), REQ-010 (Plugin Ecosystem)
- **Downstream:** (future SPEC documents implementing registry, governance, and
  community contribution infrastructure)
- **Quality Attributes:** extensibility, ecosystem growth, competitive defensibility
