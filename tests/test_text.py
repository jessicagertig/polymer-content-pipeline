"""Tests for lib/text.py and the FAQ parser."""
from lib.text import clean_body_html


def test_two_line_breaks_become_one():
    assert clean_body_html("<p>Best,<br><br>[Your Name]</p>")[0] == "<p>Best,<br>[Your Name]</p>"


def test_faq_answer_keeps_paragraphs_and_punctuation():
    from agents.content_generator import faq_items_from_html
    items = faq_items_from_html("<h3>Q?</h3><p>See <a href='x'>this</a>.</p><ul><li>One</li><li>Two</li></ul>")
    assert items == [{"q": "Q?", "a": "See this.\n\nOne\n\nTwo"}]
