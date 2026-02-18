# MCUboot Complete Reference

## Image Signing with imgtool

### Install imgtool

```bash
pip3 install imgtool
```

### Sign Image Manually

```bash
imgtool sign \
    --key root-rsa-2048.pem \
    --header-size 0x200 \
    --align 8 \
    --version 1.2.3 \
    --slot-size 0x76000 \
    build/zephyr/zephyr.bin \
    signed.bin
```

**Parameters:**
- `--key` — Signing key (PEM format)
- `--header-size` — MCUboot header size (usually 0x200 or 0x400)
- `--align` — Flash write alignment (4 or 8)
- `--version` — Image version (semantic versioning)
- `--slot-size` — Partition size from DTS
- Input: unsigned binary
- Output: signed binary with MCUboot header

### Encrypt Image

```bash
imgtool sign \
    --key signing-key.pem \
    --encrypt enc-key.pem \
    --header-size 0x200 \
    --align 8 \
    --version 1.2.3 \
    --slot-size 0x76000 \
    build/zephyr/zephyr.bin \
    encrypted-signed.bin
```

### Verify Image

```bash
imgtool verify \
    --key root-rsa-2048-pub.pem \
    signed.bin
```

### Extract Public Key

```bash
imgtool getpub -k root-rsa-2048.pem
```

## MCUboot Configuration Options

### Signature Algorithm

```kconfig
# RSA-2048 (default, most compatible)
CONFIG_BOOT_SIGNATURE_TYPE_RSA=y
CONFIG_BOOT_SIGNATURE_TYPE_RSA_LEN=2048

# RSA-3072 (more secure, larger)
CONFIG_BOOT_SIGNATURE_TYPE_RSA=y
CONFIG_BOOT_SIGNATURE_TYPE_RSA_LEN=3072

# ECDSA P-256 (smaller, faster)
CONFIG_BOOT_SIGNATURE_TYPE_ECDSA_P256=y

# ED25519 (EdDSA, modern)
CONFIG_BOOT_SIGNATURE_TYPE_ED25519=y
```

### Boot Mode

```kconfig
# Swap mode (default)
# No special config — swap is default

# Swap with scratch
CONFIG_BOOT_SWAP_USING_SCRATCH=y

# Direct-XIP
CONFIG_MCUBOOT_BOOTLOADER_MODE_DIRECT_XIP=y

# Direct-XIP with revert
CONFIG_MCUBOOT_BOOTLOADER_MODE_DIRECT_XIP_WITH_REVERT=y

# Overwrite only (no revert)
CONFIG_MCUBOOT_BOOTLOADER_MODE_OVERWRITE_ONLY=y

# RAM load (copy to RAM and execute)
CONFIG_MCUBOOT_BOOTLOADER_MODE_RAM_LOAD=y
```

### Security Features

```kconfig
# Image encryption
CONFIG_BOOT_ENCRYPT_IMAGE=y
CONFIG_BOOT_ENCRYPTION_KEY_FILE="enc-key.pem"

# Validate on every boot (slower, more secure)
CONFIG_BOOT_VALIDATE_SLOT0=y

# Anti-rollback
CONFIG_BOOT_VERSION_CMP_USE_BUILD_NUMBER=y

# Hardware unique key (HUK)
CONFIG_BOOT_ENCRYPTION_USING_HW_KEY=y
```

### Performance Tuning

```kconfig
# Maximum image sectors (controls RAM usage)
CONFIG_BOOT_MAX_IMG_SECTORS=128

# Reduce logging
CONFIG_LOG_MODE_MINIMAL=y
CONFIG_BOOT_BANNER=n

# Optimize for size
CONFIG_SIZE_OPTIMIZATIONS=y
```

### Serial Recovery

```kconfig
# Enable serial bootloader
CONFIG_MCUBOOT_SERIAL=y
CONFIG_BOOT_SERIAL_CDC_ACM=y  # USB serial
# OR
CONFIG_BOOT_SERIAL_UART=y     # UART serial

# Wait time for serial command
CONFIG_BOOT_SERIAL_WAIT_FOR_DFU=5000  # milliseconds
```

## Flash Partition Patterns

### Minimal (Single Slot)

```dts
&flash0 {
    partitions {
        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x0 0xC000>;
        };
        slot0_partition: partition@c000 {
            label = "image-0";
            reg = <0xC000 0xF4000>;  /* Rest of flash */
        };
    };
};
```

**Use case:** No DFU capability, minimal flash usage.

### Dual Slot (Swap or Overwrite)

```dts
&flash0 {
    partitions {
        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x0 0xC000>;
        };
        slot0_partition: partition@c000 {
            label = "image-0";
            reg = <0xC000 0x76000>;
        };
        slot1_partition: partition@82000 {
            label = "image-1";
            reg = <0x82000 0x76000>;
        };
        storage_partition: partition@f8000 {
            label = "storage";
            reg = <0xF8000 0x8000>;
        };
    };
};
```

