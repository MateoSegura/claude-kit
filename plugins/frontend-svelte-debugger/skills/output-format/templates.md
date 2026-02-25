# Report Templates — Diagnostic Output

Ready-to-fill templates for each diagnostic scenario. Replace `<placeholder>` text with actual findings.

---

## Template 1: Single-Cause Diagnosis

Use when evidence clearly points to one root cause with high or medium confidence.

```
[<DOMAIN>] [<HIGH|MEDIUM>] — <one-sentence root cause>.

### Root Cause

<2-4 sentence explanation of what is wrong, why it happens, and how the
symptom relates to the cause. Be specific — name the rune, function,
file, or configuration involved.>

### Evidence

- `<file:line>` — <what this line shows and why it's relevant>
- `<file:line>` — <what this line shows and why it's relevant>
- <error message fragment> — <what it means in context>

### Fix

<numbered step-by-step corrective action>

1. <first step — most specific>
2. <second step if required>
3. <optional: config change or test to run after fix>

### Verification

Run `<command>` and confirm:
- <expected output or behavior that confirms the fix worked>
- <expected UI/console behavior after fix>
```

**Example (filled)**:

```
[REACTIVITY] [HIGH] — $state object destructured at call site breaks proxy tracking.

### Root Cause

`user.svelte.ts` line 12 destructures `{ name, age }` from a `$state` object.
Svelte's reactivity system tracks reads and writes through the Proxy object.
Destructuring extracts primitive values from the proxy at the time of destructuring,
breaking the tracking chain. Subsequent mutations to `user.name` do not cause the
local `name` variable to update, and the UI never re-renders with the new value.

### Evidence

- `src/lib/user.svelte.ts:12` — `let { name, age } = user;` — destructures $state proxy
- `src/lib/user.svelte.ts:28` — `name = 'Bob';` — assigns to local copy, not proxy
- `src/routes/+page.svelte:7` — `{name}` — reads local variable that never updates

### Fix

1. Remove the destructuring at line 12
2. Replace all uses of `name` with `user.name` and `age` with `user.age`
3. Delete the now-unused `let { name, age } = user;` line

### Verification

Run `npm run dev` and trigger the state change. The UI should update
immediately to reflect the new name without a page reload.
```

---

## Template 2: Multi-Cause Diagnosis

Use when symptoms involve two independent root causes.

```
[CROSS-DOMAIN] [<HIGH|MEDIUM>] — Two independent issues contributing to failure.

### Cause 1: [<DOMAIN>]

**Root Cause**: <explanation>

**Evidence**:
- `<file:line>` — <relevance>

**Fix**:
1. <step>

---

### Cause 2: [<DOMAIN>]

**Root Cause**: <explanation>

**Evidence**:
- `<file:line>` — <relevance>

**Fix**:
1. <step>

---

### Fix Order

Fix Cause 1 first — <reason why order matters OR "causes are independent, fix in either order">.

### Verification

After fixing both causes, run `<command>` and confirm:
- <verification for cause 1 fix>
- <verification for cause 2 fix>
```

---

## Template 3: Low-Confidence Diagnosis

Use when evidence is suggestive but not conclusive.

```
[<DOMAIN>] [LOW] — Probable cause: <hypothesis>. Additional evidence needed to confirm.

### Hypothesis

<explanation of the suspected cause and why the available evidence is consistent
with it, but also consistent with alternatives>

### Evidence Available

- <what was provided and what it suggests>

### Alternative Causes

1. <alternative A> — more likely if <condition>
2. <alternative B> — more likely if <condition>

### Recommended Diagnostic Steps

To confirm the hypothesis:

1. <specific thing to check or run>: `<command or code to add>`
2. <specific thing to check or run>: `<command or code to add>`

Share the output of step 1 to confirm or rule out the hypothesis.

### Provisional Fix (if hypothesis is confirmed)

<what to change if the hypothesis turns out to be correct>
```

---

## Template 4: Escalation (Insufficient Evidence)

Use when the description is too vague to diagnose responsibly.

```
[UNKNOWN] [INSUFFICIENT-EVIDENCE] — Cannot diagnose without additional information.

### What Was Provided

<brief summary of what the user gave — error message, symptom description, etc.>

### Information Needed

1. **<artifact name>** — <why it's needed>
   How to collect: `<command>`

2. **<artifact name>** — <why it's needed>
   How to collect: `<command or instruction>`

3. **<artifact name if needed>** — <why it's needed>

### Quick Checks While Collecting

While gathering the above, check these common causes for the described symptom:

- [ ] <quick check 1>
- [ ] <quick check 2>
```

**Example (filled)**:

```
[UNKNOWN] [INSUFFICIENT-EVIDENCE] — Cannot diagnose without the browser console output and stack trace.

### What Was Provided

"The component doesn't update when I click the button."

### Information Needed

1. **Browser console output** — Identifies runtime errors and Svelte warnings
   How to collect: Open DevTools (F12) → Console tab → reproduce the issue → copy all red/yellow output

2. **Component source code** — Needed to identify reactivity pattern in use
   How to collect: Share the `.svelte` file containing the button and the state it should update

3. **Stack trace** — Pinpoints the exact line causing any thrown error
   How to collect: Click the error link in the console to expand the stack

### Quick Checks While Collecting

- [ ] Is the button's `onclick` handler updating `$state` (not a plain `let` variable)?
- [ ] Is `let` used with `$state()` — `let count = $state(0)` — or just `let count = 0`?
- [ ] Does the component use Svelte 4 syntax (`$:`) mixed with Svelte 5 runes?
```

---

## Template 5: Environment Issue

Use when the failure is caused by the development environment, not the application code.

```
[ENVIRONMENT] [<HIGH|MEDIUM>] — <one-sentence description of environment issue>.

### Root Cause

<explanation of what in the environment is causing the failure — missing tool,
wrong version, missing env var, misconfigured tool, etc.>

### Evidence

- <environment artifact> — <what it shows>
- `<command output>` — <what it means>

### Fix

1. <environment change — install, configure, set env var, etc.>
2. <restart or rebuild step required after the change>

### Verification

Run `<command>` and confirm output matches:
```
<expected output>
```

### Note

This is an environment configuration issue, not an application bug. Application
code does not need to change.
```
