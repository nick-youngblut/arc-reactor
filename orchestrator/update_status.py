from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

try:
    import psycopg2
    from psycopg2.extras import Json
except Exception:  # pragma: no cover - handled at runtime
    psycopg2 = None  # type: ignore
    Json = None  # type: ignore


logger = logging.getLogger("arc-reactor.orchestrator")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update run status in PostgreSQL")
    parser.add_argument("run_id")
    parser.add_argument("status")
    parser.add_argument("--started_at")
    parser.add_argument("--completed_at")
    parser.add_argument("--failed_at")
    parser.add_argument("--cancelled_at")
    parser.add_argument("--error_message")
    parser.add_argument("--error_task")
    parser.add_argument("--exit_code", type=int)
    parser.add_argument("--metrics")
    return parser.parse_args(argv)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _maybe_timestamp(value: str | None, fallback: datetime | None) -> datetime | None:
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return fallback
    return fallback


def _build_updates(args: argparse.Namespace) -> tuple[list[str], dict[str, Any]]:
    updates = ["status = %(status)s", "updated_at = NOW()"]
    params: dict[str, Any] = {
        "run_id": args.run_id,
        "status": args.status,
    }

    status = args.status.lower()
    now = _now()

    started_at = _maybe_timestamp(args.started_at, now if status == "running" else None)
    completed_at = _maybe_timestamp(args.completed_at, now if status == "completed" else None)
    failed_at = _maybe_timestamp(args.failed_at, now if status == "failed" else None)
    cancelled_at = _maybe_timestamp(args.cancelled_at, now if status == "cancelled" else None)

    if started_at is not None:
        updates.append("started_at = %(started_at)s")
        params["started_at"] = started_at
    if completed_at is not None:
        updates.append("completed_at = %(completed_at)s")
        params["completed_at"] = completed_at
    if failed_at is not None:
        updates.append("failed_at = %(failed_at)s")
        params["failed_at"] = failed_at
    if cancelled_at is not None:
        updates.append("cancelled_at = %(cancelled_at)s")
        params["cancelled_at"] = cancelled_at

    if args.exit_code is not None:
        updates.append("exit_code = %(exit_code)s")
        params["exit_code"] = args.exit_code
    if args.error_message is not None:
        updates.append("error_message = %(error_message)s")
        params["error_message"] = args.error_message
    if args.error_task is not None:
        updates.append("error_task = %(error_task)s")
        params["error_task"] = args.error_task
    if args.metrics is not None:
        try:
            metrics = json.loads(args.metrics)
        except json.JSONDecodeError:
            metrics = args.metrics
        updates.append("metrics = %(metrics)s")
        params["metrics"] = Json(metrics) if Json is not None else metrics

    return updates, params


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL is not set")
        return 1
    if psycopg2 is None:
        logger.error("psycopg2 is not available")
        return 1

    args = _parse_args(argv)
    updates, params = _build_updates(args)

    query = f"UPDATE runs SET {', '.join(updates)} WHERE run_id = %(run_id)s"

    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.rowcount == 0:
                    logger.error("Run %s not found", args.run_id)
                    conn.rollback()
                    return 1
        logger.info("Updated run %s to status %s", args.run_id, args.status)
        return 0
    except Exception as exc:
        logger.exception("Failed to update run status: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
