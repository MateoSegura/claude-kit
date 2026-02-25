# RTOS Fundamentals — Complete Reference

## Scheduling Theory

### Rate Monotonic Analysis (RMA)

For a set of periodic tasks with fixed priorities:

- Assign higher priority to tasks with shorter periods
- A task set is schedulable if total CPU utilization is below the bound:
  - 1 task: 100%
  - 2 tasks: 82.8%
  - 3 tasks: 78.0%
  - N tasks: N * (2^(1/N) - 1) → converges to ~69.3%

| Tasks | Utilization Bound |
|-------|------------------|
| 1 | 1.000 |
| 2 | 0.828 |
| 3 | 0.780 |
| 4 | 0.757 |
| 5 | 0.743 |
| N→∞ | 0.693 |

### Worst-Case Response Time

For task i with priority Pi:

```
R_i = C_i + Σ(for all j with higher priority) ⌈R_i / T_j⌉ * C_j
```

Where:
- C_i = worst-case execution time of task i
- T_j = period of higher-priority task j
- Solve iteratively until R_i converges

### Priority Inversion

**Problem**: High-priority task blocked waiting for a mutex held by a low-priority task, while a medium-priority task preempts the low-priority task.

```
High:   ──────[blocks on mutex]──────────────────[runs]
Med:    ───────────[runs for a long time]────────
Low:    ──[holds mutex]──[preempted]──────[resumes][unlocks]
```

**Solutions**:
1. **Priority Inheritance** — Low-priority task inherits high-priority while holding the mutex
2. **Priority Ceiling** — Mutex elevates holder to ceiling priority (highest of all potential users)
3. **Avoid** — Design so high and low priority tasks don't share mutexes

## Advanced Synchronization

### Event Flags / Event Groups

Bit-field where tasks can wait for combinations of events:

```c
/* Pseudo-code */
event_flags_t events;

/* Task A sets bit 0 */
event_set(&events, BIT(0));

/* Task B sets bit 1 */
event_set(&events, BIT(1));

/* Task C waits for both bits 0 AND 1 */
event_wait(&events, BIT(0) | BIT(1), WAIT_ALL, TIMEOUT);

/* Task D waits for bit 0 OR bit 1 */
event_wait(&events, BIT(0) | BIT(1), WAIT_ANY, TIMEOUT);
```

Use cases:
- Synchronization barrier (wait for multiple tasks to reach a point)
- Multi-condition wake (sensor ready AND timer expired)

### Reader-Writer Pattern

Multiple readers or single writer access to shared data:

```c
/* Read path (concurrent) */
reader_lock(&rw_lock);
value = shared_data;
reader_unlock(&rw_lock);

/* Write path (exclusive) */
writer_lock(&rw_lock);
shared_data = new_value;
writer_unlock(&rw_lock);
```

Implementation approaches:
1. Counting semaphore for readers + mutex for writers
2. Read-copy-update (RCU) for minimal reader overhead

### Mailbox (Single-Element Queue)

Like a message queue with capacity 1, allowing rendezvous between producer and consumer:

- Producer blocks if mailbox is full
- Consumer blocks if mailbox is empty
- Guarantees synchronized handoff

## Interrupt Architecture

### Nested Vectored Interrupt Controller (NVIC) — ARM Cortex-M

Priority levels and features:

| Feature | Cortex-M0/M0+ | Cortex-M3/M4 | Cortex-M33 |
|---------|---------------|-------------|-----------|
| Priority bits | 2 (4 levels) | 3-8 (8-256 levels) | 3-8 |
| Priority grouping | No | Yes (preempt + sub) | Yes |
| Tail chaining | Yes | Yes | Yes |
| Late arrival | Yes | Yes | Yes |
| Lazy stacking (FPU) | N/A | Yes (M4F) | Yes |

### BASEPRI Register (Cortex-M3+)

Mask interrupts below a threshold without disabling all:

```c
/* Block interrupts with priority >= 3 (lower-priority) */
__set_BASEPRI(3 << (8 - __NVIC_PRIO_BITS));

/* Restore */
__set_BASEPRI(0);
```

This allows high-priority interrupts to still fire during a critical section.

### ISR Latency Budget

Total time from interrupt event to first instruction in handler:

| Component | Cycles (typical) |
|-----------|-----------------|
| Hardware recognition | 1-2 |
| Context save (stacking) | 12 (M0) / 12 (M3/M4) |
| Vector fetch | 2-4 |
| Pipeline flush | 1-3 |
| **Total entry latency** | **~12-20 cycles** |
| Tail chaining (back-to-back ISR) | 6 cycles |

### ISR Stack Usage

On ARM Cortex-M, ISRs use the Main Stack Pointer (MSP):

- Hardware automatically pushes 8 registers (R0-R3, R12, LR, PC, xPSR) = 32 bytes
- With FPU context: additional 16 registers = 64 bytes more
- Nested ISRs stack on top — budget MSP stack for worst-case nesting depth

## Timer Patterns in Detail

### Timeout with Cancellation

```c
/* Start operation and arm timeout */
start_async_operation();
timer_start(&timeout_timer, TIMEOUT_MS);

/* On operation complete (before timeout fires) */
void operation_complete_cb(void) {
    timer_cancel(&timeout_timer);
    process_result();
}

/* On timeout (operation took too long) */
void timeout_cb(void) {
    cancel_operation();
    handle_timeout_error();
}
```

