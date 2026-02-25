# core-security

> **Role:** Knowledge companion · **Version:** 0.0.1

General-purpose secure development — OWASP awareness, secrets management, dependency scanning, and threat modeling for any software project.

This plugin is **auto-loaded as a companion** by role plugins that declare it. Do not launch it directly.

---

## Skills Inventory

| Skill | Domain Coverage |
|-------|----------------|
| `secure-coding` | OWASP Top 10 awareness, input validation, output encoding, SQL/command injection prevention, XSS/CSRF protection, secure defaults, authentication and authorization checklists, HTTP security headers |
| `secrets-management` | Environment variables, .env file patterns, vault system concepts (HashiCorp Vault, AWS/GCP/Azure), credential rotation strategies, CI/CD secrets handling, pre-commit secret detection, Docker/Kubernetes secrets |
| `dependency-scanning` | Supply chain attack vectors, SCA tool overview (npm audit, pip-audit, govulncheck, cargo-audit, Dependabot, Snyk, Trivy), SBOM generation, CVSS severity interpretation, update strategies, license compliance |
| `threat-modeling` | STRIDE methodology with threat library, data flow diagrams, trust boundary analysis, attack surface reduction, risk assessment matrices, DREAD scoring, secure boot chain of trust (generic), compliance framework reference |

---

## Auto-Loading

Role plugins that declare `core-security` as a companion will automatically inject all its skills into their agent context at launch.
