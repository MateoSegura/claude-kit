# PROC-LC-006: Release Management

**Version:** 1.0.0
**Status:** draft
**Category:** lifecycle
**Layer:** base
**Maturity:** initial
**Owner:** Release Manager
**Last Reviewed:** 2026-02-28

## 1. Purpose

Release Management governs how verified code changes are packaged, versioned, and published as releases in claude-kit. This process ensures that every release is traceable to its constituent changes via CHANGELOG entries, that version numbers follow semantic versioning conventions, and that the release pipeline produces consistent, encrypted artifacts. Without it, releases risk containing unverified changes or mismatched version metadata.

## 2. Scope

**Included:**
- Plugin version bumping (patch, minor, major) in `plugin.json` and README badges
- CHANGELOG.md authoring and formatting
- Release branch creation and management
- Git tag creation and GitHub Release publishing
- Tag-triggered CI validation and release artifact generation
- Plugin encryption for distribution

**Excluded:**
- Implementation work (governed by PROC-LC-004)
- Testing and verification (governed by PROC-LC-005)
- Deployment to end-user environments (governed by PROC-LC-007 when written)

## 3. Entry Criteria

- [ ] All planned changes for the release have been merged to `main`
- [ ] `fast-validate` and `validate-tier1` pass on `main`
- [ ] At least one plugin has been modified since the last release
- [ ] CHANGELOG.md has an `## [Unreleased]` section with entries for all changes

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Merged PRs since last release | GitHub PR history | PR metadata |
| Plugin version files | `plugins/*/. claude-plugin/plugin.json` | JSON with `version` field |
| CHANGELOG | `CHANGELOG.md` | Markdown with versioned sections |
| Current repo tag | `git tag --sort=-version:refname` | Semantic version tag |
| Plugin encryption script | `scripts/encrypt-plugins.sh` | Bash script |

## 5. Activities

### 5.1 Determine Version Bump

Review all plugin changes since the last release and determine the appropriate version bump for each modified plugin:

| Change type | Plugin bump |
|-------------|------------|
| Content fix, doc update, hook tweak, script fix | PATCH |
| New agent, command, or skill added | MINOR |
| Renamed/removed agent, command, or skill | MAJOR |

The repo tag version follows the highest-severity bump across all plugins in the release. If only CI, tooling, or repo-level files changed (no plugin changes), bump PATCH.

### 5.2 Create Release Branch

```bash
git checkout -b release/v<X.Y.Z>
```

This branch collects all release-specific changes: version bumps, CHANGELOG formatting, and README badge updates.

### 5.3 Bump Plugin Versions

For each modified plugin, update the version in two places:
1. `.claude-plugin/plugin.json` — the `"version"` field
2. `README.md` — the version badge line (`> **Role:** <Role> · **Version:** <version>`)

Both values must match exactly. The `/bump-plugin` command automates this.

### 5.4 Update CHANGELOG

Move entries from `## [Unreleased]` to a new `## [X.Y.Z]` section with the release date. The section header format is:

```
## [X.Y.Z] — YYYY-MM-DD
```

Group entries by type: Added, Changed, Fixed, Removed. Each entry references the relevant PR or commit.

### 5.5 Validate Release

Run the full validation suite on the release branch:

```bash
python3 -m py_compile claude-kit && \
bash scripts/test-cli.sh && \
python3 scripts/validate-plugins.py --all --strict && \
bash scripts/test-plugin-consistency.sh && \
bash scripts/validate-docs.sh
```

All layers must exit 0.

### 5.6 Merge Release Branch

Submit a PR from the release branch to `main`. Wait for all required CI checks to pass. Squash-merge to keep main history clean.

### 5.7 Tag and Publish

After the release branch is merged to main:

```bash
git checkout main && git pull
git tag -a v<X.Y.Z> -m "v<X.Y.Z>"
git push origin v<X.Y.Z>
```

The tag push triggers the `release.yml` workflow, which:
1. Runs Tier 1 strict validation
2. Verifies the CHANGELOG entry exists for this version
3. Extracts the CHANGELOG section for the release body
4. Creates the GitHub Release via `actions/github-script`

