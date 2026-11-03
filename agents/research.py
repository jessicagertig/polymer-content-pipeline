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
from prompts.research import (RESEARCH_SYSTEM, RESEARCH_USER, FORMAT_NOTES, EDITOR_BRIEF,
                              STEP_USER, STEP_TOPICS, DEFINITIONS_STEP, TOPIC_STEPS, STATISTICS_STEP)


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
    from agents.content_generator import page_structure  # here, not at the top: content_generator imports this module
    log.info(f"Researching: {opp.proposed_title}")
    if opp.page_type.value in STEP_TOPICS and not opp.product_based:
        return _three_step_brief(opp, page_structure(opp))
    user = RESEARCH_USER.format(
        max_searches=settings.research_max_searches,
        proposed_title=opp.proposed_title,
        page_type=opp.page_type.value,
        page_structure=page_structure(opp),
        keyword=opp.keyword,
        supporting_keywords=", ".join(opp.supporting_keywords) or "(none specified)",
        editor_brief=EDITOR_BRIEF.format(rationale=opp.rationale) if opp.page_type.value == "alternatives" else "",
        format_note=FORMAT_NOTES.get(opp.page_type.value, ""),
        max_words=settings.research_max_words,
    )
    result = research_call(
        system=RESEARCH_SYSTEM,
        user=user,
        max_searches=settings.research_max_searches,
        max_tokens=settings.research_resource_max_tokens if opp.resource_article else settings.research_max_tokens,
        blocked_domains=settings.competitor_domains(),
    )
    if not result["text"]:
        raise RuntimeError("Research call returned no text")
    log.info(
        f"Research done: {result['searches']} searches, "
        f"{result['input_tokens']} in / {result['output_tokens']} out, "
        f"{len(result['text'].split())} words"
    )
    return result["text"]


def _three_step_brief(opp, structure: str) -> str:
    """Definitions, then the article type's topic search, then statistics, each a separate call.
    Statistics gets the searches the first two steps did not use."""
    page_type = opp.page_type.value
    context = dict(
        topic=STEP_TOPICS[page_type],
        proposed_title=opp.proposed_title,
        page_type=page_type,
        page_structure=structure,
        keyword=opp.keyword,
        supporting_keywords=", ".join(opp.supporting_keywords) or "(none specified)",
    )
    definitions_note = (" Devote one search to each side of the versus." if page_type == "comparison"
                        else " If one search turns up enough, stop there.")
    steps = [
        (DEFINITIONS_STEP | {"search_note": definitions_note}, 2),
        (TOPIC_STEPS[page_type], 2),
        (STATISTICS_STEP, None),
    ]
    parts, used = [], 0
    for step, searches in steps:
        searches = searches or max(3, settings.research_step_searches - used)
        result = research_call(
            system=RESEARCH_SYSTEM,
            user=STEP_USER.format(**context, **step, max_searches=searches),
            max_searches=searches,
            max_tokens=settings.research_resource_max_tokens if opp.resource_article else settings.research_max_tokens,
            blocked_domains=settings.competitor_domains(),
        )
        if not result["text"]:
            raise RuntimeError(f"Research call for {step['step']} returned no text")
        used += result["searches"]
        log.info(f"Research, {step['step']}: {result['searches']} searches, {len(result['text'].split())} words")
        parts.append(result["text"])
    return "\n\n".join(parts)
