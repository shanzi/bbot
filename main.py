"""Telegram bot with FastAgent AI integration for document management."""

import asyncio
import base64
import datetime
import io
import logging
import os
import re
import time
import zoneinfo

from dotenv import load_dotenv
from mcp.types import ImageContent, TextContent, Role
from mcp_agent.mcp.prompt_message_multipart import PromptMessageMultipart
from PIL import Image
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegramify_markdown import markdownify

from agent_factory import get_fast_agent_app
import utils

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Constants
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file or environment variables.")

SUPPORTED_MODELS = {
    "claude-sonnet-3": "anthropic.claude-3-5-sonnet-20241022",
    "claude-sonnet-3.7": "anthropic.claude-3-7-sonnet-20250219",
    "openai-mini": "openai.gpt-4o-mini",
    "claude-sonnet-4": "anthropic.claude-sonnet-4-20250514",
    "gemini-pro": "google.gemini-2.5-pro",
    "gemini-flash": "google.gemini-2.5-flash",
}

# Global state dictionaries
current_agents = {}  # Dictionary to store the current agent for each chat
agent_instances = {}  # Dictionary to store initialized agent instances

# Get the local timezone dynamically
try:
    LOCAL_TIMEZONE = datetime.datetime.now().astimezone().tzinfo
except Exception:
    LOCAL_TIMEZONE = "UTC"  # Fallback if timezone detection fails

def downscale_image(image_path: str, max_size: tuple = (512, 512), quality: int = 60) -> bytes:
    """Downscale image to minimal size for token efficiency while maintaining readability.
    
    Args:
        image_path: Path to the original image file
        max_size: Maximum dimensions (width, height) for the resized image
        quality: JPEG quality (1-100) when saving the image
        
    Returns:
        bytes: Heavily compressed image data as bytes
    """
    with Image.open(image_path) as img:
        # Convert to RGB if necessary (for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Calculate new size maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes buffer with aggressive compression
        buffer = io.BytesIO()
        img.save(
            buffer, 
            format='JPEG', 
            quality=quality,
            optimize=True,
            progressive=True,
            subsampling=2  # More aggressive chroma subsampling
        )
        return buffer.getvalue()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued, and ask for model selection."""
    user = update.effective_user
    
    aliases = list(SUPPORTED_MODELS.keys())
    keyboard = [
        [InlineKeyboardButton(alias.capitalize(), callback_data=alias) 
         for alias in aliases[i:i + 2]]
        for i in range(0, len(aliases), 2)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot that can talk to different AI models.\n\n"
        "Which model would you like to use?",
        reply_markup=reply_markup,
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "Here are the commands you can use:\n\n"
        "/start - Start a new conversation or reset the bot.\n"
        "/status - Show current bot's status.\n"
        "/help - Show this help message.\n\n"
        "To talk to the agent, just send a message directly."
    )
    await update.message.reply_text(help_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the currently active agent for the chat."""
    chat_id = update.effective_chat.id
    agent_alias = current_agents.get(chat_id, "claude-sonnet-3")
    agent_instance = agent_instances.get(chat_id)

    status_text = f"Your current agent is: **{agent_alias.capitalize()}**\n"
    status_text += f"Initialized: **{agent_instance is not None}**\n\n"

    if agent_instance:
        # Get the actual BaseAgent instance
        actual_agent = next(iter(agent_instance._agents.values()))

        # Get context length and token count
        context_length = len(actual_agent.message_history)
        estimated_tokens = utils.estimate_tokens(actual_agent.message_history)

        status_text += f"Context Length: **{context_length}** messages\n"
        status_text += f"Estimated Tokens: **~{estimated_tokens}**\n"

    status_message = markdownify(status_text)
    await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN_V2)


async def trim_context_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trim the agent's context to a specific number of messages."""
    chat_id = update.effective_chat.id
    agent_instance = agent_instances.get(chat_id)

    if not agent_instance:
        await update.message.reply_text(
            "Agent not initialized. Please start a conversation first."
        )
        return

    try:
        keep_count = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Please provide the number of recent messages to keep.\n"
            "Usage: /trim_context <number>"
        )
        return

    actual_agent = next(iter(agent_instance._agents.values()))
    original_length = len(actual_agent.message_history)

    if keep_count >= original_length:
        await update.message.reply_text(
            f"Context length is already {original_length}. No trimming needed."
        )
        return

    if keep_count < 0:
        await update.message.reply_text(
            "Number of messages to keep cannot be negative."
        )
        return

    actual_agent.message_history = actual_agent.message_history[-keep_count:]
    new_length = len(actual_agent.message_history)

    await update.message.reply_text(
        f"Context trimmed from {original_length} to {new_length} messages."
    )


