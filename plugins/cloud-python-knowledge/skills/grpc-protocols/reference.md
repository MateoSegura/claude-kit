# gRPC & Protocols — Full Reference

Complete patterns for Python gRPC services: streaming, interceptors, TLS, health checking, reflection, and Protobuf conventions.

---

## All Four Streaming Modes

### Unary (request-response)

```python
# Server
async def GetUser(
    self,
    request: GetUserRequest,
    context: grpc.aio.ServicerContext,
) -> UserResponse:
    user = await user_repo.get(request.user_id)
    if not user:
        await context.abort(grpc.StatusCode.NOT_FOUND, "User not found")
    return UserResponse(user_id=str(user.id), email=user.email, name=user.name)

# Client
response = await stub.GetUser(GetUserRequest(user_id="abc"), timeout=5.0)
```

### Server Streaming (one request → many responses)

```python
# Server — yield each response
async def ListUsers(
    self,
    request: ListUsersRequest,
    context: grpc.aio.ServicerContext,
) -> AsyncIterator[UserResponse]:
    cursor = None
    while True:
        batch, cursor = await user_repo.paginate(
            page_size=min(request.page_size, 200),
            cursor=cursor,
        )
        for user in batch:
            yield UserResponse(user_id=str(user.id), email=user.email)
        if not cursor:
            break

# Client — async for
async def fetch_all_users():
    results = []
    async for user in stub.ListUsers(ListUsersRequest(page_size=100), timeout=60.0):
        results.append(user)
    return results
```

### Client Streaming (many requests → one response)

```python
# Server — iterate request stream
async def CreateUsers(
    self,
    request_iterator: AsyncIterator[CreateUserRequest],
    context: grpc.aio.ServicerContext,
) -> CreateUsersResponse:
    user_ids = []
    async for request in request_iterator:
        user = await user_service.create(request.email, request.name)
        user_ids.append(str(user.id))
    return CreateUsersResponse(user_ids=user_ids, created_count=len(user_ids))

# Client — send requests then read single response
async def bulk_create():
    async def generate_requests():
        for user_data in users_to_create:
            yield CreateUserRequest(email=user_data["email"], name=user_data["name"])

    response = await stub.CreateUsers(generate_requests(), timeout=120.0)
    print(f"Created {response.created_count} users")
```

### Bidirectional Streaming

```python
# Server — read and write concurrently
async def SyncUsers(
    self,
    request_iterator: AsyncIterator[SyncUserRequest],
    context: grpc.aio.ServicerContext,
) -> AsyncIterator[SyncUserResponse]:
    async for request in request_iterator:
        # Process each incoming message and yield a response
        result = await user_sync_service.process(request)
        yield SyncUserResponse(
            user_id=request.user_id,
            status=result.status,
            message=result.message,
        )

# Client
async def sync_users():
    async def send_requests():
        for user in pending_users:
            yield SyncUserRequest(user_id=user.id, action="upsert", data=user.to_proto())
            await asyncio.sleep(0.01)   # throttle

    async for response in stub.SyncUsers(send_requests(), timeout=300.0):
        handle_sync_response(response)
```

---

## Interceptors

### Server-Side Interceptor (Logging + Auth)

```python
import grpc
from grpc import aio
from typing import Callable, Any

class LoggingInterceptor(aio.ServerInterceptor):
    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        handler = await continuation(handler_call_details)
        if handler is None:
            return handler

        async def wrapper(request, context):
            method = handler_call_details.method
            start = time.monotonic()
            try:
                response = await handler.unary_unary(request, context)
                logger.info("gRPC success", method=method, latency_ms=round((time.monotonic()-start)*1000, 1))
                return response
            except Exception as e:
                logger.error("gRPC error", method=method, error=str(e))
                raise

        return handler._replace(unary_unary=wrapper)

class AuthInterceptor(aio.ServerInterceptor):
    PUBLIC_METHODS = {"/grpc.health.v1.Health/Check"}

    async def intercept_service(self, continuation, handler_call_details):
        if handler_call_details.method in self.PUBLIC_METHODS:
            return await continuation(handler_call_details)

        metadata = dict(handler_call_details.invocation_metadata or [])
        token = metadata.get("authorization", "").removeprefix("Bearer ")

        if not token or not await verify_token(token):
            async def deny(request, context):
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid token")
            return grpc.unary_unary_rpc_method_handler(deny)

        return await continuation(handler_call_details)

# Register on server
server = aio.server(interceptors=[LoggingInterceptor(), AuthInterceptor()])
```

### Client-Side Interceptor (Retry + Metadata Injection)

```python
class RetryInterceptor(aio.UnaryUnaryClientInterceptor):
    async def intercept_unary_unary(self, continuation, client_call_details, request):
        for attempt in range(3):
            call = await continuation(client_call_details, request)
            try:
                response = await call
                return response
            except grpc.aio.AioRpcError as e:
                if e.code() not in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
                    raise
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt * 0.1)

class MetadataInterceptor(aio.UnaryUnaryClientInterceptor):
    def __init__(self, service_name: str):
        self._service_name = service_name

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        new_metadata = list(client_call_details.metadata or []) + [
            ("x-source-service", self._service_name),
            ("x-request-id", str(uuid.uuid4())),
        ]
        new_details = client_call_details._replace(metadata=new_metadata)
        return await continuation(new_details, request)
```

---

## Deadlines and Timeouts

