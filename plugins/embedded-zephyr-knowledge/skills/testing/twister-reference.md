# Twister Reference

## testcase.yaml Format

```yaml
common:
  tags: kernel
  timeout: 60
  
tests:
  kernel.semaphore:
    tags: kernel sync
    min_ram: 16
  
  kernel.mutex:
    platform_exclude: qemu_x86
    extra_configs:
      - CONFIG_TEST_EXTRA=y
```

## Twister CLI

```bash
# Run all tests for platform
west twister -p native_sim

# Specific test suite
west twister -p native_sim -T tests/kernel/semaphore

# Multiple platforms
west twister -p native_sim -p qemu_cortex_m3

# With coverage
west twister -p native_sim --coverage

# Device testing (HIL)
west twister --device-testing --device-serial /dev/ttyUSB0
```

## Harness Types

```yaml
harness: console
harness_config:
  type: multi_line
  regex:
    - "Test passed"
```
