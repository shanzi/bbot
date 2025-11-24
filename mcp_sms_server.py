"""MCP server providing SMS query tools via ADB for connected Android devices."""

import subprocess
from typing import Optional

from mcp.server.fastmcp.server import FastMCP

# Initialize MCP server
fast_mcp = FastMCP("mcp-server-sms")


@fast_mcp.tool()
def query_sms(
    address: Optional[str] = None,
    read: Optional[bool] = None,
    date_from: Optional[int] = None,
    date_to: Optional[int] = None,
    sort_order: str = "DESC",
    limit: int = 100
) -> dict:
    """Query SMS messages from a connected Android device via ADB.

    Args:
        address: Filter by phone number (e.g., "+1234567890")
        read: Filter by read status (True=read, False=unread, None=all)
        date_from: Filter messages from this timestamp onwards (milliseconds since epoch)
        date_to: Filter messages up to this timestamp (milliseconds since epoch)
        sort_order: Sort by date, either "DESC" (newest first) or "ASC" (oldest first)
        limit: Maximum number of results to return (default: 100)

    Returns:
        dict: Query results with status, count, messages, and command

    Examples:
        - Get recent unread messages:
          query_sms(read=False, sort_order="DESC")
        - Get messages from specific number:
          query_sms(address="+1234567890")
        - Get messages in date range:
          query_sms(date_from=1234567890000, date_to=1234567900000)
    """
    try:
        # Build the ADB command
        command = ["adb", "shell", "content", "query", "--uri", "content://sms/"]

        # Always use a fixed projection for consistency
        projection = "address:body:date:type:read:thread_id"
        command.extend(["--projection", projection])

        # Build WHERE clause from filters
        where_clauses = []

        if address is not None:
            where_clauses.append(f"address='{address}'")

        if read is not None:
            read_value = "1" if read else "0"
            where_clauses.append(f"read={read_value}")

        if date_from is not None:
            where_clauses.append(f"date>={date_from}")

        if date_to is not None:
            where_clauses.append(f"date<={date_to}")

        if where_clauses:
            where_clause = " AND ".join(where_clauses)
            # Escape spaces for ADB shell
            where_clause = where_clause.replace(" ", "\\ ")
            command.extend(["--where", where_clause])

        # Add sort order (always by date)
        # Escape spaces for ADB shell command parsing
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "DESC"
        sort_clause = f"date\\ {sort_order.upper()}"
        command.extend(["--sort", sort_clause])

        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=False  # Don't raise exception, handle errors manually
        )

        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else f"Command exited with code {result.returncode}"
            return {
                "status": "error",
                "error": f"ADB command failed: {error_msg}",
                "return_code": result.returncode,
                "hint": "Make sure an Android device is connected via ADB and USB debugging is enabled"
            }

        output = result.stdout.strip()

        if not output:
            return {
                "status": "success",
                "count": 0,
                "messages": [],
                "info": "No messages found matching the criteria"
            }

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

        return {
            "status": "success",
            "count": len(messages),
            "messages": messages,
            "command": " ".join(command)
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Command timed out after 30 seconds"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "error": "ADB command not found",
            "hint": "Please ensure Android Debug Bridge (adb) is installed and in your system's PATH"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"An unexpected error occurred: {str(e)}"
        }


@fast_mcp.tool()
def check_adb_connection() -> dict:
    """Check if an Android device is connected via ADB.

    Returns:
        dict: Connection status and device information
    """
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else f"Command exited with code {result.returncode}"
            return {
                "status": "error",
                "error": f"ADB devices command failed: {error_msg}",
                "return_code": result.returncode
            }

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

        return {
            "status": "success",
            "connected": len(devices) > 0,
            "device_count": len(devices),
            "devices": devices
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "error": "ADB command not found",
            "hint": "Please ensure Android Debug Bridge (adb) is installed and in your system's PATH"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to check ADB connection: {str(e)}"
        }


@fast_mcp.tool()
def query_sms_threads() -> dict:
    """Query SMS conversation threads from a connected Android device.

    Returns:
        dict: List of SMS threads with status, count, and thread data
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
            check=False
        )

        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else f"Command exited with code {result.returncode}"
            return {
                "status": "error",
                "error": f"ADB command failed: {error_msg}",
                "return_code": result.returncode
            }

        output = result.stdout.strip()

        if not output:
            return {
                "status": "success",
                "count": 0,
                "threads": []
            }

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

        return {
            "status": "success",
            "count": len(threads),
            "threads": threads
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Command timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to query SMS threads: {str(e)}"
        }


@fast_mcp.tool()
def get_sms_by_thread(thread_id: str, sort_order: str = "DESC", limit: int = 50) -> dict:
    """Get all SMS messages in a specific conversation thread.

    Args:
        thread_id: The thread ID to query
        sort_order: Sort by date, either "DESC" (newest first) or "ASC" (oldest first)
        limit: Maximum number of messages to return (default: 50)

    Returns:
        dict: Messages in the thread with status, count, and message data
    """
    try:
        # Build the ADB command with thread_id filter
        # Escape spaces for ADB shell command parsing
        sort_clause = f"date\\ {sort_order.upper()}"
        command = [
            "adb", "shell", "content", "query",
            "--uri", "content://sms/",
            "--projection", "address:body:date:type:read:thread_id",
            "--where", f"thread_id={thread_id}",
            "--sort", sort_clause
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )

        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else f"Command exited with code {result.returncode}"
            return {
                "status": "error",
                "error": f"ADB command failed: {error_msg}",
                "return_code": result.returncode,
                "thread_id": thread_id
            }

        output = result.stdout.strip()

        if not output:
            return {
                "status": "success",
                "count": 0,
                "messages": [],
                "thread_id": thread_id
            }

        messages = []
        lines = output.split('\n')

        for line in lines:
            if line.startswith('Row:'):
                row_data = line.split(' ', 2)[2] if len(line.split(' ', 2)) > 2 else ""
                message = {}
                parts = row_data.split(', ')
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        message[key] = value

                if message:
                    messages.append(message)

                if len(messages) >= limit:
                    break

        return {
            "status": "success",
            "count": len(messages),
            "messages": messages,
            "thread_id": thread_id
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Command timed out after 30 seconds",
            "thread_id": thread_id
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to get messages for thread {thread_id}: {str(e)}"
        }


@fast_mcp.tool()
def get_unread_sms(limit: int = 20) -> dict:
    """Get all unread SMS messages sorted by date (newest first).

    Args:
        limit: Maximum number of messages to return (default: 20)

    Returns:
        dict: Unread messages with status, count, and message data
    """
    return query_sms(read=False, sort_order="DESC", limit=limit)


def main() -> None:
    """Run the MCP server."""
    fast_mcp.run()


if __name__ == "__main__":
    main()
