# Tier 2 Plan Templates

Reference templates for `environment.md` and `test-plan.md` — generated as
part of Tier 2 phased specifications.

---

## Environment Setup Document

For Tier 2 plans, generate `environment.md` in the plan directory.
This document ensures a fresh session (or autonomous agent) can set up
the development environment without human intervention.

### Template

```markdown
# Environment Setup

## Required Software

| Tool | Version | Install Command | Verify Command |
|------|---------|----------------|----------------|
| Node.js | >=18 | `nvm install 18` | `node --version` |
| ... | ... | ... | ... |

## API Keys & Secrets

| Variable | Source | Required For |
|----------|--------|-------------|
| `API_KEY` | `.env` file | Phase 2+ API calls |
| ... | ... | ... |

## Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `NODE_ENV` | `development` | Local development |
| ... | ... | ... |

## Setup Steps

1. `git clone <repo> && cd <repo>`
2. `cp .env.example .env`
3. `npm install`
4. `npm run db:migrate`
5. `npm run dev`

## Verification

| Check | Command | Expected |
|-------|---------|----------|
| Server starts | `curl localhost:3000/health` | `{"status":"ok"}` |
| DB connected | `npm run db:status` | "Connected" |
```

### Mode Adaptation

- **Autonomous**: Every step must be copy-paste-executable. No "configure
  your..." — provide exact values or `[PLACEHOLDER: description]` markers.
- **Pair**: Brief notes are acceptable. Assumes human can fill gaps.
- **Assistant**: Can reference external docs. "See the project wiki for..."
  is acceptable.

---

## Test Plan Document

For Tier 2 plans, generate `test-plan.md` in the plan directory.
This ensures test strategy is defined upfront, not ad-hoc per phase.

### Template

```markdown
# Test Plan

## Strategy
[One paragraph: testing philosophy for this project]

## Test Frameworks

| Layer | Framework | Config File |
|-------|-----------|------------|
| Unit | Jest | `jest.config.ts` |
| Integration | Supertest | `jest.config.ts` |
| E2E | Playwright | `playwright.config.ts` |

## Test Pyramid

| Layer | Target Coverage | Run Command |
|-------|----------------|-------------|
| Unit | 80%+ lines | `npm test -- --coverage` |
| Integration | Critical paths | `npm run test:integration` |
| E2E | Happy paths | `npm run test:e2e` |

## Per-Phase Pass/Fail Criteria

| Phase | Must Pass | Coverage Target |
|-------|-----------|----------------|
| 01 | Unit tests for new models | 80% new code |
| 02 | Integration tests for API | All endpoints |
| 03 | E2E smoke tests | Happy paths |

## Commands

| Action | Command |
|--------|---------|
| Run all tests | `npm test` |
| Run with coverage | `npm test -- --coverage` |
| Run specific suite | `npm test -- --testPathPattern=<pattern>` |
```

### Mode-Specific Constraints

- **Autonomous**: Only automated tests. Every phase must have explicit
  coverage targets. No "manually verify" steps. Include the exact commands
  to run and their expected exit codes.
- **Pair**: Automated tests by default. Up to 2 `[HUMAN-REVIEW]` items
  per phase for visual/UX verification.
- **Assistant**: Flexible. Test plan serves as a discussion guide.
