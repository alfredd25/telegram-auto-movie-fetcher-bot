from pymongo import ASCENDING
from app.db.connection import get_db
from app.utils.logger import setup_logger

logger = setup_logger()

MOVIES_COLLECTION = "movies"
CONFIG_COLLECTION = "config"


def ensure_indexes():
    db = get_db()

    movies = db[MOVIES_COLLECTION]

    movies.create_index(
        [("file_unique_id", ASCENDING)],
        unique=True,
        name="unique_file"
    )

    movies.create_index(
        [("normalized_text", ASCENDING)],
        name="search_text"
    )

    logger.info("📚 MongoDB indexes ensured")
