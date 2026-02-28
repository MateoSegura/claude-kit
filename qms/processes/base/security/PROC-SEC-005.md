# PROC-SEC-005: Encryption & Key Management

**Version:** 1.0.0
**Status:** draft
**Category:** security
**Layer:** base
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Manage the encryption of plugin content for distribution and the lifecycle of encryption keys. Plugins are encrypted at rest using AES-256-CBC to protect intellectual property during distribution.

## 2. Scope

Covers plugin encryption/decryption workflows, the split-key assembly pattern in the CLI, key rotation procedures, and encrypted distribution packaging.

## 3. Entry Criteria

- [ ] Encryption script (scripts/encrypt-plugins.sh) is available
- [ ] Split-key assembly function (_get_key()) is implemented in the CLI
- [ ] openssl is available in the execution environment

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Plaintext plugin content | plugins/ directories | Markdown, JSON, shell |
| Encryption key parts | claude-kit CLI (_get_key) | Assembled at runtime |
| openssl | System tool | CLI binary |

## 5. Activities

### 5.1 Plugin Encryption

During distribution packaging:
- Content directories (agents/, commands/, skills/, hooks/, scripts/) are tarred
- The tar archive is encrypted with AES-256-CBC via openssl
- Result is a single content.enc blob per plugin
- plugin.json and ctl.json remain plaintext (needed for loading)

### 5.2 Key Assembly

The encryption key is assembled at runtime from split parts:
- Parts are defined in the _get_key() function in the CLI
- The assembled key is never stored as a single string
- The key is never logged, printed, or committed

### 5.3 Runtime Decryption

During plugin loading (claude-kit update):
- CLI assembles the key from parts
- Decrypts content.enc to a temporary directory
- Plugin content is loaded from the temp directory
- Temp directory is cleaned up on exit

### 5.4 Key Rotation

When key rotation is required:
- New key parts are defined
- All plugins are re-encrypted with the new key
- Old encrypted bundles are replaced
- Users must update to get new encrypted packages

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Encrypted plugin bundles | dist/ | — | — |
| Key rotation records | docs/compliance/ | — | — |

## 7. Exit Criteria

- [ ] All distributed plugins are encrypted
- [ ] Key material is not exposed in any output
- [ ] Decryption produces correct plaintext content

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Encryption integrity | Decrypt and compare | Decrypted content matches original |
| Key exposure check | grep for key material in logs/output | Zero matches |
| Plaintext removal | Check dist/ directory | No plaintext content files |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Repository Owner | Authorize key changes, manage key parts |
| Release Engineer | Execute encryption during release packaging |
| Developer | Never expose key material |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Key rotation frequency | How often the key is rotated | Annually | Tracking record |
| Encryption coverage | % of distributed plugins encrypted | 100% | Release audit |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| NIST 800-53 | SC-12, SC-13 | Cryptographic key management, protection |
| NIST 800-171 | 3.13.11 | CUI encryption |

## 12. Tailoring Guidance

**Minimum viable:** Encrypt all plugins with AES-256-CBC, never expose the key.
**Full ceremony:** Add key rotation schedule, formal key custody chain, HSM storage for key parts.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SEC-001 | Secure development includes key protection rules |
| PROC-SEC-003 | Key compromise triggers incident response |
| PROC-SEC-004 | Access control covers who can access key material |
| PROC-LC-006 | Release management includes encryption step |

## 14. Traces

- **Governs:** Plugin encryption workflow, key management procedures
- **Enforced by:** `scripts/encrypt-plugins.sh`, `.claude/rules/security.md`, key exposure hooks
- **Related QA:** QA-008 (Dual Deployment Architecture — encryption for air-gap delivery)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |
