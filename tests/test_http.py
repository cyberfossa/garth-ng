import tempfile
import time
from typing import Any, cast

import pytest
from helpers import (
    _is_data_interaction,
    _is_profile_interaction,
    load_cassette as _load_cassette,
    make_mock_response,
    parse_response_body,
)

from garth.auth_tokens import OAuth1Token, OAuth2Token
from garth.exc import GarthException, GarthHTTPError
from garth.http import Client


def test_dump_and_load(authed_client: Client):
    with tempfile.TemporaryDirectory() as tempdir:
        authed_client.dump(tempdir)

        new_client = Client()
        new_client.load(tempdir)

        assert new_client.oauth1_token == authed_client.oauth1_token
        assert new_client.oauth2_token == authed_client.oauth2_token


def test_dumps_and_loads(authed_client: Client):
    s = authed_client.dumps()
    new_client = Client()
    new_client.loads(s)
    assert new_client.oauth1_token == authed_client.oauth1_token
    assert new_client.oauth2_token == authed_client.oauth2_token


def test_auto_resume_garth_home(
    authed_client: Client, monkeypatch: pytest.MonkeyPatch
):
    with tempfile.TemporaryDirectory() as tempdir:
        authed_client.dump(tempdir)
        monkeypatch.setenv("GARTH_HOME", tempdir)
        monkeypatch.delenv("GARTH_TOKEN", raising=False)

        client = Client()
        assert client.oauth1_token == authed_client.oauth1_token
        assert client.oauth2_token == authed_client.oauth2_token


def test_auto_resume_garth_token(
    authed_client: Client, monkeypatch: pytest.MonkeyPatch
):
    token = authed_client.dumps()
    monkeypatch.setenv("GARTH_TOKEN", token)
    monkeypatch.delenv("GARTH_HOME", raising=False)

    client = Client()
    assert client.oauth1_token == authed_client.oauth1_token
    assert client.oauth2_token == authed_client.oauth2_token


def test_auto_resume_garth_home_missing_tokens(
    monkeypatch: pytest.MonkeyPatch,
):
    with tempfile.TemporaryDirectory() as tempdir:
        monkeypatch.setenv("GARTH_HOME", tempdir)
        monkeypatch.delenv("GARTH_TOKEN", raising=False)

        client = Client()
        assert client._garth_home == tempdir
        assert client.oauth1_token is None
        assert client.oauth2_token is None


@pytest.fixture
def garth_home_client(monkeypatch: pytest.MonkeyPatch):
    import garth._sso_legacy

    with tempfile.TemporaryDirectory() as tempdir:
        monkeypatch.setenv("GARTH_HOME", tempdir)
        monkeypatch.delenv("GARTH_TOKEN", raising=False)

        client = Client()
        mock_oauth1 = OAuth1Token(
            oauth_token="test_token",
            oauth_token_secret="test_secret",
            domain="garmin.com",
        )
        mock_oauth2 = OAuth2Token(
            scope="CONNECT_READ",
            jti="test_jti",
            token_type="Bearer",
            access_token="test_access",
            refresh_token="test_refresh",
            expires_in=3600,
            refresh_token_expires_in=7200,
            expires_at=int(time.time() + 3600),
            refresh_token_expires_at=int(time.time() + 7200),
        )
        yield (
            client,
            tempdir,
            mock_oauth1,
            mock_oauth2,
            garth._sso_legacy,
        )


def _assert_tokens_saved(tempdir, mock_oauth1, mock_oauth2):
    loaded = Client()
    loaded.load(tempdir)
    assert loaded.oauth1_token == mock_oauth1
    assert loaded.oauth2_token == mock_oauth2


def test_auto_save_on_login(garth_home_client, monkeypatch):
    client, tempdir, mock_oauth1, mock_oauth2, sso_mod = garth_home_client
    monkeypatch.setattr(
        sso_mod,
        "login",
        lambda *a, **kw: (mock_oauth1, mock_oauth2),
    )

    client.login("user@example.com", "password")
    _assert_tokens_saved(tempdir, mock_oauth1, mock_oauth2)


def test_auto_save_on_resume_login(garth_home_client, monkeypatch):
    client, tempdir, mock_oauth1, mock_oauth2, sso_mod = garth_home_client
    monkeypatch.setattr(
        sso_mod,
        "resume_login",
        lambda *a, **kw: (mock_oauth1, mock_oauth2),
    )

    client.resume_login({"client": client, "login_params": {}}, "123")
    _assert_tokens_saved(tempdir, mock_oauth1, mock_oauth2)


