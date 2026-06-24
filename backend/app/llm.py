"""Groq SDK wrappers (OpenAI-compatible chat completions).
Assistant -> Llama 3.1 8B instant (fast, streamed);
enforcement briefs -> Llama 3.3 70B versatile (quality).

Requires GROQ_API_KEY in the environment."""
from __future__ import annotations
import os
from typing import Iterator

from groq import Groq

ASSISTANT_MODEL = "llama-3.1-8b-instant"
BRIEF_MODEL = "llama-3.3-70b-versatile"

_client: Groq | None = None


def _get_client() -> Groq | None:
    global _client
    if not os.environ.get("GROQ_API_KEY"):
        return None
    if _client is None:
        _client = Groq()
    return _client


def has_key() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def _messages(system: str, user: str) -> list[dict]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def assistant_answer(system: str, query: str) -> str:
    client = _get_client()
    if client is None:
        return _no_key_msg()
    resp = client.chat.completions.create(
        model=ASSISTANT_MODEL, max_tokens=1024,
        messages=_messages(system, query),
    )
    return (resp.choices[0].message.content or "").strip()


def assistant_stream(system: str, query: str) -> Iterator[str]:
    client = _get_client()
    if client is None:
        yield _no_key_msg()
        return
    stream = client.chat.completions.create(
        model=ASSISTANT_MODEL, max_tokens=1024,
        messages=_messages(system, query), stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def generate_brief(system: str, user: str) -> str:
    client = _get_client()
    if client is None:
        return _no_key_msg()
    resp = client.chat.completions.create(
        model=BRIEF_MODEL, max_tokens=2000,
        messages=_messages(system, user),
    )
    return (resp.choices[0].message.content or "").strip()


def _no_key_msg() -> str:
    return ("⚠️ The AI assistant is not configured. Set `GROQ_API_KEY` in the environment "
            "and restart the backend to enable the AI assistant and enforcement briefs.")
