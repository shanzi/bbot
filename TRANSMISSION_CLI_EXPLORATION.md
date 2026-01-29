# Transmission CLI Interface Exploration

## Current Setup

**Installed:**
- `transmission-gtk` (4.0.5) - GTK GUI client
- `transmission-common` (4.0.5) - Common files

**Configuration:**
- Location: `~/.config/transmission/`
- Download directory: `/home/chase/Downloads`
- RPC Status: **Disabled** (line 68: `"rpc-enabled": false`)
- RPC Port: `9091`
- RPC Auth: Not required (`"rpc-authentication-required": false`)
- RPC Whitelist: `127.0.0.1,::1` (localhost only)

## Available CLI Options

### Option 1: transmission-remote (Recommended)

**Installation:**
```bash
sudo apt install transmission-cli
```

**What it provides:**
- `transmission-remote` - CLI tool to control Transmission daemon
- `transmission-create` - Create torrent files
- `transmission-edit` - Edit torrent files
- `transmission-show` - Display torrent file info

**Usage:**
```bash
# Basic connection (assumes daemon running on localhost:9091)
transmission-remote

# List all torrents
transmission-remote -l

# Add torrent
transmission-remote -a <url-or-file>

# Start/Stop torrents
transmission-remote -t <id> -s  # Start
transmission-remote -t <id> -S  # Stop

# Remove torrent
transmission-remote -t <id> -r  # Remove (keep data)
transmission-remote -t <id> --remove-and-delete  # Remove and delete data

# Get info about specific torrent
transmission-remote -t <id> -i

# Set download speed limit
transmission-remote -d <speed>  # KB/s

# Set upload speed limit
transmission-remote -u <speed>  # KB/s
```

### Option 2: Python transmissionrpc Library

**Installation:**
```bash
# Via pip/uv (for MCP server)
uv add transmissionrpc

# Or system package
sudo apt install python3-transmissionrpc
```

**Python API:**
```python
import transmissionrpc

# Connect to transmission
client = transmissionrpc.Client('localhost', port=9091)

# List torrents
torrents = client.get_torrents()

for torrent in torrents:
    print(f"{torrent.id}: {torrent.name}")
    print(f"  Status: {torrent.status}")
    print(f"  Progress: {torrent.progress}%")
    print(f"  Download: {torrent.download_rate} B/s")
    print(f"  Upload: {torrent.upload_rate} B/s")

# Add torrent
client.add_torrent('magnet:?xt=...')
client.add_torrent('/path/to/file.torrent')

# Control torrents
client.start_torrent(1)  # Start torrent ID 1
client.stop_torrent(1)   # Stop torrent ID 1
client.remove_torrent(1) # Remove torrent ID 1
client.remove_torrent(1, delete_data=True)  # Remove and delete

# Get session stats
stats = client.session_stats()
print(f"Download: {stats.download_speed} B/s")
print(f"Upload: {stats.upload_speed} B/s")
print(f"Active torrents: {stats.active_torrent_count}")

# Change settings
client.set_session(speed_limit_down=1000, speed_limit_down_enabled=True)
```

## Enabling RPC Access

### Method 1: Edit settings.json (Transmission must be stopped)

```bash
# Stop Transmission
killall transmission-gtk

# Edit settings
nano ~/.config/transmission/settings.json

# Change:
"rpc-enabled": false,
# To:
"rpc-enabled": true,

# Save and restart Transmission
transmission-gtk &
```

### Method 2: Via GUI

1. Open Transmission GTK
2. Edit → Preferences
3. Remote tab
4. Check "Allow remote access"
5. (Optional) Set username/password
6. (Optional) Add allowed IP addresses to whitelist

## Available RPC Methods

The Transmission RPC API supports:

### Torrent Actions
- `torrent-start` - Start torrents
- `torrent-stop` - Stop torrents
- `torrent-verify` - Verify torrent data
- `torrent-reannounce` - Reannounce to trackers
- `torrent-set` - Change torrent settings
- `torrent-get` - Get torrent info
- `torrent-add` - Add new torrent
- `torrent-remove` - Remove torrent
- `torrent-set-location` - Move torrent data

### Session Actions
- `session-get` - Get session settings
- `session-set` - Change session settings
- `session-stats` - Get statistics
- `session-close` - Shutdown daemon

### Other
- `blocklist-update` - Update blocklist
- `port-test` - Test if peer port is open
- `free-space` - Check free disk space
- `queue-move-top/up/down/bottom` - Reorder queue

## Potential MCP Server Functions

Based on Transmission RPC capabilities:

```python
@fast_mcp.tool()
def list_torrents(filter_status: str = None) -> dict:
    """List all torrents with optional status filter.

    Args:
        filter_status: Optional filter (downloading, seeding, stopped, etc.)

    Returns:
        List of torrents with id, name, progress, status, speeds
    """

@fast_mcp.tool()
def add_torrent(source: str, download_dir: str = None) -> dict:
    """Add a new torrent from magnet link or file path.

    Args:
        source: Magnet link or torrent file path
        download_dir: Optional custom download directory

    Returns:
        Torrent info including ID and name
    """

@fast_mcp.tool()
def control_torrent(torrent_id: int, action: str) -> dict:
    """Control a torrent (start, stop, verify, remove).

    Args:
        torrent_id: Torrent ID
        action: start, stop, verify, remove, remove_with_data

    Returns:
        Success status
    """

@fast_mcp.tool()
def get_torrent_info(torrent_id: int) -> dict:
    """Get detailed information about a torrent.

    Args:
        torrent_id: Torrent ID

    Returns:
        Detailed torrent info including files, trackers, peers
    """

@fast_mcp.tool()
def get_session_stats() -> dict:
    """Get Transmission session statistics.

    Returns:
        Download/upload speeds, active torrents, total transferred
    """

@fast_mcp.tool()
def set_speed_limits(download_limit: int = None, upload_limit: int = None) -> dict:
    """Set download and upload speed limits.

    Args:
        download_limit: Download limit in KB/s (None to disable)
        upload_limit: Upload limit in KB/s (None to disable)

    Returns:
        Updated settings
    """
```

## Testing RPC Connection

```python
#!/usr/bin/env python3
"""Test Transmission RPC connection."""

import transmissionrpc

try:
    # Try to connect
    client = transmissionrpc.Client('localhost', port=9091)

    # Get session info
    session = client.get_session()
    print(f"✓ Connected to Transmission {session.version}")
    print(f"  Download dir: {session.download_dir}")

    # List torrents
    torrents = client.get_torrents()
    print(f"  Active torrents: {len(torrents)}")

except transmissionrpc.TransmissionError as e:
    print(f"✗ Connection failed: {e}")
    print("\nMake sure:")
    print("  1. Transmission is running")
    print("  2. RPC is enabled in settings")
    print("  3. Port 9091 is accessible")
except Exception as e:
    print(f"✗ Error: {e}")
```

## Next Steps

1. **Enable RPC** - Modify settings.json or use GUI
2. **Install CLI tools** - `sudo apt install transmission-cli`
3. **Install Python library** - `uv add transmissionrpc`
4. **Test connection** - Run test script
5. **Create MCP server** - Implement mcp_transmission_server.py

## Notes

- RPC must be enabled and Transmission must be running
- Default port is 9091
- Authentication is optional but recommended for remote access
- Whitelist controls which IPs can connect
- All operations are non-destructive (except remove with delete data)
