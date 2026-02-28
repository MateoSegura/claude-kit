# Phase 03: Backend API & Authentication

## Objective

Build a Go HTTP API server with PostgreSQL that handles user registration, authentication (JWT + refresh tokens), API key management, and serves as the foundation for telemetry ingestion and dashboard data — containerized for Kubernetes deployment.

## Satisfies

- R7: User authentication — signup, login, JWT access tokens, refresh rotation, password reset
- R8: API key management — named keys with scopes, hashed at rest, CLI authentication
- R9: Go backend API with PostgreSQL — user management, health checks, structured logging

## Steps

1. [ ] Set up API server scaffold — `apps/backend/main.go` with `go-chi/chi` router, graceful shutdown, signal handling
2. [ ] Design ent schema — `ent/schema/` with entities: `User`, `APIKey`, `RefreshToken`, `Session` using ent's schema-first code generation
3. [ ] Implement database layer — use `entgo.io/ent` for type-safe ORM with `pgx/v5` driver, auto-migration in dev, versioned migrations for production
4. [ ] Implement user registration — `POST /auth/signup` with email validation, password hashing (argon2id), duplicate detection
5. [ ] Implement login flow — `POST /auth/login` returns JWT access token (15min TTL) + refresh token (30day TTL, stored hashed in DB)
6. [ ] Implement token refresh — `POST /auth/refresh` validates refresh token, rotates it (invalidates old, issues new pair), detects token reuse
7. [ ] Implement password reset — `POST /auth/forgot-password` sends reset email with time-limited token; `POST /auth/reset-password` validates token and updates password
8. [ ] Implement API key management — `POST /users/api-keys` creates named key with scopes; `GET /users/api-keys` lists keys (masked); `DELETE /users/api-keys/{id}` revokes key
9. [ ] Implement API key authentication — middleware that accepts `Authorization: Bearer ck_...` header, validates against hashed keys in DB, attaches user context
10. [ ] Implement auth middleware — JWT validation middleware for browser sessions, API key middleware for CLI sessions; both attach user to request context
11. [ ] Implement rate limiting — per-user and per-IP rate limiting with `golang.org/x/time/rate` or Redis-based token bucket
12. [ ] Implement health endpoints — `GET /health` (liveness), `GET /ready` (readiness — checks DB connection)
13. [ ] Implement structured logging — `zerolog` with request ID, user ID, duration, status code on every request
14. [ ] Implement CLI login command — `claude-kit login` opens browser for OAuth-style flow or accepts API key via `claude-kit login --api-key ck_...`
15. [ ] Create Docker configuration — `deploy/backend/Dockerfile` (multi-stage: build with Go, run with distroless), `deploy/backend/docker-compose.yml` for local dev (API + Postgres + Redis)
16. [ ] Write API integration tests — use `testcontainers-go` to spin up Postgres, test all auth flows end-to-end

## Files to Create/Modify

### Create
- `apps/backend/main.go` — server entry point (config loading, router setup, graceful shutdown)
- `apps/backend/routes/auth.go` — signup, login, refresh, forgot-password, reset-password handlers
- `apps/backend/routes/users.go` — user profile, API key CRUD handlers
- `apps/backend/routes/health.go` — liveness and readiness probes
- `apps/backend/middleware/auth.go` — JWT + API key authentication middleware
- `apps/backend/middleware/ratelimit.go` — rate limiting middleware
- `apps/backend/middleware/logging.go` — request logging middleware
- `apps/backend/middleware/cors.go` — CORS configuration
- `internal/auth/jwt.go` — JWT creation, validation, claims parsing (RS256)
- `internal/auth/apikey.go` — API key generation (`ck_` prefix), hashing (argon2id), validation
- `internal/auth/password.go` — password hashing and verification (argon2id)
- `internal/db/db.go` — connection pool setup, health check
- `internal/db/migrate.go` — migration runner (ent auto-migrate in dev, versioned in prod)
- `ent/schema/user.go` — User entity (fields, edges, indexes, validators)
- `ent/schema/apikey.go` — APIKey entity
- `ent/schema/refreshtoken.go` — RefreshToken entity
- `ent/schema/session.go` — Session entity
- `ent/generate.go` — `//go:generate go run -mod=mod entgo.io/ent/cmd/ent generate ./schema`
- `internal/config/server.go` — server configuration (env vars: `DATABASE_URL`, `JWT_PRIVATE_KEY`, `CORS_ORIGINS`, etc.)
- `deploy/backend/Dockerfile` — multi-stage build (Go builder → distroless runtime)
- `deploy/backend/docker-compose.yml` — local dev stack (API + Postgres + Redis)
- `apps/cli/cmd/login.go` — `claude-kit login` command
- `apps/cli/cmd/logout.go` — `claude-kit logout` command

