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

## Three Version Dimensions

The QMS tracks three independent version dimensions:

### 1. Core QMS Version

The version of the Process Asset Library framework itself — templates,
instrumentation files, validation scripts, and the process document structure.
Tracked in `.claude/qms-manifest.json` as `coreVersion`. Bumped by the QMS
maintainers when the framework evolves.

```
coreVersion: "1.2.0"   ← set by install.sh / QMS_CORE_VERSION
```

### 2. Process Versions

Each `PROC-*.md` carries its own semantic version in its header. These evolve
independently of both the core version and the project version. Bumped when
process content changes (see "When to Bump" above).

### 3. User Revision

When a user installs the QMS and customizes it for their organization, they
track their revision number. This lets them say "We're on QMS core 1.2.0,
user revision 5" — distinguishing upstream framework changes from local
tailoring.

```
userRevision: 5         ← bumped via qms-revision command
```

### Version Independence

These three dimensions are fully independent:

```
Core QMS:       1.2.0   (upstream framework)
User Revision:  r5      (local customizations)
PROC-LC-004:    2.1.0   (individual process)
Project:        v3.0.0  (product version)
```

A project at `v3.0.0` might use QMS core `1.2.0` with user revision `r5`
and individual processes ranging from `1.0.0` to `2.1.0`.

### Update Flow

When the upstream QMS releases a new core version:

1. User runs `bash qms/install.sh --update`
2. The installer detects files the user has customized (marked with
   `<!-- qms-user-modified -->`)
3. Customized files are preserved (backed up, not overwritten)
4. Non-customized files are updated to the new version
5. `userRevision` is preserved across updates
6. Process document versions may be updated by the upstream release

### Customization Marker

Files customized by the user should include this HTML comment:

```markdown
<!-- qms-user-modified -->
```

This marker tells `install.sh --update` to skip the file during upgrades.
The `qms-revision` command can add this marker automatically.
