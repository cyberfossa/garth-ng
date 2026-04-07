"""Test helpers for cassette-based mocking."""

from __future__ import annotations

import gzip
import io
import json
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import urlparse

import yaml


CONNECTAPI_HOST = "connectapi.garmin.com"


def load_cassette(cassette_path: str) -> list[dict[str, Any]]:
    with open(cassette_path) as f:
        cassette = yaml.safe_load(f)
    return cassette.get("interactions", [])


def parse_response_body(interaction: dict[str, Any]) -> Any:
    body = interaction["response"]["body"]["string"]
    if isinstance(body, bytes):
        try:
            buf = io.BytesIO(body)
            body = gzip.GzipFile(fileobj=buf).read()
        except gzip.BadGzipFile:
            pass
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
    try:
        return json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return body


def _is_data_interaction(interaction: dict[str, Any]) -> bool:
    uri = interaction["request"].get("uri", "")
    if CONNECTAPI_HOST not in uri:
        return False
    if "/oauth-service/" in uri:
        return False
    return True


def _is_profile_interaction(interaction: dict[str, Any]) -> bool:
    uri = interaction["request"].get("uri", "")
    return "socialProfile" in uri


def make_mock_response(
    body: Any,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.ok = 200 <= status_code < 400
    if isinstance(body, (dict, list)):
        mock.json.return_value = body
        mock.content = json.dumps(body).encode()
        mock.text = json.dumps(body)
    elif isinstance(body, bytes):
        mock.json.side_effect = ValueError("Not JSON")
        mock.content = body
        mock.text = body.decode("utf-8", errors="replace")
    else:
        mock.json.side_effect = ValueError("Not JSON")
        mock.content = body.encode() if isinstance(body, str) else b""
        mock.text = body if isinstance(body, str) else str(body)
    mock.headers = headers or {}
    mock.url = f"https://{CONNECTAPI_HOST}/test"
    mock.raise_for_status.return_value = None
    return mock


def setup_cassette(
    client: Any,
    cassette_path: str,
) -> None:
    interactions = load_cassette(cassette_path)

    profile_body = None
    data_calls: list[tuple[str, Any]] = []
    for interaction in interactions:
        if not _is_data_interaction(interaction):
            continue
        status = interaction["response"]["status"]["code"]
        uri = interaction["request"].get("uri", "")
        if _is_profile_interaction(interaction):
            profile_body = parse_response_body(interaction)
        elif status == 204:
            data_calls.append((uri, None))
        else:
            data_calls.append((uri, parse_response_body(interaction)))

    if profile_body and isinstance(profile_body, dict):
        client._user_profile = profile_body
        if not data_calls:
            data_calls.append(("", profile_body))

    def _validate_path(path: Any, expected_uri: str) -> None:
        if not path or not expected_uri:
            return

        request_path = urlparse(str(path)).path or str(path)
        expected_path = urlparse(expected_uri).path or expected_uri
        if request_path == expected_path:
            return
        if expected_uri.endswith(request_path):
            return

        raise AssertionError(
            f"Unexpected connectapi path: {path!r}, expected: {expected_uri!r}"
        )

    def _mock_connectapi_response(
        expected_uri: str, body: Any, *args, **kwargs
    ):
        path = args[0] if args else kwargs.get("path")
        _validate_path(path, expected_uri)
        return body

    if len(data_calls) == 0:
        client.connectapi = lambda *a, **kw: None
    elif len(data_calls) == 1:
        expected_uri, body = data_calls[0]

        def _single_mock_connectapi(*args, **kwargs):
            return _mock_connectapi_response(
                expected_uri, body, *args, **kwargs
            )

        client.connectapi = _single_mock_connectapi
    else:
        iterator = iter(data_calls)

        def _mock_connectapi(*args, **kwargs):
            try:
                expected_uri, body = next(iterator)
            except StopIteration:
                return None
            return _mock_connectapi_response(
                expected_uri, body, *args, **kwargs
            )

        client.connectapi = _mock_connectapi
