# API Design — Detailed Reference

Comprehensive patterns for REST API design, filtering, bulk operations, HATEOAS, authentication, and real-world conventions.

---

## Filtering and Searching

### Simple Filtering

Use query parameters for field-level filtering:

```
GET /products?category=electronics&inStock=true&minPrice=100&maxPrice=500
```

### Complex Filtering

For APIs that need rich query capabilities, use a filter parameter with a structured format:

```
// Option 1: Field-based parameters
GET /users?status=active&role=admin&createdAfter=2025-01-01

// Option 2: Filter object (for complex conditions)
GET /users?filter[status]=active&filter[role]=admin&filter[created_at][gte]=2025-01-01

// Option 3: Search endpoint for full-text search
GET /products/search?q=wireless+headphones&category=electronics
```

### Sorting

```
// Single field
GET /users?sort=created_at        // ascending (default)
GET /users?sort=-created_at       // descending (prefix with -)

// Multiple fields
GET /users?sort=-created_at,name  // newest first, then alphabetical
```

### Field Selection (Sparse Fieldsets)

Allow clients to request only the fields they need:

```
GET /users?fields=id,name,email
// Response includes only the requested fields
```

This reduces payload size and improves performance, especially for mobile clients.

---

## Pagination — Implementation Details

### Offset-Based

```
GET /users?page=3&pageSize=20

Response:
{
    "data": [...],
    "pagination": {
        "page": 3,
        "pageSize": 20,
        "total": 1547,
        "totalPages": 78
    }
}
```

**Implementation note:** Offset pagination uses `OFFSET` in SQL, which scans and discards rows. For page 100 with pageSize 20, the database reads 2000 rows and discards 1980. This degrades on large tables.

### Cursor-Based

```
GET /users?limit=20&after=eyJpZCI6MTIzLCJjcmVhdGVkX2F0IjoiMjAyNS0wMS0xNSJ9

Response:
{
    "data": [...],
    "pagination": {
        "hasNext": true,
        "hasPrev": true,
        "startCursor": "eyJpZCI6MTI0fQ",
        "endCursor": "eyJpZCI6MTQzfQ"
    }
}
```

**Cursor contents:** Encode the sort key(s) into an opaque, base64-encoded cursor. The server decodes it to construct a `WHERE` clause:

```
// Cursor decoded: { "id": 123, "created_at": "2025-01-15" }
// SQL: WHERE (created_at, id) > ('2025-01-15', 123) ORDER BY created_at, id LIMIT 20
```

This uses an index scan (no offset), so performance is consistent regardless of page number.

---

## Bulk Operations

When clients need to create, update, or delete multiple resources in one request:

```
// Bulk create
POST /users/bulk
{
    "items": [
        { "name": "Alice", "email": "alice@example.com" },
        { "name": "Bob", "email": "bob@example.com" }
    ]
}

Response (207 Multi-Status):
{
    "results": [
        { "status": 201, "data": { "id": "u1", "name": "Alice" } },
        { "status": 409, "error": { "code": "CONFLICT", "message": "Email already exists" } }
    ]
}
```

**Conventions:**
- Return 207 Multi-Status when results are mixed (some succeed, some fail).
- Each item in the response corresponds to the same index in the request.
- Do not silently skip failures. Report the status of every item.

---

## Idempotency — Implementation Details

### Server-Side Flow

```
function handleRequest(request):
    key = request.headers["Idempotency-Key"]

    if not key:
        return processNormally(request)

    // Check idempotency store
    existing = idempotencyStore.get(key)

    if existing:
        // Same key already processed
        if existing.requestHash != hash(request.body):
            return error(422, "Idempotency key reused with different request body")
        return existing.response  // Return stored response

    // Process and store
    response = processNormally(request)
    idempotencyStore.set(key, {
        requestHash: hash(request.body),
        response: response,
        expiresAt: now() + 24_HOURS
    })
    return response
```

### Idempotency Store Options

| Store | Pros | Cons |
|-------|------|------|
| In-memory (e.g., LRU cache) | Fast, simple | Lost on restart, not shared across instances |
| Redis | Fast, shared, built-in TTL | Extra dependency |
| Database table | Durable, transactional | Slower, needs cleanup job |

For most applications, Redis with TTL is the pragmatic choice.

---

## Authentication Patterns

