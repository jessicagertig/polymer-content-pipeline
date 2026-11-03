"""
Slack Handler Lambda
Handles Slack interactivity (button clicks) for the content engine.

Routes (via API Gateway):
  POST /slack/interact - Slack button clicks -> trigger GitHub Action

Buttons:
  resume_<slug>  - "Resume now" on the Stopped message -> content-engine.yml, command resume
  redraft_<slug> - "Redraft" on the Larger error message -> opens a modal for instructions;
                   its submit -> content-engine.yml, command redraft

Env vars:
  SLACK_BOT_TOKEN        - Bot token for opening the modal and posting the confirmation
  SLACK_SIGNING_SECRET   - For verifying Slack requests (HMAC-SHA256)
  SLACK_CHANNEL_ID       - Channel for the redraft confirmation
  GITHUB_TOKEN           - PAT with repo scope for workflow_dispatch
  GITHUB_OWNER           - GitHub repo owner (default: jessicagertig)
  GITHUB_REPO            - GitHub repo name (default: polymer-content-pipeline)
"""

import hashlib
import hmac
import json
import logging
import os
import time
import urllib.parse
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "jessicagertig")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "polymer-content-pipeline")


# ---------------------------------------------------------------------------
# Dispatch table — action_id prefix -> (workflow_file, input_builder_fn)
# ---------------------------------------------------------------------------

_DISPATCH_TABLE = {
    "resume_": lambda v: ("content-engine.yml", {"command": "resume", "slug": v}),
}


def dispatch_for(action_id, value):
    """Match action_id against the dispatch table. Returns (workflow_file, inputs) or None."""
    for prefix, builder in _DISPATCH_TABLE.items():
        if action_id.startswith(prefix):
            return builder(value)
    return None


def lambda_handler(event, context):
    path = event.get("path", "")
    method = event.get("httpMethod", "")

    if method == "POST" and path == "/slack/interact":
        return handle_slack_interact(event)
    else:
        return {"statusCode": 404, "body": json.dumps({"error": "Not found"})}


# ---------------------------------------------------------------------------
# Slack signature verification
# ---------------------------------------------------------------------------

def verify_slack_signature(event):
    """Verify the request came from Slack using HMAC-SHA256."""
    signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "")
    if not signing_secret:
        logger.error("SLACK_SIGNING_SECRET not set")
        return False

    headers = event.get("headers", {})
    timestamp = headers.get("X-Slack-Request-Timestamp") or headers.get("x-slack-request-timestamp", "")
    signature = headers.get("X-Slack-Signature") or headers.get("x-slack-signature", "")

    if not timestamp or not signature:
        return False

    # Reject requests older than 5 minutes
    if abs(time.time() - int(timestamp)) > 300:
        return False

    body = event.get("body", "")
    sig_basestring = f"v0:{timestamp}:{body}"
    computed = "v0=" + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


# ---------------------------------------------------------------------------
# POST /slack/interact
# ---------------------------------------------------------------------------

def handle_slack_interact(event):
    if not verify_slack_signature(event):
        return {"statusCode": 401, "body": json.dumps({"error": "Invalid signature"})}

    body = event.get("body", "")
    params = urllib.parse.parse_qs(body)
    payload = json.loads(params.get("payload", ["{}"])[0])

    payload_type = payload.get("type", "")

    if payload_type == "view_submission":
        return handle_redraft_submission(payload)

    action = (payload.get("actions") or [{}])[0]
    if not action:
        return {"statusCode": 400, "body": json.dumps({"error": "No action found"})}

    action_id = action.get("action_id", "")
    value     = action.get("value", "")
    user_name = payload.get("user", {}).get("name", "someone")

    if action_id.startswith("redraft_"):
        trigger_id = payload.get("trigger_id", "")
        ok = open_redraft_modal(trigger_id, value)
        if not ok:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "response_type": "ephemeral",
                    "text": "Failed to open redraft modal.",
                }),
            }
        return {"statusCode": 200, "body": ""}

    dispatch = dispatch_for(action_id, value)
    if dispatch is None:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_type": "ephemeral",
                "text": f"Unknown action: {action_id}. Nothing dispatched.",
            }),
        }

    workflow_file, inputs = dispatch
    ok, detail = trigger_github_action(workflow_file, inputs)
    if not ok:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_type": "in_channel",
                "text": (
                    f"Failed to trigger {workflow_file}. Something went wrong — check CloudWatch logs.\n"
                    f"```{detail}```"
                ),
            }),
        }
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "response_type": "in_channel",
            "text": f"Dispatched {workflow_file} (by {user_name}).",
        }),
    }


