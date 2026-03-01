# ADR-007: IP Protection Model — What Is and Is Not Defensible

**Status:** accepted
**Date:** 2026-02-28
**Governing Process:** PROC-LC-003 (Architecture Design)

## Context

claude-kit plugins contain proprietary domain knowledge developed through
significant research and engineering investment. The question of how to protect
this intellectual property during distribution requires an honest assessment of
what is technically defensible and what is not.

### What IS Protectable

1. **Plugin content (copyright):** The specific text of skills, agent
   definitions, grading rubrics, and hook scripts is original authorship
   protected by copyright. Unauthorized redistribution of these files is
   copyright infringement regardless of encryption.

2. **Methodology (trade secret):** The research-backed approach to skill
   design, role architecture, rubric construction, and hook patterns — the
   "how we build plugins" knowledge — is protectable as trade secret so long
   as it is not publicly disclosed.

3. **Platform value (SaaS moat):** Cloud features — session analytics, team
   configuration management, usage dashboards — create value that exists only
   in the platform and cannot be extracted by downloading plugin files.

4. **Ecosystem effects (network moat):** A community registry, organizational
   governance tooling, and third-party plugin ecosystem create switching costs
   that increase with adoption. This is the strongest long-term moat.

### What Is NOT Protectable via Encryption

Any content that Claude reads during a session is visible to the user running
that session. This is a fundamental property of any system where the user
controls the runtime environment:

- The user can enable verbose/debug mode and see skill content in context
- The user can inspect the temp directory during a session before cleanup
- The user can ask Claude to recite its loaded instructions
- The user can examine Claude's conversation history after a session

Encryption at rest raises the effort bar but does not prevent a determined user
from accessing content at runtime. This is not a flaw in the encryption — it
is an inherent property of local execution.

## Decision

claude-kit uses a layered IP protection model that matches the protection
mechanism to the threat:

**Layer 1 — Encryption at rest (AES-256-CBC):**
All content directories are encrypted into a single `content.enc` blob per
plugin before distribution. At runtime, content is decrypted to a temporary
directory, used for the session, and cleaned up on exit. This prevents:
- Casual browsing of plugin files on the filesystem
- Bulk redistribution of plaintext plugin directories
- Automated scraping of plugin content from installed packages

**Layer 2 — Runtime opacity:**
Temporary decrypted directories use randomized paths and are deleted on session
exit. Debug mode does not expose raw skill content. These measures reduce casual
exposure without claiming to prevent determined extraction.

**Layer 3 — Legal protection:**
Plugin content is copyrighted. Distribution terms prohibit redistribution.
This is the actual enforcement mechanism for deliberate infringement.

**Layer 4 — The real moat (strategic):**
The defensible value is not in any single plugin file. It is in:
- **Research depth** — 12 research papers backing architectural decisions that
  competitors would need to independently develop
- **Shipping velocity** — first-mover advantage in domain-specific AI
  development tooling with research-backed architecture
- **Platform value** — cloud features that cannot be extracted from local
  files
- **Ecosystem lock-in** — community plugins, organizational configs, and
  network effects that increase switching costs

## Consequences

### Positive

- Honest threat model — no false promises about what encryption prevents
- Layered defense — each layer addresses a different threat vector
- Strategic clarity — investment prioritizes the real moat (platform,
  ecosystem, velocity) over the illusion of content secrecy
- User trust — not making false security claims builds credibility

### Negative

- Encryption is not a hard barrier — determined users can extract content
  at runtime, and the system must be designed with this assumption
- Legal enforcement is expensive and geographically limited
- The strategic moat (ecosystem, platform) requires significant investment
  before it becomes defensible
- Some customers may expect stronger content protection than is technically
  possible in a local-execution model

### Neutral

- No neutral consequences identified.

## Alternatives Considered

See Context section above for the alternatives evaluated during this decision.

## Traces

- **Upstream:** REQ-008 (Secure Distribution)
- **Downstream:** (future SPEC documents implementing encryption, key management, and
  distribution pipelines)
- **Quality Attributes:** security, transparency, strategic defensibility
