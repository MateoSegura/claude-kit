# Threat Modeling Reference

## STRIDE Worksheet Template

For each component in your system, fill in this worksheet:

### Component: [Name]

| Category | Threat | Likelihood | Impact | Risk | Mitigation | Status |
|----------|--------|-----------|--------|------|------------|--------|
| Spoofing | | L/M/H | L/M/H | | | |
| Tampering | | L/M/H | L/M/H | | | |
| Repudiation | | L/M/H | L/M/H | | | |
| Info Disclosure | | L/M/H | L/M/H | | | |
| Denial of Service | | L/M/H | L/M/H | | | |
| Elevation of Privilege | | L/M/H | L/M/H | | | |

**Status values:** Open, Mitigated, Accepted, Transferred, Avoided

## STRIDE Threat Library

### Spoofing Threats

| Threat | Description | Mitigations |
|--------|-------------|-------------|
| Credential theft | Attacker steals username/password | MFA, rate limiting, breach detection |
| Session hijacking | Attacker steals or predicts session token | Secure cookies, session rotation, IP binding |
| Token forgery | Attacker creates valid-looking tokens | Strong signing keys, short expiry, token validation |
| IP spoofing | Attacker forges source IP | Do not rely on IP for authentication, use mutual TLS |
| DNS spoofing | Attacker redirects domain resolution | DNSSEC, certificate pinning, HSTS |
| Email spoofing | Attacker sends email as your domain | SPF, DKIM, DMARC records |
| API impersonation | Attacker mimics legitimate API client | API key validation, mutual TLS, request signing |

### Tampering Threats

| Threat | Description | Mitigations |
|--------|-------------|-------------|
| SQL injection | Attacker modifies database queries | Parameterized queries, input validation |
| Request tampering | Attacker modifies HTTP requests | Server-side validation, HMAC signatures |
| Man-in-the-middle | Attacker intercepts and modifies traffic | TLS everywhere, certificate pinning, HSTS |
| Log tampering | Attacker modifies audit logs | Append-only logs, separate log infrastructure |
| Config tampering | Attacker modifies application config | File integrity monitoring, signed configs |
| Code injection | Attacker injects executable code | Input validation, CSP, sandboxing |
| Binary tampering | Attacker modifies deployed artifacts | Code signing, checksum verification, SBOM |

### Repudiation Threats

| Threat | Description | Mitigations |
|--------|-------------|-------------|
| Missing audit trail | No record of who did what | Comprehensive logging, audit events |
| Log deletion | Attacker removes evidence | Immutable logs, off-host storage |
| Shared accounts | Cannot attribute actions to individuals | Individual accounts, no shared credentials |
| Timestamp manipulation | Attacker alters event timing | NTP synchronization, tamper-evident logs |
| Transaction disputes | User denies performing action | Digital signatures, confirmation workflows |

### Information Disclosure Threats

| Threat | Description | Mitigations |
|--------|-------------|-------------|
| Verbose error messages | Stack traces expose internals | Generic client errors, detailed server logs |
| Directory listing | Web server exposes file structure | Disable auto-indexing, deny by default |
| Source code exposure | `.git`, backup files accessible | Proper `.gitignore`, web server config |
| API over-exposure | Endpoints return more data than needed | Minimize response fields, use DTOs |
| Side-channel leaks | Timing or size differences reveal info | Constant-time comparisons, padding |
| Cache leakage | Sensitive data in browser/proxy cache | Cache-Control headers, no-store for sensitive |
| Metadata leakage | EXIF data, document properties | Strip metadata before serving |

### Denial of Service Threats

| Threat | Description | Mitigations |
|--------|-------------|-------------|
| Volume-based flood | Overwhelming bandwidth | CDN, DDoS protection, rate limiting |
| Application-layer DoS | Expensive operations triggered cheaply | Rate limiting, request validation, timeouts |
| Resource exhaustion | Memory, CPU, disk, connection limits | Resource limits, monitoring, auto-scaling |
| Algorithmic complexity | Exploiting O(n^2) or worse algorithms | Input size limits, algorithm analysis |
| Regex DoS (ReDoS) | Crafted input causes exponential backtracking | Safe regex patterns, timeouts, RE2 engine |
| Zip bomb | Compressed file expands enormously | Decompression limits, stream processing |
| Account lockout abuse | Locking out legitimate users | Progressive delays instead of hard lockout |

### Elevation of Privilege Threats

