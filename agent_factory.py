import asyncio
import datetime
import zoneinfo
from mcp_agent.core.fastagent import FastAgent

# Get the local timezone dynamically
try:
    local_timezone = datetime.datetime.now().astimezone().tzinfo
except Exception:
    local_timezone = "UTC" # Fallback if timezone detection fails

def get_fast_agent_app(model_name: str):
    # Create the application
    fast = FastAgent(f"{model_name}-agent", config_path="fastagent.config.yaml")

    # Define the agent
    @fast.agent(
        instruction=(
            "You are a helpful assistant. Your primary focus is to manage uploaded documents. "
            "When a user provides a URL, you must determine if it's a direct link to a document (like a PDF) or a webpage. "
            "If it's a document, download it to a temporary location, extract the title, and save it with the title as the filename in the 'data/document' folder. "
            "If it's a webpage, you should first fetch and summarize the content of the webpage without downloading it. If the user then asks to save the webpage, you should use the `webpage_to_pdf` tool to convert the webpage to a PDF. The PDF should be saved in the 'data/document' folder, with a filename based on the webpage's title. "
            "Be sure to handle file names correctly, including spaces and other special characters. "
            "Uploaded attachments are saved to the 'attachment' folder. For URLs, you must use the `download_file` tool to save the document to the 'data/document' folder. "
            "When you crop a PDF, you must save the cropped file to the 'data/document/cropped' folder. "
            "When a user wants to preview a PDF, you should generate a medium-sized thumbnail of the first page and save it to the 'data/document/thumbnail' folder. Then, send the thumbnail to the user. "
            "When sending a document to Kindle, after the document has been sent, you must generate a thumbnail of the first page and attach it to your final message as a notification. "
            "After the document is in the correct location with the correct name, you must analyze its content. For binary documents like PDFs or Word files, "
            "you should extract their text content. To do this efficiently, first use a small `truncate_limit_tokens` (e.g., 200) to get a summary. "
            "After generating a summary, save it as a Markdown file with the same name as the document, but with a '.md' extension. "
            "For example, if the document is 'My Awesome Document.pdf', the summary file should be 'My Awesome Document.md'. "
            "In the future, when asked about the document's content, you can refer to this Markdown file for a quick summary.\n\n"
            "When you want to show an image to the user, use Markdown image syntax. The path must start from the 'data' directory. For example: '![alt text](data/thumbnail/image.jpg)'. "
            "You can also get weather information, get the current date and time, perform arithmetic calculations, "
            "and manage files. However, your core purpose is to be a document management assistant."
        ),
        model=model_name,
        servers=["weather", "utils", "time", "calculator", "context7", "filesystem"],
    )
    async def main_agent():
        pass # This agent will be controlled externally
    return fast

def reset_agent_context(agent_instance: FastAgent):
    # This function should clear the conversation history or reset the agent's state
    # For FastAgent, you might need to access its internal state or recreate it.
    # As a placeholder, we'll just log that it's being reset.
    print(f"Resetting context for agent: {agent_instance.name}")
    # In a real scenario, you might do something like:
    # agent_instance.clear_history()
    # Or if the agent doesn't expose a clear_history method, you might need to
    # re-initialize the agent instance itself.
