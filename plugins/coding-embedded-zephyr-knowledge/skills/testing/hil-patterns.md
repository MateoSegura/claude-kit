# Hardware-in-the-Loop Testing

## Device Testing Flag

```bash
west twister --device-testing --device-serial /dev/ttyUSB0 -p nrf52840dk_nrf52840
```

## Serial Harness

```yaml
harness: console
harness_config:
  type: one_line
  regex:
    - "PROJECT EXECUTION SUCCESSFUL"
```

## BabbleSim BLE Testing

```bash
# Build for BLE simulation
west build -b nrf52_bsim tests/bluetooth/bsim_bt/
```

## Renode Simulation

```yaml
platform_allow: renode_cortex_m3
harness: renode
```

**Run:**

```bash
west twister -p renode_cortex_m3 -T tests/
```
