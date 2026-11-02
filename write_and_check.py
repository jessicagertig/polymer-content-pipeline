"""Write each post fresh under the current prompt, write a separate opening from scratch in a call of its own (rewrite_opening.py), run the opening's own check loop, run the check loop on every other section, then the whole-article content check, then the whole-post transition pass, then a last count of em dashes per section that lists any section over the limit.

Usage: python write_and_check.py <base-slug> [<base-slug> ...]

For each base slug, the opportunity is read from <base>-FROM-output/<base>-FROM.json, given
the id <base>-TO, and written from scratch into <base>-TO-output/, with fresh research. Then the
checks run. A larger error found by the content check is only reported, in <slug>-larger-errors.md. Nothing is sent to Sanity.

Each finished step is listed in <slug>-steps.json. Run again after a failure, a post starts
at the step that failed: the article, its research, and every finished check are kept. The
file is removed when the transition pass finishes.

Cost gates: a post stops its check loop, keeping the sections done, once it has spent more
than STOP_AT dollars. The next post starts only if the one before it cost NEXT_IF_UNDER
dollars or less.
"""

import json
import sys

from lib.llm import reset_usage, cost, usage_line
from lib.logging import get
from lib.repo import ROOT
from main import _save_output, _save_research
from models.content import ContentPage

log = get(__name__)

FROM = "v4"
TO = "v8"
NEXT_IF_UNDER = 9.0
STOP_AT = 15.0


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
    from review_post import check_post, check_opening, content_check, transition_pass, em_dash_report
    from rewrite_opening import rewrite as rewrite_opening
    slug = f"{base}-{TO}"
    out = ROOT / f"{slug}-output"
    out.mkdir(exist_ok=True)
    steps = out / f"{slug}-steps.json"
    resuming = steps.exists()
    done = json.loads(steps.read_text()) if resuming else []
    if resuming:
        log.info(f"Resuming {slug}; finished steps: {', '.join(done) or 'none'}")
    steps.write_text(json.dumps(done))

    def finish(step: str) -> None:
        done.append(step)
        steps.write_text(json.dumps(done))

    for step, fn in [("write", lambda: write(base, resuming)), ("opening", lambda: rewrite_opening(slug)), ("opening check", lambda: check_opening(slug))]:
        if step not in done:
            fn()
            finish(step)
    for step, fn in [("section check", check_post), ("content check", content_check), ("transition pass", transition_pass)]:
        if step in done:
            continue
        if cost() > STOP_AT:
            log.warning(f"Skipping the {step} and every step after it for {slug}: ${cost():.2f} spent, over ${STOP_AT:.2f}")
            break
        if fn(slug, stop_at=STOP_AT):
            finish(step)
    em_dash_report(slug)
    if "transition pass" in done:
        steps.unlink()


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
