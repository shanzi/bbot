# bbot - Telegram Bot with FastAgent AI Integration

This project implements a Telegram bot that integrates with `fast-agent` to provide AI capabilities using both OpenAI and Claude LLMs. The bot can answer questions, perform calculations, fetch web content, get weather information, and tell the current date and time.

## Features

*   **Multi-Agent Support:** Switch between OpenAI, Claude, and Gemini agents.
*   **Modular Design:** Agent definitions are handled dynamically based on selected model.
*   **MCP Server Integration:** Utilizes pre-built Model Context Protocol (MCP) servers for:
    *   Weather information (`mcp-weather-server`)
    *   Web content fetching (`mcp-server-fetch`)
    *   Current date and time (`mcp-datetime`)
    *   Arithmetic calculations (`mcp-server-calculator`)
*   **Telegram Bot Commands:**
    *   `/start`: Start a new conversation or reset the bot.
    *   `/help`: Show available commands and their usage.
    *   `/switch_agent`: Change the active AI agent (OpenAI or Claude) via an inline keyboard.
    *   `/current_agent`: Show which AI agent is currently active.
*   **Dynamic Timezone:** The agent's instruction dynamically includes the local timezone of the server it's running on.

## Setup

### Prerequisites

*   Python 3.12+
*   `uv` (recommended Python package manager)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd bbot
    ```
2.  **Install `uv` (if you haven't already):**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    (Make sure `uv` is in your PATH)
3.  **Initialize `uv` project and install dependencies:**
    ```bash
    uv init
    uv pip install -r requirements.txt # Or uv pip install fast-agent-mcp mcp-datetime mcp-server-calculator mcp-server-fetch mcp-weather-server python-telegram-bot python-dotenv
    uv lock
    ```
    *(Note: `requirements.txt` is not explicitly created in this session, but `uv lock` will manage dependencies based on `pyproject.toml`)*
4.  **Create `.env` file:**
    Create a file named `.env` in the project root and add your Telegram Bot Token:
    ```
    TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    ```
    Replace `"YOUR_TELEGRAM_BOT_TOKEN"` with the token obtained from BotFather on Telegram.
5.  **Configure FastAgent Secrets:**
    Create a file named `fastagent.secrets.yaml` in the project root and add your API keys for OpenAI and Anthropic:
    ```yaml
    anthropic:
      api_key: "YOUR_ANTHROPIC_API_KEY"
    openai:
      api_key: "YOUR_OPENAI_API_KEY"
    ```
    Replace `"YOUR_ANTHROPIC_API_KEY"` and `"YOUR_OPENAI_API_KEY"` with your actual API keys.

## Running the Bot

To start the Telegram bot:

```bash
uv run python main.py
```


