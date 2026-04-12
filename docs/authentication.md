# Authentication

Garth uses OAuth2 via Garmin's SSO to authenticate, obtaining short-lived access
tokens backed by long-lived refresh tokens that auto-renew transparently. For a
quick start, see [Getting Started](getting-started.md#authentication).

## Token Lifecycle

After a successful login, Garth holds two tokens with different lifetimes:

```text
login() ──────────────────► OAuth2Token
                               ├── access_token  (~1 hour)
                               └── refresh_token (~90 days)
                                         │
                   (expired access_token)│
                                         ▼
                               auto-refresh via request()
                                         │
                   (expired refresh_token)│
                                         ▼
                               GarthException → re-login required
```

**What happens at each stage:**

- Every API call with `api=True` checks whether the access token has expired.
- If the access token is expired but the refresh token is still valid,
  `refresh_token()` is called transparently — your code never sees the
  interruption.
- If both tokens have expired, a `GarthException("No valid OAuth2 token.
  Please login.")` is raised and you must re-authenticate.

!!! tip "Auto-persist on refresh"
    When `GARTH_HOME` is set (either as an environment variable or via a previous
    `save()` call), the refreshed token is automatically written back to disk.
    Your session stays current without any extra code.

## Token Persistence

### Directory-based storage

The simplest approach: save the token directory after login, then resume it in
any subsequent script.

```python
garth.login(input("Email: "), getpass("Password: "))
garth.save("~/.garth")
```

```python
# In another script or process
garth.resume("~/.garth")
profile = garth.client.username
```

Internally, `save()` writes `~/.garth/oauth2_token.json` as human-readable JSON
(4-space indented). `resume()` reads it back and validates the token structure.

!!! note "Legacy OAuth1 tokens"
    If a directory contains `oauth1_token.json` from an older garth version,
    `resume()` raises a `GarthException` with instructions to re-authenticate.
    The OAuth1 format is no longer supported.

### Environment variables

**`GARTH_HOME`** — ideal for containers and scripts that run repeatedly. Set it
once and every subsequent `import garth` loads the session automatically.

```bash
export GARTH_HOME=~/.garth
```

```python
# Session loaded from disk automatically on import
data = garth.connectapi("/wellness-service/wellness/dailySummary")
```

**`GARTH_TOKEN`** — a base64-encoded token string, better suited for CI/CD
pipelines and secrets managers where you can't mount a directory.

Generate a token once with the CLI:

```bash
uvx garth login
# Copy the printed GARTH_TOKEN value
export GARTH_TOKEN="eyJvYXV0..."
```

```python
# Session decoded from GARTH_TOKEN automatically
data = garth.connectapi("/wellness-service/wellness/dailySummary")
```

!!! warning "Mutual exclusivity"
    `GARTH_HOME` and `GARTH_TOKEN` cannot both be set. Garth raises a
    `GarthException` at startup if both environment variables are present.

### Programmatic serialization

For secrets managers, databases, or any storage backend that isn't a filesystem,
use `dumps()` and `loads()` directly:

```python
# After login, serialize for storage:
token_str = garth.client.dumps()
# Store token_str in your secrets manager, Redis, a DB column, etc.

# Later, in another process, restore it:
garth.client.loads(token_str)
data = garth.connectapi("/wellness-service/wellness/dailySummary")
```

The format is `base64(JSON([{access_token, refresh_token, expires_at,
refresh_token_expires_at, ...}]))` — a base64-encoded JSON array containing
one object with all token fields.

## Multi-User Access

For applications that manage tokens for multiple Garmin users (e.g. a backend
with Firebase, Redis, or a relational database), create a separate `Client`
instance per user instead of using the global `garth.client` singleton.

### Per-user client instances

Every `Client` is fully self-contained — it holds its own OAuth2 token, HTTP
session, and configuration:

```python
from garth import Client

# Load a user's token from your database
token_b64 = db.get(f"users/{user_id}/garth_token")

client = Client()
client.loads(token_b64)

# Use any API — stats, data models, direct calls
steps = client.connectapi(
    "/usersummary-service/stats/steps/daily/2025-04-01/2025-04-07"
)
```

### Data and stats models with custom client

All data and stats models accept an optional `client` parameter. When omitted,
they fall back to the global singleton. Pass your instance to use a specific
user's session:

```python
from garth import Client, WeightData, DailySteps, SleepData

client = Client()
client.loads(token_from_db)

WeightData.list(days=7, client=client)
DailySteps.list(period=7, client=client)
SleepData.list(days=3, client=client)
```

### Persisting refreshed tokens

Unlike `GARTH_HOME` (which auto-persists to disk), database-backed tokens
require manual persistence after each API call — the token may have been
silently refreshed:

```python
def fetch_for_user(user_id: str, path: str):
    client = Client()
    client.loads(db.get(f"users/{user_id}/garth_token"))
    result = client.connectapi(path)
    # Token may have been refreshed — always persist back
    db.set(f"users/{user_id}/garth_token", client.dumps())
    return result
```

!!! warning "Thread safety"
    Each `Client` has its own HTTP session, so parallel requests across
    different instances are safe. However, a single `Client` instance is
    **not** thread-safe — if two threads call the API with the same instance
    simultaneously, both may attempt a token refresh. Use a lock per user or
    create short-lived instances per request.

## MFA Handling

### Interactive login

When MFA is required and no handler is provided, `MFARequiredError` is raised.
Pass a `prompt_mfa` callable to handle it in one step:

```python
garth.login(email, password, prompt_mfa=lambda: input("MFA code: "))
```

The callable takes no arguments and must return the code as a string.

### Programmatic two-step flow

For web apps or any async context where you can't block waiting for user input:

```python
from garth.sso.state import MFAState

login_result = garth.client.login(email, password, return_on_mfa=True)
if isinstance(login_result, MFAState):
    # Suspend here, deliver MFA prompt through your app's own mechanism
    mfa_code = get_code_from_your_app()
    garth.client.resume_login(login_result, mfa_code)
```

### Catching MFARequiredError

If you can't use `prompt_mfa` or `return_on_mfa`, catch the exception directly:

```python
from garth.exc import MFARequiredError

try:
    garth.login(email, password)
except MFARequiredError as e:
    mfa_code = input("MFA code: ")
    garth.client.resume_login(e.state, mfa_code)
```

!!! note "MFAState carries the session"
    The `state` object inside `MFARequiredError` holds the partial SSO session.
    It must be passed to `resume_login()` — you cannot start fresh with a new
    `login()` call to complete the same MFA challenge.

## Error Handling

### Exception hierarchy

| Exception | Raised When | Retryable | Recovery |
|---|---|---|---|
| `GarthException` | Base — general errors | — | — |
| `GarthHTTPError` | Non-success HTTP status | Depends on status | Check `error` field |
| `RateLimitError` | Garmin rate limit hit | Yes | Wait and retry |
| `CloudflareError` | Cloudflare blocks request | Yes | Wait and retry |
| `NetworkError` | DNS / timeout / network reset | Yes | Check connection |
| `AuthenticationError` | Invalid credentials | No | Re-enter credentials |
| `MFARequiredError` | MFA needed, no handler | No | Provide MFA code |

All exceptions inherit from `GarthException`. `GarthHTTPError` and `NetworkError`
carry an `error` field with the underlying `RequestException` from `curl_cffi`.

### Expired session recovery

When the refresh token expires, the next `connectapi()` call raises
`GarthException`. The standard pattern is to catch it and re-authenticate:

```python
from garth.exc import GarthException

try:
    data = garth.connectapi("/wellness-service/wellness/dailySummary")
except GarthException:
    garth.login(email, password)
    data = garth.connectapi("/wellness-service/wellness/dailySummary")
```

!!! warning "Rate limit and network errors"
    `RateLimitError`, `CloudflareError`, and `NetworkError` are retryable.
    Garth's built-in retry logic handles `5xx` and `408` status codes
    automatically. For rate limits (`429`), add it to `status_forcelist`
    explicitly — see [Configuration](configuration.md#request-settings).
