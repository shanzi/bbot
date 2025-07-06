# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot that integrates with FastAgent to provide AI capabilities using multiple LLMs (OpenAI, Claude, Gemini). The bot specializes in document management, web content processing, and general AI assistance through MCP (Model Context Protocol) servers.

## Development Commands

### Running the Bot
```bash
uv run python main.py
```

### Python Environment
- Uses `uv` for dependency management
- Python 3.12+ required
- Dependencies are managed through `pyproject.toml` and `uv.lock`

### Environment Setup
Required environment variables in `.env`:
- `TELEGRAM_BOT_TOKEN`: Telegram bot token from BotFather
- `GMAIL_ADDRESS`: Gmail address for email functionality
- `GMAIL_APP_PASSWORD`: Gmail app password for email
- `KINDLE_ADDRESS`: Kindle email address for document delivery

API keys in `fastagent.secrets.yaml`:
- `anthropic.api_key`: For Claude models
- `openai.api_key`: For OpenAI models

## Architecture

### Core Components

1. **main.py**: Telegram bot implementation
   - Handles user interactions and commands
   - Manages agent instances per chat
   - Supports file uploads (documents, images)
   - Provides agent switching capabilities

2. **agent_factory.py**: Agent creation and management
   - Creates FastAgent instances with specific model configurations
   - Configures MCP servers for each agent
   - Manages agent lifecycle and context

3. **utils.py**: Utility functions
   - File operations (download, save, email)
   - PDF processing helpers
   - Token counting and context management

4. **mcp_server_utils.py**: Custom MCP server
   - PDF processing tools (text extraction, image conversion, margin trimming)
   - File management operations
   - Email and Kindle integration

### MCP Server Integration

The bot uses multiple MCP servers configured in `fastagent.config.yaml`:
- `weather`: Weather information
- `time`: Date/time with timezone support
- `calculator`: Arithmetic calculations
- `context7`: Vector similarity search
- `filesystem`: File system operations
- `utils`: Custom PDF/document processing tools

### Agent Models

Supported models defined in `SUPPORTED_MODELS`:
- Claude: sonnet-3, sonnet-3.7, sonnet-4
- OpenAI: gpt-4o-mini, o3
- Gemini: 2.5-pro, 2.5-flash

### Data Structure

- `data/document/`: Main document storage
- `data/document/cropped/`: Cropped PDF files
- `data/document/thumbnail/`: PDF thumbnails
- `data/attachment/`: Uploaded attachments
- `data/pictures/`: Image files
- `data/trash/`: Deleted files

## Key Features

### Document Management
- PDF text extraction and processing
- PDF to image conversion for previews
- Margin trimming for PDFs
- Webpage to PDF conversion
- Document summarization and markdown generation

### Communication
- Telegram bot with inline keyboards
- Email sending with attachments
- Kindle document delivery
- Multi-agent switching within conversations

### File Operations
- File upload handling
- Trash management with recovery
- Context trimming for conversation management
- Token counting and estimation

## Development Notes

- Agent instances are managed per chat ID
- FastAgent uses async context managers for proper lifecycle
- File paths use absolute paths from the `data/` directory
- Images are displayed using Markdown syntax with `data/` prefix
- Context trimming helps manage token limits across conversations