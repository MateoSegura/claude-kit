# Process Version Policy

Every process document carries an independent semantic version (`MAJOR.MINOR.PATCH`).
Process versions are decoupled from any project or product version.

## Version Format

```
PROC-LC-001: Requirements Engineering
Version: 1.2.0
        ^.^.^
        | | └─ PATCH: editorial, clarification, typo fix
        | └── MINOR: new activity, new quality gate, new metric
        └─── MAJOR: scope change, entry/exit criteria change, artifact restructure
```

## When to Bump

| Change Type | Bump | Examples |
|-------------|------|---------|
| Fix a typo, improve wording | PATCH | Clarify an activity description |
| Add a reference to Related Processes | PATCH | Link a newly created process |
| Add a new activity step | MINOR | Add a review gate to an existing workflow |
| Add a new quality gate | MINOR | Require a checklist that wasn't required before |
| Add a new metric | MINOR | Track a KPI that wasn't tracked before |
| Change entry or exit criteria | MAJOR | Require a new prerequisite artifact |
| Change scope (what's in/out) | MAJOR | Expand process to cover a new artifact type |
| Restructure outputs/artifacts | MAJOR | Move artifacts to different directories |

## New Process Versions

Every new process starts at `1.0.0`. Unlike code plugins (which start at
`0.0.1` to signal instability), processes start at `1.0.0` because:

1. A process document is either complete enough to use or it shouldn't exist
2. The `draft` status field already signals "not yet approved for use"
3. Version `1.0.0` + status `draft` means "first version, pending approval"

## Change History

Every process document has a `## 15. Change History` section formatted as:

```markdown
| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Name | Initial release |
```

Each version bump requires a new row in this table.

## Version in Metadata

The version field appears in the process document header:

```markdown
**Version:** 1.2.0
```

No version field exists in any separate metadata file. The process document
is the single source of truth for its own version.

## Immutability of Major Versions

When a process undergoes a MAJOR version change, the previous major version's
behavior is documented in the Change History. Unlike ADRs (which are never
edited once accepted), process documents ARE edited in place — the Change
History table provides the audit trail.

## Relationship to Project Versions

Process versions have no relationship to repository tags, release versions,
or product versions. A project at `v2.5.0` might use processes ranging from
`1.0.0` to `3.1.2`. This independence is by design — processes evolve at
their own pace based on organizational learning, not product release cadence.
