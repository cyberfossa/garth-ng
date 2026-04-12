from dataclasses import dataclass, field
from typing import Any


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
