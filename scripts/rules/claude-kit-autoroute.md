# claude-kit Auto-Routing

## Session Awareness

You are using the **claude-kit plugin management system**. All skills listed in the system-reminder are already loaded and available — you do not need to "load", "activate", or "discover" them. They are ready to use immediately.

When the user asks what you can do, what's available, or about your capabilities:

1. Scan the skill list in the system-reminder
2. Group by role (engineer, tester, grader, debugger, knowledge) and core domain
3. Describe the capabilities naturally — what each role does and what commands it offers
4. Never tell the user to "load a skill" or "activate a plugin" — everything is already active

This applies universally regardless of which team is loaded (Zephyr, Python, Svelte, or any future team).

## Auto-Routing Rule

Before responding to any user message, scan the available skills listed in the system-reminder for intent matches. When a match is found, invoke the matching skill via the Skill tool IMMEDIATELY. Do not ask the user to type a slash command. Do not explain that a command exists. Just invoke it as if the user typed the command themselves.

Natural language IS implicit skill invocation. This rule overrides the default behavior of waiting for explicit `/command` syntax.

## How to Match

1. Extract the ACTION from the user's message (create, build, review, test, debug, plan, grade, etc.)
2. Scan the available skills in the system-reminder for a description that matches the action and context
3. If a match is found → invoke it via the Skill tool immediately
4. If the match is ambiguous between two skills → prefer the more specific one; if still ambiguous, ask briefly
5. If no match → respond normally without routing

## Team Resolution

For team-specific commands (engineer, grader, tester, debugger):

- If ONE team is loaded in the session → use it without asking
- If MULTIPLE teams are loaded → ask which team to use
- If NO matching role is loaded → inform the user and suggest how to load it

## Common Patterns

| Intent | Invoke |
|--------|--------|
| Create/build/make a plugin or team | `system-maker:make-team` |
| Update/enhance a plugin or team | `system-updater:update-team` |
| Review all plugins for quality | `system-updater:review-all` |
| Review and auto-fix all plugins | `system-updater:review-and-fix-all` |
| Implement/develop/code a feature | The loaded `*-engineer:develop` or `*-engineer:engineer` command |
| Plan/design/architect | The loaded `*-engineer:plan` command |
| Review code | The loaded `*-engineer:review` command (or `*-grader:grade` if no review exists) |
| Grade/evaluate/score code | The loaded `*-grader:grade` command |
| Compare implementations | The loaded `*-grader:compare` or `*-grader:grade-diff` command |
| Run/execute tests | The loaded `*-tester:test` or `*-tester:run-tests` command |
| Write/scaffold tests | The loaded `*-tester:scaffold-tests` command |
| Coverage report | The loaded `*-tester:coverage` or `*-tester:coverage-report` command |
| Debug/diagnose errors | The loaded `*-debugger:debug` or `*-debugger:diagnose` command |
| Create a project spec | `core-spec:new` |
| Check plan status | `core-spec:status` |
| Validate plugins | `validate-all` |
| Bump version | `bump-plugin` |
| Release/publish | `release` |
| Domain knowledge question | The matching `core-*` or `*-knowledge` skill |

## Exemptions

Do NOT auto-route when:

- The user explicitly says "don't use the plugin", "answer directly", or "without the command"
- The message is a greeting, acknowledgment, or general conversation
- The user is asking ABOUT a command rather than wanting to RUN it (e.g., "what does the grader do?")
- No matching skill is loaded in the current session
