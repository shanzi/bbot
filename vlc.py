"""VLC Chromecast control module for streaming movies to casting devices."""

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
        self.control_pipe = "/tmp/vlc_control.pipe"
    
    def start_casting(self, movie_path: str) -> bool:
        """Start casting a movie to Chromecast.
        
        Args:
            movie_path: Full path to the movie file
            
        Returns:
            bool: True if casting started successfully
        """
        if not os.path.exists(movie_path):
            raise FileNotFoundError(f"Movie file not found: {movie_path}")
        
        # Stop any existing VLC process
        self.stop_casting()
        
        # Create named pipe for shared control
        self._create_control_pipe()
        
        # VLC command for Chromecast with named pipe control interface
        vlc_cmd = [
            "vlc",
            movie_path,
            "--sout", "#chromecast",
            f"--sout-chromecast-ip={self.chromecast_ip}",
            "--demux-filter=demux_chromecast",
            "--intf", "rc",  # Remote control interface
            "--rc-unix", self.control_pipe,  # Use named pipe for control
            "--play-and-exit"  # Exit when playback finishes
        ]
        
        try:
            # Start VLC process with stderr redirected to null
            self.process = subprocess.Popen(
                vlc_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.current_movie = movie_path
            
            # Wait a moment for VLC to initialize
            time.sleep(2)
            
            return self.process.poll() is None
            
        except Exception as e:
            raise RuntimeError(f"Failed to start VLC casting: {e}")
    
    def _create_control_pipe(self) -> None:
        """Create named pipe for VLC control if it doesn't exist."""
        if not os.path.exists(self.control_pipe):
            try:
                os.mkfifo(self.control_pipe)
            except FileExistsError:
                # Pipe already exists, continue
                pass
    
    def send_command(self, command: str) -> bool:
        """Send control command to VLC via named pipe.
        
        Args:
            command: VLC remote control command (play, pause, stop, seek, etc.)
            
        Returns:
            bool: True if command was sent successfully
        """
        if not os.path.exists(self.control_pipe):
            return False
            
        try:
            with open(self.control_pipe, 'w') as pipe:
                pipe.write(f"{command}\n")
                pipe.flush()
            return True
        except (OSError, IOError):
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
                # Send quit command via named pipe first
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
        
        # Clean up control pipe
        if os.path.exists(self.control_pipe):
            try:
                os.unlink(self.control_pipe)
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
            "control_method": "named_pipe",
            "control_pipe": self.control_pipe
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