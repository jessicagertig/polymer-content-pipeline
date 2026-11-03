"""HTML → Portable Text self-check. Stdlib only; runs with plain python or pytest."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import portable_text  # noqa: E402


HTML = """
<p>Direct answer with <strong>bold</strong> and a <a href="/blog/ats-guide">link</a>.</p>
<h2>Why it matters</h2>
<p>Line one.<br>Line two.</p>
<ul>
  <li>First <em>item</em></li>
  <li><p>Second item</p></li>
</ul>
<ol><li>Step one</li><li>Step two</li></ol>
<table>
  <tr><th>Feature</th><th>Polymer</th></tr>
  <tr><td>Price</td><td>$<strong>0</strong></td></tr>
</table>
<blockquote><p>A <strong>quote</strong>.</p></blockquote>
<h3>Sub heading</h3>
<script>alert(1)</script>
"""


def test_blocks():
    blocks = portable_text.from_html(HTML)
    types = [(b["_type"], b.get("style"), b.get("listItem")) for b in blocks]
    assert types == [
        ("block", "normal", None),
        ("block", "h2", None),
        ("block", "normal", None),
        ("block", "normal", "bullet"),
        ("block", "normal", "bullet"),
        ("block", "normal", "number"),
        ("block", "normal", "number"),
        ("table", None, None),
        ("quote", None, None),
        ("block", "h3", None),
    ], types

    first = blocks[0]
    assert [c["text"] for c in first["children"]] == ["Direct answer with ", "bold", " and a ", "link", "."]
    assert first["children"][1]["marks"] == ["strong"]
    link_key = first["children"][3]["marks"][0]
    assert first["markDefs"] == [{"_key": link_key, "_type": "link", "href": "/blog/ats-guide"}]

    assert blocks[2]["children"][0]["text"] == "Line one.\nLine two."
    assert blocks[3]["children"][1] == {**blocks[3]["children"][1], "text": "item", "marks": ["em"]}
    assert blocks[4]["children"][0]["text"] == "Second item"

    table = blocks[7]
    assert [r["cells"] for r in table["rows"]] == [["Feature", "Polymer"], ["Price", "$0"]]
    assert all(r["_type"] == "tableRow" for r in table["rows"])

    quote = blocks[8]
    assert [(c["text"], c["marks"]) for c in quote["text"][0]["children"]] == [("A ", []), ("quote", ["strong"]), (".", [])]

    for b in blocks:
        assert b["_key"]
        for child in b.get("children", []):
            assert child["_key"] and child["_type"] == "span"


def test_faq_blocks():
    blocks = portable_text.faq_blocks([{"q": "Is it free?", "a": "Yes."}])
    assert [(b["style"], b["children"][0]["text"]) for b in blocks] == [
        ("h2", "Frequently asked questions"),
        ("h3", "Is it free?"),
        ("normal", "Yes."),
    ]
    assert portable_text.faq_blocks([]) == []


if __name__ == "__main__":
    test_blocks()
    test_faq_blocks()
    print("ok")


def test_underline_strike_and_code_are_kept():
    b = portable_text.from_html("<p><u>U</u> <s>S</s> <code>C</code></p>")[0]
    assert [(c["text"], c["marks"]) for c in b["children"] if c["marks"]] == [("U", ["underline"]), ("S", ["strike-through"]), ("C", ["code"])]


def test_faq_answer_paragraphs_are_separate_blocks():
    blocks = portable_text.faq_blocks([{"q": "Q?", "a": "One.\n\nTwo."}])
    assert [(b["style"], b["children"][0]["text"]) for b in blocks] == [("h2", "Frequently asked questions"), ("h3", "Q?"), ("normal", "One."), ("normal", "Two.")]
