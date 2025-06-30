import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("fast-agent example", config_path="fastagent.config.yaml")

# Define the agent
@fast.agent(
    instruction="You are a helpful assistant.",
    model="openai.gpt-4o-mini",
)
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent("Hello, world!")

if __name__ == "__main__":
    asyncio.run(main())
