# Serialization Complete Reference

## zcbor CBOR Codec

**CDDL Schema:**

```cddl
sensor_data = {
    temp: int,
    ? humidity: int,
    readings: [+ int],
}
```

**Generate:**

```bash
zcbor code -c sensor.cddl --output-c sensor_cbor.c
```

**Encode:**

```c
#include "sensor_cbor.h"

uint8_t buffer[128];
struct zcbor_state states[2];

zcbor_new_encode_state(states, ARRAY_SIZE(states), buffer, sizeof(buffer), 0);

struct sensor_data data = { .temp = 25, .humidity = 60 };
bool success = encode_sensor_data(states, &data);
size_t encoded_len = states[0].payload - buffer;
```

## Nanopb Protobuf

**.proto:**

```protobuf
message Telemetry {
    int32 temp = 1;
    repeated int32 readings = 2;
}
```

**.options:**

```
Telemetry.readings max_count:10
```

**CMakeLists.txt:**

```cmake
nanopb_generate_cpp(PROTO_SRCS PROTO_HDRS telemetry.proto)
target_sources(app PRIVATE ${PROTO_SRCS})
```

**Encode:**

```c
#include <pb_encode.h>
#include "telemetry.pb.h"

uint8_t buffer[128];
pb_ostream_t stream = pb_ostream_from_buffer(buffer, sizeof(buffer));

Telemetry msg = Telemetry_init_default;
msg.temp = 25;

pb_encode(&stream, Telemetry_fields, &msg);
size_t len = stream.bytes_written;
```
