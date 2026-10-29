"""
Claude wrapper with tool-use for guaranteed structured outputs and prompt caching.

Tool use guarantees the response matches the schema — no more fragile JSON parsing.
Cache control on stable system content cuts cost on repeat runs.
"""

from typing import Any, List, Union
import anthropic

from config.settings import settings
from lib.logging import get


log = get(__name__)

MODEL = "claude-sonnet-5-5"


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def structured_call(
    *,
    system: Union[str, List[dict]],
    user: str,
    tool_name: str,
    tool_description: str,
    input_schema: dict,
    max_tokens: int = 16000,
    cache_system: bool = True,
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

    response = _client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_blocks,
        tools=tools,
        tool_choice={"type": "auto"},   # forcing a tool is rejected on this model; the user prompt names it
        messages=[{"role": "user", "content": user}],
    )

    # Log cache stats if present
    usage = response.usage
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


def research_call(*, system: str, user: str, max_searches: int, max_tokens: int) -> dict:
    """
    Calls Claude with the server-side web search tool and returns
    {"text", "searches", "input_tokens", "output_tokens"}.

    Spend is capped by max_searches (the tool's max_uses), max_tokens on each response,
    and low effort. A turn the server pauses is resumed at most three times.
    """
    client = _client()
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": max_searches}]
    messages = [{"role": "user", "content": user}]
    searches = input_tokens = output_tokens = 0
    for _ in range(4):
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
            output_config={"effort": "low"},
        )
        usage = response.usage
        input_tokens += usage.input_tokens
        output_tokens += usage.output_tokens
        server_use = getattr(usage, "server_tool_use", None)
        if server_use is not None:
            searches = getattr(server_use, "web_search_requests", None) or searches
        if response.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": response.content})

    text = "\n".join(block.text for block in response.content if block.type == "text").strip()
    log.info(f"Research call: {searches} searches, {input_tokens} in, {output_tokens} out, stop={response.stop_reason}")
    return {"text": text, "searches": searches, "input_tokens": input_tokens, "output_tokens": output_tokens}
