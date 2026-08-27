"""
Threat lifecycle state machine.
Enforces the PRD transition graph: NEW → ACKNOWLEDGED → INVESTIGATING → DISPATCHED → RESOLVED (+ FALSE_POSITIVE).
"""

from app.db.models import ThreatStatusEnum

# Valid state transitions: current_state → set of allowed next states
VALID_TRANSITIONS: dict[ThreatStatusEnum, set[ThreatStatusEnum]] = {
    ThreatStatusEnum.NEW: {
        ThreatStatusEnum.ACKNOWLEDGED,
        ThreatStatusEnum.FALSE_POSITIVE,
    },
    ThreatStatusEnum.ACKNOWLEDGED: {
        ThreatStatusEnum.INVESTIGATING,
        ThreatStatusEnum.FALSE_POSITIVE,
    },
    ThreatStatusEnum.INVESTIGATING: {
        ThreatStatusEnum.DISPATCHED,
        ThreatStatusEnum.FALSE_POSITIVE,
    },
    ThreatStatusEnum.DISPATCHED: {
        ThreatStatusEnum.RESOLVED,
    },
    ThreatStatusEnum.RESOLVED: set(),       # Terminal state
    ThreatStatusEnum.FALSE_POSITIVE: set(),  # Terminal state
}


def validate_transition(current: ThreatStatusEnum, target: ThreatStatusEnum) -> bool:
    """
    Check whether transitioning from `current` to `target` is allowed.
    Returns True if the transition is valid, False otherwise.
    """
    allowed = VALID_TRANSITIONS.get(current, set())
    return target in allowed


def get_valid_transitions(current: ThreatStatusEnum) -> list[str]:
    """Return list of valid next states from the current state."""
    return [s.value for s in VALID_TRANSITIONS.get(current, set())]
