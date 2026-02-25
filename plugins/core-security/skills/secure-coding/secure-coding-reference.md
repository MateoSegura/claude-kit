# Secure Coding Reference

## SQL Injection — In Depth

### How It Works

An attacker injects SQL syntax through user-controlled input that is concatenated directly into a query string.

```
User input:  ' OR 1=1 --
Query:       SELECT * FROM users WHERE name = '' OR 1=1 --'
Result:      Returns ALL users
```

### Prevention by Language

**JavaScript (Node.js):**

```javascript
// WRONG — string concatenation
const query = `SELECT * FROM users WHERE id = ${userId}`;

// RIGHT — parameterized query (pg)
const result = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);

// RIGHT — parameterized query (mysql2)
const [rows] = await connection.execute('SELECT * FROM users WHERE id = ?', [userId]);
```

**Python:**

```python
# WRONG — string formatting
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# RIGHT — parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# RIGHT — SQLAlchemy ORM
user = session.query(User).filter(User.id == user_id).first()
```

**Go:**

```go
// WRONG — string concatenation
query := fmt.Sprintf("SELECT * FROM users WHERE id = %s", userID)

// RIGHT — parameterized query
row := db.QueryRow("SELECT * FROM users WHERE id = $1", userID)
```

**Java:**

```java
// WRONG — string concatenation
String query = "SELECT * FROM users WHERE id = " + userId;

// RIGHT — prepared statement
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
ps.setInt(1, userId);
```

### ORM Safety Notes

ORMs generally protect against SQL injection, but raw query methods bypass this:

```python
# Safe — ORM handles parameterization
User.objects.filter(id=user_id)

# DANGEROUS — raw SQL with string formatting
User.objects.raw(f"SELECT * FROM users WHERE id = {user_id}")

# Safe — raw SQL with parameters
User.objects.raw("SELECT * FROM users WHERE id = %s", [user_id])
```

## Command Injection — In Depth

### How It Works

An attacker injects shell metacharacters through input passed to a system shell.

```
User input:  ; rm -rf /
Command:     ping ; rm -rf /
Result:      Executes both ping AND rm -rf /
```

### Dangerous Shell Metacharacters

| Character | Meaning |
|-----------|---------|
| `;` | Command separator |
| `&&` | Execute next if previous succeeds |
| `\|\|` | Execute next if previous fails |
| `\|` | Pipe output to next command |
| `` ` `` | Command substitution |
| `$()` | Command substitution |
| `>` / `>>` | Redirect/append output |
| `<` | Redirect input |
| `\n` | Newline (command separator) |

### Prevention by Language

**JavaScript (Node.js):**

```javascript
// WRONG — shell execution
const { exec } = require('child_process');
exec(`ping ${hostname}`);

// RIGHT — no shell, arguments as array
const { execFile } = require('child_process');
execFile('ping', ['-c', '4', hostname]);

// RIGHT — spawn with shell: false (default)
const { spawn } = require('child_process');
spawn('ping', ['-c', '4', hostname]);
```

**Python:**

```python
# WRONG — shell=True
subprocess.run(f"ping {hostname}", shell=True)

# RIGHT — arguments as list, no shell
subprocess.run(["ping", "-c", "4", hostname])

# RIGHT — shlex.quote if shell is absolutely required
import shlex
subprocess.run(f"ping {shlex.quote(hostname)}", shell=True)
```

**Go:**

```go
// WRONG — shell execution
exec.Command("sh", "-c", "ping " + hostname).Run()

// RIGHT — direct execution with arguments
exec.Command("ping", "-c", "4", hostname).Run()
```

## Path Traversal — In Depth

### How It Works

An attacker uses `..` sequences or absolute paths to access files outside the intended directory.

```
User input:  ../../../etc/passwd
Path:        /uploads/../../../etc/passwd
Resolves to: /etc/passwd
```

### Prevention Pattern

```python
import os

def safe_file_access(base_dir, user_filename):
    # Resolve to absolute path
    requested = os.path.realpath(os.path.join(base_dir, user_filename))
    base = os.path.realpath(base_dir)

    # Verify path is within allowed directory
    if not requested.startswith(base + os.sep) and requested != base:
        raise ValueError("Path traversal detected")

    return requested
```

```javascript
const path = require('path');

function safeFilePath(baseDir, userFilename) {
  const requested = path.resolve(baseDir, userFilename);
  const base = path.resolve(baseDir);

  if (!requested.startsWith(base + path.sep) && requested !== base) {
    throw new Error('Path traversal detected');
  }

  return requested;
}
```

### Additional Checks

- Reject filenames containing `..` before path resolution (defense in depth)
- Reject null bytes (`%00`) which can truncate paths in some languages
- Validate file extensions against an allowlist
- Use chroot or container isolation to limit filesystem access

## XSS Prevention — In Depth

### Types of XSS

| Type | Trigger | Storage |
|------|---------|---------|
| Reflected | User clicks malicious link | None — payload in URL |
| Stored | User views page with saved payload | Database, file, etc. |
| DOM-based | Client-side JS processes untrusted data | None — client-side only |

### Framework Auto-Escaping

Most modern frameworks auto-escape by default:

| Framework | Auto-escapes | Danger Pattern |
|-----------|-------------|---------------|
| React | JSX expressions `{value}` | `dangerouslySetInnerHTML` |
| Angular | Template bindings `{{value}}` | `[innerHTML]`, `bypassSecurityTrust*` |
| Vue | Template syntax `{{value}}` | `v-html` directive |
| Jinja2 | With `autoescape=True` | `\|safe` filter, `Markup()` |
| Django | Default in templates | `\|safe` filter, `mark_safe()` |
| Go html/template | Default | `template.HTML()` type cast |

**Rule:** Never disable auto-escaping unless you have sanitized the content with a proven library.

### Content Security Policy (CSP)

CSP prevents XSS by controlling which scripts can execute:

```
Content-Security-Policy: default-src 'self';
  script-src 'self' 'nonce-{random}';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.example.com;
  frame-ancestors 'none';
