#!/usr/bin/env python3
"""Quick test script to check ADB SMS query behavior."""

import subprocess
import sys

def test_adb_command():
    """Test the ADB SMS query command and inspect its behavior."""

    print("=" * 70)
    print("Testing ADB SMS Query Command")
    print("=" * 70)
    print()

    # First check if device is connected
    print("1. Checking ADB device connection...")
    print("-" * 70)
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"Return code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        print()
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # Test the SMS query command
    print("2. Testing SMS query command...")
    print("-" * 70)

    command = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/",
        "--projection", "address:body:date:type:read:thread_id",
        "--sort", "date DESC"
    ]

    print(f"Command: {' '.join(command)}")
    print()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"Return code: {result.returncode}")
        print()

        print("STDOUT:")
        print(f"  Length: {len(result.stdout)} bytes")
        print(f"  Content: {repr(result.stdout[:500])}")  # First 500 chars
        if result.stdout:
            print(f"  Full output:\n{result.stdout}")
        else:
            print("  (empty)")
        print()

        print("STDERR:")
        print(f"  Length: {len(result.stderr)} bytes")
        print(f"  Content: {repr(result.stderr[:500])}")
        if result.stderr:
            print(f"  Full output:\n{result.stderr}")
        else:
            print("  (empty)")
        print()

    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out after 30 seconds")
        return
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # Test without --sort to see if that's the issue
    print("3. Testing without --sort parameter...")
    print("-" * 70)

    command_no_sort = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/",
        "--projection", "address:body:date:type:read:thread_id"
    ]

    print(f"Command: {' '.join(command_no_sort)}")
    print()

    try:
        result = subprocess.run(
            command_no_sort,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"Return code: {result.returncode}")
        print(f"STDOUT length: {len(result.stdout)} bytes")
        print(f"STDERR length: {len(result.stderr)} bytes")

        if result.stdout:
            lines = result.stdout.split('\n')
            print(f"Lines: {len(lines)}")
            print(f"First 3 lines:\n{chr(10).join(lines[:3])}")
        else:
            print("STDOUT: (empty)")

        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        print()

    except Exception as e:
        print(f"ERROR: {e}")
        return

    # Test with simpler projection
    print("4. Testing with simple projection...")
    print("-" * 70)

    command_simple = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/"
    ]

    print(f"Command: {' '.join(command_simple)}")
    print()

    try:
        result = subprocess.run(
            command_simple,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"Return code: {result.returncode}")
        print(f"STDOUT length: {len(result.stdout)} bytes")

        if result.stdout:
            lines = result.stdout.split('\n')
            print(f"Lines: {len(lines)}")
            print(f"First 5 lines:\n{chr(10).join(lines[:5])}")
        else:
            print("STDOUT: (empty)")

        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        print()

    except Exception as e:
        print(f"ERROR: {e}")

    # Test with --where to limit results
    print("5. Testing with --where filter...")
    print("-" * 70)

    command_where = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/",
        "--projection", "address:body:date",
        "--where", "read=0"
    ]

    print(f"Command: {' '.join(command_where)}")
    print()

    try:
        result = subprocess.run(
            command_where,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"Return code: {result.returncode}")
        print(f"STDOUT length: {len(result.stdout)} bytes")
        print(f"STDERR length: {len(result.stderr)} bytes")

        if result.stdout:
            lines = result.stdout.split('\n')
            print(f"Lines: {len(lines)}")
            print(f"Output:\n{result.stdout[:1000]}")
        else:
            print("STDOUT: (empty)")

        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

    except Exception as e:
        print(f"ERROR: {e}")

    print()
    print("=" * 70)
    print("Test complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_adb_command()
