"""
Indexing connector — ping search engines about new or updated pages.

Two paths:
  1. IndexNow — Bing, Yandex, Seznam. Free, no auth. https://www.indexnow.org
     The key must be hosted at https://<site_domain>/<key>.txt.
  2. Google Search Console URL Inspection API — requests indexing for Google.
     (Quota: 200 URLs/day per property)

Publishing is manual, so `submit_recent()` runs on a schedule: it reads the sitemap and
submits every URL whose <lastmod> is inside the window.
"""

import requests
from googleapiclient.discovery import build

from config.settings import settings
from lib import site_pages
from lib.google_auth import get_credentials
from lib.logging import get


log = get(__name__)

INDEXNOW_ENDPOINT = "https://api.indexnow.org/IndexNow"


def indexnow_key_file_content() -> tuple[str, str]:
    """Returns (filename, content) for the IndexNow verification file hosted on the site."""
    return f"{settings.indexnow_key}.txt", settings.indexnow_key


def ping_indexnow(urls: list[str]) -> dict:
    """Notifies IndexNow that the given URLs are new or updated."""
    if not urls:
        return {"submitted": 0}
    if not settings.indexnow_key:
        log.info("IndexNow key not set — skipping")
        return {"submitted": 0}

    payload = {
        "host": settings.site_domain,
        "key": settings.indexnow_key,
        "keyLocation": f"https://{settings.site_domain}/{settings.indexnow_key}.txt",
        "urlList": urls,
    }
    try:
        resp = requests.post(INDEXNOW_ENDPOINT, json=payload, timeout=15)
        log.info(f"IndexNow: submitted {len(urls)} URLs → HTTP {resp.status_code}")
        return {"submitted": len(urls), "status": resp.status_code}
    except requests.RequestException as e:
        log.warning(f"IndexNow submission failed: {e}")
        return {"submitted": 0, "error": str(e)}


def request_google_indexing(url: str) -> dict:
    """
    Requests Google to recrawl a URL via the URL Inspection API.
    Note: this DOESN'T guarantee indexing — Google still decides — but it's the
    fastest discovery signal available.
    """
    if not settings.google_search_console_refresh_token:
        log.info("GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN not set — skipping Google indexing request")
        return {"skipped": True}
    try:
        creds = get_credentials(scopes=["https://www.googleapis.com/auth/webmasters"])
        service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

        inspection = (
            service.urlInspection()
            .index()
            .inspect(body={"inspectionUrl": url, "siteUrl": settings.gsc_site_url})
            .execute()
        )
        log.info(f"GSC inspection: {url} → {inspection.get('inspectionResult', {}).get('indexStatusResult', {}).get('verdict')}")
        return inspection
    except Exception as e:
        log.warning(f"GSC URL inspection failed for {url}: {e}")
        return {"error": str(e)}


def submit_url(url: str) -> dict:
    """One-shot: notify IndexNow + request Google indexing."""
    return {
        "indexnow": ping_indexnow([url]),
        "google": request_google_indexing(url),
    }


def submit_recent(hours: int = 24) -> list[str]:
    """Submits every sitemap URL modified in the last `hours` to both paths."""
    urls = [f"https://{settings.site_domain}{entry['url']}" for entry in site_pages.recently_updated(hours)]
    if not urls:
        log.info(f"No sitemap entries modified in the last {hours}h")
        return []
    ping_indexnow(urls)
    for url in urls:
        request_google_indexing(url)
    return urls
