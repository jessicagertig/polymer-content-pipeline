"""Loads upcoming blog posts from the editorial content calendar — a CSV in the repo.

config/blog-content-topics.csv is the blog plan: a header row (row 1) followed by
one row per planned post. Each row maps to a ContentOpportunity the publisher can
generate and stage, ordered by Publish Slot (Launch Batch first, then Week 1…N)
then Priority (P0→P1→P2).

Columns (row 1): Priority | Publish Slot | Suggested URL Slug | Main Keyword Topic |
Supporting Secondary Keywords | Suggested Blog Title | Volume (US/mo) |
Keyword Difficulty | SEO or AEO | Content Type | Includes Polymer |
Article Brief / Angle | Noteworthy Data to Support It | Hook | ICP Target
| Generated At (written back by the bot — see mark_generated)

Once a post is staged the bot writes an ISO timestamp into that row's 'Generated At'
column in the CSV; rows with a 'Generated At' value are skipped on the next load. The
CSV goes through lib.repo, so a Lambda run commits the change to GitHub.
"""

import csv
import io
import re
from datetime import datetime, timezone

from lib import repo
from lib.logging import get
from models.content import ContentOpportunity, PageType


log = get(__name__)

CALENDAR_REL = "config/blog-content-topics.csv"
CALENDAR_PATH = repo.ROOT / CALENDAR_REL
GENERATED_AT_HEADER = "Generated At"


# ── Content Type → PageType ───────────────────────────────────────────────────
# The sheet's Content Type is free text with ~30 variants; map by substring.
# Order matters: 'listicle' before 'comparison' so "Comparison listicle" → LISTICLE.
def _content_type_to_page_type(content_type: str, title: str) -> PageType:
    c = (content_type or "").lower()
    if "hub" in c:
        return PageType.HUB
    if "alternatives" in c:
        return PageType.ALTERNATIVES
    if "interview questions" in (title or "").lower():
        return PageType.INTERVIEW_QUESTION_GUIDE
    if "listicle" in c or "roundup" in c:
        return PageType.LISTICLE
    if "how-to" in c or "how to" in c or "step-by-step" in c or "step by step" in c or "process" in c:
        return PageType.GUIDE
    if "comparison" in c:
        return PageType.COMPARISON
    if "pov" in c:
        return PageType.GUIDE
    if c:
        return PageType.GUIDE
    # No Content Type given — fall back to the title heuristic.
    return _page_type_from_title(title)


def _page_type_from_title(title: str) -> PageType:
    t = (title or "").lower()
    if "interview questions" in t:
        return PageType.INTERVIEW_QUESTION_GUIDE
    if re.search(r"\bvs\.?\b", t):
        return PageType.COMPARISON
    if "how to" in t:
        return PageType.GUIDE
    if t.startswith("why "):
        return PageType.GUIDE
    if re.search(r"^\d+\b|\b(best|top|tools|examples|ways)\b", t):
        return PageType.LISTICLE
    return PageType.GUIDE


# ── Ordering ──────────────────────────────────────────────────────────────────
def _slot_sort_key(slot: str) -> int:
    s = (slot or "").lower()
    if "launch batch" in s:
        return 0
    m = re.search(r"week\s+(\d+)", s)
    if m:
        return int(m.group(1))
    return 9999  # unknown/blank slots go last


def _priority_sort_key(priority: str) -> int:
    m = re.search(r"(\d+)", priority or "")
    return int(m.group(1)) if m else 99


# ── CSV plumbing ──────────────────────────────────────────────────────────────
def _read_rows() -> list[list[str]]:
    """Every row of the calendar CSV, header first."""
    if not CALENDAR_PATH.exists():
        raise ValueError(f"Content calendar not found at {CALENDAR_PATH}")
    return [list(row) for row in csv.reader(io.StringIO(repo.read(CALENDAR_REL), newline=""))]


def _write_rows(rows: list[list[str]]) -> None:
    buf = io.StringIO(newline="")
    csv.writer(buf).writerows(rows)
    repo.stage(CALENDAR_REL, buf.getvalue())


