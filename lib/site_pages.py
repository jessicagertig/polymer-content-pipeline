"""The site's live URL list, read from its sitemap — link targets and indexing candidates.

web/pages/sitemap.xml.js lists every content page and every published blog post; posts
carry <lastmod> (updatedDate, else Sanity's _updatedAt).
"""

import re
import urllib.request
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional
from urllib.parse import urlparse

from config.settings import settings


@lru_cache(maxsize=1)
def sitemap_entries() -> list[dict]:
    """Every <url> in the sitemap as {"url": "/path", "lastmod": "<as written, or ''>"}. sitemap.xml is a
    sitemap index (wrk-marketing web/pages/sitemap.xml.js), so every sitemap it lists is read."""
    def fetch(url: str) -> str:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode("utf-8")
    xml = fetch(f"https://{settings.site_domain}/sitemap.xml")
    if "<sitemapindex" in xml:
        xml = "".join(fetch(loc.strip()) for loc in re.findall(r"<sitemap>\s*<loc>(.*?)</loc>", xml, flags=re.S))
    entries = []
    for url_xml in re.findall(r"<url>(.*?)</url>", xml, flags=re.S):
        loc = re.search(r"<loc>(.*?)</loc>", url_xml)
        lastmod = re.search(r"<lastmod>(.*?)</lastmod>", url_xml)
        if loc:
            entries.append({
                "url": urlparse(loc.group(1).strip()).path.rstrip("/") or "/",
                "lastmod": lastmod.group(1).strip() if lastmod else "",
            })
    return entries


NOT_IN_SITEMAP = ["/free-trial"]   # real pages kept out of the sitemap so they are not indexed, but valid links


def existing_pages() -> list[dict]:
    """[{"url": "/path"}, …] — the pool of valid internal-link targets: the sitemap, plus NOT_IN_SITEMAP."""
    return [{"url": entry["url"]} for entry in sitemap_entries()] + [{"url": url} for url in NOT_IN_SITEMAP]


def blog_articles() -> list[dict]:
    """[{"url": "/blog/slug", "title": "…"}, …] — the published blog articles, the writer's list for
    internal links. The URLs come from the sitemap, the titles from Sanity."""
    from connectors import sanity
    found = sanity.query('*[_type == "blogPost" && !(_id in path("drafts.**"))]{"slug": slug.current, "title": editorialTitle}')
    titles = {d["slug"]: d["title"] for d in found.get("result", [])}
    return [{"url": e["url"], "title": titles.get(e["url"].removeprefix("/blog/"), "")}
            for e in sitemap_entries() if e["url"].startswith("/blog/")]


def recently_updated(hours: int) -> list[dict]:
    """Entries whose <lastmod> falls within the last `hours`."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return [e for e in sitemap_entries() if (when := _parse_lastmod(e["lastmod"])) and when >= cutoff]


def _parse_lastmod(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
