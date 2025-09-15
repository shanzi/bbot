# bbot - AI-Powered Document Management Telegram Bot

This project implements a sophisticated Telegram bot that integrates with `fast-agent` to provide AI-powered document management capabilities using multiple LLMs (OpenAI, Claude, Gemini). The bot specializes in document processing, PDF manipulation, web content conversion, and general AI assistance through Model Context Protocol (MCP) servers.

## 🎬 Demo Videos

- **📄 Managing Papers**: [Document Processing & Analysis](https://www.youtube.com/shorts/B_gIf8acNjc)
- **🎥 Managing Movies**: [VLC Chromecast Control](https://www.youtube.com/shorts/FS5S8OySMws)

## Features

### 🤖 **Multi-Agent AI Support**
*   **8 AI Models Available:** OpenAI GPT-5 (default)/GPT-5-mini/GPT-5-nano/GPT-4o-mini, Claude Sonnet 3.7/4/Opus 4.1, Gemini 2.5 Pro/Flash
*   **Dynamic Model Switching:** Change AI agents mid-conversation with inline keyboard
*   **Per-Chat Agent Memory:** Each chat maintains its own agent instance and conversation history
*   **Context Management:** Built-in context trimming and token estimation

### 📄 **Document Management**
*   **PDF Processing:** Text extraction, thumbnail generation, margin trimming
*   **File Upload Support:** Documents and images with automatic processing
*   **Multimodal Image Support:** Send images with captions directly to AI models for analysis
*   **Webpage to PDF:** Convert web pages to PDF documents for storage
*   **Document Summarization:** Automatic content analysis and markdown summary generation
*   **Organized Storage:** Structured folder system (documents, attachments, thumbnails, cropped, trash)

### 📧 **Email & Delivery**
*   **Email Integration:** Send documents via Gmail with attachments
*   **Kindle Support:** Direct document delivery to Kindle devices
*   **Notification System:** Visual confirmations with thumbnail previews

### 🛠 **MCP Server Integration**
*   **Weather Information:** Real-time weather data (`mcp-weather-server`)
*   **Web Content Fetching:** URL content retrieval (`mcp-server-fetch`)
*   **Date/Time Services:** Timezone-aware time information (`mcp-server-time`)
*   **Calculator:** Arithmetic calculations (`mcp-server-calculator`)
*   **File System:** Advanced file operations (`@modelcontextprotocol/server-filesystem`)
*   **Vector Search:** Document similarity search (`@upstash/context7-mcp`)
*   **Custom PDF Tools:** Specialized PDF processing utilities
*   **VLC Chromecast:** Stream movies to TV with playback control

### 💬 **Telegram Bot Commands**
*   `/start`: Initialize bot and select AI model
*   `/status`: Show current agent, context length, and token count
*   `/help`: Display available commands and usage
*   `/trim_context <number>`: Trim conversation history to specified message count
*   **File Uploads:** Drag & drop documents and images for processing
*   **Image Analysis:** Send images with captions for AI visual analysis (512x512 optimized)
*   **Movie Streaming:** Ask to watch movies and control Chromecast playback
*   **Inline Responses:** Real-time processing updates and media sharing

## Setup

### Prerequisites

*   **Python 3.12+**
*   **`uv`** - Modern Python package manager
*   **System Tools:** `poppler-utils`, `wkhtmltopdf` (for PDF processing), `vlc` (for Chromecast streaming)
*   **API Keys:** Telegram Bot Token, AI provider API keys
*   **Optional:** Gmail account for email features, Chromecast device for movie streaming

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/bbot.git
    cd bbot
    ```

2.  **Install `uv` (if you haven't already):**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    Make sure `uv` is in your PATH after installation.

3.  **Install dependencies:**
    ```bash
    uv sync
    ```
    This will automatically install all dependencies from `pyproject.toml`.

4.  **Install system dependencies:**
    ```bash
    # Ubuntu/Debian
    sudo apt-get install poppler-utils wkhtmltopdf vlc
    
    # macOS (with Homebrew)
    brew install poppler wkhtmltopdf vlc
    ```

5.  **Create environment configuration:**
    
    **a. Create `.env` file:**
    ```bash
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    
    # Email Configuration (optional - for document delivery)
    GMAIL_ADDRESS="your-email@gmail.com"
    GMAIL_APP_PASSWORD="your-app-password"
    KINDLE_ADDRESS="your-kindle@kindle.com"
    ALLOWED_EMAIL_ADDRESSES="user1@example.com,user2@example.com"
    
    # VLC Chromecast Configuration (optional - for movie streaming)
    CHROMECAST_IP="192.168.0.203"
    ```
    
    **b. Create `fastagent.secrets.yaml`:**
    ```yaml
    anthropic:
      api_key: "YOUR_ANTHROPIC_API_KEY"
    openai:
      api_key: "YOUR_OPENAI_API_KEY"
    google:
      api_key: "YOUR_GOOGLE_API_KEY"  # For Gemini models
    ```

6.  **Set up data directories:**
    ```bash
    mkdir -p data/{document/{cropped,thumbnail},attachment,pictures,trash}
    ```

## Usage

### Starting the Bot

```bash
uv run python main.py
```

### Basic Workflow

1. **Start a conversation:** Send `/start` to select your preferred AI model
2. **Upload documents:** Drag & drop PDFs, images, or other files
3. **Process content:** The bot automatically analyzes and summarizes documents
4. **Ask questions:** Query the AI about uploaded content or general topics
5. **Manage files:** Use built-in commands to organize, preview, or delete documents

### Advanced Features

#### Document Processing
- **PDF Text Extraction:** Automatically extracts and summarizes content
- **Thumbnail Generation:** Creates preview images for PDFs
- **Margin Trimming:** Removes whitespace from PDF pages
- **Format Conversion:** Convert web pages to PDFs
- **Image Processing:** Automatic image compression and optimization for AI analysis

#### File Management
- **Organized Storage:** Files are automatically categorized
- **Trash System:** Deleted files are moved to trash before permanent deletion
- **Search Capabilities:** Find documents using vector similarity search

#### Email Integration
- **Document Sharing:** Send processed documents via email
- **Kindle Delivery:** Direct document delivery to Kindle devices
- **Notification Previews:** Thumbnail confirmations for sent documents
- **Email Allow List:** Security feature to restrict email recipients

#### VLC Chromecast Streaming
- **Movie Library:** Automatic scanning of `/media/chase/Secondary/Movies`
- **Search & Discovery:** Find movies by name with intelligent matching
- **Chromecast Control:** Stream movies directly to TV with VLC
- **Playback Management:** Play, pause, stop, seek, and volume control
- **Environment Configuration:** Customizable Chromecast IP address

## Project Structure

```
bbot/
├── main.py                 # Main Telegram bot application
├── agent_factory.py        # AI agent creation and management
├── utils.py               # Utility functions for file operations
├── vlc.py                 # VLC Chromecast controller
├── mcp_server_utils.py    # Custom MCP server for PDF tools
├── mcp_vlc_server.py      # VLC Chromecast MCP server
├── fastagent.config.yaml  # MCP server configuration
├── data/                  # Document storage
│   ├── document/          # Main document storage
│   │   ├── cropped/       # Processed PDFs with trimmed margins
│   │   └── thumbnail/     # Generated preview images
│   ├── attachment/        # User uploaded files
│   ├── pictures/          # Image files
│   └── trash/             # Deleted files
└── CLAUDE.md             # Development documentation
```

## Contributing

This project uses modern Python development practices:

- **Code Quality:** All code follows pylint best practices
- **Type Safety:** Comprehensive type hints throughout
- **Documentation:** Detailed docstrings for all functions
- **Modular Design:** Clean separation of concerns
- **Error Handling:** Robust exception handling with proper chaining

See `CLAUDE.md` for detailed development guidance when working with Claude Code.

## License

This project is open source. Please check the license file for details.


