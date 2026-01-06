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
async def update_samplesheet(
    content: str,
    runtime: Any | None = None,
) -> str:
    """
    Update an existing samplesheet, including user-modified ones.

    Use this when the user asks to modify their existing samplesheet (e.g., add a row,
    change a value, remove samples). For generating new samplesheets from NGS runs
    or Benchling data, use generate_samplesheet instead.

    Args:
        content: The complete updated samplesheet CSV content

    Returns:
        Confirmation message indicating success or error
    """
    context = await get_workspace_context(runtime)
    try:
        if not context.service:
            return "Error: Workspace service unavailable."
        if not context.thread_id:
            return "Error: thread_id is required."
        if not context.user_email:
            return "Error: user_email is required."

        workspace = await context.service.get_or_create_for_thread(
            context.user_email,
            context.thread_id,
        )

        await context.service.update_samplesheet(
            workspace.id,
            context.user_email,
            content,
            "agent",
            force=True,
        )
        return "Samplesheet updated successfully."
    except ValueError as exc:
        return f"Error: {exc}"
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
async def update_config(
    content: str,
    runtime: Any | None = None,
) -> str:
    """
    Update an existing config, including user-modified ones.

    Use this when the user asks to modify their existing config (e.g., change a parameter,
    add a setting). For generating new configs from scratch, use generate_config instead.

    Args:
        content: The complete updated Nextflow config content

    Returns:
        Confirmation message indicating success or error
    """
    context = await get_workspace_context(runtime)
    try:
        if not context.service:
            return "Error: Workspace service unavailable."
        if not context.thread_id:
            return "Error: thread_id is required."
        if not context.user_email:
            return "Error: user_email is required."

        workspace = await context.service.get_or_create_for_thread(
            context.user_email,
            context.thread_id,
        )

        await context.service.update_config(
            workspace.id,
            context.user_email,
            content,
            "agent",
            force=True,
        )
        return "Config updated successfully."
    except ValueError as exc:
        return f"Error: {exc}"
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


__all__ = [
    "get_current_samplesheet",
    "update_samplesheet",
    "get_current_config",
    "update_config",
    "get_workspace_status",
]
