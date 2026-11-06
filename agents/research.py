"""Research agent — one web-search call that returns a sourced brief for the writer.

Runs before content generation. The call is capped three ways: the web search tool's
max_uses (settings.research_max_searches), the response max_tokens
(settings.research_max_tokens), and the brief's word limit in the prompt
(settings.research_max_words).
"""

import re

from config.settings import settings
from lib.llm import research_call, structured_call
from lib.logging import get
from lib.repo import ROOT
from prompts.research import (RESEARCH_SYSTEM, RESEARCH_USER, FORMAT_NOTES, EDITOR_BRIEF, POLYMER_ARTICLES_USER,
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
        editor_brief=EDITOR_BRIEF.format(rationale=opp.rationale),
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


def _polymer_articles(opp) -> str:
    """For an article with Hub Links: each published Hub Links article's text from Sanity, read by one call as
    sources, under "## Polymer articles". Empty when none is published yet."""
    from connectors import sanity
    from lib.site_pages import blog_articles
    from lib.validation import site_path
    titles = {a["url"]: a["title"] for a in blog_articles()}
    articles = []
    for path in (site_path(u) for u in opp.hub_links):
        if path not in titles:
            continue   # not published yet; the writer gets a note for it
        doc = sanity.query('*[_type == "blogPost" && slug.current == $slug && !(_id in path("drafts.**"))][0]{content}',
                           {"slug": path.rsplit("/", 1)[-1]}).get("result") or {}
        text = "\n".join("".join(c.get("text", "") for c in b.get("children", [])) for b in doc.get("content") or [] if b.get("_type") == "block")
        articles.append(f"### {titles[path]}\nhttps://{settings.site_domain}{path}\n\n{text}")
    if not articles:
        return ""
    result = structured_call(system=RESEARCH_SYSTEM, user=POLYMER_ARTICLES_USER.format(articles="\n\n".join(articles)),
                             tool_name="submit_research", tool_description="Submit the Polymer articles section of the brief.",
                             input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
                             max_tokens=settings.research_polymer_articles_max_tokens)
    log.info(f"Research, Polymer articles: {len(articles)} article(s), {len(result['text'].split())} words")
    return "## Polymer articles\n\n" + result["text"].strip()


def _three_step_brief(opp, structure: str) -> str:
    """Definitions, then the article type's topic search, then statistics, each a separate call.
    The statistics step searches only the reputable sources' sites (config/reputable-sources.txt).
    Its output is also saved on its own as <slug>-output/<slug>-statistics.md, for the checker and fixer."""
    page_type = opp.page_type.value
    context = dict(
        topic=STEP_TOPICS[page_type],
        proposed_title=opp.proposed_title,
        page_type=page_type,
        page_structure=structure,
        keyword=opp.keyword,
        supporting_keywords=", ".join(opp.supporting_keywords) or "(none specified)",
        editor_brief=EDITOR_BRIEF.format(rationale=opp.rationale),
    )
    definitions_note = (" Devote one search to each side of the versus." if page_type == "comparison"
                        else " If one search turns up enough, stop there.")
    steps = [
        (DEFINITIONS_STEP | {"search_note": definitions_note}, 2),
        (TOPIC_STEPS[page_type], 2),
        (STATISTICS_STEP, settings.research_statistics_searches),
    ]
    reputable = [address for _, addresses in settings.reputable_sources() for address in addresses]
    parts = [polymer] if opp.hub_links and (polymer := _polymer_articles(opp)) else []
    for step, searches in steps:
        result = research_call(
            system=RESEARCH_SYSTEM,
            user=STEP_USER.format(**context, **step, max_searches=searches),
            max_searches=searches,
            max_tokens=settings.research_resource_max_tokens if opp.resource_article else settings.research_max_tokens,
            blocked_domains=settings.competitor_domains(),
            allowed_domains=reputable if step is STATISTICS_STEP else None,
        )
        if not result["text"]:
            raise RuntimeError(f"Research call for {step['step']} returned no text")
        log.info(f"Research, {step['step']}: {result['searches']} searches, {len(result['text'].split())} words")
        parts.append(result["text"])
        if step is STATISTICS_STEP:
            from lib import repo
            repo.stage(f"{opp.id}-output/{opp.id}-statistics.md", result["text"])
    return "\n\n".join(parts)