```

**CSP deployment steps:**
1. Start with `Content-Security-Policy-Report-Only` to collect violations
2. Review violation reports and adjust policy
3. Switch to enforcing `Content-Security-Policy` once stable
4. Use nonces or hashes instead of `'unsafe-inline'` for scripts

## CSRF Prevention — In Depth

### Synchronizer Token Pattern

1. Server generates random token per session
2. Token embedded in forms as hidden field
3. Server validates token on every state-changing request
4. Token is NOT sent in cookies (that defeats the purpose)

### Double-Submit Cookie Pattern

1. Server sets a random value in a cookie
2. JavaScript reads the cookie and sends it as a header
3. Server verifies cookie value matches header value
4. Works because attacker cannot read cookies from another origin

### SameSite Cookie Attribute

```
Set-Cookie: session=abc123; SameSite=Lax; Secure; HttpOnly
```

| Value | Behavior |
|-------|----------|
| `Strict` | Cookie never sent cross-site (may break OAuth flows) |
| `Lax` | Cookie sent on top-level navigations (GET only) |
| `None` | Cookie always sent (requires `Secure` flag) |

**Recommendation:** Use `Lax` as default, `Strict` for sensitive operations.

## Secure Session Management

### Session Token Requirements

- Minimum 128 bits of entropy (cryptographic random)
- Transmitted only over HTTPS (`Secure` flag)
- Not accessible to JavaScript (`HttpOnly` flag)
- Scoped to specific domain and path
- Expiration set (both idle and absolute timeout)

### Session Lifecycle

```
Login → Generate new session ID
  → Set secure cookie flags
  → Store session server-side

Activity → Validate session on every request
  → Extend idle timeout on activity
  → Enforce absolute timeout regardless

Logout → Invalidate session server-side
  → Clear session cookie
  → Cannot be reused

Privilege change → Regenerate session ID
  → Invalidate old session
  → Prevents session fixation
```

### Cookie Security Flags

```
Set-Cookie: session=<token>;
  Secure;          // HTTPS only
  HttpOnly;        // No JavaScript access
  SameSite=Lax;    // CSRF protection
  Path=/;          // Scope to entire site
  Max-Age=3600;    // 1 hour expiration
  Domain=.example.com;  // Specific domain
```

## Error Handling Security

### What NOT to Expose

- Stack traces
- Database query details
- Internal file paths
- Framework version numbers
- Server hostnames or IPs
- Configuration details

### Safe Error Response Pattern

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided email address is not valid."
  }
}
```

Log the full error details server-side. Return only a safe, generic message to the client. Use error codes that the client can handle programmatically without leaking internals.

## Logging Security Events

### What to Log

- Authentication successes and failures
- Authorization failures
- Input validation failures
- Application errors and exceptions
- Privilege changes
- Data access patterns (sensitive data)
- Administrative actions

### What NOT to Log

- Passwords or credentials
- Session tokens
- Encryption keys
- Full credit card numbers
- Social security numbers
- Personal health information

### Log Format

Include enough context for investigation:

```
[timestamp] [severity] [event_type] [user_id] [ip] [resource] [result] [details]
```

Protect log integrity — logs should be append-only, stored separately from the application, and retained according to compliance requirements.

## File Upload Security

### Validation Checklist

- [ ] Validate file type by content (magic bytes), not just extension
- [ ] Enforce maximum file size server-side
- [ ] Rename uploaded files (never use user-provided filename directly)
- [ ] Store uploads outside the web root
- [ ] Scan for malware if feasible
- [ ] Strip EXIF data from images if not needed
- [ ] Serve uploaded files with `Content-Disposition: attachment` for downloads
- [ ] Set `X-Content-Type-Options: nosniff` header when serving files

### Dangerous File Types

Block or handle with extreme care:
- `.exe`, `.bat`, `.cmd`, `.sh`, `.ps1` — executables
- `.html`, `.htm`, `.svg` — can contain scripts
- `.php`, `.jsp`, `.asp`, `.py` — server-side execution
- `.xml`, `.xsl` — XXE attacks
- Archive files (`.zip`, `.tar.gz`) — zip bombs, path traversal

## API Security Checklist

- [ ] Authentication on all non-public endpoints
- [ ] Rate limiting per client/IP
- [ ] Input validation on all parameters
- [ ] Output encoding appropriate to response format
- [ ] CORS policy restricts allowed origins
- [ ] Request size limits enforced
- [ ] Sensitive data excluded from URL parameters (use request body)
- [ ] API versioning strategy documented
- [ ] Deprecation policy communicated
- [ ] Security headers set on all responses
