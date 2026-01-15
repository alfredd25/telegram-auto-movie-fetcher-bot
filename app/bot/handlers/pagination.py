from telegram import Update
from telegram.ext import ContextTypes
from app.db.queries import get_ad_text

from app.utils.auto_delete import schedule_auto_delete
from app.db.queries import search_movies, count_movies
from app.bot.handlers.search import (
    build_pagination_keyboard,
    RESULTS_PER_PAGE,
)
from app.utils.logger import setup_logger

logger = setup_logger()

AUTO_DELETE_NOTICE = "⚠️ <i>Files will be deleted in 2 minutes. If you wish to download this file, kindly forward this message to any active or saved chat and start the download from there.</i>"


async def pagination_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    try:
        action, search_query, page_str = query.data.split("|")
        page = int(page_str)
    except ValueError:
        logger.warning("⚠️ Invalid pagination callback data")
        return

    if action != "search":
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

    lines = []
    for idx, movie in enumerate(
        results, start=offset + 1
    ):
        link = (
            f"https://t.me/c/"
            f"{str(movie['channel_id'])[4:]}/"
            f"{movie['message_id']}"
        )
        lines.append(
            f"{idx}. <a href='{link}'>{movie['file_name']}</a>"
        )

    text = (
        f"🎬 <b>Results for:</b> <i>{search_query}</i>\n\n"
        + "\n".join(lines)
        + f"\n\n📊 Showing {len(results)} of {total}"
    )

    keyboard = build_pagination_keyboard(
        query=search_query,
        page=page,
        total=total,
        page_size=RESULTS_PER_PAGE,
    )

    reply_text += f"\n\n{AUTO_DELETE_NOTICE}"
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
