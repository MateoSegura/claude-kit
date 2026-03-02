# Phase 7: Test Harness Integration

**Status:** completed
**Satisfies:** R6

## Objective

Update the test harness (`test/harness/`) to import `claude_kit` directly
instead of shelling out to the CLI. The harness gains programmatic access to
plugin resolution, session preparation, and in-memory telemetry capture.

## Steps

1. **Update `test/harness/runner.py`** — Replace subprocess-based plugin
   loading with library imports:

   **Before (subprocess):**
   ```python
   result = subprocess.run(
       ["python3", "claude-kit", "--kit", kit_name, "--print", prompt],
       capture_output=True, text=True
   )
   # Parse JSONL file to get telemetry
   ```

   **After (library import):**
   ```python
   from claude_kit import PluginResolver, SessionManager, TelemetryEmitter

   # Capture telemetry in memory
   captured_events = []
   telemetry = TelemetryEmitter(
       level="debug",
       on_emit=captured_events.append,
   )

   # Resolve plugins programmatically
   resolver = PluginResolver(plugins_dirs=[plugins_dir])
   session_mgr = SessionManager(resolver, telemetry=telemetry)
   session = session_mgr.prepare(kit_names=[kit_name])

   # Use Anthropic SDK with session config
   # (system prompt, tools, etc. derived from loaded plugins)
   client = anthropic.Anthropic()
   response = client.messages.create(
       model=model,
       system=build_system_prompt(session.plugins),
       messages=[{"role": "user", "content": prompt}],
   )

   # Access telemetry as Python objects — no JSONL parsing
   session_mgr.finalize(session)
   plugin_events = [e for e in captured_events if e["event_type"] == "plugin.loaded"]
   ```

2. **Add `build_system_prompt()` helper** — The harness needs to construct the
   system prompt from loaded plugins (rules, skills). Add a utility in the
   library:

   ```python
   # claude_kit/prompt.py
   def build_system_prompt(plugins: list[Plugin]) -> str:
       """
       Build a Claude system prompt from loaded plugins.

       Concatenates rules, skill content, and hook definitions into a
       single system prompt string suitable for anthropic.messages.create().
       """
       ...
   ```

   This extracts the logic currently embedded in `cmd_run()` that builds the
   `--append-system-prompt` or similar Claude flags.

3. **Update `test/harness/metrics.py`** — Metrics collection now uses
   `TelemetryEvent` objects instead of parsed JSONL:

   ```python
   from claude_kit.models import TelemetryEvent

   def extract_metrics(events: list[dict]) -> SessionMetrics:
       """Extract metrics from captured telemetry events."""
       session_start = next(
           e for e in events if e["event_type"] == "session.start"
       )
       session_end = next(
           e for e in events if e["event_type"] == "session.end"
       )
       return SessionMetrics(
           plugins_loaded=session_end["payload"]["plugins_loaded"],
           skills_invoked=session_end["payload"]["skills_invoked"],
           duration_s=session_end["payload"]["duration_s"],
           # ... token counts from Anthropic SDK response
       )
   ```

4. **Update `test/harness/scenario.py`** — Scenario files can now specify
   plugin loading mode:

   ```yaml
   # test/scenarios/smoke.yml
   name: smoke-test
   kit: core-kit
   mode: library  # NEW: use library import instead of subprocess
   turns:
     - prompt: "What is 2+2?"
       expect:
         contains: "4"
   ```

   The `mode: library` flag tells the runner to use the `claude_kit` import
   path. `mode: subprocess` (default for backward compatibility) uses the
   existing CLI invocation.

5. **Add integration test** — Create `test/test_harness_integration.py` that
   verifies the library-based harness produces equivalent results:

   ```python
   def test_library_mode_captures_telemetry():
       """Verify library mode captures telemetry without JSONL files."""
       from test.harness.runner import run_scenario
       from test.harness.scenario import load_scenario

       scenario = load_scenario("test/scenarios/smoke.yml")
       result = run_scenario(scenario, mode="library")
       assert result.metrics.plugins_loaded > 0
       assert result.metrics.duration_s > 0
       # No JSONL files should be created in library mode
       assert not list(Path("~/.claude-kit/telemetry/").expanduser().glob("*.jsonl"))
   ```

6. **Update `test/requirements.txt`** — Add `claude-kit` as a local dependency:

   ```
   anthropic>=0.40.0
   pyyaml>=6.0
   -e ..  # Install claude_kit from repo root
   ```

## Files to Create or Modify

| File | Action | Purpose |
|------|--------|---------|
| `test/harness/runner.py` | Modify | Import claude_kit instead of subprocess |
| `test/harness/metrics.py` | Modify | Use TelemetryEvent objects |
| `test/harness/scenario.py` | Modify | Add mode: library support |
| `claude_kit/prompt.py` | Create | System prompt builder from plugins |
| `claude_kit/__init__.py` | Modify | Add prompt builder export |
| `test/test_harness_integration.py` | Create | Library-mode integration test |
| `test/requirements.txt` | Modify | Add local claude_kit dep |

## Acceptance Criteria

- [ ] `test/harness/runner.py` imports from `claude_kit` (no subprocess for
  plugin loading)
- [ ] `run_scenario(scenario, mode="library")` captures telemetry as Python
  dicts — no JSONL file parsing
- [ ] Metrics extraction works with in-memory telemetry events
- [ ] `build_system_prompt(plugins)` produces the same prompt content as the
  CLI's session preparation
- [ ] Existing subprocess-mode scenarios still work (backward compatible)
- [ ] All existing 5-layer CI tests still pass
