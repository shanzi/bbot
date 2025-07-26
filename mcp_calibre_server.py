#!/usr/bin/env python3
"""MCP server for Calibre ebook management."""

import json
import logging
import os
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

import calibre
import tempfile
import shutil
import utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("calibre-ebook")

# Global Calibre manager instance
calibre_mgr = calibre.calibre_manager

logger.info("MCP Calibre server initialized")
logger.info(f"Calibre library path: {calibre_mgr.library_path}")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available Calibre ebook management tools."""
    return [
        Tool(
            name="add_ebook",
            description="Add an ebook file to the Calibre library",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the ebook file to add"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional title override for the ebook"
                    },
                    "authors": {
                        "type": "string",
                        "description": "Optional authors override (comma-separated)"
                    }
                },
                "required": ["file_path"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="list_ebooks",
            description="List ebooks in the Calibre library with optional search",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "Optional search query (e.g., 'author:King', 'title:Python')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="convert_ebook",
            description="Convert an ebook to a different format",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the input ebook file"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Target format (pdf, epub, mobi, txt, etc.)",
                        "enum": ["pdf", "epub", "mobi", "txt", "azw3", "docx", "html"]
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional custom output path"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional title override"
                    },
                    "authors": {
                        "type": "string",
                        "description": "Optional authors override"
                    }
                },
                "required": ["input_path", "output_format"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_book_info",
            description="Get detailed information about a specific book by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "Calibre book ID"
                    }
                },
                "required": ["book_id"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="export_book",
            description="Export book files from the Calibre library",
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "Calibre book ID to export"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to export files to"
                    },
                    "formats": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific formats to export (empty for all formats)"
                    }
                },
                "required": ["book_id", "output_dir"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="search_books",
            description="Search for books with advanced query options",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (supports title:, author:, tag:, format: etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="send_book_to_kindle",
            description="Export a book from Calibre library and send it to Kindle",
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "Calibre book ID to send to Kindle"
                    },
                    "format": {
                        "type": "string",
                        "description": "Preferred format for Kindle (mobi, azw3, pdf)",
                        "enum": ["mobi", "azw3", "pdf"],
                        "default": "mobi"
                    }
                },
                "required": ["book_id"],
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for Calibre ebook management."""
    
    try:
        if name == "add_ebook":
            file_path = arguments.get("file_path", "")
            title = arguments.get("title")
            authors = arguments.get("authors")
            
            if not file_path:
                return [TextContent(
                    type="text",
                    text="Please provide a file path for the ebook to add."
                )]
            
            result = calibre_mgr.add_ebook(file_path, title, authors)
            
            if result["success"]:
                response = f"✅ {result['message']}\n"
                if result["book_id"]:
                    response += f"📚 Book ID: {result['book_id']}\n"
                response += f"📁 File: {os.path.basename(result['file_path'])}"
            else:
                response = f"❌ Failed to add ebook: {result['error']}"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "list_ebooks":
            search_query = arguments.get("search_query")
            limit = arguments.get("limit", 20)
            
            logger.info(f"MCP list_ebooks called with search_query='{search_query}', limit={limit}")
            
            result = calibre_mgr.list_ebooks(search_query, limit)
            
            logger.info(f"list_ebooks result: success={result['success']}, count={result.get('count', 0)}")
            if not result['success']:
                logger.error(f"list_ebooks error: {result.get('error')}")
            
            if result["success"]:
                if not result["books"]:
                    response = "📚 No ebooks found in library"
                    if search_query:
                        response += f" matching '{search_query}'"
                else:
                    response = f"📚 Calibre Library ({result['count']} books"
                    if search_query:
                        response += f" matching '{search_query}'"
                    response += f"):\n\n"
                    
                    for book in result["books"]:
                        response += f"🆔 {book['id']:3d} | 📖 {book['title']}\n"
                        response += f"      👤 {book['authors']}\n"
                        if book['formats']:
                            response += f"      📄 {book['formats']}\n"
                        if book['size']:
                            response += f"      📏 {book['size']}\n"
                        response += "\n"
                    
                    response += f"📍 Library: {result['library_path']}"
            else:
                response = f"❌ Failed to list ebooks: {result['error']}"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "convert_ebook":
            input_path = arguments.get("input_path", "")
            output_format = arguments.get("output_format", "pdf")
            output_path = arguments.get("output_path")
            
            if not input_path:
                return [TextContent(
                    type="text",
                    text="Please provide an input file path for conversion."
                )]
            
            # Prepare conversion options
            options = {}
            if arguments.get("title"):
                options["title"] = arguments["title"]
            if arguments.get("authors"):
                options["authors"] = arguments["authors"]
            
            result = calibre_mgr.convert_ebook(
                input_path, output_format, output_path, **options
            )
            
            if result["success"]:
                response = f"✅ {result['message']}\n"
                response += f"📥 Input: {os.path.basename(result['input_path'])}\n"
                response += f"📤 Output: {result['output_path']}\n"
                response += f"🔄 Format: {result['format']}"
            else:
                response = f"❌ Conversion failed: {result['error']}"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_book_info":
            book_id = arguments.get("book_id")
            
            if book_id is None:
                return [TextContent(
                    type="text",
                    text="Please provide a book ID."
                )]
            
            result = calibre_mgr.get_book_info(book_id)
            
            if result["success"]:
                response = f"📚 Book Information (ID: {result['book_id']}):\n\n"
                
                metadata = result["metadata"]
                for key, value in metadata.items():
                    if value and value != "None":
                        # Format common fields with icons
                        icon = {
                            "Title": "📖",
                            "Author(s)": "👤",
                            "Tags": "🏷️",
                            "Published": "📅",
                            "Publisher": "🏢",
                            "Language": "🌍",
                            "Series": "📚",
                            "Formats": "📄"
                        }.get(key, "ℹ️")
                        
                        response += f"{icon} {key}: {value}\n"
            else:
                response = f"❌ Failed to get book info: {result['error']}"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "export_book":
            book_id = arguments.get("book_id")
            output_dir = arguments.get("output_dir", "")
            formats = arguments.get("formats", [])
            
            if book_id is None:
                return [TextContent(
                    type="text",
                    text="Please provide a book ID to export."
                )]
            
            if not output_dir:
                return [TextContent(
                    type="text",
                    text="Please provide an output directory."
                )]
            
            result = calibre_mgr.export_book(book_id, output_dir, formats or None)
            
            if result["success"]:
                response = f"✅ {result['message']}\n"
                response += f"📁 Output Directory: {result['output_dir']}\n"
                
                if result["exported_files"]:
                    response += f"📄 Exported Files:\n"
                    for file_path in result["exported_files"]:
                        response += f"  • {os.path.basename(file_path)}\n"
            else:
                response = f"❌ Export failed: {result['error']}"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "search_books":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 10)
            
            if not query:
                return [TextContent(
                    type="text",
                    text="Please provide a search query."
                )]
            
            result = calibre_mgr.list_ebooks(query, limit)
            
            if result["success"]:
                if not result["books"]:
                    response = f"🔍 No books found matching '{query}'"
                else:
                    response = f"🔍 Search Results for '{query}' ({result['count']} found):\n\n"
                    
                    for book in result["books"]:
                        response += f"🆔 {book['id']} | 📖 {book['title']}\n"
                        response += f"  👤 {book['authors']}\n"
                        if book['formats']:
                            response += f"  📄 {book['formats']}\n"
                        response += "\n"
            else:
                response = f"❌ Search failed: {result['error']}"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "send_book_to_kindle":
            book_id = arguments.get("book_id")
            format_pref = arguments.get("format", "mobi")
            
            if book_id is None:
                return [TextContent(
                    type="text",
                    text="Please provide a book ID to send to Kindle."
                )]
            
            logger.info(f"Sending book ID {book_id} to Kindle in {format_pref} format")
            
            # Kindle-compatible formats
            kindle_formats = {"mobi", "azw3", "pdf", "epub"}
            
            try:
                # Create temporary directory for export
                with tempfile.TemporaryDirectory() as temp_dir:
                    # First, try to export the preferred format
                    export_result = calibre_mgr.export_book(
                        book_id, temp_dir, [format_pref]
                    )
                    
                    target_file = None
                    actual_format = format_pref
                    
                    if export_result["success"]:
                        # Filter out metadata files (.opf) and only get actual ebook files
                        ebook_files = [
                            f for f in export_result["exported_files"] 
                            if not f.lower().endswith('.opf') and 
                            any(f.lower().endswith(f'.{fmt}') for fmt in kindle_formats)
                        ]
                        
                        # Look for the preferred format
                        for file_path in ebook_files:
                            if file_path.lower().endswith(f'.{format_pref.lower()}'):
                                target_file = file_path
                                break
                    
                    # If preferred format not found, try to export all formats and find a suitable one
                    if not target_file:
                        logger.info(f"Preferred format {format_pref} not found, trying all formats")
                        export_result = calibre_mgr.export_book(book_id, temp_dir, None)
                        
                        if export_result["success"]:
                            # Filter and prioritize Kindle-compatible formats
                            ebook_files = [
                                f for f in export_result["exported_files"] 
                                if not f.lower().endswith('.opf') and 
                                any(f.lower().endswith(f'.{fmt}') for fmt in kindle_formats)
                            ]
                            
                            # Priority order for Kindle: mobi > azw3 > epub > pdf
                            format_priority = ["mobi", "azw3", "epub", "pdf"]
                            
                            for fmt in format_priority:
                                for file_path in ebook_files:
                                    if file_path.lower().endswith(f'.{fmt}'):
                                        target_file = file_path
                                        actual_format = fmt
                                        break
                                if target_file:
                                    break
                    
                    # If still no suitable file and we have EPUB, convert it to MOBI
                    if not target_file:
                        epub_file = None
                        for file_path in export_result.get("exported_files", []):
                            if file_path.lower().endswith('.epub'):
                                epub_file = file_path
                                break
                        
                        if epub_file and format_pref in ["mobi", "azw3"]:
                            logger.info(f"Converting EPUB to {format_pref.upper()} for Kindle compatibility")
                            
                            conversion_result = calibre_mgr.convert_ebook(
                                epub_file, format_pref, None
                            )
                            
                            if conversion_result["success"]:
                                target_file = conversion_result["output_path"]
                                actual_format = format_pref
                            else:
                                logger.error(f"Conversion failed: {conversion_result['error']}")
                    
                    if not target_file:
                        return [TextContent(
                            type="text",
                            text=f"❌ No Kindle-compatible format found for book ID {book_id}. "
                                 f"Supported formats: {', '.join(kindle_formats)}"
                        )]
                    
                    logger.info(f"Sending file to Kindle: {target_file} (format: {actual_format})")
                    
                    # Send to Kindle using existing email functionality
                    try:
                        utils.send_email_to_kindle(target_file)
                        
                        # Get book info for response
                        book_info = calibre_mgr.get_book_info(book_id)
                        book_title = "Unknown Book"
                        if book_info["success"] and "Title" in book_info["metadata"]:
                            book_title = book_info["metadata"]["Title"]
                        
                        response = f"📱 Successfully sent to Kindle!\n"
                        response += f"📖 Book: {book_title}\n"
                        response += f"🆔 ID: {book_id}\n"
                        response += f"📄 Format: {actual_format.upper()}\n"
                        response += f"✉️ Sent to: {os.getenv('KINDLE_ADDRESS', 'configured Kindle address')}"
                        
                        # Add conversion note if format was changed
                        if actual_format != format_pref:
                            response += f"\n📝 Note: Converted from available format to {actual_format.upper()}"
                        
                        return [TextContent(type="text", text=response)]
                        
                    except Exception as e:
                        logger.error(f"Failed to send email to Kindle: {e}")
                        return [TextContent(
                            type="text",
                            text=f"❌ Failed to send email to Kindle: {str(e)}"
                        )]
            
            except Exception as e:
                logger.error(f"Error in send_book_to_kindle: {e}")
                return [TextContent(
                    type="text",
                    text=f"❌ Error sending book to Kindle: {str(e)}"
                )]
        
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