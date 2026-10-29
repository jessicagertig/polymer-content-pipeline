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
    """Every <url> in the sitemap as {"url": "/path", "lastmod": "<as written, or ''>"}."""
    with urllib.request.urlopen(f"https://{settings.site_domain}/sitemap.xml", timeout=30) as response:
        xml = response.read().decode("utf-8")
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


def existing_pages() -> list[dict]:
    """[{"url": "/path"}, …] — the pool of valid internal-link targets."""
    return [{"url": entry["url"]} for entry in sitemap_entries()]


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
