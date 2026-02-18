---
name: coding-embedded-zephyr-knowledge:serialization
description: Data serialization in Zephyr — zcbor CBOR codec vs protobuf with nanopb, schema definition, code generation, and integration patterns
user-invocable: false
---

# Serialization Quick Reference

## zcbor vs Protobuf

| Feature | zcbor | Protobuf (nanopb) |
|---------|-------|-------------------|
| Schema | CDDL | .proto |
| Format | CBOR (binary) | Protobuf (binary) |
| Size | Smaller | Small |
| Speed | Fast | Fast |
| Ecosystem | Growing | Mature |

## zcbor (CBOR)

**CDDL schema (sensor.cddl):**

```cddl
sensor_reading = {
    temperature: int,
    humidity: int,
    timestamp: uint,
}
```

**Generate codec:**

```bash
zcbor code -c sensor.cddl --output-c sensor_cbor.c --output-h sensor_cbor.h
```

**Kconfig:**

```kconfig
CONFIG_ZCBOR=y
```

## Protobuf (nanopb)

**Proto schema (sensor.proto):**

```protobuf
syntax = "proto3";

message SensorReading {
    int32 temperature = 1;
    int32 humidity = 2;
    uint64 timestamp = 3;
}
```

**Kconfig:**

```kconfig
CONFIG_NANOPB=y
```

## Additional resources

- For complete zcbor CDDL syntax, codec generation, and Zephyr CMake integration, see [zcbor-protobuf-reference.md](zcbor-protobuf-reference.md)
