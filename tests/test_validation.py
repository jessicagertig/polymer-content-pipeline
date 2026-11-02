"""Internal-link handling self-check. Stdlib only; runs with plain python or pytest."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.validation import fix_internal_links, site_path, validate  # noqa: E402
from models.content import GeneratedContent  # noqa: E402


PAGES = {"/blog/ats-guide", "/pricing"}


def test_site_path():
    assert site_path("/blog/ats-guide/") == "/blog/ats-guide"
    assert site_path("https://www.polymer.co/pricing#plans") == "/pricing"
    assert site_path("https://polymer.co/") == "/"
    assert site_path("https://example.com/x") is None
    assert site_path("mailto:hi@polymer.co") is None


def test_fix_internal_links():
    html = (
        '<p>See <a href="/blog/ats-guide">the guide</a>, '
        '<a href="https://www.polymer.co/pricing/">pricing</a>, '
        '<a href="/blog/made-up">a made-up page</a> and '
        '<a href="https://shrm.org/x">SHRM</a>.</p>'
        '<table><tr><td><a href="/pricing">plans</a></td></tr></table>'
    )
    body, placed, todos = fix_internal_links(html, PAGES)
    assert '<a href="/blog/made-up">' not in body and "a made-up page" in body
    assert '<a href="https://shrm.org/x">' in body
    assert placed == ["/blog/ats-guide", "/pricing", "/pricing"]
    assert len(todos) == 2 and "made-up" in todos[0] and "table" in todos[1]


def test_validate_todos_do_not_fail_the_post():
    content = GeneratedContent(
        title="t", h1="h", meta_description="m", slug="s",
        body_html="<h2>x</h2>" + "<p>word</p>" * 2600, word_count=2600,
        internal_links=[{"text": "guide", "url": "/blog/ats-guide"}, {"text": "nope", "url": "/blog/nope"}],
    )
    result = validate(content, existing_urls=PAGES, placed_paths=["/pricing"])
    assert result.ok
    assert len(result.todos) == 3   # too few placed; ats-guide listed but not placed; nope not a page


if __name__ == "__main__":
    test_site_path()
    test_fix_internal_links()
    test_validate_todos_do_not_fail_the_post()
    print("ok")
