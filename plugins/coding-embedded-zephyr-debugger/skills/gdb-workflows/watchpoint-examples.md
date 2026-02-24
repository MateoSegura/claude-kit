# Watchpoint Examples

Concrete GDB watchpoint recipes for common Zephyr RTOS debugging scenarios. Each recipe includes the GDB command, expected output, and interpretation.

## 1. Memory Corruption Detection

**Scenario:** A global variable or buffer is being modified unexpectedly, causing intermittent failures.

```
# Watch a specific global variable for writes
(gdb) watch my_global_var
Hardware watchpoint 1: my_global_var

# Watch a specific memory address (4-byte aligned)
(gdb) watch *(uint32_t*)0x2000ABCD
Hardware watchpoint 1: *(uint32_t*)0x2000ABCD

# Watch a buffer range (set multiple watchpoints)
(gdb) watch *(uint32_t*)&my_buffer[0]
(gdb) watch *(uint32_t*)&my_buffer[64]
(gdb) watch *(uint32_t*)&my_buffer[128]

(gdb) continue
```

**Expected output when triggered:**
```
Hardware watchpoint 1: *(uint32_t*)0x2000ABCD

Old value = 0x00000042
New value = 0xDEADBEEF
0x00008a24 in corrupt_function () at src/buggy_module.c:47
47          *ptr = 0xDEADBEEF;
```

**Interpretation:** The backtrace at the trigger point shows exactly which function and line modified the memory. Check the call chain to understand how `corrupt_function` reached this code path.

## 2. Stack Canary Monitoring

**Scenario:** Suspect stack overflow is corrupting data. Monitor the stack sentinel to catch the exact moment of overflow.

```
# Get thread stack info
(gdb) p ((struct k_thread *)<thread_ptr>)->stack_info.start
$1 = 0x2000A000

# Set watchpoint on sentinel word (first word of stack)
(gdb) watch *(uint32_t*)0x2000A000
Hardware watchpoint 1: *(uint32_t*)0x2000A000

(gdb) continue
```

**Expected output when triggered:**
```
Hardware watchpoint 1: *(uint32_t*)0x2000A000

Old value = 0xAAAAAAAA
New value = 0x00012345
0x00009100 in deep_function () at src/processing.c:123
123         char local_buf[256];  // This pushes SP below sentinel
```

**Interpretation:** The sentinel changed from `0xAAAAAAAA` to another value, confirming stack overflow. The triggering function and its local variable allocation are the direct cause. Check the full call depth with `bt` to understand the cumulative stack usage.

## 3. Peripheral Register Change

**Scenario:** A peripheral register is being modified unexpectedly, causing hardware misbehavior. Watch the memory-mapped register.

```
# Watch GPIO output register (example: nRF52 GPIO P0 OUT register)
(gdb) watch *(uint32_t*)0x50000504
Hardware watchpoint 1: *(uint32_t*)0x50000504

# Watch I2C ENABLE register
(gdb) watch *(uint32_t*)0x40003500

# Watch UART BAUDRATE register
(gdb) watch *(uint32_t*)0x40002524

(gdb) continue
```

**Expected output when triggered:**
```
Hardware watchpoint 1: *(uint32_t*)0x50000504

Old value = 0x00000001
New value = 0x00000000
0x0000B234 in gpio_nrf_port_set_raw () at drivers/gpio/gpio_nrf.c:89
```

**Interpretation:** The GPIO output register was cleared. The backtrace reveals which driver call modified it. Trace upward to find the application code that initiated the GPIO change.

**Note:** Hardware watchpoints on peripheral registers may not work on all targets. Some peripherals use write-only registers that cannot be watched. Verify with the target's reference manual.

## 4. DMA Buffer Overrun

**Scenario:** DMA transfers are writing beyond the allocated buffer boundary.

