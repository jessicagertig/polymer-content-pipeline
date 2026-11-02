"""Lightweight text utilities."""

import re
import math


def strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def word_count(html: str) -> int:
    text = strip_html(html)
    return len([w for w in re.split(r"\s+", text) if w])


def reading_time(html: str, wpm: int = 200) -> int:
    return max(1, math.ceil(word_count(html) / wpm))


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


# "Empty" inline filler an LLM sometimes leaves inside a list scaffold it forgot to fill.
_EMPTY_INLINE = r"(?:\s|&nbsp;|<br\s*/?>)*"


def clean_body_html(html: str) -> tuple[str, int]:
    """
    Repairs common LLM HTML artifacts that render as large blank gaps in Webflow:
      - empty list items: <li> &nbsp; <br> </li>
      - empty lists:       <ul> &nbsp; </ul> / <ol></ol>
      - empty paragraphs:  <p> &nbsp; </p>
      - runs of stray <br>

    Returns (cleaned_html, artifacts_removed). A non-zero count signals a low-quality
    generation worth regenerating.
    """
    removed = 0

    # Drop empty list items
    html, n = re.subn(rf"<li>{_EMPTY_INLINE}</li>", "", html, flags=re.I)
    removed += n

    # Drop lists that have no real <li> left (only whitespace/nbsp/br between tags)
    html, n = re.subn(rf"<(ul|ol)>{_EMPTY_INLINE}</\1>", "", html, flags=re.I)
    removed += n

    # Drop empty paragraphs
    html, n = re.subn(rf"<p>{_EMPTY_INLINE}</p>", "", html, flags=re.I)
    removed += n

    # Collapse 2+ consecutive <br> into nothing (they were spacing hacks)
    html = re.sub(r"(?:<br\s*/?>\s*){2,}", "", html, flags=re.I)

    return html, removed


def lists_to_paragraphs(html: str) -> str:
    """
    Converts <ul>/<ol> lists into bullet/numbered <p> paragraphs.

    Webflow's CMS RichText *editor* (the Designer) re-parses injected HTML and
    silently empties <ul><li> structures it didn't author — leaving big blank gaps.
    Paragraphs are the one element it always keeps, so we render list items as
    "• item" / "1. item" paragraphs instead. Runs innermost-first so nested lists
    flatten cleanly.
    """
    def conv_ul(m):
        items = [it.strip() for it in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]
        return "".join(f"<p>• {it}</p>" for it in items if it)

    def conv_ol(m):
        items = [it.strip() for it in re.findall(r"<li>(.*?)</li>", m.group(1), re.S) if it.strip()]
        return "".join(f"<p>{i + 1}. {it}</p>" for i, it in enumerate(items))

    prev = None
    while prev != html:
        prev = html
        html = re.sub(r"<ul>(.*?)</ul>", conv_ul, html, flags=re.S | re.I)
        html = re.sub(r"<ol>(.*?)</ol>", conv_ol, html, flags=re.S | re.I)
    return html


def tables_to_paragraphs(html: str) -> str:
    """
    Converts <table> into Designer-safe paragraphs. Webflow's RichText editor strips
    table structure on edit, collapsing all cells into one run-on line. We instead
    render each data row as "**RowLabel** — Header2: cell2; Header3: cell3", which
    keeps the comparison readable and survives the editor.
    """
    def _cell_text(cell: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", cell)).strip()

    def conv(m):
        table = m.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S | re.I)
        parsed = []
        for r in rows:
            cells = [_cell_text(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S | re.I)]
            if any(cells):
                parsed.append(cells)
        if not parsed:
            return ""

        header_row = bool(re.search(r"<th", rows[0], re.I)) if rows else False
        headers = parsed[0] if (header_row or len(parsed) > 1) else None
        body = parsed[1:] if headers else parsed

        out = []
        for cells in body:
            label = cells[0] if cells else ""
            pairs = []
            for i in range(1, len(cells)):
                h = headers[i] if headers and i < len(headers) else ""
                pairs.append(f"{h}: {cells[i]}" if h else cells[i])
            line = f"<p><strong>{label}</strong>" + (" — " + "; ".join(pairs) if pairs else "") + "</p>"
            out.append(line)
        return "".join(out)

    return re.sub(r"<table.*?</table>", conv, html, flags=re.S | re.I)


# Inline styles so the table looks like a real grid even without the blog template's
# table CSS. Wrapped in a Webflow HTML-embed (class "w-embed") which the Designer
# treats as opaque custom code — so the table renders as a grid AND survives editing.
_TABLE_STYLE = "width:100%;border-collapse:collapse;margin:1.25em 0;font-size:0.95em"
_TD_STYLE = "border:1px solid #e3e3e3;padding:10px 12px;text-align:left;vertical-align:top"
_TH_STYLE = _TD_STYLE + ";background:#f6f6f6;font-weight:600"


def tables_to_embeds(html: str) -> str:
    """Render <table> as a styled real table wrapped in a Webflow HTML-embed.

    Unlike tables_to_paragraphs (which flattens to text), this keeps a genuine
    grid. The w-embed wrapper makes Webflow's RichText editor treat the markup as
    custom code and leave it intact, so the table both displays as a grid and
    survives a Designer edit.
    """
    def _cell_text(cell: str) -> str:
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", cell)).strip()
        return (
            text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )

    def conv(m):
        table = m.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S | re.I)
        parsed = []  # (is_header_row, [cells])
        for r in rows:
            cells = re.findall(r"<(t[hd])[^>]*>(.*?)</t[hd]>", r, re.S | re.I)
            texts = [_cell_text(c) for _tag, c in cells]
            if any(texts):
                header = bool(cells) and cells[0][0].lower() == "th"
                parsed.append((header, texts))
        if not parsed:
            return ""

        # Treat the first row as a header even if the model used <td> for it.
        first_is_header = parsed[0][0] or len(parsed) > 1

        out = [f'<div class="w-embed"><table style="{_TABLE_STYLE}">']
        for i, (_hdr, texts) in enumerate(parsed):
            tag, style = ("th", _TH_STYLE) if (i == 0 and first_is_header) else ("td", _TD_STYLE)
            cells_html = "".join(f'<{tag} style="{style}">{t}</{tag}>' for t in texts)
            out.append(f"<tr>{cells_html}</tr>")
        out.append("</table></div>")
        return "".join(out)

    return re.sub(r"<table.*?</table>", conv, html, flags=re.S | re.I)


def space_before_headings(html: str) -> str:
    """Inserts a blank spacer paragraph before each <h2> for extra breathing room.
    Uses <p>&nbsp;</p> (not <br>) because Webflow's RichText editor reliably keeps
    paragraphs but normalizes away bare <br> between blocks."""
    return re.sub(r"(<h2\b)", r"<p>&nbsp;</p>\1", html, flags=re.I)


def space_em_dashes(text: str) -> str:
    """One space before and one after every em dash (house rule 5)."""
    return re.sub(r"[ \t\u00a0]*\u2014[ \t\u00a0]*", " \u2014 ", text)


def has_empty_lists(html: str) -> bool:
    """True if the body still has an empty list item or empty list (pre-clean signal)."""
    return bool(
        re.search(rf"<li>{_EMPTY_INLINE}</li>", html, flags=re.I)
        or re.search(rf"<(ul|ol)>{_EMPTY_INLINE}</\1>", html, flags=re.I)
    )
