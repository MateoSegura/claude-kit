# Dependency Scanning Reference

## npm / Node.js Ecosystem

### npm audit

```bash
# Run audit
npm audit

# Show only high and critical
npm audit --audit-level=high

# Fix automatically (minor/patch updates only)
npm audit fix

# Fix including major version bumps (review carefully)
npm audit fix --force

# JSON output for CI parsing
npm audit --json
```

**Understanding output:**

```
# npm audit report

lodash  <4.17.21
  Severity: critical
  Prototype Pollution - https://github.com/advisories/GHSA-xxxx
  fix available via `npm audit fix`
  node_modules/lodash
```

Fields: package name, affected versions, severity, advisory link, fix availability.

### Dependabot Configuration (GitHub)

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
    # Group minor/patch updates to reduce PR noise
    groups:
      production-dependencies:
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"
    # Ignore specific packages
    ignore:
      - dependency-name: "aws-sdk"
        update-types: ["version-update:semver-major"]
```

### Renovate Bot Configuration

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "group:allNonMajor",
    ":automergeMinor",
    ":automergePatch"
  ],
  "packageRules": [
    {
      "matchUpdateTypes": ["major"],
      "labels": ["breaking-change"],
      "automerge": false
    },
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true,
      "automergeType": "pr",
      "requiredStatusChecks": ["ci/tests"]
    }
  ],
  "vulnerabilityAlerts": {
    "labels": ["security"],
    "automerge": true
  }
}
```

### Socket.dev

Detects supply chain attacks that traditional vulnerability scanners miss:

- Install scripts that download and execute code
- Obfuscated code in packages
- Network access from packages that should not need it
- Typosquatting detection
- Maintainer account changes

```yaml
# GitHub Action
- uses: socketsecurity/socket-security-action@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Python Ecosystem

### pip-audit

```bash
# Install
pip install pip-audit

# Audit installed packages
pip-audit

# Audit from requirements file
pip-audit -r requirements.txt

# Fix automatically
pip-audit --fix

# JSON output
pip-audit -f json

# Strict mode (fail on any finding)
pip-audit --strict
```

### Safety

```bash
# Install
pip install safety

# Check installed packages
safety check

# Check from requirements file
safety check -r requirements.txt

# JSON output
safety check --json
```

### Python-specific Risks

- `setup.py` can execute arbitrary code during `pip install`
- Always use `--no-build-isolation` carefully
- Prefer wheels (`.whl`) over source distributions when possible
- Use `pip install --require-hashes` for reproducible, verified installs:

```
# requirements.txt with hashes
requests==2.31.0 \
    --hash=sha256:58cd2187c01e70e6e26505bca751777aa9f2ee0b7f4300988b709f44e013003eb
```

## Go Ecosystem

### govulncheck

```bash
# Install
go install golang.org/x/vuln/cmd/govulncheck@latest

# Check all packages
govulncheck ./...

# JSON output
govulncheck -json ./...
```

**Key advantage:** govulncheck only reports vulnerabilities in code paths your application actually calls, reducing false positives significantly.

### Go-specific Practices

- `go.sum` provides cryptographic verification of module content
- Use `GONOSUMCHECK` and `GONOSUMDB` sparingly
- Use `GOPRIVATE` for internal modules (prevents leaking internal module names to sum database)
- Run `go mod tidy` regularly to remove unused dependencies
- Review `go.sum` changes in PRs

## Rust Ecosystem

### cargo-audit

```bash
# Install
cargo install cargo-audit

# Run audit
cargo audit

# Fix automatically
cargo audit fix

# JSON output
cargo audit --json
```

### cargo-deny

More comprehensive than cargo-audit — checks licenses, bans, and advisories:

```bash
# Install
cargo install cargo-deny

# Initialize configuration
cargo deny init

# Run all checks
cargo deny check
```

```toml
# deny.toml
[advisories]
vulnerability = "deny"
unmaintained = "warn"

[licenses]
allow = ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause"]
deny = ["GPL-3.0"]

[bans]
multiple-versions = "warn"
deny = [
    { name = "openssl" }  # prefer rustls
]
```

## Ruby Ecosystem

### bundler-audit

```bash
# Install
gem install bundler-audit

# Update advisory database
bundle audit update

# Run audit
bundle audit check

# CI-friendly
bundle audit check --update
```

## Java / JVM Ecosystem

### OWASP Dependency-Check

```xml
<!-- Maven plugin -->
<plugin>
    <groupId>org.owasp</groupId>
    <artifactId>dependency-check-maven</artifactId>
    <version>9.0.0</version>
    <configuration>
        <failBuildOnCVSS>7</failBuildOnCVSS>
    </configuration>
</plugin>
```

```bash
# Run
mvn dependency-check:check