```
# Set watchpoint just past the end of the DMA buffer
(gdb) p &dma_rx_buffer[DMA_BUFFER_SIZE]
$1 = (uint8_t *) 0x2000C400

# Watch the word just past the buffer
(gdb) watch *(uint32_t*)0x2000C400
Hardware watchpoint 1: *(uint32_t*)0x2000C400

(gdb) continue
```

**Expected output when triggered:**
```
Hardware watchpoint 1: *(uint32_t*)0x2000C400

Old value = 0x00000000
New value = 0x48656C6C
# Triggered during DMA ISR — backtrace shows interrupt context
0x0000D456 in dma_nrf_isr () at drivers/dma/dma_nrf.c:234
```

**Interpretation:** The DMA controller wrote past the buffer end. This means either:
1. DMA transfer length exceeds buffer size
2. DMA is configured for circular mode and buffer calculation is wrong
3. DMA destination address is misconfigured

Check DMA configuration registers and compare transfer length with buffer allocation.

## 5. Shared Variable Race Condition

**Scenario:** A variable shared between threads (or thread and ISR) is being modified at unexpected times, suggesting a missing lock or race condition.

```
# Watch the shared variable
(gdb) watch shared_counter
Hardware watchpoint 1: shared_counter

# Optional: conditional watchpoint to catch specific modifications
(gdb) watch shared_counter if shared_counter < 0
# Or watch for unexpected values
(gdb) watch shared_counter if shared_counter > 1000

(gdb) continue
```

**Expected output when triggered:**
```
Hardware watchpoint 1: shared_counter

Old value = 42
New value = 43
0x0000A100 in isr_handler () at src/sensor.c:67
67          shared_counter++;   // Non-atomic increment from ISR context!
```

**Interpretation:** The variable is being modified from ISR context without protection. If another thread also modifies this variable, the non-atomic read-modify-write creates a race condition. The fix is to use `atomic_inc()` or protect with `irq_lock()`/`irq_unlock()`.

### Advanced: Detecting Read-Write Races

```
# Access watchpoint (triggers on both read AND write)
(gdb) awatch shared_state
Hardware access watchpoint 1: shared_state

(gdb) continue

# This triggers on EVERY access, so use conditional:
(gdb) awatch shared_state if $caller_is("thread_a") || $caller_is("isr_handler")
```

## 6. Heap Corruption Detection

**Scenario:** Dynamic memory allocation (k_malloc/k_free) is corrupting heap metadata.

```
# Watch heap metadata for the system heap
# Find heap start address
(gdb) p &_system_heap
(gdb) p *(struct sys_heap *)&_system_heap

# Watch the first chunk header (implementation-dependent)
(gdb) watch *(uint32_t*)(<heap_start>)

# Alternative: watch for double-free by monitoring freed block
(gdb) p <ptr_from_k_malloc>
(gdb) watch *(uint32_t*)<ptr>
# After k_free, any write to this address suggests use-after-free
```

## Hardware Watchpoint Limitations

| Target | Max Data Watchpoints | Max Code Breakpoints | Notes |
|--------|---------------------|---------------------|-------|
| Cortex-M0/M0+ | 2 | 4 | Limited watchpoint width |
| Cortex-M3/M4/M7 | 4 | 6 | 1/2/4 byte watchpoint width |
| Cortex-M33 | 4 | 8 | TrustZone-aware |
| nRF52840 | 4 | 6 | Cortex-M4F |
| nRF5340 | 4 | 8 | Cortex-M33 |
| STM32F4 | 4 | 6 | Cortex-M4F |
| ESP32 (Xtensa) | 2 | 2 | Limited debug resources |
| ESP32-C3 (RISC-V) | Varies | Varies | Implementation-dependent |

**Tips for limited watchpoints:**
- Use conditional breakpoints instead when possible (cheaper than watchpoints)
- Remove watchpoints when not needed (`delete <N>`)
- Align watched addresses to 4-byte boundaries for maximum coverage
- On Cortex-M, a single watchpoint can cover 1, 2, or 4 bytes
