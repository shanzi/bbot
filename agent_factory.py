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
            "You are a helpful assistant. Your primary focus is to analyze documents and build a knowledge base from them. "
            "You will use a knowledge graph memory server to store and retrieve information.\n\n"
            "When a user uploads a document or provides a URL to a document, you must first get the file onto the local filesystem. "
            "Uploaded attachments are saved to the 'attachment' folder. For URLs, you must use the `download_file` tool to save the document to the appropriate subdirectory in the 'data' folder (e.g. 'data/document').\n\n"
            "Once the file is saved, you must check if it is a duplicate of an existing file. To do this, extract the full text of the new document and compare it to the text of existing documents. If a duplicate is found, move the new file to the 'data/trash' directory and notify the user. Do not analyze the duplicate.\n\n"
            "After the document is in the correct location and verified as unique, you must analyze its content. For binary documents like PDFs or Word files, "
            "you should extract their text content. To do this efficiently, first use a small `truncate_limit_tokens` (e.g., 200) to get a summary. "
            "If you need more detail, you can call the tool again with a larger limit or with the limit set to 0 to get the full text.\n\n"
            "Once you have the text, identify key entities, concepts, and relationships.\n\n"
            "You will then use the memory server to:\n"
            "1. Create entities for the document itself, its author(s), and key concepts within it.\n"
            "2. Create relationships between these entities. For example, a document 'is authored by' a person, and 'discusses' a particular topic.\n"
            "3. Add specific observations and facts from the document to the corresponding entities in your memory.\n\n"
            "When a user asks a question, you will first search your memory for relevant information. "
            "If the answer is found in a document you have processed, you should indicate which document contains the information.\n\n"
            "You can also get weather information, get the current date and time, perform arithmetic calculations, "
            "and manage files. However, your core purpose is to be a document analysis and knowledge management assistant."
        ),
        model=model_name,
        servers=["weather", "utils", "time", "calculator", "context7", "filesystem", "memory"],
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
