from __future__ import annotations

import uuid
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from backend.agents.checkpointer import checkpointer_session
from backend.agents.pipeline_agent import PipelineAgent
from backend.agents.streaming import stream_agent_response
from backend.config import settings
from backend.dependencies import get_current_user_context
from backend.utils.auth import UserContext

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    type: str = Field(default="message")
    content: str
    thread_id: str | None = None


async def _event_stream(
    messages: list[Any],
    *,
    thread_id: str,
    user: UserContext,
    request: Request,
) -> AsyncIterator[bytes]:
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_email": user.email,
            "user_name": user.name,
            "benchling_service": request.app.state.benchling_service,
            "storage_service": request.app.state.storage_service,
            "database_service": request.app.state.database_service,
        }
    }
    async with checkpointer_session(settings) as checkpointer:
        agent = PipelineAgent.create(settings, checkpointer=checkpointer)
        async for chunk in stream_agent_response(agent.agent, messages, config=config):
            line = f"data: {chunk.rstrip()}\n\n"
            yield line.encode("utf-8")


@router.post("/chat")
async def chat_rest(
    request: ChatRequest,
    http_request: Request,
    user: UserContext = Depends(get_current_user_context),
):
    if request.type != "message":
        return StreamingResponse(
            iter([b'data: 3:"Invalid message type"\n\n']),
            media_type="text/event-stream",
        )

    thread_id = request.thread_id or f"thread-{uuid.uuid4().hex}"
    messages = [HumanMessage(content=request.content)]
    return StreamingResponse(
        _event_stream(
            messages,
            thread_id=thread_id,
            user=user,
            request=http_request,
        ),
        media_type="text/event-stream",
    )
