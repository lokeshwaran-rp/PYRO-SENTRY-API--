"""
Lifecycle state transition unit tests.
Validates the PRD-enforced state machine graph:
NEW -> ACKNOWLEDGED -> INVESTIGATING -> DISPATCHED -> RESOLVED
NEW -> FALSE_POSITIVE
ACKNOWLEDGED -> FALSE_POSITIVE
INVESTIGATING -> FALSE_POSITIVE
"""

import pytest
from app.db.models import ThreatStatusEnum
from app.services.lifecycle import validate_transition, get_valid_transitions, VALID_TRANSITIONS


def test_valid_sequential_transitions():
    """Test full sequential workflow transitions."""
    assert validate_transition(ThreatStatusEnum.NEW, ThreatStatusEnum.ACKNOWLEDGED) is True
    assert validate_transition(ThreatStatusEnum.ACKNOWLEDGED, ThreatStatusEnum.INVESTIGATING) is True
    assert validate_transition(ThreatStatusEnum.INVESTIGATING, ThreatStatusEnum.DISPATCHED) is True
    assert validate_transition(ThreatStatusEnum.DISPATCHED, ThreatStatusEnum.RESOLVED) is True


def test_valid_false_positive_transitions():
    """Test transitions to FALSE_POSITIVE from intermediate non-terminal states."""
    assert validate_transition(ThreatStatusEnum.NEW, ThreatStatusEnum.FALSE_POSITIVE) is True
    assert validate_transition(ThreatStatusEnum.ACKNOWLEDGED, ThreatStatusEnum.FALSE_POSITIVE) is True
    assert validate_transition(ThreatStatusEnum.INVESTIGATING, ThreatStatusEnum.FALSE_POSITIVE) is True


def test_invalid_skipping_transitions():
    """Test that skipping intermediate steps is strictly rejected."""
    # NEW directly to RESOLVED
    assert validate_transition(ThreatStatusEnum.NEW, ThreatStatusEnum.RESOLVED) is False
    # NEW directly to DISPATCHED
    assert validate_transition(ThreatStatusEnum.NEW, ThreatStatusEnum.DISPATCHED) is False
    # NEW directly to INVESTIGATING
    assert validate_transition(ThreatStatusEnum.NEW, ThreatStatusEnum.INVESTIGATING) is False
    # ACKNOWLEDGED directly to RESOLVED
    assert validate_transition(ThreatStatusEnum.ACKNOWLEDGED, ThreatStatusEnum.RESOLVED) is False
    # ACKNOWLEDGED directly to DISPATCHED
    assert validate_transition(ThreatStatusEnum.ACKNOWLEDGED, ThreatStatusEnum.DISPATCHED) is False


def test_terminal_states_immutable():
    """Test that RESOLVED and FALSE_POSITIVE are terminal (no outbound transitions)."""
    for state in ThreatStatusEnum:
        assert validate_transition(ThreatStatusEnum.RESOLVED, state) is False
        assert validate_transition(ThreatStatusEnum.FALSE_POSITIVE, state) is False


def test_get_valid_transitions_helper():
    """Test get_valid_transitions returns correct list of string names."""
    new_next = get_valid_transitions(ThreatStatusEnum.NEW)
    assert set(new_next) == {"ACKNOWLEDGED", "FALSE_POSITIVE"}

    dispatched_next = get_valid_transitions(ThreatStatusEnum.DISPATCHED)
    assert dispatched_next == ["RESOLVED"]

    resolved_next = get_valid_transitions(ThreatStatusEnum.RESOLVED)
    assert resolved_next == []
