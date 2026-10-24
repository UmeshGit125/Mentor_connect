# ruff: noqa: E501
"""Placeholder for tests against the live Claude implementation. Skipped unless RUN_LIVE_AI=1."""
import pytest


@pytest.mark.live_ai
def test_live_ai_placeholder():
    pass