# Helper functions for handle_message
async def _handle_document_upload(update, context, chat_id, message_id):
    """Handle document upload and return attachment info."""
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text="Downloading attachment..."
    )
    doc = update.message.document
    file = await context.bot.get_file(doc.file_id)
    target_dir = utils.get_save_directory("attachment")
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, f"{int(time.time()*1000)}--{doc.file_name}")
    await file.download_to_drive(target)
    return f"(attachment downloaded to {target})"


async def _handle_photo_upload(update, context, chat_id, message_id):
    """Handle photo upload and return tuple of (ImageContent, caption_text)."""
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text="Downloading image..."
    )
    # Get the largest photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    target_dir = utils.get_save_directory("pictures")
    os.makedirs(target_dir, exist_ok=True)
    file_extension = file.file_path.split('.')[-1] if file.file_path else 'jpg'
    target = os.path.join(target_dir, f"{int(time.time()*1000)}.{file_extension}")
    await file.download_to_drive(target)
    
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text="Processing image..."
    )
    
    # Downscale the image to reduce tokens (512x512 default)
    downscaled_image_data = downscale_image(target)
    image_data = base64.b64encode(downscaled_image_data).decode('utf-8')
    
    image_content = ImageContent(
        type="image",
        mimeType="image/jpeg",  # Always JPEG after downscaling
        data=image_data
    )
    
    # Extract caption if present
    caption_text = update.message.caption or ""
    
    return image_content, caption_text


async def _get_or_create_agent(chat_id, context, message_id):
    """Get existing agent or create new one if needed."""
    agent_alias = current_agents.get(chat_id, "claude-sonnet-3")
    agent_to_use = agent_instances.get(chat_id)

    if not agent_to_use:
        model_name = SUPPORTED_MODELS.get(agent_alias)
        if model_name:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"Loading {agent_alias.capitalize()} agent..."
            )
            fast_app = get_fast_agent_app(model_name)
            # IMPORTANT: Use 'async with' to ensure proper FastAgent lifecycle management.
            # Do not revert to 'await fast_app.run()' as it can lead to resource leaks.
            async with fast_app.run() as agent:
                agent_instances[chat_id] = agent
                agent_to_use = agent_instances[chat_id]
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Invalid agent selected. Please use /start to select an agent."
            )
            return None
    return agent_to_use


