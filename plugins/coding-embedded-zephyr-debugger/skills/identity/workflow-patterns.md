# Investigation Patterns

Step-by-step investigation templates for each failure domain. Each template defines the entry point, key artifacts to examine, GDB commands to run, and escalation criteria.

## 1. Hard Fault Investigation

**Entry point:** CFSR/HFSR non-zero, or fault handler backtrace in logs.

### Steps
1. **Read fault registers** — Decode CFSR (MemManage, BusFault, UsageFault sub-registers), HFSR, MMFAR, BFAR. For Xtensa: EXCCAUSE/EXCVADDR. For RISC-V: mcause/mtval.
2. **Identify fault type** — Map register bits to fault category: invalid memory access, bus error, undefined instruction, unaligned access, divide by zero, coprocessor fault.
3. **Get faulting address** — Extract PC from stacked exception frame. Use `addr2line -e build/zephyr/zephyr.elf <PC>` to map to source.
4. **Analyze backtrace** — Walk the call chain from fault handler to identify the call path leading to the fault.
5. **Check memory map** — Compare faulting address against linker map (`build/zephyr/zephyr.map`) to determine which section/symbol it falls in.
6. **Inspect surrounding code** — Read the source at the faulting location. Check pointer dereferences, array indexing, DMA buffer boundaries.
7. **Check MPU configuration** — If MemManage fault, verify MPU region configuration against the access that triggered the fault.

### Key Artifacts
- `CFSR` at `0xE000ED28` (Cortex-M), `EXCCAUSE` (Xtensa), `mcause` (RISC-V)
- Stacked exception frame (R0-R3, R12, LR, PC, xPSR)
- `build/zephyr/zephyr.map` — linker map
- `build/zephyr/zephyr.elf` — ELF with debug symbols

### GDB Commands
```
info registers
x/8x $sp           # stacked exception frame
bt full             # full backtrace with locals
info threads        # all thread states
p/x *(uint32_t*)0xE000ED28  # CFSR
p/x *(uint32_t*)0xE000ED2C  # HFSR
p/x *(uint32_t*)0xE000ED34  # MMFAR
p/x *(uint32_t*)0xE000ED38  # BFAR
```

### Escalation
- If fault address is in flash (code execution fault) -> check for corrupted firmware image
- If fault recurs at different addresses -> suspect memory corruption, escalate to memory analysis
- If fault only under load -> suspect stack overflow, check sentinel and thread analyzer

---

## 2. Stack Overflow Investigation

**Entry point:** Stack sentinel corruption detected, MPU stack guard exception, or thread analyzer reports >90% usage.

### Steps
1. **Check stack sentinel** — Examine the stack sentinel word (usually `0xAAAAAAAA`) at the bottom of the thread stack. Corruption indicates overflow.
2. **Run thread analyzer** — Enable `CONFIG_THREAD_ANALYZER` and `CONFIG_THREAD_ANALYZER_AUTO`, check output for stack usage percentages.
3. **Identify the overflowing thread** — Correlate the faulting thread with thread analyzer output. Note the thread name, priority, and stack size.
4. **Analyze call depth** — Use `bt` in GDB to measure the deepest call chain. Count frames and estimate stack consumption per frame.
5. **Check for large local variables** — Search for arrays, structs, or buffers allocated on the stack in the call chain. Use `arm-zephyr-eabi-size -A build/zephyr/zephyr.elf` for section sizes.
6. **Check recursive calls** — Look for recursion in the call chain. Any recursion on embedded targets is suspect.
7. **Review stack allocation** — Check `CONFIG_MAIN_STACK_SIZE`, thread-specific `K_THREAD_STACK_DEFINE` sizes, and `CONFIG_ISR_STACK_SIZE`.

### Key Artifacts
- Thread analyzer output (serial/RTT log)
- Stack sentinel state
- `CONFIG_MAIN_STACK_SIZE`, `CONFIG_ISR_STACK_SIZE`, `K_THREAD_STACK_DEFINE` values
- GDB backtrace with frame sizes

### GDB Commands
```
info threads
thread <N>
bt full
info frame          # per-frame stack usage
p/x *(uint32_t*)<stack_bottom>  # sentinel check
```

### Escalation
- If stack usage is >80% without overflow -> recommend increasing stack size as prevention
- If overflow corrupts adjacent memory -> escalate to memory corruption analysis

---

## 3. Kernel Panic Investigation

