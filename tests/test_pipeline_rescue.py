import pipeline
import review_post
import rewrite_opening
import suggest_graphics


def test_a_step_that_fails_twice_is_skipped_and_the_post_goes_on(tmp_path, monkeypatch):
    calls, skipped = [], []
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)

    def ok(name):
        return lambda *a, **k: calls.append(name) or True

    def broken(*a, **k):
        calls.append("transition pass")
        raise RuntimeError("Response cut off")

    for name in ("check_post", "check_opening", "content_check", "em_dash_report", "hide_resources",
                 "resource_review", "restore_resources", "competitor_links"):
        monkeypatch.setattr(review_post, name, ok(name))
    monkeypatch.setattr(review_post, "transition_pass", broken)
    monkeypatch.setattr(rewrite_opening, "rewrite", ok("opening"))
    monkeypatch.setattr(suggest_graphics, "suggest", ok("graphics"))
    monkeypatch.setattr(pipeline, "recheck_saved", ok("recheck"))
    monkeypatch.setattr(pipeline, "_skip", lambda slug, step, error: skipped.append(step))

    done = pipeline.run_steps("post", lambda resuming: calls.append("write"))

    assert calls.count("transition pass") == 2
    assert skipped == ["transition pass"]
    assert done == list(pipeline.STEP_ORDER)
    assert "graphics" in calls
