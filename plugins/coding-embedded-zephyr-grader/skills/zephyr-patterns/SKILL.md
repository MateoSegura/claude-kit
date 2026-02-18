---
name: zephyr-patterns
description: "25+ Zephyr RTOS correctness patterns organized by category including kernel APIs, threading, ISR safety, devicetree, Kconfig, synchronization, memory management, and error handling with examples and anti-patterns."
---

# Zephyr Patterns

Quick reference for evaluating Zephyr RTOS correctness. This skill covers the 25+ patterns that distinguish correct, idiomatic Zephyr code from buggy or non-idiomatic code.

## Pattern Categories Overview

| Category | Pattern Count | Key Concerns |
|----------|---------------|--------------|
| Kernel APIs | 4 | Sleep functions, yield, init ordering |
| Threading | 5 | Thread creation, stack sizing, priorities, termination |
| ISR Safety | 4 | ISR detection, forbidden operations, signaling |
| Devicetree | 6 | Device access, macros, bindings, aliases |
| Kconfig | 3 | CONFIG prefix, types, dependencies |
| Synchronization | 5 | Mutexes, semaphores, message queues, atomics |
| Memory Management | 3 | Heaps, slabs, stack allocation |
| Error Handling | 2 | Errno propagation, error codes |
| Power Management | 2 | Device PM, system PM |
| **Total** | **34** | - |

## Decision Matrix for Correctness Evaluation

Use this table to quickly identify which patterns to check based on code structure:

| Code Contains | Check These Patterns |
|---------------|----------------------|
| Interrupt handlers (ISR_DIRECT_DECLARE) | ISR safety (4 patterns) |
| k_thread_create() calls | Threading patterns (5 patterns) |
| DEVICE_DT_GET() | Devicetree patterns (6 patterns) |
| CONFIG_* references | Kconfig patterns (3 patterns) |
| Shared global variables | Synchronization patterns (5 patterns) |
| k_malloc/k_heap_alloc | Memory patterns (3 patterns) |
| return -ERRNO | Error handling patterns (2 patterns) |
| pm_device_* calls | Power management patterns (2 patterns) |

## Critical Anti-Patterns (Auto-Fail)

These patterns indicate fundamental misunderstanding and should result in very low scores:

| Anti-Pattern | Why It's Critical | Severity |
|--------------|-------------------|----------|
| k_sleep/k_msleep in ISR | Causes system crash | Critical |
| Mutex acquire in ISR | Causes deadlock | Critical |
| Unprotected shared state (ISR + thread) | Race conditions, data corruption | Critical |
| Missing device_is_ready() check | Runtime crash if device not available | Major |
| Unbounded stack allocation (VLA/alloca) | Stack overflow | Major |

## Quick Pattern Checklist

For rapid evaluation, check these 10 high-impact patterns first:

- [ ] No sleeping in ISRs (k_sleep, k_msleep, k_usleep)
- [ ] No mutex locking in ISRs (k_mutex_lock)
- [ ] device_is_ready() called before using device
- [ ] Shared state between ISR and threads protected (k_sem, k_msgq, atomic)
- [ ] Thread stacks defined with K_THREAD_STACK_DEFINE
- [ ] Thread priorities in valid range (0-99, lower=higher priority)
- [ ] DT_NODELABEL/DT_ALIAS used instead of string searches
- [ ] CONFIG_ prefix for all Kconfig symbols
- [ ] Negative errno values returned (return -EINVAL, not EINVAL)
- [ ] k_mutex vs k_sem chosen correctly (mutex for mutual exclusion, sem for signaling)

## Additional Resources

For complete pattern specifications with code examples and detailed anti-pattern analysis:

- [correctness-checklist.md](correctness-checklist.md) — All 34 patterns fully specified with: pattern name, what to check, grep/regex patterns for detection, severity classification, scoring impact, correct vs incorrect code examples
- [anti-patterns.md](anti-patterns.md) — Common Zephyr mistakes with BAD code example, failure mode explanation (WHY it fails), and GOOD corrected code for each anti-pattern
