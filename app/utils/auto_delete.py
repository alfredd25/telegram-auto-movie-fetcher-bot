from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from app.utils.logger import setup_logger
from app.db.queries import schedule_db_deletion, get_due_deletions, remove_deletion_task

logger = setup_logger()

AUTO_DELETE_SECONDS = 120


async def process_deletions_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to poll MongoDB and delete due messages."""
    try:
        due_tasks = get_due_deletions()
        if not due_tasks:
            return

        for task in due_tasks:
            task_id = task["_id"]
            chat_id = task["chat_id"]
            bot_msg_id = task.get("bot_message_id")
            user_msg_id = task.get("user_message_id")

            # Try deleting bot message
            if bot_msg_id:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=bot_msg_id)
                except TelegramError as e:
                    logger.warning(f"Failed to delete bot message {bot_msg_id} in {chat_id}: {e}")

            # Try deleting user message
            if user_msg_id:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=user_msg_id)
                except TelegramError as e:
                    logger.warning(f"Failed to delete user message {user_msg_id} in {chat_id}: {e}")

            # Remove from DB regardless of success/failure (to prevent infinite retry loops)
            remove_deletion_task(task_id)
            logger.info(f"🗑️ Processed auto-delete task {task_id}")

    except Exception as e:
        logger.error(f"Error in process_deletions_job: {e}")


def schedule_auto_delete(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    bot_message_id: int,
    user_message_id: int | None = None,
):
    """Schedules a deletion by saving it to the database."""
    delete_at = datetime.utcnow() + timedelta(seconds=AUTO_DELETE_SECONDS)
    schedule_db_deletion(
        chat_id=chat_id,
        bot_message_id=bot_message_id,
        user_message_id=user_message_id,
        delete_at=delete_at
    )
    logger.info(f"Scheduled persistent deletion for msg {bot_message_id} in {chat_id}")
