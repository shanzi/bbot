import asyncio
import datetime
import zoneinfo
from mcp_agent.core.fastagent import FastAgent

# Get the local timezone dynamically
try:
    local_timezone = datetime.datetime.now().astimezone().tzinfo
except Exception:
    local_timezone = "UTC" # Fallback if timezone detection fails

# Create the application
fast = FastAgent("fast-agent example", config_path="fastagent.config.yaml")

# Define the agent
@fast.agent(
    instruction=f"You are a helpful assistant. You can get weather information, fetch web content, get the current date and time (currently in {local_timezone}), and perform arithmetic calculations.",
    model="openai.gpt-4o-mini",
    servers=["weather", "fetch", "datetime", "calculator"],
)
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())