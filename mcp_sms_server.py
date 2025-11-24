"""MCP server providing SMS query tools via ADB for connected Android devices."""

import json
import subprocess
from typing import Optional

from mcp.server.fastmcp.server import FastMCP

# Initialize MCP server
fast_mcp = FastMCP("mcp-server-sms")


@fast_mcp.tool()
def query_sms(
    projection: Optional[str] = None,
    where: Optional[str] = None,
    sort: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100
) -> str:
    """Query SMS messages from a connected Android device via ADB.

    Args:
        projection: Colon-separated list of column names to retrieve (e.g., "address:body:date")
                   Common columns: _id, address, person, date, date_sent, protocol, read,
                   status, type, body, service_center, locked, error_code, seen, thread_id
        where: SQL WHERE clause to filter results (e.g., "type=1 AND read=0")
               Common filters: type (1=inbox, 2=sent), read (0=unread, 1=read),
               address (phone number), date (timestamp in milliseconds)
        sort: Sort order for results (e.g., "date DESC", "address ASC")
        user_id: Android user ID to query (optional)
        limit: Maximum number of results to return (default: 100)

    Returns:
        str: Query results in JSON format or error message

    Examples:
        - Get recent unread messages:
          query_sms(projection="address:body:date", where="read=0", sort="date DESC")
        - Get all sent messages:
          query_sms(where="type=2", sort="date DESC")
        - Get messages from specific number:
          query_sms(where="address='+1234567890'")
    """
    try:
        # Build the ADB command
        command = ["adb", "shell", "content", "query", "--uri", "content://sms/"]

        if user_id:
            command.extend(["--user", user_id])

        if projection:
            command.extend(["--projection", projection])

        if where:
            command.extend(["--where", where])

        if sort:
            command.extend(["--sort", sort])

        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        output = result.stdout.strip()

        if not output:
            return json.dumps({
                "status": "success",
                "count": 0,
                "messages": [],
                "info": "No messages found matching the criteria"
            }, indent=2)

        # Parse the output
        # ADB content query returns rows in format: Row: 0 col1=value1, col2=value2, ...
        messages = []
        lines = output.split('\n')

        for line in lines:
            if line.startswith('Row:'):
                # Extract the row data
                row_data = line.split(' ', 2)[2] if len(line.split(' ', 2)) > 2 else ""

                # Parse key=value pairs
                message = {}
                parts = row_data.split(', ')
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        message[key] = value

                if message:
                    messages.append(message)

                # Apply limit
                if len(messages) >= limit:
                    break

        return json.dumps({
            "status": "success",
            "count": len(messages),
            "messages": messages,
            "command": " ".join(command)
        }, indent=2)

    except subprocess.TimeoutExpired:
        return json.dumps({
            "status": "error",
            "error": "Command timed out after 30 seconds"
        }, indent=2)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        return json.dumps({
            "status": "error",
            "error": f"ADB command failed: {error_msg}",
            "hint": "Make sure an Android device is connected via ADB and USB debugging is enabled"
        }, indent=2)
    except FileNotFoundError:
        return json.dumps({
            "status": "error",
            "error": "ADB command not found",
            "hint": "Please ensure Android Debug Bridge (adb) is installed and in your system's PATH"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"An unexpected error occurred: {str(e)}"
        }, indent=2)


@fast_mcp.tool()
def check_adb_connection() -> str:
    """Check if an Android device is connected via ADB.

    Returns:
        str: Connection status and device information in JSON format
    """
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )

        lines = result.stdout.strip().split('\n')
        devices = []

        # Parse device list (skip first line which is "List of devices attached")
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    devices.append({
                        "serial": parts[0],
                        "status": parts[1]
                    })

        return json.dumps({
            "status": "success",
            "connected": len(devices) > 0,
            "device_count": len(devices),
            "devices": devices
        }, indent=2)

    except FileNotFoundError:
        return json.dumps({
            "status": "error",
            "error": "ADB command not found",
            "hint": "Please ensure Android Debug Bridge (adb) is installed and in your system's PATH"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Failed to check ADB connection: {str(e)}"
        }, indent=2)


@fast_mcp.tool()
def query_sms_threads() -> str:
    """Query SMS conversation threads from a connected Android device.

    Returns:
        str: List of SMS threads in JSON format
    """
    try:
        command = [
            "adb", "shell", "content", "query",
            "--uri", "content://sms/conversations",
            "--projection", "thread_id:snippet:msg_count:date"
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        output = result.stdout.strip()

        if not output:
            return json.dumps({
                "status": "success",
                "count": 0,
                "threads": []
            }, indent=2)

        threads = []
        lines = output.split('\n')

        for line in lines:
            if line.startswith('Row:'):
                row_data = line.split(' ', 2)[2] if len(line.split(' ', 2)) > 2 else ""
                thread = {}
                parts = row_data.split(', ')
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        thread[key] = value

                if thread:
                    threads.append(thread)

        return json.dumps({
            "status": "success",
            "count": len(threads),
            "threads": threads
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Failed to query SMS threads: {str(e)}"
        }, indent=2)


@fast_mcp.tool()
def get_sms_by_thread(thread_id: str, limit: int = 50) -> str:
    """Get all SMS messages in a specific conversation thread.

    Args:
        thread_id: The thread ID to query
        limit: Maximum number of messages to return (default: 50)

    Returns:
        str: Messages in the thread in JSON format
    """
    try:
        return query_sms(
            projection="address:body:date:type:read",
            where=f"thread_id={thread_id}",
            sort="date DESC",
            limit=limit
        )
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Failed to get messages for thread {thread_id}: {str(e)}"
        }, indent=2)


@fast_mcp.tool()
def get_unread_sms(limit: int = 20) -> str:
    """Get all unread SMS messages.

    Args:
        limit: Maximum number of messages to return (default: 20)

    Returns:
        str: Unread messages in JSON format
    """
    try:
        return query_sms(
            projection="address:body:date:thread_id",
            where="read=0",
            sort="date DESC",
            limit=limit
        )
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Failed to get unread messages: {str(e)}"
        }, indent=2)


def main() -> None:
    """Run the MCP server."""
    fast_mcp.run()


if __name__ == "__main__":
    main()