# Gradle
gradle dependencyCheckAnalyze
```

## Container Scanning

### Trivy

```bash
# Install
brew install trivy  # or download binary

# Scan container image
trivy image myapp:latest

# Scan filesystem
trivy fs .

# Scan IaC (Terraform, CloudFormation, etc.)
trivy config .

# Generate SBOM
trivy image --format cyclonedx myapp:latest > sbom.json

# Severity filter
trivy image --severity HIGH,CRITICAL myapp:latest

# Ignore unfixed vulnerabilities
trivy image --ignore-unfixed myapp:latest

# Exit code for CI
trivy image --exit-code 1 --severity CRITICAL myapp:latest
```

### Grype

```bash
# Install
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh

# Scan image
grype myapp:latest

# Scan directory
grype dir:.

# Scan SBOM
grype sbom:./sbom.json

# Fail on severity
grype myapp:latest --fail-on high
```

## SBOM Generation

### Syft (by Anchore)

```bash
# Install
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh

# Generate SBOM from container image
syft myapp:latest -o cyclonedx-json > sbom.cdx.json
syft myapp:latest -o spdx-json > sbom.spdx.json

# Generate from directory
syft dir:. -o cyclonedx-json > sbom.cdx.json

# Generate from archive
syft myapp.tar -o cyclonedx-json > sbom.cdx.json
```

### cdxgen (CycloneDX Generator)

```bash
# Install
npm install -g @cyclonedx/cdxgen

# Generate SBOM
cdxgen -o sbom.json

# Specific project type
cdxgen -t python -o sbom.json
cdxgen -t node -o sbom.json
```

### SBOM in CI/CD

```yaml
# GitHub Actions example
jobs:
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          format: cyclonedx-json
          output-file: sbom.cdx.json

      - name: Scan SBOM for vulnerabilities
        uses: anchore/scan-action@v3
        with:
          sbom: sbom.cdx.json
          fail-build: true
          severity-cutoff: high
```

## CVSS Scoring Deep Dive

### CVSS v3.1 Metrics

**Base Score** (inherent severity):

| Metric | Values |
|--------|--------|
| Attack Vector (AV) | Network, Adjacent, Local, Physical |
| Attack Complexity (AC) | Low, High |
| Privileges Required (PR) | None, Low, High |
| User Interaction (UI) | None, Required |
| Scope (S) | Unchanged, Changed |
| Confidentiality (C) | None, Low, High |
| Integrity (I) | None, Low, High |
| Availability (A) | None, Low, High |

**Temporal Score** (changes over time):
- Exploit Code Maturity
- Remediation Level
- Report Confidence

**Environmental Score** (organization-specific):
- Modified base metrics based on your environment
- Security requirements (CIA) importance

### Interpreting CVSS in Practice

A CVSS score is a starting point, not the final word:

| Factor | Increases Real Risk | Decreases Real Risk |
|--------|-------------------|-------------------|
| Exposure | Internet-facing | Internal only, behind VPN |
| Data sensitivity | Handles PII/financial | Static public content |
| Exploit availability | Public exploit/PoC exists | Theoretical only |
| Compensating controls | None | WAF, network segmentation |
| Dependency role | Direct, runtime | Dev-only, test-only |

## License Compliance

### Common Open Source Licenses

| License | Type | Key Requirements |
|---------|------|-----------------|
| MIT | Permissive | Include license text |
| Apache-2.0 | Permissive | Include license, state changes, patent grant |
| BSD-2-Clause | Permissive | Include license text |
| BSD-3-Clause | Permissive | Include license, no endorsement |
| ISC | Permissive | Include license text |
| GPL-2.0 | Copyleft | Source distribution required for derivatives |
| GPL-3.0 | Copyleft | Source distribution, patent grant, anti-tivoization |
| LGPL-2.1 | Weak copyleft | Dynamic linking OK, static requires source |
| MPL-2.0 | Weak copyleft | Modified files must be shared |
| AGPL-3.0 | Strong copyleft | Network use triggers source distribution |

### License Scanning

```bash
# npm
npx license-checker --summary
npx license-checker --failOn 'GPL-3.0'

# Python
pip install pip-licenses
pip-licenses --summary

# Go
go install github.com/google/go-licenses@latest
go-licenses check ./...
```

## Update Strategy Decision Tree

```
Is this a security update?
  |
  YES → Update immediately, test, deploy
  |
  NO → Is this a major version bump?
        |
        YES → Schedule review, check changelog for breaking changes
        |     Run full test suite, update integration tests
        |     Deploy to staging first
        |
        NO → Is this a minor/patch bump?
              |
              YES → Auto-merge if CI passes (with established trust)
              |     Or batch with other updates weekly
```
