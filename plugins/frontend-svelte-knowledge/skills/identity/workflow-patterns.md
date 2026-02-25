# Knowledge Plugin Usage Patterns

This document describes how companion role plugins (engineer, grader, tester) consume the domain knowledge provided by `frontend-svelte-knowledge`.

## How Skills Are Loaded

1. Each role plugin lists `frontend-svelte-knowledge` as a companion in its `ctl.json`
2. When a role plugin's agent needs domain knowledge, it references a skill by name in its `skills:` frontmatter field
3. Claude auto-loads the skill's `SKILL.md` when the task matches the skill's description
4. Detailed reference files (e.g., `reference.md`, `examples.md`) are loaded on demand when Claude reads them

## Skill Consumption by Role

### Engineer

The engineer plugin uses ALL seven domain skills:

| Skill | Engineer Usage |
|---|---|
| svelte5-runes | Writing reactive code, choosing the correct rune for each scenario |
| sveltekit-patterns | Route setup, load functions, form actions, SSR strategy |
| component-patterns | Building composable, typed component APIs |
| css-architecture | Implementing design tokens, theming, responsive layouts |
| human-centered-design | Applying spacing, typography, and transition principles |
| accessibility | Baking WCAG 2.2 AA into every component from the start |
| desktop-targets | Adapting web code for Tauri/Electron when targeting desktop |
| usb-serial-hid | Implementing serial/USB/HID communication in Tauri commands |
| ble-communication | Building BLE scanning and GATT interaction features |
| lan-discovery | Implementing network device discovery and TCP/UDP communication |
| audio-midi-devices | Adding audio capture/playback and MIDI support |
| hardware-abstraction | Structuring device management architecture and IoT protocols |

### Grader

The grader plugin references domain skills as the authoritative standard against which code is scored:

| Skill | Grader Usage |
|---|---|
| svelte5-runes | Verify rune usage is correct, flag Svelte 4 patterns as critical defects |
| component-patterns | Score component API design, composition quality, prop typing |
| css-architecture | Evaluate token usage, naming, responsive strategy |
| human-centered-design | Score visual hierarchy, spacing consistency, transition quality |
| accessibility | Score against WCAG 2.2 AA checklist, flag violations |
| usb-serial-hid | Verify correct crate usage, error handling, resource cleanup |
| ble-communication | Score BLE state management, permission handling, cross-platform correctness |
| hardware-abstraction | Evaluate device architecture patterns, error recovery, anti-patterns |

### Tester

The tester plugin references skills to generate correct test patterns:

| Skill | Tester Usage |
|---|---|
| svelte5-runes | Test reactive state behavior, derived values, effects |
| sveltekit-patterns | Test load functions, form actions, route guards, error boundaries |
| component-patterns | Component rendering tests, prop validation, event handling |
| accessibility | Automated a11y audit integration (axe-core), keyboard navigation tests |
| hardware-abstraction | Test device state machines, mock hardware connections, error recovery paths |

## Common Lookup Patterns

### Pattern 1: Rune Selection

When an engineer agent needs to decide which rune to use:
1. The `svelte5-runes` skill auto-loads based on task context
2. The SKILL.md provides the quick-reference rune decision table
3. If deeper API details are needed, Claude reads `rune-api-reference.md`

### Pattern 2: Grading Against Standards

When the grader agent scores a component:
1. The relevant skill (e.g., `accessibility`) auto-loads
2. The SKILL.md provides the checklist or scoring criteria
3. The grader cross-references the code against each criterion
4. Violations are cited with the specific standard from the knowledge skill

### Pattern 3: Test Generation

When the tester agent writes component tests:
1. `component-patterns` loads to understand expected component behavior
2. `svelte5-runes` loads for correct reactive state testing patterns
3. The tester generates tests that verify the patterns documented in these skills

### Pattern 4: Desktop Adaptation

When building for Tauri or Electron:
1. The `desktop-targets` skill loads when the task mentions desktop, Tauri, or Electron
2. Provides IPC patterns, native API usage, platform-specific considerations
3. Other skills (components, CSS) remain applicable — desktop builds are still Svelte

### Pattern 5: Hardware Device Integration

When building hardware-connected features:
1. The `hardware-abstraction` skill loads for architecture patterns (device traits, async streams, state machines)
2. The specific hardware skill loads for API reference (`usb-serial-hid`, `ble-communication`, `lan-discovery`, or `audio-midi-devices`)
3. The `desktop-targets` skill provides the Tauri IPC foundation all hardware skills build upon

## Skill Independence

Each skill is self-contained. Skills do not reference each other's internal files. This means:
- Any skill can be loaded independently without pulling in the full plugin
- Role plugins can selectively include only the skills relevant to their agents
- Skills can be updated independently without cascading changes