| Threat | Description | Mitigations |
|--------|-------------|-------------|
| IDOR | Accessing another user's resources by ID | Authorization checks on every access |
| Privilege escalation | Normal user gains admin access | Role-based access, server-side enforcement |
| JWT manipulation | Altering token claims | Signature verification, algorithm pinning |
| Path traversal | Accessing files outside allowed directory | Canonicalize paths, chroot/sandbox |
| Deserialization attacks | Malicious serialized objects | Allowlist deserialization, avoid native serialization |
| Container escape | Breaking out of container isolation | Rootless containers, seccomp, AppArmor |
| Dependency hijacking | Malicious package gains code execution | Lock files, hash verification, minimal permissions |

## Data Flow Diagram Templates

### Web Application (Typical)

```
+---------+       HTTPS        +-----------+       SQL        +----------+
| Browser | =================> | Web Server| ==============> | Database |
|  (User) | <================= | (Process) | <============== | (Store)  |
+---------+       HTML/JSON    +-----------+       Results    +----------+
                                     |
                     - - - - - - - - | - - - - - - - - -
                     Trust boundary  |  (internal network)
                                     |
                               +-----------+
                               |  Cache    |
                               |  (Redis)  |
                               +-----------+
```

### Microservices Architecture

```
                    TRUST BOUNDARY (Internet)
- - - - - - - - - - - - - | - - - - - - - - - - - - -
                           |
+---------+   HTTPS   +---------+   gRPC   +---------+
| Mobile  | ========> |   API   | =======> | Auth    |
|  App    | <======== | Gateway | <======= | Service |
+---------+           +---------+          +---------+
                           |                    |
                      +---------+          +---------+
                      | Order   |          | User    |
                      | Service |          |   DB    |
                      +---------+          +---------+
                           |
                      +---------+
                      | Payment |---------> External
                      | Service |           Payment
                      +---------+           Provider
                           |
              - - - - - - -|- - - - - - -
              Trust boundary (PCI zone)
```

### IoT / Embedded System

```
+---------+    BLE/WiFi    +-----------+     MQTT/TLS     +----------+
| Sensor  | =============> |  Gateway  | ===============> |  Cloud   |
| Device  | <============= |  (Edge)   | <=============== | Backend  |
+---------+   Commands     +-----------+   Telemetry      +----------+
    |                           |                              |
 [Firmware]              [Certificate]                   +-----------+
 [Signed]                [Store]                         | Dashboard |
                                                         | (Web UI)  |
                                                         +-----------+
  - - - - - - - - - -     - - - - - - -     - - - - - - - - - - - -
  Physical boundary        Network edge      Cloud trust boundary
```

## Attack Trees

### Example: Unauthorized Data Access

```
Goal: Access customer PII
  |
  +-- 1. Exploit application vulnerability
  |     +-- 1.1 SQL injection (A03)
  |     +-- 1.2 IDOR — enumerate user IDs (A01)
  |     +-- 1.3 API returns excessive data (A01)
  |
  +-- 2. Compromise credentials
  |     +-- 2.1 Credential stuffing (leaked passwords)
  |     +-- 2.2 Phishing admin account
  |     +-- 2.3 Brute force weak passwords
  |
  +-- 3. Insider threat
  |     +-- 3.1 Over-privileged service account
  |     +-- 3.2 Developer with production DB access
  |     +-- 3.3 Shared credentials
  |
  +-- 4. Infrastructure compromise
        +-- 4.1 Unpatched server vulnerability
        +-- 4.2 Exposed database port
        +-- 4.3 Stolen cloud credentials
```

## Risk Assessment Scoring

### Qualitative Risk Matrix (Detailed)

**Likelihood scale:**

| Level | Description | Criteria |
|-------|-------------|----------|
| Very High | Almost certain | Known exploit, low skill required, high motivation |
| High | Likely | Exploit exists, moderate skill, some motivation |
| Medium | Possible | Theoretical, requires skill, opportunistic |
| Low | Unlikely | Requires significant effort, low reward |
| Very Low | Rare | Requires insider access + expert skill + high risk |

**Impact scale:**

| Level | Description | Criteria |
|-------|-------------|----------|
| Critical | Catastrophic | Mass data breach, complete system compromise, regulatory action |
| High | Severe | Significant data loss, extended downtime, financial loss |
| Medium | Moderate | Limited data exposure, temporary disruption, manageable cost |
| Low | Minor | Minimal exposure, brief disruption, negligible cost |
| Negligible | Insignificant | No real impact, theoretical concern only |

