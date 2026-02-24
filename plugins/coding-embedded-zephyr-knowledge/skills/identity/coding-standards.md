# Zephyr Knowledge — Coding Standards

Standards and conventions for Zephyr RTOS reference material maintained in this knowledge plugin. These apply to the content itself (accuracy, formatting, completeness), not to user code.

## Content Accuracy Requirements

- All API references must target Zephyr v3.x+ (post-LTS 3.5). Mark any pre-v3 patterns with `[DEPRECATED]`.
- Devicetree syntax must follow the Zephyr devicetree specification — compatible strings, phandle references, status properties.
- Kconfig symbols must use `CONFIG_` prefix consistently. Document dependencies (`depends on`, `select`, `imply`).
- Code examples must compile against current Zephyr. No pseudocode in API reference sections — only compilable snippets.
- Hardware register addresses and peripheral mappings must reference official vendor datasheets, not community wikis.

## Naming Conventions

- Skill directory names: lowercase, hyphen-separated, domain-scoped (e.g., `zephyr-kernel`, `hardware-nordic`, `hardware-stm32`)
- Reference file names: lowercase, hyphen-separated, descriptive (e.g., `gpio-api.md`, `spi-examples.md`, `ble-profiles.md`)
- Code identifiers in examples: follow Zephyr coding style — `snake_case` for functions and variables, `UPPER_CASE` for macros and Kconfig symbols
- Struct types: `struct k_*` for kernel objects, `struct device` for device instances

## Code Example Format

Every code example must include:
1. **Context comment** — what the example demonstrates
2. **Required headers** — `#include` directives (may be abbreviated with `// ...` for common headers)
3. **Compilable code** — actual C that would compile with Zephyr, not pseudocode
4. **Board/SoC context** — which target the example is tested against (if hardware-specific)

```c
/* Example: GPIO toggle on nRF52840-DK */
#include <zephyr/drivers/gpio.h>

#define LED0_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);

void main(void) {
    gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    while (1) {
        gpio_pin_toggle_dt(&led);
        k_msleep(500);
    }
}
```

## Devicetree Overlay Format

- Use `&node_label` syntax for references to existing nodes
- Include `status = "okay"` explicitly when enabling peripherals
- Document which SoC/board the overlay targets in a comment header
- Group related property assignments together

## Error Handling in Examples

- Always check return values from Zephyr API calls in examples
- Use `__ASSERT` for programming errors, return codes for runtime errors
- Show both the error check and the recovery/logging pattern
- Prefer `LOG_ERR` / `LOG_WRN` / `LOG_INF` over `printk` in examples

## Cross-Reference Standards

- When referencing Zephyr upstream docs, use relative paths to the Zephyr doc tree (e.g., `docs/hardware/peripherals/gpio.rst`)
- When referencing vendor datasheets, include the document number (e.g., "nRF52840 PS v1.8, Section 6.9")
- When referencing other skills in this plugin, use the skill directory name (e.g., "see `zephyr-kernel` skill")