### 5.8 Encrypt Plugins for Distribution

For distribution releases, encrypt plugin content:

```bash
scripts/encrypt-plugins.sh --plugins-dir plugins/ --remove-plaintext
```

This creates `content.enc` blobs per plugin using AES-256-CBC encryption. The `--remove-plaintext` flag is only used for distribution artifacts, never during development.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Updated plugin.json files | `plugins/*/.claude-plugin/plugin.json` | — | — |
| Updated README badges | `plugins/*/README.md` | — | — |
| CHANGELOG entry | `CHANGELOG.md` | — | `## [X.Y.Z]` |
| Git tag | Git repository | — | `vX.Y.Z` |
| GitHub Release | GitHub Releases | — | — |
| Encrypted plugin bundles | Distribution artifacts | — | `content.enc` |

## 7. Exit Criteria

- [ ] All modified plugin versions are bumped and README badges match
- [ ] CHANGELOG has a dated `## [X.Y.Z]` section with all changes documented
- [ ] Release branch merged to `main` with all CI checks passing
- [ ] Git tag `vX.Y.Z` exists and has been pushed
- [ ] GitHub Release exists with the CHANGELOG section as the body
- [ ] `release.yml` workflow completed successfully

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Version consistency | `test-plugin-consistency.sh` | All plugin.json versions match their README badges |
| CHANGELOG integrity | `release.yml` step 2 | A `## [X.Y.Z]` entry exists in CHANGELOG.md matching the tag |
| Full validation | `validate-plugins.py --all --strict` | Exit code 0, no FATAL findings |
| CI release pipeline | `release.yml` workflow | All steps complete successfully |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Release Manager | Determines version bump, creates release branch, tags release |
| Developer | Bumps plugin versions, updates CHANGELOG entries |
| CI System | Validates release, creates GitHub Release from tag |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Release frequency | Number of releases per month | >= 2 | Count of `vX.Y.Z` tags per month |
| Release validation pass rate | Percentage of release tags where `release.yml` succeeds | 100% | GitHub Actions workflow history |
| Version accuracy | Percentage of releases with correctly bumped versions | 100% | Post-release audit of plugin.json vs CHANGELOG |
| Time from merge to release | Calendar hours from last PR merge to tag creation | < 24 hours | Git log timestamps |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.4.9 Software Release | This process implements the software release activities |
| ISO/IEC 12207:2017 | 6.3.6 Configuration Management (release baseline) | Tag creation establishes a release configuration baseline |
| CMMI-DEV v2.0 | CM (Configuration Management) | Covers CM SP 1.3 (create or release baselines) |

## 12. Tailoring Guidance

**Minimum viable process (patch release):** For releases containing only PATCH bumps, the CHANGELOG update and version bump may be combined into a single commit on the release branch. Full validation is still required.

**Full ceremony (major release):** For releases containing a MAJOR bump, the CHANGELOG must include a migration guide section. The release branch should be reviewed by at least two people. A dedicated test evidence record (TEST-XXX) should be created.

**Hotfix release:** For critical fixes that cannot wait for the regular release cadence, create a `hotfix/<description>` branch directly from the latest tag, apply the fix, and follow the abbreviated release flow. The CHANGELOG entry is still required.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-004 | Depends on: merged implementations accumulate toward a release |
| PROC-LC-005 | Depends on: passing tests gate release readiness |
| PROC-SP-001 | Extends: configuration management defines version baselines |
| PROC-SEC-005 | Related: encryption process runs during release packaging |
| PROC-SP-005 | Related: defect fixes may trigger release |

## 14. Traces

- **Governs:** `CHANGELOG.md`, `plugins/*/.claude-plugin/plugin.json` (version field), Git tags (`vX.Y.Z`), GitHub Releases
- **Enforced by:** `release.yml` (tag-triggered validation and release creation), `scripts/test-plugin-consistency.sh` (version badge matching), `scripts/encrypt-plugins.sh` (distribution encryption)
- **Related QA:** Version bump rules in `.claude/rules/plugin-versions.md`, release cadence guidance in `.claude/rules/git-workflow.md`

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing release management workflow with tag-triggered CI |
