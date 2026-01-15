import re
from telegram import Update
from telegram.ext import ContextTypes

from app.db.queries import insert_movie
from app.utils.config import DB_CHANNEL_ID
from app.utils.logger import setup_logger

logger = setup_logger()


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[.\-_()\[\]]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def channel_post_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.channel_post
    if not message:
        return

    if message.chat.id != DB_CHANNEL_ID:
        return

    file = None

    if message.document:
        file = message.document
    elif message.video:
        file = message.video
    elif message.audio:
        file = message.audio

    if not file or not file.file_name:
        return

    caption = message.caption or ""
    searchable = f"{file.file_name} {caption}"

    metadata = {
        "message_id": message.message_id,
        "channel_id": message.chat.id,
        "file_id": file.file_id,
        "file_unique_id": file.file_unique_id,
        "file_name": file.file_name,
        "file_size": file.file_size,
        "caption": caption,
        "mime_type": file.mime_type,
        "normalized_text": normalize_text(searchable),
    }

    inserted = insert_movie(metadata)

    if inserted:
        logger.info(f"🆕 Auto-indexed: {file.file_name}")
