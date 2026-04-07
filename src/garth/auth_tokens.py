import time

from pydantic.dataclasses import dataclass


@dataclass(repr=False)
class OAuth2Token:
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
