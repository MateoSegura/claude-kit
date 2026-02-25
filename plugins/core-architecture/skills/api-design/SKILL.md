---
name: core-architecture:api-design
description: "API design principles — REST conventions, GraphQL vs REST vs gRPC tradeoffs, versioning strategies, pagination patterns, error responses, idempotency, and rate limiting."
user-invocable: false
---

# API Design

Principles and conventions for designing APIs that are consistent, predictable, and easy to consume. Language-agnostic.

## Additional resources

- [api-reference.md](api-reference.md) — Detailed patterns: pagination, filtering, error responses, versioning, idempotency, rate limiting, webhooks, authentication

---

## Protocol Comparison

| Aspect | REST | GraphQL | gRPC |
|--------|------|---------|------|
| Transport | HTTP/1.1 or HTTP/2 | HTTP (POST) | HTTP/2 |
| Data format | JSON | JSON | Protocol Buffers |
| Schema | OpenAPI (optional) | SDL (required) | .proto (required) |
| Strengths | Simple, cacheable | Flexible queries | High performance, streaming |
| Weaknesses | Over/under-fetching | Caching harder, N+1 | Not browser-native |
| Best for | Public APIs, CRUD | Mobile, dashboards | Service-to-service |

**Decision:** Public API -> REST. Mobile with varied views -> GraphQL. Internal microservices -> gRPC.

---

## REST Conventions

**Resources are nouns, plural.** `GET /users`, `POST /orders`, `DELETE /users/123`.

**HTTP methods match semantics:**

| Method | Purpose | Idempotent | Body |
|--------|---------|------------|------|
| GET | Read | Yes | No |
| POST | Create | No | Yes |
| PUT | Replace entirely | Yes | Yes |
| PATCH | Partial update | No* | Yes |
| DELETE | Remove | Yes | No |

**Status codes:** 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable, 429 Rate Limited, 500 Internal Error.

**Nested vs flat:** If the child cannot exist without the parent, nest it (`/users/123/orders`). If it has its own lifecycle, keep it flat (`/orders?userId=123`).

---

## Error Response Convention

Consistent envelope across all endpoints:

```
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "details": [
            { "field": "email", "message": "Must be a valid email" }
        ],
        "requestId": "req-abc-123"
    }
}
```

Machine-readable `code` for client logic, human-readable `message` for display, `requestId` for support correlation.

---

## Pagination

| Strategy | Pros | Cons | Best For |
|----------|------|------|----------|
| **Offset** (`?page=3&pageSize=20`) | Simple, jump-to-page | Slow on large tables | Admin panels, small datasets |
| **Cursor** (`?after=eyJ...&limit=20`) | Consistent, performant | No jump-to-page | Feeds, timelines, large datasets |
| **Keyset** | Performant, deterministic | Needs sortable unique column | Sorted lists, event streams |

Always include pagination metadata: `total`, `hasNext`, `nextCursor` (or `totalPages`).

---

## Versioning

**Recommended:** URL path versioning (`/v1/users`, `/v2/users`) for public APIs. Bump only for breaking changes.

| Breaking | Non-Breaking |
|----------|-------------|
| Removing/renaming a field | Adding optional field |
| Changing a field's type | Adding new endpoint |
| Removing an endpoint | Adding query parameter |

---

## Idempotency

POST endpoints that create resources should accept an `Idempotency-Key` header. Server checks if the key was already processed; if yes, returns the stored response instead of duplicating the operation.

```
POST /payments
Idempotency-Key: pay-abc-123
```

GET, PUT, DELETE are naturally idempotent. Keys should expire after a reasonable window (24 hours).

---

## Rate Limiting

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1706140800
```

Return 429 with `Retry-After` header when exceeded. Strategies: fixed window, sliding window, token bucket. Apply per-user or per-API-key.

See [api-reference.md](api-reference.md) for full details on filtering, bulk operations, webhooks, HATEOAS, and authentication patterns.
