#!/usr/bin/env python3
"""Test script for Calibre functionality."""

import logging
import os
import subprocess
from calibre import CalibreManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def test_calibre_command():
    """Test basic calibredb command."""
    print("=== Testing Basic Calibredb Command ===")
    
    library_path = os.getenv("CALIBRE_LIBRARY_PATH", os.path.expanduser("~/Calibre Library"))
    print(f"Library path: {library_path}")
    print(f"Library exists: {os.path.exists(library_path)}")
    
    if os.path.exists(library_path):
        contents = os.listdir(library_path)
        print(f"Library contents: {contents}")
    
    try:
        cmd = ["calibredb", "list", "--library-path", library_path, "--limit", "5"]
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Exit code: {result.returncode}")
        print(f"Stdout: {repr(result.stdout)}")
        print(f"Stderr: {repr(result.stderr)}")
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"Output lines: {len(lines)}")
            for i, line in enumerate(lines):
                print(f"Line {i}: {repr(line)}")
        
    except Exception as e:
        print(f"Error running calibredb: {e}")

def test_calibre_manager():
    """Test CalibreManager class."""
    print("\n=== Testing CalibreManager ===")
    
    manager = CalibreManager()
    print(f"Manager library path: {manager.library_path}")
    
    result = manager.list_ebooks(limit=5)
    print(f"List result: {result}")

def main():
    """Run all tests."""
    test_calibre_command()
    test_calibre_manager()

if __name__ == "__main__":
    main()