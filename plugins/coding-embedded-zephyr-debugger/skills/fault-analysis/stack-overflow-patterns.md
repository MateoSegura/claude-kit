# Stack Overflow Patterns

Detection methods, analysis procedures, and sizing methodology for stack overflow diagnosis in Zephyr RTOS.

## Stack Sentinel Detection

Zephyr places a sentinel value (`0xAAAAAAAA`) at the bottom of each thread stack when `CONFIG_STACK_SENTINEL=y`. The kernel checks this value on context switch.

### Checking Sentinel Integrity

```bash
# In GDB, check sentinel for a specific thread
# First get the thread's stack info
p ((struct k_thread *)<thread_ptr>)->stack_info.start
p ((struct k_thread *)<thread_ptr>)->stack_info.size

# Read sentinel word (4 bytes at stack bottom)
p/x *(uint32_t*)((struct k_thread *)<thread_ptr>)->stack_info.start
# Expected: 0xAAAAAAAA if intact
# Any other value: stack overflow confirmed
```

### Sentinel Limitations

- Only checked on context switch — overflow during a long-running function is not caught until next switch
- Does not catch overflow that skips the sentinel word (large stack frame allocation)
- Not available if `CONFIG_STACK_SENTINEL` is disabled (it is off by default)
- MPU stack guard (`CONFIG_MPU_STACK_GUARD`) is more reliable but requires MPU hardware

## MPU Stack Guard

When `CONFIG_MPU_STACK_GUARD=y` and the hardware has an MPU, Zephyr configures a guard region at the bottom of each thread stack. Overflow triggers an immediate MemManage fault (MMFSR.DACCVIOL) instead of silently corrupting memory.

### Identifying MPU Guard Faults

1. CFSR shows MMFSR.DACCVIOL = 1
2. MMFAR points to an address at or near a thread's stack bottom
3. The faulting PC is in the overflowing function (not the guard setup)

```
# Verify fault is at stack guard boundary
p/x *(uint32_t*)0xE000ED34  # MMFAR
# Compare with thread stack_info.start — should be close to stack bottom
```

### MPU Guard vs Sentinel

| Feature | CONFIG_STACK_SENTINEL | CONFIG_MPU_STACK_GUARD |
|---------|----------------------|----------------------|
| Detection timing | Context switch only | Immediate (synchronous fault) |
| Hardware required | None | MPU |
| Memory overhead | 4 bytes per thread | One MPU region per thread |
| Reliability | Can miss large frame overflows | Catches all overflows into guard region |
| Production use | Development only | Suitable for production |

## Thread Analyzer

Zephyr's thread analyzer reports stack usage for all threads. Enable with:

```
CONFIG_THREAD_ANALYZER=y
CONFIG_THREAD_ANALYZER_AUTO=y
CONFIG_THREAD_ANALYZER_AUTO_INTERVAL=10
CONFIG_THREAD_NAME=y
```

### Interpreting Thread Analyzer Output

```
Thread analysis:
 my_thread        : STACK: unused 128 usage 896 / 1024 (87%)
 idle             : STACK: unused 200 usage 56 / 256 (21%)
 sysworkq         : STACK: unused 412 usage 612 / 1024 (59%)
 logging          : STACK: unused 180 usage 332 / 512 (64%)
```

| Usage | Status | Action |
|-------|--------|--------|
| 0-50% | Safe | No action needed, stack may be oversized |
| 50-70% | Normal | Acceptable for most applications |
| 70-85% | Warning | Monitor — overflow risk under peak load |
| 85-95% | Danger | Increase stack size immediately |
| >95% | Critical | Overflow imminent or already occurring |

### Important Notes

- Thread analyzer measures high-water mark using stack painting (fill pattern `0xAAAAAAAA`)
- Measurement is approximate — does not account for ISR stack usage on the thread's stack
- ISR stack is separate (`CONFIG_ISR_STACK_SIZE`) but nested interrupts can cause ISR stack overflow
- Stack usage can vary between runs due to different code paths and timing

