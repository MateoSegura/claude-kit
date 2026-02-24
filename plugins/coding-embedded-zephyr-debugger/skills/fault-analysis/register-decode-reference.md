# Register Decode Reference

Complete bit-field decode tables for fault registers across Cortex-M, Xtensa, and RISC-V architectures.

## Cortex-M: CFSR (0xE000ED28)

### MMFSR — MemManage Fault Status Register (CFSR bits [7:0])

| Bit | Name | Description | Common Causes | Next Step |
|-----|------|-------------|---------------|-----------|
| 0 | IACCVIOL | Instruction access violation | Executing from non-executable region, corrupted function pointer, MPU violation | Check PC in stacked frame, verify MPU regions |
| 1 | DACCVIOL | Data access violation | NULL pointer dereference, accessing MPU-protected region, stack overflow into guard region | Check MMFAR for faulting address, map to variable/region |
| 3 | MUNSTKERR | MemManage on unstacking | SP corrupted during exception return | Check SP alignment, look for stack corruption |
| 4 | MSTKERR | MemManage on stacking | SP points to invalid memory during exception entry | Likely stack overflow — SP went below stack allocation |
| 7 | MMARVALID | MMFAR holds valid address | If set, read MMFAR for exact faulting address | Always check this before reading MMFAR |

### BFSR — BusFault Status Register (CFSR bits [15:8])

| Bit | Name | Description | Common Causes | Next Step |
|-----|------|-------------|---------------|-----------|
| 8 | IBUSERR | Instruction bus error | Flash read error, executing from unmapped address | Check code region mapping, flash integrity |
| 9 | PRECISERR | Precise data bus error | Accessing unmapped peripheral, wrong register address | Check BFAR for exact address, verify peripheral base |
| 10 | IMPRECISERR | Imprecise data bus error | Write buffer error, asynchronous bus fault | BFAR invalid — check recent memory writes in code |
| 11 | UNSTKERR | BusFault on unstacking | Corrupt exception return SP | Check for stack corruption |
| 12 | STKERR | BusFault on stacking | SP in invalid bus region during exception | Stack pointer corruption or overflow |
| 13 | LSPERR | Lazy FP stacking error | FP context save to invalid address | Check SP when FPU context was last used |
| 15 | BFARVALID | BFAR holds valid address | Only valid for precise errors | Check before reading BFAR |

### UFSR — UsageFault Status Register (CFSR bits [31:16])

| Bit | Name | Description | Common Causes | Next Step |
|-----|------|-------------|---------------|-----------|
| 16 | UNDEFINSTR | Undefined instruction | Corrupted code, ARM/Thumb mode mismatch, missing ISA extension | Check instruction at PC, verify Thumb bit in LR |
| 17 | INVSTATE | Invalid execution state | BX to address with bit[0]=0 (ARM mode on Cortex-M) | Check function pointer or LR value — bit 0 must be 1 |
| 18 | INVPC | Invalid PC load | Bad EXC_RETURN value, corrupted exception frame | Check LR value during exception return |
| 19 | NOCP | No coprocessor | FPU instruction without FPU enabled | Check CONFIG_FPU=y and SCB->CPACR |
| 24 | UNALIGNED | Unaligned access | Unaligned load/store with CONFIG_ARMV7_M_ARMV8_M_FP | Enable CONFIG_CORTEX_M_ALLOW_UNALIGNED or fix alignment |
| 25 | DIVBYZERO | Division by zero | Integer divide by zero (only faults if SCB->CCR.DIV_0_TRP=1) | Check divisor source, add zero-check |

## Cortex-M: HFSR (0xE000ED2C)

| Bit | Name | Description | Common Causes |
|-----|------|-------------|---------------|
| 1 | VECTTBL | Vector table read error | Flash corruption, wrong VTOR base |
| 30 | FORCED | Forced hard fault | Configurable fault escalated (MemManage/BusFault/UsageFault handler not enabled) |
| 31 | DEBUGEVT | Debug event fault | Breakpoint/watchpoint when debug not connected |

When FORCED=1, always check CFSR for the underlying cause. The hard fault handler was invoked because the specific fault handler was disabled or the specific fault handler itself faulted.

## Cortex-M: DFSR (0xE000ED30)

| Bit | Name | Description |
|-----|------|-------------|
| 0 | HALTED | Halt requested by debug |
| 1 | BKPT | BKPT instruction executed |
| 2 | DWTTRAP | Data watchpoint trap |
| 3 | VCATCH | Vector catch triggered |
| 4 | EXTERNAL | External debug event |

