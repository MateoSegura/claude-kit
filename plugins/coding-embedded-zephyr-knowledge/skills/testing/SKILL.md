---
name: testing
description: Zephyr testing strategy — twister test framework, hardware-in-the-loop patterns, test pyramid, coverage analysis, and CI integration
user-invocable: false
---

# Testing Quick Reference

## Test Pyramid for Embedded

```
     /\
    /  \   E2E Tests (HIL, real hardware)
   /____\
  /      \  Integration Tests (Renode, BabbleSim)
 /________\
/__________\ Unit Tests (native_sim, ztest)
```

## Ztest Framework

```c
#include <zephyr/ztest.h>

ZTEST_SUITE(test_suite_name, NULL, NULL, NULL, NULL, NULL);

ZTEST(test_suite_name, test_function_name)
{
    zassert_equal(1 + 1, 2, "Math is broken");
    zassert_true(condition, "Condition failed");
    zassert_not_null(ptr, "Pointer is NULL");
}
```

## Twister Test Runner

**Basic usage:**

```bash
west twister -p native_sim -T tests/
```

**testcase.yaml:**

```yaml
tests:
  kernel.threads.basic:
    tags: kernel
    platform_allow: native_sim qemu_cortex_m3
    integration_platforms:
      - native_sim
```

## Coverage Analysis

```bash
west twister -p native_sim --coverage -T tests/
genhtml -o coverage build/twister-out/coverage.info
```

## Additional resources

- For testcase.yaml format, platform filters, and twister CLI reference, see [twister-reference.md](twister-reference.md)
- For hardware-in-the-loop patterns, BabbleSim BLE testing, and Renode simulation, see [hil-patterns.md](hil-patterns.md)
