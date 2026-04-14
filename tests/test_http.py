import json
import os
import tempfile
import time
from typing import Any, cast

import pytest
from curl_cffi.requests.exceptions import RequestException

import garth.http as http_mod
from garth.auth_tokens import OAuth2Token
from garth.exc import GarthException, GarthHTTPError, MFARequiredError
from garth.http import Client
from garth.sso.state import MFAState
from garth.sso.strategy import LoginResult
from tests.helpers import (
    _is_data_interaction,
    load_cassette as _load_cassette,
    make_mock_response,
    parse_response_body,
)


def test_dump_and_load(oauth2_token: OAuth2Token):
    with tempfile.TemporaryDirectory() as tempdir:
        client = Client()
        client.oauth2_token = oauth2_token
        client.dump(tempdir)

        new_client = Client()
        new_client.load(tempdir)

        assert new_client.oauth2_token == oauth2_token


def test_dump_load_preserves_client_id():
    with tempfile.TemporaryDirectory() as tempdir:
        client = Client()
        client.oauth2_token = OAuth2Token(
            access_token="token-a",
            refresh_token="token-b",
            expires_in=3600,
            client_id="GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2",
        )
        client.dump(tempdir)

        loaded_client = Client()
        loaded_client.load(tempdir)

        assert loaded_client.oauth2_token is not None
        assert (
            loaded_client.oauth2_token.client_id
            == "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2"
        )


def test_legacy_oauth1_detection():
    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, "oauth1_token.json"), "w") as f:
            json.dump({"oauth_token": "x", "oauth_token_secret": "y"}, f)

        new_client = Client()
        with pytest.raises(
            GarthException,
            match="Legacy OAuth1 tokens found",
        ):
            new_client.load(tempdir)


def test_load_missing_tokens_raises():
    with tempfile.TemporaryDirectory() as tempdir:
        new_client = Client()
        with pytest.raises(
            GarthException,
            match="No token files found",
        ):
            new_client.load(tempdir)


def test_dumps_and_loads(oauth2_token: OAuth2Token):
    client = Client()
    client.oauth2_token = oauth2_token

    s = client.dumps()
    new_client = Client()
    new_client.loads(s)

    assert new_client.oauth2_token == oauth2_token


def test_auto_resume_garth_home(
    oauth2_token: OAuth2Token, monkeypatch: pytest.MonkeyPatch
):
    with tempfile.TemporaryDirectory() as tempdir:
        client = Client()
        client.oauth2_token = oauth2_token
        client.dump(tempdir)

        monkeypatch.setenv("GARTH_HOME", tempdir)
        monkeypatch.delenv("GARTH_TOKEN", raising=False)

        resumed_client = Client()
        assert resumed_client.oauth2_token == oauth2_token


def test_auto_resume_garth_token(
    oauth2_token: OAuth2Token, monkeypatch: pytest.MonkeyPatch
):
    client = Client()
    client.oauth2_token = oauth2_token
    token = client.dumps()

    monkeypatch.setenv("GARTH_TOKEN", token)
    monkeypatch.delenv("GARTH_HOME", raising=False)

    resumed_client = Client()
    assert resumed_client.oauth2_token == oauth2_token


def test_auto_resume_garth_home_missing_tokens(
    monkeypatch: pytest.MonkeyPatch,
):
    with tempfile.TemporaryDirectory() as tempdir:
        monkeypatch.setenv("GARTH_HOME", tempdir)
        monkeypatch.delenv("GARTH_TOKEN", raising=False)

        client = Client()
        assert client._garth_home == tempdir
        assert client.oauth2_token is None


@pytest.fixture
def garth_home_client(monkeypatch: pytest.MonkeyPatch):
    with tempfile.TemporaryDirectory() as tempdir:
        monkeypatch.setenv("GARTH_HOME", tempdir)
        monkeypatch.delenv("GARTH_TOKEN", raising=False)

        client = Client()
        mock_oauth2_token = OAuth2Token(
            access_token="test_access_token_jwt",
            refresh_token="test_refresh_token",
            expires_in=3600,
            expires_at=time.time() + 3600,
            refresh_token_expires_in=7200,
            refresh_token_expires_at=time.time() + 7200,
        )
        yield client, tempdir, mock_oauth2_token


