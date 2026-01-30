"""Factory module for creating and managing FastAgent instances."""

import datetime
import os

from fast_agent import FastAgent

# Get the local timezone dynamically
try:
    LOCAL_TIMEZONE = datetime.datetime.now().astimezone().tzinfo
except Exception:
    LOCAL_TIMEZONE = "UTC"  # Fallback if timezone detection fails


def get_fast_agent_app(model_name: str, chat_id: int = None):
    """Create a FastAgent application with document management capabilities.

    Args:
        model_name: The name of the model to use for the agent
        chat_id: The Telegram chat ID for this agent session (used for reminders)

    Returns:
        FastAgent: Configured agent application
    """
    # Get the skills directory path (relative to this file)
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")

    # Create the application with skills directory
    fast = FastAgent(
        f"{model_name}-agent",
        config_path="fastagent.config.yaml",
        skills_directory=skills_dir
    )

    # Define the agent with MCP servers and skills
    @fast.agent(
        instruction=_get_agent_instruction(chat_id),
        model=model_name,
        servers=["utils", "time", "calculator", "fetch", "filesystem", "calibre", "sms",
                 "transmission", "search", "reminder"],
        skills=skills_dir,
    )
    async def main_agent():
        """Main agent function - controlled externally."""
        pass  # This agent will be controlled externally

    return fast


def _get_agent_instruction(chat_id: int = None) -> str:
    """Get the core instruction set for the agent.

    Args:
        chat_id: The Telegram chat ID for this agent session

    Returns:
        str: Base instruction text for the agent
    """
    chat_id_info = f"\n\n**IMPORTANT: Your Telegram Chat ID is {chat_id}**\n" \
                   f"When creating reminders using the `add_reminder` tool, you MUST include this chat_id as a parameter.\n" \
                   f"This ensures reminders are sent to the correct Telegram chat.\n" if chat_id else ""

    return (
        "You are a helpful AI assistant with specialized skills in document management, "
        "ebook organization, SMS handling, torrent management, and web content processing. "
        "\n\n"
        "Your skills are defined in separate skill files that provide detailed guidance for each area of expertise. "
        "When a user's request matches one of your skills, the relevant skill instructions will be loaded automatically. "
        "\n\n"
        "## Core Principles\n"
        "1. **Content-Based Organization**: Always name files based on their actual content, not original filenames\n"
        "2. **ASCII-Safe Naming**: Use only ASCII characters, hyphens, underscores, and dots in filenames - never use parentheses, brackets, or special characters\n"
        "3. **User Guidance**: Explain what you're doing and why, especially for file operations\n"
        "4. **Safety First**: Move files to trash before deletion, ask for confirmation on destructive operations\n"
        "5. **Quality**: Create summaries, thumbnails, and metadata to enhance usability\n"
        "\n\n"
        "## Available Skills\n"
        "Your specialized skills will be loaded when needed:\n"
        "- **Document Management**: Intelligent file organization with content-based naming\n"
        "- **PDF Processing**: Extract, crop, convert, and preview PDF files\n"
        "- **SMS Management**: Query and manage messages from connected Android devices\n"
        "- **Ebook Management**: Calibre library integration for ebook organization and Kindle delivery\n"
        "- **Torrent Management**: BitTorrent download management with intelligent routing\n"
        "- **Web Content**: Download files from URLs and convert webpages to PDF\n"
        "- **Reminder Management**: Create, track, and manage scheduled reminders and tasks\n"
        "\n\n"
        "## MCP Servers Available\n"
        "You have access to these MCP servers for additional capabilities:\n"
        "- `utils`: Custom PDF/document processing tools\n"
        "- `time`: Date/time operations with timezone support\n"
        "- `calculator`: Arithmetic calculations\n"
        "- `fetch`: Web content fetching\n"
        "- `filesystem`: File system operations\n"
        "- `calibre`: Ebook library management\n"
        "- `sms`: SMS message access via ADB\n"
        "- `transmission`: BitTorrent client control\n"
        "- `search`: Web search capabilities\n"
        "- `reminder`: Create and manage reminders/scheduled tasks\n"
        f"{chat_id_info}"
        "\n\n"
        "{{agentSkills}}\n"
        "\n\n"
        "The current date and time is: {{currentDate}}\n"
        "Timezone: " + str(LOCAL_TIMEZONE)
    )

def reset_agent_context(agent_instance: FastAgent) -> None:
    """Reset the conversation history or state of an agent instance.
    
    Args:
        agent_instance: The FastAgent instance to reset
        
    Note:
        This is a placeholder implementation. In a real scenario, you might need
        to access the agent's internal state or recreate the instance entirely.
    """
    print(f"Resetting context for agent: {agent_instance.name}")
    # In a real scenario, you might do something like:
    # agent_instance.clear_history()
    # Or if the agent doesn't expose a clear_history method, you might need to
    # re-initialize the agent instance itself.
