from __future__ import annotations

import hashlib
import json
import logging
import os

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from google.cloud import pubsub_v1
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models.runs import Run

app = FastAPI(title="Arc Reactor Weblog Receiver")
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

GCP_PROJECT = os.environ.get("GCP_PROJECT", "")
PUBSUB_TOPIC = os.environ.get("PUBSUB_TOPIC", "arc-reactor-weblog-events")
publisher = pubsub_v1.PublisherClient()
TOPIC_PATH = publisher.topic_path(GCP_PROJECT, PUBSUB_TOPIC)


async def get_db_session():
    async with async_session() as session:
        yield session


class WeblogEvent(BaseModel):
    runName: str
    runId: str
    event: str
    utcTime: str
    trace: dict | None = None
    metadata: dict | None = None


@app.post("/weblog/{run_id}/{secret}")
async def receive_weblog_event(
    run_id: str,
    secret: str,
    event: WeblogEvent,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(Run).where(Run.run_id == run_id))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    if secret_hash != run.weblog_secret_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret",
        )

    if run.status in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Run already terminated",
        )

    message_data = {
        "arc_run_id": run_id,
        "event": event.model_dump(),
    }

    future = publisher.publish(
        TOPIC_PATH,
        data=json.dumps(message_data).encode(),
        ordering_key=run_id,
    )

    background_tasks.add_task(_log_publish_result, future, run_id, event.event)

    return {"status": "accepted"}


def _log_publish_result(future, run_id: str, event_type: str) -> None:
    try:
        message_id = future.result(timeout=10)
        logger.debug(
            "Published weblog event: run=%s, event=%s, msg=%s",
            run_id,
            event_type,
            message_id,
        )
    except Exception as exc:
        logger.error(
            "Failed to publish weblog event: run=%s, event=%s, error=%s",
            run_id,
            event_type,
            exc,
        )


@app.get("/health")
async def health():
    return {"status": "healthy"}
