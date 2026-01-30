#!/usr/bin/env python3
"""MCP server for managing reminders and scheduled tasks.

This server allows agents to create, list, and manage reminders/scheduled tasks
stored in a JSON file. The main bot application checks this file periodically
and triggers reminders by simulating messages to the agent.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent


# Data directory for storing reminders
DATA_DIR = Path(__file__).parent / "data" / "reminders"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REMINDERS_FILE = DATA_DIR / "reminders.json"


def load_reminders() -> list[dict[str, Any]]:
    """Load reminders from JSON file."""
    if not REMINDERS_FILE.exists():
        return []

    try:
        with open(REMINDERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_reminders(reminders: list[dict[str, Any]]) -> None:
    """Save reminders to JSON file."""
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f, indent=2)


def get_next_id(reminders: list[dict[str, Any]]) -> int:
    """Get next available reminder ID."""
    if not reminders:
        return 1
    return max(r.get('id', 0) for r in reminders) + 1


# Create MCP server
app = Server("reminder-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available reminder management tools."""
    return [
        Tool(
            name="add_reminder",
            description=(
                "Add a new reminder or scheduled task. The reminder will be stored and "
                "triggered at the specified time, causing the agent to proactively message the user. "
                "Returns the reminder ID which the system uses to route the notification."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Reminder message or task description"
                    },
                    "trigger_time": {
                        "type": "string",
                        "description": "When to trigger (ISO format: 2026-01-28T15:30:00 or relative like '+30m', '+2h', '+1d')"
                    },
                    "chat_id": {
                        "type": "integer",
                        "description": "Telegram chat ID where the reminder should be sent"
                    },
                    "recurrence": {
                        "type": "string",
                        "description": "Optional recurrence pattern: 'daily', 'weekly', 'monthly' (not implemented yet)",
                        "enum": ["none", "daily", "weekly", "monthly"]
                    }
                },
                "required": ["message", "trigger_time", "chat_id"]
            }
        ),
        Tool(
            name="list_reminders",
            description="List all reminders, optionally filtered by status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: 'pending', 'triggered', 'cancelled', or 'all'",
                        "enum": ["all", "pending", "triggered", "cancelled"]
                    }
                }
            }
        ),
        Tool(
            name="cancel_reminder",
            description="Cancel a pending reminder by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "ID of the reminder to cancel"
                    }
                },
                "required": ["reminder_id"]
            }
        ),
        Tool(
            name="get_pending_reminders",
            description="Get all pending reminders (used by bot for checking triggers).",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for reminder management."""

    if name == "add_reminder":
        return await add_reminder(
            arguments["message"],
            arguments["trigger_time"],
            arguments["chat_id"],
            arguments.get("recurrence", "none")
        )

    elif name == "list_reminders":
        return await list_reminders_tool(
            arguments.get("status", "all")
        )

    elif name == "cancel_reminder":
        return await cancel_reminder(arguments["reminder_id"])

    elif name == "get_pending_reminders":
        return await get_pending_reminders()

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def add_reminder(
    message: str,
    trigger_time: str,
    chat_id: int,
    recurrence: str = "none"
) -> list[TextContent]:
    """Add a new reminder."""
    reminders = load_reminders()

    # Parse trigger time
    try:
        # Check if relative time (e.g., '+30m', '+2h', '+1d')
        if trigger_time.startswith('+'):
            import re
            match = re.match(r'\+(\d+)([mhd])', trigger_time)
            if not match:
                return [TextContent(
                    type="text",
                    text=f"Invalid relative time format: {trigger_time}. Use '+30m', '+2h', or '+1d'"
                )]

            value, unit = match.groups()
            value = int(value)

            from datetime import timedelta
            now = datetime.now()
            if unit == 'm':
                trigger_dt = now + timedelta(minutes=value)
            elif unit == 'h':
                trigger_dt = now + timedelta(hours=value)
            elif unit == 'd':
                trigger_dt = now + timedelta(days=value)

            trigger_time_iso = trigger_dt.isoformat()
        else:
            # Parse ISO format
            trigger_dt = datetime.fromisoformat(trigger_time)
            trigger_time_iso = trigger_time

        # Check if time is in the past
        if trigger_dt < datetime.now():
            return [TextContent(
                type="text",
                text=f"Cannot set reminder in the past: {trigger_dt.strftime('%Y-%m-%d %H:%M:%S')}"
            )]

    except ValueError as e:
        return [TextContent(
            type="text",
            text=f"Invalid time format: {trigger_time}. Use ISO format (2026-01-28T15:30:00) or relative (+30m, +2h, +1d)"
        )]

    # Create reminder
    reminder = {
        "id": get_next_id(reminders),
        "message": message,
        "trigger_time": trigger_time_iso,
        "chat_id": chat_id,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "recurrence": recurrence
    }

    reminders.append(reminder)
    save_reminders(reminders)

    return [TextContent(
        type="text",
        text=(
            f"✅ Reminder created (ID: {reminder['id']})\n"
            f"Message: {message}\n"
            f"Trigger: {trigger_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Chat ID: {chat_id}\n"
            f"Status: pending"
        )
    )]


async def list_reminders_tool(status: str = "all") -> list[TextContent]:
    """List all reminders."""
    reminders = load_reminders()

    # Filter by status if specified
    filtered_reminders = reminders if status == "all" else [r for r in reminders if r["status"] == status]

    if not filtered_reminders:
        return [TextContent(
            type="text",
            text=f"No reminders found (status: {status})"
        )]

    # Format reminders
    lines = [f"📋 All Reminders (status: {status}):\n"]

    for reminder in sorted(filtered_reminders, key=lambda r: r["trigger_time"]):
        trigger_dt = datetime.fromisoformat(reminder["trigger_time"])
        status_emoji = {
            "pending": "⏰",
            "triggered": "✅",
            "cancelled": "❌"
        }.get(reminder["status"], "❓")

        lines.append(
            f"\n{status_emoji} ID: {reminder['id']} | Status: {reminder['status']}\n"
            f"   Message: {reminder['message']}\n"
            f"   Trigger: {trigger_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"   Created: {datetime.fromisoformat(reminder['created_at']).strftime('%Y-%m-%d %H:%M:%S')}"
        )

    return [TextContent(type="text", text="".join(lines))]


async def cancel_reminder(reminder_id: int) -> list[TextContent]:
    """Cancel a reminder."""
    reminders = load_reminders()

    # Find reminder
    reminder = next((r for r in reminders if r["id"] == reminder_id), None)

    if not reminder:
        return [TextContent(
            type="text",
            text=f"❌ Reminder {reminder_id} not found"
        )]

    if reminder["status"] == "cancelled":
        return [TextContent(
            type="text",
            text=f"⚠️ Reminder {reminder_id} is already cancelled"
        )]

    if reminder["status"] == "triggered":
        return [TextContent(
            type="text",
            text=f"⚠️ Reminder {reminder_id} has already been triggered"
        )]

    # Cancel reminder
    reminder["status"] = "cancelled"
    reminder["cancelled_at"] = datetime.now().isoformat()
    save_reminders(reminders)

    return [TextContent(
        type="text",
        text=f"✅ Reminder {reminder_id} cancelled: {reminder['message']}"
    )]


async def get_pending_reminders() -> list[TextContent]:
    """Get all pending reminders (for bot to check)."""
    reminders = load_reminders()
    pending = [r for r in reminders if r["status"] == "pending"]

    # Return as JSON for bot to parse
    return [TextContent(
        type="text",
        text=json.dumps(pending, indent=2)
    )]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
