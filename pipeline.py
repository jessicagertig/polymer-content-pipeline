"""The steps every post goes through, in order: the writer, a new opening (rewrite_opening.py),
the resources hidden from every review step, the opening's check loop, the check loop on every
other section, the whole-article content check, the whole-post transition pass, the resource
review (which puts the resources back), the recheck of links and validation, the list of
links that may go to competitors, the graphics suggestions, and a last count of em dashes per section.

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

STEP_ORDER = ("write", "hide resources", "opening", "opening check", "section check", "content check",
              "transition pass", "resource review", "recheck", "competitor links", "graphics")


def next_step(slug: str) -> str:
    """The step a post stopped or failed at: the first step in STEP_ORDER that is not finished."""
    steps = ROOT / f"{slug}-output" / f"{slug}-steps.json"
    done = json.loads(steps.read_text()) if steps.exists() else []
    return next((s for s in STEP_ORDER if s not in done), "")


def recheck_saved(slug: str) -> None:
    """The internal links and validation run again on the saved article, and the to-do list is rebuilt."""
    from agents.content_generator import recheck
    from main import _save_output
    path = ROOT / f"{slug}-output" / f"{slug}.json"
    page = recheck(ContentPage.model_validate_json(path.read_text()))
    _save_output(page)
    log.info(f"Rechecked {slug}: {len(page.todos)} to-do item(s)")


SKIPPED = "Step skipped"   # the start of a to-do item for a step that did not run; the recheck keeps these


def _skip(slug: str, step: str, error: str) -> None:
    """Adds a to-do item to the saved post saying the step did not run."""
    from main import _save_output
    page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
    page.todos.append({"item": f"{SKIPPED}: the {step} failed twice and did not run ({error}).", "done": ""})
    _save_output(page)


def run_steps(slug: str, write: Callable[[bool], None], stop_at: float = STOP_AT) -> list[str]:
    """Runs every step for one post, starting after the last finished step. `write(resuming)`
    writes the post and saves it under `slug`. Returns the finished steps; the post is done
    when "graphics" is among them."""
    from review_post import (check_post, check_opening, content_check, transition_pass, em_dash_report, hide_resources, resource_review,
                             restore_resources, competitor_links)
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

    def attempt(step: str, fn: Callable[[], object]) -> object:
        """Runs a step, and once more if it fails. A step that fails twice is skipped: the article keeps
        the version from before it, the to-do list says which step did not run, and the post goes on."""
        for n in (1, 2):
            try:
                return fn()
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
                log.warning(f"The {step} failed for {slug} (attempt {n} of 2): {error}")
        if step == "resource review":
            restore_resources(slug)
        _skip(slug, step, error)
        return True

    if "write" not in done:   # never skipped: without it there is no article
        write(resuming)
        finish("write")
    for step, fn in [("hide resources", lambda: hide_resources(slug)), ("opening", lambda: rewrite_opening(slug)),
                     ("opening check", lambda: check_opening(slug))]:
        if step not in done:
            attempt(step, fn)
            finish(step)
    for step, fn in [("section check", check_post), ("content check", content_check), ("transition pass", transition_pass)]:
        if step in done:
            continue
        if cost() > stop_at:
            log.warning(f"Skipping the {step} and every step after it for {slug}: ${cost():.2f} spent, over ${stop_at:.2f}")
            break
        if attempt(step, lambda fn=fn: fn(slug, stop_at=stop_at)):
            finish(step)
    for before, step, fn in [("transition pass", "resource review", resource_review), ("resource review", "recheck", recheck_saved),
                             ("recheck", "competitor links", competitor_links), ("competitor links", "graphics", suggest)]:
        if before in done and step not in done:
            attempt(step, lambda fn=fn: fn(slug))
            finish(step)
    try:
        em_dash_report(slug)
    except Exception as e:
        log.warning(f"The em dash report failed for {slug}: {type(e).__name__}: {e}")
    if "graphics" in done:
        steps.unlink()
    return done