## Stack Sizing Methodology

### Step 1: Identify Stack Consumers

For each thread, catalog:
- Maximum call depth (count frames in deepest backtrace)
- Local variable sizes (especially arrays and structs on stack)
- Function pointer calls (unknown depth — requires manual analysis)
- Library calls (printf family, crypto, JSON parsing are heavy consumers)

### Step 2: Calculate Baseline

```
Base = sum of all local variables in deepest call chain
     + (frame_count * frame_overhead)   # ~32-64 bytes per frame on Cortex-M
     + ISR_nesting_overhead             # if CONFIG_IRQ_OFFLOAD or nested IRQ
     + FPU_context                      # +136 bytes if FPU is used (S0-S31 + FPSCR)
     + alignment_padding                # 8-byte alignment per frame
```

### Step 3: Apply Safety Margin

| Context | Multiplier | Rationale |
|---------|-----------|-----------|
| Development | 2.0x | Extra room for debugging, assertions, printf |
| Testing | 1.5x | Reduced but still safe for unexpected paths |
| Production | 1.25x | Minimal margin after profiling confirms actual usage |

### Step 4: Common Stack Sizes

| Thread Type | Typical Size | Notes |
|-------------|-------------|-------|
| Simple sensor reader | 512-768 bytes | Minimal call depth, no formatting |
| BLE handler | 1024-2048 bytes | Depends on MTU and attribute count |
| Shell thread | 2048-4096 bytes | Printf formatting is expensive |
| Networking (TCP/IP) | 2048-4096 bytes | Socket operations, TLS adds more |
| Logging thread | 512-1024 bytes | Depends on log message formatting |
| Main thread | 1024-4096 bytes | Depends on initialization complexity |
| ISR stack | 1024-2048 bytes | Shared by all ISRs, size for deepest nesting |

### Step 5: Kconfig Settings

```
# Per-thread default (if not specified in K_THREAD_STACK_DEFINE)
CONFIG_MAIN_STACK_SIZE=1024

# ISR stack (shared by all interrupts)
CONFIG_ISR_STACK_SIZE=2048

# System workqueue
CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE=1024

# Idle thread
CONFIG_IDLE_STACK_SIZE=256

# Shell (if enabled)
CONFIG_SHELL_STACK_SIZE=2048

# Logging thread
CONFIG_LOG_PROCESS_THREAD_STACK_SIZE=768

# Network
CONFIG_NET_TX_STACK_SIZE=1200
CONFIG_NET_RX_STACK_SIZE=1500
```

## Common Overflow Triggers

| Trigger | Description | Detection |
|---------|-------------|-----------|
| printf/snprintf | Format string processing uses 200-500 bytes of stack | Thread analyzer shows spike during logging |
| JSON parsing | cJSON/json-c allocate temporary structures on stack | Overflow during message parsing |
| TLS handshake | mbedTLS uses 4-10KB of stack during handshake | Overflow at connection establishment |
| Recursive functions | Any recursion on embedded is dangerous | GDB backtrace shows repeated frames |
| Large local arrays | `char buf[512]` in a deeply-nested function | Static analysis of local variable sizes |
| Compiler inlining | Aggressive inlining can multiply stack usage | Compare -O0 vs -Os stack usage |
| Floating point | FPU context save adds 136 bytes to exception frame | Overflow only during interrupt with FPU active |

## GDB Stack Analysis Commands

```bash
# List all threads with stack info
info threads

# Switch to suspect thread
thread <N>

# Full backtrace with local variables
bt full

# Check stack usage per frame
info frame 0
info frame 1
# ... repeat for each frame

# Find stack boundaries
p/x ((struct k_thread *)z_current_get())->stack_info.start
p/x ((struct k_thread *)z_current_get())->stack_info.size

# Paint check — find first non-0xAA byte from stack bottom
# (manual scan in GDB)
x/64x <stack_bottom>
```