### Modify
- `apps/cli/cmd/root.go` — add auth state loading (read stored API key/token from config dir)
- `internal/config/cli.go` — add auth config paths (`~/.config/claude-kit/credentials.json`)

## ent Schema Definitions

```go
// ent/schema/user.go
func (User) Fields() []ent.Field {
    return []ent.Field{
        field.UUID("id", uuid.UUID{}).Default(uuid.New),
        field.String("email").Unique().NotEmpty(),
        field.String("password").NotEmpty().Sensitive(),  // argon2id hash
        field.String("name").Optional(),
        field.Time("created_at").Default(time.Now),
        field.Time("updated_at").Default(time.Now).UpdateDefault(time.Now),
    }
}
func (User) Edges() []ent.Edge {
    return []ent.Edge{
        edge.To("api_keys", APIKey.Type),
        edge.To("sessions", Session.Type),
        edge.To("refresh_tokens", RefreshToken.Type),
    }
}

// ent/schema/apikey.go
func (APIKey) Fields() []ent.Field {
    return []ent.Field{
        field.UUID("id", uuid.UUID{}).Default(uuid.New),
        field.String("name").NotEmpty(),                  // user-chosen label
        field.String("key_prefix").NotEmpty(),            // first 8 chars (ck_abc1****)
        field.String("key_hash").NotEmpty().Sensitive(),  // argon2id hash of full key
        field.Strings("scopes").Optional(),               // e.g., ["telemetry:write", "sessions:read"]
        field.Time("last_used").Optional().Nillable(),
        field.Time("created_at").Default(time.Now),
        field.Time("revoked_at").Optional().Nillable(),   // soft delete
    }
}
func (APIKey) Edges() []ent.Edge {
    return []ent.Edge{
        edge.From("user", User.Type).Ref("api_keys").Unique().Required(),
    }
}

// ent/schema/session.go
func (Session) Fields() []ent.Field {
    return []ent.Field{
        field.UUID("id", uuid.UUID{}).Default(uuid.New),
        field.Time("started_at").Default(time.Now),
        field.Time("ended_at").Optional().Nillable(),
        field.Int("duration_secs").Optional(),
        field.Enum("mode").Values("interactive", "autonomous"),
        field.String("kit_name").Optional(),
        field.Strings("plugins_loaded").Optional(),
        field.String("model").Optional(),
        field.String("os").Optional(),                   // e.g., "darwin/arm64"
        field.String("cli_version").Optional(),
        field.JSON("metadata", map[string]any{}).Optional(),
    }
}
func (Session) Edges() []ent.Edge {
    return []ent.Edge{
        edge.From("user", User.Type).Ref("sessions").Unique().Required(),
        edge.From("api_key", APIKey.Type).Ref("sessions").Unique().Optional(),
    }
}
```

## API Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/auth/signup` | None | Create account |
| POST | `/auth/login` | None | Login, get tokens |
| POST | `/auth/refresh` | Refresh token | Rotate tokens |
| POST | `/auth/forgot-password` | None | Request reset email |
| POST | `/auth/reset-password` | Reset token | Set new password |
| GET | `/users/me` | JWT/API key | Get profile |
| PATCH | `/users/me` | JWT | Update profile |
| GET | `/users/api-keys` | JWT | List API keys (masked) |
| POST | `/users/api-keys` | JWT | Create API key |
| DELETE | `/users/api-keys/{id}` | JWT | Revoke API key |
| GET | `/health` | None | Liveness probe |
| GET | `/ready` | None | Readiness probe (DB check) |

## Acceptance Criteria

- [ ] `POST /auth/signup` creates a user and returns 201 with JWT + refresh token
- [ ] `POST /auth/login` returns 200 with JWT (15min TTL) + refresh token (30d TTL)
- [ ] `POST /auth/refresh` rotates the refresh token and issues a new JWT
- [ ] Reusing an old refresh token invalidates the entire token family (rotation attack detection)
- [ ] `POST /users/api-keys` returns a full API key (`ck_...`) that is only shown once; subsequent `GET` returns masked version
- [ ] API key in `Authorization: Bearer ck_...` header authenticates requests and attaches user context
- [ ] `claude-kit login --api-key ck_...` stores the key in `~/.config/claude-kit/credentials.json` and verifies it against the API
- [ ] `docker-compose up` in `deploy/backend/` starts a working API + Postgres stack
- [ ] All auth endpoints have integration tests using testcontainers-go
- [ ] Rate limiting returns 429 after threshold (configurable per environment)
- [ ] Health endpoints return 200 when healthy, 503 when DB is unreachable

## Dependencies

- Requires: Phase 01 (shared `internal/` packages, Go module)
- Blocks: Phase 04 (telemetry needs API endpoints), Phase 06 (dashboard needs API)
