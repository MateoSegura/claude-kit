# Secrets Management Reference

## Environment Variable Patterns by Platform

### Node.js

**Using dotenv:**

```javascript
// Load at application entry point
require('dotenv').config();

// Access variables
const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) {
  throw new Error('DATABASE_URL is required');
}
```

**Using native --env-file (Node 20.6+):**

```bash
node --env-file=.env app.js
```

**Validation pattern:**

```javascript
const required = ['DATABASE_URL', 'API_KEY', 'JWT_SECRET'];
for (const key of required) {
  if (!process.env[key]) {
    console.error(`Missing required environment variable: ${key}`);
    process.exit(1);
  }
}
```

### Python

**Using python-dotenv:**

```python
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env from current directory

db_url = os.environ['DATABASE_URL']  # raises KeyError if missing
api_key = os.environ.get('API_KEY', 'default-for-dev')  # with fallback
```

**Using pydantic-settings (recommended for typed config):**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False

    class Config:
        env_file = '.env'

settings = Settings()  # validates and parses from environment
```

### Go

**Using godotenv:**

```go
import (
    "os"
    "github.com/joho/godotenv"
)

func init() {
    godotenv.Load() // loads .env file
}

func main() {
    dbURL := os.Getenv("DATABASE_URL")
    if dbURL == "" {
        log.Fatal("DATABASE_URL is required")
    }
}
```

### Rust

**Using dotenvy:**

```rust
use std::env;

fn main() {
    dotenvy::dotenv().ok();
    let db_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
}
```

## .env File Best Practices

### File Hierarchy

```
.env                  # Default values (committed only if non-secret)
.env.local            # Local overrides (NEVER committed)
.env.development      # Development defaults
.env.production       # Production defaults (no real secrets)
.env.test             # Test environment defaults
.env.example          # Template with dummy values (ALWAYS committed)
```

**Loading priority** (varies by framework, typical order):
1. System environment variables (highest priority)
2. `.env.local`
3. `.env.{environment}`
4. `.env`

### .env.example Template

```bash
# Database
DATABASE_URL=postgres://user:password@localhost:5432/myapp_dev
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=replace-with-random-string-min-32-chars
SESSION_SECRET=replace-with-random-string

# External APIs
STRIPE_SECRET_KEY=sk_test_replace_me
SENDGRID_API_KEY=SG.replace_me

# Feature Flags
ENABLE_NEW_DASHBOARD=false
```

## Vault Integration Patterns

### HashiCorp Vault — Application Pattern

```
Application starts
  |
  v
Authenticate to Vault (AppRole, Kubernetes, AWS IAM, etc.)
  |
  v
Read secrets from Vault path
  |
  v
Cache secrets in memory (never on disk)
  |
  v
Renew lease before expiry
  |
  v
Re-read secrets on rotation event
```

**Key concepts:**
- **Paths**: Secrets organized in hierarchical paths (e.g., `secret/data/myapp/production`)
- **Policies**: Define which paths a token can read/write
- **Leases**: Secrets have TTL, application must renew or re-fetch
- **Dynamic secrets**: Vault generates unique credentials per request (e.g., database user/pass)

### AWS Secrets Manager Pattern

```python
import boto3
import json

