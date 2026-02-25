---
name: core-embedded:memory-management
description: "Embedded memory management — static vs dynamic allocation, memory pools, stack sizing, heap fragmentation, memory-mapped I/O, DMA, and linker script fundamentals"
user-invocable: false
---

# Memory Management Quick Reference

## Memory Architecture Overview

Embedded systems have constrained, heterogeneous memory. Understanding the memory map is essential for reliable firmware.

```
+------------------+  High address
|   Stack (SRAM)   |  Grows downward, per-task
+------------------+
|   Heap  (SRAM)   |  Optional, grows upward
+------------------+
|   .bss  (SRAM)   |  Zero-initialized globals
+------------------+
|   .data (SRAM)   |  Initialized globals (copied from Flash at boot)
+------------------+  RAM start
        ...
+------------------+  Flash end
|   .rodata        |  Constants, string literals
+------------------+
|   .text          |  Code (execute-in-place)
+------------------+
|   Vector table   |  Interrupt vectors
+------------------+  Flash start (0x00000000 or 0x08000000)
```

## Static vs Dynamic Allocation

- **Static** (preferred): All memory decided at compile/link time. Deterministic, no fragmentation, analyzable via linker map. Wastes memory if worst-case != typical case.
- **Dynamic** (use with caution): `malloc`/`free`. Acceptable for init-only allocation. Avoid in ISRs, tight loops, safety-critical paths.
- **Memory pools**: Fixed-size block allocators. Combine flexibility of dynamic with determinism of static.

| Criterion | Static | Dynamic | Pool |
|-----------|--------|---------|------|
| Deterministic | Yes | No | Yes |
| Fragmentation | None | Risk | None |
| Memory efficiency | Low (worst-case) | High (on-demand) | Medium |
| ISR-safe | Yes | No | Yes (with lock-free pool) |

## Memory Pool Guidelines

- Size blocks to the most common allocation size
- Use separate pools for different object types (no cross-contamination)
- Monitor high-water mark to detect pool exhaustion trends
- Consider lock-free pool designs for ISR-to-task allocation
- See [memory-reference.md](memory-reference.md) for implementation examples

## Stack Sizing

### Estimation Approach

1. **Measure worst-case call depth** — deepest function call chain including ISR nesting
2. **Account for local variables** — largest stack frame at each call level
3. **Add ISR overhead** — hardware pushes context (typically 32-128 bytes per nesting level)
4. **Add safety margin** — 20-50% above calculated worst case

### Stack Size Recommendations

| Task Type | Typical Range | Notes |
|-----------|--------------|-------|
| Simple I/O | 256-512 bytes | GPIO, basic sensor reads |
| Protocol processing | 1-2 KB | UART/SPI parsing, state machines |
| Networking | 2-4 KB | TCP/IP stack, TLS handshakes |
| printf/logging | 512-1 KB extra | Format strings use significant stack |
| Recursive algorithms | Avoid | Use iterative alternatives |

### Stack Overflow Detection

- **Canary/sentinel**: Write known pattern at stack bottom, check periodically
- **MPU-based**: Configure memory protection unit to fault on stack overflow
- **Fill pattern**: Pre-fill stack with 0xDEADBEEF, check high-water mark post-run

## Heap Fragmentation

### The Problem

Repeated malloc/free of varying sizes creates unusable gaps:

```
[USED 32B][FREE 16B][USED 64B][FREE 8B][USED 32B]
                                         ^-- can't allocate 20B despite 24B free
```

### Prevention Strategies

1. **Avoid dynamic allocation** — use static buffers and pools
2. **Allocate once, never free** — acceptable for initialization
3. **Fixed-size allocations only** — memory pool pattern
4. **LIFO allocation** — stack-like allocator where last allocated is first freed
5. **Compacting allocator** — relocates objects (complex, rare in embedded)

## Memory-Mapped I/O

Peripheral registers accessed through fixed memory addresses.

Access peripheral registers through volatile pointers or struct overlays. Critical rules:
- Always use `volatile` for hardware registers — prevents compiler optimization
- Use set/clear registers when available to avoid read-modify-write races
- Never cache register values in local variables across operations
- See `hal-patterns` skill for detailed register access recipes

## DMA Concepts

Direct Memory Access transfers data between peripherals and memory without CPU intervention.

### When to Use DMA

- High-throughput data streams (ADC sampling, audio, display)
- Peripheral-to-memory or memory-to-peripheral transfers
- Memory-to-memory block copies
- Freeing CPU for computation while data moves in background

### DMA Transfer Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Single | One transfer per trigger | Sporadic peripheral events |
| Burst | Multiple transfers per trigger | High-speed peripherals |
| Circular | Buffer wraps around automatically | Continuous streaming (ADC, audio) |
| Double-buffer | Ping-pong between two buffers | Processing one buffer while filling the other |

### Cache Coherency

On systems with data cache (Cortex-M7, etc.):

- **Before DMA read**: Invalidate cache for the DMA buffer region
- **Before DMA write**: Clean (flush) cache for the DMA buffer region
- **Or**: Place DMA buffers in non-cacheable memory region

## Linker Script Basics

### Key Sections

| Section | Content | Location |
|---------|---------|----------|
| `.text` | Executable code | Flash |
| `.rodata` | Constants, string literals | Flash |
| `.data` | Initialized global/static variables | Flash (LMA) -> RAM (VMA) |
| `.bss` | Zero-initialized global/static variables | RAM |
| `.stack` | Task stacks | RAM |
| `.heap` | Dynamic allocation arena | RAM |

Use `__attribute__((section(".name")))` to place variables in specific sections (e.g., `.nocache` for DMA buffers, `.backup_sram` for retained data). After building, check the `.map` file for Flash/RAM usage breakdown.

## Additional Resources

- For detailed allocation patterns, DMA configuration examples, and linker script recipes, see [memory-reference.md](memory-reference.md)