### Token-Based (JWT)

```
// Client sends token in Authorization header
GET /users/me
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

// Server validates token, extracts claims
// No session state needed on server
```

**JWT Best Practices:**
- Use short-lived access tokens (5-15 minutes)
- Use long-lived refresh tokens (days/weeks) stored securely
- Sign with RS256 (asymmetric) for microservices, HS256 (symmetric) for monoliths
- Include only necessary claims (user ID, roles) — not sensitive data

### API Keys

```
// Header-based (preferred)
GET /data
X-API-Key: sk_live_abc123

// Query parameter (for webhooks/callbacks where headers are not controllable)
GET /webhook?apiKey=sk_live_abc123
```

**API Key Best Practices:**
- Prefix keys with environment (`sk_live_`, `sk_test_`)
- Hash keys in storage (never store plaintext)
- Support key rotation (multiple active keys per client)
- Scope keys to specific permissions

---

## HATEOAS (Hypermedia)

Responses include links to related actions and resources:

```
GET /orders/456
{
    "id": "456",
    "status": "confirmed",
    "total": 150.00,
    "links": {
        "self":    { "href": "/orders/456", "method": "GET" },
        "cancel":  { "href": "/orders/456/cancel", "method": "POST" },
        "ship":    { "href": "/orders/456/ship", "method": "POST" },
        "items":   { "href": "/orders/456/items", "method": "GET" },
        "customer": { "href": "/customers/789", "method": "GET" }
    }
}
```

**When to use:** Public APIs where discoverability matters. Internal APIs usually skip HATEOAS because clients are tightly coupled anyway.

---

## Webhook Design

When your API needs to notify external systems of events:

```
// Webhook registration
POST /webhooks
{
    "url": "https://client.example.com/hooks/orders",
    "events": ["order.placed", "order.shipped"],
    "secret": "whsec_abc123"
}

// Webhook delivery
POST https://client.example.com/hooks/orders
Content-Type: application/json
X-Webhook-Signature: sha256=abc123...
X-Webhook-Id: evt-789
X-Webhook-Timestamp: 1706140800

{
    "id": "evt-789",
    "type": "order.placed",
    "timestamp": "2025-01-25T10:00:00Z",
    "data": {
        "orderId": "456",
        "total": 150.00
    }
}
```

**Webhook Best Practices:**
- Sign payloads with HMAC (using the shared secret) so receivers can verify authenticity
- Include a unique event ID for deduplication
- Retry with exponential backoff on failure (5xx or timeout)
- Allow receivers to respond with 200-299 to acknowledge; anything else triggers retry
- Provide a way to replay missed events

---

## Content Negotiation

```
// Client requests specific format
GET /reports/monthly
Accept: application/json           // JSON response
Accept: text/csv                   // CSV response
Accept: application/pdf            // PDF response

// Server responds with appropriate format
Content-Type: application/json

// If server cannot produce requested format
HTTP/1.1 406 Not Acceptable
```

---

## Deprecation Convention

When retiring an endpoint or field:

```
// Response headers signal deprecation
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Mar 2026 00:00:00 GMT
Link: </v2/users>; rel="successor-version"

// Response body can include deprecation notices for fields
{
    "id": "123",
    "name": "Alice",
    "username": "alice",  // deprecated, use "name" instead
}
```

**Deprecation Process:**
1. Announce deprecation with timeline (minimum 3-6 months for public APIs)
2. Add `Deprecation` and `Sunset` headers
3. Log usage of deprecated endpoints to track migration progress
4. After sunset date, return 410 Gone with migration instructions

---

## API Design Checklist

Before publishing an API endpoint:

- [ ] Resource naming uses nouns (not verbs), plural for collections
- [ ] HTTP methods match semantics (GET reads, POST creates, etc.)
- [ ] Status codes are appropriate (not 200 for everything)
- [ ] Error responses use consistent envelope with machine-readable codes
- [ ] Pagination is implemented for list endpoints
- [ ] Input validation returns specific field-level errors
- [ ] Authentication and authorization are enforced
- [ ] Rate limiting is configured with appropriate headers
- [ ] Sensitive data is not exposed in URLs (use headers or body)
- [ ] POST endpoints that create resources support idempotency keys
- [ ] API is documented (OpenAPI spec, examples, error catalog)
