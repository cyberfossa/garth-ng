# Migrating to v1.0.0

This guide covers all breaking changes introduced in v1.0.0 and how to update
your code.

## Overview

v1.0.0 replaces the entire auth stack: `requests` + OAuth1 is gone, replaced
by `curl_cffi` + direct DI-OAuth2. The SSO module is now strategy-based,
and the public API is fully typed with explicit parameters instead of
`*args, **kwargs`.

**What stayed the same:**

- `import garth` — the package name is unchanged
- `garth.connectapi()`, `garth.save()`, `garth.resume()` — same function names
- All stats and data types (`DailySteps`, `SleepData`, etc.)
- `GARTH_HOME` and `GARTH_TOKEN` environment variables
- Domain configuration (`garmin.com`, `garmin.cn`)

## Install

```bash
pip uninstall garth        # remove old version
pip install "garth-ng>=1.0.0a1"  # install new version
```

Or with uv:

```bash
uv add "garth-ng>=1.0.0a1"
```

## Saved tokens are not compatible

v1.0.0 uses a new token format. Old tokens (both on disk and base64-encoded)
will not load — you must re-authenticate.

```bash
# Delete old saved tokens
rm -rf ~/.garth/

# Unset old base64 token if used
unset GARTH_TOKEN
```

Then log in again:

```python
garth.login(email, password, prompt_mfa=input)
garth.save("~/.garth")
```

!!! warning "No automatic migration"
    There is no upgrade path for existing tokens. The old OAuth1-based flow
    no longer works with Garmin's servers, so the tokens cannot be converted.

## Breaking changes

### `login()` signature and return type

The most impactful change. `login()` now has explicit typed parameters and
returns a single token instead of a tuple.

```python
# OLD
oauth1, oauth2 = garth.login(email, password)

# NEW
token = garth.login(email, password)
# token is OAuth2Token
```

The `prompt_mfa` parameter keeps the same `Callable[[], str]` signature —
a no-argument callable that returns the MFA code:

```python
# OLD — still works, no change needed
garth.login(email, password, prompt_mfa=lambda: input("MFA code: "))
```

### MFA handling

The two-step MFA flow uses a `MFAState` dataclass instead of a raw dict:

```python
# OLD
result1, result2 = garth.login(email, password, return_on_mfa=True)
if result1 == "needs_mfa":
    garth.client.resume_login(result2, mfa_code)

# NEW
result = garth.client.login(email, password, return_on_mfa=True)
if isinstance(result, MFAState):
    garth.client.resume_login(result, mfa_code)
```

`MFAState` is importable from `garth.sso.state` if you need the type for
annotations.

### `OAuth1Token` removed

The `OAuth1Token` class no longer exists. All references must be removed:

```python
# OLD
from garth.auth_tokens import OAuth1Token, OAuth2Token
garth.client.oauth1_token

# NEW
from garth.auth_tokens import OAuth2Token
# oauth1_token attribute no longer exists on Client
```

### `OAuth2Token` field changes

Several fields changed from required to optional. Code that accesses `scope`
or `jti` without a `None` check may break:

| Field | Old type | New type |
|---|---|---|
| `scope` | `str` (required) | `str \| None` (default `None`) |
| `jti` | `str` (required) | `str \| None` (default `None`) |
| `token_type` | `str` (required) | `str` (default `"Bearer"`) |
| `expires_at` | `int` | `float \| None` |
| `refresh_token_expires_in` | `int` | `int \| None` |
| `refresh_token_expires_at` | `int` | `float \| None` |

New fields added: `mfa_token`, `mfa_expiration_timestamp`,
`mfa_expiration_timestamp_millis` (all optional).

!!! warning "Positional construction"
    The field order changed. If you construct `OAuth2Token` with positional
    arguments, switch to keyword arguments.

### `Client.sess` renamed to `Client.session`

```python
# OLD
garth.client.sess

# NEW
garth.client.session
```

The session object is now a `curl_cffi.requests.Session` instead of
`requests.Session`.

### `refresh_oauth2()` renamed to `refresh_token()`

```python
# OLD
garth.client.refresh_oauth2()

# NEW
garth.client.refresh_token()
```

### `configure()` — removed parameters

Three parameters were removed:

| Removed parameter | Reason |
|---|---|
| `oauth1_token` | OAuth1 flow removed |
| `pool_connections` | Handled internally by curl_cffi |
| `pool_maxsize` | Handled internally by curl_cffi |

```python
# OLD
garth.configure(oauth1_token=token, pool_connections=20, pool_maxsize=20)

# NEW — these parameters no longer exist
garth.configure()
```

### `dump()` — `oauth2_only` parameter removed

```python
# OLD
garth.client.dump(path, oauth2_only=True)

# NEW — always writes only OAuth2 (the only token type now)
garth.client.dump(path)
```

### Exception types

`GarthHTTPError.error` is now a `curl_cffi.requests.exceptions.RequestException`
instead of `requests.HTTPError`:

```python
# OLD
from requests import HTTPError
try:
    garth.connectapi("/some/endpoint")
except GarthHTTPError as e:
    original: HTTPError = e.error

# NEW
from curl_cffi.requests.exceptions import RequestException
try:
    garth.connectapi("/some/endpoint")
except GarthHTTPError as e:
    original: RequestException = e.error
```

New exception types added to the hierarchy:

```text
GarthException
├── GarthHTTPError
├── RateLimitError
├── CloudflareError
├── NetworkError
├── AuthenticationError
└── MFARequiredError
```

All are importable from `garth.exc`.

### `sso` module restructured

`garth.sso` changed from a single module to a package with a strategy pattern.
The internal API is completely different:

```python
# OLD
from garth.sso import login, exchange, get_oauth1_token

# NEW — internal API changed, use garth.login() instead
from garth.sso import login  # different signature: login(session, email, password, domain)
```

Unless you were calling `garth.sso` functions directly (not common), this
does not affect you. Use the top-level `garth.login()` and
`garth.client.resume_login()` instead.

### HTTP library change

The underlying HTTP library changed from `requests` to `curl_cffi`. This
affects code that:

- Passes `requests.Session` instances to `Client(session=...)`
- Inspects `Response` objects beyond `.json()`, `.status_code`, `.content`
- Catches `requests`-specific exceptions

```python
# OLD
from requests import Session
client = garth.Client(session=Session())

# NEW
from curl_cffi.requests import Session
client = garth.Client(session=Session(impersonate="chrome120"))
```

## Migration checklist

1. Update the package: `pip install "garth-ng>=1.0.0a1"`
2. Delete saved tokens and re-authenticate
3. Fix `login()` return value — single token, not a tuple
4. Verify `prompt_mfa` usage — signature unchanged (`Callable[[], str]`)
5. Remove all `OAuth1Token` references
6. Rename `client.sess` → `client.session`
7. Rename `refresh_oauth2()` → `refresh_token()`
8. Remove `pool_connections` / `pool_maxsize` from `configure()`
9. Remove `oauth2_only` from `dump()` calls
10. Update exception handling if catching `requests.HTTPError` directly
11. Check `OAuth2Token.scope` and `.jti` for `None` before use
