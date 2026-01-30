from app.utils.config import (
    TG_API_ID,
    TG_API_HASH,
    DB_URI,
    DB_CHANNEL_ID,
    CLIENT_CHANNEL_ID
)

# Source and Target Channels
# DB_CHANNEL_ID is the source private channel (where files are indexed from)
# CLIENT_CHANNEL_ID is the destination private channel (Main Channel)
SOURCE_CHANNEL_ID = DB_CHANNEL_ID
TARGET_CHANNEL_ID = CLIENT_CHANNEL_ID

# Configuration Constraints
MAX_FILE_SIZE = 1.2 * 1024 * 1024 * 1024  # 1.2 GB in bytes
THROTTLE_DELAY = 1.5  # Seconds to wait between forwards
