# Auth Patterns -- Full Reference

Complete patterns for authentication and authorization in backend services.

---

## OAuth 2.0 Authorization Code Flow -- Detailed

### Step-by-step with security considerations

```
// 1. Generate state parameter (CSRF protection)
state = generate_random_string(32)
store_in_session("oauth_state", state)

// 2. Build authorization URL
auth_url = "https://auth.example.com/authorize?" + url_encode({
    response_type: "code",
    client_id: CLIENT_ID,
    redirect_uri: "https://app.example.com/callback",
    scope: "openid profile email",
    state: state,
    // Optional: prompt=consent (force consent screen)
    // Optional: login_hint=user@example.com (pre-fill email)
})

// 3. Redirect user to auth_url
redirect(auth_url)

// 4. Handle callback
function handle_callback(request):
    // Verify state matches
    if request.params.state != session.get("oauth_state"):
        raise SecurityError("CSRF detected -- state mismatch")

    // Check for error response
    if request.params.error:
        raise AuthError(request.params.error_description)

    // Exchange code for tokens
    response = http.post("https://auth.example.com/token", {
        grant_type: "authorization_code",
        code: request.params.code,
        redirect_uri: "https://app.example.com/callback",
        client_id: CLIENT_ID,
        client_secret: CLIENT_SECRET,
    })

    // Validate response
    if response.status != 200:
        raise AuthError("Token exchange failed")

    tokens = response.json()
    // tokens = { access_token, refresh_token, id_token, expires_in, token_type }

    // If using OpenID Connect, validate id_token
    if tokens.id_token:
        user_info = validate_and_decode_jwt(tokens.id_token)

    // Store tokens securely
    session.set("access_token", tokens.access_token)
    session.set("refresh_token", tokens.refresh_token)
    session.set("token_expires_at", now() + tokens.expires_in)
```

---

## PKCE Implementation Details

```
// Code verifier: cryptographically random string, 43-128 characters
// Allowed characters: [A-Z] [a-z] [0-9] - . _ ~
function generate_code_verifier():
    return base64url_encode(random_bytes(32))
    // Example: "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"

// Code challenge: SHA-256 hash of verifier, base64url-encoded
function generate_code_challenge(verifier):
    return base64url_encode(sha256(verifier))
    // Example: "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

// Authorization request includes challenge:
// GET /authorize?...&code_challenge=CHALLENGE&code_challenge_method=S256

// Token exchange includes verifier (NOT challenge):
// POST /token body includes code_verifier=VERIFIER
// Server computes SHA256(verifier) and compares to stored challenge

// Why PKCE matters:
// Without PKCE, an attacker who intercepts the authorization code
// (via malicious app, browser extension, or redirect interception)
// can exchange it for tokens. With PKCE, the attacker would also
// need the code_verifier, which never leaves the client.
```

---

## JWT Implementation Patterns

### Token creation

```
function create_access_token(user, scopes, config):
    now = current_timestamp()
    payload = {
        sub: user.id,
        iss: config.issuer,
        aud: config.audience,
        exp: now + config.access_token_ttl,   // 5-15 minutes
        iat: now,
        jti: generate_uuid(),
        scope: join(scopes, " "),
        roles: user.roles,
        // Add custom claims as needed:
        tenant_id: user.tenant_id,
    }
    return sign_jwt(payload, config.private_key, algorithm="RS256", kid=config.key_id)

function create_refresh_token(user, family_id, config):
    payload = {
        sub: user.id,
        iss: config.issuer,
        exp: current_timestamp() + config.refresh_token_ttl,  // 7-30 days
        jti: generate_uuid(),
        family: family_id,   // token family for rotation detection
        type: "refresh",
    }
    return sign_jwt(payload, config.private_key, algorithm="RS256", kid=config.key_id)
```

### JWKS endpoint

```
// Serve public keys at /.well-known/jwks.json
// Clients use this to verify JWT signatures

GET /.well-known/jwks.json
Response:
{
    "keys": [
        {
            "kty": "RSA",
            "kid": "key-id-1",
            "use": "sig",
            "alg": "RS256",
            "n": "<RSA modulus, base64url>",
            "e": "AQAB"
        },
        {
            "kty": "RSA",
            "kid": "key-id-2",   // rotated key
            "use": "sig",
            "alg": "RS256",
            "n": "<RSA modulus, base64url>",
            "e": "AQAB"
        }
    ]
}

// Key rotation strategy:
// 1. Generate new key pair, add to JWKS with new kid
// 2. Start signing new tokens with new kid
// 3. Keep old key in JWKS until all tokens signed with it expire
// 4. Remove old key from JWKS after grace period
```

### Token validation middleware

```
function jwt_auth_middleware(request, next):
    // Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.starts_with("Bearer "):
        return error_response(401, "Missing or invalid Authorization header")

    token = auth_header.remove_prefix("Bearer ")

    try:
        claims = validate_jwt(token, {
            issuer: config.expected_issuer,
            audience: config.expected_audience,
            jwks_uri: config.jwks_uri,
        })
    catch TokenExpiredError:
        return error_response(401, "Token expired")
    catch InvalidTokenError as e:
        return error_response(401, "Invalid token: " + e.message)

    // Attach claims to request context
    request.auth = {
        user_id: claims.sub,
        roles: claims.roles,
        scopes: claims.scope.split(" "),
        tenant_id: claims.tenant_id,
    }

    return next(request)
```

