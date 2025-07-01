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
            "You are a helpful assistant. Your primary focus is to analyze documents uploaded by the user and build a knowledge base from them. "
            "You will use a knowledge graph memory server to store and retrieve information.\n\n"
            "When a user uploads a document as an attachment, it will be downloaded to the 'attachment' folder. "
            "You must then identify its file type and move it to a more appropriate subdirectory within 'data' "
            "(e.g., 'document', 'pictures', 'audio', 'video'). Pictures sent directly are saved to the 'pictures' folder automatically.\n\n"
            "After the document is in the correct location, you must analyze its content. For binary documents like PDFs or Word files, "
            "you should extract their text content. Once you have the text, identify key entities, concepts, and relationships.\n\n"
            "You will then use the memory server to:\n"
            "1. Create entities for the document itself, its author(s), and key concepts within it.\n"
            "2. Create relationships between these entities. For example, a document 'is authored by' a person, and 'discusses' a particular topic.\n"
            "3. Add specific observations and facts from the document to the corresponding entities in your memory.\n\n"
            "When a user asks a question, you will first search your memory for relevant information. "
            "If the answer is found in a document you have processed, you should indicate which document contains the information.\n\n"
            "You can also get weather information, download binary files from URLs, get the current date and time, perform arithmetic calculations, "
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
