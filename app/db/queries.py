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
    # Replace common separators with space, including '+'
    text = re.sub(r"[.\-_()\[\]+]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def search_movies(
    query: str,
    limit: int,
    offset: int,
):
    db = get_db()
    normalized_query = normalize_query(query)
    
    # Escape for regex safely
    escaped_query = re.escape(normalized_query)
    
    # Strict 4-Level Relevance Scoring
    # Priority 4: Exact Match (Score 40)
    # Priority 3: Prefix Match (Score 30) - Starts with query + word boundary
    # Priority 2: Word Match (Score 20) - Contains query as full word
    # Priority 1: Partial Match (Score 10) - Verification fallback
    
    pipeline = [
        # 1. Filter candidates first (Optimization)
        {
            "$match": {
                "normalized_text": {
                    "$regex": escaped_query,
                    "$options": "i",
                }
            }
        },
        # 2. Assign Scores
        {
            "$addFields": {
                "score": {
                    "$switch": {
                        "branches": [
                            # P4: EXACT MATCH
                            {
                                "case": {"$eq": ["$normalized_text", normalized_query]},
                                "then": 40
                            },
                            # P3: PREFIX MATCH (Start + Word Boundary check)
                            # Regex: ^query\b
                            {
                                "case": {
                                    "$regexMatch": {
                                        "input": "$normalized_text",
                                        "regex": f"^{escaped_query}\\b",
                                        "options": "i"
                                    }
                                },
                                "then": 30
                            },
                            # P2: WORD BOUNDARY MATCH
                            # Regex: \bquery\b
                            {
                                "case": {
                                    "$regexMatch": {
                                        "input": "$normalized_text",
                                        "regex": f"\\b{escaped_query}\\b",
                                        "options": "i"
                                    }
                                },
                                "then": 20
                            }
                        ],
                        # P1: PARTIAL MATCH (Default)
                        "default": 10
                    }
                },
                # Calculate length for tie-breaking: shorter matches are "closer" to the query
                "text_len": {"$strLenCP": "$normalized_text"}
            }
        },
        # 3. Sort deterministically
        {
            "$sort": {
                "score": -1,        # Higher score first
                "text_len": 1,      # Shorter text first (closer to exact match)
                "file_name": 1      # Alphabetical tie-breaker
            }
        },
        {"$skip": offset},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "message_id": 1,
                "channel_id": 1,
                "file_name": 1,
                "file_size": 1,
            }
        },
    ]

    cursor = db[MOVIES_COLLECTION].aggregate(pipeline)

    return list(cursor)


def count_movies(query: str) -> int:
    db = get_db()
    normalized = normalize_query(query)

    terms = [re.escape(term) for term in normalized.split()]
    pattern = r".*".join(terms)

    return db[MOVIES_COLLECTION].count_documents(
        {
            "normalized_text": {
                "$regex": pattern,
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
