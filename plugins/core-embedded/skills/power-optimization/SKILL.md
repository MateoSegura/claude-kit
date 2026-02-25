---
name: core-embedded:power-optimization
description: "Embedded power optimization — sleep modes, wake sources, clock gating, voltage scaling, duty cycling, power state machines, and battery monitoring"
user-invocable: false
---

# Power Optimization Quick Reference

## Power Budget Fundamentals

Power consumption in embedded systems comes from three sources:

- **Dynamic power**: Proportional to clock frequency and voltage squared (P = C * V^2 * f)
- **Leakage current**: Always present, increases with temperature
- **Peripheral power**: External sensors, radios, displays, actuators

### Typical Current Ranges

| State | Cortex-M0/M0+ | Cortex-M4 | Cortex-M33 |
|-------|---------------|-----------|------------|
| Active (full speed) | 3-10 mA | 10-30 mA | 10-20 mA |
| Sleep (CPU halted) | 0.5-2 mA | 1-5 mA | 0.5-3 mA |
| Deep sleep | 1-10 uA | 2-20 uA | 1-10 uA |
| Shutdown/off | 10-100 nA | 20-500 nA | 10-100 nA |

## Sleep Modes

### Mode Hierarchy

```
Active
  |  CPU running, all peripherals available
  v
Idle / Sleep
  |  CPU halted, peripherals running, SRAM retained
  |  Wake: any interrupt
  v
Deep Sleep / Stop
  |  CPU halted, most clocks stopped, SRAM retained
  |  Wake: RTC, GPIO, LPUART, specific interrupts
  v
Standby
  |  Most SRAM lost, minimal logic powered
  |  Wake: RTC, wakeup pin, watchdog
  v
Shutdown / Off
     Lowest power, all state lost except backup registers
     Wake: wakeup pin, RTC (if backup domain powered)
```

### Mode Selection Guide

| Mode | Wake Latency | RAM Retained | Use Case |
|------|-------------|-------------|----------|
| Idle | < 1 us | All | Waiting for next interrupt in active processing |
| Deep sleep | 1-10 us | All | Between periodic sensor readings (seconds) |
| Standby | 1-10 ms | Backup only | Long idle periods (minutes to hours) |
| Shutdown | 10-100 ms | None | Ultra-low-power storage, wake on external event |

## Wake Sources

### Common Wake Sources by Mode

| Wake Source | Idle | Deep Sleep | Standby | Shutdown |
|-------------|------|-----------|---------|----------|
| Any interrupt | Yes | - | - | - |
| GPIO edge | Yes | Yes | Pin-specific | Pin-specific |
| RTC alarm | Yes | Yes | Yes | Yes (if powered) |
| UART receive | Yes | LP-UART only | - | - |
| Watchdog | Yes | Yes | Yes | - |
| Comparator | Yes | Yes | Board-specific | - |
| Timer | Yes | LP-timer only | - | - |

### Wake Pin Configuration

- Configure wake pins before entering low-power mode
- Set proper pull-up/pull-down to avoid floating inputs drawing current
- Debounce external signals to prevent spurious wakes
- Clear pending interrupt flags before entering sleep

## Peripheral Clock Gating

Disable clocks to unused peripherals to reduce dynamic power.

### Strategy

```
Boot:
  1. Enable only essential clocks (core, memory controller)
  2. Enable peripheral clock only when needed
  3. Disable peripheral clock after use

Example flow:
  enable_clock(SPI1)
  spi_transfer(...)
  disable_clock(SPI1)    /* Saves power between transfers */
```

### Guidelines

- Disable clocks to unused GPIOs, timers, ADCs, communication peripherals
- Check if peripheral retains configuration when clock is gated (varies by MCU)
- Some peripherals require re-initialization after clock gate — check datasheet
- Group peripheral usage to minimize clock enable/disable transitions

## Voltage Scaling

Lower supply voltage reduces dynamic power quadratically but limits maximum clock frequency.

### Voltage/Frequency Tradeoff

