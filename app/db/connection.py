from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.utils.config import DB_URI
from app.utils.logger import setup_logger
from urllib.parse import urlparse

logger = setup_logger()

_client = None
_db = None


def get_db():
    global _client, _db

    if _db is not None:
        return _db

    try:
        _client = MongoClient(
            DB_URI,
            serverSelectionTimeoutMS=5000,
        )

        # Parse DB name safely from URI
        parsed = urlparse(DB_URI)
        db_name = parsed.path.lstrip("/")

        if not db_name:
            raise RuntimeError("Database name missing in DB_URI")

        # ✅ PING THE ACTUAL DATABASE (NOT admin)
        _client[db_name].command("ping")

        _db = _client[db_name]

    except ConnectionFailure as e:
        logger.error("❌ Failed to connect to MongoDB")
        raise RuntimeError(e)

    logger.info(f"✅ Connected to MongoDB (DB: {db_name})")
    return _db
