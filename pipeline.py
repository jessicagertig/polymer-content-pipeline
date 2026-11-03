"""The steps every post goes through, in order: the writer, a new opening (rewrite_opening.py),
the resources hidden from every review step, the opening's check loop, the check loop on every
other section, the whole-article content check, the whole-post transition pass, the resource
review (which puts the resources back), the recheck of links and validation, the graphics
suggestions, and a last count of em dashes per section.

Each finished step is listed in <slug>-steps.json. Run again after a failure, a post starts at
the step that failed: the article, its research, and every finished check are kept. The file
is removed when the graphics step finishes.

Cost gate: a post stops its check loops, keeping the sections done, once it has spent more
than STOP_AT dollars.
"""

import json
from typing import Callable

from lib.llm import cost
from lib.logging import get
from lib.repo import ROOT
from models.content import ContentPage

log = get(__name__)

STOP_AT = 15.0


def recheck_saved(slug: str) -> None:
    """The internal links and validation run again on the saved article, and the to-do list is rebuilt."""
    from agents.content_generator import recheck
    from main import _save_output
    path = ROOT / f"{slug}-output" / f"{slug}.json"
    page = recheck(ContentPage.model_validate_json(path.read_text()))
    _save_output(page)
    log.info(f"Rechecked {slug}: {len(page.todos)} to-do item(s)")


def run_steps(slug: str, write: Callable[[bool], None], stop_at: float = STOP_AT) -> list[str]:
    """Runs every step for one post, starting after the last finished step. `write(resuming)`
    writes the post and saves it under `slug`. Returns the finished steps; the post is done
    when "graphics" is among them."""
    from review_post import check_post, check_opening, content_check, transition_pass, em_dash_report, hide_resources, resource_review
    from rewrite_opening import rewrite as rewrite_opening
    from suggest_graphics import suggest
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

    for step, fn in [("write", lambda: write(resuming)), ("hide resources", lambda: hide_resources(slug)),
                     ("opening", lambda: rewrite_opening(slug)), ("opening check", lambda: check_opening(slug))]:
        if step not in done:
            fn()
            finish(step)
    for step, fn in [("section check", check_post), ("content check", content_check), ("transition pass", transition_pass)]:
        if step in done:
            continue
        if cost() > stop_at:
            log.warning(f"Skipping the {step} and every step after it for {slug}: ${cost():.2f} spent, over ${stop_at:.2f}")
            break
        if fn(slug, stop_at=stop_at):
            finish(step)
    if "transition pass" in done and "resource review" not in done:
        resource_review(slug)
        finish("resource review")
    if "resource review" in done and "recheck" not in done:
        recheck_saved(slug)
        finish("recheck")
    if "recheck" in done and "graphics" not in done:
        suggest(slug)
        finish("graphics")
    em_dash_report(slug)
    if "graphics" in done:
        steps.unlink()
    return done
