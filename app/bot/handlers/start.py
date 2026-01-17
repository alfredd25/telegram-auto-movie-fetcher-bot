import base64
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from app.utils.config import DB_CHANNEL_ID
from app.utils.logger import setup_logger
from app.db.queries import get_ad_text

logger = setup_logger()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("DEBUG: Start command triggered")
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
            encoded_data = payload.split("-", 1)[1]
            
            # Fix padding if necessary
            missing_padding = len(encoded_data) % 4
            if missing_padding:
                encoded_data += '=' * (4 - missing_padding)

            decoded_data = base64.urlsafe_b64decode(encoded_data).decode("utf-8")
            
            # Attempt to parse
            # Support both `_` (new) and `-` (old) separators
            if "_" in decoded_data:
                parts = decoded_data.split("_")
                # Expected: [channel_id, message_id]
                target_channel_id = int(parts[0])
                target_message_id = int(parts[-1]) # Use last part as message_id to be safe
            elif "-" in decoded_data:
                # Old format: -100xxx-123 or 123-456
                # If negative channel ID: -100...-123 -> ['', '100...', '123'] (split by -)
                # We can't simply split by - if the ID is negative.
                # Regex or rsplit is better.
                # Message ID is always the last part and positive.
                parts = decoded_data.rsplit("-", 1)
                # parts[0] is channel (string), parts[1] is message
                target_channel_id = int(parts[0])
                target_message_id = int(parts[1])
            else:
                 raise ValueError(f"Unknown format: {decoded_data}")

            # Security check
            if target_channel_id != int(DB_CHANNEL_ID):
                 logger.warning(f"Channel ID mismatch. Target: {target_channel_id}, Config: {DB_CHANNEL_ID}")

            ad_text = get_ad_text()
            caption = f"Here is your file, requested by {user.mention_html()}"
            if ad_text:
                caption += f"\n\n{ad_text}"

            try:
                await context.bot.copy_message(
                    chat_id=message.chat_id,
                    from_chat_id=target_channel_id,
                    message_id=target_message_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            except TelegramError as original_error:
                # Retry logic for private channels (often missing -100 prefix)
                if "Chat not found" in str(original_error) and target_channel_id > 0:
                    try:
                        fixed_channel_id = int(f"-100{target_channel_id}")
                        logger.warning(f"Original ID {target_channel_id} failed. Retrying with {fixed_channel_id}")
                        
                        await context.bot.copy_message(
                            chat_id=message.chat_id,
                            from_chat_id=fixed_channel_id,
                            message_id=target_message_id,
                            caption=caption,
                            parse_mode="HTML"
                        )
                    except TelegramError as retry_error:
                        # If retry also fails, raise the original error (or the new one)
                        logger.error(f"Retry failed: {retry_error}")
                        raise original_error
                else:
                    raise original_error
            
        except TelegramError as e:
            if "Chat not found" in str(e):
                logger.error(f"Bot is not in the DB channel ({target_channel_id}). Please add the bot as Admin.")
                await message.reply_text("🚨 Error: I cannot access the file channel. Please ensure I am an Admin there.")
            else:
                logger.error(f"Telegram error processing start payload: {e}")
                await message.reply_text("❌ Unable to retrieve the file.")
                
        except Exception as e:
            logger.error(f"Error processing start payload {payload}: {e}", exc_info=True)
            await message.reply_text("❌ Invalid link or file not found.")


    else:
         await message.reply_text(
            f"👋 Hi {user.mention_html()}! I can help you search for movies.\n"
            "Just send me a name or use /search command.",
            parse_mode="HTML"
        )
