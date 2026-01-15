from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from app.utils.config import DB_URI
from app.utils.logger import setup_logger

logger = setup_logger()

_client = None
_db = None


def get_db():
    global _client, _db

    if _db is not None:
        return _db

    try:
        _client = MongoClient(DB_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
    except ConnectionFailure as e:
        logger.error("❌ Failed to connect to MongoDB Atlas")
        raise RuntimeError(e)

    _db = _client.get_default_database()
    logger.info("✅ Connected to MongoDB Atlas")

    return _db
