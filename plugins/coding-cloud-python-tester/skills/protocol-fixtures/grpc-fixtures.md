# gRPC Test Fixtures

## In-Process gRPC Server

```python
import pytest
import grpc
from grpc import aio as grpc_aio
from app.grpc.servicer import MyServiceServicer
from app.proto import my_service_pb2_grpc

@pytest.fixture
async def grpc_server():
    """Start an in-process gRPC server for testing."""
    server = grpc_aio.server()
    my_service_pb2_grpc.add_MyServiceServicer_to_server(
        MyServiceServicer(), server
    )
    port = server.add_insecure_port("[::]:0")
    await server.start()
    yield f"localhost:{port}"
    await server.stop(grace=0)

@pytest.fixture
async def grpc_channel(grpc_server):
    """Async gRPC channel connected to test server."""
    async with grpc_aio.insecure_channel(grpc_server) as channel:
        yield channel

@pytest.fixture
async def grpc_stub(grpc_channel):
    """gRPC service stub for making test calls."""
    return my_service_pb2_grpc.MyServiceStub(grpc_channel)
```

## Testing Unary RPCs

```python
from app.proto import my_service_pb2

@pytest.mark.asyncio
async def test_get_resource(grpc_stub):
    request = my_service_pb2.GetResourceRequest(id="test-123")
    response = await grpc_stub.GetResource(request)
    assert response.id == "test-123"
    assert response.name != ""

@pytest.mark.asyncio
async def test_get_resource_not_found(grpc_stub):
    request = my_service_pb2.GetResourceRequest(id="nonexistent")
    with pytest.raises(grpc_aio.AioRpcError) as exc_info:
        await grpc_stub.GetResource(request)
    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND
```

## Testing Server Streaming RPCs

```python
@pytest.mark.asyncio
async def test_list_resources_stream(grpc_stub):
    request = my_service_pb2.ListResourcesRequest(page_size=10)
    items = []
    async for response in grpc_stub.ListResources(request):
        items.append(response)
    assert len(items) > 0
    assert all(hasattr(item, "id") for item in items)
```

## Deadline and Metadata Testing

```python
@pytest.mark.asyncio
async def test_deadline_propagation(grpc_stub):
    request = my_service_pb2.SlowRequest(delay_seconds=10)
    with pytest.raises(grpc_aio.AioRpcError) as exc_info:
        await grpc_stub.SlowOperation(
            request, timeout=0.1  # 100ms deadline
        )
    assert exc_info.value.code() == grpc.StatusCode.DEADLINE_EXCEEDED

@pytest.mark.asyncio
async def test_metadata_forwarding(grpc_stub):
    metadata = [("x-request-id", "test-req-001")]
    request = my_service_pb2.EchoRequest(message="hello")
    response, call = await grpc_stub.Echo.with_call(request, metadata=metadata)
    trailing = dict(await call.trailing_metadata())
    assert "x-request-id" in trailing
```

## Protobuf Message Factories

```python
from app.proto import my_service_pb2

def make_resource(**overrides):
    """Factory for creating test Resource messages."""
    defaults = {
        "id": "test-resource-001",
        "name": "Test Resource",
        "status": my_service_pb2.ResourceStatus.ACTIVE,
        "config": my_service_pb2.Config(key="default", value="test"),
    }
    defaults.update(overrides)
    return my_service_pb2.Resource(**defaults)
```
