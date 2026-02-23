---
name: coding-embedded-zephyr-tester:scaffold-tests
description: "Generate test scaffolding for existing Zephyr modules with FFF mocks and testcase.yaml"
allowed-tools: Read, Glob, Grep, Write, Edit
user-invocable: true
---

# Scaffold Tests

You generate complete test infrastructure for existing Zephyr modules: test directory, CMakeLists.txt, prj.conf, testcase.yaml, FFF mock headers, and a test source file with ZTEST_SUITE registration and stub test cases.

## Workflow

### Step 1: Identify the Module Under Test

Determine which module to scaffold tests for:

- **User specifies a file** -> Read it, extract its module name and public API
- **User specifies a directory** -> Find all .c/.h files, identify the module
- **User specifies a function** -> Find the containing module

Use Glob and Grep to locate the module's files:

```
Glob(pattern: "src/**/<module>*.{c,h}")
Grep(pattern: "int <module>_", output_mode: "files_with_matches")
```

### Step 2: Analyze the Module API

Read the module's header file to extract:

1. **Public functions**: Name, parameters, return type, documented error codes
2. **Public types**: Structs, enums, typedefs used in the API
3. **Dependencies**: Include directives that reveal external dependencies

Read the implementation file to identify:

1. **Zephyr API usage**: Which kernel, driver, or subsystem APIs are called
2. **Internal state**: Static variables, module-level structs
3. **Error paths**: All negative return paths

### Step 3: Generate Test Directory

Create the test directory structure:

```
tests/unit/<module>/
├── CMakeLists.txt
├── prj.conf
├── testcase.yaml
└── src/
    ├── main.c
    └── mock_<dependency>.h
```

### Step 4: Generate CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(test_<module>)

target_sources(app PRIVATE
    src/main.c
)

# Include path for module under test
target_include_directories(app PRIVATE
    ${CMAKE_SOURCE_DIR}/../../../src/<module>/include
)
```

Adjust include paths based on actual project structure.

### Step 5: Generate prj.conf

```ini
# ---- Test Framework ----
CONFIG_ZTEST=y
CONFIG_ZTEST_NEW_API=y

# ---- Logging ----
CONFIG_LOG=y
CONFIG_LOG_DEFAULT_LEVEL=3

# ---- Module Dependencies ----
# [Auto-detected from module's Kconfig usage]
```

### Step 6: Generate testcase.yaml

```yaml
tests:
  <module>.unit:
    platform_allow: native_sim
    tags: unit <module>
    integration_platforms:
      - native_sim
    harness: ztest
```

### Step 7: Generate Mock Headers

For each external dependency, create FFF mock declarations:

```c
/* mock_<dependency>.h */
#ifndef MOCK_<DEPENDENCY>_H_
#define MOCK_<DEPENDENCY>_H_

#include <zephyr/fff.h>
#include <zephyr/drivers/<dependency>.h>

FAKE_VALUE_FUNC(int, <api_func_1>, const struct device *);
FAKE_VALUE_FUNC(int, <api_func_2>, const struct device *, ...);

#endif /* MOCK_<DEPENDENCY>_H_ */
```

### Step 8: Generate Test Source File

Create `main.c` with:

1. ZTEST_SUITE registration with fixture and before/after
2. One ZTEST_F stub per public API function (happy path)
3. One ZTEST_F stub per documented error return (error path)
4. Arrange-Act-Assert comments in each test body
5. TODO comments for assertions that need implementation

```c
#include <zephyr/ztest.h>
#include <zephyr/fff.h>
DEFINE_FFF_GLOBALS;

#include "<module>.h"
#include "mock_<dependency>.h"

#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(test_<module>, LOG_LEVEL_DBG);

struct <module>_fixture {
    /* TODO: add fixture fields based on test needs */
};

static void *<module>_setup(void)
{
    static struct <module>_fixture fixture;
    return &fixture;
}

static void <module>_before(void *f)
{
    struct <module>_fixture *fixture = f;
    memset(fixture, 0, sizeof(*fixture));
    RESET_FAKE(<api_func_1>);
    RESET_FAKE(<api_func_2>);
    FFF_RESET_HISTORY();
}

ZTEST_SUITE(<module>, NULL, <module>_setup, <module>_before, NULL, NULL);

/* --- Happy path tests --- */

ZTEST_F(<module>, test_<func1>_succeeds)
{
    /* Arrange */
    /* TODO: configure mocks for success */

    /* Act */
    int ret = <func1>();

    /* Assert */
    zassert_equal(ret, 0, "<func1> returned %d, expected 0", ret);
}

/* --- Error path tests --- */

ZTEST_F(<module>, test_<func1>_returns_einval_for_null_input)
{
    /* Arrange: no mock setup needed */

    /* Act */
    int ret = <func1>(NULL);

    /* Assert */
    zassert_equal(ret, -EINVAL,
                  "<func1>(NULL) returned %d, expected -EINVAL", ret);
}
```

### Step 9: Present Summary

```
## Test Scaffolding: tests/unit/<module>/

### Files Created
- tests/unit/<module>/CMakeLists.txt
- tests/unit/<module>/prj.conf
- tests/unit/<module>/testcase.yaml
- tests/unit/<module>/src/main.c
- tests/unit/<module>/src/mock_<dependency>.h

### Test Stubs Generated
| Test | Type | Status |
|------|------|--------|
| test_<func1>_succeeds | happy path | stub (needs assertions) |
| test_<func1>_returns_einval_for_null_input | error path | stub |
| test_<func2>_succeeds | happy path | stub |
| ... | ... | ... |

### Next Steps
1. Fill in mock configurations in each test's Arrange section
2. Complete assertions in each test's Assert section
3. Run: `west twister -p native_sim -T tests/unit/<module>/`
4. Add more test cases for edge cases and boundary conditions
```

## Error Handling

- **Module not found** -> Inform user, ask for correct path
- **No public API header** -> Warn that API surface cannot be auto-detected, scaffold with minimal stubs
- **Complex dependencies** -> List all dependencies and let user decide which to mock
- **Existing test directory** -> Warn before overwriting, offer to merge
