# Zephyr RTOS Workflow Patterns

Step-by-step procedures for the seven core workflow stages in Zephyr firmware development.

## 1. Project Initialization (Init)

### When starting a new Zephyr project:

1. **Determine workspace topology.** Ask the user which west manifest layout they prefer:
   - **T2 (star topology):** Application repo is the manifest repo, Zephyr is a dependency. Best for product development where the app owns the manifest.
   - **T3 (forest topology):** Separate manifest repo that pulls in Zephyr, modules, and the application as peers. Best for organizations with multiple apps sharing modules.
   - **Freestanding:** Application lives outside any west workspace, uses `ZEPHYR_BASE` environment variable. Best for quick prototypes.

2. **Initialize the workspace:**
   ```bash
   west init -m <manifest-repo-url> <workspace-dir>
   cd <workspace-dir>
   west update
   ```

3. **Set up the Python virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r zephyr/scripts/requirements.txt
   ```

4. **Create the application skeleton:**
   ```
   app/
   ├── CMakeLists.txt
   ├── Kconfig
   ├── prj.conf
   ├── boards/
   │   └── <board>.overlay
   ├── src/
   │   └── main.c
   └── tests/
       └── unit/
   ```

5. **Configure sysbuild from the start:**
   - Create `sysbuild.conf` at the application root.
   - Add MCUboot configuration: `SB_CONFIG_BOOTLOADER_MCUBOOT=y`
   - Create `sysbuild/mcuboot.conf` for bootloader-specific Kconfig if needed.

6. **Verify the toolchain:** Run `west build -b <target_board> --sysbuild -- -DBOARD_ROOT=.` to confirm compilation succeeds before writing any application code.

## 2. Writing Code (Write)

### When implementing a new subsystem/module:

1. **Define the API header first.** The header is the contract:
   ```c
   /* src/sensor_mgr/include/sensor_mgr.h */
   #ifndef SENSOR_MGR_H_
   #define SENSOR_MGR_H_

   int sensor_mgr_init(void);
   int sensor_mgr_start(uint32_t interval_ms);
   int sensor_mgr_stop(void);
   int sensor_mgr_read(struct sensor_sample *out);

   #endif /* SENSOR_MGR_H_ */
   ```

2. **Create the implementation file.** Runtime-initialize all OS objects:
   ```c
   LOG_MODULE_REGISTER(sensor_mgr, CONFIG_APP_SENSOR_LOG_LEVEL);

   static struct k_msgq sample_queue;
   static char __aligned(4) sample_queue_buf[8 * sizeof(struct sensor_sample)];
   static struct k_work_delayable sample_work;

   int sensor_mgr_init(void)
   {
       k_msgq_init(&sample_queue, sample_queue_buf,
                    sizeof(struct sensor_sample), 8);
       k_work_init_delayable(&sample_work, sample_work_handler);
       return 0;
   }
   ```

3. **Add the module to CMakeLists.txt** using `zephyr_library_named()`.

4. **Create board overlays** for every target board, with comments on every property.

5. **Add Kconfig symbols** in the application `Kconfig` for any compile-time configuration.

6. **Update `prj.conf`** with required CONFIG_ symbols, grouped and commented.

7. **Write unit tests** in `tests/unit/<module>/` before considering the module complete.

## 3. Building (Build)

### Standard build procedure:

1. **First build / after Kconfig changes:**
   ```bash
   west build -b <board> app --sysbuild --pristine
   ```
   The `--pristine` flag is critical after any Kconfig or devicetree change. Without it, stale cached values cause phantom bugs.

2. **Incremental builds (code changes only):**
   ```bash
   west build
   ```

3. **Multi-board builds (portability check):**
   ```bash
   west build -b nrf52dk/nrf52832 app --sysbuild --pristine -d build/nrf52
   west build -b nucleo_f411re app --sysbuild --pristine -d build/stm32
   west build -b esp32s3_devkitc/esp32s3/procpu app --sysbuild --pristine -d build/esp32
   ```

4. **Inspect generated devicetree:** After build, always check `build/zephyr/zephyr.dts` to verify the overlay was applied correctly.

5. **Inspect resolved Kconfig:** Check `build/zephyr/.config` to verify all expected symbols are set and no dependencies are missing.

### Build failure triage:

- **Devicetree error:** Check `build/zephyr/zephyr.dts` for the actual generated tree. Common causes: missing node, wrong compatible string, missing binding YAML.
- **Kconfig error:** Run `west build -t menuconfig` to trace the dependency chain. Never guess at Kconfig fixes.
- **Linker error (undefined symbol):** Usually means a Kconfig option is not enabled or a source file is not added to CMakeLists.txt.
- **Linker error (region overflow):** Flash or RAM exhausted. Check `build/zephyr/zephyr.map` for the largest consumers. Consider `CONFIG_SIZE_OPTIMIZATIONS=y`.

## 4. Flashing (Flash)

### Standard flash procedure:

1. **Flash with verification:**
   ```bash
   west flash --verify
   ```
   The `--verify` flag reads back the flashed image and compares it to the binary. Catches flash corruption, which is more common than most developers realize.

2. **MCUboot signed images:** With sysbuild, `west flash` automatically handles the signed image. For manual signing:
   ```bash
   west sign -t imgtool -- --key <key.pem> --version 1.0.0
   ```

3. **Platform-specific runners:**
   - **Nordic (nRF):** `west flash --runner nrfjprog` or `--runner jlink`
   - **STM32:** `west flash --runner openocd` or `--runner stm32cubeprogrammer`
   - **ESP32:** `west flash --runner esp32` (uses esptool.py)

4. **Erase before flash (when switching bootloaders or fixing corruption):**
   ```bash
   west flash --erase
   ```

## 5. Debugging (Debug)

### GDB debugging workflow:

1. **Start debug session:**
   ```bash
   west debug
   ```
   This launches GDB connected to the target via the configured runner (OpenOCD, J-Link, etc.).

2. **RTOS-aware debugging:** With OpenOCD, Zephyr threads are visible as GDB threads:
   ```gdb
   info threads          # List all Zephyr threads
   thread 3              # Switch to thread 3
   bt                    # Backtrace for current thread
   ```

3. **Common debug commands:**
   ```gdb
   monitor reset halt    # Reset and halt the target
   break main            # Set breakpoint at main
   watch my_variable     # Hardware watchpoint on variable
   x/16xw 0x20000000    # Examine 16 words at RAM base
   ```

4. **Coredump analysis (post-mortem):**
   ```bash
   # If coredump backend is configured (CONFIG_DEBUG_COREDUMP=y)
   west coredump parse build/zephyr/zephyr.elf <coredump_file>
   ```

5. **SystemView (on request):** If the user wants real-time thread visualization:
   ```
   CONFIG_SEGGER_SYSTEMVIEW=y
   CONFIG_USE_SEGGER_RTT=y
   CONFIG_TRACING=y
   CONFIG_TRACING_BACKEND_SYSTEMVIEW=y
   ```
   Launch SystemView application, connect via J-Link RTT.

6. **Logging-based debugging (when JTAG is unavailable):**
   - Set per-module log levels: `CONFIG_APP_SENSOR_LOG_LEVEL_DBG=y`
   - Use `LOG_HEXDUMP_DBG()` for buffer contents.
   - Use `LOG_DBG("state=%d, ret=%d", state, ret)` at state transitions.

## 6. Testing (Test)

### Unit testing with twister:

1. **Create test structure:**
   ```
   tests/unit/sensor_mgr/
   ├── CMakeLists.txt
   ├── prj.conf
   ├── testcase.yaml
   └── src/
       └── test_sensor_mgr.c
   ```

2. **Write testcase.yaml:**
   ```yaml
   tests:
     sensor_mgr.unit:
       platform_allow: native_sim
       tags: unit sensor
       integration_platforms:
         - native_sim
   ```

3. **Write tests with ztest:**
   ```c
   #include <zephyr/ztest.h>
   #include "sensor_mgr.h"

   ZTEST_SUITE(sensor_mgr, NULL, NULL, NULL, NULL, NULL);

   ZTEST(sensor_mgr, test_init_succeeds)
   {
       int ret = sensor_mgr_init();
       zassert_equal(ret, 0, "init returned %d", ret);
   }

   ZTEST(sensor_mgr, test_read_before_start_fails)
   {
       struct sensor_sample sample;
       int ret = sensor_mgr_read(&sample);
       zassert_equal(ret, -EAGAIN, "expected -EAGAIN, got %d", ret);
   }
   ```

4. **Run tests:**
   ```bash
   # Unit tests on native_sim
   west twister -p native_sim -T tests/unit/

   # Integration tests on QEMU
   west twister -p qemu_cortex_m3 -T tests/integration/

   # BLE protocol tests with BabbleSim
   west twister -p nrf52_bsim -T tests/bluetooth/

   # All tests (CI)
   west twister -T tests/ --integration
   ```

5. **Coverage report:**
   ```bash
   west twister -p native_sim -T tests/ --coverage
   # Output in twister-out/coverage/
   ```

## 7. Release (Release)

### Preparing a firmware release:

1. **Version the image:** Use semantic versioning in `VERSION` file at app root:
   ```
   VERSION_MAJOR = 1
   VERSION_MINOR = 2
   VERSION_PATCHLEVEL = 0
   ```

2. **Sign the image for MCUboot:**
   ```bash
   west sign -t imgtool -d build -- \
       --key <signing-key.pem> \
       --version $(cat VERSION | tr '\n' '.' | sed 's/\.$//')
   ```

3. **Generate DFU package for OTA:**
   ```bash
   # For Nordic DFU (nRF Connect SDK projects)
   nrfutil pkg generate --hw-version 52 \
       --sd-req 0x00 \
       --application build/zephyr/app_update.bin \
       --application-version-string "1.2.0" \
       dfu_package.zip

   # For mcumgr-based DFU (vanilla Zephyr)
   # The signed bin from west sign is directly uploadable via mcumgr
   mcumgr --conntype ble --connstring "peer_name=MyDevice" \
       image upload build/zephyr/zephyr.signed.bin
   ```

4. **Verify the update on device:**
   ```bash
   mcumgr --conntype ble --connstring "peer_name=MyDevice" image list
   mcumgr --conntype ble --connstring "peer_name=MyDevice" image confirm
   ```

5. **Release checklist:**
   - [ ] All tests pass on target hardware
   - [ ] Image signed with production key (not development key)
   - [ ] Version number incremented
   - [ ] CHANGELOG updated
   - [ ] Binary size within flash budget (check `build/zephyr/zephyr.map`)
   - [ ] Power consumption measured in target use case
   - [ ] OTA update path tested (upgrade AND rollback)