# ---------------------------------------------------------------------------
# Redraft modal
# ---------------------------------------------------------------------------

def open_redraft_modal(trigger_id, slug):
    """Open a Slack modal so the user can type the instructions for a redraft.

    `slug` is stored as private_metadata so it round-trips back on view_submission.
    """
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    if not token or not trigger_id:
        logger.error("Missing SLACK_BOT_TOKEN or trigger_id")
        return False

    view = {
        "type": "modal",
        "callback_id": "redraft_submit",
        "private_metadata": slug,
        "title": {"type": "plain_text", "text": "Redraft"},
        "submit": {"type": "plain_text", "text": "Redraft"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "instructions_block",
                "label": {
                    "type": "plain_text",
                    "text": f"Instructions for redrafting {slug}",
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "instructions_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "What to change in the article",
                    },
                },
            },
        ],
    }

    data = json.dumps({"trigger_id": trigger_id, "view": view}).encode()
    req = urllib.request.Request(
        "https://slack.com/api/views.open",
        data=data,
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json; charset=utf-8")

    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        if not result.get("ok"):
            logger.error(f"views.open error: {result.get('error')} (response_metadata={result.get('response_metadata')})")
            return False
        return True
    except Exception as e:
        logger.error(f"views.open failed: {e}")
        return False


def handle_redraft_submission(payload):
    """Handle the modal submit: extract the instructions + slug, dispatch the redraft."""
    view = payload.get("view", {})
    if view.get("callback_id") != "redraft_submit":
        return {"statusCode": 200, "body": ""}

    slug = view.get("private_metadata", "")

    state_values = view.get("state", {}).get("values", {})
    instructions = (
        state_values.get("instructions_block", {})
        .get("instructions_input", {})
        .get("value", "")
        or ""
    ).strip()

    if not slug or not instructions:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_action": "errors",
                "errors": {"instructions_block": "Please enter instructions."},
            }),
        }

    ok, detail = trigger_github_action(
        "content-engine.yml",
        {"command": "redraft", "slug": slug, "instructions": instructions},
    )
    if not ok:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_action": "errors",
                "errors": {
                    "instructions_block": (
                        "Failed to trigger the redraft. Something went wrong — check CloudWatch logs. "
                        f"{detail}"
                    ),
                },
            }),
        }

    user_name = payload.get("user", {}).get("name", "someone")
    preview = (instructions[:120] + "…") if len(instructions) > 120 else instructions
    post_plain_message_to_channel(
        f"Dispatched content-engine.yml redraft for {slug} (by {user_name}).\n> {preview}"
    )

    # Empty 200 closes the modal.
    return {"statusCode": 200, "body": ""}


def post_plain_message_to_channel(text):
    """Post a simple text message to SLACK_CHANNEL_ID. Used for the redraft dispatch confirmation."""
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    channel = os.environ.get("SLACK_CHANNEL_ID", "")
    if not token or not channel:
        logger.error("SLACK_BOT_TOKEN or SLACK_CHANNEL_ID not set")
        return False

    data = json.dumps({"channel": channel, "text": text, "unfurl_links": False, "unfurl_media": False}).encode()
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=data,
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        if not result.get("ok"):
            logger.error(f"chat.postMessage error: {result.get('error')}")
            return False
        return True
    except Exception as e:
        logger.error(f"chat.postMessage failed: {e}")
        return False


def trigger_github_action(workflow_file, inputs):
    """Trigger workflow_file via GitHub API workflow_dispatch.

    Returns (ok: bool, detail: str). On failure, detail is a best-effort
    capture of HTTP status + GitHub response body + payload sent.
    """
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        logger.error("GITHUB_TOKEN not set")
        return False, "GITHUB_TOKEN env var not set on the Lambda."

    url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/actions/workflows/{workflow_file}/dispatches"
    )
    payload = {"ref": "main", "inputs": inputs}
    data = json.dumps(payload).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "polymer-content-engine-slack-lambda")
    req.add_header("Content-Type", "application/json")

    try:
        resp = urllib.request.urlopen(req)
        logger.info(f"GitHub dispatch triggered ({workflow_file}): {resp.status}")
        return True, ""
    except urllib.error.HTTPError as e:
        try:
            body_text = e.read().decode("utf-8", errors="replace")
        except Exception:
            body_text = "<unreadable response body>"
        detail = f"HTTP {e.code} from GitHub. Response: {body_text}. Payload sent: {json.dumps(payload)}"
        logger.error(detail)
        return False, detail
    except Exception as e:
        detail = f"{type(e).__name__}: {e}. URL: {url}. Payload: {json.dumps(payload)}"
        logger.error(detail)
        return False, detail
