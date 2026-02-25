# Power Optimization — Complete Reference

## Power Profiling Methodology

### Measurement Setup

| Tool | Accuracy | Sampling Rate | Use Case |
|------|----------|--------------|----------|
| Multimeter (DC) | High | Manual | Average current measurement |
| Current probe + scope | Medium | MHz | Transient capture, mode transitions |
| Power profiler (Nordic PPK2, Joulescope) | High | 100 kHz+ | Full power profile with timestamps |
| Shunt resistor + ADC | Medium | Variable | Self-profiling in firmware |
| INA219/INA226 module | High | Up to 1 kHz | Low-cost automated profiling |

### Profiling Procedure

1. **Establish baseline** — Measure current in known states (active, idle, sleep)
2. **Profile transitions** — Capture mode entry/exit timing and energy cost
3. **Measure worst case** — Run maximum workload scenario
4. **Calculate budget** — Compare against battery capacity or power supply limit
5. **Optimize and re-measure** — Iterate on the highest-cost operations

### Energy Budget Calculation

```
Battery life = Battery capacity (mAh) / Average current (mA)

Example:
  Battery: 230 mAh (CR2032)
  Duty cycle: 50 ms active at 10 mA, 9.95 s sleep at 3 uA

  Avg current = (10 * 0.05 + 0.003 * 9.95) / 10 = 0.053 mA = 53 uA
  Battery life = 230 / 0.053 = 4340 hours ≈ 181 days

  With self-discharge (~1% / month for CR2032):
  Effective life ≈ 150 days
```

## Sleep Mode Configuration

### Entry Checklist

Before entering any low-power mode:

1. **Complete pending I/O** — Wait for UART TX complete, SPI transfer done
2. **Flush buffers** — Log buffers, DMA buffers
3. **Save volatile state** — Any data that will be lost in deeper modes
4. **Configure wake sources** — RTC alarm, GPIO interrupt, LPUART
5. **Disable unused peripherals** — Gate clocks, disable power domains
6. **Clear pending interrupts** — Avoid immediate wake from stale flags
7. **Set wake-up flag** — Enable EXTI lines, RTC alarm interrupt

### Exit Sequence

After waking from low-power mode:

1. **Reconfigure clocks** — PLL may need relock after deep sleep
2. **Re-enable peripherals** — Restore clock gates, peripheral config
3. **Check wake source** — Determine why we woke up
4. **Restore state** — Reload saved context if needed
5. **Resume operation** — Continue from where work was suspended

### Sleep Mode Energy Comparison

For a periodic sensing application:

```
Option A: Sleep mode (1 mA idle, 1 us wake)
  Active: 10 mA * 50 ms = 0.5 mA·ms
  Sleep:  1 mA * 9950 ms = 9950 mA·ms
  Total per cycle: 9950.5 mA·ms
  Average: 995 uA

Option B: Deep sleep (5 uA idle, 5 us wake)
  Active: 10 mA * 50 ms = 0.5 mA·ms
  Sleep:  0.005 mA * 9950 ms = 49.75 mA·ms
  Wake penalty: 10 mA * 0.005 ms = 0.05 mA·ms
  Total per cycle: 50.3 mA·ms
  Average: 5.03 uA  <-- 200x improvement

Option C: Standby (0.5 uA idle, 5 ms wake)
  Active: 10 mA * 50 ms = 0.5 mA·ms
  Sleep:  0.0005 mA * 9950 ms = 4.975 mA·ms
  Wake penalty: 10 mA * 5 ms = 50 mA·ms
  Total per cycle: 55.475 mA·ms
  Average: 5.55 uA  <-- wake penalty offsets sleep savings
```

Key insight: deeper sleep saves less if wake penalty is significant relative to sleep duration.

## Clock Optimization

### Clock Tree Strategy

```
Boot:
  HSI (internal RC) → stable in microseconds, moderate power

Active processing:
  HSE (external crystal) → PLL → high frequency
  Enable only needed bus clocks (AHB, APB1, APB2)

Low-power active:
  MSI (multi-speed internal) → lower frequency, lower power
  Reduce APB dividers

Sleep:
  LSE (32.768 kHz crystal) → RTC, LPTIM
  All other clocks gated
```

### Clock Switching Patterns

```c
/* Pseudo-code: switch between high and low performance */

void enter_high_performance(void) {
    enable_hse();
    configure_pll(/* target MHz */);
    wait_pll_lock();
    switch_sysclk_to_pll();
    set_voltage_range(RANGE_HIGH);
}

void enter_low_power_run(void) {
    switch_sysclk_to_msi(/* 2 MHz */);
    disable_pll();
    disable_hse();
    set_voltage_range(RANGE_LOW);
}
```

### Peripheral Clock Gating Examples

```c
/* Enable before use, disable after */
void spi_transfer_with_clock_mgmt(uint8_t *data, size_t len) {
    enable_peripheral_clock(SPI1_CLK);

    spi_configure(SPI1, &config);
    spi_transfer(SPI1, data, len);
    spi_wait_complete(SPI1);

    disable_peripheral_clock(SPI1_CLK);
}
```

## Peripheral Power Domains

### Power Domain Hierarchy

```
Always-on domain
├── Backup registers
├── RTC
├── LSE oscillator
└── Wakeup logic

Core domain (off in standby)
├── CPU
├── SRAM
├── Flash
└── DMA

Peripheral domain (gated per-peripheral)
├── UART1, UART2, ...
├── SPI1, SPI2, ...
├── I2C1, I2C2, ...
├── ADC, DAC
├── Timer1, Timer2, ...
└── USB, CAN, ...
```

### SRAM Retention

