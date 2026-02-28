# PROC-SP-001: Configuration Management

**Version:** 1.0.0
**Status:** draft
**Category:** support
**Layer:** base
**Maturity:** initial
**Owner:** Configuration Manager
**Last Reviewed:** 2026-02-28

## 1. Purpose

Configuration Management governs how all versioned artifacts in claude-kit are identified, baselined, changed, and tracked. This process ensures that the git repository, plugin versions, branch naming, and merge strategies maintain a consistent and auditable state. It underpins every other lifecycle process by providing the version control discipline that makes traceability possible.

## 2. Scope

**Included:**
- Git repository management (branching, merging, tagging)
- Branch naming convention enforcement (`<type>/<description>`)
- Plugin version identification and tracking (`plugin.json` version field)
- Configuration baselines (release tags, main branch state)
- Merge strategy (squash merge to main)
- File structure conventions (plugin directory layout, docs/ structure)

**Excluded:**
- Content of plugin files (governed by PROC-LC-004)
- Release publishing (governed by PROC-LC-006)
- Encryption of configuration items for distribution (governed by PROC-SEC-005)

## 3. Entry Criteria

- [ ] Git repository exists with `main` as the primary branch
- [ ] CI workflows are configured in `.github/workflows/`
- [ ] Branch naming enforcement is active in `push.yml`

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Git workflow rules | `.claude/rules/git-workflow.md` | Markdown rule file |
| Plugin version convention | `.claude/rules/plugin-versions.md` | Markdown rule file |
| Plugin conventions | `.claude/rules/plugin-conventions.md` | Markdown rule file |
| CI workflow definitions | `.github/workflows/*.yml` | YAML workflow files |
| Plugin directory structure | `plugins/` | File system hierarchy |

## 5. Activities

### 5.1 Identify Configuration Items

Every artifact in the repository is a configuration item (CI). The primary CIs are:

| Configuration Item | Location | Version Mechanism |
|-------------------|----------|-------------------|
| CLI executable | `claude-kit` | Repo release tag |
| Plugin content | `plugins/<name>/` | `plugin.json` version field |
| CI/CD pipelines | `.github/workflows/` | Git commit history |
| Agent rules | `.claude/rules/` | Git commit history |
| Documentation | `docs/` | Document status fields |
| QMS processes | `qms/` | Process version fields |
| Templates | `templates/`, `qms/templates/` | Git commit history |
| Scripts | `scripts/` | Git commit history |

### 5.2 Manage Branches

All development occurs on feature branches created from `main`. Branch names must follow the enforced convention:

```
<type>/<short-description>
```

Valid types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `style`, `release`, `hotfix`. The `push.yml` workflow rejects any branch that does not match this pattern (skipped for pushes directly to main).

### 5.3 Establish Baselines

Two types of baselines exist:

1. **Development baseline** — the `main` branch represents the latest integrated state. All PRs target main via squash merge.
2. **Release baseline** — git tags (`vX.Y.Z`) mark release points. Each tag is immutable once pushed and corresponds to a GitHub Release.

### 5.4 Control Changes

All changes flow through the following pipeline:
1. Create feature branch from `main`
2. Commit changes with Conventional Commits format
3. Push branch (triggers `fast-validate`)
4. Open PR to `main` (triggers `pr-validate`)
5. Pass required CI checks
6. Squash merge to `main`

Direct commits to `main` are prohibited by process (and should be protected by GitHub branch protection rules).

### 5.5 Track Plugin Versions

Each plugin maintains an independent version in `.claude-plugin/plugin.json`. The version badge in the plugin's `README.md` must always match. Version bumps follow the semantic versioning rules documented in `.claude/rules/plugin-versions.md`:
- PATCH for content improvements
- MINOR for new agents, commands, or skills
- MAJOR for breaking changes

### 5.6 Audit Configuration State

The `test-plugin-consistency.sh` script verifies configuration integrity:
- README version badge matches `plugin.json` version
- Agent skill cross-references resolve to real companion skills
- Hook event types are valid
- Frontmatter key names are correct for each file type
- CHANGELOG version entries align with plugin.json versions

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Feature branches | Git repository | — | `<type>/<description>` |
| Release tags | Git repository | — | `vX.Y.Z` |
| Plugin version files | `plugins/*/.claude-plugin/plugin.json` | `plugin.json.tmpl` | — |
| Version badges | `plugins/*/README.md` | — | — |

## 7. Exit Criteria

- [ ] All configuration items are under version control in git
- [ ] Branch naming convention is enforced by CI
- [ ] Plugin versions are consistent (plugin.json matches README badge)
- [ ] Release baselines are established via immutable tags
- [ ] Squash merge strategy is used for all PRs to main

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Branch naming | `push.yml` CI check | Branch matches `<type>/<description>` or is `main` |
| Version consistency | `test-plugin-consistency.sh` | All plugin.json versions match README badges |
| Configuration integrity | `validate-plugins.py --all --strict` | All plugins pass structural validation |
| Baseline immutability | Git tag protection | Release tags are never moved or deleted |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Configuration Manager | Maintains version conventions, audits configuration integrity |
| Developer | Creates branches following naming convention, bumps plugin versions |
| CI System | Enforces branch naming, runs configuration validation |
| Release Manager | Creates release baselines (tags) |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Branch naming compliance | Percentage of branches matching the convention | 100% | CI enforcement logs in `push.yml` |
| Version consistency rate | Percentage of plugins where plugin.json matches README badge | 100% | `test-plugin-consistency.sh` output |
| Merge strategy compliance | Percentage of PRs merged via squash merge | 100% | Git log audit (single-commit merges on main) |
| Orphan branch count | Number of branches older than 30 days not merged | 0 | `git branch -r --sort=-committerdate` audit |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.3.6 Configuration Management | This process directly implements software configuration management |
| ISO/IEC 12207:2017 | 6.3.6.3 Configuration Control | Activities 5.2-5.4 implement configuration control |
| CMMI-DEV v2.0 | CM (Configuration Management) | Covers CM SP 1.1 (identify items), SP 1.2 (establish system), SP 2.1 (track change requests), SP 1.3 (create baselines) |

## 12. Tailoring Guidance

**Minimum viable process (single developer):** Branch naming and version consistency are still enforced by CI. The squash merge strategy is the only supported merge method regardless of team size.

**Full ceremony (multi-team):** When multiple teams work concurrently, release baselines should be coordinated to avoid version conflicts. Cross-team consistency checks (`.claude/rules/cross-team-consistency.md`) become mandatory for every merge.

**Hotfix variant:** Hotfix branches (`hotfix/<description>`) may branch from a release tag rather than main. They follow the same naming and validation rules but target a specific release baseline.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-004 | Depends on: Implementation uses branches and commits managed by this process |
| PROC-LC-006 | Depends on: Release Management creates baselines using tags from this process |
| PROC-SP-002 | Related: Quality Assurance verifies configuration integrity |
| PROC-SP-006 | Related: Peer Review validates changes before merge |
| PROC-SEC-001 | Related: Secure Development relies on configuration control to prevent unauthorized changes |

## 14. Traces

- **Governs:** Git branches, Git tags (`vX.Y.Z`), `plugins/*/.claude-plugin/plugin.json`, `plugins/*/README.md` (version badge)
- **Enforced by:** `push.yml` (branch naming enforcement), `scripts/test-plugin-consistency.sh` (version badge matching), `scripts/validate-plugins.py` (structural validation)
- **Related QA:** Branch naming rules in `.claude/rules/git-workflow.md`, version conventions in `.claude/rules/plugin-versions.md`

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing git workflow and plugin version management |
