# methodology/ — Requirements Derivation and Research Methodology

**Governing Process:** PROC-ORG-001 (Process Governance)

This layer is **meta-documentation** — it describes HOW the other documentation
layers were created, what evidence supports them, and where the gaps are. It
exists so that a reader encountering claude-kit's requirements and architecture
decisions for the first time can evaluate the rigor of the process that produced
them.

Methodology documents are free-form (no ID prefix). They are cross-cutting —
they reference documents in other layers but are not part of the forward
traceability chain (research → requirements → architecture → specs).

## Documents

| Document | What It Answers |
|----------|----------------|
| `requirements-derivation.md` | How were the 10 requirements identified? What methodology drove the selection? How do we know these are the right 10? |
| `evidence-quality.md` | How strong is the evidence behind each claim? Academic vs. industry vs. practitioner sources — graded. |
| `coverage-analysis.md` | What does the research cover well, partially, and not at all? Competitive gap mapping. |

## Who This Is For

- **Investors / business evaluators:** "How do I know your requirements are
  systematically derived and not cherry-picked?"
- **Technical advisors:** "What's the evidence quality? How reproducible is
  the methodology?"
- **Enterprise buyers:** "How does this map to the problems my team actually
  has?"
- **The team itself:** "Where are our blind spots?"

## Not Part of the Traceability Chain

Methodology documents do not use ID prefixes (REQ-XXX, ADR-XXX) because they
are not traceable artifacts — they are process documentation. They reference
other layers' documents but are not referenced BY those documents.
