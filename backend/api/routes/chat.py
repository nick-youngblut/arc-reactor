from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from langchain_core.messages import HumanMessage
from psycopg_pool import PoolTimeout

from backend.agents.pipeline_agent import PipelineAgent
from backend.agents.streaming import stream_agent_response
from backend.config import settings
from backend.utils.auth import UserContext, verify_iap_jwt

logger = logging.getLogger(__name__)
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
    """WebSocket endpoint for AI agent chat."""
    await websocket.accept()
    logger.info("WebSocket accepted, authenticating...")
    try:
        user = _authenticate_websocket(websocket)
        logger.info("Authenticated user: %s", user.email)
    except WebSocketDisconnect:
        logger.warning("Authentication failed - closing connection")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.send_json({"type": "connected"})
    logger.info("Sent 'connected' message, initializing agent...")

    try:
        checkpointer_service = websocket.app.state.checkpointer_service
        agent = PipelineAgent.create(
            settings,
            checkpointer=checkpointer_service.checkpointer,
        )
        logger.info("Agent initialized successfully")
    except Exception as exc:
        logger.exception("Failed to initialize agent: %s", exc)
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Failed to initialize agent: {exc}",
            }
        )
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    logger.info("Waiting for messages...")
    try:
        while True:
            payload: dict[str, Any] = await websocket.receive_json()
            logger.info("Received message: type=%s", payload.get("type"))
            if payload.get("type") != "message":
                await websocket.send_json({"type": "error", "message": "Invalid message type"})
                continue

            content = payload.get("content")
            if not content:
                await websocket.send_json({"type": "error", "message": "Message content required"})
                continue

            logger.info("Processing message: %s", content[:100] if len(content) > 100 else content)
            thread_id = payload.get("thread_id") or f"thread-{uuid.uuid4().hex}"
            messages = [HumanMessage(content=content)]
            config = {
                "recursion_limit": 100,  # Allow more iterations for complex agentic tasks
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": user.email,
                    "user_email": user.email,
                    "user_name": user.name,
                    "benchling_service": websocket.app.state.benchling_service,
                    "storage_service": websocket.app.state.storage_service,
                    "database_service": websocket.app.state.database_service,
                },
            }

            try:
                chunk_count = 0
                async for chunk in stream_agent_response(
                    agent.agent,
                    messages,
                    config=config,
                ):
                    chunk_count += 1
                    await websocket.send_text(chunk)
                logger.info("Streamed %d chunks", chunk_count)
            except PoolTimeout:
                logger.error("Pool timeout during streaming")
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Service temporarily unavailable. Please try again.",
                    }
                )
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
        return