## Xtensa: EXCCAUSE Complete Table

| Value | Name | Description | Common Cause |
|-------|------|-------------|-------------|
| 0 | IllegalInstructionCause | Illegal instruction | Corrupted code, wrong ISA config |
| 1 | SyscallCause | SYSCALL instruction | Intentional system call |
| 2 | InstructionFetchErrorCause | Instruction fetch error on address | Bad PC, flash read error |
| 3 | LoadStoreErrorCause | Load/store error on address | Invalid memory region |
| 4 | Level1InterruptCause | Level-1 interrupt | Normal interrupt (not a fault) |
| 5 | AllocaCause | MOVSP used with non-contiguous register window | Window overflow/underflow |
| 6 | IntegerDivideByZeroCause | Integer divide by zero | Missing zero-check |
| 9 | LoadStoreAlignmentCause | Unaligned load/store | Misaligned pointer |
| 12 | InstrPIFDataErrorCause | PIF data error on instruction fetch | Bus error |
| 13 | LoadStorePIFDataErrorCause | PIF data error on load/store | Bus error |
| 14 | InstrPIFAddrErrorCause | PIF address error on instruction fetch | Out-of-range address |
| 15 | LoadStorePIFAddrErrorCause | PIF address error on load/store | Out-of-range address |
| 20 | InstFetchProhibitedCause | Instruction fetch prohibited by PMS/MPU | Code execution from data region |
| 24 | LoadProhibitedCause | Load prohibited by PMS/MPU | Read from protected region |
| 26 | IntegerDivideByZeroCause (alt) | Division by zero (alternate encoding) | Some Xtensa variants use this |
| 28 | LoadProhibitedCause (alt) | Load prohibited (alternate) | ESP32 specific |
| 29 | StoreProhibitedCause | Store prohibited by PMS/MPU | Write to protected region |

Note: EXCVADDR (special register 238) contains the virtual address that caused exceptions 2, 3, 9, 20, 24, 28, 29.

## RISC-V: mcause Exception Codes

| Value | Name | Description | Common Cause |
|-------|------|-------------|-------------|
| 0 | Instruction address misaligned | PC not aligned to instruction boundary | Bad function pointer, corrupted return address |
| 1 | Instruction access fault | No permission to fetch instruction | MPU/PMP violation, invalid code address |
| 2 | Illegal instruction | Undefined or privileged instruction | Wrong ISA extension, code corruption |
| 3 | Breakpoint | EBREAK instruction | Debug breakpoint |
| 4 | Load address misaligned | Unaligned load | Misaligned pointer |
| 5 | Load access fault | No permission to read | PMP violation, invalid address |
| 6 | Store/AMO address misaligned | Unaligned store or atomic | Misaligned write pointer |
| 7 | Store/AMO access fault | No permission to write | PMP violation, read-only region |
| 8 | Environment call from U-mode | ECALL from user mode | System call |
| 9 | Environment call from S-mode | ECALL from supervisor mode | System call |
| 11 | Environment call from M-mode | ECALL from machine mode | System call |
| 12 | Instruction page fault | Page fault on fetch | Virtual memory only |
| 13 | Load page fault | Page fault on load | Virtual memory only |
| 15 | Store/AMO page fault | Page fault on store | Virtual memory only |

Note: mtval (mstatus) contains the faulting address or instruction value depending on the exception type.

## Stacked Exception Frame (Cortex-M)

When a fault occurs, the processor automatically pushes 8 registers to the stack:

| Offset | Register | Notes |
|--------|----------|-------|
| SP+0x00 | R0 | First argument |
| SP+0x04 | R1 | Second argument |
| SP+0x08 | R2 | Third argument |
| SP+0x0C | R3 | Fourth argument |
| SP+0x10 | R12 | Scratch register |
| SP+0x14 | LR | Return address (caller) |
| SP+0x18 | PC | **Faulting instruction address** |
| SP+0x1C | xPSR | Program status (includes Thumb bit) |

If FPU is active and lazy stacking is enabled, an additional 18 words (S0-S15, FPSCR, reserved) are pushed.

To read the stacked frame in GDB:
```
x/8x $sp        # If in handler mode
x/8x $psp       # If fault was in thread mode (common for Zephyr)
```

The PC value at SP+0x18 is the most critical — use `addr2line -e build/zephyr/zephyr.elf <PC>` to find the faulting source line.
