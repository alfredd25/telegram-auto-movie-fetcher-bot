from telegram.ext import ContextTypes
from app.utils.logger import setup_logger

logger = setup_logger()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error Type: {type(context.error)}")
    logger.error(f"Error Message: {context.error}")
    logger.exception("Unhandled exception occurred", exc_info=context.error)
