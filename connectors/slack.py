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
        return _client().chat_postMessage(channel=channel, blocks=blocks, text=text, unfurl_links=False, unfurl_media=False)["ts"]
    except SlackApiError as e:
        log.error(f"Slack post to {channel} failed: {e.response['error']}")
        return ""


def _upload(channel: str, path: Path, title: str, ts: str, last_chars: int = 0) -> None:
    """Attaches a file in the thread of the message `ts`. When the upload fails (the bot needs the
    files:write scope, and the channel setting must be the channel's ID), the file's text is posted
    in the same thread instead, one reply per section; with `last_chars`, only the end of the text."""
    if not _configured() or not ts or not path.exists():
        log.info(f"Slack not configured, no message, or {path.name} missing — skipping upload to {channel}")
        return
    try:
        _client().files_upload_v2(channel=channel, file=str(path), title=title, thread_ts=ts)
        return
    except SlackApiError as e:
        log.warning(f"Slack upload of {path.name} failed ({e.response['error']}); posting its text in the thread instead")
    text = path.read_text()
    _thread(channel, ts, [text[-last_chars:]] if last_chars else _sections(text))


def _thread(channel: str, ts: str, parts: list[str]) -> None:
    """Posts each part as a reply in the thread of the message `ts`, split to Slack's section limit."""
    for part in parts:
        for i in range(0, len(part), _SECTION_MAX_CHARS):
            chunk = part[i:i + _SECTION_MAX_CHARS]
            try:
                _client().chat_postMessage(channel=channel, thread_ts=ts, text=chunk, unfurl_links=False, unfurl_media=False,
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


def _read(path: Path) -> str:
    return path.read_text().strip() if path.exists() else ""


def _header(text: str) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text[:150]}}


def notify_staged(page: ContentPage, spent: str = "") -> None:
    """Posts the review messages for a staged post, each its own message, in this order: the
    summary; the larger errors, when there are any; the fixes (em dashes and the to-do list), when
    there are any; the graphic ideas, with the suggestions in that message's thread; and the
    article, with the article in that message's thread."""
    notify_summary(page, spent)
    notify_larger_error(page)
    notify_fixes(page)
    notify_graphics(page)
    notify_article(page)


def notify_summary(page: ContentPage, spent: str = "") -> None:
    """The post is staged as a Sanity draft: what it is, its cost, and how many review items follow."""
    opp = page.opportunity
    content = page.content
    out = _outputs(opp.id)
    draft_link = f"<{page.sanity_draft_url}|Open in Studio>" if page.sanity_draft_url else page.sanity_document_id
    larger = _read(out / f"{opp.id}-larger-errors.md")
    em_lines = [l for l in _read(out / f"{opp.id}-em-dashes.md").splitlines() if l.startswith("- ")]
    places = _read(out / f"{opp.id}-graphics.md").count("\n## ")
    suspects = len(_read(out / f"{opp.id}-competitor-links.md").splitlines())
    blocks = [
        _header(f"✅ Draft staged: {opp.proposed_title}"),
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Keyword:*\n{opp.keyword}"},
                {"type": "mrkdwn", "text": f"*Type:*\n{opp.page_type.value.capitalize()}"},
                {"type": "mrkdwn", "text": f"*Draft:*\n{draft_link}"},
                {"type": "mrkdwn", "text": f"*Words:*\n{content.word_count:,}"},
                {"type": "mrkdwn", "text": f"*Cost:*\n{spent or 'not recorded'}"},
                {"type": "mrkdwn", "text": f"*Live URL once published:*\n{page.live_url}"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Larger errors:* {'yes, in the next message' if larger else 'none'}\n"
                    f"*Fixes:* {len(page.todos)} to-do item(s), {len(em_lines)} section(s) over the em dash limit, "
                    f"{suspects} link(s) that may go to competitors\n"
                    f"*Graphic ideas:* {places} place(s)\n"
                    f"*Header image alt text:* {content.main_image_alt or '_none_'}"
                ),
            },
        },
    ]
    _post(settings.slack_content_channel, blocks, text=f"Draft staged: {opp.proposed_title}")


def notify_fixes(page: ContentPage) -> None:
    """The em dash report, the to-do list, and the links that may go to competitors, when any of
    them has anything in it."""
    opp = page.opportunity
    em = _read(_outputs(opp.id) / f"{opp.id}-em-dashes.md")
    suspects = _read(_outputs(opp.id) / f"{opp.id}-competitor-links.md")
    if not em and not page.todos and not suspects:
        return
    todos = "\n".join(f"• {t['item']}" for t in page.todos) or "None."
    blocks = [
        _header(f"✏️ Fixes: {opp.proposed_title}"),
        {"type": "section", "text": {"type": "mrkdwn", "text": _text(f"*Em dashes:*\n{em or 'No section is over the limit.'}")}},
        {"type": "section", "text": {"type": "mrkdwn", "text": _text(f"*To-do:*\n{todos}")}},
    ]
    if suspects:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": _text(
            f"*Links that may go to competitors* (keep or remove them in Studio):\n{suspects}")}})
    _post(settings.slack_content_channel, blocks, text=f"Fixes: {opp.proposed_title}")


