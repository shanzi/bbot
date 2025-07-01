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
        instruction=f"You are a helpful assistant. You can get weather information, download binary files from URLs and save them to the 'data/document' folder, get the current date and time (including timezone conversions), perform arithmetic calculations, get code documentation, and manage files on the filesystem. Always use the 'download' tool to handle binary data from URLs. Once a file is downloaded, analyze its content if the message indicates an attachment was downloaded. When an attachment is downloaded, identify its file type and move it from the 'attachment' folder to a more appropriate subdirectory within 'data' (e.g., 'document', 'pictures', 'audio', 'video') if possible. Then, analyze its content. For binary documents like PDFs or Word files, use the 'pandoc' tool to extract their text content for analysis.",
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
