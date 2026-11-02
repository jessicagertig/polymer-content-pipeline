"""Write a new opening for staged posts from scratch, by the Opening rules in the system prompt.

Usage: python rewrite_opening.py <slug> [<slug> ...]

For each slug, reads <slug>-output/<slug>.json. The writer is never shown the post's current
opening. It gets the title, target keyword, blog format and its outline, the article after the opening, and
the research brief, and writes an entirely new opening from scratch, with its own self-check.
The new opening replaces the text before the first <h2>. The old and new openings are
appended to <slug>-output/<slug>-openings.md so they can be compared. Nothing goes to Sanity
unless STAGE_TO_SANITY=true.
"""

import os
import re
import sys
from datetime import datetime

from config.settings import settings
from connectors import sanity
from lib.llm import structured_call
from lib.text import word_count, reading_time, space_em_dashes
from lib.logging import get
from main import _save_output
from models.content import ContentPage
from prompts.content import CONTENT_SYSTEM
from agents.content_generator import page_structure

log = get(__name__)

OPENING_USER = """Write the opening of this article, by the Opening rules in the system prompt. The opening is everything before the first H2. You are not writing the body.

## Proposed title
{title}

## Target keyword
{keyword}

## Blog format: {page_type}

{page_structure}

## The article after the opening
{article}

## Research
Every statistic in the opening follows the Numbers and statistics rules in the system prompt.

{research}

Write a draft first. Then read the draft back against the house rules, the Opening rules, the Numbers and statistics rules, the Voice and Tone sections of the writing guide, and every rule in The Elements of Style, one rule at a time, and write one line per rule on what you found. Read the whole text of each rule, examples included.

Then check the draft for errors in logic. There are four rules, described below. For each error you find, write a line in the check you submit: quote the sentences involved and say what is wrong. Finish checking the whole draft before you correct anything. Then correct every error listed in the check when you write the final version.

First, wherever the draft gives a reason for something, check that the reason supports the conclusion it is given for. A reason can be true and still not support that conclusion. For example, an opening about rejection emails might say to send rejections promptly because a candidate left waiting will apply elsewhere and may accept another offer. That may be true, but the employer is not hiring that candidate, so it does not support sending the rejection promptly.

Second, check that no sentence is inconsistent with another. For example, an opening might say that most candidates never hear back, then cite a survey in which one in three did not hear back. One in three is not most.

Third, check for direct contradictions, where two statements cannot both be true. For example, a draft might advise in one sentence never to put interview feedback in writing, and in a later sentence recommend emailing each candidate written feedback. (This example is not asserting that one or the other is correct.)

Fourth, when making claims or statements that do not come from the research brief, make sure you are not too specific. For example, you cannot claim that a candidate spent only 15 minutes on an application. You can claim they have less time and work devoted to the role than somebody who reached the final interview, or an interview at all. That is clearly true. And you could say something like, someone who has simply submitted an application has not spent time preparing for an interview. That is clearly true. It is not clearly true that they only spent 15 minutes to submit the application.

Submit the draft, the check, and the final opening.

Call the `write_opening` tool with the draft, the check, and the opening as HTML paragraphs."""


OPENING_SCHEMA = {
    "type": "object",
    "properties": {
        "draft_html": {"type": "string", "description": "Written first. The draft opening as <p> paragraphs."},
        "check": {"type": "string", "description": "Written second. One line per rule on what the draft got wrong, or NONE."},
        "opening_html": {"type": "string", "description": "Written last. The final opening as <p> paragraphs only, with every fault in the check corrected."},
    },
    "required": ["draft_html", "check", "opening_html"],
}


def split_opening(body_html: str) -> tuple[str, str]:
    m = re.search(r"<h2[\s>]", body_html, flags=re.I)
    if not m:
        raise ValueError("no <h2> in the body")
    return body_html[: m.start()], body_html[m.start():]


def rewrite(slug: str) -> None:
    path = settings_root() / f"{slug}-output" / f"{slug}.json"
    page = ContentPage.model_validate_json(path.read_text())
    content = page.content
    old_opening, rest = split_opening(content.body_html)
    system = CONTENT_SYSTEM.format(brand_guidelines=settings.brand_guidelines(), elements_of_style=settings.elements_of_style())
    user = OPENING_USER.format(
        title=content.h1,
        keyword=page.opportunity.keyword,
        page_type=page.opportunity.page_type.value,
        page_structure=page_structure(page.opportunity),
        article=rest,
        research=page.research_brief,
    )
    result = structured_call(
        system=system,
        user=user,
        tool_name="write_opening",
        tool_description="Submit the opening.",
        input_schema=OPENING_SCHEMA,
        max_tokens=8000,
    )
    new_opening = space_em_dashes(result["opening_html"].strip()) + "\n"
    content.body_html = new_opening + rest
    content.word_count = word_count(content.body_html)
    content.reading_time_minutes = reading_time(content.body_html)
    if os.environ.get("STAGE_TO_SANITY") == "true":   # files only unless asked; Sanity is for finished posts
        sanity.create_draft(content)
    _save_output(page)
    record = settings_root() / f"{slug}-output" / f"{slug}-openings.md"
    stamp = datetime.now().isoformat(timespec="minutes")
    with record.open("a") as f:
        f.write(f"# {slug} opening rewrite {stamp}\n\n## Before\n\n{old_opening}\n\n## Draft\n\n{result.get('draft_html', '').strip()}\n\n## Writer's check\n\n{result.get('check', '').strip()}\n\n## After\n\n{new_opening}\n\n")
    log.info(f"Opening rewritten for {slug}: {word_count(old_opening)} -> {word_count(new_opening)} words")


def settings_root():
    from lib.repo import ROOT
    return ROOT


if __name__ == "__main__":
    for s in sys.argv[1:]:
        rewrite(s)
