import time

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(repr=False, config=ConfigDict(extra="ignore"))
class OAuth2Token:
    """OAuth 2.0 token response from Garmin's SSO.

    A Pydantic dataclass representing the OAuth2 token obtained after
    successful SSO login. Includes access token, refresh token, and related
    metadata. The `extra="ignore"` config allows unknown fields from the API
    to be silently discarded.

    Expiry timestamps are auto-computed in `__post_init__`: if `expires_at`
    or `refresh_token_expires_at` are not provided, they are calculated as
    `now + expires_in` / `now + refresh_token_expires_in`.

    Attributes:
        access_token: JWT for API calls.
        refresh_token: Token used to obtain a new access token.
        expires_in: Seconds until access_token expires.
        token_type: Token type, typically "Bearer".
        expires_at: Unix timestamp when access_token expires
            (auto-computed).
        refresh_token_expires_in: Seconds until refresh_token expires.
        refresh_token_expires_at: Unix timestamp when refresh_token
            expires (auto-computed).
        scope: OAuth scope(s) granted.
        jti: JWT ID claim.
        mfa_token: MFA-related token (if MFA was used).
        mfa_expiration_timestamp: MFA token expiry (string format).
        mfa_expiration_timestamp_millis: MFA token expiry (milliseconds).
        client_id: OAuth client ID.
    """

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    expires_at: float | None = None
    refresh_token_expires_in: int | None = None
    refresh_token_expires_at: float | None = None
    scope: str | None = None
    jti: str | None = None
    mfa_token: str | None = None
    mfa_expiration_timestamp: str | None = None
    mfa_expiration_timestamp_millis: int | None = None
    client_id: str | None = None

    def __post_init__(self) -> None:
        """Compute expires_at and refresh_token_expires_at timestamps.

        If expires_at is not explicitly provided, it is calculated as the
        current Unix time plus expires_in. Similarly,
        refresh_token_expires_at is computed from refresh_token_expires_in
        if not provided.
        """
        now = time.time()
        if self.expires_at is None and self.expires_in is not None:
            self.expires_at = now + self.expires_in
        if (
            self.refresh_token_expires_at is None
            and self.refresh_token_expires_in is not None
        ):
            self.refresh_token_expires_at = now + self.refresh_token_expires_in

    @property
    def expired(self) -> bool:
        """Return True if the token has expired.

        When expires_at is None, the token is treated as non-expired
        (returns False). This handles tokens deserialized without an
        expiry field.
        """
        if self.expires_at is None:
            return False
        return self.expires_at < time.time()

    @property
    def refresh_expired(self) -> bool:
        """Return True if the refresh token has expired.

        When refresh_token_expires_at is None, the token is treated as
        non-expired (returns False). This handles tokens deserialized without
        a refresh expiry field.
        """
        if self.refresh_token_expires_at is None:
            return False
        return self.refresh_token_expires_at < time.time()

    def __repr__(self) -> str:
        return (
            f"OAuth2Token(scope={self.scope!r}, "
            f"jti={self.jti!r}, "
            f"token_type={self.token_type!r}, "
            f"access_token='***', "
            f"refresh_token='***', "
            f"mfa_token='***', "
            f"mfa_expiration_timestamp={self.mfa_expiration_timestamp!r}, "
            f"expires_in={self.expires_in!r}, "
            f"expires_at={self.expires_at!r}, "
            f"refresh_token_expires_in={self.refresh_token_expires_in!r}, "
            f"refresh_token_expires_at={self.refresh_token_expires_at!r})"
        )

    def __str__(self) -> str:
        return f"{self.token_type.title()} {self.access_token}"
