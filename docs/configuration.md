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

### Custom token callback

Register a callback that fires automatically after login and every token
refresh. Use this instead of `GARTH_HOME` when you need custom storage
(database, secrets manager, etc.):

```python
def persist_token(token: OAuth2Token) -> None:
    redis.set("garth:token", token.to_dict())

garth.configure(on_token_update=persist_token)
```

The callback receives the fresh `OAuth2Token` after each successful login or
refresh. It **replaces** the automatic file dump — when a callback is set,
`GARTH_HOME` is ignored for auto-persistence.

To revert to the default persistence behavior:

```python
garth.configure(
    on_token_update=garth.client.dump_to_home
)
```

!!! warning "Exception handling"
    If your callback raises an exception, it propagates up through the login or
    refresh call. Handle errors inside your callback to avoid interrupting the
    authentication flow.
