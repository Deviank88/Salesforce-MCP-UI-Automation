from __future__ import annotations

import pytest

from salesforce_mcp.guardrails import guard_dangerous_action, requires_confirmation


def test_requires_confirmation_detects_destructive_words() -> None:
    assert requires_confirmation("Delete data stream")
    assert requires_confirmation("elimina connessione")
    assert not requires_confirmation("Open Data Cloud setup")


def test_guard_blocks_dangerous_action_without_confirmation() -> None:
    with pytest.raises(ValueError, match="Potentially destructive action blocked"):
        guard_dangerous_action(False, "Delete")


def test_guard_allows_confirmed_dangerous_action_with_warning() -> None:
    warnings = guard_dangerous_action(True, "Delete")
    assert warnings == ["Dangerous action confirmation was explicitly provided."]
