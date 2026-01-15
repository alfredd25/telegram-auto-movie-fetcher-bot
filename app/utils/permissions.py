from telegram import Update
from telegram.ext import ContextTypes
from app.utils.config import ADMIN_USER_IDS


async def is_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    user = update.effective_user

    if user and user.id in ADMIN_USER_IDS:
        return True

    chat = update.effective_chat

    if chat.type == "private":
        return False

    try:
        member = await context.bot.get_chat_member(
            chat_id=chat.id,
            user_id=user.id,
        )
        return member.status in ("administrator", "creator")
    except Exception:
        return False
