# API Protocols -- Full Reference

Complete patterns for API protocol implementation. All examples use pseudocode.

---

## gRPC -- Streaming Patterns

### Server Streaming (one request, many responses)

```
// Server: yield each response as it becomes available
function ListOrders(request, context):
    cursor = null
    loop:
        batch, cursor = order_repo.paginate(
            page_size=min(request.page_size, 200),
            cursor=cursor
        )
        for order in batch:
            yield OrderResponse(
                order_id: order.id,
                status: order.status,
                total: order.total
            )
        if cursor is null:
            break

// Client: iterate over response stream
function fetch_all_orders():
    results = []
    for response in stub.ListOrders(ListOrdersRequest(page_size=100), timeout=60s):
        results.append(response)
    return results
```

### Client Streaming (many requests, one response)

```
// Server: consume all incoming messages, return aggregate
function CreateOrders(request_stream, context):
    order_ids = []
    for request in request_stream:
        order = order_service.create(request.item, request.quantity)
        order_ids.append(order.id)
    return CreateOrdersResponse(
        order_ids=order_ids,
        created_count=length(order_ids)
    )

// Client: send multiple requests, receive single response
function bulk_create_orders(orders_data):
    function generate_requests():
        for data in orders_data:
            yield CreateOrderRequest(item=data.item, quantity=data.quantity)
    response = stub.CreateOrders(generate_requests(), timeout=120s)
    return response
```

### Bidirectional Streaming

```
// Server: process each incoming message and respond
function SyncOrders(request_stream, context):
    for request in request_stream:
        result = order_sync_service.process(request)
        yield SyncResponse(
            order_id=request.order_id,
            status=result.status,
            message=result.message
        )

// Client: send and receive concurrently
function sync_orders(pending_orders):
    function send_requests():
        for order in pending_orders:
            yield SyncRequest(order_id=order.id, action="upsert")
            throttle(10ms)

    for response in stub.SyncOrders(send_requests(), timeout=300s):
        handle_sync_response(response)
```

---

## gRPC -- Interceptors

### Server-Side Logging Interceptor

```
class LoggingInterceptor:
    function intercept(request, context, handler):
        method = context.method_name
        start = monotonic_time()
        try:
            response = handler(request, context)
            log.info("gRPC success",
                method=method,
                latency_ms=elapsed_ms(start))
            return response
        catch error:
            log.error("gRPC error",
                method=method,
                error=error.message,
                latency_ms=elapsed_ms(start))
            rethrow
```

### Server-Side Auth Interceptor

```
class AuthInterceptor:
    public_methods = ["/grpc.health.v1.Health/Check"]

    function intercept(request, context, handler):
        if context.method_name in public_methods:
            return handler(request, context)

        metadata = context.get_metadata()
        token = metadata.get("authorization", "").remove_prefix("Bearer ")

        if not token or not verify_token(token):
            context.abort(UNAUTHENTICATED, "Invalid token")

        return handler(request, context)
```

### Client-Side Retry Interceptor

```
class RetryInterceptor:
    function intercept(request, call_details, continuation):
        for attempt in 0..2:
            try:
                return continuation(request, call_details)
            catch RpcError as error:
                if error.code not in [UNAVAILABLE, DEADLINE_EXCEEDED]:
                    rethrow
                if attempt == 2:
                    rethrow
                sleep(2^attempt * 100ms)
```

---

## gRPC -- Deadline Propagation

```
// Forward remaining deadline from incoming context to outgoing calls
function GetOrderWithUser(request, context):
    remaining = context.time_remaining()
    if remaining is null or remaining <= 0.5s:
        context.abort(DEADLINE_EXCEEDED, "Insufficient time remaining")

    // Leave buffer for local processing
    downstream_timeout = min(remaining - 0.1s, 5s)

    user = user_stub.GetUser(
        GetUserRequest(user_id=request.user_id),
        timeout=downstream_timeout
    )
    // ... build response ...
```

---

## gRPC -- Health Checking

```
// Standard health checking protocol (grpc.health.v1)
// Every gRPC service should implement this

health_servicer = HealthServicer()

// Register per-service health status
health_servicer.set("", SERVING)                        // overall server
health_servicer.set("orders.v1.OrderService", SERVING)  // specific service
health_servicer.set("payments.v1.PaymentService", NOT_SERVING)  // degraded

// Client health check
health_stub = HealthStub(channel)
response = health_stub.Check(
    HealthCheckRequest(service="orders.v1.OrderService"),
    timeout=2s
)
is_healthy = response.status == SERVING

// Watch for health changes (streaming)
for status in health_stub.Watch(HealthCheckRequest(service="")):
    log.info("Health status changed", status=status)
```

---

## GraphQL -- Schema Design Patterns

### Relay-style pagination (cursor-based)

```
type OrderConnection {
    edges: [OrderEdge!]!
    pageInfo: PageInfo!
    totalCount: Int!
}

type OrderEdge {
    node: Order!
    cursor: String!
}

type PageInfo {
    hasNextPage: Boolean!
    hasPreviousPage: Boolean!
    startCursor: String
    endCursor: String
}

// Query: first N items after cursor
query {
    orders(first: 10, after: "cursor_abc") {
        edges {
            node { id, status, total }
            cursor
        }
        pageInfo { hasNextPage, endCursor }
        totalCount
    }
}
```

### Error handling in mutations