**Entry point:** `k_panic()` or `k_oops()` backtrace in logs, or `CONFIG_RESET_ON_FATAL_ERROR` triggers reset.

### Steps
1. **Capture the panic backtrace** — Read the fatal error handler output. Identify the reason code (K_ERR_*).
2. **Identify the panic source** — Use `addr2line` to map the panic PC to source code.
3. **Check assertion context** — If triggered by `__ASSERT`, read the assertion condition and the variables involved.
4. **Analyze the calling thread** — Identify which thread hit the panic. Check its state, priority, and pending operations.
5. **Review recent kernel operations** — Check for recent k_mutex_lock, k_sem_take, k_msgq_put that might have failed.
6. **Check for ISR-context violations** — Verify the panic did not occur because a blocking call was made from ISR context.

### Key Artifacts
- Fatal error handler output with reason code
- `z_fatal_error()` backtrace
- Thread state at time of panic
- Assertion condition (if applicable)

### GDB Commands
```
bt full
info threads
thread apply all bt
p z_current_get()->base.name
p z_current_get()->base.prio
```

### Escalation
- If panic is in kernel code (not application) -> likely a Zephyr bug, check upstream issues
- If panic is intermittent -> suspect race condition, escalate to timing analysis

---

## 4. Deadlock/Timing Investigation

**Entry point:** System hangs, threads stuck in PENDING state, watchdog timeout.

### Steps
1. **Dump all thread states** — Use GDB `info threads` or Zephyr shell `kernel threads` to list all thread states.
2. **Identify blocked threads** — Find threads in PENDING state. Determine what each is waiting on (mutex, semaphore, queue).
3. **Build lock dependency graph** — For each blocked thread, identify the lock it holds and the lock it waits on. Look for cycles.
4. **Check priority inversion** — If a low-priority thread holds a lock a high-priority thread needs, check if priority inheritance is enabled (`CONFIG_PRIORITY_CEILING`).
5. **Analyze ISR latency** — If timing-related, check ISR execution time and whether ISRs are being masked too long.
6. **Check for ISR-context blocking** — Verify no thread is calling blocking APIs from ISR context (k_mutex_lock, k_sem_take with timeout, k_sleep).

### Key Artifacts
- Thread state dump (name, priority, state, stack pointer)
- Mutex ownership chain
- `CONFIG_PRIORITY_CEILING` setting
- ISR execution timing

### GDB Commands
```
info threads
thread apply all bt
p ((struct k_mutex *)<addr>)->owner
p ((struct k_mutex *)<addr>)->lock_count
p ((struct k_sem *)<addr>)->count
```

### Escalation
- If deadlock involves kernel internal locks -> likely Zephyr bug
- If timing-sensitive -> recommend adding `CONFIG_THREAD_RUNTIME_STATS` for profiling

---

## 5. Peripheral Failure Investigation

**Entry point:** `device_is_ready()` returns false, bus errors in logs, peripheral not responding.

### Steps
1. **Check device ready state** — Verify `device_is_ready()` for the peripheral's device pointer. If false, the driver init failed.
2. **Inspect DTS configuration** — Read the devicetree node for the peripheral. Verify compatible string, reg address, interrupt assignment, bus parent.
3. **Check Kconfig enablement** — Verify the driver Kconfig is enabled (e.g., `CONFIG_I2C=y`, `CONFIG_SPI=y`).
4. **Probe the bus** — For I2C: check for ACK at expected address. For SPI: verify chip select and clock. For UART: check baud rate and pin muxing.
5. **Check pin configuration** — Verify GPIO pin mux assignments in DTS match the physical board connections.
6. **Analyze clock/power domains** — Verify the peripheral's clock source is enabled and the power domain is active.
7. **Check DMA configuration** — If DMA-enabled, verify channel assignment, buffer alignment, and transfer size.

### Key Artifacts
- `device_is_ready()` return value
- Devicetree node definition (board DTS + overlay)
- Driver Kconfig options
- Bus probe results (I2C scan, SPI loopback)
- Pin mux configuration

### GDB Commands
```
p device_is_ready(DEVICE_DT_GET(DT_NODELABEL(<node>)))
p *(struct i2c_driver_data *)<device>->data
p *(struct spi_config *)<config>
```

### Escalation
- If bus probe fails at hardware level -> physical connection issue, outside software debugging scope
- If driver init succeeds but transfers fail -> suspect timing or interrupt configuration

---

## 6. Boot/MCUboot Failure Investigation

**Entry point:** Board does not reach main(), MCUboot rejects image, boot loop.

