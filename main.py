import asyncio
import logging
import os
import datetime
import zoneinfo

from telegram import Update, ForceReply, ReplyKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from mcp_agent.core.fastagent import FastAgent
from openai_agent import get_fast_agent_app as get_openai_agent_app
from claude_agent import get_fast_agent_app as get_claude_agent_app

# Load environment variables from .env file
load_dotenv()

# Get Telegram bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file or environment variables.")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Agent instances (will be initialized later)
openai_agent_instance = None
claude_agent_instance = None

# Dictionary to store the current agent for each chat
current_agents = {}

# Get the local timezone dynamically
try:
    local_timezone = datetime.datetime.now().astimezone().tzinfo
except Exception:
    local_timezone = "UTC" # Fallback if timezone detection fails

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot that can talk to two different AI agents: OpenAI and Claude. "
        "Use /switch_agent to change the active agent."
    )
    # Set default agent for the chat
    current_agents[update.effective_chat.id] = "openai"

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        """Here are the commands you can use:

/start - Start a new conversation or reset the bot.
/help - Show this help message.
/switch_agent - Change the active AI agent (OpenAI or Claude).
/current_agent - Show which AI agent is currently active.

To talk to the agent, just send a message directly."""
    )
    await update.message.reply_text(help_text)

async def switch_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allows the user to switch between OpenAI and Claude agents."""
    chat_id = update.effective_chat.id
    current_agent_name = current_agents.get(chat_id, "openai") # Default to openai

    keyboard = [
        ["OpenAI", "Claude"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        f"Your current agent is {current_agent_name.capitalize()}. Which agent would you like to switch to?",
        reply_markup=reply_markup,
    )

async def current_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the currently active agent for the chat."""
    chat_id = update.effective_chat.id
    agent_name = current_agents.get(chat_id, "openai")
    await update.message.reply_text(f"Your current agent is: {agent_name.capitalize()}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    chat_id = update.effective_chat.id
    user_message = update.message.text

    agent_name = current_agents.get(chat_id, "openai")
    agent_to_use = None

    if agent_name == "openai":
        agent_to_use = openai_agent_instance
    elif agent_name == "claude":
        agent_to_use = claude_agent_instance
    else:
        await update.message.reply_text("Invalid agent selected. Please use /switch_agent.")
        return

    if agent_to_use:
        try:
            response_text = await agent_to_use.send(user_message)
            await update.message.reply_text(response_text)

        except Exception as e:
            logger.error(f"Error communicating with {agent_name} agent: {e}")
            await update.message.reply_text(f"Sorry, I encountered an error with the {agent_name} agent.")
    else:
        await update.message.reply_text("Agent not initialized. Please contact the bot administrator.")

async def post_init(application: Application) -> None:
    """Initialize agents and set bot commands after the bot is ready."""
    global openai_agent_instance, claude_agent_instance

    # Initialize OpenAI Agent
    openai_fast_app = get_openai_agent_app()
    async with openai_fast_app.run() as agent:
        openai_agent_instance = agent

    # Initialize Claude Agent
    claude_fast_app = get_claude_agent_app()
    async with claude_fast_app.run() as agent:
        claude_agent_instance = agent

    # Set bot commands for auto-completion menu
    await application.bot.set_my_commands([
        BotCommand("start", "Start a new conversation or reset the bot"),
        BotCommand("help", "Show available commands and their usage"),
        BotCommand("switch_agent", "Change the active AI agent"),
        BotCommand("current_agent", "Show which AI agent is currently active"),
    ])

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("switch_agent", switch_agent))
    application.add_handler(CommandHandler("current_agent", current_agent))

    # on non command messages - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