def test_auto_resume_both_set_raises(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("GARTH_HOME", "/some/path")
    monkeypatch.setenv("GARTH_TOKEN", "some_token")

    with pytest.raises(GarthException, match="cannot both be set"):
        Client()


def test_auto_persist_on_refresh(
    authed_client: Client, monkeypatch: pytest.MonkeyPatch
):
    with tempfile.TemporaryDirectory() as tempdir:
        authed_client.dump(tempdir)
        monkeypatch.setenv("GARTH_HOME", tempdir)
        monkeypatch.delenv("GARTH_TOKEN", raising=False)

        client = Client()
        assert client._garth_home == tempdir

        new_oauth2 = OAuth2Token(
            scope="CONNECT_READ CONNECT_WRITE",
            jti="new_jti",
            token_type="Bearer",
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            expires_in=7200,
            refresh_token_expires_in=14400,
            expires_at=int(time.time() + 7200),
            refresh_token_expires_at=int(time.time() + 14400),
        )

        import garth._sso_legacy

        monkeypatch.setattr(
            garth._sso_legacy,
            "exchange",
            lambda *args, **kwargs: new_oauth2,
        )

        import os

        oauth1_path = os.path.join(tempdir, "oauth1_token.json")
        oauth1_mtime_before = os.path.getmtime(oauth1_path)

        time.sleep(0.01)

        client.refresh_oauth2()

        oauth1_mtime_after = os.path.getmtime(oauth1_path)
        assert oauth1_mtime_before == oauth1_mtime_after

        fresh_client = Client()
        fresh_client.load(tempdir)
        assert fresh_client.oauth2_token == new_oauth2


def test_configure_oauth2_token(client: Client, oauth2_token: OAuth2Token):
    assert client.oauth2_token is None
    client.configure(oauth2_token=oauth2_token)
    assert client.oauth2_token == oauth2_token


def test_configure_domain(client: Client):
    assert client.domain == "garmin.com"
    client.configure(domain="garmin.cn")
    assert client.domain == "garmin.cn"


def test_configure_proxies(client: Client):
    assert client.sess.proxies == {}
    proxy = {"https": "http://localhost:8888"}
    client.configure(proxies=proxy)
    assert client.sess.proxies["https"] == proxy["https"]


def test_configure_ssl_verify(client: Client):
    assert client.sess.verify is True
    client.configure(ssl_verify=False)
    assert client.sess.verify is False


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
    from requests.exceptions import HTTPError

    not_found_resp.raise_for_status.side_effect = HTTPError(
        "404 Client Error", response=not_found_resp
    )

    call_count = {"n": 0}

    def mock_sess_request(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return ok_resp
        return not_found_resp

    authed_client.sess.request = mock_sess_request
    resp = authed_client.request("GET", "connect", "/")
    assert resp.ok

    with pytest.raises(GarthHTTPError) as e:
        authed_client.request("GET", "connectapi", "/", api=True)
    assert "404" in str(e.value)


@pytest.mark.skip(reason="deferred to Task 12")
def test_login_success_mfa(monkeypatch, client: Client):
    pass


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


def test_refresh_oauth2_token(authed_client: Client, monkeypatch):
    assert authed_client.oauth2_token and isinstance(
        authed_client.oauth2_token, OAuth2Token
    )
    authed_client.oauth2_token.expires_at = int(time.time())
    assert authed_client.oauth2_token.expired

    interactions = _load_cassette(
        "tests/cassettes/test_refresh_oauth2_token.yaml"
    )
    profile_data = None
    for inter in interactions:
        if _is_profile_interaction(inter):
            profile_data = parse_response_body(inter)
            break

    new_oauth2 = OAuth2Token(
        scope="CONNECT_READ CONNECT_WRITE",
        jti="refreshed_jti",
        token_type="Bearer",
        access_token="refreshed_access",
        refresh_token="refreshed_refresh",
        expires_in=3600,
        refresh_token_expires_in=7200,
        expires_at=int(time.time() + 3600),
        refresh_token_expires_at=int(time.time() + 7200),
    )

    import garth._sso_legacy

    monkeypatch.setattr(
        garth._sso_legacy,
        "exchange",
        lambda *args, **kwargs: new_oauth2,
    )

    mock_resp = make_mock_response(profile_data)
    mock_resp.json.return_value = profile_data
    authed_client.sess.request = lambda *a, **kw: mock_resp

    profile = authed_client.connectapi("/userprofile-service/socialProfile")
    assert profile
    assert isinstance(profile, dict)
    assert profile["userName"]


def test_download(authed_client: Client):
    interactions = _load_cassette("tests/cassettes/test_download.yaml")
    raw_body = interactions[0]["response"]["body"]["string"]
    mock_resp = make_mock_response(raw_body, status_code=200)
    authed_client.sess.request = lambda *a, **kw: mock_resp

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

    def mock_sess_request(*args, **kwargs):
        idx = call_idx["n"]
        call_idx["n"] += 1
        body = bodies[idx] if idx < len(bodies) else None
        code = codes[idx] if idx < len(codes) else 200
        resp = make_mock_response(body or "", code)
        if code == 200 and body:
            resp.json.return_value = body
        if code >= 400:
            from requests.exceptions import HTTPError

            resp.ok = False
            resp.raise_for_status.side_effect = HTTPError(
                f"{code} Client Error",
                response=resp,
            )
        return resp

    authed_client.sess.request = mock_sess_request

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

    def mock_sess_request(*args, **kwargs):
        idx = call_idx["n"]
        call_idx["n"] += 1
        return responses[idx]

    authed_client.sess.request = mock_sess_request

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


@pytest.mark.skip(reason="deferred to Task 12")
def test_resume_login(client: Client):
    pass
