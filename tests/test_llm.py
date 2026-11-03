"""Tests for the model call retries in lib/llm.py."""
import httpx
import pytest

from lib import llm


def test_a_dropped_connection_is_retried(monkeypatch):
    monkeypatch.setattr(llm, "RETRY_WAITS", (0, 0, 0))
    calls = []

    def call():
        calls.append(1)
        if len(calls) < 3:
            raise httpx.RemoteProtocolError("peer closed connection without sending complete message body")
        return "ok"

    assert llm._with_retries(call, "test") == "ok" and len(calls) == 3


def test_other_errors_are_not_retried(monkeypatch):
    monkeypatch.setattr(llm, "RETRY_WAITS", (0, 0, 0))
    calls = []

    def call():
        calls.append(1)
        raise ValueError("bad input")

    with pytest.raises(ValueError):
        llm._with_retries(call, "test")
    assert len(calls) == 1
