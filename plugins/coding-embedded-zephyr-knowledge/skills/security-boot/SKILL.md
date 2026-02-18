---
name: coding-embedded-zephyr-knowledge:security-boot
description: Secure boot chain with MCUboot bootloader, TF-M trusted execution, and PSA Crypto — sysbuild configuration, image signing, and secure partitions
user-invocable: false
---

# Secure Boot Quick Reference

## Secure Boot Chain Overview

**Modern Zephyr secure boot uses sysbuild** to orchestrate multiple images:

1. **MCUboot** — Bootloader with image verification
2. **TF-M** (optional, Cortex-M33+) — Trusted Firmware-M for secure partitions
3. **Application** — Your firmware (non-secure world if using TF-M)

**Critical:** All secure boot configurations require sysbuild. Do NOT use standalone MCUboot builds.

## MCUboot with Sysbuild

### Minimal Configuration

**sysbuild.conf** (in project root, NOT in app directory):

```kconfig
SB_CONFIG_BOOTLOADER_MCUBOOT=y
```

**prj.conf** (application):

```kconfig
CONFIG_BOOTLOADER_MCUBOOT=y
```

**Build:**

```bash
west build -b nrf52840dk_nrf52840 --sysbuild
west flash
```

### Image Signing

**Generate signing key:**

```bash
west build -t mcuboot_sign_key
# Creates mcuboot_private.pem and mcuboot_public.pem
```

**Specify key in sysbuild:**

```kconfig
# sysbuild.conf
SB_CONFIG_BOOTLOADER_MCUBOOT=y
SB_CONFIG_MCUBOOT_SIGNATURE_KEY_FILE="bootloader/mcuboot/root-rsa-2048.pem"
```

**Signing happens automatically during build.**

### Flash Partition Layout

**DTS overlay** (e.g., `boards/nrf52840dk_nrf52840.overlay`):

```dts
&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;

        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x00000000 0x0000C000>;  /* 48 KB */
        };
        slot0_partition: partition@c000 {
            label = "image-0";
            reg = <0x0000C000 0x00076000>;  /* 472 KB */
        };
        slot1_partition: partition@82000 {
            label = "image-1";
            reg = <0x00082000 0x00076000>;  /* 472 KB */
        };
        storage_partition: partition@f8000 {
            label = "storage";
            reg = <0x000f8000 0x00008000>;  /* 32 KB */
        };
    };
};

/ {
    chosen {
        zephyr,code-partition = &slot0_partition;
    };
};
```

**Layout:**
- **boot_partition** — MCUboot bootloader
- **slot0_partition** — Primary application image
- **slot1_partition** — Secondary image (for DFU)
- **storage_partition** — Settings, filesystem

## Upgrade Modes

### Swap (Default)

**Behavior:**
1. New image written to slot1
2. On reset, MCUboot swaps slot0 ↔ slot1
3. Application boots from slot0
4. If confirmed, swap is permanent
5. If not confirmed, MCUboot reverts on next boot

**Configuration:**

```kconfig
# sysbuild/mcuboot.conf
CONFIG_BOOTLOADER_MCUBOOT=y
# Swap is default, no extra config needed
```

**Application must confirm:**

```c
#include <zephyr/dfu/mcuboot.h>

void main(void) {
    /* Mark image as OK to prevent revert */
    boot_write_img_confirmed();
}
```

### Direct-XIP

**Behavior:**
- Application executes directly from slot (no copy)
- Faster boot
- Requires XIP-capable flash

**Configuration:**

```kconfig
# sysbuild/mcuboot.conf
CONFIG_MCUBOOT_BOOTLOADER_MODE_DIRECT_XIP=y
CONFIG_MCUBOOT_BOOTLOADER_MODE_DIRECT_XIP_WITH_REVERT=y
```

### Overwrite-Only

**Behavior:**
- New image overwrites slot0
- No revert capability
- Smaller bootloader

**Configuration:**

```kconfig
# sysbuild/mcuboot.conf
CONFIG_MCUBOOT_BOOTLOADER_MODE_OVERWRITE_ONLY=y
```

## Image Encryption

**Encrypt images for secure DFU:**

