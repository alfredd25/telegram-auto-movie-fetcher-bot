import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatType
from app.db.queries import get_ad_text

from app.utils.auto_delete import schedule_auto_delete
from app.db.queries import search_movies, count_movies
from app.bot.handlers.search import (
    build_pagination_keyboard,
    RESULTS_PER_PAGE,
)
from app.utils.logger import setup_logger
from app.utils.formatters import format_size

logger = setup_logger()

AUTO_DELETE_NOTICE = "⚠️ <i>Search results will be deleted in 2 minutes.</i>"


async def pagination_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    # Get bot username for deep linking
    bot = await context.bot.get_me()
    bot_username = bot.username

    try:
        action, search_query, page_str = query.data.split("|")
        page = int(page_str)
    except ValueError:
        logger.warning("⚠️ Invalid pagination callback data")
        return

    if action != "search":
        return

    if query.message.chat.type == ChatType.PRIVATE:
        await query.answer(
            text="⚠️ Search is only available in the group.",
            show_alert=True
        )
        return

    total = count_movies(search_query)
    offset = page * RESULTS_PER_PAGE

    results = search_movies(
        query=search_query,
        limit=RESULTS_PER_PAGE,
        offset=offset,
    )

    if not results:
        await query.edit_message_text(
            "❌ No more results.",
        )
        return

    # Build inline buttons — one per result
    file_buttons = []
    for idx, movie in enumerate(
        results, start=offset + 1
    ):
        payload_data = f"{movie['channel_id']}_{movie['message_id']}"
        encoded_payload = base64.urlsafe_b64encode(payload_data.encode()).decode()
        link = f"https://t.me/{bot_username}?start=getfile-{encoded_payload}"
        size = format_size(movie.get('file_size'))

        file_buttons.append([
            InlineKeyboardButton(
                f"{idx}. {movie['file_name']} ({size})",
                url=link,
            )
        ])

    # Append pagination row if needed
    pagination_kb = build_pagination_keyboard(
        query=search_query,
        page=page,
        total=total,
        page_size=RESULTS_PER_PAGE,
    )
    if pagination_kb:
        file_buttons.extend(pagination_kb.inline_keyboard)

    keyboard = InlineKeyboardMarkup(file_buttons)

    text = (
        f"🎬 <b>Results for:</b> <i>{search_query}</i>\n\n"
        f"📊 Showing {len(results)} of {total}"
    )

    text += f"\n\n{AUTO_DELETE_NOTICE}"
    ad_text = get_ad_text()
    if ad_text:
        text += f"\n\n{ad_text}"


    sent = await query.edit_message_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )

    schedule_auto_delete(
        context=context,
        chat_id=sent.chat_id,
        bot_message_id=sent.message_id,
    )



    logger.info(
        f"📄 Pagination: '{search_query}' page {page}"
    )
