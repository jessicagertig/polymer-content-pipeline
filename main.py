"""
Blog Bot (Polymer) — main orchestrator.

Writes editorial BLOG POSTS as Sanity `blogPost` drafts. Publishing is manual: review
and publish in Studio, then deploy the site.

Commands:
  python main.py run           # scheduled daily run: the next 'Launch Batch' post, or this week's calendar post
  python main.py calendar [N]  # write + STAGE the next N scheduled posts from the calendar (default 1)
  python main.py launch        # write + STAGE all pending 'Launch Batch' posts at once
  python main.py redraft SLUG  # write a staged post again, following REDRAFT_INSTRUCTIONS (Slack's Redraft button)
  python main.py resume SLUG   # resume a stopped post from its last finished step (Slack's Resume now button)
  python main.py index         # submit sitemap URLs modified in the last 24h to IndexNow + Google
  python main.py doctor        # check settings + connectivity

DRY_RUN=true runs every step for a post but stages nothing to Sanity, sends nothing to Slack,
and leaves the calendar unmarked.
"""

import os
import sys
from rich.console import Console
from rich.table import Table

from lib.logging import setup as setup_logging, get


log = get(__name__)
console = Console()

# This run's articles and failures: the run's log goes into the article's folder when the run
# worked on one article, and each failure gets a Failed message in Slack.
_run: dict = {"slugs": [], "failures": []}


def _fresh_calendar_opportunities() -> list:
    """Calendar posts with no blogPost (draft or published) in Sanity yet, earliest-first."""
    from connectors import sanity
    from lib import content_calendar
    opps = content_calendar.load_opportunities()
    return [o for o in opps if not sanity.document_exists(o.id)]


def _split_launch(opps: list) -> tuple[list, list]:
    """(launch-batch, scheduled) — Launch Batch posts are staged all at once (bulk);
    scheduled ones go one-per-run."""
    launch = [o for o in opps if o.launch_batch]
    scheduled = [o for o in opps if not o.launch_batch]
    return launch, scheduled


def _save_output(page) -> None:
    """Writes the post into <slug>-output/ in the repo: <slug>.json (the whole ContentPage,
    to-do list included), <slug>.md (for review), <slug>-research.md. A Lambda run pushes
    them to GitHub at the end of the run (lib.repo)."""
    from lib import repo
    slug = page.opportunity.id
    repo.stage(f"{slug}-output/{slug}.json", page.model_dump_json(indent=2))
    repo.stage(f"{slug}-output/{slug}.md", _as_markdown(page))
    _save_research(page)
    log.info(f"Saved output: {slug}-output/")


def _save_research(page) -> None:
    """Writes the research brief on its own, so it survives a failed writing call."""
    from lib import repo
    if not page.research_brief:
        return
    slug = page.opportunity.id
    repo.stage(f"{slug}-output/{slug}-research.md", page.research_brief)


def _as_markdown(page) -> str:
    """The post as one markdown file for review: the SEO fields, the body, the FAQ, then
    the to-do list for the follow-up run."""
    from markdownify import markdownify
    c = page.content
    head = (
        f"# {c.h1}\n\n"
        f"pageTitle: {c.title}\n"
        f"slug: {c.slug}\n"
        f"metaDescription: {c.meta_description}\n"
        f"mainImageAlt: {c.main_image_alt}\n\n"
    )
    body = markdownify(c.body_html, heading_style="ATX")
    faq = "\n\n## Frequently asked questions\n\n" + "\n\n".join(
        f"### {item['q']}\n\n{item['a']}" for item in c.faq_items
    ) if c.faq_items else ""
    todo = "\n\n## To-do\n\n" + "\n".join(
        f"- {t['item']}" + (f" (done {t['done']})" if t.get("done") else "") for t in page.todos
    ) if page.todos else ""
    return head + body.strip() + faq + todo + "\n"


