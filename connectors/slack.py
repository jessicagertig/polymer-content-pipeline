"""Slack connector — notifications and run reports."""

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config.settings import settings
from lib.logging import get
from models.content import ContentPage


log = get(__name__)


def _client() -> WebClient:
    return WebClient(token=settings.slack_bot_token)


def _post(channel: str, blocks: list, text: str = "") -> None:
    if not settings.slack_bot_token or settings.slack_bot_token.startswith("xoxb-..."):
        log.info(f"Slack not configured — skipping post to {channel}: {text}")
        return
    try:
        _client().chat_postMessage(channel=channel, blocks=blocks, text=text)
    except SlackApiError as e:
        log.error(f"Slack post to {channel} failed: {e.response['error']}")


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


def notify_staged(page: ContentPage) -> None:
    """Notifies that a post is staged as a Sanity draft and ready for review."""
    opp = page.opportunity
    content = page.content
    draft_link = f"<{page.sanity_draft_url}|Open in Studio>" if page.sanity_draft_url else page.sanity_document_id
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
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Header image alt text:* {content.main_image_alt or '_none_'}\n"
                    f"*Live URL once published:* {page.live_url}"
                ),
            },
        },
    ]
    _post(settings.slack_content_channel, blocks, text=f"Draft staged: {opp.proposed_title}")


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
