---
name: core-embedded:rtos-fundamentals
description: "RTOS-agnostic kernel concepts — tasks, scheduling, synchronization primitives, message queues, timers, interrupt handling, and watchdog patterns"
user-invocable: false
---

# RTOS Fundamentals Quick Reference

## Core Concepts

An RTOS (Real-Time Operating System) provides deterministic task scheduling, synchronization, and resource management for embedded systems. Unlike general-purpose OSes, an RTOS guarantees bounded response times for critical operations.

## Task/Thread Model

### Task States

Tasks cycle through: **Ready** (eligible to run) -> **Running** (executing on CPU) -> **Blocked** (waiting for event/timeout/resource). Some RTOSes also have a **Suspended** state (explicitly paused).

### Task Design Guidelines

- One responsibility per task — avoid monolithic "do everything" tasks
- Choose stack size based on worst-case call depth plus safety margin (typically 20-50% extra)
- Assign priorities based on urgency, not importance (Rate Monotonic Analysis for periodic tasks)
- Minimize time spent at high priority — do the urgent work and defer the rest

## Scheduling

- **Preemptive**: Higher-priority tasks immediately preempt lower-priority ones. Required for hard real-time guarantees.
- **Cooperative**: Tasks run until they explicitly yield or block. Simpler but no timing guarantees.
- **Time-slicing**: Equal-priority tasks share CPU in round-robin fashion (configurable quantum, typically 1-10 ms).

### Priority Assignment Strategies

| Strategy | Rule | Use Case |
|----------|------|----------|
| Rate Monotonic | Shorter period = higher priority | Periodic tasks with deadlines |
| Deadline Monotonic | Shorter deadline = higher priority | When deadline != period |
| Priority Ceiling | Lock elevates to ceiling priority | Preventing priority inversion |

## Synchronization Primitives

### Semaphore

Counting semaphore for signaling and resource counting.

```
Producer:  signal(sem)   --> increments count
Consumer:  wait(sem)     --> decrements count (blocks if 0)
```

- **Binary semaphore** (count 0 or 1): event signaling between tasks or ISR-to-task
- **Counting semaphore**: resource pool management (N available units)
- ISR-safe for the signal/give operation (never wait/take from ISR)

### Mutex

Mutual exclusion with ownership and priority inheritance. Only the owner can unlock. Priority inheritance prevents priority inversion (low-priority holder temporarily inherits blocking task's priority). Never use from ISR context.

### Mutex vs Semaphore

| Feature | Mutex | Binary Semaphore |
|---------|-------|-----------------|
| Ownership | Yes (only owner unlocks) | No (anyone can signal) |
| Priority inheritance | Yes | No |
| ISR signal | No | Yes |
| Use case | Protecting shared data | Event notification |

### Condition Variable

Wait for a condition while atomically releasing a mutex. Always re-check the condition after waking (spurious wakeups). Use broadcast when multiple waiters need notification.

## Message Queues

Fixed-size FIFO for inter-task communication. Copies data into the queue (no pointer aliasing).

```
Task A:  send(queue, &msg, timeout)    --> copies msg into queue
Task B:  receive(queue, &msg, timeout) --> copies msg out of queue
```

- Size the queue for burst tolerance: how many messages can arrive before the consumer processes them
- Prefer fixed-size messages to avoid fragmentation
- ISR-safe for send (non-blocking mode)

## Timers

- **One-shot**: fires once after a delay. **Periodic**: fires repeatedly at a fixed interval.
- Timer callbacks typically run in ISR or dedicated timer-task context — keep them short
- Common patterns: timeout (one-shot, cancel on success), periodic poll, debounce (restart on each edge), watchdog feed

## Interrupt Handling

### ISR Design Rules

1. **Keep ISRs short** — acknowledge the interrupt, capture data, defer processing
2. **No blocking calls** — never wait on mutex, sleep, or allocate memory in ISR
3. **Signal a task** — use semaphore give, queue send, or event flag from ISR
4. **Minimize shared state** — use lock-free structures or disable interrupts briefly

### Deferred Processing Pattern

```
ISR:
  1. Read hardware register / clear interrupt flag
  2. Copy raw data to buffer
  3. Signal processing task (semaphore give or queue send)
  4. Return immediately

Task:
  1. Wait for signal (semaphore take or queue receive)
  2. Process data at task priority
  3. Update application state
```

### Interrupt Priority vs Task Priority

- Interrupt priorities are separate from task priorities
- All interrupts preempt all tasks (on most architectures)
- Nested interrupts: higher-priority interrupt preempts lower-priority ISR
- Critical sections (disabling interrupts) should be as brief as possible

## Watchdog Patterns

### Hardware Watchdog

A hardware timer that resets the system if not periodically "fed" (kicked). Catches infinite loops and deadlocks.

```
Task:
  while (1) {
      do_work();
      feed_watchdog();   /* Must happen within timeout window */
  }
```

### Multi-Task Watchdog

A supervisor task collects health check-ins from all monitored tasks. It only feeds the hardware watchdog when every task has reported in within its deadline. This catches per-task deadlocks, not just global hangs.

**Guidelines**: Set timeout longer than worst-case execution time. Feed from the main loop, never from a timer ISR. Consider windowed watchdog (must feed within a time window, not too early or too late).

## Additional Resources

- For detailed scheduling analysis, synchronization patterns, and worked examples, see [rtos-reference.md](rtos-reference.md)
