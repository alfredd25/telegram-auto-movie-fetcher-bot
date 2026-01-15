from telegram import Update
from telegram.ext import ContextTypes
from app.db.queries import set_ad_text
from app.utils.logger import setup_logger
from app.utils.permissions import is_admin

logger = setup_logger()


async def set_ad_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not await is_admin(update, context):
        await message.reply_text("❌ Admin only command")
        return

    if not context.args:
        await message.reply_text(
            "Usage:\n/set_ad <ad text>"
        )
        return

    ad_text = " ".join(context.args)
    set_ad_text(ad_text)

    await message.reply_text("✅ Ad text updated")

    logger.info(
        f"📢 Ad updated by admin {user.id}"
    )
