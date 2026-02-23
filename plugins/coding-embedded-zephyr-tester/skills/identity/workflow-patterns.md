# Zephyr Test Workflow Patterns

Step-by-step procedures for the core test engineering workflows: writing unit tests, writing integration tests, running tests, analyzing coverage, triaging failures, and CI integration.

## 1. Unit Test Workflow

### When writing unit tests for a Zephyr module:

1. **Analyze the module under test.**
   - Read the public API header: identify every exported function, its parameters, return values, and documented error conditions.
   - Read the implementation: identify internal state, edge cases, error paths, and Zephyr API dependencies.
   - List all external dependencies that need mocking (driver APIs, kernel primitives, other modules).

2. **Design the test case list.**
   - One test per public API function per behavior:
     - Happy path (valid inputs, successful operation)
     - Error paths (NULL pointers, invalid parameters, resource exhaustion)
     - Edge cases (boundary values, empty buffers, maximum lengths)
     - State transitions (init before start, stop before start, double init)
   - Name each test: `test_<module>_<function>_<scenario>_<expected>`

3. **Create the test directory structure:**
   ```
   tests/unit/<module>/
   ├── CMakeLists.txt
   ├── prj.conf
   ├── testcase.yaml
   └── src/
       ├── main.c
       └── mock_<dependency>.h (if FFF mocks needed)
   ```

4. **Write FFF mocks** for all external dependencies:
   - `FAKE_VALUE_FUNC` for functions returning values
   - `FAKE_VOID_FUNC` for void functions
   - Define `custom_fake` functions for complex behavior
   - Always reset in the `before` fixture function

5. **Write the test suite:**
   - `ZTEST_SUITE()` with setup/before/after/teardown
   - `ZTEST()` or `ZTEST_F()` for each test case
   - Arrange-Act-Assert pattern in every test body
   - Diagnostic message on every assertion

6. **Write testcase.yaml:**
   ```yaml
   tests:
     <module>.unit:
       platform_allow: native_sim
       tags: unit <module>
       integration_platforms:
         - native_sim
   ```

7. **Run and verify:**
   ```bash
   west twister -p native_sim -T tests/unit/<module>/
   ```
   All tests must pass. Fix failures immediately -- do not move on with known failures.

8. **Check coverage (optional but recommended):**
   ```bash
   west twister -p native_sim -T tests/unit/<module>/ --coverage
   ```
   Target: 80%+ line coverage, 70%+ branch coverage for the module under test.

## 2. Integration Test Workflow

### When writing integration tests for subsystem interactions:

1. **Identify the integration boundary.**
   - Which modules interact? (e.g., sensor driver + data processing + storage)
   - What is the communication mechanism? (message queues, work queues, events)
   - What is the expected end-to-end behavior?

2. **Select the test platform:**
   - **native_sim:** For module interactions that do not require specific hardware emulation. Preferred for speed.
   - **qemu_cortex_m3:** For tests that need ARM architecture specifics (MPU, interrupt priorities, Cortex-M fault behavior).
   - **nrf52_bsim:** For BLE protocol tests (multi-device connection, pairing, GATT operations).
   - **Renode:** For complex multi-board scenarios or specific peripheral emulation.

3. **Design the integration scenario:**
   - Define the data flow: input -> processing stages -> expected output
   - Identify synchronization points (where to wait for async operations)
   - Plan failure injection (what happens when a subsystem fails mid-flow)

4. **Write the test with real subsystems:**
   - Initialize all participating modules in the setup fixture
   - Use real Zephyr kernel primitives (threads, queues, events) -- do NOT mock the kernel
   - Mock only the hardware boundary (device drivers at the bottom of the stack)
   - Use `k_sem_take()` with timeout for synchronization -- never `k_sleep()`

5. **Write testcase.yaml with platform filters:**
   ```yaml
   tests:
     data_pipeline.integration:
       platform_allow:
         - native_sim
         - qemu_cortex_m3
       tags: integration pipeline
       integration_platforms:
         - qemu_cortex_m3
       timeout: 60
   ```

6. **Run on all target platforms:**
   ```bash
   west twister -p native_sim -p qemu_cortex_m3 -T tests/integration/<feature>/
   ```

## 3. Coverage Analysis Workflow

### When analyzing and improving code coverage:

1. **Generate the coverage report:**
   ```bash
   west twister -p native_sim -T tests/ --coverage --coverage-tool lcov
   ```
   Output lands in `twister-out/coverage/`.

2. **Read the summary report:**
   - Open `twister-out/coverage/index.html` or parse `twister-out/coverage/coverage.info`
   - Note overall line coverage, branch coverage, function coverage percentages
   - Identify files below threshold (target: 80% line, 70% branch)

3. **Identify untested paths:**
   - Sort source files by coverage percentage (lowest first)
   - For each low-coverage file, identify uncovered line ranges
   - Classify uncovered code:
     - **Error paths:** Return values from failed API calls. These are high-value test targets.
     - **Edge cases:** Boundary conditions, empty inputs, maximum values. High value.
     - **Defensive checks:** NULL pointer guards, range validation. Medium value.
     - **Platform-specific paths:** Code behind `IS_ENABLED()` that is not active on native_sim. May require QEMU target.
     - **ISR paths:** Interrupt handlers. Require timer or GPIO simulation on native_sim.

