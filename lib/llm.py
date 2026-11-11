"""
Claude wrapper with tool-use for guaranteed structured outputs and prompt caching.

Tool use guarantees the response matches the schema — no more fragile JSON parsing.
Cache control on stable system content cuts cost on repeat runs.
"""

import threading
import time
from typing import Any, List, Union
import anthropic

from config.settings import settings
from lib.logging import get


log = get(__name__)

MODEL = "claude-sonnet-4-6"

# Dollars per million tokens for MODEL, and per web search.
PRICE = {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30, "search": 10.0 / 1000 * 1_000_000}
USAGE = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0, "search": 0}
_usage_lock = threading.Lock()


def reset_usage() -> None:
    with _usage_lock:
        for k in USAGE:
            USAGE[k] = 0


def _record_usage(usage, searches: int = 0) -> None:
    with _usage_lock:
        USAGE["input"] += usage.input_tokens
        USAGE["output"] += usage.output_tokens
        USAGE["cache_write"] += getattr(usage, "cache_creation_input_tokens", 0) or 0
        USAGE["cache_read"] += getattr(usage, "cache_read_input_tokens", 0) or 0
        USAGE["search"] += searches


def cost() -> float:
    """Dollars spent since reset_usage(), from USAGE and PRICE."""
    with _usage_lock:
        return sum(USAGE[k] * PRICE[k] / 1_000_000 for k in USAGE)


def usage_line() -> str:
    with _usage_lock:
        u = dict(USAGE)
    return (f"${cost():.2f}: {u['input']} in, {u['output']} out, {u['cache_write']} cache written, "
            f"{u['cache_read']} cache read, {u['search']} searches")


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


RETRY_WAITS = (15, 60, 180)   # seconds before the second, third, and fourth attempt


def _retryable(e: Exception) -> bool:
    """A dropped or reset connection, a timeout, a rate limit, or a server or overload error. The
    HTTP library's transport errors are matched by class name, because the anthropic package's
    HTTP library has changed names (httpx, httpx2)."""
    if isinstance(e, anthropic.APIConnectionError) or any(c.__name__ == "TransportError" for c in type(e).__mro__):
        return True
    if isinstance(e, anthropic.APIStatusError):
        status = getattr(e, "status_code", 0) or 0
        return status == 429 or status >= 500 or "overloaded" in str(e).lower()
    return False


def _with_retries(call, what: str):
    """Runs `call`, and runs it again after each wait in RETRY_WAITS when it fails with an error
    a later attempt can get past."""
    for attempt, wait in enumerate((*RETRY_WAITS, None), 1):
        try:
            return call()
        except Exception as e:
            if wait is None or not _retryable(e):
                raise
            log.warning(f"{what} failed on attempt {attempt} ({type(e).__name__}: {e}); trying again in {wait}s")
            time.sleep(wait)


def structured_call(
    *,
    system: Union[str, List[dict]],
    user: str,
    tool_name: str,
    tool_description: str,
    input_schema: dict,
    max_tokens: int = 32000,
    cache_system: bool = True,
    thinking: bool = False,
) -> dict:
    """
    Calls Claude and forces it to invoke a tool matching the schema.
    Returns the tool input dict — guaranteed to match input_schema.

    If `cache_system` is True, the system prompt is marked with cache_control so
    repeat invocations with the same system content hit the cache (5min TTL).
    """
    if isinstance(system, str):
        system_blocks = [
            {
                "type": "text",
                "text": system,
                **({"cache_control": {"type": "ephemeral"}} if cache_system else {}),
            }
        ]
    else:
        system_blocks = system

    tools = [
        {
            "name": tool_name,
            "description": tool_description,
            "input_schema": input_schema,
        }
    ]

    # Streamed, because the API refuses a non-streaming request whose max_tokens could
    # take longer than ten minutes to produce. The stream is only read to the end.
    def call():
        with _client().messages.stream(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_blocks,
            tools=tools,
            # Forced, so the model writes nothing before the call; thinking cannot be combined with a forced tool.
            tool_choice={"type": "auto"} if thinking else {"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user}],
            **({"thinking": {"type": "adaptive"}} if thinking else {}),
        ) as stream:
            return stream.get_final_message()

    response = _with_retries(call, f"Model call for '{tool_name}'")

    # Log cache stats if present
    usage = response.usage
    _record_usage(usage)
    if hasattr(usage, "cache_read_input_tokens"):
        read = getattr(usage, "cache_read_input_tokens", 0) or 0
        write = getattr(usage, "cache_creation_input_tokens", 0) or 0
        if read or write:
            log.debug(f"Cache: {read} read, {write} written, {usage.input_tokens} in, {usage.output_tokens} out")

    log.info(f"Structured call: stop={response.stop_reason}, {usage.input_tokens} in, {usage.output_tokens} out")
    if response.stop_reason == "max_tokens":
        raise RuntimeError(f"Response cut off at max_tokens={max_tokens} before the '{tool_name}' call completed")
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            missing = [k for k in input_schema.get("required", []) if k not in block.input]
            if missing:
                raise RuntimeError(f"'{tool_name}' call is missing required fields: {missing}")
            return block.input

    raise RuntimeError(f"Claude did not call the expected tool '{tool_name}'")


def research_call(*, system: str, user: str, max_searches: int, max_tokens: int, blocked_domains: list[str] | None = None,
                  allowed_domains: list[str] | None = None) -> dict:
    """
    Calls Claude with the server-side web search tool and returns
    {"text", "searches", "input_tokens", "output_tokens"}.

    Spend is capped by max_searches (the tool's max_uses), max_tokens on each response,
    and low effort. A turn the server pauses is resumed at most three times.
    The search never returns results from blocked_domains. With allowed_domains, it returns
    results only from those; the search tool takes one or the other, not both.
    """
    client = _client()
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": max_searches, "allowed_callers": ["direct"]}]
    if allowed_domains:
        tools[0]["allowed_domains"] = allowed_domains
    elif blocked_domains:
        tools[0]["blocked_domains"] = blocked_domains
    messages = [{"role": "user", "content": user}]
    searches = input_tokens = output_tokens = 0
    # Streamed, like structured_call, because the API refuses a non-streaming request whose
    # max_tokens could take longer than ten minutes to produce (a resource article's 32,000).
    def call():
        with client.messages.stream(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
            output_config={"effort": "low"},
        ) as stream:
            return stream.get_final_message()

    for _ in range(4):
        response = _with_retries(call, "Research call")
        usage = response.usage
        input_tokens += usage.input_tokens
        output_tokens += usage.output_tokens
        server_use = getattr(usage, "server_tool_use", None)
        before = searches
        if server_use is not None:
            searches = getattr(server_use, "web_search_requests", None) or searches
        _record_usage(usage, searches - before)
        if response.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": response.content})

    text = "\n".join(block.text for block in response.content if block.type == "text").strip()
    log.info(f"Research call: {searches} searches, {input_tokens} in, {output_tokens} out, stop={response.stop_reason}")
    return {"text": text, "searches": searches, "input_tokens": input_tokens, "output_tokens": output_tokens, "stop": response.stop_reason}