---

## Refresh Token Rotation -- Full Implementation

```
// Database table for tracking refresh tokens
table refresh_tokens:
    jti: string (primary key)       // JWT ID
    family_id: string (indexed)     // token family
    user_id: string (indexed)
    used: boolean (default false)
    revoked: boolean (default false)
    expires_at: timestamp
    created_at: timestamp

function handle_token_refresh(refresh_token_string):
    // 1. Decode and validate refresh token
    claims = validate_jwt(refresh_token_string, config)
    if claims.type != "refresh":
        raise InvalidTokenError("Not a refresh token")

    // 2. Look up token record
    token_record = db.query(
        "SELECT * FROM refresh_tokens WHERE jti = ?", claims.jti
    )
    if not token_record:
        raise InvalidTokenError("Unknown refresh token")

    // 3. Check for reuse (possible token theft)
    if token_record.used or token_record.revoked:
        // Token was already used! Revoke entire family
        db.execute(
            "UPDATE refresh_tokens SET revoked = true WHERE family_id = ?",
            token_record.family_id
        )
        log.security("Refresh token reuse detected",
            user_id=claims.sub, family=token_record.family_id)
        raise SecurityError("Token reuse detected -- all sessions revoked")

    // 4. Mark old token as used
    db.execute("UPDATE refresh_tokens SET used = true WHERE jti = ?", claims.jti)

    // 5. Load user and issue new tokens
    user = user_service.get(claims.sub)
    if not user or user.is_disabled:
        raise AuthError("User not found or disabled")

    new_access_token = create_access_token(user, user.scopes, config)
    new_refresh_token = create_refresh_token(user, token_record.family_id, config)

    // 6. Store new refresh token
    new_claims = decode_jwt_unverified(new_refresh_token)
    db.insert(refresh_tokens, {
        jti: new_claims.jti,
        family_id: token_record.family_id,
        user_id: user.id,
        expires_at: timestamp_from_unix(new_claims.exp),
    })

    return { access_token: new_access_token, refresh_token: new_refresh_token }

// Cleanup: periodically delete expired token records
// DELETE FROM refresh_tokens WHERE expires_at < now() - interval '30 days'
```

---

## RBAC Implementation

```
// Database schema
table roles:
    id: uuid
    name: string (unique)        // "admin", "editor", "viewer"
    description: string

table permissions:
    id: uuid
    name: string (unique)        // "orders:read", "orders:write", "users:manage"
    description: string

table role_permissions:
    role_id: uuid (FK -> roles)
    permission_id: uuid (FK -> permissions)
    primary key (role_id, permission_id)

table user_roles:
    user_id: uuid (FK -> users)
    role_id: uuid (FK -> roles)
    tenant_id: uuid (optional, for multi-tenant)
    primary key (user_id, role_id, tenant_id)

// Permission check
function require_permission(required_permission):
    return function middleware(request, next):
        user_permissions = get_user_permissions(request.auth.user_id)
        if required_permission not in user_permissions:
            return error_response(403, "Insufficient permissions")
        return next(request)

// Cache permissions per user (invalidate on role change)
function get_user_permissions(user_id) -> set[string]:
    cached = cache.get("permissions:" + user_id)
    if cached:
        return cached
    permissions = db.query(
        "SELECT DISTINCT p.name FROM permissions p
         JOIN role_permissions rp ON p.id = rp.permission_id
         JOIN user_roles ur ON rp.role_id = ur.role_id
         WHERE ur.user_id = ?", user_id
    )
    result = set([p.name for p in permissions])
    cache.set("permissions:" + user_id, result, ttl=300)
    return result
```

---

## API Key Management

```
// API key format: prefix + random bytes
// Example: sk_live_a1b2c3d4e5f6g7h8i9j0...
// Prefix helps identify key type and environment

function generate_api_key(key_type, environment):
    prefix = key_type + "_" + environment + "_"   // e.g., "sk_live_"
    random_part = base64url_encode(random_bytes(32))
    full_key = prefix + random_part

    // Store HASH of key, not the key itself
    key_hash = sha256(full_key)

    db.insert(api_keys, {
        key_hash: key_hash,
        key_prefix: full_key[0:12],   // store prefix for identification
        name: "Production API Key",
        scopes: ["read", "write"],
        created_by: current_user.id,
        expires_at: now() + 365 days,  // optional expiration
        rate_limit: 1000,              // requests per minute
    })

    // Return full key ONCE -- it cannot be retrieved again
    return full_key

function validate_api_key(key_string):
    key_hash = sha256(key_string)
    record = db.query("SELECT * FROM api_keys WHERE key_hash = ?", key_hash)
    if not record:
        return null
    if record.expires_at and record.expires_at < now():
        return null
    if record.revoked:
        return null
    // Update last_used_at for monitoring
    db.execute("UPDATE api_keys SET last_used_at = ? WHERE key_hash = ?", now(), key_hash)
    return record

// Security rules:
// - Always hash keys before storing (like passwords)
// - Support key rotation: allow multiple active keys per client
// - Log all key usage for audit
// - Alert on unusual usage patterns (spike in requests, new IP ranges)
// - Provide a revocation endpoint for compromised keys
```
