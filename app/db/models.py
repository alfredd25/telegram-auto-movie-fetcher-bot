from pymongo import ASCENDING
from app.db.connection import get_db
from app.utils.logger import setup_logger

logger = setup_logger()

MOVIES_COLLECTION = "movies"
CONFIG_COLLECTION = "config"
DELETIONS_COLLECTION = "deletions"


def ensure_indexes():
    db = get_db()

    movies = db[MOVIES_COLLECTION]
    deletions = db[DELETIONS_COLLECTION]

    movies.create_index(
        [("file_unique_id", ASCENDING), ("channel_id", ASCENDING)],
        unique=True,
        name="unique_file_channel"
    )

    movies.create_index(
        [("normalized_text", ASCENDING)],
        name="search_text"
    )

    deletions.create_index(
        [("delete_at", ASCENDING)],
        name="idx_delete_at"
    )

    logger.info("📚 MongoDB indexes ensured")
