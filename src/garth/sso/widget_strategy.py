from __future__ import annotations

import random
import re
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from curl_cffi.requests.exceptions import (
    RequestException as CurlRequestException,
)

from ..exc import (
    AuthenticationError,
    CloudflareError,
    MFARequiredError,
    NetworkError,
)
from .state import MFAState
from .strategy import LoginResult


if TYPE_CHECKING:
    from curl_cffi.requests import Session


class WidgetStrategy:
    @property
    def name(self) -> str:
        return "widget"

    def login(
        self,
        session: Session,
        email: str,
        password: str,
        domain: str,
    ) -> LoginResult:
        sso_base = f"https://sso.{domain}/sso"
        embed_url = f"{sso_base}/embed"
        signin_url = f"{sso_base}/signin"

        embed_params = {
            "id": "gauth-widget",
            "embedWidget": "true",
            "gauthHost": sso_base,
        }
        signin_params = {
            **embed_params,
            "gauthHost": embed_url,
            "service": embed_url,
            "source": embed_url,
            "redirectAfterAccountLoginUrl": embed_url,
            "redirectAfterAccountCreationUrl": embed_url,
        }

        try:
            _ = session.get(embed_url, params=embed_params)
        except CurlRequestException as e:
            raise NetworkError(
                msg=f"Network error during embed GET: {e}"
            ) from e

        try:
            resp = session.get(
                signin_url,
                params=signin_params,
                headers={"Referer": embed_url},
            )
        except CurlRequestException as e:
            raise NetworkError(
                msg=f"Network error during signin GET: {e}"
            ) from e
        if self._is_cloudflare(resp):
            raise CloudflareError(msg="Cloudflare challenge on signin page")

        csrf_token = self._extract_csrf(resp.text)

        time.sleep(random.uniform(1.5, 4.0))

        try:
            resp = session.post(
                signin_url,
                params=signin_params,
                headers={"Referer": resp.url},
                data={
                    "username": email,
                    "password": password,
                    "_csrf": csrf_token,
                    "embed": "true",
                },
            )
        except CurlRequestException as e:
            raise NetworkError(
                msg=f"Network error during signin POST: {e}"
            ) from e
        if self._is_cloudflare(resp):
            raise CloudflareError(msg="Cloudflare challenge on POST")

        if self._is_mfa_required(resp.text):
            mfa_csrf = self._extract_csrf(resp.text)
            mfa_url = f"https://sso.{domain}/sso/verifyMFA/loginEnterMfaCode"
            raise MFARequiredError(
                msg="MFA required",
                state=MFAState(
                    strategy_name=self.name,
                    domain=domain,
                    state={
                        "mfa_url": mfa_url,
                        "service_url": embed_url,
                        "signin_params": signin_params,
                        "csrf_token": mfa_csrf,
                        "referer": str(resp.url),
                    },
                ),
            )

        ticket = self._extract_ticket(resp)
        if ticket:
            return LoginResult(ticket, embed_url)

        raise AuthenticationError(
            msg="Widget login failed: no ticket in response"
        )

    def handle_mfa(
        self,
        session: Session,
        _domain: str,
        state: dict[str, object],
        mfa_code: str,
    ) -> LoginResult:
        mfa_url = str(state["mfa_url"])
        signin_params = state.get("signin_params")
        csrf_token = state.get("csrf_token", "")
        referer = state.get("referer", mfa_url)
        try:
            resp = session.post(
                mfa_url,
                params=signin_params,
                headers={"Referer": str(referer)},
                data={
                    "mfa-code": mfa_code,
                    "embed": "true",
                    "_csrf": str(csrf_token),
                    "fromPage": "setupEnterMfaCode",
                },
            )
        except CurlRequestException as e:
            raise NetworkError(
                msg=f"Network error during MFA POST: {e}"
            ) from e
        ticket = self._extract_ticket(resp)
        if ticket:
            return LoginResult(ticket, str(state["service_url"]))
        raise AuthenticationError(
            msg="Widget MFA failed: no ticket in response"
        )

    def _extract_csrf(self, html: str) -> str:
        patterns = [
            r'name="_csrf"\s+value="([^"]+)"',
            r'name="_csrf"[^>]*value="([^"]+)"',
            r'value="([^"]+)"\s+name="_csrf"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        raise AuthenticationError(msg="No CSRF token found in login page")

    def _extract_ticket(self, response: object) -> str | None:
        text = getattr(response, "text", None)
        if isinstance(text, str):
            ticket = self._extract_ticket_from_text(text)
            if ticket:
                return ticket

        json_func = getattr(response, "json", None)
        if callable(json_func):
            try:
                payload = cast(Callable[[], object], json_func)()
            except (TypeError, ValueError):
                payload = None
            if payload is not None:
                ticket = self._extract_ticket_from_json(payload)
                if ticket:
                    return ticket

        url = getattr(response, "url", None)
        if isinstance(url, str):
            ticket = self._extract_ticket_from_text(url)
            if ticket:
                return ticket

        headers = getattr(response, "headers", None)
        get_method = getattr(headers, "get", None)
        if callable(get_method):
            location = get_method("Location") or get_method("location")
            if isinstance(location, str):
                ticket = self._extract_ticket_from_text(location)
                if ticket:
                    return ticket

        return None

    def _extract_ticket_from_text(self, value: str) -> str | None:
        patterns = [
            r'embed\?ticket=(ST-[^"&\s]+)',
            r'[?&]ticket=(ST-[^"&\s]+)',
            r'"serviceTicketId"\s*:\s*"(ST-[^"]+)"',
            r'"serviceTicket"\s*:\s*"(ST-[^"]+)"',
            r'"ticket"\s*:\s*"(ST-[^"]+)"',
            r'serviceTicketId["\'\s:=]+(ST-[^"\'\s<,&]+)',
            r'ticket["\'\s:=]+(ST-[^"\'\s<,&]+)',
            r'^(ST-[^"\'\s<,&]+)$',
        ]
        for pattern in patterns:
            match = re.search(pattern, value)
            if match:
                return match.group(1)
        return None

    def _extract_ticket_from_json(self, payload: object) -> str | None:
        if isinstance(payload, dict):
            for value in payload.values():
                ticket = self._extract_ticket_from_json(value)
                if ticket:
                    return ticket
            return None
        if isinstance(payload, list):
            for value in payload:
                ticket = self._extract_ticket_from_json(value)
                if ticket:
                    return ticket
            return None
        if isinstance(payload, str):
            return self._extract_ticket_from_text(payload)
        return None

    def _is_cloudflare(self, resp: object) -> bool:
        text = getattr(resp, "text", None)
        if isinstance(text, str):
            return (
                "cf-browser-verification" in text
                or "Just a moment" in text
                or "__cf_chl" in text
            )
        return False

    def _is_mfa_required(self, html: str) -> bool:
        mfa_indicators = [
            "loginEnterMfaCode",
            "mfaMethod",
            "mfa-code",
            "verifyMFA",
        ]
        return any(indicator in html for indicator in mfa_indicators)