def _stage_one(o, instructions: str = "") -> "object":
    """Writes one calendar post and runs every step in pipeline.run_steps, then stages it once as a
    Sanity draft, notifies Slack, and marks the calendar row as generated. Returns the staged
    ContentPage, or None when the post failed or stopped before its last step. A post that
    stopped resumes from its last finished step on the next run. With `instructions`, the post is
    a redraft: the writer uses the saved research and follows the instructions, and the calendar
    row is not marked again."""
    from agents import publisher
    from agents.content_generator import generate
    from connectors import slack
    from lib import content_calendar, resources
    from lib.llm import reset_usage, usage_line
    from lib.repo import ROOT
    from models.content import ContentPage
    from pipeline import run_steps

    console.print(f"[cyan]→ {o.proposed_title}[/cyan]  ({o.page_type.value}, kw: {o.keyword})")
    slug = o.id
    _run["slugs"].append(slug)
    reset_usage()

    def write(resuming: bool) -> None:
        saved = ROOT / f"{slug}-output" / f"{slug}-research.md"
        page = ContentPage(opportunity=o, research_brief=saved.read_text() if (resuming or instructions) and saved.exists() else "",
                           redraft_instructions=instructions)
        try:
            generate(page)
        except Exception:
            if page.content:
                _save_output(page)
            else:
                _save_research(page)
            raise
        page.content.slug = slug
        _save_output(page)

    try:
        done = run_steps(slug, write)
        if "graphics" not in done:
            log.warning(f"'{o.proposed_title}' stopped after: {', '.join(done)}. Not staged; {usage_line()}")
            if os.environ.get("DRY_RUN") != "true":
                slack.notify_stopped(ContentPage(opportunity=o), done, usage_line())
            return None
        page = ContentPage.model_validate_json((ROOT / f"{slug}-output" / f"{slug}.json").read_text())
        if os.environ.get("DRY_RUN") == "true":   # a full test run: every step, but nothing staged, sent, or marked
            log.info(f"DRY_RUN: '{o.proposed_title}' finished every step; not staged; {usage_line()}")
            return page
        page.content.body_html = resources.unwrap(page.content.body_html)
        publisher.stage(page)
        _save_output(page)
        console.print(f"  [green]Staged:[/green] {page.sanity_document_id}; {usage_line()}")
        try:
            slack.notify_staged(page, spent=usage_line())
        except Exception as e:
            log.warning(f"Slack notification failed (post is staged): {type(e).__name__}: {e}")
        if o.calendar_row and not instructions:
            content_calendar.mark_generated(o.calendar_row)
        return page
    except Exception as e:
        from pipeline import next_step
        log.exception(f"Failed for '{o.proposed_title}': {e}; {usage_line()}")
        console.print(f"  [red]Failed:[/red] {e}")
        _run["failures"].append({"opp": o, "step": next_step(slug), "reason": str(e), "spent": usage_line()})
        return None


def _saved_opportunity(slug: str):
    """The post's opportunity from its saved article, or from the calendar when the post failed
    before its article was saved."""
    from lib import content_calendar
    from lib.repo import ROOT
    from models.content import ContentPage
    path = ROOT / f"{slug}-output" / f"{slug}.json"
    if path.exists():
        return ContentPage.model_validate_json(path.read_text()).opportunity
    return next(o for o in content_calendar.load_opportunities() if o.id == slug)


def redraft():
    """CLI: python main.py redraft <slug>. Writes a staged post again from its saved research,
    following the instructions typed into the Slack Redraft box (REDRAFT_INSTRUCTIONS), runs every
    step, and stages it in place of the earlier Sanity draft. Every file in the post's folder but
    the research brief and its statistics is removed first, so no record from the earlier draft carries over; git
    keeps the earlier draft."""
    from lib.repo import ROOT
    slug = sys.argv[2]
    opp = _saved_opportunity(slug)
    for f in (ROOT / f"{slug}-output").iterdir():
        if f.is_file() and f.name not in (f"{slug}-research.md", f"{slug}-statistics.md"):
            f.unlink()
    _stage_one(opp, os.environ["REDRAFT_INSTRUCTIONS"])


