# pyright: reportExplicitAny=false, reportAny=false

import dataclasses
import json
from dataclasses import dataclass, field
from typing import Any

from garth.exc import GarthException


@dataclass
class MFAState:
    """Session context for deferred MFA completion.

    Created by login() when MFA is required and return_on_mfa=True. Pass this
    state along with the MFA code to Client.resume_login() to complete
    authentication after the user has provided their MFA code.

    Attributes:
        strategy_name: Name of the login strategy that created this state.
            Used to dispatch the MFA verification to the correct strategy.
        domain: Garmin domain (garmin.com or garmin.cn).
        state: Strategy-specific session data needed to complete MFA.
    """

    strategy_name: str
    domain: str
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class MFAChallenge:
    """Session context for deferred MFA completion with cookies.

    This wraps the MFA state together with the session cookies required to
    resume authentication after the user provides the MFA code.

    Security: The serialized JSON from ``to_json()`` contains session cookies
    that grant access to the Garmin SSO flow. Treat this data as a secret —
    do not expose it to untrusted parties, log it, or store it unencrypted
    in publicly accessible locations.

    Attributes:
        mfa_state: MFA state created during login.
        cookies: Session cookies needed to continue the MFA flow.
    """

    mfa_state: MFAState
    cookies: dict[str, str]

    def to_json(self) -> str:
        """Serialize this MFA challenge to a JSON string.

        Returns:
            JSON representation of the MFA challenge.
        """
        return json.dumps(
            {
                "mfa_state": dataclasses.asdict(self.mfa_state),
                "cookies": self.cookies,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> "MFAChallenge":
        """Deserialize an MFA challenge from a JSON string.

        Args:
            data: JSON representation of an MFA challenge.

        Returns:
            A reconstructed MFAChallenge instance.

        Raises:
            GarthException: If the JSON is malformed or missing required keys,
                or if the domain is not in the allowlist.
        """
        from garth.http import ALLOWED_DOMAINS

        try:
            parsed_data: dict[str, Any] = json.loads(data)
            mfa_state_data: dict[str, Any] = parsed_data["mfa_state"]
            cookies: dict[str, str] = parsed_data["cookies"]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise GarthException(msg=f"Invalid MFA challenge data: {e}") from e
        try:
            mfa_state = MFAState(**mfa_state_data)
        except (TypeError, ValueError) as e:
            raise GarthException(msg=f"Invalid MFA state fields: {e}") from e
        if mfa_state.domain not in ALLOWED_DOMAINS:
            raise GarthException(
                msg=f"Invalid domain in MFA state: {mfa_state.domain!r}. "
                f"Allowed: {sorted(ALLOWED_DOMAINS)}"
            )
        return cls(mfa_state=mfa_state, cookies=cookies)
