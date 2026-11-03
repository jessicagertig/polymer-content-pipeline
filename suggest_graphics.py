"""Suggest the graphics for a finished post, from the image menu (config/image-menu.md).

Usage: python suggest_graphics.py <slug> [<slug> ...]

For each slug, reads <slug>-output/<slug>.json and writes <slug>-output/<slug>-graphics.md: for
each place, the paragraph it follows, why a graphic helps there, and two or three options, each
with a type from the menu, a description in the menu's visual terms, and alt text. The article
is not changed. Nothing goes to Sanity.
"""

import re
import sys

from config.settings import settings
from lib.llm import structured_call, usage_line
from lib.logging import get
from lib.repo import ROOT
from models.content import ContentPage

log = get(__name__)

GRAPHICS_SYSTEM = """You plan the graphics for finished articles on the Polymer blog. Polymer is an applicant tracking system. A designer makes each graphic later from your description. You do not write or change the article."""

# Alt text from the published 2026 articles, word for word: an in-house card, a bar chart, a stage list, a flow diagram, and a step diagram.
ALT_EXAMPLES = """- Card titled First impression bias, with a face-with-monocle emoji above the definition, “The interviewer's opinion forms before the first question and carries through the whole interview.”
- Bar chart titled A structured interview adds three times the predictive value of an unstructured one, showing the improvement in predicting job performance when each is added to a test of general mental ability. Structured interview 24%, unstructured interview 8%. Source Schmidt and Hunter, 1998.
- The seven hiring stages listed in order, each with a candidate count: Inbox 254, Screen 41, Interview 12, Decide 5, Offer 3, Hired 2, Archived 58. Hired is highlighted.
- Flow diagram titled Where applications come from. Three sources, Careers page, Job board, and Search engine, each with an arrow flowing down into a single box labeled Inbox.
- A numbered four-step staircase: Ask the same questions, Score the same way, Look for tradeoffs and proof, Keep notes in one place, Result: hiring calls you can explain."""

GRAPHICS_USER = """Suggest the graphics for the article below.

## The image menu

{menu}

## Alt text in the published articles

{alt_examples}

## The article

{article}

Choose the type of every graphic from the image menu. Find the places in the article where a graphic genuinely helps the reader: a sequence, a comparison of figures, a scorecard or a table, a screen, a definition worth a card. The content decides what goes in each graphic. When at all possible, spread the places through the article, in different sections from the first section after the opening to the section before the last, instead of putting several places in one section. Do not put a graphic in the opening (the text before the first heading), in the last section, or in the FAQ. Do not suggest a graphic for a template, a sample email, or a rubric, which the article already shows as text.

At each place, give two or three options. Each option has:
- a type, named exactly as in the image menu;
- a description of the graphic in the visual terms of that type's "Describe it like this" line: the frame, the layout, any emoji and its tile, where the title and source sit, and the text on the graphic, kept as short as the published graphics keep theirs;
- alt text in the style of the published alt text above: the kind of graphic and its title first, then every label and number the description names, then the source as "Source <name>, <year>." when the graphic shows a statistic.

Every label, number, and name in a description or alt text comes from the article. Invent nothing. Every title and label on a graphic uses the article's own words; do not coin a term the article does not use. Write a source line only when the article names the source as a company, an organization, or an author. Never write a web address on a graphic or in alt text.

Put two statistics in one chart only when the two measure the same thing in the same way, as the image menu says; never pair figures that measure different things. Use a bar chart only for figures the article gives. Do not suggest a graphic that only lists the article's headings, which the table of contents already shows. The paragraph a graphic follows is in the section named for that graphic, and every figure, label, and title on the graphic comes from that section, so the graphic shows what the reader has just read.

Call the `suggest_graphics` tool with the places in article order."""

GRAPHICS_SCHEMA = {
    "type": "object",
    "properties": {
        "places": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string", "description": "The heading of the section, exactly as in the article."},
                    "after": {"type": "string", "description": "The first six words of the paragraph the graphic follows, exactly as in the article."},
                    "why": {"type": "string", "description": "One line on what the passage does that a graphic helps with."},
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "alt": {"type": "string"},
                            },
                            "required": ["type", "description", "alt"],
                        },
                    },
                },
                "required": ["section", "after", "why", "options"],
            },
        },
    },
    "required": ["places"],
}


WEB_ADDRESS = re.compile(r"\b[\w-]+\.(?:com|io|org|net|co|ai)\b", re.I)


def _plain(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def suggest(slug: str) -> None:
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    content = page.content
    faq = "\n\n".join(f"<h3>{i['q']}</h3>\n<p>{i['a']}</p>" for i in content.faq_items)
    article = f"<h1>{content.h1}</h1>\n{content.body_html}\n<h2>Frequently asked questions</h2>\n{faq}"
    result = structured_call(
        system=GRAPHICS_SYSTEM,
        user=GRAPHICS_USER.format(menu=settings.image_menu(), alt_examples=ALT_EXAMPLES, article=article),
        tool_name="suggest_graphics",
        tool_description="Submit the graphics, place by place, in article order.",
        input_schema=GRAPHICS_SCHEMA,
    )
    sections = {_plain(s.split("</h2>", 1)[0]): _plain(s) for s in re.split(r"<h2[^>]*>", content.body_html)[1:]}
    blocks = [f"# Graphics for {slug}\n"]
    for n, p in enumerate(result["places"], 1):
        found = "" if _plain(p["after"]) in sections.get(_plain(p["section"]), "") else " (this paragraph was not found in this section)"
        lines = [f"## {n}. {p['section']}", f"- Place: after the paragraph beginning \"{p['after']}\" in \"{p['section']}\"{found}", f"- Why here: {p['why']}"]
        for letter, o in zip("ABC", p["options"]):
            flag = " (contains a web address)" if WEB_ADDRESS.search(o["description"] + " " + o["alt"]) else ""
            lines.append(f"- Option {letter}: {o['type']}{flag}\n  - Description: {o['description']}\n  - Alt: {o['alt']}")
        blocks.append("\n".join(lines))
    (ROOT / f"{slug}-output" / f"{slug}-graphics.md").write_text("\n\n".join(blocks) + "\n")
    log.info(f"Graphics for {slug}: {len(result['places'])} place(s); {usage_line()}")


if __name__ == "__main__":
    for s in sys.argv[1:]:
        suggest(s)
