import asyncio
import logging
import os
import datetime
import zoneinfo
import time
import utils

from telegram import Update, ForceReply, ReplyKeyboardMarkup, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued, and ask for model selection."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot that can talk to different AI models. "
        "Please choose a model to start our conversation."
    )

    aliases = list(SUPPORTED_MODELS.keys())
    keyboard = [
        [InlineKeyboardButton(alias.capitalize(), callback_data=alias) for alias in aliases[i:i + 2]]
        for i in range(0, len(aliases), 2)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Which model would you like to use?",
        reply_markup=reply_markup,
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        """Here are the commands you can use:

/start - Start a new conversation or reset the bot.
/status - Show current bot's status.
/help - Show this help message.

To talk to the agent, just send a message directly."""
    )
    await update.message.reply_text(help_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the currently active agent for the chat."""
    chat_id = update.effective_chat.id
    agent_alias = current_agents.get(chat_id, "openai-mini")
    agent_instance = agent_instances.get(chat_id)

    status_text = f"Your current agent is: **{agent_alias.capitalize()}**\n"
    status_text += f"Initialized: **{agent_instance is not None}**\n\n"

    if agent_instance:
        # Get the actual BaseAgent instance
        actual_agent = next(iter(agent_instance._agents.values()))

        # Get context length
        context_length = len(actual_agent.get_context())
        status_text += f"Context Length: **{context_length}**\n"

        # Get available tools
        tools = actual_agent.get_tools()
        if tools:
            tool_names = [f"`{tool.name}`" for tool in tools]
            status_text += f"Available Tools: {', '.join(tool_names)}\n"
        else:
            status_text += "Available Tools: **None**\n"

    status_message = markdownify(status_text)
    await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN_V2)


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

    agent_alias = current_agents.get(chat_id, "openai-mini")
    agent_to_use = agent_instances.get(chat_id)

    if not agent_to_use:
        model_name = SUPPORTED_MODELS.get(agent_alias)
        if model_name:
            fast_app = get_fast_agent_app(model_name)
            # IMPORTANT: Use 'async with' to ensure proper FastAgent lifecycle management.
            # Do not revert to 'await fast_app.run()' as it can lead to resource leaks.
            async with fast_app.run() as agent:
                agent_instances[chat_id] = agent
                agent_to_use = agent_instances[chat_id]
        else:
            await update.message.reply_text("Invalid agent selected. Please use /start to select an agent.")
            return

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
            await update.message.reply_text(telegram_response, parse_mode=ParseMode.MARKDOWN_V2, reply_to_message_id=update.message.message_id)

        except Exception as e:
            logger.error(f"Error communicating with {agent_alias} agent: {e}")
            await update.message.reply_text(f"Sorry, I encountered an error with the {agent_alias} agent.")
    else:
        await update.message.reply_text("Agent not initialized. Please contact the bot administrator.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    selected_alias = query.data

    if selected_alias in SUPPORTED_MODELS:
        current_agents[chat_id] = selected_alias
        # Reset agent context when switching models
        agent_instances.pop(chat_id, None)
        await query.edit_message_text(text=f"Switched to {selected_alias.capitalize()} agent (model: {SUPPORTED_MODELS[selected_alias]}).")
    else:
        await query.edit_message_text(text="Invalid model selection.")


async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Start a new conversation or reset the bot."),
        BotCommand("status", "Show current bot's status."),
        BotCommand("help", "Show this help message."),
    ])


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))

    # Handle button presses
    application.add_handler(CallbackQueryHandler(button_callback))

    # on non command messages - echo the message on Telegram
    application.add_handler(MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.ATTACHMENT, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