4. **Prioritize by risk:**
   - Error handling paths in safety-critical modules: MUST cover
   - Public API boundary validation: MUST cover
   - Internal helper functions with complex logic: SHOULD cover
   - Simple getter/setter functions: NICE to cover
   - Debug-only or logging-only paths: LOW priority

5. **Write targeted tests** for uncovered paths:
   - One test per uncovered error path
   - Use FFF `custom_fake` to force specific return values that trigger error paths
   - Use `return_val_seq` for sequences that trigger multi-step error flows

6. **Re-run coverage and verify improvement:**
   ```bash
   west twister -p native_sim -T tests/ --coverage --coverage-tool lcov
   ```
   Compare before/after metrics.

## 4. Test Execution and Triage Workflow

### When running tests and handling failures:

1. **Run the test suite:**
   ```bash
   # Full suite
   west twister -T tests/ --integration

   # Specific module
   west twister -p native_sim -T tests/unit/sensor_mgr/

   # With verbose output for debugging
   west twister -p native_sim -T tests/unit/sensor_mgr/ -v

   # Retry failed tests to detect flaky tests
   west twister -T tests/ --retry-failed 3
   ```

2. **Parse results:**
   - Check twister exit code (0 = all pass, non-zero = failures)
   - Read `twister-out/twister.log` for detailed output
   - Read `twister-out/testplan.json` for structured results
   - Check individual test logs in `twister-out/<platform>/<test>/handler.log`

3. **Triage failures:**
   - **Assertion failure:** Read the assertion message. Identify whether the test expectation is wrong or the code has a bug. Check the test's Arrange section for incorrect mock setup.
   - **Build failure:** Missing CONFIG_ option, missing include, linker error. Fix CMakeLists.txt or prj.conf.
   - **Timeout:** Test hung waiting for a condition that never occurred. Check synchronization logic, mock configuration, and whether the mock actually triggers the expected callback.
   - **Crash (hard fault):** NULL pointer dereference, stack overflow, or memory corruption. Run with address sanitizer on native_sim: `CONFIG_ASAN=y`.
   - **Flaky (passes sometimes):** Timing-dependent test. Replace `k_sleep()` with explicit synchronization. Add `--retry-failed 3` to confirm flakiness. Quarantine if cannot fix immediately.

4. **Handle flaky tests:**
   - Confirm flakiness with `--retry-failed 5`
   - Add to quarantine list: `twister --quarantine-list quarantine.yaml`
   - File a bug/TODO with reproduction steps
   - Root cause: usually timing (use semaphores), uninitialized memory (use memset in setup), or test interdependence (reset mocks)

## 5. CI Integration Workflow

### Setting up tests for CI/CD:

1. **Define the CI test command:**
   ```bash
   # Fast check (unit tests only, native_sim)
   west twister -p native_sim -T tests/unit/ --integration -O ci-results/

   # Full check (all platforms)
   west twister -T tests/ --integration -O ci-results/

   # With coverage gate
   west twister -p native_sim -T tests/ --coverage --coverage-tool lcov -O ci-results/
   ```

2. **Configure JUnit output** for CI dashboard:
   ```bash
   west twister -T tests/ --integration -O ci-results/
   # JUnit XML: ci-results/twister.xml
   ```

3. **Set coverage thresholds:**
   - Parse `coverage.info` with lcov tools
   - Fail CI if line coverage drops below threshold
   - Typical thresholds: 80% line, 70% branch for application modules

4. **Manage quarantine lists:**
   ```yaml
   # quarantine.yaml
   - scenarios:
       - sensor_mgr.integration.timing_test
     platforms:
       - qemu_cortex_m3
     comment: "Flaky timing test, investigating root cause (ISSUE-123)"
   ```

5. **Optimize CI execution time:**
   - Use `--subset` for parallelization across CI workers
   - Use `--changed-only` (if supported) to run tests for changed modules
   - Run unit tests on every commit, integration tests on PR merge
   - Use `--short` to skip long-running tests in pre-commit hooks

## 6. Test Scaffolding Workflow

### When generating test infrastructure for an existing module:

1. **Read the module's public API header.** Extract all function signatures.

2. **Identify dependencies.** Grep for `#include` directives and Zephyr API calls.

3. **Generate the test skeleton:**
   - CMakeLists.txt with proper include paths
   - prj.conf with required CONFIG_ options
   - testcase.yaml with native_sim platform
   - main.c with ZTEST_SUITE, fixture struct, setup/before/after, and one ZTEST stub per public function
   - mock_*.h with FFF declarations for all external dependencies

4. **Fill in test cases** following the unit test workflow.

## 7. Regression Test Workflow

### When a bug is reported:

1. **Write a test that reproduces the bug** (must FAIL without the fix).
2. **Name it descriptively:** `test_<module>_regression_<brief_description>`.
3. **Add a comment** with the bug/issue reference:
   ```c
   /* Regression test for ISSUE-42: NULL pointer crash when
    * sensor_read called before sensor_init */
   ZTEST(sensor_mgr, test_regression_read_before_init_returns_error)
   {
       struct sensor_sample sample;
       int ret = sensor_mgr_read(&sample);
       zassert_equal(ret, -EAGAIN,
                     "expected -EAGAIN before init, got %d", ret);
   }
   ```
4. **Verify the fix makes it pass.**
5. **Add to the permanent test suite** -- regression tests are never removed.
