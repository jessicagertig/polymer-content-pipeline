"""Slack connector — notifications and run reports."""

from pathlib import Path

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config.settings import settings
from lib.logging import get
from lib.repo import ROOT
from models.content import ContentPage


log = get(__name__)

# Slack section blocks cap out at 3000 chars of text.
_SECTION_MAX_CHARS = 2900


def _client() -> WebClient:
    return WebClient(token=settings.slack_bot_token)


def _configured() -> bool:
    return bool(settings.slack_bot_token) and not settings.slack_bot_token.startswith("xoxb-...")


def _post(channel: str, blocks: list, text: str = "") -> str:
    """Posts a message and returns its ts, which replies in its thread need, or "" when nothing was posted."""
    if not _configured():
        log.info(f"Slack not configured — skipping post to {channel}: {text}")
        return ""
    try:
        return _client().chat_postMessage(channel=channel, blocks=blocks, text=text)["ts"]
    except SlackApiError as e:
        log.error(f"Slack post to {channel} failed: {e.response['error']}")
        return ""


def _upload(channel: str, path: Path, title: str, ts: str) -> None:
    """Attaches a file in the thread of the message `ts`. When the upload fails (the bot needs the
    files:write scope, and the channel setting must be the channel's ID), the file's text is posted
    in the same thread instead, one reply per section."""
    if not _configured() or not ts or not path.exists():
        log.info(f"Slack not configured, no message, or {path.name} missing — skipping upload to {channel}")
        return
    try:
        _client().files_upload_v2(channel=channel, file=str(path), title=title, thread_ts=ts)
        return
    except SlackApiError as e:
        log.warning(f"Slack upload of {path.name} failed ({e.response['error']}); posting its text in the thread instead")
    _thread(channel, ts, _sections(path.read_text()))


def _thread(channel: str, ts: str, parts: list[str]) -> None:
    """Posts each part as a reply in the thread of the message `ts`, split to Slack's section limit."""
    for part in parts:
        for i in range(0, len(part), _SECTION_MAX_CHARS):
            chunk = part[i:i + _SECTION_MAX_CHARS]
            try:
                _client().chat_postMessage(channel=channel, thread_ts=ts, text=chunk,
                                           blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": chunk}}])
            except SlackApiError as e:
                log.error(f"Slack thread reply in {channel} failed: {e.response['error']}")


def _sections(markdown: str) -> list[str]:
    """A markdown file split at its H2 headings, one part per section."""
    head, *rest = ("\n" + markdown).split("\n## ")
    return ([head.strip()] if head.strip() else []) + [f"## {p.strip()}" for p in rest]


def _text(s: str) -> str:
    """Section text, cut to Slack's limit."""
    return s if len(s) <= _SECTION_MAX_CHARS else s[:_SECTION_MAX_CHARS] + "\n…(cut; see the files on GitHub)"


def _outputs(slug: str) -> Path:
    return ROOT / f"{slug}-output"


def _outputs_link(slug: str) -> str:
    if not settings.github_repo:
        return f"`{slug}-output/`"
    return f"<https://github.com/{settings.github_repo}/tree/{settings.github_branch}/{slug}-output|{slug}-output on GitHub>"


def notify_new_drafts(pages: list[ContentPage]) -> None:
    """Posts a message listing new draft opportunities for review."""
    if not pages:
        return

    rows = []
    for p in pages:
        opp = p.opportunity
        emoji = {"how-to": "🛠️", "guide": "📖", "listicle": "📝", "opinion": "💬", "comparison": "⚔️", "update": "🔄"}.get(
            opp.page_type.value, "✍️"
        )
        rows.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{emoji} *{opp.proposed_title}*\n"
                        f"Keyword: `{opp.keyword}` · {opp.monthly_volume:,} mo/searches · "
                        f"Score: {opp.priority_score:.1f}\n"
                        f"_{opp.rationale}_"
                    ),
                },
            }
        )
        rows.append({"type": "divider"})

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🤖 {len(pages)} new content opportunities"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "These posts have been generated and staged as Sanity drafts.",
            },
        },
        {"type": "divider"},
        *rows,
    ]

    _post(settings.slack_content_channel, blocks, text=f"{len(pages)} new content opportunities ready for review")


