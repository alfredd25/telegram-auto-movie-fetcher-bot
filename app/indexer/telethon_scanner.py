import re
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import Message

from app.db.queries import (
    insert_movie,
    get_last_indexed_message,
    update_last_indexed_message,
)
from app.utils.config import DB_CHANNEL_ID
from app.utils.logger import setup_logger
from app.utils.config import (
    TG_API_ID,
    TG_API_HASH,
)

logger = setup_logger()


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[.\-_()\[\]+]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def run_telethon_indexer():
    last_indexed = get_last_indexed_message(DB_CHANNEL_ID) or 0
    logger.info(
        f"📡 Telethon indexing started "
        f"(resume from message_id={last_indexed})"
    )

    processed_since_checkpoint = 0
    CHECKPOINT_INTERVAL = 50
    THROTTLE_DELAY = 0.15

    async with TelegramClient(
        "indexer_session",
        TG_API_ID,
        TG_API_HASH,
    ) as client:

        try:
            await client.get_entity(DB_CHANNEL_ID)
        except ValueError:
            logger.info("🔄 Channel entity not found in cache. Refreshing dialogs...")
            dialogs = await client.get_dialogs()

            try:
                await client.get_entity(DB_CHANNEL_ID)
            except ValueError:
                logger.error(f"❌ Channel {DB_CHANNEL_ID} NOT found in account dialogs!")
                logger.info("👇 Available Channels (copy the ID of the one you want):")
                for d in dialogs:
                    if d.is_channel:
                        logger.info(f"   ID: {d.id}  |  Name: {d.title}")
                
                logger.warning("⚠️ Please update TEST_DB_CHANNEL_ID or PROD_DB_CHANNEL_ID in .env")
                return

        try:
            async for message in client.iter_messages(
                DB_CHANNEL_ID,
                min_id=last_indexed,
                reverse=True,
            ):
                if not message.file or not message.file.name:
                    continue

                metadata = {
                    "message_id": message.id,
                    "channel_id": DB_CHANNEL_ID,
                    "file_id": message.file.id,
                    "file_unique_id": str(message.file.id),
                    "file_name": message.file.name,
                    "file_size": message.file.size,
                    "caption": message.text or "",
                    "mime_type": message.file.mime_type,
                    "normalized_text": normalize_text(
                        f"{message.file.name} {message.text or ''}"
                    ),
                }

                inserted = insert_movie(metadata)
                processed_since_checkpoint += 1

                if inserted:
                    logger.info(f"📦 Indexed: {message.file.name}")

                if processed_since_checkpoint >= CHECKPOINT_INTERVAL:
                    update_last_indexed_message(DB_CHANNEL_ID, message.id)
                    processed_since_checkpoint = 0

                await asyncio.sleep(THROTTLE_DELAY)

        except FloodWaitError as e:
            logger.warning(
                f"⏳ FloodWait hit. Sleeping for {e.seconds + 5} seconds"
            )
            await asyncio.sleep(e.seconds + 5)
            return await run_telethon_indexer()

        except Exception as e:
            logger.exception("❌ Indexing failed unexpectedly")
            raise e



    logger.info("✅ Telethon indexing complete")
