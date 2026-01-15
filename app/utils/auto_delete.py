from telegram.ext import ContextTypes
from app.utils.logger import setup_logger

logger = setup_logger()

AUTO_DELETE_SECONDS = 120


async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    chat_id = data["chat_id"]

    bot_message_id = data.get("bot_message_id")
    user_message_id = data.get("user_message_id")

    try:
        if bot_message_id:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=bot_message_id,
            )

        if user_message_id:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=user_message_id,
            )

        logger.info(
            f"🗑️ Auto-deleted bot_message={bot_message_id}, "
            f"user_message={user_message_id}"
        )

    except Exception:
        logger.warning(
            "⚠️ Failed to auto-delete one or more messages"
        )


def schedule_auto_delete(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    bot_message_id: int,
    user_message_id: int | None = None,
):
    context.job_queue.run_once(
        delete_message_job,
        when=AUTO_DELETE_SECONDS,
        data={
            "chat_id": chat_id,
            "bot_message_id": bot_message_id,
            "user_message_id": user_message_id,
        },
    )