def notify_graphics(page: ContentPage) -> None:
    """The graphic ideas: a message of its own, with the suggestions in its thread."""
    opp = page.opportunity
    graphics = _outputs(opp.id) / f"{opp.id}-graphics.md"
    if not graphics.exists():
        return
    places = graphics.read_text().count("\n## ")
    blocks = [
        _header(f"🖼️ Graphic ideas: {opp.proposed_title}"),
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{places} place(s), each with two or three options, in this message's thread."}},
    ]
    ts = _post(settings.slack_content_channel, blocks, text=f"Graphic ideas: {opp.proposed_title}")
    _upload(settings.slack_content_channel, graphics, f"Graphic ideas: {opp.proposed_title}", ts)


def notify_article(page: ContentPage) -> None:
    """The article: a message of its own, with the article in its thread."""
    opp = page.opportunity
    article = _outputs(opp.id) / f"{opp.id}.md"
    if not article.exists():
        return
    blocks = [
        _header(f"📄 Article: {opp.proposed_title}"),
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{page.content.word_count:,} words, in this message's thread."}},
    ]
    ts = _post(settings.slack_content_channel, blocks, text=f"Article: {opp.proposed_title}")
    _upload(settings.slack_content_channel, article, f"Article: {opp.proposed_title}", ts)


def notify_stopped(page: ContentPage, done: list[str], spent: str) -> None:
    """Notifies that a post stopped before its last step and was not staged, and why. The next
    run resumes it from its last finished step."""
    opp = page.opportunity
    blocks = [
        _header(f"⏸️ Stopped before staging: {opp.proposed_title}"),
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Finished steps:* {', '.join(done) or 'none'}\n"
                    f"*Cost so far:* {spent}\n"
                    "The check loops stop once a post costs more than the cost ceiling, or a step stops partway. "
                    "Nothing was staged to Sanity. The next run resumes this post from its last finished step, "
                    "or Resume now resumes it right away."
                ),
            },
        },
        {
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "Resume now", "emoji": True},
                "value": opp.id,
                "action_id": f"resume_{opp.id}",
                "style": "primary",
            }],
        },
    ]
    _post(settings.slack_content_channel, blocks, text=f"Stopped before staging: {opp.proposed_title}")


def notify_failed(opp, command: str, step: str, reason: str, spent: str, log_path: Path) -> None:
    """A run failed. For an article: its title, the step it failed at, the reason, the cost so far,
    and a Retry now button; the next run also tries the article again. For a run with no article,
    the command and the reason. The run's log goes in the message's thread."""
    title = opp.proposed_title if opp else f"{command} run"
    lines = ([f"*Failed at:* {step}"] if step else []) + [f"*Reason:* {' '.join(reason.split())[:500]}"]
    if spent:
        lines.append(f"*Cost so far:* {spent}")
    if opp:
        lines.append("Nothing was staged to Sanity. The next run tries this article again, or Retry now tries it right away.")
    blocks = [_header(f"❌ Failed: {title}"), {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}}]
    if opp:
        blocks.append({
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "Retry now", "emoji": True},
                "value": opp.id,
                "action_id": f"resume_{opp.id}",
                "style": "primary",
            }],
        })
    ts = _post(settings.slack_content_channel, blocks, text=f"Failed: {title}")
    _upload(settings.slack_content_channel, log_path, f"Log: {title}", ts, last_chars=_SECTION_MAX_CHARS * 3)


def notify_larger_error(page: ContentPage) -> None:
    """Each larger error the content check reported, with both statements quoted as the fixer
    wrote them, and the question whether to redraft the article. The article itself is in the
    Article message. The Redraft button opens a box for the instructions (lambdas/slack_handler)."""
    opp = page.opportunity
    larger = _read(_outputs(opp.id) / f"{opp.id}-larger-errors.md")
    if not larger:
        return
    blocks = [
        _header(f"⚠️ Larger error: {opp.proposed_title}"),
        {"type": "section", "text": {"type": "mrkdwn", "text": _text(larger)}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Do you want to redraft this article?* The article is in the Article message below."}},
        {
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "Redraft", "emoji": True},
                "value": opp.id,
                "action_id": f"redraft_{opp.id}",
                "style": "primary",
            }],
        },
    ]
    _post(settings.slack_content_channel, blocks, text=f"Larger error: {opp.proposed_title}")


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
