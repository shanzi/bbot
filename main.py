import asyncio
import logging
import os
import datetime
import zoneinfo
import time
import utils

from telegram import Update, ForceReply, ReplyKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode, ChatAction
from telegramify_markdown import markdownify
from dotenv import load_dotenv

from mcp_agent.core.fastagent import FastAgent
from agent_factory import get_fast_agent_app, reset_agent_context

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

# Dictionary to store initialized agent instances
agent_instances = {}

# Define supported models
SUPPORTED_MODELS = {
    "openai-mini": "openai.gpt-4o-mini",
    "openai-o3": "openai.o3",
    "openai-o3-pro": "openai.o3-pro",
    "claude-sonnet": "anthropic.claude-3-5-sonnet-latest",
    "claude-opus": "anthropic.claude-3-opus-20240229",
    "claude-haiku": "anthropic.claude-3-haiku-20240307",
    "gemini-pro": "google.gemini-pro",
    "gemini-flash": "google.gemini-2.5-flash",
}

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
    current_agents[update.effective_chat.id] = list(SUPPORTED_MODELS.keys())[0]

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
    """Allows the user to switch between different AI models."""
    chat_id = update.effective_chat.id
    current_model_alias = current_agents.get(chat_id, "claude") # Default to claude

    keyboard = [
        [alias for alias in SUPPORTED_MODELS.keys()]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        f"Your current model is {current_model_alias.capitalize()}. Which model would you like to switch to?",
        reply_markup=reply_markup,
    )

async def current_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the currently active agent for the chat."""
    chat_id = update.effective_chat.id
    agent_alias = current_agents.get(chat_id, "claude")
    await update.message.reply_text(f"Your current agent is: {agent_alias.capitalize()}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    chat_id = update.effective_chat.id

    # Handle text messages
    user_message = update.message.text or ""
    
    if update.message.document:
        doc = update.message.document
        file = await context.bot.get_file(doc.file_id)
        target_dir = utils.get_save_directory("attachment")
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, f"{int(time.time()*1000)}--{doc.file_name}")
        await file.download_to_drive(target)

        user_message += f"(attachment downloaded to {target})"

    for alias, model_name in SUPPORTED_MODELS.items():
        if user_message.lower() == alias.lower():
            current_agents[chat_id] = alias
            await update.message.reply_text(f"Switched to {alias.capitalize()} agent (model: {model_name}).")
            return

    agent_name = current_agents.get(chat_id, "claude")
    agent_to_use = agent_instances.get(agent_name)

    if agent_to_use:
        try:
            # Send typing action
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

            # Get the actual BaseAgent instance from the AgentApp
            # Since we only have one agent per FastAgent instance, we can get the first one
            actual_agent = next(iter(agent_to_use._agents.values()))
            
            # Generate the response as a PromptMessageMultipart object
            response_multipart = await actual_agent.generate([actual_agent._normalize_message_input(user_message)], None)

            # Get only the last text content (final assistant response)
            response_text = response_multipart.last_text()

            telegram_response = markdownify(response_text)
            await update.message.reply_text(telegram_response, parse_mode=ParseMode.MARKDOWN_V2)

        except Exception as e:
            logger.error(f"Error communicating with {agent_name} agent: {e}")
            await update.message.reply_text(f"Sorry, I encountered an error with the {agent_name} agent.")
    else:
        await update.message.reply_text("Agent not initialized. Please contact the bot administrator.")

async def post_init(application: Application) -> None:
    """Initialize agents and set bot commands after the bot is ready."""
    # Initialize agents
    global agent_instances
    for alias, model_name in SUPPORTED_MODELS.items():
        fast_app = get_fast_agent_app(model_name)
        async with fast_app.run() as agent:
            agent_instances[alias] = agent

    # Set bot commands for auto-completion menu
    await application.bot.set_my_commands([
        BotCommand("start", "Start a new conversation or reset the bot"),
        BotCommand("help", "Show available commands and their usage"),
        BotCommand("switch_agent", "Change the active AI agent"),
        BotCommand("current_agent", "Show which AI agent is currently active"),
        BotCommand("clear_context", "Clear the current agent's conversation context"),
    ])

async def clear_context_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the context of the currently active agent."""
    agent_name = current_agents.get(chat_id, "claude")
    agent_to_use = agent_instances.get(agent_name)
    
    if agent_to_use:
        reset_agent_context(agent_to_use)
        await update.message.reply_text(f"Context for {agent_name.capitalize()} agent has been cleared.")
    else:
        await update.message.reply_text("No active agent to clear context for.")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("switch_agent", switch_agent))
    application.add_handler(CommandHandler("current_agent", current_agent))
    application.add_handler(CommandHandler("clear_context", clear_context_command))

    # on non command messages - echo the message on Telegram
    application.add_handler(MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.ATTACHMENT, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