# ── Public API ────────────────────────────────────────────────────────────────
def load_opportunities() -> list[ContentOpportunity]:
    """Returns planned posts as ContentOpportunities, ordered Publish Slot then
    Priority. Rows already marked with a 'Generated At' timestamp are skipped."""
    rows = _read_rows()
    if not rows:
        raise ValueError(f"Content calendar {CALENDAR_PATH} has no rows")

    hdr = [str(c).strip() if c else "" for c in rows[0]]
    idx = {h: i for i, h in enumerate(hdr)}
    gen_i = idx.get(GENERATED_AT_HEADER)

    def cell(row, name: str) -> str:
        i = idx.get(name)
        if i is None or i >= len(row) or row[i] is None:
            return ""
        return str(row[i]).strip()

    if "Suggested Blog Title" not in idx:
        raise ValueError(f"Content calendar missing 'Suggested Blog Title' column; headers={hdr}")

    # Pair each data row with its 1-based row number (header is row 1).
    numbered = [(i + 1, r) for i, r in enumerate(rows) if i > 0]
    numbered = [(n, r) for (n, r) in numbered if cell(r, "Suggested Blog Title")]
    numbered.sort(key=lambda nr: (
        _slot_sort_key(cell(nr[1], "Publish Slot")),
        _priority_sort_key(cell(nr[1], "Priority")),
    ))

    opps: list[ContentOpportunity] = []
    for calendar_row, r in numbered:
        # Skip rows already generated (their 'Generated At' cell is populated).
        if gen_i is not None and gen_i < len(r) and str(r[gen_i]).strip():
            continue

        title = cell(r, "Suggested Blog Title")
        slug = cell(r, "Suggested URL Slug").strip("/").split("/")[-1]
        if not slug:
            log.warning(f"Skipping calendar row {calendar_row} with no Suggested URL Slug: {title!r}")
            continue

        kws = [k.strip() for k in re.split(r"[;,]", cell(r, "Supporting Secondary Keywords")) if k.strip()]
        content_type = cell(r, "Content Type")
        rationale = " ".join(
            x for x in (
                cell(r, "Article Brief / Angle"),
                f"Hook: {cell(r, 'Hook')}" if cell(r, "Hook") else "",
                f"Data: {cell(r, 'Noteworthy Data to Support It')}" if cell(r, "Noteworthy Data to Support It") else "",
                f"ICP: {cell(r, 'ICP Target')}" if cell(r, "ICP Target") else "",
            ) if x
        ) or f"Planned blog post from the editorial calendar ({content_type or 'guide'})."

        opps.append(
            ContentOpportunity(
                id=slug,
                page_type=_content_type_to_page_type(content_type, title),
                keyword=cell(r, "Main Keyword Topic") or title,
                supporting_keywords=kws,
                monthly_volume=_to_int(cell(r, "Volume (US/mo)")),
                difficulty=_to_float(cell(r, "Keyword Difficulty")),
                proposed_url=f"/blog/{slug}",
                proposed_title=title,
                rationale=rationale,
                calendar_row=calendar_row,
                launch_batch=_slot_sort_key(cell(r, "Publish Slot")) == 0,
                includes_polymer=cell(r, "Includes Polymer").strip().lower() in ("yes", "y", "true", "1"),
                product_based=cell(r, "Product-based").strip().lower() in ("yes", "y", "true", "1"),
                resource_article=cell(r, "Resource article").strip().lower() in ("yes", "y", "true", "1"),
                hub_links=[u for u in re.split(r"[\s;,]+", cell(r, "Hub Links")) if u],
            )
        )

    log.info(f"Loaded {len(opps)} blog opportunities from {CALENDAR_PATH.name}")
    return opps


def planned_titles() -> dict[str, str]:
    """{"/blog/<slug>": Suggested Blog Title} for every calendar row, generated or not."""
    rows = _read_rows()
    slug_i, title_i = rows[0].index("Suggested URL Slug"), rows[0].index("Suggested Blog Title")
    return {f"/blog/{r[slug_i].strip('/').split('/')[-1]}": r[title_i] for r in rows[1:] if len(r) > max(slug_i, title_i)}


def mark_generated(row: int) -> None:
    """Marks a calendar row as generated: writes an ISO-8601 UTC timestamp into its
    'Generated At' cell in the CSV. Non-fatal — the post is already staged and the
    Sanity document check backstops a failed write, so errors are logged."""
    try:
        rows = _read_rows()
        header = rows[0]
        if GENERATED_AT_HEADER not in header:
            header.append(GENERATED_AT_HEADER)
        col = header.index(GENERATED_AT_HEADER)

        target = rows[row - 1]
        while len(target) <= col:
            target.append("")
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        target[col] = timestamp

        _write_rows(rows)
        log.info(f"Marked calendar row {row} as generated ({timestamp})")
    except Exception as e:
        log.warning(f"Failed to mark calendar row {row} as generated: {type(e).__name__}: {e}")


def last_generated() -> "datetime | None":
    """The latest 'Generated At' timestamp in the calendar, or None when no row has one."""
    rows = _read_rows()
    if GENERATED_AT_HEADER not in rows[0]:
        return None
    col = rows[0].index(GENERATED_AT_HEADER)
    stamps = [datetime.fromisoformat(r[col].strip()) for r in rows[1:] if len(r) > col and r[col].strip()]
    return max(stamps, default=None)


def _to_int(s: str) -> int:
    try:
        return int(re.sub(r"[^\d]", "", s) or 0)
    except ValueError:
        return 0


def _to_float(s: str) -> float:
    try:
        return float(re.sub(r"[^\d.]", "", s) or 0)
    except ValueError:
        return 0.0
