# Intent Mapping Reference

Complete mapping of natural language patterns to claude-kit skills. Each row shows user intent patterns and the corresponding skill to invoke.

## Plugin Management

| User says something like... | Skill to invoke |
|---|---|
| "create a plugin", "build a new agent", "make a plugin for X", "I need a plugin that does X", "create a team", "build a full team for X", "I need engineer + grader + tester for X" | `system-maker:make-team` |
| "update this plugin", "add a skill to X", "enhance this plugin", "modify the plugin", "update the whole team", "update all plugins", "enhance all roles in X team" | `system-updater:update-team` |
| "review all plugins", "check plugin quality", "audit the plugins", "plugin health report" | `system-updater:review-all` |
| "fix all plugins", "review and fix plugins", "auto-fix plugin issues" | `system-updater:review-and-fix-all` |
| "validate plugins", "check plugin quality", "run validation" | `validate-all` |
| "semantic review of plugins", "deep review plugin quality" | `system-maker:validate` |
| "bump the version", "increment version", "update the version number" | `bump-plugin` |
| "release", "publish", "cut a release", "tag a release" | `release` |

## Engineering — Develop

| User says something like... | Skill pattern |
|---|---|
| "implement X", "build X feature", "develop X", "write code for X", "code this up" | `*-engineer:develop` or `*-engineer:engineer` |
| "scaffold a new project", "set up the project", "initialize the application" | `*-engineer:develop` or `*-engineer:engineer` |

**Note:** The engineer develop command name varies by team:
- `embedded-zephyr-engineer:develop`
- `frontend-svelte-engineer:develop`
- `cloud-python-engineer:engineer`

When resolving, match any loaded skill whose name ends with `-engineer:develop` or `-engineer:engineer`.

## Engineering — Plan

| User says something like... | Skill pattern |
|---|---|
| "plan the architecture", "design the system", "plan how to build X", "what's the best approach for X" | `*-engineer:plan` |
| "architect this", "create an architecture for X", "design the technical approach" | `*-engineer:plan` |

All teams use `plan` as the command name.

## Engineering — Review

| User says something like... | Skill pattern |
|---|---|
| "review my code", "code review", "check my changes", "look at what I wrote", "PR review" | `*-engineer:review` |

**Note:** Not all teams have a review command. Currently available:
- `embedded-zephyr-engineer:review`
- `frontend-svelte-engineer:review`

If no review command is loaded, fall back to the grader's grade command.

## Grading — Grade

| User says something like... | Skill pattern |
|---|---|
| "grade my code", "evaluate this code", "score this implementation", "rate this code" | `*-grader:grade` |
| "how good is this code", "is this code any good", "what would you score this" | `*-grader:grade` |
| "blind review", "objective evaluation", "quantitative assessment" | `*-grader:grade` |

All teams use `grade` as the command name.

## Grading — Compare

| User says something like... | Skill pattern |
|---|---|
| "compare these implementations", "which approach is better", "A vs B comparison" | `*-grader:compare` or `*-grader:grade-diff` |
| "compare before and after", "diff these approaches", "evaluate the improvement" | `*-grader:compare` or `*-grader:grade-diff` |

**Note:** Command name varies:
- `embedded-zephyr-grader:compare`
- `frontend-svelte-grader:compare`
- `cloud-python-grader:grade-diff`

## Testing — Run Tests

| User says something like... | Skill pattern |
|---|---|
| "run tests", "test this", "execute tests", "run the test suite" | `*-tester:test` or `*-tester:run-tests` |
| "does this pass tests", "check if tests pass", "verify with tests" | `*-tester:test` or `*-tester:run-tests` |

**Note:** Command name varies:
- `embedded-zephyr-tester:test`
- `frontend-svelte-tester:test`
- `cloud-python-tester:run-tests`

## Testing — Scaffold Tests

| User says something like... | Skill pattern |
|---|---|
| "write tests for X", "scaffold tests", "create test files", "generate tests" | `*-tester:scaffold-tests` |
| "I need tests for this module", "add test coverage for X" | `*-tester:scaffold-tests` |

All teams use `scaffold-tests` as the command name.

## Testing — Coverage

| User says something like... | Skill pattern |
|---|---|
| "coverage report", "show test coverage", "how much is covered", "coverage analysis" | `*-tester:coverage` or `*-tester:coverage-report` |

**Note:** Command name varies:
- `embedded-zephyr-tester:coverage`
- `frontend-svelte-tester:coverage`
- `cloud-python-tester:coverage-report`

## Debugging

| User says something like... | Skill pattern |
|---|---|
| "debug this", "why is this crashing", "diagnose this error", "what's causing this failure" | `*-debugger:debug` or `*-debugger:diagnose` |
| "read the crash log", "analyze this stack trace", "why did this fail" | `*-debugger:debug` or `*-debugger:diagnose` |

**Note:** Command name varies:
- `embedded-zephyr-debugger:debug`
- `cloud-python-debugger:debug`
- `frontend-svelte-debugger:diagnose`

## Project Planning

| User says something like... | Skill to invoke |
|---|---|
| "create a spec", "plan this project", "write the requirements", "spec out this feature" | `core-spec:new` |
| "what's the plan status", "show progress", "where are we", "plan status" | `core-spec:status` |

## Domain Knowledge

When the user asks a knowledge question (not action-oriented), match against loaded knowledge skills:

| Topic area | Possible skills |
|---|---|
| Design patterns, SOLID, architecture | `core-architecture:design-patterns`, `core-architecture:solid-principles`, `core-architecture:clean-architecture` |
| API design, REST, GraphQL, gRPC | `core-architecture:api-design`, `core-backend:api-protocols` |
| Git workflows, branching, commits | `core-git:branching-strategies`, `core-git:commit-conventions`, `core-git:advanced-operations` |
| Security, secrets, dependencies | `core-security:secure-coding`, `core-security:secrets-management`, `core-security:threat-modeling` |
| Testing philosophy, TDD, mocks | `core-testing:test-philosophy`, `core-testing:tdd-bdd`, `core-testing:test-doubles` |
| CI/CD, Docker, Kubernetes, deployment | `core-devops:ci-cd-patterns`, `core-devops:containerization`, `core-devops:deployment-strategies` |
| CSS, accessibility, components, UX | `core-frontend:css-architecture`, `core-frontend:accessibility`, `core-frontend:component-architecture` |
| Database, auth, message queues | `core-backend:database-patterns`, `core-backend:auth-patterns`, `core-backend:message-queues` |
| RTOS, HAL, embedded protocols, power | `core-embedded:rtos-fundamentals`, `core-embedded:hal-patterns`, `core-embedded:comm-protocols` |

Only invoke knowledge skills that are actually loaded in the current session. If the relevant knowledge plugin is not loaded, answer from parametric knowledge and mention that the knowledge plugin exists.

## Configuration

| User says something like... | Skill to invoke |
|---|---|
| "customize keybindings", "rebind keys", "change keyboard shortcuts" | `keybindings-help` |
