---
name: core-backend:auth-patterns
description: "Authentication and authorization patterns for backend services: OAuth 2.0 flows (authorization code, client credentials, PKCE), JWT structure and validation, session-based vs token-based auth, RBAC vs ABAC, API key management, and refresh token rotation. Load when implementing authentication, authorization, or identity management."
user-invocable: false
---

# Auth Patterns -- Quick Reference

## Additional resources

- [auth-reference.md](auth-reference.md) -- Full patterns: OAuth 2.0 flow details, JWT implementation, token refresh, RBAC/ABAC, API key management

---

## Auth Strategy Decision Matrix

| Need | Approach | Trade-off |
|------|----------|-----------|
| Browser-based web app | Session-based (cookie) | Requires server-side state; CSRF protection needed |
| SPA / mobile app | OAuth 2.0 + PKCE + JWT | Stateless; must handle token refresh |
| Service-to-service | Client credentials + mTLS | No user context; machine identity |
| Third-party integrations | API keys | Simple but less secure; no expiration by default |
| Microservice mesh | mTLS via service mesh | Zero-trust; transparent to app code |
| External identity provider | OAuth 2.0 authorization code | Delegates auth to IdP; complex setup |

---

## OAuth 2.0 Flows

### Authorization Code (server-side apps)

```
1. Client redirects user to authorization server:
   GET /authorize?response_type=code&client_id=CLIENT_ID
       &redirect_uri=CALLBACK_URL&scope=read+write&state=RANDOM_STATE

2. User authenticates and consents

3. Authorization server redirects back with code:
   GET /callback?code=AUTH_CODE&state=RANDOM_STATE

4. Client exchanges code for tokens (server-side, confidential):
   POST /token
   Body: grant_type=authorization_code&code=AUTH_CODE
         &redirect_uri=CALLBACK_URL&client_id=CLIENT_ID&client_secret=SECRET

5. Authorization server returns:
   { access_token, refresh_token, expires_in, token_type }
```

### Authorization Code + PKCE (SPAs, mobile apps)

```
1. Client generates code_verifier (random 43-128 chars)
   code_challenge = BASE64URL(SHA256(code_verifier))

2. Client redirects with challenge:
   GET /authorize?response_type=code&client_id=CLIENT_ID
       &code_challenge=CHALLENGE&code_challenge_method=S256
       &redirect_uri=CALLBACK_URL&scope=read&state=STATE

3. User authenticates, authorization server redirects with code

4. Client exchanges code with verifier (no client_secret needed):
   POST /token
   Body: grant_type=authorization_code&code=AUTH_CODE
         &code_verifier=VERIFIER&redirect_uri=CALLBACK_URL&client_id=CLIENT_ID
```

### Client Credentials (service-to-service)

```
POST /token
Body: grant_type=client_credentials&client_id=SERVICE_ID
      &client_secret=SERVICE_SECRET&scope=api.read

// Returns access_token only (no refresh token -- service re-authenticates)
```

---

## JWT Structure

```
Header.Payload.Signature

Header:  { "alg": "RS256", "typ": "JWT", "kid": "key-id-1" }
Payload: {
    "sub": "user-123",           // subject (user ID)
    "iss": "https://auth.example.com",  // issuer
    "aud": "https://api.example.com",   // audience
    "exp": 1700000000,           // expiration (Unix timestamp)
    "iat": 1699996400,           // issued at
    "jti": "unique-token-id",    // JWT ID (for revocation)
    "scope": "read write",       // granted scopes
    "roles": ["admin", "user"]   // custom claim
}
Signature: RS256(base64url(header) + "." + base64url(payload), private_key)
```

---

## JWT Validation Checklist

```
function validate_jwt(token, config):
    1. Decode header (without verification) to get 'kid' and 'alg'
    2. Fetch signing key by 'kid' from JWKS endpoint (cache keys with TTL)
    3. Verify signature using the public key
    4. Check 'alg' matches expected algorithm (NEVER accept "none")
    5. Check 'exp' > current_time (token not expired)
    6. Check 'nbf' <= current_time (if present -- token is active)
    7. Check 'iss' matches expected issuer
    8. Check 'aud' contains this service's identifier
    9. Check required scopes/roles are present in claims
    10. Return validated claims
```

**Security rules:**
- Always validate the full chain (signature, expiry, issuer, audience)
- Use asymmetric algorithms (RS256, ES256) -- never HS256 with shared secrets across services
- Cache JWKS keys but refresh on key rotation (check for unknown 'kid')
- Keep access tokens short-lived (5-15 minutes)
- Never store sensitive data in JWT payload (it is base64-encoded, not encrypted)

---

## Session-Based vs Token-Based Auth

| Aspect | Session-Based | Token-Based (JWT) |
|--------|--------------|-------------------|
| State | Server-side session store | Stateless (token is self-contained) |
| Scalability | Requires shared session store (Redis) | No shared state needed |
| Revocation | Immediate (delete session) | Requires token blacklist or short TTL |
| CSRF | Vulnerable (needs CSRF tokens) | Not vulnerable (no cookies by default) |
| XSS | Cookie HTTPOnly protects session ID | Token in localStorage is vulnerable |
| Best for | Traditional web apps, SSR | APIs, SPAs, mobile, microservices |

---

## RBAC vs ABAC

### RBAC (Role-Based Access Control)

```
// Simple: assign roles to users, permissions to roles
roles:
    admin: [read, write, delete, manage_users]
    editor: [read, write]
    viewer: [read]

function check_permission(user, required_permission):
    user_permissions = get_permissions_for_roles(user.roles)
    return required_permission in user_permissions
```

### ABAC (Attribute-Based Access Control)

```
// Flexible: evaluate policies based on attributes of user, resource, and context
policy: "Allow if user.department == resource.department AND time is business hours"

function check_access(user, resource, action, context):
    for policy in applicable_policies(action, resource.type):
        if policy.evaluate(user.attributes, resource.attributes, context):
            return ALLOW
    return DENY
```

| Aspect | RBAC | ABAC |
|--------|------|------|
| Complexity | Simple | Complex |
| Flexibility | Fixed roles | Dynamic policies |
| Best for | Most applications | Multi-tenant, regulatory compliance |
| Audit | Easy (who has what role) | Complex (policy evaluation traces) |

---

## Refresh Token Rotation

```
function refresh_access_token(refresh_token):
    1. Validate refresh token (check signature, expiry, not revoked)
    2. Check token family (detect reuse of old refresh tokens)
    3. If token was already used:
       -> Revoke entire token family (possible token theft)
       -> Force re-authentication
    4. Issue new access token + new refresh token
    5. Mark old refresh token as used (but keep for reuse detection)
    6. Return { access_token, refresh_token, expires_in }

// Token family: all refresh tokens descended from the same login session
// If a revoked refresh token is presented, it means the attacker
// AND the legitimate user both have valid tokens -> revoke everything
```
