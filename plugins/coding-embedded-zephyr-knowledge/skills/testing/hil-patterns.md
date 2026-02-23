# Hardware-in-the-Loop Testing

Patterns and configuration for testing Zephyr applications on real hardware and hardware simulators using the twister test framework.

## Device Testing with Twister

### Basic Device Test

```bash
# Run tests on a physical board connected via serial
west twister --device-testing \
  --device-serial /dev/ttyUSB0 \
  -p nrf52840dk/nrf52840 \
  -T tests/subsys/logging/
```

### Multiple Devices

```bash
# Hardware map for multi-device testing
west twister --device-testing \
  --hardware-map hardware-map.yaml \
  -T tests/
```

**hardware-map.yaml:**

```yaml
- platform: nrf52840dk/nrf52840
  id: "000683424571"
  serial: /dev/ttyACM0
  runner: jlink
- platform: nucleo_h743zi
  id: "066DFF555654"
  serial: /dev/ttyACM1
  runner: openocd
```

## Serial Console Harness

The console harness captures serial output and matches against expected patterns.

### Single-Line Match

```yaml
harness: console
harness_config:
  type: one_line
  regex:
    - "PROJECT EXECUTION SUCCESSFUL"
```

### Multi-Line Match (Ordered)

```yaml
harness: console
harness_config:
  type: multi_line
  ordered: true
  regex:
    - "Initializing BLE stack"
    - "Advertising started"
    - "Connected to peer"
```

### Custom Timeout

```yaml
harness: console
harness_config:
  type: one_line
  regex:
    - "Test completed"
  timeout: 120  # seconds — default is 60
```

## BabbleSim BLE Testing

BabbleSim provides a simulated BLE physical layer for testing multi-device BLE scenarios without hardware.

### Build for BLE Simulation

```bash
# Build the BLE test for nrf52_bsim (BabbleSim target)
west build -b nrf52_bsim tests/bluetooth/bsim_bt/bsim_test_audio
```

### Run BabbleSim Tests

```bash
# Run with twister (auto-manages BabbleSim processes)
west twister -p nrf52_bsim -T tests/bluetooth/bsim_bt/

# Or manually with BabbleSim scripts
cd ${BSIM_OUT_PATH}/bin
./bs_nrf52_bsim_tests_bluetooth_bsim_bt_bsim_test_advx \
  -s=tests_bluetooth_bsim_bt_bsim_test_advx -d=0 &
./bs_2G4_phy_v1 -s=tests_bluetooth_bsim_bt_bsim_test_advx -D=1 -sim_length=10e6
```

### BabbleSim Prerequisites

```bash
# Set environment variable pointing to BabbleSim build output
export BSIM_OUT_PATH=/path/to/bsim/out
# BabbleSim must be built separately — see ext/hal_nordic/nrf_802154/driver/
```

## Renode Simulation

Renode provides full SoC simulation for testing without physical hardware.

### Twister with Renode

```yaml
# testcase.yaml
platform_allow: renode_cortex_m3
harness: renode
```

```bash
west twister -p renode_cortex_m3 -T tests/kernel/
```

### Custom Renode Script

```yaml
harness: renode
harness_config:
  renode_script: custom_platform.resc
```

### Renode Robot Framework Integration

```bash
# Run Renode tests with Robot Framework assertions
renode-test tests/test_suite.robot
```

## QEMU vs Hardware Test Matrix

| Feature | QEMU/native_sim | Renode | BabbleSim | Physical HW |
|---------|-----------------|--------|-----------|-------------|
| Kernel tests | Yes | Yes | No | Yes |
| Driver tests | Partial (stubs) | Yes (emulated) | No | Yes |
| BLE tests | No | Partial | Yes | Yes |
| Timing accuracy | Low | Medium | Medium | High |
| CI-friendly | Yes | Yes | Yes | Needs runner |
| Setup complexity | None | Low | Medium | High |

## Test Isolation Best Practices

- Use `CONFIG_TEST=y` to enable test-specific Kconfig overrides
- Prefer `ztest_new_suite` with `before`/`after` hooks for setup/teardown
- For HIL tests, add `slow` tag to `testcase.yaml` so CI can filter them:
  ```yaml
  tags: slow hardware-required
  ```
- Reset peripheral state between test cases using device PM API or explicit re-init
- Use unique serial patterns per test case to avoid cross-test regex matches
