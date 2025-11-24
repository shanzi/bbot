"""Test script for the SMS MCP server functionality."""

import subprocess
import json


def test_adb_connection():
    """Test if ADB is connected to a device."""
    print("Testing ADB connection...")
    result = subprocess.run(
        ["adb", "devices"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print()


def test_sms_query():
    """Test basic SMS query."""
    print("Testing basic SMS query (last 5 messages)...")
    command = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/",
        "--projection", "address:body:date:type",
        "--sort", "date DESC"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    print(f"Command: {' '.join(command)}")
    print(f"Output:\n{result.stdout[:1000]}")  # First 1000 chars
    print()


def test_unread_messages():
    """Test querying unread messages."""
    print("Testing unread messages query...")
    command = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/",
        "--projection", "address:body:date",
        "--where", "read=0",
        "--sort", "date DESC"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    print(f"Command: {' '.join(command)}")
    print(f"Output:\n{result.stdout[:1000]}")
    print()


def test_sent_messages():
    """Test querying sent messages."""
    print("Testing sent messages query...")
    command = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/",
        "--projection", "address:body:date",
        "--where", "type=2",
        "--sort", "date DESC"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    print(f"Command: {' '.join(command)}")
    print(f"Output:\n{result.stdout[:1000]}")
    print()


def test_conversation_threads():
    """Test querying conversation threads."""
    print("Testing conversation threads query...")
    command = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/conversations"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    print(f"Command: {' '.join(command)}")
    print(f"Output:\n{result.stdout[:1000]}")
    print()


def show_available_columns():
    """Show available SMS database columns."""
    print("Common SMS database columns:")
    columns = {
        "_id": "Unique message ID",
        "thread_id": "Conversation thread ID",
        "address": "Phone number (sender/recipient)",
        "person": "Contact ID from contacts database",
        "date": "Timestamp (milliseconds since epoch)",
        "date_sent": "Sent timestamp",
        "protocol": "Protocol identifier (0 = SMS_PROTO)",
        "read": "Read status (0 = unread, 1 = read)",
        "status": "Message status",
        "type": "Message type (1 = inbox, 2 = sent, 3 = draft, 4 = outbox, 5 = failed, 6 = queued)",
        "body": "Message content",
        "service_center": "SMS service center address",
        "locked": "Lock status (0 = unlocked, 1 = locked)",
        "error_code": "Error code if failed",
        "seen": "Seen status (0 = not seen, 1 = seen)",
        "sub_id": "Subscription ID for multi-SIM devices"
    }

    for col, desc in columns.items():
        print(f"  {col:20s} - {desc}")
    print()


def main():
    """Run all tests."""
    print("=" * 70)
    print("SMS MCP Server Test Suite")
    print("=" * 70)
    print()

    print("Prerequisites:")
    print("1. Android device connected via USB")
    print("2. USB debugging enabled on device")
    print("3. ADB authorized (check device for prompt)")
    print("4. SMS read permission granted")
    print()

    show_available_columns()

    try:
        test_adb_connection()
        test_sms_query()
        test_unread_messages()
        test_sent_messages()
        test_conversation_threads()

        print("=" * 70)
        print("Tests completed!")
        print()
        print("Usage examples for the MCP server:")
        print()
        print("1. Get recent unread messages:")
        print('   query_sms(read=False, sort_order="DESC")')
        print()
        print("2. Get messages from specific contact:")
        print('   query_sms(address="+1234567890", sort_order="DESC")')
        print()
        print("3. Get messages in date range:")
        print('   query_sms(date_from=1234567890000, date_to=1234567900000)')
        print()
        print("4. Get read messages from a contact:")
        print('   query_sms(address="+1234567890", read=True)')
        print()
        print("5. Check ADB connection:")
        print('   check_adb_connection()')
        print()
        print("6. Get unread messages (helper):")
        print('   get_unread_sms(limit=20)')
        print()
        print("7. Get messages in a thread:")
        print('   get_sms_by_thread(thread_id="123", sort_order="ASC")')
        print()

    except FileNotFoundError:
        print("ERROR: ADB not found. Please install Android Debug Bridge (adb)")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
