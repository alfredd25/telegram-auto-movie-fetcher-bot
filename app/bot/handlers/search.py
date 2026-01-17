import base64
from urllib.parse import quote_plus
from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.db.queries import search_movies, count_movies
from app.utils.logger import setup_logger
from app.utils.auto_delete import schedule_auto_delete
from app.db.queries import get_ad_text
from app.utils.permissions import is_admin

from app.utils.formatters import format_size
from app.utils.config import GROUP_SUPPORT_URL
from telegram.constants import ChatType

logger = setup_logger()

RESULTS_PER_PAGE = 5
AUTO_DELETE_NOTICE = "⚠️ <i>Search results will be deleted in 2 minutes.</i>"


def build_pagination_keyboard(
    query: str,
    page: int,
    total: int,
    page_size: int,
):
    buttons = []

    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                "⬅ Prev",
                callback_data=f"search|{query}|{page - 1}",
            )
        )

    if (page + 1) * page_size < total:
        buttons.append(
            InlineKeyboardButton(
                "Next ➡",
                callback_data=f"search|{query}|{page + 1}",
            )
        )

    if not buttons:
        return None

    return InlineKeyboardMarkup([buttons])

async def search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user
    
    # Get bot username for deep linking
    bot = await context.bot.get_me()
    bot_username = bot.username

    page = 0


    if not context.args:
        await message.reply_text(
            "❗ Usage:\n/search <movie name>"
        )
        return

    # Check for private chat
    if message.chat.type == ChatType.PRIVATE:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Join Group to Search", url=GROUP_SUPPORT_URL)]
        ])
        await message.reply_text(
            "❌ <b>Search is not available in private chat.</b>\n\n"
            "Please join our group to search for movies and series.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    query = " ".join(context.args).strip()

    total = count_movies(query)
    if total == 0:
        encoded_query = quote_plus(query)
        google_url = f"https://www.google.com/search?q={encoded_query}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Check on Google 🔎", url=google_url)]
        ])

        sent_msg = await message.reply_text(
            f"Hey {user.first_name} 👋 Please don’t send messages like this.\n"
            "Search using ONLY the movie or series name.\n"
            "You may add the year or language if needed.\n"
            "(Make sure the spelling matches Google results) ❗🔍\n\n"
            "Wrong examples:\n"
            "KGF movie ❌\n"
            "KGF link ❌\n"
            "KGF undo ❌\n"
            "KGF123 ❌ etc.\n\n"
            "Correct examples:\n"
            "KGF ✔️\n"
            "KGF Tamil ✔️\n"
            "KGF 2022 ✔️\n"
            "Money Heist ✔️\n"
            "Money Heist S1 ✔️\n"
            "Money Heist S1E1 ✔️\n\n"
            "🚫 Avoid special characters like:\n"
            "@ # $ % & * ( ) ! / - ' \" , .\n\n"
            "📺 Make sure the movie or series is released on OTT.\n\n"
            "🔎 Re-check the spelling on google and try again 👇.",
            reply_markup=keyboard,
        )
        
        schedule_auto_delete(
            context=context,
            chat_id=sent_msg.chat_id,
            bot_message_id=sent_msg.message_id,
            user_message_id=message.message_id,
        )
        return

    results = search_movies(
        query=query,
        limit=RESULTS_PER_PAGE,
        offset=0,
    )

    lines = []
    for idx, movie in enumerate(results, start=1):
        # Create deep link payload: channel_id_message_id
        # We encode it to keep it clean and URL safe
        payload_data = f"{movie['channel_id']}_{movie['message_id']}"
        encoded_payload = base64.urlsafe_b64encode(payload_data.encode()).decode()
        
        link = f"https://t.me/{bot_username}?start=getfile-{encoded_payload}"
        size = format_size(movie.get('file_size'))
        
        lines.append(
            f"{idx}. <a href='{link}'>{movie['file_name']}</a> ({size})"
        )

    reply_text = (
        f"👋 Hi @{user.username or user.first_name},\n\n"
        f"🎬 <b>Results for:</b> <i>{query}</i>\n\n"
        + "\n".join(lines)
        + f"\n\n📊 Showing {len(results)} of {total}"
    )

    keyboard = build_pagination_keyboard(
        query=query,
        page=page,
        total=total,
        page_size=RESULTS_PER_PAGE,
    )

    logger.info(
        f"🔍 Search by {user.id}: '{query}' "
        f"({len(results)}/{total})"
    )
    reply_text += f"\n\n{AUTO_DELETE_NOTICE}"
    ad_text = get_ad_text()
    if ad_text:
        reply_text += f"\n\n{ad_text}"

    sent = await message.reply_text(
        reply_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )

    schedule_auto_delete(
        context=context,
        chat_id=sent.chat_id,
        bot_message_id=sent.message_id,
        user_message_id=message.message_id,
    )



async def plain_text_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):


    message = update.effective_message
    text = message.text.strip()

    if text.startswith("/"):
        return



    if len(text.split()) < 1:
        return

    context.args = text.split()
    await search_command(update, context)

