"""MCP server providing Transmission BitTorrent client control tools."""

import json
from typing import Optional

import transmissionrpc
from mcp.server.fastmcp.server import FastMCP

# Initialize MCP server
fast_mcp = FastMCP("mcp-server-transmission")

# Default connection parameters
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9091


def get_client() -> transmissionrpc.Client:
    """Create and return a Transmission RPC client.

    Returns:
        transmissionrpc.Client: Connected client instance

    Raises:
        Exception: If connection fails
    """
    try:
        return transmissionrpc.Client(DEFAULT_HOST, port=DEFAULT_PORT)
    except Exception as e:
        raise Exception(f"Failed to connect to Transmission daemon: {e}")


@fast_mcp.tool()
def list_torrents(filter_status: Optional[str] = None) -> str:
    """List all torrents with optional status filter.

    Args:
        filter_status: Optional filter (downloading, seeding, stopped, checking, all)

    Returns:
        str: JSON formatted list of torrents with their details
    """
    try:
        client = get_client()
        torrents = client.get_torrents()

        if not torrents:
            return json.dumps({
                "count": 0,
                "torrents": [],
                "message": "No torrents found"
            }, indent=2)

        torrent_list = []
        for t in torrents:
            status = t.status.lower()

            # Filter if requested
            if filter_status and filter_status.lower() != 'all':
                if filter_status.lower() not in status:
                    continue

            # Format ETA
            eta_str = "N/A"
            try:
                if t.eta:
                    eta_str = str(t.eta)
            except:
                eta_str = "N/A"

            torrent_info = {
                "id": t.id,
                "name": t.name,
                "status": status,
                "progress": f"{t.percentDone * 100:.1f}%",
                "size": f"{t.totalSize / (1024**3):.2f} GB",
                "downloaded": f"{t.downloadedEver / (1024**3):.2f} GB",
                "uploaded": f"{t.uploadedEver / (1024**3):.2f} GB",
                "ratio": f"{(t.uploadedEver / t.downloadedEver if t.downloadedEver > 0 else 0):.2f}",
                "download_rate": f"{t.rateDownload / 1024:.2f} KB/s",
                "upload_rate": f"{t.rateUpload / 1024:.2f} KB/s",
                "eta": eta_str,
                "download_path": t.downloadDir,
                "torrent_file": t.torrentFile,
            }
            torrent_list.append(torrent_info)

        return json.dumps({
            "count": len(torrent_list),
            "torrents": torrent_list
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@fast_mcp.tool()
def add_torrent(source: str, download_dir: Optional[str] = None, paused: bool = False) -> str:
    """Add a new torrent from magnet link or torrent file path.

    Args:
        source: Magnet link or path to .torrent file
        download_dir: Optional download directory (e.g., '/media/chase/Secondary/Movies')
        paused: If True, add torrent in paused state (default: False)

    Returns:
        str: JSON formatted result with torrent ID and name
    """
    try:
        client = get_client()

        kwargs = {"paused": paused}
        if download_dir:
            kwargs["download_dir"] = download_dir

        torrent = client.add_torrent(source, **kwargs)

        return json.dumps({
            "success": True,
            "torrent_id": torrent.id,
            "name": torrent.name,
            "status": "paused" if paused else "started",
            "download_dir": download_dir or "default"
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@fast_mcp.tool()
def show_active_downloads() -> str:
    """Show detailed status of currently active/downloading torrents.

    Returns:
        str: Formatted status of active downloads with progress, speeds, and ETA
    """
    try:
        client = get_client()
        torrents = client.get_torrents()

        # Filter to only downloading/active torrents
        active_torrents = [t for t in torrents if 'downloading' in t.status.lower() or t.rateDownload > 0]

        if not active_torrents:
            return json.dumps({
                "count": 0,
                "active_downloads": [],
                "message": "No active downloads"
            }, indent=2)

        downloads = []
        for t in active_torrents:
            # Format ETA nicely
            eta_formatted = "Unknown"
            try:
                if t.eta:
                    if hasattr(t.eta, 'total_seconds'):
                        total_seconds = int(t.eta.total_seconds())
                    else:
                        total_seconds = int(t.eta)

                    if total_seconds > 0:
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        if hours > 0:
                            eta_formatted = f"{hours}h {minutes}m"
                        elif minutes > 0:
                            eta_formatted = f"{minutes}m {seconds}s"
                        else:
                            eta_formatted = f"{seconds}s"
            except:
                eta_formatted = "Unknown"

            download_info = {
                "id": t.id,
                "name": t.name,
                "progress": f"{t.percentDone * 100:.1f}%",
                "size": {
                    "total": f"{t.totalSize / (1024**3):.2f} GB",
                    "downloaded": f"{t.downloadedEver / (1024**3):.2f} GB",
                    "remaining": f"{(t.totalSize - t.downloadedEver) / (1024**3):.2f} GB"
                },
                "speed": {
                    "download": f"{t.rateDownload / 1024:.2f} KB/s" if t.rateDownload > 0 else "0 KB/s",
                    "upload": f"{t.rateUpload / 1024:.2f} KB/s" if t.rateUpload > 0 else "0 KB/s"
                },
                "eta": eta_formatted,
                "peers": getattr(t, 'peersConnected', 0),
                "ratio": f"{(t.uploadedEver / t.downloadedEver if t.downloadedEver > 0 else 0):.2f}",
                "download_path": t.downloadDir,
                "torrent_file": t.torrentFile
            }
            downloads.append(download_info)

        return json.dumps({
            "count": len(downloads),
            "active_downloads": downloads,
            "summary": f"{len(downloads)} active download(s)"
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e)
        }, indent=2)


@fast_mcp.tool()
def manage_torrent(torrent_id: int, action: str) -> str:
    """Manage a torrent - start, pause, or remove.

    Args:
        torrent_id: Torrent ID
        action: Action to perform - start, pause, remove, remove_with_data

    Returns:
        str: JSON formatted result
    """
    try:
        client = get_client()
        action = action.lower()

        if action == "start":
            client.start_torrent(torrent_id)
            message = f"Started torrent {torrent_id}"

        elif action == "pause":
            client.stop_torrent(torrent_id)
            message = f"Paused torrent {torrent_id}"

        elif action == "remove":
            client.remove_torrent(torrent_id, delete_data=False)
            message = f"Removed torrent {torrent_id} (data preserved)"

        elif action == "remove_with_data":
            client.remove_torrent(torrent_id, delete_data=True)
            message = f"Removed torrent {torrent_id} and deleted data"

        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown action: {action}. Valid actions: start, pause, remove, remove_with_data"
            }, indent=2)

        return json.dumps({
            "success": True,
            "action": action,
            "torrent_id": torrent_id,
            "message": message
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


def main() -> None:
    """Run the MCP server."""
    fast_mcp.run()


if __name__ == "__main__":
    main()