### DREAD Scoring (Alternative)

Rate each factor 1-10:

| Factor | Question |
|--------|----------|
| **D**amage | How bad is the impact? |
| **R**eproducibility | How easy to reproduce? |
| **E**xploitability | How easy to exploit? |
| **A**ffected users | How many users impacted? |
| **D**iscoverability | How easy to find? |

**Risk = (D + R + E + A + D) / 5**

| Score | Rating |
|-------|--------|
| 8-10 | Critical |
| 5-7 | High |
| 3-4 | Medium |
| 1-2 | Low |

## Secure Boot Chain of Trust — Extended

### Generic Boot Chain

```
Stage 0: Hardware Root of Trust
  - Immutable: ROM code or hardware fuses
  - Contains: Public key hash for Stage 1 verification
  - Cannot be updated or modified

Stage 1: First-Stage Bootloader
  - Verified by: Stage 0 using embedded public key
  - Purpose: Hardware init, load and verify Stage 2
  - Size: Minimal (fits in ROM/OTP shadow)
  - Update: Rarely (if ever) — often locked after provisioning

Stage 2: Second-Stage Bootloader
  - Verified by: Stage 1
  - Purpose: Load OS/firmware, manage updates, recovery
  - Features: A/B slots, rollback protection, recovery mode
  - Examples: MCUboot, U-Boot, UEFI, Coreboot

Stage 3: Operating System / Firmware
  - Verified by: Stage 2
  - Purpose: Run application code
  - Features: Kernel signature verification, dm-verity (Linux)

Stage 4: Application
  - Verified by: OS-level mechanisms
  - Purpose: User-facing functionality
  - Features: Code signing, sandboxing, permission model
```

### Key Management for Boot Chain

| Key | Storage | Usage | Rotation |
|-----|---------|-------|----------|
| Root key (private) | HSM, offline | Signs Stage 1 image | Never (or re-provision) |
| Root key (public hash) | Hardware fuses/OTP | Verifies Stage 1 | Cannot rotate |
| Signing key (private) | Secure build server | Signs firmware images | Per release cycle |
| Signing key (public) | Bootloader | Verifies firmware | Updated with bootloader |
| Encryption key | Hardware/fuses | Protects image confidentiality | Per device family |

### Anti-Rollback Protection

```
Current version: 2.1.0 (security counter = 5)

Update to 2.2.0 (counter = 6):  ALLOWED — counter >= current
Update to 2.0.0 (counter = 3):  REJECTED — counter < current
Update to 2.1.1 (counter = 5):  ALLOWED — counter >= current
```

**Implementation approaches:**
- Monotonic counter in OTP fuses (hardware-backed, limited writes)
- Signed version number in image header (software-backed)
- Replay-protected memory block (RPMB) on eMMC

## Compliance Frameworks (Reference)

| Framework | Focus | Key Security Requirements |
|-----------|-------|--------------------------|
| SOC 2 | Service organizations | Access control, encryption, monitoring, incident response |
| PCI DSS | Payment card data | Network segmentation, encryption, access control, testing |
| HIPAA | Health information | Access control, audit trails, encryption, risk assessment |
| GDPR | Personal data (EU) | Data minimization, consent, breach notification, DPIAs |
| ISO 27001 | Information security | Risk management, asset management, access control |
| NIST CSF | Cybersecurity | Identify, Protect, Detect, Respond, Recover |
| CIS Controls | Prioritized actions | Asset inventory, secure config, vulnerability management |

## Threat Modeling Process Checklist

### Before the Session

- [ ] Identify the system or feature to model
- [ ] Gather architecture diagrams and documentation
- [ ] Identify participants (dev, security, ops, product)
- [ ] Prepare DFD templates

### During the Session

- [ ] Draw or update the data flow diagram
- [ ] Identify all trust boundaries
- [ ] Walk through each component using STRIDE
- [ ] Rate likelihood and impact for each threat
- [ ] Determine response for each threat (mitigate, accept, transfer, avoid)
- [ ] Assign owners and timelines for mitigations

### After the Session

- [ ] Document all findings in the threat model
- [ ] Create tickets for agreed mitigations
- [ ] Schedule follow-up review
- [ ] Update threat model when architecture changes
- [ ] Validate mitigations through testing
