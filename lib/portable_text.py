"""HTML → Portable Text for the blogPost `content` field (studio/schemas/blogPost.js).

Handles what the writer emits: <h2>/<h3>/<h4>/<p>, <ul>/<ol>/<li>, <table>,
<blockquote>, <strong>/<em>/<u>/<s>/<code>, <a href>, <br>. Table cells are flattened to plain text,
which is what the table object accepts. Quotes keep bold, italics, links, and lists.
"""

import re
import uuid
from html.parser import HTMLParser


def _key() -> str:
    return uuid.uuid4().hex[:12]


_BLOCK_STYLES = {"h2": "h2", "h3": "h3", "h4": "h4", "p": "normal"}
_LIST_TAGS = {"ul": "bullet", "ol": "number"}
_INLINE_MARKS = {"strong": "strong", "b": "strong", "em": "em", "i": "em", "u": "underline",
                 "s": "strike-through", "del": "strike-through", "strike": "strike-through", "code": "code"}
_SKIP_TAGS = {"h1", "script", "style", "img"}


def block(text: str, style: str = "normal") -> dict:
    """One plain-text block — used for the FAQ section appended after the body."""
    return {
        "_key": _key(),
        "_type": "block",
        "style": style,
        "markDefs": [],
        "children": [{"_key": _key(), "_type": "span", "marks": [], "text": text}],
    }


def toc_block() -> dict:
    """The table of contents. The site builds its list from the post's H2s."""
    return {"_key": _key(), "_type": "toc", "heading": "Table of contents"}


def faq_blocks(faq_items: list[dict]) -> list[dict]:
    """The FAQ as the H2 + H3/paragraph pairs web/pages/blog/[slug].js detects for the
    accordion and the FAQPage schema. Each paragraph of an answer is its own block."""
    if not faq_items:
        return []
    blocks = [block("Frequently asked questions", "h2")]
    for item in faq_items:
        blocks.append(block(item["q"], "h3"))
        blocks.extend(block(p) for p in item["a"].split("\n\n") if p.strip())
    return blocks


def from_html(html: str) -> list[dict]:
    converter = _Converter()
    converter.feed(html)
    converter.close()
    converter._close_block()
    return converter.blocks


class _Converter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self.block: dict | None = None
        self.marks: list[str] = []
        self.mark_defs: list[dict] = []
        self.lists: list[str] = []
        self.table: dict | None = None
        self.row: dict | None = None
        self.cell: list[str] | None = None
        self.quote: list[dict] | None = None
        self.skip_depth = 0

    # ── blocks ──────────────────────────────────────────────────────────────
    def _open_block(self, style: str = "normal", list_item: str | None = None) -> None:
        self._close_block()
        self.block = {"_key": _key(), "_type": "block", "style": style, "markDefs": [], "children": []}
        if list_item:
            self.block["listItem"] = list_item
            self.block["level"] = max(1, len(self.lists))

    def _close_block(self) -> None:
        if self.block is None:
            return
        children = [c for c in self.block["children"] if c["text"]]
        if children:
            children[0]["text"] = children[0]["text"].lstrip()
            children[-1]["text"] = children[-1]["text"].rstrip()
            children = [c for c in children if c["text"]]
        if children:
            used = {m for c in children for m in c["marks"]}
            self.block["children"] = children
            self.block["markDefs"] = [d for d in self.mark_defs if d["_key"] in used]
            target = self.quote if self.quote is not None else self.blocks
            target.append(self.block)
        self.block = None
        self.mark_defs = []

    def _span(self, text: str) -> None:
        if self.block is None:
            self._open_block()
        children = self.block["children"]
        marks = list(self.marks)
        if children and children[-1]["marks"] == marks:
            children[-1]["text"] += text
        else:
            children.append({"_key": _key(), "_type": "span", "marks": marks, "text": text})

    # ── parser callbacks ────────────────────────────────────────────────────
    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in _SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in _BLOCK_STYLES:
            # A <p> inside <li> continues the list item's block.
            if tag == "p" and self.block is not None and "listItem" in self.block:
                return
            self._open_block(_BLOCK_STYLES[tag])
        elif tag in _LIST_TAGS:
            self._close_block()
            self.lists.append(_LIST_TAGS[tag])
        elif tag == "li":
            self._open_block("normal", list_item=self.lists[-1] if self.lists else "bullet")
        elif tag in _INLINE_MARKS:
            self.marks.append(_INLINE_MARKS[tag])
        elif tag == "a":
            href = dict(attrs).get("href", "")
            key = _key()
            self.mark_defs.append({"_key": key, "_type": "link", "href": href})
            self.marks.append(key)
        elif tag == "br":
            if self.block is not None:
                self._span("\n")
        elif tag == "table":
            self._close_block()
            self.table = {"_key": _key(), "_type": "table", "rows": []}
        elif tag == "tr":
            self.row = {"_key": _key(), "_type": "tableRow", "cells": []}
        elif tag in ("td", "th"):
            self.cell = []
        elif tag == "blockquote":
            self._close_block()
            self.quote = []

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in _BLOCK_STYLES:
            if tag == "p" and self.block is not None and "listItem" in self.block:
                return
            self._close_block()
        elif tag == "li":
            self._close_block()
        elif tag in _LIST_TAGS:
            self._close_block()
            if self.lists:
                self.lists.pop()
        elif tag in _INLINE_MARKS:
            self._pop_mark(_INLINE_MARKS[tag])
        elif tag == "a":
            link_keys = {d["_key"] for d in self.mark_defs}
            for i in range(len(self.marks) - 1, -1, -1):
                if self.marks[i] in link_keys:
                    del self.marks[i]
                    break
        elif tag in ("td", "th"):
            if self.row is not None and self.cell is not None:
                self.row["cells"].append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.cell = None
        elif tag == "tr":
            if self.table is not None and self.row is not None and any(self.row["cells"]):
                self.table["rows"].append(self.row)
            self.row = None
        elif tag == "table":
            if self.table is not None and self.table["rows"]:
                self.blocks.append(self.table)
            self.table = None
        elif tag == "blockquote":
            self._close_block()
            quote_blocks = self.quote or []
            self.quote = None
            for b in quote_blocks:
                b["style"] = "normal"
            if quote_blocks:
                self.blocks.append({"_key": _key(), "_type": "quote", "text": quote_blocks})

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.cell is not None:
            self.cell.append(data)
            return
        text = re.sub(r"[ \t\r\n]+", " ", data)
        if self.block is None and not text.strip():
            return
        self._span(text)

    def _pop_mark(self, mark: str) -> None:
        for i in range(len(self.marks) - 1, -1, -1):
            if self.marks[i] == mark:
                del self.marks[i]
                return
