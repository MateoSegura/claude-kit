---
name: embedded-zephyr-debugger:fault-analysis
description: "Fault register decode reference and stack overflow analysis patterns for Cortex-M (CFSR/HFSR/MMFAR/BFAR), Xtensa (EXCCAUSE), and RISC-V (mcause) architectures. Quick reference for identifying hard fault types, memory access violations, and stack overflow conditions in Zephyr RTOS firmware."
user-invocable: false
---

# Fault Analysis Quick Reference

Rapid fault type identification from register values. Use this to decode fault registers and classify the failure before deep investigation.

## Cortex-M Fault Register Map

| Register | Address | Purpose |
|----------|---------|---------|
| CFSR | `0xE000ED28` | Combined: MMFSR[7:0] + BFSR[15:8] + UFSR[31:16] |
| HFSR | `0xE000ED2C` | Hard Fault Status — escalation and vector table errors |
| MMFAR | `0xE000ED34` | MemManage Fault Address (valid when MMFSR.MMARVALID=1) |
| BFAR | `0xE000ED38` | BusFault Address (valid when BFSR.BFARVALID=1) |
| DFSR | `0xE000ED30` | Debug Fault Status |

## Quick Decision Tree

```
Fault handler entered
├── HFSR.FORCED=1 → Escalated fault, check CFSR
│   ├── CFSR[7:0] non-zero → MemManage fault
│   │   ├── MMFSR.IACCVIOL → Instruction access violation (bad PC)
│   │   ├── MMFSR.DACCVIOL → Data access violation (bad pointer)
│   │   └── MMFSR.MSTKERR → Stacking error (stack pointer corrupt)
│   ├── CFSR[15:8] non-zero → BusFault
│   │   ├── BFSR.PRECISERR → Precise bus error (BFAR valid)
│   │   ├── BFSR.IMPRECISERR → Imprecise bus error (BFAR invalid)
│   │   └── BFSR.STKERR → Stacking bus error
│   └── CFSR[31:16] non-zero → UsageFault
│       ├── UFSR.UNDEFINSTR → Undefined instruction
│       ├── UFSR.INVSTATE → Invalid execution state (Thumb bit)
│       ├── UFSR.INVPC → Invalid PC load
│       ├── UFSR.NOCP → Coprocessor access (FPU not enabled?)
│       ├── UFSR.UNALIGNED → Unaligned access
│       └── UFSR.DIVBYZERO → Division by zero
├── HFSR.VECTTBL=1 → Vector table read error (flash corruption?)
└── CFSR=0, HFSR=0 → Check for NMI, debug fault, or non-ARM fault source
```

## Xtensa Quick Reference

| EXCCAUSE | Name | Common Cause |
|----------|------|-------------|
| 0 | IllegalInstruction | Corrupted code, bad function pointer |
| 2 | InstructionFetchError | Code execution from invalid address |
| 3 | LoadStoreError | Unaligned or invalid memory access |
| 6 | IntegerDivideByZero | Division by zero |
| 20 | InstFetchProhibited | MPU/PMS code access violation |
| 28 | LoadProhibited | MPU/PMS read violation |
| 29 | StoreProhibited | MPU/PMS write violation |

## RISC-V Quick Reference

| mcause | Name | Common Cause |
|--------|------|-------------|
| 0 | Instruction address misaligned | Bad function pointer |
| 1 | Instruction access fault | Code at invalid address |
| 2 | Illegal instruction | Corrupted code, wrong ISA extension |
| 4 | Load address misaligned | Unaligned read |
| 5 | Load access fault | Read from invalid address |
| 6 | Store address misaligned | Unaligned write |
| 7 | Store access fault | Write to invalid/protected address |

## Stack Overflow Quick Check

```
Stack overflow suspected?
├── Check sentinel: p/x *(uint32_t*)<stack_bottom>
│   ├── 0xAAAAAAAA → Sentinel intact, probably not stack overflow
│   └── Other value → Sentinel corrupted, stack overflow confirmed
├── Check CONFIG_MPU_STACK_GUARD
│   ├── Enabled + MemManage fault at stack boundary → MPU caught overflow
│   └── Not enabled → No hardware protection, rely on sentinel
└── Check thread analyzer: CONFIG_THREAD_ANALYZER=y
    └── Usage >90% → At risk even if not overflowed yet
```

## Additional Resources
- For complete CFSR/HFSR/DFSR bit-field tables, Xtensa EXCCAUSE values 0-39, and RISC-V mcause codes, see [register-decode-reference.md](register-decode-reference.md)
- For stack sentinel detection, thread analyzer usage, and sizing methodology, see [stack-overflow-patterns.md](stack-overflow-patterns.md)
