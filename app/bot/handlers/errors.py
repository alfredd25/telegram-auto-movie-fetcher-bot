from telegram.ext import ContextTypes
from app.utils.logger import setup_logger

logger = setup_logger()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception occurred", exc_info=context.error)
