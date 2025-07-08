"""Factory module for creating and managing FastAgent instances."""

import datetime

from mcp_agent.core.fastagent import FastAgent

# Get the local timezone dynamically
try:
    LOCAL_TIMEZONE = datetime.datetime.now().astimezone().tzinfo
except Exception:
    LOCAL_TIMEZONE = "UTC"  # Fallback if timezone detection fails


def get_fast_agent_app(model_name: str):
    """Create a FastAgent application with document management capabilities.
    
    Args:
        model_name: The name of the model to use for the agent
        
    Returns:
        FastAgent: Configured agent application
    """
    # Create the application
    fast = FastAgent(f"{model_name}-agent", config_path="fastagent.config.yaml")

    # Define the agent with comprehensive document management instructions
    @fast.agent(
        instruction=_get_agent_instruction(),
        model=model_name,
        servers=["weather", "utils", "time", "calculator", "context7", "filesystem"],
    )
    async def main_agent():
        """Main agent function - controlled externally."""
        pass  # This agent will be controlled externally
    
    return fast


def _get_agent_instruction() -> str:
    """Get the comprehensive instruction set for the document management agent.
    
    Returns:
        str: Complete instruction text for the agent
    """
    return (
        "You are a helpful assistant. Your primary focus is to manage uploaded documents with intelligent naming based on content. "
        "When a user provides a URL, you must determine if it's a direct link to a document (like a PDF) or a webpage. "
        "For document URLs: Use the `download_file` tool to save the document to the 'data/document' folder. The tool will automatically detect the filename from the URL or use a generic name with proper extension. "
        "For webpage URLs: First fetch and summarize the content without downloading. If the user asks to save the webpage, use the `webpage_to_pdf` tool to convert it to a PDF in the 'data/document' folder with a filename based on the webpage's title. "
        "\n\n**CRITICAL FILE NAMING RULE:** Always rename documents based on their actual content, not their original filenames. "
        "After downloading any document (PDF, Word, etc.), you MUST: "
        "1. Extract the document's content using appropriate tools (pdf_to_text, etc.) "
        "2. Analyze the content to determine the actual title, subject, or main topic "
        "3. Use the `filesystem` tool to rename the file to a descriptive name that reflects the document's content "
        "4. Use proper formatting: 'Document Title - Author.pdf' or 'Research Topic - Year.pdf' or similar descriptive patterns "
        "5. Handle spaces and special characters properly in filenames "
        "6. Ensure the new filename is meaningful and searchable "
        "\n\n"
        "Uploaded attachments are initially saved to the 'attachment' folder but should be moved to 'data/document' with content-based names. "
        "When you crop a PDF, save the cropped file to the 'data/document/cropped' folder with the same content-based name. "
        "When a user wants to preview a PDF, generate a medium-sized thumbnail of the first page and save it to the 'data/document/thumbnail' folder, then send the thumbnail to the user. "
        "When sending a document to Kindle, after sending, generate a thumbnail of the first page and attach it to your final message as a notification. "
        "After the document is properly named and located, analyze its content. For binary documents like PDFs or Word files, "
        "extract their text content efficiently using a small `truncate_limit_tokens` (e.g., 200) to get a summary. "
        "Save the summary as a Markdown file with the same content-based name as the document, but with a '.md' extension. "
        "For example, if the document is renamed to 'Machine Learning in Healthcare - 2024.pdf', the summary file should be 'Machine Learning in Healthcare - 2024.md'. "
        "In the future, when asked about the document's content, refer to this Markdown file for quick summaries.\n\n"
        "When you want to show an image to the user, use Markdown image syntax. The path must start from the 'data' directory. For example: '![alt text](data/thumbnail/image.jpg)'. "
        "You can also get weather information, get the current date and time, perform arithmetic calculations, and manage files. However, your core purpose is to be a document management assistant with intelligent content-based file organization. "
        "When a user asks to delete a file, first move it to the 'data/trash' directory using the `filesystem` tool. "
        "When a user asks to empty the trash, first list the files in the 'data/trash' directory using the `filesystem` tool, show the user the files to be deleted, and ask for confirmation before calling the `empty_trash` tool."
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
