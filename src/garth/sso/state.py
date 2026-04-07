from dataclasses import dataclass, field
from typing import Any


@dataclass
class MFAState:
    strategy_name: str
    domain: str
    state: dict[str, Any] = field(default_factory=dict)