def resume():
    """CLI: python main.py resume <slug>. Resumes a stopped post from its last finished step."""
    _stage_one(_saved_opportunity(sys.argv[2]))


def stage_launch_batch() -> int:
    """Generate + stage every pending 'Launch Batch' post, all at once (bulk).
    Returns how many were staged."""
    launch, _ = _split_launch(_fresh_calendar_opportunities())
    if not launch:
        return 0

    console.rule(f"[bold green]Blog Bot — Launch Batch: staging {len(launch)} post(s)[/bold green]")
    return sum(1 for o in launch if _stage_one(o) is not None)


def stage_calendar(limit: int = 1) -> int:
    """Generate + stage the next `limit` SCHEDULED (Week N) posts from the calendar.
    Launch Batch posts are handled separately by stage_launch_batch(). Returns how many
    were staged."""
    _, scheduled = _split_launch(_fresh_calendar_opportunities())
    if not scheduled:
        console.print("[yellow]No upcoming scheduled calendar posts left to stage.[/yellow]")
        return 0

    batch = scheduled[:limit]
    console.rule(f"[bold green]Blog Bot — Staging {len(batch)} scheduled post(s) from calendar[/bold green]")
    return sum(1 for o in batch if _stage_one(o) is not None)


def run_from_calendar():
    """CLI: stage the next N upcoming posts from the calendar (N from argv, default 1)."""
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    stage_calendar(limit)


def run_launch():
    """CLI: generate + stage ALL pending 'Launch Batch' posts at once (bulk)."""
    n = stage_launch_batch()
    if n == 0:
        console.print("[yellow]No pending Launch Batch posts.[/yellow]")


def scheduled_run():
    """Daily: one Launch Batch post per run while any remain. After that, one Week N post, only
    when no post was generated in the last 7 days (the calendar's Generated At column)."""
    from datetime import datetime, timedelta, timezone
    from lib import content_calendar

    launch, scheduled = _split_launch(_fresh_calendar_opportunities())
    if launch:
        log.info(f"Launch Batch: {len(launch)} post(s) left; staging the next one.")
        _stage_one(launch[0])
        return
    last = content_calendar.last_generated()
    if last and datetime.now(timezone.utc) - last < timedelta(days=7):
        log.info(f"Last post generated {last:%Y-%m-%d}; the next Week N post is due 7 days after it.")
        return
    if scheduled:
        log.info(f"Calendar phase ({len(scheduled)} left): staging this week's post.")
        _stage_one(scheduled[0])
    else:
        log.info("Calendar exhausted: nothing to stage.")


def submit_recent_for_indexing():
    """Daily job — submit sitemap URLs modified in the last 24h to IndexNow + Google."""
    from connectors import indexing
    urls = indexing.submit_recent(hours=24)
    log.info(f"Submitted {len(urls)} URL(s) for indexing.")


def doctor():
    """Sanity-checks credentials and connectivity for all services."""
    from config.settings import settings
    from lib.content_calendar import CALENDAR_PATH

    checks = []

    pairs = [
        ("Anthropic API key", settings.anthropic_api_key),
        ("Google Sheets client ID", settings.google_internal_sheets_client_id),
        ("Google Sheets client secret", settings.google_internal_sheets_client_secret),
        ("Google Sheets refresh token", settings.google_internal_sheets_refresh_token),
        ("Search Console refresh token (optional)", settings.google_search_console_refresh_token),
        ("GSC site URL", settings.gsc_site_url),
        ("Sanity dataset", settings.sanity_dataset),
        ("Sanity API token", settings.sanity_api_token),
        ("Sanity Studio URL", settings.sanity_studio_url),
        ("IndexNow key", settings.indexnow_key),
        ("Slack bot token", settings.slack_bot_token),
        ("Slack content channel", settings.slack_content_channel),
        ("Content calendar CSV", str(CALENDAR_PATH) if CALENDAR_PATH.exists() else ""),
    ]
    for label, value in pairs:
        checks.append((label, "✓ set" if value else "✗ missing"))

    brand = settings.brand_guidelines()
    if not brand.strip():
        checks.append(("Brand guidelines", "✗ config/brand_guidelines.md is empty"))
    elif "[To be written.]" in brand:
        checks.append(("Brand guidelines", "⚠ config/brand_guidelines.md still has placeholders"))
    else:
        checks.append(("Brand guidelines", "✓ filled"))

    table = Table(title="Doctor report", show_header=True)
    table.add_column("Check")
    table.add_column("Status")
    for label, status in checks:
        table.add_row(label, status)
    console.print(table)

    console.rule("[bold]Live probes[/bold]")
    _probe("Sanity", _probe_sanity)
    _probe("Slack", _probe_slack)
    _probe("Calendar", _probe_calendar)
    _probe("Sitemap", _probe_sitemap)


