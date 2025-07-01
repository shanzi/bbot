import asyncio
import datetime
import zoneinfo
from mcp_agent.core.fastagent import FastAgent

# Get the local timezone dynamically
try:
    local_timezone = datetime.datetime.now().astimezone().tzinfo
except Exception:
    local_timezone = "UTC" # Fallback if timezone detection fails

def get_fast_agent_app():
    # Create the application
    fast = FastAgent("claude-agent", config_path="fastagent.config.yaml")

    # Define the agent
    @fast.agent(
        instruction=f"You are a helpful assistant. You can get weather information, download binary files from URLs and save them to the 'data/document' folder, get the current date and time (including timezone conversions), perform arithmetic calculations, get code documentation, and manage files on the filesystem. Always use the 'download' tool to handle binary data from URLs. Once a file is downloaded, analyze its content if the message indicates an attachment was downloaded. When an attachment is downloaded, identify its file type and move it from the 'attachment' folder to a more appropriate subdirectory within 'data' (e.g., 'document', 'pictures', 'audio', 'video') if possible. Then, analyze its content. For PDF files, use the 'pdftotext' tool to extract their text content for analysis. For other binary documents like Word files, use the 'utils.document_to_markdown' tool to extract their text content for analysis.",
        model="anthropic.claude-3-5-sonnet-latest",
        servers=["weather", "utils", "time", "calculator", "context7", "filesystem", "pdftotext"],
    )
    async def main_agent():
        pass # This agent will be controlled externally
    return fast

async def main():
    fast_app = get_fast_agent_app()
    async with fast_app.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())