def notify_staged(page: ContentPage, spent: str = "") -> None:
    """Notifies that a post is staged as a Sanity draft and ready for review, with the run's report:
    the cost, any larger errors, the em dash report, and the to-do list. The graphic suggestions
    go in the message's thread, as a file, or as text when the upload fails."""
    opp = page.opportunity
    content = page.content
    slug = opp.id
    out = _outputs(slug)
    draft_link = f"<{page.sanity_draft_url}|Open in Studio>" if page.sanity_draft_url else page.sanity_document_id
    larger = (out / f"{slug}-larger-errors.md").read_text().strip() if (out / f"{slug}-larger-errors.md").exists() else ""
    em = (out / f"{slug}-em-dashes.md").read_text().strip() if (out / f"{slug}-em-dashes.md").exists() else ""
    todos = "\n".join(f"• {t['item']}" for t in page.todos) or "None."
    graphics = out / f"{slug}-graphics.md"
    places = graphics.read_text().count("\n## ") if graphics.exists() else 0
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "✅ Draft staged in Sanity"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Post:*\n{opp.proposed_title}"},
                {"type": "mrkdwn", "text": f"*Keyword:*\n{opp.keyword}"},
                {"type": "mrkdwn", "text": f"*Type:*\n{opp.page_type.value.capitalize()}"},
                {"type": "mrkdwn", "text": f"*Draft:*\n{draft_link}"},
                {"type": "mrkdwn", "text": f"*Words:*\n{content.word_count:,}"},
                {"type": "mrkdwn", "text": f"*Cost:*\n{spent or 'not recorded'}"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": _text(f"*Larger errors:*\n{larger or 'None reported.'}")}},
        {"type": "section", "text": {"type": "mrkdwn", "text": _text(f"*Em dashes:*\n{em or 'No section is over the limit.'}")}},
        {"type": "section", "text": {"type": "mrkdwn", "text": _text(f"*To-do:*\n{todos}")}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Graphic suggestions:* {places} place(s), in this message's thread\n"
                    f"*Header image alt text:* {content.main_image_alt or '_none_'}\n"
                    f"*Files:* {_outputs_link(slug)}\n"
                    f"*Live URL once published:* {page.live_url}"
                ),
            },
        },
    ]
    ts = _post(settings.slack_content_channel, blocks, text=f"Draft staged: {opp.proposed_title}")
    _upload(settings.slack_content_channel, graphics, f"Graphic suggestions: {opp.proposed_title}", ts)


def notify_stopped(page: ContentPage, done: list[str], spent: str) -> None:
    """Notifies that a post stopped before its last step and was not staged, and why. The next
    run resumes it from its last finished step."""
    opp = page.opportunity
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "⏸️ Post stopped before staging"}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Post:* {opp.proposed_title}\n"
                    f"*Finished steps:* {', '.join(done) or 'none'}\n"
                    f"*Cost so far:* {spent}\n"
                    "The check loops stop once a post costs more than the cost ceiling, or a step stops partway. "
                    "Nothing was staged to Sanity. The next run resumes this post from its last finished step.\n"
                    f"*Files:* {_outputs_link(opp.id)}"
                ),
            },
        },
    ]
    _post(settings.slack_content_channel, blocks, text=f"Post stopped before staging: {opp.proposed_title}")


def notify_larger_error(page: ContentPage) -> None:
    """Posts each larger error the content check reported, with both statements quoted as the
    fixer wrote them, puts the draft in the message's thread (as a file, or as text when the upload
    fails), and asks whether to redraft the article. The engine can only send to Slack, so the
    answer comes through a Claude session."""
    opp = page.opportunity
    out = _outputs(opp.id)
    larger = out / f"{opp.id}-larger-errors.md"
    if not larger.exists() or not larger.read_text().strip():
        return
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "⚠️ Larger error in a staged draft"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Post:* {opp.proposed_title}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": _text(larger.read_text().strip())}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Do you want to redraft this article?* The draft is in this message's thread."}},
    ]
    ts = _post(settings.slack_content_channel, blocks, text=f"Larger error: {opp.proposed_title}")
    _upload(settings.slack_content_channel, out / f"{opp.id}.md", f"Draft: {opp.proposed_title}", ts)


def notify_competitor_threat(competitor: str, keyword: str, their_rank: int, traffic_delta: int) -> None:
    """Fires to the alerts channel when a competitor is rapidly gaining on a keyword."""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚨 Competitor gaining traction"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Competitor:*\n{competitor}"},
                {"type": "mrkdwn", "text": f"*Keyword:*\n`{keyword}`"},
                {"type": "mrkdwn", "text": f"*Their rank:*\n#{their_rank}"},
                {"type": "mrkdwn", "text": f"*Traffic delta (30d):*\n+{traffic_delta:,} visits"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "A comparison page opportunity has been added to the content calendar.",
            },
        },
    ]
    _post(settings.slack_alerts_channel, blocks, text=f"Competitor threat: {competitor} gaining on '{keyword}'")


# Slack section blocks cap out at 3000 chars of text.
_RUN_REPORT_MAX_CHARS = 2900


def notify_run_report(job: str, lines: list[str], ok: bool = True) -> None:
    """Posts the captured log of one scheduled run (run/index) to the report channel —
    Lambda only surfaces logs in CloudWatch otherwise, so this is the per-execution
    visibility in the channel people actually watch."""
    icon = "✅" if ok else "❌"
    body = "\n".join(f"• {line}" for line in lines) if lines else "_(nothing logged)_"
    if len(body) > _RUN_REPORT_MAX_CHARS:
        body = body[:_RUN_REPORT_MAX_CHARS] + "\n…(truncated — see CloudWatch for the full run)"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{icon} blog-bot-{job} run report"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": body},
        },
    ]
    _post(
        settings.slack_report_channel or settings.slack_content_channel,
        blocks,
        text=f"blog-bot-{job} run report",
    )