def get_secret(secret_name, region="us-east-1"):
    client = boto3.client('secretsmanager', region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret('myapp/production/database')
db_password = secrets['password']
```

### GCP Secret Manager Pattern

```python
from google.cloud import secretmanager

def get_secret(project_id, secret_id, version="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")
```

### Azure Key Vault Pattern

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://myvault.vault.azure.net/",
    credential=credential
)

secret = client.get_secret("database-password")
db_password = secret.value
```

## CI/CD Secrets Configuration

### GitHub Actions

**Setting secrets:**
- Repository Settings > Secrets and variables > Actions
- Organization-level secrets for shared credentials
- Environment-level secrets for per-environment values

**Using secrets in workflows:**

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # uses environment-specific secrets
    steps:
      - name: Deploy
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
          API_KEY: ${{ secrets.API_KEY }}
        run: ./deploy.sh
```

**Security rules:**
- Secrets are masked in logs (but not foolproof — base64 encoding can bypass)
- Secrets are not passed to workflows from forked repositories
- Use `environment` protection rules for production secrets

### GitLab CI

```yaml
deploy:
  stage: deploy
  variables:
    DB_PASSWORD: $DB_PASSWORD  # from CI/CD Settings > Variables
  script:
    - ./deploy.sh
  environment:
    name: production
```

**Variable settings:**
- Mark as "Protected" — only available on protected branches
- Mark as "Masked" — hidden in job logs
- Scope to environment for granular access

### General CI/CD Rules

- Never echo environment variables in CI logs
- Use `--quiet` or redirect output when running commands that might print secrets
- Avoid passing secrets as command-line arguments (visible in process lists)
- Use file-based secrets when the platform supports it
- Audit who has access to modify CI/CD secrets
- Rotate CI/CD secrets on the same schedule as application secrets

## Credential Rotation Implementation

### Database Password Rotation (Zero Downtime)

```
Phase 1: Create new credentials
  - Generate new password
  - Create new database user (or update existing with new password)
  - Verify new credentials work

Phase 2: Deploy with dual acceptance
  - Application accepts both old and new credentials
  - Or: connection pool supports credential refresh

Phase 3: Roll out new credentials
  - Update secret store with new credentials
  - Restart/reload application instances
  - Verify all instances use new credentials

Phase 4: Revoke old credentials
  - Remove old password from database
  - Remove old credentials from secret store
  - Verify old credentials are rejected
```

### API Key Rotation

```
Phase 1: Generate new key in provider dashboard
Phase 2: Add new key to secret store alongside old key
Phase 3: Update application to use new key
Phase 4: Verify new key works in all environments
Phase 5: Revoke old key in provider dashboard
Phase 6: Remove old key from secret store
```

### JWT Signing Key Rotation

```
Phase 1: Generate new signing key
Phase 2: Add new key to JWKS (JSON Web Key Set)
  - New tokens signed with new key
  - Old tokens still verifiable with old key
Phase 3: Wait for all old tokens to expire
Phase 4: Remove old key from JWKS
```

## Pre-Commit Secret Detection

### git-secrets (AWS)

```bash
# Install
brew install git-secrets  # or from source

# Configure for a repository
cd my-repo
git secrets --install
git secrets --register-aws  # AWS-specific patterns

# Add custom patterns
git secrets --add 'PRIVATE KEY'
git secrets --add --allowed 'AKIAEXAMPLE'  # false positive
```

### detect-secrets (Yelp)

```bash
# Install
pip install detect-secrets

# Generate baseline
detect-secrets scan > .secrets.baseline

# Pre-commit hook
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### gitleaks

```bash
# Install
brew install gitleaks  # or download binary

# Scan repository
gitleaks detect --source .

# Pre-commit hook
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

### truffleHog

```bash
# Install
brew install trufflehog  # or pip install truffleHog

# Scan repository
trufflehog git file://. --only-verified
```

## Incident Response: Leaked Secret

### Immediate Actions (First 15 Minutes)

1. **Rotate the secret NOW** — do not wait for investigation
2. **Revoke the old secret** in the provider/service
3. **Check for unauthorized usage** — review access logs
4. **Assess blast radius** — what can this secret access?

### Follow-Up Actions

5. **Remove from git history** if committed:
   ```bash
   # Preferred: git-filter-repo
   git filter-repo --invert-paths --path secrets.env

   # Alternative: BFG Repo Cleaner
   java -jar bfg.jar --delete-files secrets.env
   java -jar bfg.jar --replace-text passwords.txt
   ```
6. **Force-push cleaned history** to all remotes
7. **Notify affected parties** if external data was exposed
8. **Add pre-commit hooks** to prevent recurrence
9. **Document the incident** for postmortem

### Common Leak Sources

| Source | Detection | Prevention |
|--------|-----------|------------|
| Git commit | `gitleaks`, `truffleHog` | Pre-commit hooks |
| CI/CD logs | Manual log review | Mask variables, avoid echo |
| Error messages | Application monitoring | Generic error responses |
| Docker images | `trivy`, `syft` | Multi-stage builds, `.dockerignore` |
| Stack traces | Error tracking tools | Redact secrets from crash reports |
| Browser dev tools | N/A | Never send secrets to client |
| Slack/email | DLP tools | Never share secrets via messaging |

## Docker Secrets

### Build-Time Secrets (BuildKit)

```dockerfile
# Dockerfile
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm install
```

```bash
# Build command
docker build --secret id=npmrc,src=.npmrc .
```

**Never use `ARG` or `ENV` for secrets** — they persist in image layers.

### Runtime Secrets (Docker Compose)

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - DATABASE_URL  # reads from host environment
    env_file:
      - .env  # reads from file
```

### Runtime Secrets (Docker Swarm)

```yaml
services:
  app:
    secrets:
      - db_password

secrets:
  db_password:
    external: true
```

Secrets mounted as files at `/run/secrets/<secret_name>`.

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  db-password: cGFzc3dvcmQ=  # base64 encoded (NOT encrypted)
```

**Important:** Kubernetes Secrets are base64-encoded, not encrypted at rest by default. Use:
- Sealed Secrets (Bitnami) for git-safe encrypted secrets
- External Secrets Operator to sync from vault
- Enable etcd encryption at rest in cluster configuration