def _assert_oauth2_token_saved(tempdir: str, oauth2_token: OAuth2Token):
    loaded = Client()
    loaded.load(tempdir)
    assert loaded.oauth2_token == oauth2_token


def test_auto_save_on_login(garth_home_client, monkeypatch):
    client, tempdir, mock_oauth2_token = garth_home_client
    monkeypatch.setattr(
        http_mod.sso,
        "login",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: mock_oauth2_token,
    )

    client.login("user@example.com", "password")
    _assert_oauth2_token_saved(tempdir, mock_oauth2_token)


def test_auto_save_on_resume_login(garth_home_client, monkeypatch):
    client, tempdir, mock_oauth2_token = garth_home_client
    mfa_state = MFAState(
        strategy_name="json-portal",
        domain="garmin.com",
        state={"mfa_url": "https://sso.garmin.com/portal/api/mfa/verifyCode"},
    )
    monkeypatch.setattr(
        http_mod.sso,
        "handle_mfa",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: mock_oauth2_token,
    )

    client.resume_login(mfa_state, "123456")
    _assert_oauth2_token_saved(tempdir, mock_oauth2_token)


def test_auto_resume_both_set_raises(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("GARTH_HOME", "/some/path")
    monkeypatch.setenv("GARTH_TOKEN", "some_token")

    with pytest.raises(GarthException, match="cannot both be set"):
        Client()


def test_configure_domain(client: Client):
    assert client.domain == "garmin.com"
    client.configure(domain="garmin.cn")
    assert client.domain == "garmin.cn"


def test_configure_proxies(client: Client):
    assert client.session.proxies == {}
    proxy = {"https": "http://localhost:8888"}
    client.configure(proxies=proxy)
    assert client.session.proxies.get("https") == proxy["https"]


def test_configure_ssl_verify(client: Client):
    assert client.session.verify is True
    client.configure(ssl_verify=False)
    assert client.session.verify is False


def test_configure_timeout(client: Client):
    assert client.timeout == 10
    client.configure(timeout=99)
    assert client.timeout == 99


def test_client_request(authed_client: Client):
    ok_resp = make_mock_response("<html>OK</html>", status_code=200)
    not_found_resp = make_mock_response(
        "<html>Not Found</html>", status_code=404
    )
    not_found_resp.ok = False
    not_found_resp.raise_for_status.side_effect = RequestException(
        "404 Client Error"
    )

    call_count = {"n": 0}

    def mock_session_request(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return ok_resp
        return not_found_resp

    authed_client.session.request = mock_session_request
    resp = authed_client.request("GET", "connect", "/")
    assert resp.ok

    with pytest.raises(GarthHTTPError) as e:
        authed_client.request("GET", "connectapi", "/", api=True)
    assert "404" in str(e.value)


def test_retry_on_503(authed_client: Client, monkeypatch: pytest.MonkeyPatch):
    authed_client.configure(retries=2, backoff_factor=0.5)
    retry_resp = make_mock_response("service unavailable", status_code=503)
    ok_resp = make_mock_response({"ok": True}, status_code=200)

    calls = {"n": 0}

    def mock_session_request(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            return retry_resp
        return ok_resp

    sleeps: list[float] = []

    def mock_sleep(value: float):
        sleeps.append(value)

    monkeypatch.setattr(authed_client.session, "request", mock_session_request)
    monkeypatch.setattr("garth.http._time.sleep", mock_sleep)

    response = authed_client.request("GET", "connectapi", "/test", api=False)

    assert response.status_code == 200
    assert calls["n"] == 3
    assert sleeps == [0.5, 1.0]


def test_login_full_flow(monkeypatch: pytest.MonkeyPatch, client: Client):
    oauth2_token = OAuth2Token(
        access_token="test_access_token_jwt",
        refresh_token="test_refresh_token",
        expires_in=3600,
        expires_at=time.time() + 3600,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )

    monkeypatch.setattr(
        http_mod.sso,
        "login",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: oauth2_token,
    )

    result = client.login("user@example.com", "password")

    assert result == oauth2_token
    assert client.oauth2_token == oauth2_token


def test_login_mfa_with_prompt(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    mfa_state = MFAState(
        strategy_name="json-portal",
        domain="garmin.com",
        state={"mfa_url": "https://sso.garmin.com/portal/api/mfa/verifyCode"},
    )
    oauth2_token = OAuth2Token(
        access_token="test_access_token_jwt",
        refresh_token="test_refresh_token",
        expires_in=3600,
        expires_at=time.time() + 3600,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )

    def prompt_mfa() -> str:
        return "123456"

    monkeypatch.setattr(
        http_mod.sso,
        "login",
        lambda *a, **kw: (_ for _ in ()).throw(
            MFARequiredError(msg="MFA required", state=mfa_state)
        ),
    )
    monkeypatch.setattr(
        http_mod.sso,
        "handle_mfa",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: oauth2_token,
    )

    result = client.login(
        "user@example.com",
        "password",
        prompt_mfa=prompt_mfa,
    )

    assert result == oauth2_token
    assert client.oauth2_token == oauth2_token


def test_login_return_on_mfa(monkeypatch: pytest.MonkeyPatch, client: Client):
    mfa_state = MFAState(
        strategy_name="json-portal",
        domain="garmin.com",
        state={"mfa_url": "https://sso.garmin.com/portal/api/mfa/verifyCode"},
    )

    monkeypatch.setattr(
        http_mod.sso,
        "login",
        lambda *a, **kw: (_ for _ in ()).throw(
            MFARequiredError(msg="MFA required", state=mfa_state)
        ),
    )

    result = client.login(
        "user@example.com",
        "password",
        return_on_mfa=True,
    )

    assert result == mfa_state
    assert client.oauth2_token is None


def test_refresh_token_uses_new_refresh_function(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    current_token = OAuth2Token(
        access_token="access-old",
        refresh_token="refresh-old",
        expires_in=3600,
        expires_at=time.time() - 1,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )
    refreshed_token = OAuth2Token(
        access_token="access-new",
        refresh_token="refresh-new",
        expires_in=3600,
        expires_at=time.time() + 3600,
    )
    client.oauth2_token = current_token

    monkeypatch.setattr(
        http_mod.oauth,
        "refresh_oauth2_token",
        lambda *a, **kw: refreshed_token,
    )

    client.refresh_token()

    assert client.oauth2_token == refreshed_token


def test_request_refreshes_expired_token(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    expired_token = OAuth2Token(
        access_token="access-old",
        refresh_token="refresh-old",
        expires_in=3600,
        expires_at=time.time() - 1,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )
    refreshed_token = OAuth2Token(
        access_token="access-new",
        refresh_token="refresh-new",
        expires_in=3600,
        expires_at=time.time() + 3600,
    )
    response = make_mock_response({"ok": True}, status_code=200)
    captured_headers: dict[str, str] = {}

    def mock_refresh_token():
        client.oauth2_token = refreshed_token

    def mock_session_request(method, url, headers=None, **kwargs):
        if headers is not None:
            captured_headers.update(headers)
        return response

    client.oauth2_token = expired_token
    monkeypatch.setattr(client, "refresh_token", mock_refresh_token)
    monkeypatch.setattr(client.session, "request", mock_session_request)

    client.request("GET", "connectapi", "/test", api=True)

    assert captured_headers["Authorization"] == "Bearer access-new"


def test_request_requires_valid_oauth2_token(client: Client):
    with pytest.raises(
        GarthException,
        match="No valid OAuth2 token. Please login.",
    ):
        client.request("GET", "connectapi", "/test", api=True)


def test_username(authed_client: Client):
    interactions = _load_cassette("tests/cassettes/test_username.yaml")
    profile_data = parse_response_body(interactions[0])

    assert authed_client._user_profile is None
    authed_client.connectapi = lambda *a, **kw: profile_data
    assert authed_client.username
    assert authed_client._user_profile


def test_profile_alias(authed_client: Client):
    interactions = _load_cassette("tests/cassettes/test_profile_alias.yaml")
    profile_data = parse_response_body(interactions[0])

    assert authed_client._user_profile is None
    authed_client.connectapi = lambda *a, **kw: profile_data
    profile = authed_client.profile
    assert profile == authed_client.user_profile
    assert authed_client._user_profile is not None


def test_connectapi(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/cassettes/test_connectapi.yaml",
    )
    stress = cast(
        list[dict[str, Any]],
        authed_client.connectapi(
            "/usersummary-service/stats/stress/daily/2023-07-21/2023-07-21"
        ),
    )
    assert stress
    assert isinstance(stress, list)
    assert len(stress) == 1
    assert stress[0]["calendarDate"] == "2023-07-21"
    assert list(stress[0]["values"].keys()) == [
        "highStressDuration",
        "lowStressDuration",
        "overallStressLevel",
        "restStressDuration",
        "mediumStressDuration",
    ]


def test_download(authed_client: Client):
    interactions = _load_cassette("tests/cassettes/test_download.yaml")
    raw_body = interactions[0]["response"]["body"]["string"]
    mock_resp = make_mock_response(raw_body, status_code=200)
    authed_client.session.request = lambda *a, **kw: mock_resp

    downloaded = authed_client.download(
        "/download-service/files/activity/11998957007"
    )
    assert downloaded
    zip_magic_number = b"\x50\x4b\x03\x04"
    assert downloaded[:4] == zip_magic_number


def test_upload(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/cassettes/test_upload.yaml",
    )
    fpath = "tests/12129115726_ACTIVITY.fit"
    with open(fpath, "rb") as f:
        uploaded = authed_client.upload(f)
    assert uploaded


def test_upload_uses_multipart(authed_client: Client):
    from io import BytesIO
    from unittest.mock import MagicMock, patch

    from curl_cffi import CurlMime

    # Create fake FIT file with a .name attribute
    fake_data = b"FIT\x00test"
    fp = BytesIO(fake_data)
    fp.name = "test.fit"

    # Mock the low-level session.request to avoid real HTTP
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "detailedImportResult": {"successes": []}
    }

    with patch.object(
        authed_client.session, "request", return_value=mock_response
    ) as mock_req:
        authed_client.upload(fp)

    # Verify multipart= was passed (not files=)
    call_kwargs = mock_req.call_args.kwargs
    assert "files" not in call_kwargs, (
        "files= was passed — should use multipart= instead"
    )
    assert "multipart" in call_kwargs, "multipart= was not passed"
    assert isinstance(call_kwargs["multipart"], CurlMime), (
        "multipart value must be a CurlMime instance"
    )


def test_delete(authed_client: Client):
    interactions = _load_cassette("tests/cassettes/test_delete.yaml")

    data_interactions = [i for i in interactions if _is_data_interaction(i)]
    bodies = []
    for inter in data_interactions:
        code = inter["response"]["status"]["code"]
        if code == 204:
            bodies.append(None)
        else:
            bodies.append(parse_response_body(inter))
    codes = [i["response"]["status"]["code"] for i in data_interactions]

    call_idx = {"n": 0}

    def mock_session_request(*args, **kwargs):
        idx = call_idx["n"]
        call_idx["n"] += 1
        body = bodies[idx] if idx < len(bodies) else None
        code = codes[idx] if idx < len(codes) else 200
        resp = make_mock_response(body or "", code)
        if code == 200 and body:
            resp.json.return_value = body
        if code >= 400:
            resp.ok = False
            resp.raise_for_status.side_effect = RequestException(
                f"{code} Client Error"
            )
        return resp

    authed_client.session.request = mock_session_request

    activity_id = "12135235656"
    path = f"/activity-service/activity/{activity_id}"
    assert authed_client.connectapi(path)
    authed_client.delete(
        "connectapi",
        path,
        api=True,
    )
    with pytest.raises(GarthHTTPError) as e:
        authed_client.connectapi(path)
    assert "404" in str(e.value)


def test_put(authed_client: Client):
    interactions = _load_cassette("tests/cassettes/test_put.yaml")

    data_interactions = [i for i in interactions if _is_data_interaction(i)]

    responses = []
    for inter in data_interactions:
        code = inter["response"]["status"]["code"]
        if code == 204:
            responses.append(make_mock_response("", code))
        else:
            body = parse_response_body(inter)
            resp = make_mock_response(body, code)
            resp.json.return_value = body
            responses.append(resp)

    call_idx = {"n": 0}

    def mock_session_request(*args, **kwargs):
        idx = call_idx["n"]
        call_idx["n"] += 1
        return responses[idx]

    authed_client.session.request = mock_session_request

    data = [
        {
            "changeState": "CHANGED",
            "trainingMethod": "HR_RESERVE",
            "lactateThresholdHeartRateUsed": 170,
            "maxHeartRateUsed": 185,
            "restingHrAutoUpdateUsed": False,
            "sport": "DEFAULT",
            "zone1Floor": 130,
            "zone2Floor": 140,
            "zone3Floor": 150,
            "zone4Floor": 160,
            "zone5Floor": 170,
        }
    ]
    path = "/biometric-service/heartRateZones"
    authed_client.put(
        "connectapi",
        path,
        api=True,
        json=data,
    )
    assert authed_client.connectapi(path)


def test_resume_login_flow(monkeypatch: pytest.MonkeyPatch, client: Client):
    mfa_state = MFAState(
        strategy_name="json-portal",
        domain="garmin.com",
        state={"mfa_url": "https://sso.garmin.com/portal/api/mfa/verifyCode"},
    )
    oauth2_token = OAuth2Token(
        access_token="test_access_token_jwt",
        refresh_token="test_refresh_token",
        expires_in=3600,
        expires_at=time.time() + 3600,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )

    monkeypatch.setattr(
        http_mod.sso,
        "handle_mfa",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: oauth2_token,
    )

    result = client.resume_login(mfa_state, "123456")

    assert result == oauth2_token
    assert client.oauth2_token == oauth2_token


def test_auto_save_on_refresh(garth_home_client, monkeypatch):
    client, tempdir, mock_oauth2_token = garth_home_client
    client.oauth2_token = OAuth2Token(
        access_token="access-old",
        refresh_token="refresh-old",
        expires_in=3600,
        expires_at=time.time() - 1,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "refresh_oauth2_token",
        lambda *a, **kw: mock_oauth2_token,
    )

    client.refresh_token()
    _assert_oauth2_token_saved(tempdir, mock_oauth2_token)


def test_refresh_token_no_save_without_garth_home(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    client.oauth2_token = OAuth2Token(
        access_token="access-old",
        refresh_token="refresh-old",
        expires_in=3600,
        expires_at=time.time() - 1,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )
    refreshed_token = OAuth2Token(
        access_token="access-new",
        refresh_token="refresh-new",
        expires_in=3600,
        expires_at=time.time() + 3600,
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "refresh_oauth2_token",
        lambda *a, **kw: refreshed_token,
    )
    dump_called = []
    monkeypatch.setattr(
        client, "dump", lambda *a, **kw: dump_called.append(True)
    )

    client.refresh_token()

    assert client.oauth2_token == refreshed_token
    assert not dump_called  # dump must NOT be called


def test_request_raises_when_no_response(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    def mock_session_request(*a, **kw):
        return None

    monkeypatch.setattr(client.session, "request", mock_session_request)

    with pytest.raises(GarthException, match="No response returned"):
        client.request("GET", "connect", "/test")


def test_on_token_update_fires_on_login(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    oauth2_token = OAuth2Token(
        access_token="test_access_token_jwt",
        refresh_token="test_refresh_token",
        expires_in=3600,
        expires_at=time.time() + 3600,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )
    received: list[OAuth2Token] = []
    client.configure(on_token_update=received.append)

    monkeypatch.setattr(
        http_mod.sso,
        "login",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: oauth2_token,
    )

    client.login("user@example.com", "password")
    assert received == [oauth2_token]


def test_on_token_update_fires_on_refresh(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    client.oauth2_token = OAuth2Token(
        access_token="access-old",
        refresh_token="refresh-old",
        expires_in=3600,
        expires_at=time.time() - 1,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )
    refreshed_token = OAuth2Token(
        access_token="access-new",
        refresh_token="refresh-new",
        expires_in=3600,
        expires_at=time.time() + 3600,
    )
    received: list[OAuth2Token] = []
    client.configure(on_token_update=received.append)

    monkeypatch.setattr(
        http_mod.oauth,
        "refresh_oauth2_token",
        lambda *a, **kw: refreshed_token,
    )

    client.refresh_token()
    assert received == [refreshed_token]


def test_on_token_update_fires_on_resume_login(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    mfa_state = MFAState(
        strategy_name="json-portal",
        domain="garmin.com",
        state={
            "mfa_url": ("https://sso.garmin.com/portal/api/mfa/verifyCode")
        },
    )
    oauth2_token = OAuth2Token(
        access_token="test_access_token_jwt",
        refresh_token="test_refresh_token",
        expires_in=3600,
        expires_at=time.time() + 3600,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )
    received: list[OAuth2Token] = []
    client.configure(on_token_update=received.append)

    monkeypatch.setattr(
        http_mod.sso,
        "handle_mfa",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: oauth2_token,
    )

    client.resume_login(mfa_state, "123456")
    assert received == [oauth2_token]


def test_on_token_update_replaces_dump(garth_home_client, monkeypatch):
    client, _, mock_oauth2_token = garth_home_client
    dump_called: list[bool] = []
    monkeypatch.setattr(
        client, "dump", lambda *a, **kw: dump_called.append(True)
    )
    received: list[OAuth2Token] = []
    client.configure(on_token_update=received.append)

    monkeypatch.setattr(
        http_mod.sso,
        "login",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: mock_oauth2_token,
    )

    client.login("user@example.com", "password")
    assert received == [mock_oauth2_token]
    assert not dump_called


def test_on_token_update_fires_without_garth_home(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    assert client._garth_home is None
    oauth2_token = OAuth2Token(
        access_token="test_access_token_jwt",
        refresh_token="test_refresh_token",
        expires_in=3600,
        expires_at=time.time() + 3600,
    )
    received: list[OAuth2Token] = []
    client.configure(on_token_update=received.append)

    monkeypatch.setattr(
        http_mod.sso,
        "login",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: oauth2_token,
    )

    client.login("user@example.com", "password")
    assert received == [oauth2_token]


def test_on_token_update_exception_propagates(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    client.oauth2_token = OAuth2Token(
        access_token="access-old",
        refresh_token="refresh-old",
        expires_in=3600,
        expires_at=time.time() - 1,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
    )
    refreshed_token = OAuth2Token(
        access_token="access-new",
        refresh_token="refresh-new",
        expires_in=3600,
        expires_at=time.time() + 3600,
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "refresh_oauth2_token",
        lambda *a, **kw: refreshed_token,
    )

    def boom(token: OAuth2Token):
        raise ValueError("callback failed")

    client.configure(on_token_update=boom)

    with pytest.raises(ValueError, match="callback failed"):
        client.refresh_token()


def test_on_token_update_not_called_on_load(
    oauth2_token: OAuth2Token,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        client = Client()
        client.oauth2_token = oauth2_token
        client.dump(tmpdir)

        received: list[OAuth2Token] = []
        new_client = Client()
        new_client.configure(on_token_update=received.append)
        new_client.load(tmpdir)

        assert new_client.oauth2_token == oauth2_token
        assert not received


def test_default_on_token_update_is_noop(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GARTH_HOME", raising=False)
    monkeypatch.delenv("GARTH_TOKEN", raising=False)
    client = Client()
    mock_token = OAuth2Token(
        access_token="test",
        refresh_token="refresh",
        expires_in=3600,
        expires_at=time.time() + 3600,
    )
    # Default callback should be callable and not raise
    client._on_token_update(mock_token)  # Must not raise
    assert callable(client._on_token_update)


def test_auto_resume_sets_dump_callback(monkeypatch: pytest.MonkeyPatch):
    with tempfile.TemporaryDirectory() as tempdir:
        monkeypatch.setenv("GARTH_HOME", tempdir)
        monkeypatch.delenv("GARTH_TOKEN", raising=False)
        client = Client()
        mock_token = OAuth2Token(
            access_token="test",
            refresh_token="refresh",
            expires_in=3600,
            expires_at=time.time() + 3600,
        )
        client.oauth2_token = mock_token
        # Calling the callback should dump the token to disk
        client._on_token_update(mock_token)
        _assert_oauth2_token_saved(tempdir, mock_token)


def test_configure_resets_to_dump_to_home(garth_home_client, monkeypatch):
    client, tempdir, mock_oauth2_token = garth_home_client
    received: list[OAuth2Token] = []
    client.configure(on_token_update=received.append)
    client._on_token_update(mock_oauth2_token)
    assert received == [mock_oauth2_token]
    received.clear()

    client.configure(on_token_update=client.dump_to_home)
    client.oauth2_token = mock_oauth2_token
    client._on_token_update(mock_oauth2_token)

    _assert_oauth2_token_saved(tempdir, mock_oauth2_token)


def test_configure_resets_to_dump_to_home_noop(
    monkeypatch: pytest.MonkeyPatch, client: Client
):
    assert client._garth_home is None
    received: list[OAuth2Token] = []
    client.configure(on_token_update=received.append)

    client.configure(on_token_update=client.dump_to_home)
    mock_token = OAuth2Token(
        access_token="test",
        refresh_token="refresh",
        expires_in=3600,
        expires_at=time.time() + 3600,
    )
    client._on_token_update(mock_token)
    assert not received
    assert callable(client._on_token_update)


def test_custom_callback_overrides_auto_dump(garth_home_client, monkeypatch):
    client, tempdir, mock_oauth2_token = garth_home_client
    dump_called: list[bool] = []
    monkeypatch.setattr(
        client, "dump", lambda *a, **kw: dump_called.append(True)
    )
    received: list[OAuth2Token] = []
    client.configure(on_token_update=received.append)

    monkeypatch.setattr(
        http_mod.sso,
        "login",
        lambda *a, **kw: LoginResult(
            "ST-ticket", "https://sso.garmin.com/sso/embed"
        ),
    )
    monkeypatch.setattr(
        http_mod.oauth,
        "exchange_service_ticket",
        lambda *a, **kw: mock_oauth2_token,
    )

    client.login("user@example.com", "password")
    assert received == [mock_oauth2_token]
    assert not dump_called  # Custom callback replaced dump lambda


def test_configure_none_disables_callback(
    garth_home_client, monkeypatch: pytest.MonkeyPatch
):
    client, tempdir, mock_oauth2_token = garth_home_client
    # _auto_resume set dump_to_home because GARTH_HOME exists
    # Verify dump is initially active
    client.oauth2_token = mock_oauth2_token
    client._on_token_update(mock_oauth2_token)
    _assert_oauth2_token_saved(tempdir, mock_oauth2_token)

    # Clear saved token for next test
    import os as os_module

    oauth2_path = os_module.path.join(
        os_module.path.expanduser(tempdir), "oauth2_token.json"
    )
    if os_module.path.exists(oauth2_path):
        os_module.remove(oauth2_path)

    # Disable via None
    client.configure(on_token_update=None)
    assert callable(client._on_token_update)

    # Override to custom callback
    received: list[OAuth2Token] = []
    client.configure(on_token_update=received.append)
    # Disable again with None
    client.configure(on_token_update=None)
    client._on_token_update(mock_oauth2_token)
    # Should not have called the custom callback
    assert not received
    assert callable(client._on_token_update)
