# Configuration

All configuration is done through `garth.configure()`. Options can be combined
in a single call.

## Domain Settings

### China region

For users in China, configure the domain to use `garmin.cn`:

```python
garth.configure(domain="garmin.cn")
```

## Proxy Settings

### Proxy through Charles

For debugging or monitoring HTTP traffic:

```python
garth.configure(proxies={"https": "http://localhost:8888"}, ssl_verify=False)
```

!!! warning "SSL verification"
    Disabling SSL verification (`ssl_verify=False`) should only be used for
    debugging purposes. Do not use in production.

### Custom proxy

```python
garth.configure(proxies={
    "http": "http://proxy.example.com:8080",
    "https": "http://proxy.example.com:8080"
})
```

## Request Settings

### Timeout

Set the request timeout in seconds (default: 10):

```python
garth.configure(timeout=30)
```

### Retries

Configure automatic retry behavior for failed requests:

```python
garth.configure(
    retries=5,                            # Max retry attempts (default: 3)
    status_forcelist=(408, 500, 502, 503, 504),  # HTTP codes to retry
    backoff_factor=1.0,                   # Delay multiplier between retries
)
```

!!! note "429 not retried by default"
    HTTP 429 (Too Many Requests) is not in the default retry list because
    retrying can make rate limiting worse. Add it explicitly if needed:
    `status_forcelist=(408, 429, 500, 502, 503, 504)`

## Token Persistence

### Custom token storage

Implement the `TokenStorage` protocol to persist tokens in any backend
(database, secrets manager, etc.) instead of the filesystem:

```python
from garth import TokenStorage
from garth.auth_tokens import OAuth2Token

class RedisTokenStorage:
    def save(self, token: OAuth2Token) -> None:
        redis.set("garth:token", token.model_dump_json())

    def load(self) -> OAuth2Token | None:
        data = redis.get("garth:token")
        return OAuth2Token.model_validate_json(data) if data else None

garth.configure(storage=RedisTokenStorage())
```

The storage's `save()` is called automatically after each successful login or
token refresh. `load()` is called once when `configure(storage=...)` is first
set, so the client resumes any previously saved session immediately.

To use file-based persistence with a custom path:

```python
from garth import FileTokenStorage

garth.configure(storage=FileTokenStorage("~/.garth"))
```

To disable persistence (tokens in memory only):

```python
garth.configure(storage=None)
```