### Steps
1. **Identify boot stage** — Determine where boot stops: ROM bootloader, MCUboot, Zephyr kernel init, application main().
2. **Check MCUboot logs** — Enable `CONFIG_MCUBOOT_LOG_LEVEL_DBG` and read serial output during boot. Look for image validation errors.
3. **Inspect partition layout** — Read the partition manager output or DTS fixed-partitions. Verify slot sizes, alignment, and non-overlap.
4. **Validate image headers** — Parse MCUboot image header (magic bytes, version, flags, TLV area) to verify image integrity.
5. **Check signing** — Verify the image was signed with the correct key. Check for key mismatch between MCUboot config and signing tool.
6. **Analyze sysbuild** — For multi-image builds (nRF53), verify sysbuild dependency chain and that all images are compatible.
7. **Check DTS/Kconfig conflicts** — Compare the DTS/Kconfig between MCUboot and application. Look for partition definition mismatches.

### Key Artifacts
- MCUboot serial log output
- Partition layout from DTS `fixed-partitions`
- Image header dump (first 32 bytes of each slot)
- Signing key configuration
- `pm_static.yml` (if using partition manager)

### GDB Commands
```
# Connect before app starts (halt at reset)
monitor reset halt
x/8x 0x00000000     # vector table
x/32bx <slot0_addr> # MCUboot image header
```

### Escalation
- If MCUboot itself does not start -> suspect ROM bootloader or flash corruption
- If swap/revert loop -> check swap status bytes and image confirmation flag

---

## 7. ISR/Timing Issue Investigation

**Entry point:** Missed interrupts, jitter in periodic tasks, interrupt priority conflicts.

### Steps
1. **Map interrupt priorities** — List all configured interrupts with their priorities. Check for priority conflicts or missing preemption.
2. **Measure ISR duration** — Use GPIO toggling or cycle counter to measure actual ISR execution time.
3. **Check interrupt nesting** — Verify `CONFIG_IRQ_OFFLOAD` and nested interrupt behavior if applicable.
4. **Analyze scheduler timing** — Check time slice configuration and whether `CONFIG_TIMESLICING` is enabled.
5. **Inspect timer configuration** — Verify system tick source (SysTick, RTC, timer peripheral) and tick rate.
6. **Check for interrupt masking** — Look for long critical sections (`irq_lock()`/`irq_unlock()`) that block interrupt servicing.

### Key Artifacts
- NVIC priority registers (Cortex-M)
- ISR execution time measurements
- Scheduler timing traces
- `CONFIG_SYS_CLOCK_TICKS_PER_SEC` value

### GDB Commands
```
p/x *(uint32_t*)0xE000E400   # NVIC priority register 0
x/16x 0xE000E100             # NVIC ISER (enabled interrupts)
x/16x 0xE000E200             # NVIC ISPR (pending interrupts)
```

### Escalation
- If ISR duration exceeds 10us -> recommend deferring work to work queue
- If priority inversion suspected -> escalate to deadlock/timing analysis

---

## 8. Network Stack Failure Investigation

**Entry point:** BLE connection failure, LTE attach timeout, WiFi association failure, socket errors.

### Steps
1. **Identify protocol layer** — Determine which layer fails: physical (radio), link (MAC/L2), network (IP), transport (TCP/UDP), application.
2. **Check connection parameters** — For BLE: advertising interval, connection interval, MTU. For LTE: APN, band, PLMN. For WiFi: SSID, channel, security.
3. **Analyze state machine** — Trace the protocol state machine. Identify the last successful state and the failed transition.
4. **Check modem/radio state** — For cellular: AT command responses. For BLE: HCI event traces. For WiFi: driver state.
5. **Review socket errors** — Map errno values to specific failure conditions. Check for buffer exhaustion, connection reset, timeout.
6. **Inspect net shell output** — Use Zephyr net shell commands (`net iface`, `net stats`, `net conn`) for interface and connection state.

### Key Artifacts
- Protocol trace (BLE HCI, LTE AT commands, WiFi management frames)
- Connection parameter negotiation logs
- Socket error codes (errno values)
- Net shell output
- Radio/modem firmware version

### GDB Commands
```
p net_if_get_by_index(1)->if_dev->dev->name
p net_if_flag_is_set(net_if_get_by_index(1), NET_IF_UP)
```

### Escalation
- If radio/modem firmware suspected -> outside Zephyr scope, recommend vendor tools
- If intermittent -> recommend adding network statistics logging for pattern detection
