import pipeline
import review_post
import rewrite_opening
import suggest_graphics
from models.content import ContentOpportunity, ContentPage, PageType
from prompts.content import ALTERNATIVES_SYSTEM
from prompts.review import ALTERNATIVES_FIND_USER, ALTERNATIVES_FIX_USER, ALTERNATIVES_REVIEW_SYSTEM


def test_an_alternatives_article_skips_the_steps_its_playbook_replaces(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    (tmp_path / "post-output").mkdir()
    opp = ContentOpportunity(id="post", page_type=PageType.ALTERNATIVES, keyword="ashby alternatives",
                             proposed_url="/blog/post", proposed_title="Best Ashby Alternatives in 2026", rationale="r")
    (tmp_path / "post-output" / "post.json").write_text(ContentPage(opportunity=opp).model_dump_json())

    def ok(name):
        return lambda *a, **k: calls.append(name) or True

    for name in ("check_post", "check_opening", "content_check", "transition_pass", "em_dash_report", "hide_resources",
                 "resource_review", "restore_resources", "competitor_links"):
        monkeypatch.setattr(review_post, name, ok(name))
    monkeypatch.setattr(rewrite_opening, "rewrite", ok("opening"))
    monkeypatch.setattr(suggest_graphics, "suggest", ok("graphics"))
    monkeypatch.setattr(pipeline, "recheck_saved", ok("recheck"))

    done = pipeline.run_steps("post", lambda resuming: None)

    assert not {"opening", "check_opening", "content_check", "transition_pass"} & set(calls)
    assert "check_post" in calls and "graphics" in calls
    assert done.count("transition pass") == 1 and set(done) == set(pipeline.STEP_ORDER)


def test_the_alternatives_prompts_carry_only_the_house_rules_and_the_elements_of_style():
    for prompt in (ALTERNATIVES_SYSTEM, ALTERNATIVES_REVIEW_SYSTEM, ALTERNATIVES_FIND_USER, ALTERNATIVES_FIX_USER):
        assert "Numbers and statistics" not in prompt and "transition rule" not in prompt and "<<LOGIC>>" not in prompt
    assert "1. Colons are only allowed" in ALTERNATIVES_SYSTEM and "**Opening:**" not in ALTERNATIVES_SYSTEM
