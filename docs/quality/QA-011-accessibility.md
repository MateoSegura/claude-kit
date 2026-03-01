# QA-011 — Accessibility

**Status:** draft
**Priority:** should
**Category:** compliance

## Context

Section 508 of the Rehabilitation Act requires any software procured by or used
within a federal agency to be accessible to individuals with disabilities. This
applies to claude-kit if it is procured by federal agencies or used by defense
contractors within federal environments.

Federal procurement officers check for a Voluntary Product Accessibility
Template (VPAT) — a standardized document describing how a product meets
accessibility requirements. Not having a VPAT can delay or block federal
procurement.

Since claude-kit is primarily a CLI tool, the accessibility surface is narrower
than a web application. However, the constraint still applies to CLI output,
documentation, and any web-based components (dashboards, configuration UIs).

## Constraint

### Section 508 Requirements

Section 508 incorporates WCAG 2.0 Level AA success criteria. Key requirements
for a CLI tool:

| Requirement | Application to claude-kit |
|------------|--------------------------|
| **Text alternatives for non-text content** | CLI output must not rely solely on color to convey information |
| **Keyboard navigation** | CLI is inherently keyboard-navigable (satisfied by default) |
| **Color independence** | Use text labels and symbols alongside color coding in output |
| **Screen reader compatibility** | Output must be parseable by screen readers; avoid raw ANSI escape sequences that break assistive technology |
| **Accessible documentation** | All documentation (README, help text, web docs) must be accessible |
| **Error identification** | Error messages must be descriptive and programmatically determinable |

### WCAG 2.0 AA for Web Components

If claude-kit adds web-based dashboards or configuration UIs (REQ-009):

1. All images must have alt text
2. Color contrast ratio must meet 4.5:1 for normal text
3. All functionality must be operable via keyboard
4. Pages must have proper heading hierarchy and landmarks
5. Forms must have associated labels
6. Dynamic content updates must be announced to assistive technology

### VPAT Requirements

A VPAT (Voluntary Product Accessibility Template) must document:

1. Compliance level for each applicable criterion (Supports, Partially Supports,
   Does Not Support, Not Applicable)
2. Remarks and explanations for each criterion
3. Product version and evaluation date
4. Testing methodology

## Architectural Impact

| Constraint | Impact |
|------------|--------|
| Color independence | All `[kit:]` and `[dev:]` debug traces must include text labels, not just colored output |
| Screen reader compatibility | Evaluate ANSI escape sequence usage; provide a `--no-color` or `--accessible` flag if needed |
| Web accessibility | Future dashboards (REQ-009) must be built accessibility-first, not retrofitted |
| Documentation | All markdown documentation must follow accessible formatting (proper headings, alt text, link text) |

## Phased Approach

### Phase 1: CLI Accessibility Audit (months 1–2)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Audit CLI output for color-only information (use text labels alongside color) | Month 1 | 16 hours |
| Verify screen reader compatibility with CLI output | Month 1 | 8 hours |
| Implement `--accessible` flag if ANSI sequences break assistive technology | Month 1–2 | 8–16 hours |
| Review all error messages for clarity and descriptiveness | Month 2 | 8 hours |

### Phase 2: VPAT Creation (month 2–3)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Complete VPAT for CLI tool | Month 2 | 16–24 hours |
| Have VPAT reviewed by accessibility consultant | Month 3 | $2K–$5K |

### Phase 3: Web Component Accessibility (when REQ-009 is implemented)

| Step | Timeline | Cost Estimate |
|------|----------|---------------|
| Build web dashboards with accessibility-first approach | With REQ-009 | Part of development |
| Automated accessibility testing in CI (axe-core, Lighthouse) | With REQ-009 | $0–$2K/year |
| Update VPAT to include web components | With REQ-009 | 8 hours |
| Manual accessibility testing with assistive technology | With REQ-009 | $3K–$8K per round |

**Estimated total (CLI only): $2K–$5K + 48–72 hours internal.**

## Artifacts Required

| Artifact | Audience | Frequency |
|----------|----------|-----------|
| VPAT (Voluntary Product Accessibility Template) | Federal procurement officers | Per major version |
| Accessibility conformance report | Auditors | Per major version |
| Accessibility testing results | Internal QA | Per release |
