"""Tests for pipeline.next_step and review_post.external_links."""
import json

from lib.repo import ROOT
from pipeline import next_step
from review_post import external_links


def test_next_step_is_the_first_unfinished_step():
    out = ROOT / "next-step-test-output"
    out.mkdir(exist_ok=True)
    try:
        (out / "next-step-test-steps.json").write_text(json.dumps(["write", "hide resources", "opening"]))
        assert next_step("next-step-test") == "opening check"
    finally:
        (out / "next-step-test-steps.json").unlink(missing_ok=True)
        out.rmdir()


def test_external_links_groups_by_website():
    html = '<a href="https://www.leonar.app/blog/x">a</a> <a href="https://www.polymer.co/blog/y">b</a> <a href="https://hrdive.com/z">c</a>'
    assert external_links(html) == {"leonar.app": ["https://www.leonar.app/blog/x"], "hrdive.com": ["https://hrdive.com/z"]}
