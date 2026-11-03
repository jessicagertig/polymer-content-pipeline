"""Content generation agent — Claude writes AEO-optimized pages with structured output."""

import json

from config.settings import settings
from lib.llm import structured_call
from agents.research import research_brief
from lib.logging import get
from lib.site_pages import existing_pages
from lib.text import word_count as wc, reading_time, clean_body_html, has_empty_lists, space_em_dashes
from lib.validation import validate, fix_internal_links
from models.content import ContentPage, GeneratedContent, ContentStatus
from prompts.content import CONTENT_SYSTEM, CONTENT_USER, PAGE_SCHEMA, PAGE_STRUCTURES, POLYMER_INCLUDED, POLYMER_EXCLUDED, REDRAFT_SECTION


log = get(__name__)


def faq_items_from_html(html: str) -> list[dict]:
    """[{q, a}] from an <h3>question</h3><p>answer</p> sequence, as plain text, which is how the
    site shows FAQ answers. Each paragraph or list item of an answer stays a separate paragraph,
    with a blank line between them."""
    import re

    def plain(fragment: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", " ", fragment, flags=re.I))).strip()

    items = []
    for q, a in re.findall(r"<h3[^>]*>(.*?)</h3>\s*((?:(?!<h3)[\s\S])*)", html, flags=re.I | re.S):
        paragraphs = [plain(p) for p in re.split(r"</(?:p|li)>", a, flags=re.I)]
        items.append({"q": plain(q), "a": "\n\n".join(p for p in paragraphs if p)})
    return [i for i in items if i["q"] and i["a"]]


def page_structure(opp) -> str:
    """The blog format for one opportunity: the alternatives playbook or the page structure for its type."""
    competitor_name = opp.competitor_signal.competitor if opp.competitor_signal else "the competitor"
    if opp.page_type.value == "alternatives":
        structure = settings.alternatives_playbook()
    else:
        structure = PAGE_STRUCTURES.get(opp.page_type.value, PAGE_STRUCTURES["guide"])
    return structure.replace("{competitor}", competitor_name)


def generate(page: ContentPage) -> ContentPage:
    """Generates full page content. Validates before returning."""
    opp = page.opportunity
    log.info(f"Generating: {opp.proposed_title}")

    pages = existing_pages()
    brand = settings.brand_guidelines()
    research = page.research_brief or research_brief(opp)
    page.research_brief = research

    competitor_context = "N/A"
    if opp.competitor_signal:
        cs = opp.competitor_signal
        competitor_context = (
            f"Competitor: {cs.competitor}\n"
            f"Their page: {cs.competitor_url}\n"
            f"They rank #{cs.competitor_rank} for this keyword.\n"
            "Write a fair, factual comparison. Acknowledge where they're genuinely better."
        )

    page_type = opp.page_type.value
    structure = page_structure(opp)

    if opp.includes_polymer:
        polymer_section = POLYMER_INCLUDED.format(feature_inventory=settings.feature_inventory())
    else:
        polymer_section = POLYMER_EXCLUDED

    user = CONTENT_USER.format(
        keyword=opp.keyword,
        supporting_keywords=", ".join(opp.supporting_keywords) or "(none specified)",
        page_type=page_type,
        page_structure=structure,
        proposed_url=opp.proposed_url,
        proposed_title=opp.proposed_title,
        competitor_context=competitor_context,
        research=research,
        site_domain=settings.site_domain,
        existing_pages=json.dumps(pages),
        polymer_section=polymer_section,
        redraft_section=REDRAFT_SECTION.format(instructions=page.redraft_instructions) if page.redraft_instructions else "",
    )

    # System prompt with brand guidelines is mostly stable across calls → cache it
    system = CONTENT_SYSTEM.format(brand_guidelines=brand, elements_of_style=settings.elements_of_style())

    # Generate; regenerate once if the model leaves empty list scaffolds (renders as
    # big blank gaps). On the final attempt we sanitize whatever we got.
    MAX_ATTEMPTS = 2
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = structured_call(
            system=system,
            user=user,
            tool_name="generate_post",
            tool_description="Submit the complete generated blog post.",
            input_schema=PAGE_SCHEMA,
            max_tokens=32000,
            cache_system=True,
        )
        if isinstance(result.get("faq_html"), str):   # the FAQ comes as HTML; nested JSON broke on some models
            result["faq_items"] = faq_items_from_html(result["faq_html"])
        bad_list = None
        for key in ("faq_items", "internal_links"):
            if isinstance(result.get(key), str):   # some models return the list as a JSON string
                try:
                    result[key] = json.loads(result[key])
                except ValueError as e:
                    bad_list = f"{key} came back as unparseable text ({e})"
        if bad_list and attempt < MAX_ATTEMPTS:
            log.warning(f"Attempt {attempt}/{MAX_ATTEMPTS}: {bad_list}; regenerating…")
            continue
        if bad_list:
            raise ValueError(bad_list)
        if not has_empty_lists(result["body_html"]):
            break
        log.warning(
            f"Attempt {attempt}/{MAX_ATTEMPTS}: model emitted empty list scaffolds for "
            f"'{opp.proposed_title}'"
            + ("; regenerating…" if attempt < MAX_ATTEMPTS else "; sanitizing final output.")
        )

    from lib import repo
    repo.stage(f"{opp.id}-output/{opp.id}-writer-check.md",
               f"# {opp.id} writer's self-check\n\n## Draft\n\n{result.get('draft_body_html', '').strip()}\n\n"
               f"## Check\n\n{result.get('check', '').strip()}\n\n## Final\n\n{result['body_html'].strip()}\n")

    # Safety-net cleanup of empty lists/paragraphs/stray <br> before staging
    body_html, removed = clean_body_html(result["body_html"])
    body_html = space_em_dashes(body_html)
    if removed:
        log.warning(f"Sanitized {removed} empty HTML artifact(s) from body before staging")

    # Internal links: remove links to pages that are not on the site; note the rest as to-dos
    existing_urls = {p["url"] for p in pages}
    body_html, placed_paths, link_todos = fix_internal_links(body_html, existing_urls)
    word_total = wc(body_html)

    # Strip any path prefix from slug — Claude sometimes returns 'pages/my-slug'
    # but the slug field only wants the final segment 'my-slug'
    raw_slug = result["slug"].lstrip("/").split("/")[-1]

    content = GeneratedContent(
        title=result["title"],
        h1=result["h1"],
        meta_description=result["meta_description"],
        main_image_alt=result.get("main_image_alt", ""),
        slug=raw_slug,
        body_html=body_html,
        faq_items=[{k: space_em_dashes(v) if isinstance(v, str) else v for k, v in i.items()} for i in result.get("faq_items", [])],
        internal_links=result.get("internal_links", []),
        word_count=word_total,
        reading_time_minutes=reading_time(body_html),
    )

    # Validate before returning — caller decides whether to stage
    result_validation = validate(content, existing_urls=existing_urls, placed_paths=placed_paths)

    if not result_validation.ok:
        log.error(f"Validation FAILED for '{opp.proposed_title}': {result_validation.errors}")
        raise ValueError(
            f"Generated content failed validation:\n  " + "\n  ".join(result_validation.errors)
        )

    if result_validation.warnings:
        log.warning(f"Validation warnings: {result_validation.warnings}")

    page.todos = [{"item": t, "done": ""} for t in link_todos + result_validation.todos]
    if page.todos:
        log.warning(f"To-do for the follow-up run: {[t['item'] for t in page.todos]}")

    page.content = content
    page.status = ContentStatus.GENERATING

    log.info(f"Generated {word_total} words, {len(content.faq_items)} FAQs")
    return page


def recheck(page: ContentPage) -> ContentPage:
    """After the review steps: fix_internal_links and validate run again on the final body, and the
    to-do list is rebuilt from them. A check that fails here is added to the to-do list instead of
    raised, so the reviewed article is kept."""
    existing_urls = {p["url"] for p in existing_pages()}
    content = page.content
    content.body_html, placed_paths, link_todos = fix_internal_links(content.body_html, existing_urls)
    content.word_count = wc(content.body_html)
    content.reading_time_minutes = reading_time(content.body_html)
    result = validate(content, existing_urls=existing_urls, placed_paths=placed_paths)
    items = link_todos + [f"Failed check after review: {e}" for e in result.errors] + result.todos
    page.todos = [{"item": t, "done": ""} for t in items]
    if page.todos:
        log.warning(f"To-do after review: {[t['item'] for t in page.todos]}")
    return page
