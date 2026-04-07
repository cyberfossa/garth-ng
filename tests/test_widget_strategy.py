import copy
from typing import TYPE_CHECKING, cast
from unittest.mock import patch

import pytest

from garth.exc import CloudflareError, MFARequiredError
from garth.sso.strategy import LoginResult
from garth.sso.widget_strategy import WidgetStrategy


if TYPE_CHECKING:
    from curl_cffi.requests import Session


class FakeResponse:
    text: str
    url: str
    headers: object

    def __init__(
        self,
        text: str,
        *,
        url: str = "https://sso.garmin.com/sso/embed",
        headers: object | None = None,
    ) -> None:
        self.text = text
        self.url = url
        self.headers = headers if headers is not None else {}


class FakeSession:
    _get_responses: list[FakeResponse]
    _post_responses: list[FakeResponse]
    get_calls: list[tuple[str, dict[str, str]]]
    post_calls: list[tuple[str, dict[str, object]]]

    def __init__(
        self,
        get_responses: list[FakeResponse],
        post_responses: list[FakeResponse],
    ) -> None:
        self._get_responses = list(get_responses)
        self._post_responses = list(post_responses)
        self.get_calls = []
        self.post_calls = []

    def get(
        self,
        url: str,
        params: dict[str, str],
        **kwargs: object,
    ) -> FakeResponse:
        del kwargs
        self.get_calls.append((url, params))
        return self._get_responses.pop(0)

    def post(self, url: str, **kwargs: object) -> FakeResponse:
        self.post_calls.append((url, dict(kwargs)))
        return self._post_responses.pop(0)


class FakeHeaders:
    def __init__(self, data: dict[str, str]) -> None:
        self._data = data

    def get(self, key: str) -> str | None:
        return self._data.get(key)


