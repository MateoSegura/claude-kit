---
name: core-backend:api-protocols
description: "API protocol patterns for backend services: gRPC (protobuf, streaming modes, interceptors), GraphQL (schema design, resolvers, N+1 problem, subscriptions), REST conventions, WebSockets, Server-Sent Events -- when to use each protocol and their trade-offs. Load when choosing or implementing API protocols."
user-invocable: false
---

# API Protocols -- Quick Reference

## Additional resources

- [protocols-reference.md](protocols-reference.md) -- Full patterns: gRPC streaming, GraphQL schema design, WebSocket lifecycle, SSE implementation

---

## Protocol Decision Matrix

| Need | Protocol | Trade-off |
|------|----------|-----------|
| Standard CRUD API | REST (HTTP/JSON) | Simple, widely supported; no schema enforcement |
| High-performance internal RPC | gRPC (HTTP/2 + Protobuf) | Binary protocol, fast; requires codegen |
| Flexible client queries | GraphQL | Single endpoint; complexity in server, N+1 risk |
| Real-time bidirectional | WebSockets | Persistent connection; harder to scale |
| Real-time server push | Server-Sent Events (SSE) | Simple, HTTP-based; server-to-client only |
| File upload/download | REST or tus protocol | Multipart or resumable; avoid in gRPC/GraphQL |
| Schema-first contract | gRPC (protobuf) or GraphQL | Strong typing; schema evolution rules differ |

---

## gRPC Overview

### Communication modes

| Mode | Description | Use case |
|------|-------------|----------|
| Unary | One request, one response | Standard RPC calls |
| Server streaming | One request, stream of responses | Paginated results, live updates |
| Client streaming | Stream of requests, one response | Bulk upload, aggregation |
| Bidirectional | Stream both directions | Chat, real-time sync |

### Protobuf conventions

```
syntax = "proto3";
package orders.v1;    // version in package name for evolution

service OrderService {
    rpc GetOrder(GetOrderRequest) returns (OrderResponse);                    // Unary
    rpc ListOrders(ListOrdersRequest) returns (stream OrderResponse);        // Server stream
    rpc CreateOrders(stream CreateOrderRequest) returns (CreateOrdersResp);  // Client stream
    rpc SyncOrders(stream SyncRequest) returns (stream SyncResponse);        // Bidi stream
}

// Field numbering rules:
//   1-15: one byte encoding (use for frequently accessed fields)
//   16-2047: two byte encoding
//   Never reuse field numbers -- use 'reserved' for removed fields

// Enums: always include UNSPECIFIED = 0 as default
enum OrderStatus {
    ORDER_STATUS_UNSPECIFIED = 0;
    ORDER_STATUS_PENDING = 1;
    ORDER_STATUS_CONFIRMED = 2;
    ORDER_STATUS_SHIPPED = 3;
}
```

### gRPC status codes

| gRPC Code | HTTP Equivalent | When to use |
|-----------|----------------|-------------|
| OK | 200 | Success |
| INVALID_ARGUMENT | 400 | Bad request data |
| NOT_FOUND | 404 | Resource not found |
| ALREADY_EXISTS | 409 | Duplicate resource |
| PERMISSION_DENIED | 403 | Authorized but not permitted |
| UNAUTHENTICATED | 401 | Missing or invalid credentials |
| RESOURCE_EXHAUSTED | 429 | Rate limit exceeded |
| UNAVAILABLE | 503 | Temporary; client should retry |
| DEADLINE_EXCEEDED | 504 | Timeout |
| INTERNAL | 500 | Unexpected server error |

### Interceptors (middleware for gRPC)

Server-side: logging, authentication, rate limiting, metrics
Client-side: retry, metadata injection, deadline propagation

---

## GraphQL Overview

### Schema design principles

```
type Query {
    order(id: ID!): Order
    orders(filter: OrderFilter, first: Int, after: String): OrderConnection!
}

type Mutation {
    createOrder(input: CreateOrderInput!): CreateOrderPayload!
    cancelOrder(id: ID!): CancelOrderPayload!
}

type Subscription {
    orderStatusChanged(orderId: ID!): Order!
}

// Use input types for mutations
input CreateOrderInput {
    items: [OrderItemInput!]!
    shippingAddress: AddressInput!
}

// Use payload types for mutation responses (allows error fields)
type CreateOrderPayload {
    order: Order
    errors: [UserError!]!
}
```

### N+1 problem in GraphQL

```
// Problem: resolving nested fields triggers N+1 queries
query {
    orders(first: 10) {
        id
        items {        // resolver fetches items per order = N queries
            product {  // resolver fetches product per item = N*M queries
                name
            }
        }
    }
}

// Solution: DataLoader pattern
// Batch and cache lookups within a single request
// See database-patterns skill for DataLoader implementation
```

### When NOT to use GraphQL

- Simple CRUD with predictable access patterns (REST is simpler)
- File uploads (use REST multipart)
- Real-time with complex auth per field (WebSocket subscriptions add complexity)
- Internal microservice communication (gRPC is more efficient)

---

## WebSockets

### Connection lifecycle

1. Client sends HTTP upgrade request (with `Upgrade: websocket` header)
2. Server responds with 101 Switching Protocols
3. Bidirectional message exchange (text or binary frames)
4. Either side sends close frame to terminate

### Best practices

- Implement heartbeat/ping-pong to detect dead connections
- Use message framing with type field: `{"type": "chat", "payload": {...}}`
- Handle reconnection on client side with exponential backoff
- Authenticate during the upgrade request (via token in query param or first message)
- Set max message size to prevent memory exhaustion

---

## Server-Sent Events (SSE)

```
// Server sends events over a long-lived HTTP response
// Content-Type: text/event-stream

// Event format:
event: order_status
data: {"order_id": "123", "status": "shipped"}
id: 42
retry: 5000

// Fields:
//   event: event type (optional, defaults to "message")
//   data: payload (can be multi-line, each line prefixed with "data: ")
//   id: event ID (client sends Last-Event-ID on reconnect)
//   retry: reconnection delay in milliseconds
```

### When to use SSE vs WebSockets

| SSE | WebSockets |
|-----|------------|
| Server-to-client only | Bidirectional |
| Auto-reconnect built in | Must implement reconnect |
| Works with HTTP/2 multiplexing | Requires separate TCP connection |
| Simple to implement | More complex protocol |
| Use for: notifications, feeds, dashboards | Use for: chat, gaming, collaborative editing |