```
// Use union types or payload types for structured errors
type CreateOrderPayload {
    order: Order
    errors: [UserError!]!
}

type UserError {
    field: String          // which input field caused the error
    message: String!       // human-readable message
    code: ErrorCode!       // machine-readable code
}

enum ErrorCode {
    INVALID_INPUT
    NOT_FOUND
    INSUFFICIENT_STOCK
    PAYMENT_DECLINED
    RATE_LIMITED
}

// Resolver returns errors in payload, not as GraphQL errors
// GraphQL errors are for unexpected/system errors only
```

### DataLoader integration

```
// Create DataLoader instances per request (not globally)
function create_request_context():
    return {
        order_items_loader: DataLoader(batch_load_order_items),
        product_loader: DataLoader(batch_load_products),
        user_loader: DataLoader(batch_load_users),
    }

// Resolver uses loader instead of direct DB query
function resolve_order_items(order, args, context):
    return context.order_items_loader.load(order.id)

function resolve_product(order_item, args, context):
    return context.product_loader.load(order_item.product_id)

// Batch load function: receives list of keys, returns map of results
function batch_load_order_items(order_ids):
    items = db.query("SELECT * FROM order_items WHERE order_id IN (?)", order_ids)
    return group_by(items, "order_id")
```

---

## WebSocket -- Implementation Pattern

### Connection management

```
class ConnectionManager:
    active_connections: map[user_id -> set[WebSocket]]
    rooms: map[room_id -> set[user_id]]

    function connect(websocket, user_id):
        accept(websocket)
        active_connections[user_id].add(websocket)

    function disconnect(websocket, user_id):
        active_connections[user_id].remove(websocket)
        if active_connections[user_id] is empty:
            delete active_connections[user_id]

    function send_to_user(user_id, message):
        for ws in active_connections.get(user_id, []):
            try:
                ws.send(serialize(message))
            catch ConnectionClosed:
                disconnect(ws, user_id)

    function broadcast_to_room(room_id, message, exclude=null):
        for user_id in rooms.get(room_id, []):
            if user_id != exclude:
                send_to_user(user_id, message)
```

### Message protocol

```
// Use a consistent message envelope
message_envelope = {
    type: string,         // "chat", "presence", "notification", "error"
    payload: object,      // type-specific data
    timestamp: iso8601,   // server timestamp
    id: string,           // message ID for deduplication/ack
}

// Client -> Server messages:
{ type: "subscribe",   payload: { room: "room-123" } }
{ type: "unsubscribe", payload: { room: "room-123" } }
{ type: "chat",        payload: { room: "room-123", text: "hello" } }
{ type: "ping" }

// Server -> Client messages:
{ type: "chat",         payload: { room: "room-123", from: "user-1", text: "hello" } }
{ type: "presence",     payload: { room: "room-123", user: "user-1", status: "online" } }
{ type: "notification", payload: { title: "New order", body: "Order #123 received" } }
{ type: "pong" }
{ type: "error",        payload: { code: "UNAUTHORIZED", message: "Token expired" } }
```

---

## SSE -- Implementation Pattern

```
// Server endpoint
function sse_endpoint(request):
    // Authenticate (token in query param or header)
    user = authenticate(request)
    if not user:
        return error_response(401)

    // Set SSE headers
    response.headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",   // disable nginx buffering
    }

    // Get last event ID for resumption
    last_id = request.headers.get("Last-Event-ID")

    // Stream events
    function generate():
        // Send missed events if resuming
        if last_id:
            for event in get_events_since(last_id):
                yield format_sse(event)

        // Stream new events
        subscription = event_bus.subscribe(user.id)
        try:
            for event in subscription:
                yield format_sse(event)
        finally:
            subscription.unsubscribe()

    return streaming_response(generate())

function format_sse(event):
    lines = []
    if event.type:
        lines.append("event: " + event.type)
    lines.append("data: " + serialize_json(event.payload))
    lines.append("id: " + event.id)
    lines.append("")   // blank line terminates event
    return join(lines, "\n") + "\n"
```

---

## REST -- Resource Design Conventions

```
// URL structure: /<resource>/<id>/<sub-resource>
GET    /orders              // list orders (with pagination, filtering)
POST   /orders              // create order
GET    /orders/{id}         // get single order
PUT    /orders/{id}         // full update
PATCH  /orders/{id}         // partial update
DELETE /orders/{id}         // delete order
GET    /orders/{id}/items   // list items for order

// Pagination: cursor-based (preferred) or offset-based
GET /orders?cursor=abc&limit=20
GET /orders?offset=40&limit=20

// Filtering and sorting
GET /orders?status=pending&sort=-created_at&min_total=100

// Standard response envelope
{
    "data": [...],
    "meta": { "total": 142, "cursor": "next_abc" },
    "errors": []    // only populated on error responses
}

// HTTP status codes
// 200 OK: successful GET, PUT, PATCH, DELETE
// 201 Created: successful POST (include Location header)
// 204 No Content: successful DELETE with no body
// 400 Bad Request: validation error
// 401 Unauthorized: missing/invalid auth
// 403 Forbidden: authenticated but not authorized
// 404 Not Found: resource does not exist
// 409 Conflict: duplicate or state conflict
// 422 Unprocessable Entity: semantic validation error
// 429 Too Many Requests: rate limited (include Retry-After header)
```
