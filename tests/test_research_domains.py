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


def test_a_product_article_researches_products_on_their_own_sites_then_statistics(monkeypatch):
    calls = []
    monkeypatch.setattr(research, "research_call", lambda **k: calls.append(k) or {"text": "x", "searches": 1, "stop": "end_turn"})
    monkeypatch.setattr(research, "_polymer_articles", lambda opp: "")
    opp = ContentOpportunity(id="t", page_type=PageType.GUIDE, keyword="ats cost", proposed_url="/blog/t",
                             proposed_title="T", rationale="r", product_based=True)
    research._three_step_brief(opp, "structure")
    assert len(calls) == 2
    assert "research only products" in calls[0]["user"] and calls[0]["blocked_domains"] is None and not calls[0]["allowed_domains"]
    assert "research only statistics" in calls[1]["user"] and calls[1]["allowed_domains"]


def test_a_research_step_cut_off_at_its_token_limit_stops_the_article(monkeypatch):
    monkeypatch.setattr(research, "research_call", lambda **k: {"text": "x", "searches": 1, "stop": "max_tokens"})
    opp = ContentOpportunity(id="t", page_type=PageType.GUIDE, keyword="ats cost", proposed_url="/blog/t",
                             proposed_title="T", rationale="r", product_based=True)
    try:
        research._three_step_brief(opp, "structure")
    except RuntimeError as e:
        assert "cut off" in str(e)
    else:
        raise AssertionError("a cut-off step did not stop the article")
