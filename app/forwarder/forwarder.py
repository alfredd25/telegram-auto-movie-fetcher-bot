
import asyncio
import logging
import time
import sys
from telethon import TelegramClient, errors
from app.forwarder.config import (
    TG_API_ID,
    TG_API_HASH,
    SOURCE_CHANNEL_ID,
    TARGET_CHANNEL_ID,
    THROTTLE_DELAY,
    MAX_FILE_SIZE
)
from app.forwarder.state import ForwarderState

# Configure Logging
# Using utf-8 for file handler to support emojis/special chars
file_handler = logging.FileHandler("forwarder.log", encoding="utf-8")
stream_handler = logging.StreamHandler(sys.stdout)

# On Windows, the console might not support utf-8 characters like emojis
# defaulting to 'replace' or 'ignore' is hard with standard StreamHandler without custom class
# So we will rely on Python 3.7+ usually handling this better, but to be safe we can use a simpler format for console if needed.
# For now, let's just properly configure the handlers.

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        file_handler,
        stream_handler
    ]
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Telegram File Forwarder...")
    
    # Initialize State (Database)
    try:
        state = ForwarderState()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return

    # Initialize Telethon Client
    # We use the existing 'telethon_session' from the root directory
    client = TelegramClient('telethon_session', TG_API_ID, TG_API_HASH)
    
    try:
        await client.start()
        logger.info("Telethon client connected")
    except Exception as e:
        logger.error(f"Failed to connect Telethon client: {e}")
        return

    # Get user to verify correct account
    me = await client.get_me()
    logger.info(f"Logged in as: {me.first_name} (ID: {me.id})")
    
    logger.info(f"Source Channel: {SOURCE_CHANNEL_ID}")
    logger.info(f"Target Channel: {TARGET_CHANNEL_ID}")
    logger.info(f"Max File Size: {MAX_FILE_SIZE / (1024*1024*1024):.2f} GB")
    
    # Get pending movies
    # We get all movies that fit criteria
    # The state class handles sorting by message_id ASC
    logger.info("Fetching list of pending movies...")
    cursor = state.get_pending_movies(MAX_FILE_SIZE)
    total_found = state.collection.count_documents({}) 
    # Note: total_found above is forwarded count, not source count.
    # Source count is hard to get efficiently if we have filters, but we can iterate.
    
    logger.info("🔄 specific count not pre-calculated to save time. Starting stream...")

    success_count = 0
    skipped_count = 0
    fail_count = 0

    try:
        for movie in cursor:
            msg_id = movie.get("message_id")
            # Use the channel_id from the DB record if available, otherwise fallback to env config
            # This handles cases where files are indexed from multiple channels
            src_peer = movie.get("channel_id") or SOURCE_CHANNEL_ID
            
            if not msg_id:
                logger.warning(f"Skipping document with missing message_id: {movie.get('_id')}")
                continue

            # Check if already forwarded
            if state.is_forwarded(msg_id):
                skipped_count += 1
                if skipped_count % 1000 == 0:
                    logger.info(f"Skipped {skipped_count} already forwarded messages...")
                continue

            # Fetch the message first to verify it contains a file
            try:
                # ids parameter gets a single message if passed as int/list of ints
                messages = await client.get_messages(src_peer, ids=[msg_id])
                message = messages[0] if messages else None

                if not message:
                    logger.warning(f"Message {msg_id} not found or deleted using get_messages.")
                    state.mark_forwarded(msg_id, SOURCE_CHANNEL_ID, TARGET_CHANNEL_ID, "skipped")
                    skipped_count += 1
                    continue
                
                # Check for file
                if not message.file:
                    logger.info(f"Message {msg_id} is text/service (no file). Marking as skipped.")
                    state.mark_forwarded(msg_id, SOURCE_CHANNEL_ID, TARGET_CHANNEL_ID, "skipped")
                    skipped_count += 1
                    continue

                # Forward the message (using the message object is safer/faster if we already have it)
                logger.info(f"Forwarding message {msg_id}...")
                
                await client.forward_messages(
                    entity=TARGET_CHANNEL_ID,
                    messages=message, # Pass the message object directly
                    from_peer=src_peer # explicit from_peer is good practice
                )
                
                # Mark as success
                state.mark_forwarded(msg_id, src_peer, TARGET_CHANNEL_ID, "success")
                success_count += 1
                logger.info(f"Forwarded {msg_id} successfully")
                
                # Throttle
                time.sleep(THROTTLE_DELAY)

            except errors.FloodWaitError as e:
                logger.warning(f"FloodWaitError triggered. Waiting for {e.seconds} seconds...")
                # Add a safety buffer of 2 seconds
                wait_time = e.seconds + 2
                time.sleep(wait_time)
                
                # Retry
                # ... retry logic ...
                logger.info("Retrying after FloodWait...")
                try:
                    await client.forward_messages(
                        entity=TARGET_CHANNEL_ID,
                        messages=msg_id,
                        from_peer=src_peer
                    )
                    state.mark_forwarded(msg_id, src_peer, TARGET_CHANNEL_ID, "success")
                    success_count += 1
                    logger.info(f"Forwarded {msg_id} successfully after retry")
                    time.sleep(THROTTLE_DELAY)
                except Exception as retry_e:
                    logger.error(f"Failed to retry message {msg_id}: {retry_e}")
                    state.mark_forwarded(msg_id, src_peer, TARGET_CHANNEL_ID, "failed")
                    fail_count += 1

            except Exception as e:
                logger.error(f"Error forwarding message {msg_id}: {e}")
                # Mark as failed so we can track it, or just don't mark it so we retry later?
                # Marking as 'failed' allows us to manually inspect later.
                state.mark_forwarded(msg_id, SOURCE_CHANNEL_ID, TARGET_CHANNEL_ID, "failed")
                fail_count += 1
                time.sleep(THROTTLE_DELAY)

    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
    finally:
        logger.info("Forwarding session finished.")
        logger.info(f"Stats: Success={success_count}, Skipped={skipped_count}, Failed={fail_count}")
        state.close()
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
