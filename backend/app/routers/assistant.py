"""Claude-powered endpoints: grounded NL assistant + per-hotspot enforcement briefs."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .. import llm, prompts

router = APIRouter(prefix="/api", tags=["assistant"])


class AssistantQuery(BaseModel):
    query: str


def _store(request: Request):
    return request.app.state.store


@router.post("/assistant")
def assistant(request: Request, body: AssistantQuery):
    store = _store(request)
    ctx, candidate_ids = prompts.build_assistant_context(store, body.query)
    system = prompts.ASSISTANT_SYSTEM.format(context=ctx)
    answer = llm.assistant_answer(system, body.query)
    return {"answer": answer, "used_hotspot_ids": candidate_ids, "model": llm.ASSISTANT_MODEL}


@router.post("/assistant/stream")
def assistant_stream(request: Request, body: AssistantQuery):
    store = _store(request)
    ctx, candidate_ids = prompts.build_assistant_context(store, body.query)
    system = prompts.ASSISTANT_SYSTEM.format(context=ctx)

    def gen():
        # first line is a JSON header with the hotspot ids to highlight, then text
        import json
        yield json.dumps({"used_hotspot_ids": candidate_ids}) + "\n"
        for chunk in llm.assistant_stream(system, body.query):
            yield chunk

    return StreamingResponse(gen(), media_type="text/plain")


@router.post("/brief/{hid}")
def brief(request: Request, hid: str):
    store = _store(request)
    user = prompts.build_brief_user(store, hid)
    if user is None:
        raise HTTPException(404, f"hotspot {hid} not found")
    md = llm.generate_brief(prompts.BRIEF_SYSTEM, user)
    return {"hotspot_id": hid, "brief_markdown": md, "model": llm.BRIEF_MODEL}
