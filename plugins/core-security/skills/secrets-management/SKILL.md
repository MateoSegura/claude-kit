---
name: core-security:secrets-management
description: "Environment variables, vault systems, credential rotation, CI/CD secrets, and never-hardcode-credentials practices"
user-invocable: false
---

# Secrets Management Quick Reference

## Golden Rule

**Never hardcode credentials.** Not in source code, not in config files checked into version control, not in Docker images, not in logs.

## Secret Types

| Type | Examples | Risk if Leaked |
|------|----------|---------------|
| API keys | Stripe, AWS, GitHub tokens | Unauthorized API access, billing fraud |
| Database credentials | Connection strings, passwords | Data breach, data destruction |
| Signing keys | JWT secrets, code signing keys | Token forgery, supply chain compromise |
| Encryption keys | AES keys, TLS private keys | Data decryption, MITM attacks |
| Service accounts | OAuth client secrets, SA keys | Lateral movement, privilege escalation |
| SSH keys | Deploy keys, user private keys | Server access, code repository access |

## Environment Variables

**The baseline approach for local development and simple deployments.**

```bash
# .env file (NEVER commit this)
DATABASE_URL=postgres://user:pass@localhost:5432/mydb
API_KEY=sk-live-abc123
JWT_SECRET=your-random-secret-here
```

**Loading patterns:**
- Node.js: `dotenv` package or `--env-file` flag (v20.6+)
- Python: `python-dotenv` or `os.environ`
- Go: `godotenv` or `os.Getenv`
- Shell: `source .env` or `export $(cat .env | xargs)`

**Rules:**
- One `.env` per environment (`.env.development`, `.env.production`)
- Never share `.env` files via chat, email, or tickets
- Use `.env.example` (with dummy values) as a template for teammates

## .gitignore Essentials

Every project must ignore secret files from day one:

```gitignore
# Environment files
.env
.env.*
!.env.example

# Key files
*.pem
*.key
*.p12
*.pfx

# Cloud credentials
credentials.json
service-account*.json
.aws/credentials
.gcp/

# IDE and OS files that may contain tokens
.idea/
.vscode/settings.json
```

**If secrets were accidentally committed:**
1. Rotate the secret immediately — assume it is compromised
2. Remove from history with `git filter-repo` (preferred) or BFG Repo Cleaner
3. Force-push the cleaned history
4. Verify the secret is gone from all branches and tags

## Vault Systems (Concepts)

**What they provide:**
- Centralized secret storage with encryption at rest
- Access control policies (who can read which secrets)
- Audit logging (who accessed what, when)
- Automatic rotation
- Dynamic secrets (generated on demand, short-lived)

**Common solutions:**
- **HashiCorp Vault** — self-hosted or HCP, policy-based access
- **AWS Secrets Manager / Parameter Store** — native AWS integration
- **Azure Key Vault** — native Azure integration
- **GCP Secret Manager** — native GCP integration
- **1Password / Doppler** — developer-focused SaaS options

**When to use a vault vs. env vars:**
- Single developer, local project: `.env` files are fine
- Team project, shared secrets: vault or encrypted secret store
- Production deployment: always use platform-native secret management

## Credential Rotation

**Why rotate:**
- Limits blast radius if a secret is leaked
- Reduces window of exposure from undetected breaches
- Compliance requirement in many standards (SOC2, PCI-DSS)

**Rotation strategy:**

| Secret Type | Recommended Interval | Approach |
|-------------|---------------------|----------|
| API keys | 90 days or on suspicion | Generate new key, update consumers, revoke old |
| Database passwords | 90 days | Dual-credential rotation (new + old valid briefly) |
| Signing keys | Annually or on compromise | Overlap period, update all verifiers |
| TLS certificates | Before expiry (automate with ACME/Let's Encrypt) | Auto-renew 30 days before expiry |
| Personal tokens | 90 days | Regenerate in provider settings |

**Zero-downtime rotation pattern:**
1. Generate new credential
2. Configure application to accept both old and new
3. Roll out new credential to all consumers
4. Revoke old credential
5. Remove dual-acceptance configuration

## CI/CD Secrets

**Rules for pipeline secrets:**
- Store secrets in the CI platform's secret management (GitHub Actions Secrets, GitLab CI Variables, etc.)
- Never echo or print secrets in build logs
- Use environment-scoped secrets when available
- Restrict secret access to specific branches or environments
- Review workflow files for secret leakage before merging

**GitHub Actions example:**
```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

**Common mistakes:**
- Logging environment variables during debug (`printenv`, `env`)
- Using secrets in `run` commands that get shell-expanded into logs
- Storing secrets in workflow files or Dockerfiles
- Forking repos that have secrets configured (secrets do not transfer, but workflow code referencing them does)

## Never Hardcode Credentials Checklist

- [ ] No passwords, tokens, or keys in source code
- [ ] No secrets in Dockerfiles or docker-compose files
- [ ] No secrets in CI/CD workflow files (use platform secrets)
- [ ] No secrets in configuration files checked into git
- [ ] No secrets in log output or error messages
- [ ] No secrets in comments or documentation
- [ ] No secrets in commit messages
- [ ] `.env` and key files listed in `.gitignore`
- [ ] `.env.example` provided with placeholder values
- [ ] Pre-commit hooks scan for accidental secret commits

## Additional Resources

For detailed vault integration patterns, rotation implementation guides, and CI/CD platform-specific configuration, see [secrets-reference.md](secrets-reference.md).
