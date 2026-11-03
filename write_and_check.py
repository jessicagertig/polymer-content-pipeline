"""Write a test copy of each post fresh under the current prompt, then run every step in pipeline.run_steps: a new opening, the opening's check loop, the check loop on every other section, the whole-article content check, the transition pass, the recheck of links and validation, the graphics suggestions, and a last count of em dashes per section.

Usage: python write_and_check.py <base-slug> [<base-slug> ...]

For each base slug, the opportunity is read from <base>-FROM-output/<base>-FROM.json, given
the id <base>-TO, and written from scratch into <base>-TO-output/, with fresh research. Then the
checks run. A larger error found by the content check is only reported, in <slug>-larger-errors.md. Nothing is sent to Sanity.

The steps, the step file, and resuming after a failure are in pipeline.run_steps, which the
production path in main.py also uses.

Cost gates: a post stops its check loop, keeping the sections done, once it has spent more
than STOP_AT dollars. The next post starts only if the one before it cost NEXT_IF_UNDER
dollars or less.
"""

import sys

from lib.llm import reset_usage, cost, usage_line
from lib.logging import get
from lib.repo import ROOT
from main import _save_output, _save_research
from models.content import ContentPage
from pipeline import STOP_AT, run_steps

log = get(__name__)

FROM = "v4"
TO = "v9"
NEXT_IF_UNDER = 9.0


def write(base: str, resuming: bool) -> str:
    """Research and write the post. Resuming a failed run, the research saved by that run is used."""
    from agents.content_generator import generate
    src = f"{base}-{FROM}"
    slug = f"{base}-{TO}"
    old = ContentPage.model_validate_json((ROOT / f"{src}-output" / f"{src}.json").read_text())
    opp = old.opportunity.model_copy(update={"id": slug, "proposed_url": old.opportunity.proposed_url.replace(src, slug)})
    saved = ROOT / f"{slug}-output" / f"{slug}-research.md"
    page = ContentPage(opportunity=opp, research_brief=saved.read_text() if resuming and saved.exists() else "")
    try:
        generate(page)
    except Exception:
        _save_research(page)
        raise
    page.content.slug = slug
    _save_output(page)
    log.info(f"Written {slug}: {page.content.word_count} words; {usage_line()}")
    return slug


def run(base: str) -> None:
    run_steps(f"{base}-{TO}", lambda resuming: write(base, resuming), STOP_AT)


if __name__ == "__main__":
    bases = sys.argv[1:]
    for n, base in enumerate(bases):
        reset_usage()
        try:
            run(base)
        except Exception as e:
            log.exception(f"Failed {base}-{TO}: {e}; {usage_line()}")
            continue
        spent = cost()
        log.info(f"Done {base}-{TO}: {usage_line()}")
        if spent > NEXT_IF_UNDER and n + 1 < len(bases):
            log.warning(f"Not starting the next post: {base}-{TO} cost ${spent:.2f}, over ${NEXT_IF_UNDER:.2f}")
            break
