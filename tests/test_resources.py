"""Tests for lib/resources.py: hide, show, unwrap."""
from lib.resources import hide, show, unwrap, inner, placeholder


def test_hide_show_unwrap():
    body = '<p>Intro</p><h2>A</h2><p>a</p><div class="resource"><p>T1</p></div><h2>B</h2><div class="resource"><table><tr><td>R</td></tr></table></div><p>b</p>'
    masked, rs = hide(body)
    assert masked == '<p>Intro</p><h2>A</h2><p>a</p><div data-resource="1"></div><h2>B</h2><div data-resource="2"></div><p>b</p>'
    assert [r["section"] for r in rs] == ["A", "B"]
    assert show(masked, rs) == (body, [])
    shown, missing = show(masked.replace(placeholder(1), ""), rs)
    assert missing == [1] and shown.index("T1") < shown.index("<h2>B</h2>")
    assert unwrap(body) == '<p>Intro</p><h2>A</h2><p>a</p><p>T1</p><h2>B</h2><table><tr><td>R</td></tr></table><p>b</p>'
    assert inner(rs[0]["html"]) == "<p>T1</p>"
