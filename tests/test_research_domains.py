"""The definitions and statistics searches are limited to the approved sources."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agents.research as research  # noqa: E402
from models.content import ContentOpportunity, PageType  # noqa: E402


def test_definitions_and_statistics_use_approved_sources_only(monkeypatch):
    calls = []
    monkeypatch.setattr(research, "research_call", lambda **k: calls.append(k) or {"text": "x", "searches": 1})
    monkeypatch.setattr(research, "_polymer_articles", lambda opp: "")
    opp = ContentOpportunity(id="t", page_type=PageType.GUIDE, keyword="interview", proposed_url="/blog/t",
                             proposed_title="T", rationale="r")
    research._three_step_brief(opp, "structure")
    limited = [bool(c["allowed_domains"]) for c in calls]
    assert limited == [True, False, True]   # definitions, best practices, statistics
