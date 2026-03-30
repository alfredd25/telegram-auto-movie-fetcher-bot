from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from app.utils.config import BOT_TOKEN, DB_CHANNEL_ID
from app.utils.logger import setup_logger
from app.db.models import ensure_indexes
from app.bot.handlers.search import search_command, plain_text_search
from app.bot.handlers.start import start_command
from app.bot.handlers.admin import set_ad_command
from app.bot.handlers.errors import error_handler
from app.bot.handlers.pagination import pagination_callback
from app.bot.handlers.channel_watcher import channel_post_handler
from app.utils.auto_delete import process_deletions_job


logger = setup_logger()


def run_bot():
    logger.info("Starting Telegram Movie Bot...")

    ensure_indexes()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("set_ad", set_ad_command))

    application.add_handler(
        MessageHandler(
            filters.Chat(DB_CHANNEL_ID) & filters.UpdateType.CHANNEL_POST,
            channel_post_handler,
        )
    )

    application.add_handler(
        CallbackQueryHandler(pagination_callback, pattern=r"^search\|")
    )
    application.add_handler(
        CommandHandler("set_ad", set_ad_command)
    )

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_text_search))
    application.add_error_handler(error_handler)
    application.add_handler(CallbackQueryHandler(pagination_callback))

    # Start persistent auto-delete poller
    application.job_queue.run_repeating(process_deletions_job, interval=15, first=5)

    logger.info("Bot started successfully. Waiting for updates...")
    application.run_polling()