### Rate Limiter

```c
static uint32_t last_event_time = 0;
#define MIN_INTERVAL_MS  100

void on_event(void) {
    uint32_t now = get_tick_ms();
    if ((now - last_event_time) >= MIN_INTERVAL_MS) {
        last_event_time = now;
        process_event();
    }
    /* Else: rate-limited, discard */
}
```

### Exponential Backoff

```c
uint32_t backoff_ms = INITIAL_BACKOFF_MS;

void retry_with_backoff(void) {
    if (attempt_operation()) {
        backoff_ms = INITIAL_BACKOFF_MS;  /* Reset on success */
        return;
    }

    timer_start(&retry_timer, backoff_ms);
    backoff_ms = MIN(backoff_ms * 2, MAX_BACKOFF_MS);
}
```

## Task Design Patterns

### Producer-Consumer with Bounded Queue

```
Producer Task             Queue (N slots)         Consumer Task
  |                        +---+---+---+           |
  |-- send(msg) --------> | 1 | 2 | 3 | -------> receive(msg) --|
  |                        +---+---+---+           |
  |  (blocks if full)                     (blocks if empty)
```

Guidelines:
- Size queue for burst tolerance: worst-case production rate * consumer processing time
- Monitor queue fill level for overload detection
- Use non-blocking send from ISR, blocking send from tasks

### Pipeline Pattern

Chain of tasks processing data sequentially:

```
Raw Data --> [Acquire Task] --> [Filter Task] --> [Transmit Task] --> Output
              queue 1            queue 2           queue 3
```

Benefits:
- Each stage has clear responsibility
- Stages can run at different priorities
- Easy to add/remove processing stages

### Finite State Machine Task

```c
typedef enum { STATE_IDLE, STATE_ACTIVE, STATE_ERROR } state_t;
typedef void (*state_handler_t)(event_t event);

static state_t current_state = STATE_IDLE;
static const state_handler_t handlers[] = {
    [STATE_IDLE]   = handle_idle,
    [STATE_ACTIVE] = handle_active,
    [STATE_ERROR]  = handle_error,
};

void task_main(void) {
    while (1) {
        event_t event;
        receive_event(&event, TIMEOUT);
        handlers[current_state](event);
    }
}

void handle_idle(event_t event) {
    switch (event.type) {
    case EVENT_START:
        init_hardware();
        current_state = STATE_ACTIVE;
        break;
    case EVENT_TIMEOUT:
        /* Stay idle */
        break;
    }
}
```

## Deadlock Prevention

### Four Conditions for Deadlock

1. **Mutual exclusion** — Resource held exclusively
2. **Hold and wait** — Task holds one resource while waiting for another
3. **No preemption** — Resources cannot be forcibly taken
4. **Circular wait** — A→B→C→A dependency chain

### Prevention Strategies

| Strategy | How | Cost |
|----------|-----|------|
| Lock ordering | Always acquire mutexes in the same global order | Discipline required |
| Try-lock | Attempt lock with timeout, release all on failure | Retry overhead |
| Single lock | Use one mutex for all shared resources | Reduced concurrency |
| Lock-free | Use atomic operations instead of mutexes | Complexity |
| Avoid nesting | Design so tasks never hold multiple mutexes | May not be feasible |

### Detecting Deadlocks

- Implement lock acquisition logging in debug builds
- Use watchdog to detect frozen tasks
- RTOS-specific thread analyzers can dump lock ownership

## Watchdog Architecture

### Hardware Watchdog Registers

Typical hardware watchdog interface:

```c
/* Feed/kick the watchdog */
WDG->KEY = FEED_SEQUENCE_1;   /* e.g., 0xAAAA */
WDG->KEY = FEED_SEQUENCE_2;   /* e.g., 0x5555 */

/* Configure timeout */
WDG->PRESCALER = WDG_PRESCALER_256;
WDG->RELOAD = timeout_value;

/* Enable (often cannot be disabled once started) */
WDG->KEY = ENABLE_SEQUENCE;
```

### Windowed Watchdog

Must feed within a time window — not too early, not too late:

```
|------- forbidden -------|- allowed -|- forbidden -|
0                      open         close        reset
```

Catches:
- Infinite loops (feeds too late → reset)
- Runaway code executing too fast (feeds too early → reset)

### Supervisor Pattern Implementation

```c
#define MAX_MONITORED_TASKS  8
#define CHECK_PERIOD_MS      1000

static struct {
    bool checked_in;
    uint32_t deadline_ms;
} task_health[MAX_MONITORED_TASKS];

void supervisor_task(void) {
    while (1) {
        sleep_ms(CHECK_PERIOD_MS);

        bool all_healthy = true;
        for (int i = 0; i < MAX_MONITORED_TASKS; i++) {
            if (task_health[i].deadline_ms > 0 && !task_health[i].checked_in) {
                all_healthy = false;
                log_error("Task %d missed deadline", i);
            }
            task_health[i].checked_in = false;  /* Reset for next period */
        }

        if (all_healthy) {
            feed_hardware_watchdog();
        }
        /* If not all healthy, hardware watchdog will eventually reset */
    }
}

/* Called by each monitored task */
void task_checkin(int task_id) {
    task_health[task_id].checked_in = true;
}
```
