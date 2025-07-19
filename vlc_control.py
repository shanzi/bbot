#!/usr/bin/env python3
"""Standalone VLC control script using the virtualized stdin pipe."""

import sys
import os

def send_vlc_command(command: str) -> bool:
    """Send a command to VLC via the virtualized stdin pipe.
    
    Args:
        command: VLC remote control command
        
    Returns:
        bool: True if command was sent successfully
    """
    stdin_pipe = "/tmp/vlc_stdin.pipe"
    
    if not os.path.exists(stdin_pipe):
        print(f"Error: VLC stdin pipe {stdin_pipe} not found. Is VLC running?")
        return False
    
    try:
        # Write command to the stdin pipe
        with open(stdin_pipe, 'w') as f:
            f.write(f"{command}\n")
            f.flush()
        print(f"✅ Sent command: {command}")
        return True
    except (OSError, IOError) as e:
        print(f"❌ Failed to send command: {e}")
        return False

def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python vlc_control.py <command>")
        print("Commands: play, pause, stop, quit, seek <position>, volume <level>")
        print("Examples:")
        print("  python vlc_control.py play")
        print("  python vlc_control.py pause")
        print("  python vlc_control.py seek +30")
        print("  python vlc_control.py volume 75")
        sys.exit(1)
    
    # Join all arguments to handle commands with parameters
    command = " ".join(sys.argv[1:])
    
    success = send_vlc_command(command)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()