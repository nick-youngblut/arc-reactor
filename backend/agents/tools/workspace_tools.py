from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from backend.agents.tools.base import get_workspace_context, tool_error_handler


@tool
@tool_error_handler
async def get_current_samplesheet(runtime: Any | None = None) -> str:
    """
    Get the current samplesheet content for the active workspace.

    Returns:
        The latest samplesheet content as a string.
    """
    context = await get_workspace_context(runtime)
    try:
        if not context.service:
            return "Error: Workspace service unavailable."
        if not context.thread_id:
            return "Error: thread_id is required."
        if not context.user_email:
            return "Error: user_email is required."

        workspace = await context.service.get_by_thread(context.user_email, context.thread_id)
        if not workspace or not workspace.samplesheet.content:
            return "No samplesheet found for this workspace."
        return workspace.samplesheet.content
    finally:
        if context.close:
            await context.close()


@tool
@tool_error_handler
async def get_current_config(runtime: Any | None = None) -> str:
    """
    Get the current config content for the active workspace.

    Returns:
        The latest config content as a string.
    """
    context = await get_workspace_context(runtime)
    try:
        if not context.service:
            return "Error: Workspace service unavailable."
        if not context.thread_id:
            return "Error: thread_id is required."
        if not context.user_email:
            return "Error: user_email is required."

        workspace = await context.service.get_by_thread(context.user_email, context.thread_id)
        if not workspace or not workspace.config.content:
            return "No config found for this workspace."
        return workspace.config.content
    finally:
        if context.close:
            await context.close()


@tool
@tool_error_handler
async def get_workspace_status(runtime: Any | None = None) -> str:
    """
    Get current workspace status (pipeline, modifiers, and timestamps).

    Returns:
        JSON summary of workspace state.
    """
    context = await get_workspace_context(runtime)
    try:
        if not context.service:
            return "Error: Workspace service unavailable."
        if not context.thread_id:
            return "Error: thread_id is required."
        if not context.user_email:
            return "Error: user_email is required."

        workspace = await context.service.get_by_thread(context.user_email, context.thread_id)
        if not workspace:
            return "No workspace found for this thread."

        payload = {
            "workspace_id": str(workspace.id),
            "thread_id": workspace.thread_id,
            "pipeline": workspace.pipeline,
            "version": workspace.version,
            "samplesheet": {
                "present": bool(workspace.samplesheet.content),
                "modified_by": workspace.samplesheet.modified_by,
                "modified_at": workspace.samplesheet.modified_at.isoformat()
                if workspace.samplesheet.modified_at
                else None,
            },
            "config": {
                "present": bool(workspace.config.content),
                "modified_by": workspace.config.modified_by,
                "modified_at": workspace.config.modified_at.isoformat()
                if workspace.config.modified_at
                else None,
            },
        }
        return json.dumps(payload, indent=2)
    finally:
        if context.close:
            await context.close()
