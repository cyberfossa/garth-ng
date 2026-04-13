import time

from garth.auth_tokens import OAuth2Token


def test_oauth2_token_construction():
    token = OAuth2Token(
        access_token="test_jwt",
        refresh_token="test_refresh",
        expires_in=97200,
    )

    assert token.access_token == "test_jwt"
    assert token.refresh_token == "test_refresh"
    assert "expires_in" not in token.__dict__
    assert token.expires_at is not None
    assert token.token_type == "Bearer"
    assert token.scope is None
    assert token.jti is None


def test_str(oauth2_token: OAuth2Token):
    assert str(oauth2_token) == "Bearer bar"


def test_repr_hides_tokens(oauth2_token: OAuth2Token):
    r = repr(oauth2_token)

    assert "access_token='***'" in r
    assert "refresh_token='***'" in r
    assert oauth2_token.access_token not in r
    assert oauth2_token.refresh_token not in r


def test_expired_when_expires_at_in_past():
    token = OAuth2Token(
        access_token="test_jwt",
        refresh_token="test_refresh",
        expires_in=3600,
        expires_at=time.time() - 1,
    )

    assert token.expired is True


def test_not_expired_when_expires_at_none():
    token = OAuth2Token(
        access_token="test_jwt",
        refresh_token="test_refresh",
        expires_in=3600,
        expires_at=None,
    )

    assert token.expired is False


def test_refresh_expired_when_in_past():
    token = OAuth2Token(
        access_token="test_jwt",
        refresh_token="test_refresh",
        expires_in=3600,
        refresh_token_expires_at=time.time() - 1,
    )

    assert token.refresh_expired is True


def test_refresh_not_expired_when_none():
    token = OAuth2Token(
        access_token="test_jwt",
        refresh_token="test_refresh",
        expires_in=3600,
        refresh_token_expires_at=None,
    )

    assert token.refresh_expired is False


def test_oauth2_token_preserves_jti_field(
    oauth2_token: OAuth2Token,
):
    assert oauth2_token.jti == "foo"


def test_oauth2_token_no_client_id_defaults_to_none():
    token = OAuth2Token(
        access_token="a",
        refresh_token="b",
        expires_in=3600,
        token_type="Bearer",
    )

    assert token.client_id is None