Some MCUs allow partial SRAM power-down:

```
Full SRAM retention:  moderate current (e.g., 5 uA)
Partial retention:    lower current (e.g., 2 uA, retain first 32 KB only)
No retention:         lowest current (e.g., 0.3 uA, all SRAM lost)
```

Strategy: Place critical state in the retained SRAM region, reconstruct the rest on wake.

## Duty Cycling Patterns

### Adaptive Duty Cycling

Adjust the sensing interval based on observed data:

```c
#define MIN_INTERVAL_MS    1000
#define MAX_INTERVAL_MS   60000
#define THRESHOLD          5      /* units of change */

static uint32_t interval_ms = MIN_INTERVAL_MS;
static int16_t last_value;

void adaptive_sense(void) {
    int16_t current = read_sensor();
    int16_t delta = abs(current - last_value);

    if (delta > THRESHOLD) {
        /* Rapid change — increase sample rate */
        interval_ms = MAX(interval_ms / 2, MIN_INTERVAL_MS);
    } else {
        /* Stable — decrease sample rate */
        interval_ms = MIN(interval_ms * 2, MAX_INTERVAL_MS);
    }

    last_value = current;
    set_wakeup_timer(interval_ms);
    enter_deep_sleep();
}
```

### Event-Driven Wake

Instead of periodic polling, wake only on external events:

```c
/* Configure GPIO interrupt for sensor data-ready pin */
configure_gpio_interrupt(SENSOR_DRDY_PIN, EDGE_RISING);

/* Configure sensor for threshold-based alerting */
sensor_set_threshold(TEMP_SENSOR, UPPER_LIMIT, LOWER_LIMIT);

/* Sleep until sensor triggers */
enter_deep_sleep();

/* ISR wakes system, processes alert */
void sensor_alert_isr(void) {
    signal_processing_task();
}
```

### Batched Communication

Reduce radio-on time by batching multiple readings:

```c
#define BATCH_SIZE  10
static struct reading batch[BATCH_SIZE];
static int batch_count = 0;

void on_sensor_reading(struct reading *r) {
    batch[batch_count++] = *r;

    if (batch_count >= BATCH_SIZE) {
        /* Power on radio, send all readings, power off radio */
        radio_power_on();
        transmit_batch(batch, batch_count);
        radio_power_off();
        batch_count = 0;
    }
}
```

## Power State Machine Implementation

### State Table Pattern

```c
typedef enum {
    PWR_STATE_ACTIVE,
    PWR_STATE_IDLE,
    PWR_STATE_DEEP_SLEEP,
    PWR_STATE_STANDBY,
} pwr_state_t;

typedef struct {
    void (*enter)(void);
    void (*exit)(void);
    pwr_state_t (*check_transition)(void);
} pwr_state_handler_t;

static const pwr_state_handler_t state_table[] = {
    [PWR_STATE_ACTIVE] = {
        .enter = active_enter,
        .exit = active_exit,
        .check_transition = active_check,
    },
    [PWR_STATE_IDLE] = {
        .enter = idle_enter,
        .exit = idle_exit,
        .check_transition = idle_check,
    },
    [PWR_STATE_DEEP_SLEEP] = {
        .enter = deep_sleep_enter,
        .exit = deep_sleep_exit,
        .check_transition = deep_sleep_check,
    },
    [PWR_STATE_STANDBY] = {
        .enter = standby_enter,
        .exit = standby_exit,
        .check_transition = standby_check,
    },
};

void power_manager_run(void) {
    pwr_state_t new_state = state_table[current_state].check_transition();
    if (new_state != current_state) {
        state_table[current_state].exit();
        state_table[new_state].enter();
        current_state = new_state;
    }
}
```

### Transition Rules

```
Active → Idle:       No pending work, idle timeout elapsed
Idle → Deep Sleep:   No active peripherals, longer idle expected
Deep Sleep → Standby: Extended inactivity, non-critical data can be lost
Any → Active:        Wake event, work request, interrupt
```

## Battery Technology Reference

### Common Battery Chemistries

| Chemistry | Nominal V | Capacity Range | Self-Discharge | Rechargeable |
|-----------|-----------|---------------|----------------|-------------|
| CR2032 (LiMnO2) | 3.0 V | 220-240 mAh | ~1%/month | No |
| CR123A | 3.0 V | 1500 mAh | ~1%/month | No |
| AA Alkaline | 1.5 V | 2500-3000 mAh | ~5%/year | No |
| LiPo | 3.7 V | 100-10000 mAh | ~3%/month | Yes |
| LiFePO4 | 3.2 V | 500-3000 mAh | ~3%/month | Yes |
| NiMH AA | 1.2 V | 2000-2800 mAh | ~20%/month | Yes |

### LiPo Voltage-to-SoC Curve

```
Voltage (V)   SoC (%)
  4.20          100
  4.15           95
  4.05           85
  3.97           75
  3.87           60
  3.80           50
  3.72           35
  3.63           20
  3.50           10
  3.40            5
  3.00            0  (cutoff — do not discharge below this)
```

Note: This curve shifts significantly under load and temperature variation.

### Coin Cell Limitations

CR2032 constraints for IoT applications:

- **Peak current**: 15-25 mA max (internal resistance ~15-40 ohm)
- **Pulse current**: Short bursts (< 50 ms) can exceed steady-state limit
- **Temperature**: Capacity drops 20-40% at -20 C
- **Voltage sag**: Under 10 mA load, voltage may drop to 2.7 V
- **Longevity**: Plan for 5+ year shelf life applications

Design strategy for coin cell: buffer with a capacitor (100 uF - 1 mF) for current peaks during radio TX.