```python
# Deadline propagation — pass deadline from incoming context to outgoing call
async def GetOrderWithUser(self, request, context: grpc.aio.ServicerContext):
    # Forward the remaining deadline to the downstream call
    remaining = context.time_remaining()
    if remaining is None or remaining <= 0.5:
        await context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, "Insufficient time")

    user = await user_stub.GetUser(
        GetUserRequest(user_id=request.user_id),
        timeout=min(remaining - 0.1, 5.0),   # leave 100ms buffer
    )
    ...

# Client: set absolute deadline
import grpc
deadline = grpc.aio.Deadline.from_relative_time(10.0)   # 10 seconds from now
response = await stub.GetUser(request, timeout=10.0)
```

---

## Metadata

```python
# Server: read metadata from client
async def GetUser(self, request, context: grpc.aio.ServicerContext):
    metadata = dict(context.invocation_metadata())
    request_id = metadata.get("x-request-id", "unknown")
    structlog.contextvars.bind_contextvars(request_id=request_id)

    # Send trailing metadata back to client
    await context.send_initial_metadata([("x-processed-by", "user-svc-v1")])
    # ...
    await context.set_trailing_metadata([("x-duration-ms", "42")])
    return response

# Client: send metadata, read trailing metadata
call = stub.GetUser(
    request,
    metadata=[("authorization", f"Bearer {token}"), ("x-request-id", request_id)],
    timeout=5.0,
)
response = await call
trailing = await call.trailing_metadata()
```

---

## Health Checking Protocol

```python
# Server — grpc-health-checking package
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

health_servicer = health.HealthServicer(experimental_non_blocking=True)
health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

# Mark services as serving/not serving
health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)                  # overall
health_servicer.set("user.v1.UserService", health_pb2.HealthCheckResponse.SERVING)
health_servicer.set("order.v1.OrderService", health_pb2.HealthCheckResponse.NOT_SERVING)

# Client — check health
from grpc_health.v1 import health_pb2, health_pb2_grpc

health_stub = health_pb2_grpc.HealthStub(channel)
resp = await health_stub.Check(
    health_pb2.HealthCheckRequest(service="user.v1.UserService"),
    timeout=2.0,
)
print(resp.status == health_pb2.HealthCheckResponse.SERVING)  # True/False

# Watch (streaming health updates)
async for status in health_stub.Watch(health_pb2.HealthCheckRequest(service="")):
    print(status.status)
```

---

## Server Reflection

```python
# Enable reflection for grpcurl and testing tools
from grpc_reflection.v1alpha import reflection, reflection_pb2

SERVICE_NAMES = (
    user_service_pb2.DESCRIPTOR.services_by_name["UserService"].full_name,
    reflection.SERVICE_NAME,
)
reflection.enable_server_reflection(SERVICE_NAMES, server)

# Test with grpcurl
# grpcurl -plaintext localhost:50051 list
# grpcurl -plaintext -d '{"user_id":"123"}' localhost:50051 user.v1.UserService/GetUser
```

---

## TLS Configuration

```python
# Server with TLS
with open("server.key", "rb") as f:
    private_key = f.read()
with open("server.crt", "rb") as f:
    certificate_chain = f.read()
with open("ca.crt", "rb") as f:
    root_certificates = f.read()

server_credentials = grpc.ssl_server_credentials(
    [(private_key, certificate_chain)],
    root_certificates=root_certificates,
    require_client_auth=True,    # mutual TLS
)
server.add_secure_port("[::]:50051", server_credentials)

# Client with TLS
channel_credentials = grpc.ssl_channel_credentials(
    root_certificates=root_certificates,
    private_key=client_key,
    certificate_chain=client_cert,
)
channel = aio.secure_channel("user-svc:50051", channel_credentials)
```

---

## Protobuf Best Practices

```protobuf
// Field numbering: stable, never reuse
// 1-15: one byte encoding (use for frequent fields)
// 16-2047: two byte encoding

// Versioning: use packages
package user.v1;  // bump to v2 for breaking changes

// Reserved: mark removed fields to prevent reuse
message UserResponse {
  reserved 5, 6;              // reserved field numbers
  reserved "old_field_name";  // reserved field names
}

// Well-known types for common fields
import "google/protobuf/timestamp.proto";
import "google/protobuf/duration.proto";
import "google/protobuf/struct.proto";    // arbitrary JSON
import "google/protobuf/any.proto";       // any message type
import "google/protobuf/wrappers.proto";  // nullable primitives

// Use StringValue for nullable strings (proto3 has no optional scalars pre-3.15)
import "google/protobuf/wrappers.proto";
google.protobuf.StringValue optional_field = 7;

// proto3 optional (preferred in protobuf 3.15+)
optional string optional_field = 7;

// Enums: always include UNSPECIFIED = 0
enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PENDING = 1;
  ORDER_STATUS_CONFIRMED = 2;
  ORDER_STATUS_SHIPPED = 3;
  ORDER_STATUS_DELIVERED = 4;
  ORDER_STATUS_CANCELLED = 5;
}
```

---

## gRPC Gateway (REST + gRPC from one service)

```protobuf
// Add HTTP annotations to proto
import "google/api/annotations.proto";

service UserService {
  rpc GetUser(GetUserRequest) returns (UserResponse) {
    option (google.api.http) = {
      get: "/v1/users/{user_id}"
    };
  }
  rpc CreateUser(CreateUserRequest) returns (UserResponse) {
    option (google.api.http) = {
      post: "/v1/users"
      body: "*"
    };
  }
}
```

```bash
# Generate gRPC gateway reverse proxy
protoc --grpc-gateway_out=. proto/user_service.proto
```
