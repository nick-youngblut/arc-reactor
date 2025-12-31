from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from langchain_core.messages import HumanMessage

from backend.agents.checkpointer import checkpointer_session
from backend.agents.pipeline_agent import PipelineAgent
from backend.agents.streaming import stream_agent_response
from backend.config import settings
from backend.utils.auth import UserContext, verify_iap_jwt

router = APIRouter(tags=["chat"])


def _authenticate_websocket(websocket: WebSocket) -> UserContext:
    jwt_token = websocket.headers.get("X-Goog-IAP-JWT-Assertion")
    if not jwt_token:
        if settings.get("debug", False):
            return UserContext(email="dev@example.com", name="Developer")
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

    claims = verify_iap_jwt(jwt_token)
    email = claims.get("email")
    if not email:
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

    name = claims.get("name", email)
    return UserContext(email=email, name=name)


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        user = _authenticate_websocket(websocket)
    except WebSocketDisconnect:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.send_json({"type": "connected"})

    try:
        while True:
            payload: dict[str, Any] = await websocket.receive_json()
            if payload.get("type") != "message":
                await websocket.send_json({"type": "error", "message": "Invalid message type"})
                continue

            content = payload.get("content")
            if not content:
                await websocket.send_json({"type": "error", "message": "Message content required"})
                continue

            thread_id = payload.get("thread_id") or f"thread-{uuid.uuid4().hex}"
            messages = [HumanMessage(content=content)]
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "user_email": user.email,
                    "user_name": user.name,
                }
            }

            async with checkpointer_session(settings) as checkpointer:
                agent = PipelineAgent.create(settings, checkpointer=checkpointer)
                async for chunk in stream_agent_response(
                    agent.agent,
                    messages,
                    config=config,
                ):
                    await websocket.send_text(chunk)
    except WebSocketDisconnect:
        return
