---
name: nxp-hardware
description: NXP hardware support — i.MX RT crossover MCUs, LPC Cortex-M33, Kinetis, FlexSPI NOR boot, MCUXpresso SDK, security features (EdgeLock, HAB)
user-invocable: false
---

# NXP Quick Reference

## NXP Families

| Family | Core | Features |
|--------|------|----------|
| i.MX RT1060 | Cortex-M7 | 600MHz, FlexSPI XIP |
| LPC55S69 | Dual Cortex-M33 | TrustZone, PUF |
| Kinetis K64F | Cortex-M4 | General purpose |

## FlexSPI NOR Boot

i.MX RT devices execute code directly from external flash (XIP).

```dts
&flexspi {
    status = "okay";
    reg = <0x402a8000 0x4000>, <0x60000000 0x800000>;
    
    flash0: flash@0 {
        compatible = "nxp,imx-flexspi-nor";
        size = <DT_SIZE_M(8)>;
    };
};
```

## Debug

**J-Link:**

```bash
west flash --runner jlink
west debug --runner jlink
```

**LinkServer (MCUXpresso):**

```bash
west flash --runner linkserver
```

## Additional resources

- For NXP devicetree bindings, FlexSPI configuration, and power modes, see [nxp-reference.md](nxp-reference.md)
- For NXP-specific examples including LPC55S69 with TF-M, see [nxp-examples.md](nxp-examples.md)
