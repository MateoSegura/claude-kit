---
name: core-security:secure-coding
description: "OWASP Top 10 awareness, input validation, output encoding, injection prevention, and secure defaults for any software project"
user-invocable: false
---

# Secure Coding Quick Reference

## OWASP Top 10 Overview (2021)

| # | Category | Core Prevention |
|---|----------|----------------|
| A01 | Broken Access Control | Deny by default, enforce server-side, validate ownership |
| A02 | Cryptographic Failures | Use strong algorithms, never store plaintext secrets |
| A03 | Injection | Parameterize queries, validate input, encode output |
| A04 | Insecure Design | Threat model early, use secure design patterns |
| A05 | Security Misconfiguration | Harden defaults, disable unused features, patch promptly |
| A06 | Vulnerable Components | Track dependencies, scan regularly, update quickly |
| A07 | Auth Failures | Use MFA, rate-limit logins, use proven frameworks |
| A08 | Data Integrity Failures | Verify sources, sign artifacts, validate serialized data |
| A09 | Logging Failures | Log security events, protect logs, monitor for anomalies |
| A10 | SSRF | Validate URLs, allowlist destinations, isolate fetches |

## Input Validation

**Validate all external input at system boundaries:**

- Reject unexpected types, lengths, and ranges before processing
- Use allowlists over denylists — define what is permitted, not what is forbidden
- Validate on the server side even if client-side validation exists
- Canonicalize data before validation (normalize Unicode, resolve paths)

**Common input sources to validate:**

- HTTP parameters (query, body, headers, cookies)
- File uploads (type, size, name, content)
- API request payloads
- Environment variables from external sources
- Database results when used in further queries

## Output Encoding

Encode output based on the context where it will be rendered:

| Context | Encoding | Example |
|---------|----------|---------|
| HTML body | HTML entity encoding | `<` becomes `&lt;` |
| HTML attribute | Attribute encoding | Quote and encode special chars |
| JavaScript | JavaScript encoding | Escape `'`, `"`, `\`, newlines |
| URL parameter | URL/percent encoding | `encodeURIComponent()` |
| CSS value | CSS encoding | Escape non-alphanumeric chars |
| SQL | Parameterized queries | Never concatenate user input |

## Injection Prevention

### SQL Injection

```
WRONG:  query("SELECT * FROM users WHERE id = " + userId)
RIGHT:  query("SELECT * FROM users WHERE id = ?", [userId])
```

Always use parameterized queries or prepared statements. ORMs typically handle this, but verify raw query escape paths.

### Command Injection

```
WRONG:  exec("ping " + hostname)
RIGHT:  execFile("ping", [hostname])  // pass args as array
```

Avoid shell execution when possible. Use language APIs that accept argument arrays instead of shell strings. If shell is required, use strict allowlists on input.

### Path Traversal

```
WRONG:  readFile("/uploads/" + filename)
RIGHT:  Resolve path, verify it starts with allowed base directory
```

Canonicalize the path (resolve `..`, symlinks), then verify the resolved path is within the expected directory.

### XSS Prevention

- Use frameworks with auto-escaping templates (React, Angular, Jinja2 with autoescape)
- Set `Content-Security-Policy` headers
- Use `HttpOnly` and `Secure` flags on sensitive cookies
- Sanitize rich text with proven libraries, never regex

### CSRF Protection

- Use anti-CSRF tokens (synchronizer pattern or double-submit cookie)
- Verify `Origin` and `Referer` headers on state-changing requests
- Use `SameSite` cookie attribute (`Lax` or `Strict`)

## Secure Defaults

- **Deny by default**: All access denied unless explicitly granted
- **Fail securely**: Errors should not leak information or grant access
- **Least privilege**: Components run with minimum required permissions
- **Defense in depth**: Multiple layers — never rely on a single control
- **Separation of duties**: Split critical operations across roles or services

## Authentication Checklist

- [ ] Use proven authentication frameworks — do not build your own
- [ ] Hash passwords with bcrypt, scrypt, or Argon2 (never MD5/SHA alone)
- [ ] Enforce minimum password length (12+ characters recommended)
- [ ] Implement account lockout or progressive delays after failed attempts
- [ ] Use MFA for privileged accounts
- [ ] Generate session tokens with cryptographic randomness
- [ ] Invalidate sessions on logout, password change, and privilege escalation
- [ ] Set session expiration timeouts

## Authorization Checklist

- [ ] Enforce authorization on every request, server-side
- [ ] Verify resource ownership — user A cannot access user B's data
- [ ] Use role-based (RBAC) or attribute-based (ABAC) access control
- [ ] Log authorization failures for monitoring
- [ ] Deny by default — explicit grants only
- [ ] Re-validate permissions before destructive operations

## Cryptography Basics

**Use:**
- AES-256-GCM for symmetric encryption
- RSA-2048+ or ECDSA P-256+ for asymmetric operations
- SHA-256+ for hashing
- HMAC for message authentication
- TLS 1.2+ for transport security

**Avoid:**
- DES, 3DES, RC4, MD5, SHA-1 for security purposes
- ECB mode for block ciphers
- Custom cryptographic implementations
- Hardcoded keys or IVs

## HTTP Security Headers

```
Content-Security-Policy: default-src 'self'; script-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

## Additional Resources

For detailed checklists, code patterns, and prevention strategies organized by vulnerability class, see [secure-coding-reference.md](secure-coding-reference.md).