| Voltage Range | Max Frequency (typical) | Power Savings |
|---------------|------------------------|---------------|
| Range 1 (high) | 80-170 MHz | Baseline |
| Range 2 (medium) | 26-80 MHz | ~30-50% |
| Range 3 (low) | 2-26 MHz | ~50-70% |

### Dynamic Voltage and Frequency Scaling (DVFS)

```
High workload  --> Range 1 (high voltage, high frequency)
Medium workload --> Range 2 (medium voltage, medium frequency)
Low workload   --> Range 3 (low voltage, low frequency)
Idle           --> Sleep mode
```

- Transition takes time (voltage regulator settling: 1-50 us)
- Plan transitions during idle periods to hide latency
- Never exceed maximum frequency for current voltage range

## Duty Cycling

The most effective power reduction strategy: spend most time in low-power mode, wake briefly to do work.

### Periodic Sensing Pattern

```
  Active     Sleep          Active     Sleep
|--50ms--|---9.95s--------|--50ms--|---9.95s--------|

Avg current = (I_active * t_active + I_sleep * t_sleep) / t_total
            = (10mA * 50ms + 5uA * 9950ms) / 10000ms
            = (0.5 + 0.05) / 10
            = 55 uA average
```

### Duty Cycle Optimization

| Optimization | Effect |
|-------------|--------|
| Reduce active time | Faster processing, DMA, pre-computed tables |
| Increase sleep time | Less frequent sensing/reporting |
| Use deeper sleep | Lower sleep current |
| Batch operations | Combine multiple tasks in single wake cycle |
| Local processing | Filter/aggregate locally, transmit less often |

## Power State Machine

### Design Pattern

```
                  +----------+
         init --> | STARTUP  |
                  +----------+
                       |
                       v
  timeout/      +-----------+      work request
  idle -------> |   SLEEP   | <------- done
  |             +-----------+
  |                  |
  |            wake event
  |                  |
  |                  v
  |             +-----------+
  +------------ |  ACTIVE   |
                +-----------+
                     |
               critical event
                     |
                     v
                +-----------+
                |  ALERT    |  (high power, max performance)
                +-----------+
```

### Implementation Guidelines

- Define explicit states with entry/exit actions
- Entry action: enable clocks, configure peripherals, restore context
- Exit action: save context, disable peripherals, gate clocks
- Track time-in-state for power profiling
- Implement graceful transitions (don't sleep while UART TX is in progress)

## Battery Monitoring

### Measurement Techniques

| Method | Accuracy | Complexity | Notes |
|--------|----------|-----------|-------|
| ADC voltage | Medium | Low | Needs voltage divider, affected by load |
| Coulomb counting | High | High | Integrates current over time, needs calibration |
| Fuel gauge IC | High | Medium | Dedicated chip (MAX17048, BQ27441) |
| OCV lookup table | Medium | Low | Open-circuit voltage vs SoC curve |

### Voltage-Based Estimation

```c
/* Simple battery percentage from voltage (LiPo example) */
uint8_t battery_percent(uint16_t mv) {
    if (mv >= 4200) return 100;
    if (mv >= 4050) return 90;
    if (mv >= 3900) return 75;
    if (mv >= 3800) return 55;
    if (mv >= 3700) return 30;
    if (mv >= 3600) return 15;
    if (mv >= 3500) return 5;
    return 0;
}
```

### Low-Battery Handling

- Define threshold levels: warning (20%), critical (10%), shutdown (5%)
- At warning: reduce duty cycle, disable non-essential features
- At critical: transmit final status, save persistent state
- At shutdown: enter lowest power mode, configure wake on charger detect

### Measurement Best Practices

- Measure during idle periods (avoid load-dependent voltage sag)
- Average multiple ADC samples to reduce noise
- Account for battery internal resistance at high loads
- Temperature-compensate the voltage-to-SoC curve

## Additional Resources

- For detailed power profiling methodology, sleep mode configuration examples, and battery management patterns, see [power-reference.md](power-reference.md)
