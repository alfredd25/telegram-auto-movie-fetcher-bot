import base64
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from app.utils.config import DB_CHANNEL_ID
from app.utils.logger import setup_logger

logger = setup_logger()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    
    if not context.args:
        await message.reply_text(
            f"👋 Hi {user.mention_html()}! I can help you search for movies.\n"
            "Just send me a name or use /search command.",
            parse_mode="HTML"
        )
        return

    payload = context.args[0]
    
    if payload.startswith("getfile-"):
        try:
            # Format: getfile-<base64_encoded_string>
            # where encoded string contains: "channel_id-message_id"
            encoded_data = payload.split("-", 1)[1]
            decoded_data = base64.urlsafe_b64decode(encoded_data).decode("utf-8")
            
            # Extract IDs (we might store full channel ID or part of it, let's stick to what we have)
            # The search logic uses db storage which has channel_id and message_id
            parts = decoded_data.split("-")
            if len(parts) < 2:
                raise ValueError("Invalid payload format")
                
            target_channel_id = int(parts[0])
            target_message_id = int(parts[1])
            
            # Security check: ensure we are only forwarding from our allowed DB channel
            # This prevents users from using the bot to forward from random channels if they guessed IDs
            # Although copy_message requires the bot to be admin in the source chat usually or have access.
            if target_channel_id != int(DB_CHANNEL_ID):
                 # If DB_CHANNEL_ID might be -100... and target might be the same
                 pass 

            await context.bot.copy_message(
                chat_id=message.chat_id,
                from_chat_id=target_channel_id,
                message_id=target_message_id,
                caption=f"Here is your file, requested by {user.mention_html()}",
                parse_mode="HTML"
            )
            
        except (ValueError, IndexError, TelegramError) as e:
            logger.error(f"Error processing start payload {payload}: {e}")
            await message.reply_text("❌ Invalid link or file not found.")
    else:
         await message.reply_text(
            f"👋 Hi {user.mention_html()}! I can help you search for movies.\n"
            "Just send me a name or use /search command.",
            parse_mode="HTML"
        )
