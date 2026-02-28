# research/ — Theoretical Research

**Governing Process:** PROC-LC-001 (Market Analysis)

This directory contains theoretical research papers exploring the foundations of
AI-assisted software development. These papers inform requirements and
architecture decisions but are not operational documents.

For a guided tour of all papers and their relationships, see
[overview.md](overview.md).

## Papers

| Paper | Topic |
|-------|-------|
| [overview.md](overview.md) | Research overview and paper relationships |
| [agent-friendly-codebases.md](agent-friendly-codebases.md) | Structuring code for AI agent consumption |
| [ai-instrumentation.md](ai-instrumentation.md) | Repository instrumentation for AI agents |
| [ai-native-engineer.md](ai-native-engineer.md) | The AI-native engineering workflow |
| [developer-tools-landscape.md](developer-tools-landscape.md) | Developer tools ecosystem analysis |
| [human-agent-orchestration.md](human-agent-orchestration.md) | Human-agent collaboration patterns |
| [intent-formalization.md](intent-formalization.md) | Formalizing developer intent |
| [llm-non-determinism.md](llm-non-determinism.md) | Managing LLM non-determinism |
| [memory-architecture.md](memory-architecture.md) | Agent memory systems |
| [multi-agent-architecture.md](multi-agent-architecture.md) | Multi-agent system design |
| [runtime-governance.md](runtime-governance.md) | Runtime governance patterns |
| [state-and-roadmap.md](state-and-roadmap.md) | Project state and roadmap |
| [symbolic-scaffolding.md](symbolic-scaffolding.md) | Symbolic scaffolding for AI |
| [theory-context-cache.md](theory-context-cache.md) | Context cache architecture theory |

## Relationship to Other Layers

Research papers sit at the beginning of the traceability chain. When a research
insight becomes actionable, it should be formalized as a requirement in
`docs/requirements/` with a trace back to the originating paper.
