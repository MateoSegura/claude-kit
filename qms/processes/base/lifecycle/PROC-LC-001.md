# PROC-LC-001: Market Analysis

**Version:** 1.0.0
**Status:** draft
**Category:** lifecycle
**Layer:** base
**Maturity:** initial
**Owner:** Product Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Market Analysis provides a structured approach to understanding the competitive landscape, identifying customer needs, and tracking technology trends that inform product direction. This process ensures that claude-kit's development priorities are grounded in real market signals rather than assumptions, and that research findings are captured in a durable, referenceable format within the documentation system.

## 2. Scope

**Included:**
- Competitive landscape analysis of AI-native developer tools
- Customer need identification for target segments (defense contractors, federal agencies, enterprises)
- Technology trend tracking for Claude model capabilities, plugin architectures, and AI governance frameworks
- Research paper creation and maintenance in `docs/research/`
- Market signal synthesis that feeds into requirements engineering

**Excluded:**
- Sales or marketing execution (messaging, campaigns, pricing)
- Product roadmap prioritization (handled by Requirements Engineering, PROC-LC-002)
- Financial modeling or revenue forecasting

## 3. Entry Criteria

- [ ] A new technology trend, competitive development, or customer signal has been identified
- [ ] The topic does not already have an existing research paper covering it in `docs/research/`
- [ ] Sufficient publicly available information exists to produce a substantive analysis

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Customer feedback and requests | Support channels, GitHub issues | Unstructured text |
| Competitive product announcements | Public releases, documentation | Web content |
| Technology trend signals | Academic papers, vendor announcements, SDK changelogs | Mixed formats |
| Existing research papers | `docs/research/` | Markdown files |
| Current requirements | `docs/requirements/REQ-XXX` | Structured requirement documents |

## 5. Activities

### 5.1 Trend Identification

Monitor external signals that may affect claude-kit's product direction. Sources include Anthropic model release notes, competing tool announcements (Cursor, Windsurf, Cline, Aider), regulatory changes affecting AI in defense and federal sectors, and shifts in developer workflow patterns. Record each signal with a date stamp and source link in a triage list.

### 5.2 Competitive Landscape Analysis

For each significant competitor or adjacent tool, document: product positioning, feature set relevant to claude-kit's domain, pricing model, target market overlap, and technical architecture differences. The existing `docs/research/developer-tools-landscape.md` serves as the canonical competitive analysis document and should be updated incrementally rather than rewritten.

### 5.3 Customer Need Synthesis

Aggregate customer signals from GitHub issues, direct feedback, and usage patterns into need categories. Map each need to an existing requirement (REQ-XXX) or flag it as a potential new requirement. Prioritize needs by frequency, strategic importance to target markets (defense, federal, enterprise), and feasibility given current architecture.

### 5.4 Research Paper Creation

When a topic warrants deep analysis, create a new research paper in `docs/research/`. Follow the conventions established by the existing 14 papers: narrative structure, cross-references to other research papers, and actionable insights that connect to requirements or architecture decisions. Add the paper to `docs/research/INDEX.md` and to `docs/research/overview.md`.

### 5.5 Market Signal Review

Quarterly, review all accumulated signals and research papers. Identify patterns that suggest new requirements, architecture pivots, or deprecation candidates. Produce a brief synthesis memo that feeds into Requirements Engineering (PROC-LC-002).

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Research papers | `docs/research/` | — (narrative format) | No ID prefix |
| Research overview | `docs/research/overview.md` | — | — |
| Research index | `docs/research/INDEX.md` | — | — |
| Market signal synthesis | `docs/research/state-and-roadmap.md` | — | — |

## 7. Exit Criteria

- [ ] Research paper (if created) is reviewed for factual accuracy and internal consistency
- [ ] Paper is added to `docs/research/INDEX.md` and referenced in `docs/research/overview.md`
- [ ] Actionable findings are documented with explicit links to existing REQ-XXX documents or flagged as candidates for new requirements
- [ ] `bash scripts/validate-docs.sh` passes with the new or modified document

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Research depth | Peer review of paper | Paper contains specific, verifiable claims with source attribution; no unsupported generalizations |
| Cross-reference integrity | `scripts/validate-docs.sh` | All document references resolve to real files |
| Actionability | Review checklist | At least one finding links to or proposes a REQ-XXX requirement |
| Currency | Date check | No research paper older than 12 months without a review annotation |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Product Lead | Prioritizes which market signals warrant deep research; approves synthesis memos |
| Research Author | Writes and maintains research papers; ensures cross-references are valid |
| Technical Lead | Reviews research for technical accuracy and feasibility of proposed directions |
| Requirements Engineer | Receives market signal synthesis and translates actionable findings into REQ-XXX documents |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Research coverage | Number of research papers covering active market trends | >= 10 active papers | Count files in `docs/research/` |
| Signal-to-requirement ratio | Percentage of identified market signals that result in REQ-XXX documents | >= 30% | Manual tracking per quarterly review |
| Research currency | Percentage of papers updated or reviewed within last 6 months | >= 80% | Git log analysis on `docs/research/` |
| Competitive coverage | Number of major competitors with documented analysis | >= 3 competitors | Review `developer-tools-landscape.md` |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.1.1 Business analysis | Market analysis feeds business and stakeholder requirements |
| ISO/IEC 33001 | Process capability | Research process maturity contributes to organizational process capability |
| NIST SP 800-218 | PO.1.1 | Security requirements from market analysis feed secure development practices |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** Skip formal synthesis memos. Maintain research papers in `docs/research/` and add a one-line "Implications" section at the end of each paper that notes requirements impact. Review papers when starting a new feature.

**Full ceremony (team with dedicated product role):** Execute all activities including quarterly signal reviews, formal synthesis memos, and cross-functional review of research papers before they influence requirements.

**When to skip entirely:** Internal tooling projects with a single known customer and no competitive pressure. Even then, technology trend tracking (Activity 5.1) remains valuable for architecture decisions.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-002 | Feeds into: market signal synthesis drives requirements engineering |
| PROC-LC-003 | Feeds into: technology trend analysis informs architecture decisions |
| PROC-ORG-004 | Feeds into: competitive analysis contributes to risk identification |
| PROC-ORG-005 | Related: supplier (Anthropic) capability tracking overlaps with technology trends |
| PROC-LC-008 | Receives from: improvement proposals may trigger new market analysis |

## 14. Traces

- **Governs:** `docs/research/` (all research papers, overview, index)
- **Enforced by:** `scripts/validate-docs.sh` (cross-reference integrity)
- **Related QA:** Market responsiveness, product-market fit

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing research paper practice into a governed process |
