# West and Sysbuild Complete Reference

## West Manifest (west.yml)

```yaml
manifest:
  version: "0.13"
  
  remotes:
    - name: zephyrproject-rtos
      url-base: https://github.com/zephyrproject-rtos
    - name: company
      url-base: https://github.com/mycompany
  
  projects:
    - name: zephyr
      remote: zephyrproject-rtos
      revision: v3.7-branch
      import: true
    - name: custom-module
      remote: company
      revision: main
      path: modules/custom
  
  self:
    path: application
```

## West Commands Reference

### Workspace Management

```bash
west init -m URL [--mr REVISION] [PATH]
west update [PROJECT ...]
west list                    # List all projects
west status                  # Git status of all projects
west diff                    # Git diff of all projects
west forall -c "git status"  # Run command in all projects
```

### Build Commands

```bash
west build -b BOARD [SOURCE]
west build -b BOARD -p auto    # Auto pristine when needed
west build -b BOARD -p always  # Always pristine
west build -t TARGET           # Build specific target
west build -d BUILD_DIR        # Custom build directory
```

### Flash and Debug

```bash
west flash [--runner RUNNER]
west flash --hex-file FILE
west debug
west debugserver
west attach
```

### Twister (Testing)

```bash
west twister -p PLATFORM -T TESTSUITE
west twister --all             # Run all tests
west twister --coverage        # With coverage
west twister -v                # Verbose
```

## Sysbuild Configuration

### Image Dependencies

**sysbuild.cmake:**

```cmake
# MCUboot configuration
set(mcuboot_KCONFIG_ROOT ${CMAKE_CURRENT_LIST_DIR}/sysbuild/mcuboot/Kconfig.root)
set(mcuboot_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/sysbuild/mcuboot.conf)
set(mcuboot_DTC_OVERLAY_FILE ${CMAKE_CURRENT_LIST_DIR}/sysbuild/mcuboot.overlay)

# Application configuration  
set(${DEFAULT_IMAGE}_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/prj.conf)
```

### Multi-Core Builds

```cmake
# nRF5340 dual-core
SB_CONFIG_NETCORE_APP_UPDATE=y
```

## Custom West Commands

**scripts/west_commands.py:**

```python
from west.commands import WestCommand

class MyCommand(WestCommand):
    def __init__(self):
        super().__init__(
            'mycmd',
            'my custom command',
            'Long description here')
    
    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name)
        return parser
    
    def do_run(self, args, unknown_args):
        self.inf('Running my command')

def register_commands():
    return [MyCommand()]
```

**Register in west.yml:**

```yaml
west-commands:
  - file: scripts/west_commands.py
```