**Use case:** Standard DFU with revert capability.

### Dual Slot with Scratch

```dts
&flash0 {
    partitions {
        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x0 0xC000>;
        };
        slot0_partition: partition@c000 {
            label = "image-0";
            reg = <0xC000 0x69000>;
        };
        slot1_partition: partition@75000 {
            label = "image-1";
            reg = <0x75000 0x69000>;
        };
        scratch_partition: partition@de000 {
            label = "image-scratch";
            reg = <0xDE000 0x1A000>;  /* Scratch area for swap */
        };
        storage_partition: partition@f8000 {
            label = "storage";
            reg = <0xF8000 0x8000>;
        };
    };
};
```

**Use case:** Devices without erase-on-write flash.

### External Flash Secondary Slot

```dts
&flash0 {
    partitions {
        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x0 0xC000>;
        };
        slot0_partition: partition@c000 {
            label = "image-0";
            reg = <0xC000 0xF4000>;
        };
    };
};

&external_flash {
    partitions {
        slot1_partition: partition@0 {
            label = "image-1";
            reg = <0x0 0xF4000>;
        };
    };
};
```

**Kconfig:**

```kconfig
CONFIG_FLASH_MAP=y
CONFIG_FLASH_MAP_CUSTOM=y
```

**Use case:** Limited internal flash, abundant external flash.

## Image Header Format

**MCUboot prepends header to image:**

```
Offset | Size | Field
-------|------|------------------
0x00   | 4    | Magic (0x96f3b83d)
0x04   | 4    | Load address
0x08   | 2    | Header size
0x0A   | 2    | Protected TLV size
0x0C   | 4    | Image size
0x10   | 4    | Flags
0x14   | 12   | Version (major.minor.rev+build)
0x20   | ...  | Padding to header size
...    | ...  | Image binary
...    | ...  | TLV (signatures, hashes)
```

**TLV (Type-Length-Value) area contains:**
- Image hash (SHA256)
- Signature (RSA/ECDSA)
- Dependencies
- Encryption info

## Upgrade Workflow

### Application Triggers Upgrade

```c
#include <zephyr/dfu/mcuboot.h>
#include <zephyr/storage/flash_map.h>

/* Download new image to slot1 */
const struct flash_area *fa;
flash_area_open(FLASH_AREA_ID(image_1), &fa);

/* Write image data */
flash_area_write(fa, 0, image_data, image_size);

flash_area_close(fa);

/* Mark for upgrade on next boot */
boot_request_upgrade(BOOT_UPGRADE_TEST);
/* Options: BOOT_UPGRADE_TEST (revert if not confirmed)
            BOOT_UPGRADE_PERMANENT (no revert) */

/* Reboot to apply */
sys_reboot(SYS_REBOOT_COLD);
```

### Application Confirms Image

```c
void main(void) {
    /* Check if running after upgrade */
    if (boot_is_img_confirmed()) {
        printk("Running confirmed image\n");
    } else {
        printk("Running test image\n");

        /* Test application... */

        /* If tests pass, confirm image */
        if (tests_passed()) {
            boot_write_img_confirmed();
            printk("Image confirmed\n");
        } else {
            /* Will revert on next boot */
            printk("Tests failed, will revert\n");
            sys_reboot(SYS_REBOOT_COLD);
        }
    }
}
```

## Debugging MCUboot

### Enable MCUboot Logging

```kconfig
# sysbuild/mcuboot.conf
CONFIG_LOG=y
CONFIG_MCUBOOT_LOG_LEVEL_INF=y
CONFIG_BOOT_BANNER=y
```

### View Boot Info

**MCUboot prints on boot:**

```
*** Booting Zephyr OS build v3.7.0 ***
I: Starting bootloader
I: Primary image: magic=good, swap_type=0x1, copy_done=0x3, image_ok=0x1
I: Secondary image: magic=good, swap_type=0x1, copy_done=0x3, image_ok=0x1
I: Boot source: primary slot
I: Swap type: none
I: Bootloader chainload address offset: 0xc000
```

### Common Issues

**Error: "Image in the primary slot is not valid"**
- Cause: Unsigned image or corrupted signature
- Fix: Verify signing key matches, check partition alignment

**Error: "Unable to find bootable image"**
- Cause: No valid image in slot0 or slot1
- Fix: Flash application to slot0, verify partition layout

**Infinite revert loop**
- Cause: Application not confirming image
- Fix: Add `boot_write_img_confirmed()` to application

## Kconfig: Image Version

**Set version in application:**

```kconfig
# prj.conf
CONFIG_MCUBOOT_IMGTOOL_SIGN_VERSION="1.2.3+4"
```

**Auto-generated during build** — sysbuild calls imgtool with this version.

**Anti-rollback check:**

```kconfig
# sysbuild/mcuboot.conf
CONFIG_BOOT_VERSION_CMP_USE_BUILD_NUMBER=y
```

MCUboot rejects images with `major.minor.rev+build` lower than current image.
