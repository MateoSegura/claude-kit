---
name: cloud-python-knowledge:grpc-protocols
description: "gRPC and Protocol Buffers reference for Python: protobuf definitions, service stubs, all four streaming modes (unary, server-streaming, client-streaming, bidirectional), interceptors, error handling, deadlines, metadata, health checking protocol, and grpcio-tools code generation. Load when implementing or consuming gRPC services in Python."
user-invocable: false
---

# gRPC & Protocols — Quick Reference

Stack: `grpcio>=1.60`, `protobuf>=4.25`, `grpcio-tools`, `grpcio-health-checking`, `grpcio-reflection`.

## Additional resources

- [reference.md](reference.md) — Complete proto definitions, all streaming patterns, interceptors, error handling, deadlines, metadata, reflection, health checking

---

## Proto Definition Quick Reference

```protobuf
// proto/user_service.proto
syntax = "proto3";
package user.v1;
option python_package = "user.v1";

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

service UserService {
  rpc GetUser(GetUserRequest) returns (UserResponse);                         // Unary
  rpc ListUsers(ListUsersRequest) returns (stream UserResponse);             // Server streaming
  rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);   // Client streaming
  rpc SyncUsers(stream SyncUserRequest) returns (stream SyncUserResponse);   // Bidirectional
}

message GetUserRequest {
  string user_id = 1;
}

message UserResponse {
  string user_id = 1;
  string email = 2;
  string name = 3;
  google.protobuf.Timestamp created_at = 4;
}

message ListUsersRequest {
  int32 page_size = 1;   // max 200
  string page_token = 2;
}

message CreateUserRequest {
  string email = 1;
  string name = 2;
}

message CreateUsersResponse {
  repeated string user_ids = 1;
  int32 created_count = 2;
}
```

---

## Code Generation

```bash
# Install tools
pip install grpcio-tools==1.63.0 grpcio==1.63.0

# Generate Python stubs
python -m grpc_tools.protoc \
  --proto_path=proto/ \
  --python_out=src/generated/ \
  --grpc_python_out=src/generated/ \
  --pyi_out=src/generated/ \
  proto/user_service.proto

# With buf (modern alternative — preferred)
buf generate
```

**buf.yaml:**
```yaml
version: v2
plugins:
  - plugin: buf.build/protocolbuffers/python
    out: src/generated
  - plugin: buf.build/grpc/python
    out: src/generated
  - plugin: buf.build/protocolbuffers/pyi
    out: src/generated
```

---

## Server Quick Reference

```python
import grpc
from grpc import aio
from src.generated import user_service_pb2, user_service_pb2_grpc

class UserServiceImpl(user_service_pb2_grpc.UserServiceServicer):

    async def GetUser(self, request, context: grpc.aio.ServicerContext):
        user = await user_repo.get(request.user_id)
        if not user:
            await context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.user_id} not found")
        return user_service_pb2.UserResponse(
            user_id=str(user.id),
            email=user.email,
            name=user.name,
        )

    async def ListUsers(self, request, context: grpc.aio.ServicerContext):
        async for user in user_repo.iter_all(page_size=request.page_size):
            yield user_service_pb2.UserResponse(user_id=str(user.id), email=user.email, name=user.name)

async def serve():
    server = aio.server(options=[
        ("grpc.max_send_message_length", 10 * 1024 * 1024),   # 10 MB
        ("grpc.max_receive_message_length", 10 * 1024 * 1024),
        ("grpc.keepalive_time_ms", 30_000),
    ])
    user_service_pb2_grpc.add_UserServiceServicer_to_server(UserServiceImpl(), server)

    # Health checking
    from grpc_health.v1 import health, health_pb2_grpc
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set("user.v1.UserService", health_pb2.HealthCheckResponse.SERVING)

    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()

asyncio.run(serve())
```

---

## Client Quick Reference

```python
import grpc
from grpc import aio

channel = aio.insecure_channel(
    "user-svc:50051",
    options=[
        ("grpc.keepalive_time_ms", 30_000),
        ("grpc.keepalive_timeout_ms", 5_000),
    ],
)
stub = user_service_pb2_grpc.UserServiceStub(channel)

# Unary call with deadline
try:
    response = await stub.GetUser(
        user_service_pb2.GetUserRequest(user_id="123"),
        timeout=5.0,                         # seconds
        metadata=[("x-request-id", "abc")],
    )
except grpc.aio.AioRpcError as e:
    if e.code() == grpc.StatusCode.NOT_FOUND:
        ...    # handle not found
    elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
        ...    # handle timeout
    raise

# Server streaming
async for user in stub.ListUsers(
    user_service_pb2.ListUsersRequest(page_size=100),
    timeout=30.0,
):
    process(user)
```

---

## Status Codes Reference

| gRPC Code | HTTP Equivalent | When to Use |
|-----------|----------------|-------------|
| `OK` | 200 | Success |
| `INVALID_ARGUMENT` | 400 | Bad request data |
| `NOT_FOUND` | 404 | Resource not found |
| `ALREADY_EXISTS` | 409 | Duplicate resource |
| `PERMISSION_DENIED` | 403 | Authorized but not permitted |
| `UNAUTHENTICATED` | 401 | Missing or invalid credentials |
| `RESOURCE_EXHAUSTED` | 429 | Rate limit exceeded |
| `UNAVAILABLE` | 503 | Service temporarily unavailable (retry) |
| `DEADLINE_EXCEEDED` | 504 | Timeout (may or may not retry) |
| `INTERNAL` | 500 | Unexpected server error |
| `UNIMPLEMENTED` | 501 | Method not implemented |

---

## Error Handling Pattern

```python
# Server side — rich error details
from grpc_status import rpc_status
from google.rpc import status_pb2, error_details_pb2

async def GetUser(self, request, context):
    if not request.user_id:
        # Attach detailed field violation info
        detail = error_details_pb2.BadRequest(
            field_violations=[
                error_details_pb2.BadRequest.FieldViolation(
                    field="user_id",
                    description="user_id must not be empty",
                )
            ]
        )
        status = status_pb2.Status(
            code=grpc.StatusCode.INVALID_ARGUMENT.value[0],
            message="Invalid request",
            details=[detail],
        )
        await context.abort_with_status(rpc_status.to_status(status))
```
