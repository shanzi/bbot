#!/usr/bin/env python3
"""Test the fixed ADB command with escaped spaces."""

import subprocess

def test_escaped_sort():
    """Test ADB query with escaped spaces in --sort parameter."""

    print("Testing fixed ADB command with escaped spaces...")
    print("=" * 70)

    # Test with escaped spaces
    command = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/",
        "--projection", "address:body:date:type:read:thread_id",
        "--sort", "date\\ DESC"
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
        print(f"STDOUT length: {len(result.stdout)} bytes")
        print(f"STDERR length: {len(result.stderr)} bytes")
        print()

        if result.returncode != 0:
            print("ERROR!")
            print(f"STDERR: {result.stderr}")
        else:
            print("SUCCESS!")
            lines = result.stdout.split('\n')
            print(f"Got {len(lines)} lines")
            print("\nFirst 3 rows:")
            for line in lines[:3]:
                if line.strip():
                    print(line[:150])  # First 150 chars

        print()

    except Exception as e:
        print(f"Exception: {e}")

    # Test with escaped spaces and WHERE clause
    print("=" * 70)
    print("Testing with WHERE clause (escaped)...")
    print()

    command2 = [
        "adb", "shell", "content", "query",
        "--uri", "content://sms/",
        "--projection", "address:date",
        "--where", "read=0\\ AND\\ type=1",
        "--sort", "date\\ DESC"
    ]

    print(f"Command: {' '.join(command2)}")
    print()

    try:
        result = subprocess.run(
            command2,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"Return code: {result.returncode}")
        print(f"STDOUT length: {len(result.stdout)} bytes")
        print()

        if result.returncode != 0:
            print("ERROR!")
            print(f"STDERR: {result.stderr}")
        else:
            print("SUCCESS!")
            lines = result.stdout.split('\n')
            print(f"Got {len(lines)} lines")
            if len(lines) > 1:
                print("\nFirst 2 rows:")
                for line in lines[:2]:
                    if line.strip():
                        print(line)

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_escaped_sort()