class FakeJsonResponse(FakeResponse):
    def __init__(
        self,
        payload: object,
        *,
        text: str = "",
        url: str = "https://sso.garmin.com/sso/embed",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(text=text, url=url, headers=headers)
        self._payload = payload

    def json(self) -> object:
        return self._payload


_MFA_STATE: dict[str, object] = {
    "mfa_url": ("https://sso.garmin.com/sso/verifyMFA/loginEnterMfaCode"),
    "service_url": "https://sso.garmin.com/sso/embed",
    "signin_params": {
        "id": "gauth-widget",
        "embedWidget": "true",
        "gauthHost": "https://sso.garmin.com/sso/embed",
        "service": "https://sso.garmin.com/sso/embed",
        "source": "https://sso.garmin.com/sso/embed",
        "redirectAfterAccountLoginUrl": ("https://sso.garmin.com/sso/embed"),
        "redirectAfterAccountCreationUrl": (
            "https://sso.garmin.com/sso/embed"
        ),
    },
    "csrf_token": "mfa-csrf-test",
    "referer": ("https://sso.garmin.com/sso/verifyMFA/loginEnterMfaCode"),
}


def test_widget_login_success():
    strategy = WidgetStrategy()
    session = FakeSession(
        get_responses=[
            FakeResponse("<html>embed</html>"),
            FakeResponse(
                '<input type="hidden" name="_csrf" value="csrf-123" />'
            ),
        ],
        post_responses=[
            FakeResponse('<a href="/sso/embed?ticket=ST-WIDGET-123">ok</a>')
        ],
    )

    with patch(
        "garth.sso.widget_strategy.random.uniform",
        return_value=2.5,
    ):
        with patch("garth.sso.widget_strategy.time.sleep"):
            result = strategy.login(
                session=cast("Session", cast(object, session)),
                email="john@example.com",
                password="secret",
                domain="garmin.com",
            )

    assert result == LoginResult(
        ticket="ST-WIDGET-123",
        service_url="https://sso.garmin.com/sso/embed",
    )
    post_url, post_kwargs = session.post_calls[0]
    assert post_url == "https://sso.garmin.com/sso/signin"
    assert "json" not in post_kwargs
    post_data = cast(dict[str, str], post_kwargs["data"])
    assert post_data["_csrf"] == "csrf-123"


@pytest.mark.parametrize(
    ("csrf_html", "expected"),
    [
        ('<input name="_csrf" value="aaa">', "aaa"),
        (
            '<input name="_csrf" type="hidden" value="bbb">',
            "bbb",
        ),
        ('<input value="ccc" name="_csrf">', "ccc"),
    ],
)
def test_csrf_extraction(csrf_html: str, expected: str):
    strategy = WidgetStrategy()
    session = FakeSession(
        get_responses=[
            FakeResponse("<html>embed</html>"),
            FakeResponse(csrf_html),
        ],
        post_responses=[
            FakeResponse('<a href="/sso/embed?ticket=ST-CSRF-1">')
        ],
    )

    with patch(
        "garth.sso.widget_strategy.random.uniform",
        return_value=1.7,
    ):
        with patch("garth.sso.widget_strategy.time.sleep"):
            _ = strategy.login(
                session=cast("Session", cast(object, session)),
                email="john@example.com",
                password="secret",
                domain="garmin.com",
            )

    _post_url, post_kwargs = session.post_calls[0]
    post_data = cast(dict[str, str], post_kwargs["data"])
    assert post_data["_csrf"] == expected


def test_ticket_extraction():
    strategy = WidgetStrategy()
    session = FakeSession(
        get_responses=[
            FakeResponse("<html>embed</html>"),
            FakeResponse('<input name="_csrf" value="csrf-ticket">'),
        ],
        post_responses=[
            FakeResponse(
                '<script>location="/sso/embed?ticket=ST-TEST-42";</script>'
            )
        ],
    )

    with patch(
        "garth.sso.widget_strategy.random.uniform",
        return_value=1.8,
    ):
        with patch("garth.sso.widget_strategy.time.sleep"):
            result = strategy.login(
                session=cast("Session", cast(object, session)),
                email="john@example.com",
                password="secret",
                domain="garmin.com",
            )

    assert result == LoginResult(
        ticket="ST-TEST-42",
        service_url="https://sso.garmin.com/sso/embed",
    )


def test_cloudflare_detection():
    strategy = WidgetStrategy()
    session = FakeSession(
        get_responses=[
            FakeResponse("<html>embed</html>"),
            FakeResponse("<html>Just a moment...</html>"),
        ],
        post_responses=[],
    )

    with pytest.raises(CloudflareError):
        _ = strategy.login(
            session=cast("Session", cast(object, session)),
            email="john@example.com",
            password="secret",
            domain="garmin.com",
        )


def test_mfa_required():
    strategy = WidgetStrategy()
    session = FakeSession(
        get_responses=[
            FakeResponse("<html>embed</html>"),
            FakeResponse('<input name="_csrf" value="csrf-456">'),
        ],
        post_responses=[
            FakeResponse(
                "<html>verifyMFA loginEnterMfaCode"
                ' <input name="_csrf"'
                ' value="mfa-csrf-789">'
                "</html>"
            )
        ],
    )

    with patch(
        "garth.sso.widget_strategy.random.uniform",
        return_value=2.0,
    ):
        with patch("garth.sso.widget_strategy.time.sleep"):
            with pytest.raises(MFARequiredError) as exc_info:
                _ = strategy.login(
                    session=cast(
                        "Session",
                        cast(object, session),
                    ),
                    email="john@example.com",
                    password="secret",
                    domain="garmin.com",
                )

    state = exc_info.value.state
    assert state is not None
    assert state.strategy_name == "widget"
    assert state.domain == "garmin.com"
    assert state.state["mfa_url"] == (
        "https://sso.garmin.com/sso/verifyMFA/loginEnterMfaCode"
    )
    assert state.state["csrf_token"] == "mfa-csrf-789"
    assert "signin_params" in state.state
    assert "referer" in state.state
    assert state.state["service_url"] == "https://sso.garmin.com/sso/embed"


def test_handle_mfa_success():
    strategy = WidgetStrategy()
    session = FakeSession(
        get_responses=[],
        post_responses=[
            FakeResponse('<a href="/sso/embed?ticket=ST-MFA-OK">ok</a>')
        ],
    )

    result = strategy.handle_mfa(
        cast("Session", cast(object, session)),
        "garmin.com",
        copy.deepcopy(_MFA_STATE),
        "123456",
    )

    assert result == LoginResult(
        ticket="ST-MFA-OK",
        service_url="https://sso.garmin.com/sso/embed",
    )
    _post_url, post_kwargs = session.post_calls[0]
    assert "json" not in post_kwargs
    post_data = cast(dict[str, str], post_kwargs["data"])
    assert post_data["mfa-code"] == "123456"
    assert post_data["embed"] == "true"
    assert post_data["_csrf"] == "mfa-csrf-test"
    assert post_data["fromPage"] == "setupEnterMfaCode"
    assert post_kwargs["params"] == _MFA_STATE["signin_params"]


@pytest.mark.parametrize(
    ("response", "expected_ticket"),
    [
        (
            FakeResponse(
                '{"responseStatus":'
                '{"type":"SUCCESSFUL"},'
                '"serviceTicketId":"ST-MFA-JSON"}'
            ),
            "ST-MFA-JSON",
        ),
        (
            FakeResponse(
                "",
                url=("https://sso.garmin.com/sso/embed?ticket=ST-MFA-URL"),
            ),
            "ST-MFA-URL",
        ),
        (
            FakeResponse(
                "",
                headers={
                    "Location": (
                        "https://sso.garmin.com"
                        "/sso/embed"
                        "?ticket=ST-MFA-LOCATION"
                    )
                },
            ),
            "ST-MFA-LOCATION",
        ),
    ],
)
def test_handle_mfa_ticket_variants(
    response: FakeResponse, expected_ticket: str
):
    strategy = WidgetStrategy()
    session = FakeSession(get_responses=[], post_responses=[response])

    result = strategy.handle_mfa(
        cast("Session", cast(object, session)),
        "garmin.com",
        copy.deepcopy(_MFA_STATE),
        "123456",
    )

    assert result == LoginResult(
        ticket=expected_ticket,
        service_url="https://sso.garmin.com/sso/embed",
    )


def test_handle_mfa_ticket_from_json_payload():
    strategy = WidgetStrategy()
    session = FakeSession(
        get_responses=[],
        post_responses=[
            FakeJsonResponse(
                {
                    "responseStatus": {"type": "SUCCESSFUL"},
                    "meta": {
                        "serviceTicketId": ("ST-MFA-NESTED-JSON"),
                    },
                }
            )
        ],
    )

    result = strategy.handle_mfa(
        cast("Session", cast(object, session)),
        "garmin.com",
        copy.deepcopy(_MFA_STATE),
        "123456",
    )

    assert result == LoginResult(
        ticket="ST-MFA-NESTED-JSON",
        service_url="https://sso.garmin.com/sso/embed",
    )


def test_handle_mfa_ticket_from_headers_object():
    strategy = WidgetStrategy()
    response = FakeResponse("")
    response.headers = FakeHeaders(
        {
            "Location": (
                "https://sso.garmin.com/sso/embed?ticket=ST-MFA-HEADERS-OBJECT"
            )
        }
    )
    session = FakeSession(get_responses=[], post_responses=[response])

    result = strategy.handle_mfa(
        cast("Session", cast(object, session)),
        "garmin.com",
        copy.deepcopy(_MFA_STATE),
        "123456",
    )

    assert result == LoginResult(
        ticket="ST-MFA-HEADERS-OBJECT",
        service_url="https://sso.garmin.com/sso/embed",
    )


def test_no_client_id():
    strategy = WidgetStrategy()
    session = FakeSession(
        get_responses=[
            FakeResponse("<html>embed</html>"),
            FakeResponse('<input name="_csrf" value="csrf-no-client">'),
        ],
        post_responses=[
            FakeResponse('<a href="/sso/embed?ticket=ST-NO-CLIENT">ok</a>')
        ],
    )

    with patch(
        "garth.sso.widget_strategy.random.uniform",
        return_value=2.2,
    ):
        with patch("garth.sso.widget_strategy.time.sleep"):
            _ = strategy.login(
                session=cast("Session", cast(object, session)),
                email="john@example.com",
                password="secret",
                domain="garmin.com",
            )

    for url, params in session.get_calls:
        assert "clientId" not in url
        assert "clientId" not in params

    post_url, post_kwargs = session.post_calls[0]
    assert "clientId" not in post_url
    assert "clientId" not in post_kwargs
    post_params = cast(dict[str, str], post_kwargs.get("params", {}))
    assert "clientId" not in post_params
    post_data = cast(dict[str, str], post_kwargs["data"])
    assert "clientId" not in post_data


def test_random_delay():
    strategy = WidgetStrategy()
    session = FakeSession(
        get_responses=[
            FakeResponse("<html>embed</html>"),
            FakeResponse('<input name="_csrf" value="csrf-delay">'),
        ],
        post_responses=[
            FakeResponse('<a href="/sso/embed?ticket=ST-DELAY-1">ok</a>')
        ],
    )

    with patch(
        "garth.sso.widget_strategy.random.uniform",
        return_value=3.33,
    ) as random_uniform:
        with patch("garth.sso.widget_strategy.time.sleep") as sleep:
            _ = strategy.login(
                session=cast("Session", cast(object, session)),
                email="john@example.com",
                password="secret",
                domain="garmin.com",
            )

    random_uniform.assert_called_once_with(1.5, 4.0)
    sleep.assert_called_once_with(3.33)
