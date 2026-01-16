from datetime import datetime
from pymongo.errors import DuplicateKeyError

from app.db.connection import get_db
from app.db.models import MOVIES_COLLECTION, CONFIG_COLLECTION
from app.utils.logger import setup_logger

import re
from pymongo import ASCENDING

logger = setup_logger()


# ---------- MOVIES ----------

FORWARDED_COLLECTION = "forwarded_files"

def get_movie_metadata(channel_id: int, message_id: int) -> dict | None:
    db = get_db()
    return db[MOVIES_COLLECTION].find_one(
        {"channel_id": channel_id, "message_id": message_id},
        {"_id": 0, "file_size": 1, "file_name": 1}
    )

def is_file_forwarded(channel_id: int, message_id: int) -> bool:
    db = get_db()
    return db[FORWARDED_COLLECTION].find_one(
        {"original_channel_id": channel_id, "original_message_id": message_id}
    ) is not None

def mark_file_as_forwarded(channel_id: int, message_id: int, dest_message_id: int = None):
    db = get_db()
    db[FORWARDED_COLLECTION].insert_one({
        "original_channel_id": channel_id,
        "original_message_id": message_id,
        "dest_message_id": dest_message_id,
        "forwarded_at": datetime.utcnow()
    })

def normalize_query(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[.\-_()\[\]]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def search_movies(
    query: str,
    limit: int,
    offset: int,
):
    db = get_db()
    normalized = normalize_query(query)

    cursor = (
        db[MOVIES_COLLECTION]
        .find(
            {
                "normalized_text": {
                    "$regex": normalized,
                    "$options": "i",
                }
            },
            {
                "_id": 0,
                "message_id": 1,
                "channel_id": 1,
                "file_name": 1,
                "file_size": 1,
            },
        )
        .sort("message_id", ASCENDING)
        .skip(offset)
        .limit(limit)
    )

    return list(cursor)


def count_movies(query: str) -> int:
    db = get_db()
    normalized = normalize_query(query)

    return db[MOVIES_COLLECTION].count_documents(
        {
            "normalized_text": {
                "$regex": normalized,
                "$options": "i",
            }
        }
    )

def insert_movie(metadata: dict) -> bool:
    """
    Insert a movie document.
    Returns True if inserted, False if duplicate.
    """
    db = get_db()
    try:
        metadata["created_at"] = datetime.utcnow()
        db[MOVIES_COLLECTION].insert_one(metadata)
        return True
    except DuplicateKeyError:
        return False



# ---------- CONFIG ----------

CONFIG_COLLECTION = "config"


def get_ad_text() -> str:
    db = get_db()
    doc = db[CONFIG_COLLECTION].find_one(
        {"_id": "ad_text"}
    )
    return doc["value"] if doc else ""


def set_ad_text(value: str):
    db = get_db()
    db[CONFIG_COLLECTION].update_one(
        {"_id": "ad_text"},
        {"$set": {"value": value}},
        upsert=True,
    )

# ---------- INDEX PROGRESS ----------

def get_last_indexed_message(channel_id: int) -> int | None:
    db = get_db()
    doc = db[CONFIG_COLLECTION].find_one(
        {"_id": "index_progress", "channel_id": channel_id}
    )
    return doc["last_message_id"] if doc else None


def update_last_indexed_message(channel_id: int, message_id: int):
    db = get_db()
    db[CONFIG_COLLECTION].update_one(
        {"_id": "index_progress", "channel_id": channel_id},
        {
            "$set": {
                "last_message_id": message_id,
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )
