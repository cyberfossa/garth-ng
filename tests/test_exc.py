from unittest.mock import Mock

from garth.exc import (
    AuthenticationError,
    CloudflareError,
    GarthException,
    GarthHTTPError,
    MFARequiredError,
    NetworkError,
    RateLimitError,
)
from garth.sso.state import MFAState


class TestExceptionInheritance:
    def test_rate_limit_error_inherits(self):
        exc = RateLimitError(msg="Rate limit exceeded")
        assert isinstance(exc, GarthException)
        assert isinstance(exc, Exception)

    def test_cloudflare_error_inherits(self):
        exc = CloudflareError(msg="Cloudflare error")
        assert isinstance(exc, GarthException)
        assert isinstance(exc, Exception)

    def test_network_error_inherits(self):
        exc = NetworkError(msg="Network error")
        assert isinstance(exc, GarthException)
        assert isinstance(exc, Exception)

    def test_authentication_error_inherits(self):
        exc = AuthenticationError(msg="Authentication failed")
        assert isinstance(exc, GarthException)
        assert isinstance(exc, Exception)

    def test_mfa_required_error_inherits(self):
        exc = MFARequiredError(msg="MFA required")
        assert isinstance(exc, GarthException)
        assert isinstance(exc, Exception)


class TestMFARequiredError:
    def test_mfa_error_with_state(self):
        state = MFAState(
            strategy_name="EMAIL",
            domain="garmin.com",
            state={"code": "123456"},
        )
        exc = MFARequiredError(msg="MFA required", state=state)
        assert exc.state == state
        assert exc.state.strategy_name == "EMAIL"

    def test_mfa_error_without_state(self):
        exc = MFARequiredError(msg="MFA required")
        assert exc.state is None


class TestNetworkError:
    def test_network_error_without_request_error(self):
        exc = NetworkError(msg="Connection timeout")
        assert exc.error is None

    def test_network_error_with_none_error(self):
        exc = NetworkError(msg="Connection failed", error=None)
        assert exc.error is None


class TestGarthHTTPError:
    def test_garth_http_error_class_exists(self):
        # Create a mock RequestException to pass as error
        mock_error = Mock()
        mock_error.__str__ = Mock(return_value="Connection refused")

        # Instantiate GarthHTTPError with required args
        exc = GarthHTTPError(msg="HTTP request failed", error=mock_error)

        # Assert inheritance chain
        assert isinstance(exc, GarthHTTPError)
        assert isinstance(exc, GarthException)
        assert isinstance(exc, Exception)

        # Assert stored attributes match inputs
        assert exc.msg == "HTTP request failed"
        assert exc.error is mock_error

        # Assert str(exc) contains meaningful info
        str_repr = str(exc)
        assert "HTTP request failed" in str_repr
        assert "Connection refused" in str_repr