def _probe(name: str, fn) -> None:
    try:
        result = fn()
        console.print(f"[green]✓[/green] {name}: {result}")
    except Exception as e:
        console.print(f"[red]✗[/red] {name}: {type(e).__name__}: {e}")


def _probe_sanity() -> str:
    from connectors import sanity
    return f"{sanity.count_posts()} blogPost documents"


def _probe_slack() -> str:
    from connectors.slack import _client
    r = _client().auth_test()
    return f"connected as {r['user']} in {r['team']}"


def _probe_calendar() -> str:
    from lib import content_calendar
    return f"{len(content_calendar.load_opportunities())} rows not yet generated"


def _probe_sitemap() -> str:
    from lib import site_pages
    return f"{len(site_pages.existing_pages())} URLs"


COMMANDS = {
    "run": scheduled_run,
    "calendar": run_from_calendar,
    "launch": run_launch,
    "redraft": redraft,
    "resume": resume,
    "index": submit_recent_for_indexing,
    "doctor": doctor,
}


def _run_cli(cmd: str) -> bool:
    """Runs a COMMANDS entry. Returns False if it raised. The run's log is saved to
    run-logs/<date>-<command>.log, or to the article's folder when the run worked on one article,
    and each failure gets a Failed message in Slack with the log in its thread. doctor keeps no log."""
    from datetime import datetime, timezone
    from lib import repo
    from lib.logging import start_run_log, stop_run_log
    from lib.repo import ROOT

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")
    log_path = ROOT / "run-logs" / f"{stamp}-{cmd}.log"
    handler = start_run_log(log_path) if cmd != "doctor" else None
    ok = True
    repo.reset()
    try:
        COMMANDS[cmd]()
        repo.push(f"Engine run: {cmd}")
    except Exception as e:
        ok = False
        log.exception(f"Command '{cmd}' failed: {e}")
        _run["failures"].append({"opp": None, "step": "", "reason": str(e), "spent": ""})
    finally:
        if handler:
            stop_run_log(handler)
    if handler and len(_run["slugs"]) == 1:
        slug = _run["slugs"][0]
        (ROOT / f"{slug}-output").mkdir(exist_ok=True)
        log_path = log_path.replace(ROOT / f"{slug}-output" / f"{slug}-{stamp}-{cmd}.log")
    if os.environ.get("DRY_RUN") != "true":
        from connectors import slack
        for failure in _run["failures"]:
            try:
                slack.notify_failed(failure["opp"], cmd, failure["step"], failure["reason"], failure["spent"], log_path)
            except Exception as e:
                log.warning(f"Slack Failed message did not post: {type(e).__name__}: {e}")
    return ok


if __name__ == "__main__":
    setup_logging()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd not in COMMANDS:
        console.print(f"[red]Unknown command: {cmd}[/red]")
        console.print(f"Available: {', '.join(COMMANDS)}")
        sys.exit(1)

    if not _run_cli(cmd):
        sys.exit(1)
