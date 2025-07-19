#!/usr/bin/env python3
"""MCP server for VLC Chromecast control."""

import json
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)

import vlc

# Initialize MCP server
server = Server("vlc-chromecast")

# Global VLC controller instance
vlc_ctrl = vlc.vlc_controller


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available VLC control tools."""
    return [
        Tool(
            name="list_movies",
            description="List all movie files in the movies directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Movies directory path (optional, defaults to /media/chase/Secondary/Movies)",
                        "default": "/media/chase/Secondary/Movies"
                    }
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="find_movies",
            description="Search for movies by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find movies"
                    },
                    "directory": {
                        "type": "string", 
                        "description": "Movies directory path (optional)",
                        "default": "/media/chase/Secondary/Movies"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="start_casting",
            description="Start casting a movie to Chromecast",
            inputSchema={
                "type": "object",
                "properties": {
                    "movie_path": {
                        "type": "string",
                        "description": "Full path to the movie file to cast"
                    },
                    "chromecast_ip": {
                        "type": "string",
                        "description": "Chromecast IP address (optional, defaults to 192.168.0.203)",
                        "default": "192.168.0.203"
                    }
                },
                "required": ["movie_path"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="control_playback",
            description="Control VLC playback (play, pause, stop, seek, volume)",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["play", "pause", "stop", "seek", "volume"],
                        "description": "Playback control action"
                    },
                    "value": {
                        "type": "string",
                        "description": "Value for seek (time/percentage) or volume (0-100)"
                    }
                },
                "required": ["action"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="stop_casting",
            description="Stop VLC casting and clean up",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_vlc_status",
            description="Get current VLC casting status",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for VLC control."""
    
    try:
        if name == "list_movies":
            directory = arguments.get("directory", "/media/chase/Secondary/Movies")
            movies = vlc.list_movie_files(directory)
            
            if not movies:
                return [TextContent(
                    type="text",
                    text=f"No movie files found in {directory}"
                )]
            
            # Format movie list
            result = f"Found {len(movies)} movies in {directory}:\n\n"
            for i, movie in enumerate(movies, 1):
                result += f"{i:3d}. {movie['name']}\n"
                result += f"     Path: {movie['path']}\n"
                result += f"     Size: {movie['size_mb']} MB\n"
                result += f"     Type: {movie['extension']}\n\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "find_movies":
            query = arguments.get("query", "")
            directory = arguments.get("directory", "/media/chase/Secondary/Movies")
            
            if not query:
                return [TextContent(
                    type="text",
                    text="Please provide a search query"
                )]
            
            matches = vlc.find_movie(query, directory)
            
            if not matches:
                return [TextContent(
                    type="text",
                    text=f"No movies found matching '{query}'"
                )]
            
            result = f"Found {len(matches)} movies matching '{query}':\n\n"
            for i, movie in enumerate(matches, 1):
                result += f"{i}. {movie['name']}\n"
                result += f"   Path: {movie['path']}\n"
                result += f"   Size: {movie['size_mb']} MB\n\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "start_casting":
            movie_path = arguments.get("movie_path", "")
            chromecast_ip = arguments.get("chromecast_ip", "192.168.0.203")
            
            if not movie_path:
                return [TextContent(
                    type="text",
                    text="Please provide a movie file path"
                )]
            
            # Update Chromecast IP if provided
            vlc_ctrl.chromecast_ip = chromecast_ip
            
            try:
                success = vlc_ctrl.start_casting(movie_path)
                if success:
                    movie_name = movie_path.split("/")[-1]
                    return [TextContent(
                        type="text",
                        text=f"✅ Started casting '{movie_name}' to Chromecast ({chromecast_ip})\n"
                             f"Use control_playback tool to play/pause/stop/seek."
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text="❌ Failed to start casting. VLC process may not have started properly."
                    )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error starting cast: {str(e)}"
                )]
        
        elif name == "control_playback":
            action = arguments.get("action", "")
            value = arguments.get("value", "")
            
            if not action:
                return [TextContent(
                    type="text",
                    text="Please specify an action: play, pause, stop, seek, or volume"
                )]
            
            success = False
            result_msg = ""
            
            if action == "play":
                success = vlc_ctrl.play()
                result_msg = "▶️ Playback resumed"
            elif action == "pause":
                success = vlc_ctrl.pause()
                result_msg = "⏸️ Playback paused"
            elif action == "stop":
                success = vlc_ctrl.stop()
                result_msg = "⏹️ Playback stopped"
            elif action == "seek":
                if not value:
                    return [TextContent(
                        type="text",
                        text="Please provide a seek value (e.g., '30', '+10', '-5', '50%')"
                    )]
                success = vlc_ctrl.seek(value)
                result_msg = f"⏩ Seeking to {value}"
            elif action == "volume":
                if not value:
                    return [TextContent(
                        type="text",
                        text="Please provide a volume level (0-100)"
                    )]
                try:
                    vol_level = int(value)
                    if 0 <= vol_level <= 100:
                        success = vlc_ctrl.volume(vol_level)
                        result_msg = f"🔊 Volume set to {vol_level}%"
                    else:
                        return [TextContent(
                            type="text",
                            text="Volume must be between 0 and 100"
                        )]
                except ValueError:
                    return [TextContent(
                        type="text",
                        text="Volume must be a number between 0 and 100"
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown action: {action}. Use: play, pause, stop, seek, or volume"
                )]
            
            if success:
                return [TextContent(type="text", text=result_msg)]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to execute {action}. Is VLC running?"
                )]
        
        elif name == "stop_casting":
            success = vlc_ctrl.stop_casting()
            if success:
                return [TextContent(
                    type="text",
                    text="⏹️ VLC casting stopped and cleaned up"
                )]
            else:
                return [TextContent(
                    type="text",
                    text="❌ Failed to stop casting"
                )]
        
        elif name == "get_vlc_status":
            status = vlc_ctrl.get_status()
            
            result = "🎬 VLC Chromecast Status:\n\n"
            result += f"Playing: {'✅ Yes' if status['is_playing'] else '❌ No'}\n"
            result += f"Chromecast IP: {status['chromecast_ip']}\n"
            result += f"Control Method: {status['control_method']}\n"
            
            if status['current_movie']:
                movie_name = status['current_movie'].split("/")[-1]
                result += f"Current Movie: {movie_name}\n"
                result += f"Full Path: {status['current_movie']}\n"
            else:
                result += "Current Movie: None\n"
            
            return [TextContent(type="text", text=result)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())