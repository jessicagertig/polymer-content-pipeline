"""
Publisher agent — generates a post and stages it as a Sanity draft.

`generate_and_stage(page)`
  Generates content → writes `drafts.<slug>` to Sanity (createOrReplace).
  Publishing is manual: the draft is reviewed and published in Studio and the site is
  deployed. Nothing here auto-publishes.
"""

from connectors import sanity
from lib.logging import get
from models.content import ContentPage, ContentStatus


log = get(__name__)


def generate_and_stage(page: ContentPage) -> ContentPage:
    from agents.content_generator import generate

    page = generate(page)

    opp = page.opportunity
    # Force the slug to the one the idempotency check in main.py keys on (derived from
    # opportunity.proposed_url) instead of trusting whatever slug Claude invented —
    # otherwise document_exists() never finds it and the same post is regenerated on
    # every run.
    page.content.slug = opp.proposed_url.lstrip("/").split("/")[-1]

    sanity.create_draft(page.content)

    page.sanity_document_id = sanity.draft_id(page.content.slug)
    page.sanity_draft_url = sanity.studio_url(page.sanity_document_id)
    page.live_url = sanity.live_url(page.content.slug)
    page.status = ContentStatus.STAGED

    log.info(f"Staged: {page.sanity_document_id}")
    return page