async def _process_agent_response(agent_to_use, message_contents, context, chat_id, message_id):
    """Process message with agent and send response."""
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text="Thinking..."
    )
    
    # Get the actual BaseAgent instance from the AgentApp
    # Since we only have one agent per FastAgent instance, we can get the first one
    actual_agent = next(iter(agent_to_use._agents.values()))
    
    # Log the estimated token count
    estimated_tokens = utils.estimate_tokens(actual_agent.message_history)
    logger.info(f"Calling agent with ~{estimated_tokens} tokens.")

    # Log multipart message construction
    logger.info(f"Creating multipart message with {len(message_contents)} content parts")
    for i, content in enumerate(message_contents):
        logger.info(f"Content {i}: {type(content).__name__} - {content.type}")

    # Create PromptMessageMultipart directly
    multipart_message = PromptMessageMultipart(
        role="user",
        content=message_contents
    )
    
    # Generate the response using the multipart message
    response_multipart = await actual_agent.generate([multipart_message], None)

    # Get only the last text content (final assistant response)
    response_text = response_multipart.last_text()

    # Find all image tags in the response
    image_tags = re.findall(r'!\[(.*?)\]\((.*?)\)', response_text)
    logger.info(f"Found {len(image_tags)} image tags in the response.")
    
    # Find file attachment directives in the response
    # Pattern matches ATTACH_FILE: followed by path until end of line or backtick
    attach_file_pattern = r'ATTACH_FILE:([^`\n]+)'
    file_attachments = re.findall(attach_file_pattern, response_text)
    # Strip whitespace from file paths
    file_attachments = [path.strip() for path in file_attachments]
    logger.info(f"Found {len(file_attachments)} file attachments in the response.")
    
    # Remove ATTACH_FILE directives from response text before sending
    clean_response_text = re.sub(r'`?ATTACH_FILE:[^`\n]+`?\n?', '', response_text).strip()
    # Clean up multiple consecutive newlines
    clean_response_text = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_response_text)
    
    media_group = []
    for alt_text, file_path in image_tags:
        if not os.path.isabs(file_path):
            if file_path.startswith('data/'):
                file_path = os.path.join(os.getcwd(), file_path)
            else:
                file_path = utils.get_save_directory(file_path)
        
        if os.path.exists(file_path):
            logger.info(f"Found image at {file_path}")
            media_group.append(
                InputMediaPhoto(media=open(file_path, 'rb'), caption=alt_text)
            )
        else:
            logger.warning(f"Image not found at {file_path}")

    telegram_response = markdownify(clean_response_text)
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=telegram_response,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    
    if media_group:
        await context.bot.send_media_group(chat_id=chat_id, media=media_group)
    
    # Send file attachments
    for file_path in file_attachments:
        if os.path.exists(file_path):
            logger.info(f"Sending file attachment: {file_path}")
            with open(file_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=file,
                    filename=os.path.basename(file_path),
                    caption=f"📄 {os.path.basename(file_path)}"
                )
        else:
            logger.warning(f"File attachment not found: {file_path}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ File not found: {os.path.basename(file_path)}"
            )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages, documents, and photos."""
    chat_id = update.effective_chat.id

    # Send an initial placeholder message immediately
    placeholder_message = await update.message.reply_text(
        "Initializing...", reply_to_message_id=update.message.message_id
    )

    try:
        # Prepare message contents list for multimodal support
        message_contents = []
        
        # Handle text messages (can be combined with attachments)
        if update.message.text:
            user_text = update.message.text
            message_contents.append(TextContent(type="text", text=user_text))
        
        # Handle document attachments
        if update.message.document:
            attachment_info = await _handle_document_upload(
                update, context, chat_id, placeholder_message.message_id
            )
            message_contents.append(TextContent(type="text", text=attachment_info))
        
        # Handle photo attachments
        if update.message.photo:
            image_content, caption_text = await _handle_photo_upload(
                update, context, chat_id, placeholder_message.message_id
            )
            # Add caption as text content if present
            if caption_text:
                message_contents.append(TextContent(type="text", text=caption_text))
            # Add the image content
            message_contents.append(image_content)

        # Ensure we have content to send
        if not message_contents:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=placeholder_message.message_id,
                text="No content to process."
            )
            return

        # Get or initialize agent
        agent_to_use = await _get_or_create_agent(
            chat_id, context, placeholder_message.message_id
        )
        if not agent_to_use:
            return

        # Process message with agent
        await _process_agent_response(
            agent_to_use, message_contents, context, chat_id, placeholder_message.message_id
        )

    except Exception as e:
        agent_alias = current_agents.get(chat_id, "claude-sonnet-3")
        logger.error(f"Error communicating with {agent_alias} agent: {e}")
        error_message = f"Sorry, I encountered an error with the {agent_alias} agent: {e}"
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=placeholder_message.message_id,
            text=error_message
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callback queries for model selection."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    selected_alias = query.data

    if selected_alias in SUPPORTED_MODELS:
        current_agents[chat_id] = selected_alias
        # Reset agent context when switching models
        agent_instances.pop(chat_id, None)
        model_name = SUPPORTED_MODELS[selected_alias]
        await query.edit_message_text(
            text=f"Switched to {selected_alias.capitalize()} agent (model: {model_name})."
        )
    else:
        await query.edit_message_text(text="Invalid model selection.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the user."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Clear the agent for the current chat on error
    if update and hasattr(update, 'effective_chat') and update.effective_chat:
        chat_id = update.effective_chat.id
        if chat_id in agent_instances:
            agent_instances.pop(chat_id)
            logger.info(f"Agent for chat_id {chat_id} has been cleared due to an error.")
            await update.effective_chat.send_message(
                "An error occurred and my session has been reset. Please try again."
            )

async def post_init(app):
    """Initialize bot commands after startup."""
    await app.bot.set_my_commands([
        BotCommand("start", "Start a new conversation or reset the bot."),
        BotCommand("status", "Show current bot's status."),
        BotCommand("help", "Show this help message."),
    ])


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Register the error handler
    application.add_error_handler(error_handler)

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("trim_context", trim_context_command))

    # Handle button presses
    application.add_handler(CallbackQueryHandler(button_callback))

    # Handle non-command messages and attachments
    application.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND) | filters.ATTACHMENT, 
            handle_message
        )
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()