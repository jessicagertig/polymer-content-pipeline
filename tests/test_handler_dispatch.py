"""Tests for the handler.py dispatch table."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "lambdas" / "slack_handler"))
from handler import dispatch_for


def test_resume_routes_to_content_engine():
    result = dispatch_for("resume_interview-guide", "interview-guide")
    assert result == ("content-engine.yml", {"command": "resume", "slug": "interview-guide"})


def test_unknown_prefix_returns_none():
    assert dispatch_for("nonsense_foo", "foo") is None
    assert dispatch_for("", "") is None


def test_redraft_is_not_in_dispatch_table():
    # redraft_ is intercepted in handle_slack_interact (opens a modal)
    # rather than dispatched to a workflow. Sanity check the table doesn't claim it.
    assert dispatch_for("redraft_interview-guide", "interview-guide") is None