```kconfig
# sysbuild.conf
SB_CONFIG_MCUBOOT_ENCRYPTION_KEY_FILE="enc-rsa-2048.pem"
SB_CONFIG_MCUBOOT_ENCRYPT_IMAGE=y

# sysbuild/mcuboot.conf
CONFIG_BOOT_ENCRYPT_IMAGE=y
CONFIG_BOOT_ENCRYPTION_KEY_FILE="enc-rsa-2048.pem"
```

**Generate encryption key:**

```bash
imgtool keygen -k enc-rsa-2048.pem -t rsa-2048
```

## Anti-Rollback Protection

**Prevent downgrade attacks:**

```kconfig
# sysbuild/mcuboot.conf
CONFIG_BOOT_VERSION_CMP_USE_BUILD_NUMBER=y

# prj.conf
CONFIG_MCUBOOT_IMGTOOL_SIGN_VERSION="1.2.3+4"
#                                          ^ build number
```

**MCUboot rejects images with lower version.**

## TF-M Integration

**Available on:** Cortex-M33, Cortex-M55 (ARMv8-M with TrustZone)

### Enable TF-M

**sysbuild.conf:**

```kconfig
SB_CONFIG_BOOTLOADER_MCUBOOT=y
SB_CONFIG_BUILD_WITH_TFM=y
```

**prj.conf:**

```kconfig
CONFIG_BUILD_WITH_TFM=y
CONFIG_TFM_BOARD="nordic_nrf/nrf9160dk_nrf9160/ns"
```

**Note:** `ns` suffix indicates non-secure application.

### TF-M Boot Flow

1. **MCUboot** — Verifies both TF-M and application images
2. **TF-M secure partition** — Boots first, initializes secure services
3. **Non-secure application** — Boots second, calls TF-M via PSA APIs

### Secure Partitions

TF-M provides isolated partitions:

- **PSA Crypto** — Cryptographic operations
- **PSA Storage** — Secure persistent storage
- **PSA Attestation** — Device identity and measurements
- **PSA Firmware Update** — Secure DFU

## PSA Crypto API

**Access from non-secure application:**

```c
#include <psa/crypto.h>

psa_status_t status = psa_crypto_init();
if (status != PSA_SUCCESS) {
    printk("PSA Crypto init failed: %d\n", status);
    return;
}

/* Generate random bytes */
uint8_t random[16];
psa_generate_random(random, sizeof(random));

/* Hash data */
psa_hash_operation_t op = PSA_HASH_OPERATION_INIT;
uint8_t hash[32];
size_t hash_len;

psa_hash_setup(&op, PSA_ALG_SHA_256);
psa_hash_update(&op, data, data_len);
psa_hash_finish(&op, hash, sizeof(hash), &hash_len);
```

**Kconfig:**

```kconfig
CONFIG_PSA_CRYPTO_CLIENT=y
CONFIG_MBEDTLS_PSA_CRYPTO_C=y
```

## Signing Keys Management

**Development keys** (included in Zephyr tree):

```
bootloader/mcuboot/root-rsa-2048.pem
bootloader/mcuboot/root-ec-p256.pem
```

**Production:** Generate unique keys per product.

**Key types:**
- **RSA-2048** — Most compatible, larger signatures (256 bytes)
- **RSA-3072** — More secure, even larger (384 bytes)
- **ECDSA P-256** — Smaller signatures (64 bytes), fast

**Generate key:**

```bash
imgtool keygen -k my-rsa-key.pem -t rsa-2048
imgtool keygen -k my-ec-key.pem -t ecdsa-p256
```

## sysbuild Image Configuration

**Per-image configuration files:**

```cmake
# sysbuild.cmake
set(mcuboot_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/sysbuild/mcuboot.conf)
set(${DEFAULT_IMAGE}_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/prj.conf)
```

**Directory structure:**

```
project/
├── sysbuild.conf           # Sysbuild configuration
├── sysbuild.cmake          # Per-image config paths
├── sysbuild/
│   └── mcuboot.conf        # MCUboot-specific config
├── prj.conf                # Application config
└── boards/
    └── board.overlay       # Partition layout
```

## Additional resources

- For complete MCUboot configuration options, image signing with imgtool, partition layouts, and upgrade mode details, see [mcuboot-reference.md](mcuboot-reference.md)
- For TF-M secure partition configuration, PSA API reference, isolation levels, and NS application patterns, see [tfm-integration.md](tfm-integration.md)
