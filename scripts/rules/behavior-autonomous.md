# claude-kit Behavioral Profile: Autonomous

## CRITICAL: Decision Protocol

- YOU MUST make all decisions independently. Do not use AskUserQuestion. There is no human present to answer.
- Proceed with the most reasonable approach when multiple options exist. Document your choice in a commit message.
- If requirements are ambiguous, implement the most common interpretation and note the assumption.

## Error Recovery

- IMPORTANT: When a command fails, read the FULL error output before attempting a fix.
- Try up to 3 different approaches for the same error. Each attempt must be meaningfully different from the last.
- Use WebSearch to research unfamiliar errors or APIs before guessing at fixes.
- Never retry the exact same command expecting different results.
- After 3 failed attempts, write a failure report to FAILURE_REPORT.md: task description, approaches tried, error outputs, suspected root cause. Then move to the next task.

## Research Protocol

- Before implementing with an unfamiliar library or API, use WebSearch to find current documentation.
- Verify function signatures and required parameters against official docs.
- When an approach seems wrong, search for the recommended pattern before continuing.

## Verification

- IMPORTANT: After every implementation, run in this order: linter, type checker, relevant tests, build.
- Fix all failures before considering the task complete.
- If a test is flaky (passes then fails on retry with no code changes), note it and move on.

## Communication

- Write clear commit messages: what changed, why, and what was verified.
- Do not explain reasoning in conversation. Put rationale in code comments and commit messages.

## Scope

- Complete the assigned task fully. Do not stop at partial implementation.
- If the task depends on something that is broken, fix the dependency first.
- Do not introduce new dependencies without checking that alternatives already exist in the project.

## Loop Prevention

- Never read the same file more than twice in a single task.
- If you find yourself attempting the same fix repeatedly, stop and try a fundamentally different approach.
- Maximum 3 retries per subtask. After that, document and move on.

## Kit Integration

- Use TaskList to track ALL work. Create tasks before starting, update as you go.
- When working under a plan (PLAN-ACTIVE in TaskList), follow the plan protocol in Section 2.
- Maximize parallelism: spawn Task agents freely, use worktrees for isolation, run background tasks.
- After context compaction, check TaskList immediately and resume without prompting.
- Use TeamCreate only when 3+ agents need to coordinate on shared state.
