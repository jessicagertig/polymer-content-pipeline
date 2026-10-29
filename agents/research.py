"""Research agent — one web-search call that returns a sourced brief for the writer.

Runs before content generation. The call is capped three ways: the web search tool's
max_uses (settings.research_max_searches), the response max_tokens
(settings.research_max_tokens), and the brief's word limit in the prompt
(settings.research_max_words).
"""

import re

from config.settings import settings
from lib.llm import research_call
from lib.logging import get
from lib.repo import ROOT
from prompts.research import RESEARCH_SYSTEM, RESEARCH_USER, FORMAT_NOTES


log = get(__name__)


def _saved_brief(slug: str):
    """The brief in <slug>-output/ from an earlier run, or the one for the slug without a -vN suffix."""
    if not settings.research_reuse:
        return None
    base = re.sub(r"-v\d+$", "", slug)
    for name in (slug, base):
        path = ROOT / f"{name}-output" / f"{name}-research.md"
        if path.exists() and path.read_text().strip():
            log.info(f"Research reused from {name}-output for {slug}")
            return path.read_text()
    return None


def research_brief(opp) -> str:
    """Returns the research brief text for one opportunity. Raises if the call returns nothing."""
    saved = _saved_brief(opp.id)
    if saved is not None:
        return saved
    log.info(f"Researching: {opp.proposed_title}")
    user = RESEARCH_USER.format(
        max_searches=settings.research_max_searches,
        proposed_title=opp.proposed_title,
        page_type=opp.page_type.value,
        keyword=opp.keyword,
        rationale=opp.rationale,
        format_note=FORMAT_NOTES.get(opp.page_type.value, ""),
        max_words=settings.research_max_words,
    )
    result = research_call(
        system=RESEARCH_SYSTEM,
        user=user,
        max_searches=settings.research_max_searches,
        max_tokens=settings.research_max_tokens,
    )
    if not result["text"]:
        raise RuntimeError("Research call returned no text")
    log.info(
        f"Research done: {result['searches']} searches, "
        f"{result['input_tokens']} in / {result['output_tokens']} out, "
        f"{len(result['text'].split())} words"
    )
    return result["text"]
