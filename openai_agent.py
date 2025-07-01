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
    fast = FastAgent("openai-agent", config_path="fastagent.config.yaml")

    # Define the agent
    @fast.agent(
        instruction=f"You are a helpful assistant. You can get weather information, download binary files from URLs and save them to the 'data/document' folder, get the current date and time (including timezone conversions), perform arithmetic calculations, get code documentation, and manage files on the filesystem. Always use the 'download' tool to handle binary data from URLs.",
        model="openai.gpt-4o-mini",
        servers=["weather", "download", "datetime", "calculator", "context7", "filesystem"],
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