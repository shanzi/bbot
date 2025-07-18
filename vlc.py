"""VLC Chromecast control module for streaming movies to casting devices."""

import io
import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class VLCChromecast:
    """VLC Chromecast controller for streaming movies."""
    
    def __init__(self, chromecast_ip: Optional[str] = None):
        """Initialize VLC Chromecast controller.
        
        Args:
            chromecast_ip: IP address of the Chromecast device (optional, uses CHROMECAST_IP env var)
        """
        self.chromecast_ip = chromecast_ip or os.getenv("CHROMECAST_IP", "192.168.0.203")
        self.process: Optional[subprocess.Popen] = None
        self.current_movie: Optional[str] = None
        self.pid_file = "/tmp/vlc_chromecast.pid"
        
        # Kill any previous VLC process on initialization to ensure only one instance
        self._kill_previous_vlc()
    
    def start_casting(self, movie_path: str) -> bool:
        """Start casting a movie to Chromecast.
        
        Args:
            movie_path: Full path to the movie file
            
        Returns:
            bool: True if casting started successfully
        """
        if not os.path.exists(movie_path):
            raise FileNotFoundError(f"Movie file not found: {movie_path}")
        
        # Stop current instance if running
        self.stop_casting()
        
        # VLC command for Chromecast with stdin control interface
        vlc_cmd = [
            "vlc",
            movie_path,
            "--sout", "#chromecast",
            f"--sout-chromecast-ip={self.chromecast_ip}",
            "--demux-filter=demux_chromecast",
            "--intf", "rc",  # Remote control interface
            "--rc-fake-tty",  # Enable stdin control
            "--play-and-exit"  # Exit when playback finishes
        ]
        
        try:
            # Start VLC process with stdin pipe for control
            self.process = subprocess.Popen(
                vlc_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,  # Use text mode for easier string handling
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.current_movie = movie_path
            
            # Save PID file for process management
            self._save_pid_file()
            
            # Wait a moment for VLC to initialize
            time.sleep(2)
            
            return self.process.poll() is None
            
        except Exception as e:
            raise RuntimeError(f"Failed to start VLC casting: {e}")
    
    
    def _save_pid_file(self) -> None:
        """Save the current VLC process PID to a file."""
        if self.process:
            try:
                with open(self.pid_file, 'w') as f:
                    f.write(str(self.process.pid))
            except OSError:
                # Failed to write PID file, continue anyway
                pass
    
    def _kill_previous_vlc(self) -> None:
        """Kill any previous VLC process using the PID file."""
        if not os.path.exists(self.pid_file):
            return
            
        try:
            with open(self.pid_file, 'r') as f:
                pid_str = f.read().strip()
                if pid_str:
                    pid = int(pid_str)
                    # Check if process exists and kill it
                    try:
                        os.killpg(os.getpgid(pid), 15)  # SIGTERM
                        time.sleep(1)
                        # Force kill if still running
                        try:
                            os.killpg(os.getpgid(pid), 9)  # SIGKILL
                        except ProcessLookupError:
                            pass
                    except ProcessLookupError:
                        # Process doesn't exist anymore
                        pass
        except (OSError, ValueError):
            # Failed to read PID file or invalid PID
            pass
        finally:
            # Clean up PID file
            try:
                os.unlink(self.pid_file)
            except OSError:
                pass
    
    def send_command(self, command: str) -> bool:
        """Send control command to VLC via stdin.
        
        Args:
            command: VLC remote control command (play, pause, stop, seek, etc.)
            
        Returns:
            bool: True if command was sent successfully
        """
        if not self.process or self.process.poll() is not None:
            return False
            
        try:
            self.process.stdin.write(f"{command}\n")
            self.process.stdin.flush()
            return True
        except (OSError, IOError, BrokenPipeError):
            return False
    
    def play(self) -> bool:
        """Resume playback."""
        return self.send_command("play")
    
    def pause(self) -> bool:
        """Pause playback."""
        return self.send_command("pause")
    
    def stop(self) -> bool:
        """Stop playback."""
        return self.send_command("stop")
    
    def seek(self, position: str) -> bool:
        """Seek to position.
        
        Args:
            position: Time position (e.g., "30", "+10", "-5", "50%")
        """
        return self.send_command(f"seek {position}")
    
    def volume(self, level: int) -> bool:
        """Set volume level.
        
        Args:
            level: Volume level (0-100)
        """
        return self.send_command(f"volume {level}")
    
    def stop_casting(self) -> bool:
        """Stop VLC casting process."""
        if self.process and self.process.poll() is None:
            try:
                # Send quit command via stdin first
                self.send_command("quit")
                # Wait for graceful shutdown
                self.process.wait(timeout=3)
            except (subprocess.TimeoutExpired, OSError):
                # Force terminate if graceful shutdown fails
                try:
                    os.killpg(os.getpgid(self.process.pid), 15)  # SIGTERM
                    self.process.wait(timeout=2)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    # Force kill if still running
                    try:
                        os.killpg(os.getpgid(self.process.pid), 9)  # SIGKILL
                    except ProcessLookupError:
                        pass
            
            self.process = None
            self.current_movie = None
        
        
        # Clean up PID file
        if os.path.exists(self.pid_file):
            try:
                os.unlink(self.pid_file)
            except OSError:
                pass
                
        return True
    
    def is_playing(self) -> bool:
        """Check if VLC is currently playing."""
        return self.process is not None and self.process.poll() is None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current VLC status.
        
        Returns:
            dict: Status information
        """
        return {
            "is_playing": self.is_playing(),
            "current_movie": self.current_movie,
            "chromecast_ip": self.chromecast_ip,
            "control_method": "stdin",
            "pid_file": self.pid_file,
            "current_pid": self.process.pid if self.process else None
        }


def list_movie_files(movies_dir: str = "/media/chase/Secondary/Movies") -> List[Dict[str, str]]:
    """List all movie files in the specified directory.
    
    Args:
        movies_dir: Directory to scan for movie files
        
    Returns:
        List of movie file information dictionaries
    """
    # Common video file extensions
    video_extensions = {
        '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', 
        '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', '.mts', '.m2ts'
    }
    
    movies = []
    movies_path = Path(movies_dir)
    
    if not movies_path.exists():
        return []
    
    try:
        for file_path in movies_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                # Get file info
                stat = file_path.stat()
                size_mb = round(stat.st_size / (1024 * 1024), 1)
                
                movies.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size_mb": size_mb,
                    "extension": file_path.suffix.lower(),
                    "directory": str(file_path.parent)
                })
                
    except PermissionError:
        # Handle permission issues gracefully
        pass
    
    # Sort by name for consistent ordering
    movies.sort(key=lambda x: x["name"].lower())
    return movies


def find_movie(query: str, movies_dir: str = "/media/chase/Secondary/Movies") -> List[Dict[str, str]]:
    """Find movies matching a search query.
    
    Args:
        query: Search query (case-insensitive)
        movies_dir: Directory to search in
        
    Returns:
        List of matching movie file information
    """
    all_movies = list_movie_files(movies_dir)
    query_lower = query.lower()
    
    matches = []
    for movie in all_movies:
        if query_lower in movie["name"].lower():
            matches.append(movie)
    
    return matches


# Global VLC instance for easy access
vlc_controller = VLCChromecast()


def main():
    """Example usage of VLC Chromecast controller."""
    # List available movies
    print("Available movies:")
    movies = list_movie_files()
    for i, movie in enumerate(movies[:10], 1):  # Show first 10
        print(f"{i:2d}. {movie['name']} ({movie['size_mb']} MB)")
    
    if movies:
        print(f"\nTotal: {len(movies)} movies found")
        
        # Example: Start casting first movie
        first_movie = movies[0]
        print(f"\nExample: Starting to cast '{first_movie['name']}'")
        
        try:
            vlc_controller.start_casting(first_movie["path"])
            print("Casting started successfully!")
            print("Use vlc_controller.pause(), .play(), .stop(), .seek() to control playback")
        except Exception as e:
            print(f"Error starting cast: {e}")


if __name__ == "__main__":
    main()