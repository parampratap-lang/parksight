"""Anthropic SDK wrappers. Assistant -> Sonnet 4.6 (fast, streamed);
enforcement briefs -> Opus 4.8 (quality)."""
from __future__ import annotations
import os
from typing import Iterator

import anthropic

ASSISTANT_MODEL = "claude-sonnet-4-6"
BRIEF_MODEL = "claude-opus-4-8"

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def has_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def assistant_answer(system: str, query: str) -> str:
    client = _get_client()
    if client is None:
        return _no_key_msg()
    msg = client.messages.create(
        model=ASSISTANT_MODEL, max_tokens=1024, system=system,
        messages=[{"role": "user", "content": query}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


def assistant_stream(system: str, query: str) -> Iterator[str]:
    client = _get_client()
    if client is None:
        yield _no_key_msg()
        return
    with client.messages.stream(
        model=ASSISTANT_MODEL, max_tokens=1024, system=system,
        messages=[{"role": "user", "content": query}],
    ) as stream:
        for text in stream.text_stream:
            yield text


def generate_brief(system: str, user: str) -> str:
    client = _get_client()
    if client is None:
        return _no_key_msg()
    # stream to stay under HTTP timeouts and collect the full markdown
    with client.messages.stream(
        model=BRIEF_MODEL, max_tokens=2000, system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        msg = stream.get_final_message()
        return "".join(b.text for b in msg.content if b.type == "text").strip()


def _no_key_msg() -> str:
    return ("⚠️ Claude is not configured. Set `ANTHROPIC_API_KEY` in the environment "
            "and restart the backend to enable the AI assistant and enforcement briefs.")
