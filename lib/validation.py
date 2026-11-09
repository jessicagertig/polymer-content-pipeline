"""Content quality validation — runs before staging.

Internal-link problems never fail a post. The body is fixed where Python can fix it
(a link to a page that is not on the site is removed, its text kept) and everything
else becomes a to-do for the follow-up run that adds Polymer references and links.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from config.settings import settings
from models.content import GeneratedContent


@dataclass
class ValidationResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)   # for the follow-up run; never fail the post


# Constraints
FLOOR_WORD_COUNT = 2000    # body, FAQ excluded; under this fails the post
MIN_WORD_COUNT = 2500      # body, FAQ excluded; under this the writer expands the article once, and a post still under it gets a to-do
REPORT_WORD_COUNT = 6000   # over this is reported as a to-do, never failed
MAX_META_DESCRIPTION = 160
MAX_TITLE_LENGTH = 65
MIN_FAQ_ITEMS = 3
MIN_INTERNAL_LINKS = 2

_ANCHOR = re.compile(r'<a\b[^>]*\bhref="([^"]*)"[^>]*>(.*?)</a>', re.S | re.I)
_FLATTENED = re.compile(r"<table\b.*?</table>", re.S | re.I)   # lib.portable_text drops links inside tables


def site_path(href: str) -> Optional[str]:
    """The site path for an internal href ("/blog/x", "https://www.polymer.co/blog/x/",
    "/blog/x#faq"), normalized to the sitemap's form; None for an external or relative link."""
    parts = urlparse(href.strip())
    domains = {settings.site_domain.lower(), settings.site_domain.lower().removeprefix("www.")}
    if parts.netloc and parts.netloc.lower() not in domains:
        return None
    if not parts.netloc and not parts.path.startswith("/"):
        return None
    return parts.path.rstrip("/") or "/"


def fix_internal_links(body_html: str, existing_urls: set) -> tuple[str, list[str], list[str]]:
    """Finds the internal links in the body. No link is removed.
    Returns (body_html, site paths placed in the body, to-do items)."""
    placed: list[str] = []
    todos: list[str] = []
    flattened = [m.span() for m in _FLATTENED.finditer(body_html)]

    def fix(m: re.Match) -> str:
        href, text = m.group(1), m.group(2)
        path = site_path(href)
        if path is None:
            return m.group(0)
        placed.append(path)
        if any(a <= m.start() < b for a, b in flattened):
            todos.append(f"Link to {path} is inside a table and will not render; move it into a paragraph.")
        return m.group(0)

    return _ANCHOR.sub(fix, body_html), placed, todos


def _plain(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def validate(
    content: GeneratedContent,
    existing_urls: Optional[set] = None,
    placed_paths: Optional[list[str]] = None,
    hub_links: Optional[list[str]] = None,
) -> ValidationResult:
    """Validates generated content. Returns ok=False if any hard requirement fails.
    placed_paths: the site paths fix_internal_links found in the body.
    hub_links: a hub's article URLs, each of which must be linked in the body."""
    result = ValidationResult()
    existing_urls = existing_urls or set()

    # Title length
    if len(content.title) > MAX_TITLE_LENGTH:
        result.warnings.append(
            f"Title is {len(content.title)} chars; Google truncates around {MAX_TITLE_LENGTH}"
        )
    if not content.title.strip():
        result.errors.append("Title is empty")

    # Meta description
    if len(content.meta_description) > MAX_META_DESCRIPTION:
        result.warnings.append(
            f"Meta description is {len(content.meta_description)} chars; aim for {MAX_META_DESCRIPTION}"
        )
    if not content.meta_description.strip():
        result.errors.append("Meta description is empty")

    # Word count
    if content.word_count < FLOOR_WORD_COUNT:
        result.errors.append(
            f"Word count {content.word_count} below the floor of {FLOOR_WORD_COUNT}"
        )
    elif content.word_count < MIN_WORD_COUNT:
        result.todos.append(f"Body is {content.word_count} words, under the {MIN_WORD_COUNT} minimum.")
    if content.word_count > REPORT_WORD_COUNT:
        result.todos.append(f"Body is {content.word_count} words, over {REPORT_WORD_COUNT}.")

    # Body must have semantic structure
    body = content.body_html.lower()
    if "<h2" not in body:
        result.errors.append("Body has no <h2> headings — bad for SEO + AEO")

    # Empty list scaffolds render as large blank gaps
    from lib.text import has_empty_lists
    if has_empty_lists(content.body_html):
        result.errors.append("Body contains empty list items/lists (malformed generation)")

    # Slug
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", content.slug):
        result.errors.append(f"Slug '{content.slug}' must be kebab-case lowercase")

    # FAQ items
    if len(content.faq_items) < MIN_FAQ_ITEMS:
        result.warnings.append(
            f"Only {len(content.faq_items)} FAQ items; aim for at least {MIN_FAQ_ITEMS}"
        )

    # Internal links — shortfalls go to the to-do list; the post is not failed
    placed = set(placed_paths or [])
    if len(placed) < MIN_INTERNAL_LINKS:
        result.todos.append(
            f"Only {len(placed)} internal link(s) in the body; add at least {MIN_INTERNAL_LINKS - len(placed)} more."
        )
    for link in content.internal_links:
        url, text = link.get("url", ""), link.get("text", "")
        path = site_path(url)
        if path is None or path not in existing_urls:
            result.todos.append(f"Listed link to {url} is not a page on the site; ignore it or find the right page.")
        elif path not in placed:
            result.todos.append(f"Add a link to {path} ('{text}'): listed but not placed in the body.")
    for url in hub_links or []:
        path = site_path(url)
        if path not in existing_urls:
            result.todos.append(f"Add a link to {url} once it is published.")
        elif path not in placed:
            result.todos.append(f"Add a link to {url}: a hub article not linked in the body.")

    if result.errors:
        result.ok = False

    return result
