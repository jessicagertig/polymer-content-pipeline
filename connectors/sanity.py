"""Sanity connector — writes blogPost drafts and checks for existing posts.

Project a6d1clb1, document type `blogPost` (studio/schemas/blogPost.js). A staged post is
`drafts.<slug>`; publishing happens in Studio.
"""

import json
import urllib.parse
import urllib.request
from datetime import date
from typing import Optional

from config.settings import settings
from lib import portable_text
from lib.logging import get
from models.content import GeneratedContent


log = get(__name__)


def _request(path: str, body: Optional[dict] = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    url = f"https://{settings.sanity_project_id}.api.sanity.io/v{settings.sanity_api_version}{path}"
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Authorization", f"Bearer {settings.sanity_api_token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def query(groq: str, params: Optional[dict] = None) -> dict:
    qs = {"query": groq}
    for name, value in (params or {}).items():
        qs[f"${name}"] = json.dumps(value)
    return _request(f"/data/query/{settings.sanity_dataset}?{urllib.parse.urlencode(qs)}")


def count_posts() -> int:
    return query('count(*[_type == "blogPost"])').get("result", 0)


def document_exists(slug: str) -> bool:
    """True if a blogPost with this slug exists, draft or published."""
    result = query('count(*[_type == "blogPost" && slug.current == $slug])', {"slug": slug})
    return result.get("result", 0) > 0


def draft_id(slug: str) -> str:
    return f"drafts.{slug}"


def build_document(content: GeneratedContent) -> dict:
    """The blogPost document. No featureImage: the header image is added in Studio.
    The table of contents goes after the opening, before the first H2."""
    body = portable_text.from_html(content.body_html)
    first_h2 = next((i for i, b in enumerate(body) if b.get("style") == "h2"), len(body))
    body.insert(first_h2, portable_text.toc_block())
    return {
        "_id": draft_id(content.slug),
        "_type": "blogPost",
        "editorialTitle": content.h1,
        "pageTitle": content.title,
        "slug": {"_type": "slug", "current": content.slug},
        "publishDate": date.today().isoformat(),
        "author": {"_type": "reference", "_ref": settings.sanity_author_ref},
        "metaDescription": content.meta_description,
        "content": body + portable_text.faq_blocks(content.faq_items),
    }


def create_draft(content: GeneratedContent) -> dict:
    doc = build_document(content)
    result = _request(
        f"/data/mutate/{settings.sanity_dataset}",
        {"mutations": [{"createOrReplace": doc}]},
    )
    log.info(f"Sanity draft written: {doc['_id']} ({len(doc['content'])} blocks)")
    return result


def studio_url(document_id: str) -> str:
    if not settings.sanity_studio_url:
        return ""
    published_id = document_id.removeprefix("drafts.")
    return f"{settings.sanity_studio_url.rstrip('/')}/desk/blogPost;{published_id}"


def live_url(slug: str) -> str:
    return f"https://{settings.site_domain}/blog/{slug}"
