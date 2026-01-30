import pymongo
from urllib.parse import urlparse
from datetime import datetime
from app.forwarder.config import DB_URI

class ForwarderState:
    def __init__(self):
        self.client = pymongo.MongoClient(DB_URI)
        parsed = urlparse(DB_URI)
        db_name = parsed.path.lstrip("/")
        if not db_name:
            raise ValueError("Database name could not be parsed from DB_URI")
            
        self.db = self.client[db_name]
        self.collection = self.db["forwarded_files"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        # Remove any documents where source_message_id is null/None
        # This fixes the DuplicateKeyError if bad data exists
        self.collection.delete_many({"source_message_id": None})
        
        # Create unique index on source_message_id to prevent duplicates
        self.collection.create_index("source_message_id", unique=True)

    def is_forwarded(self, message_id):
        """Check if a message has already been processed (success or skipped)."""
        return self.collection.find_one({
            "source_message_id": message_id,
            "status": {"$in": ["success", "skipped"]}
        }) is not None

    def mark_forwarded(self, source_msg_id, source_channel, target_channel, status="success"):
        """Mark a message as forwarded in the database."""
        doc = {
            "source_channel_id": source_channel,
            "source_message_id": source_msg_id,
            "target_channel_id": target_channel,
            "forwarded_at": datetime.utcnow(),
            "status": status
        }
        try:
            self.collection.insert_one(doc)
        except pymongo.errors.DuplicateKeyError:
            # If it exists, update the status just in case it was failed before
            self.collection.update_one(
                {"source_message_id": source_msg_id},
                {"$set": {
                    "status": status,
                    "forwarded_at": datetime.utcnow()
                }}
            )

    def get_pending_movies(self, max_size):
        """
        Get all movies that qualify for forwarding and have NOT been forwarded yet.
        Returns a cursor of movie documents.
        """
        # 1. Get List of all forwarded message_ids to avoid processing them again
        # This is more efficient than checking one by one if the list is not massive (e.g. < 100k)
        forwarded_cursor = self.collection.find(
            {"status": {"$in": ["success", "skipped"]}},
            {"source_message_id": 1}
        )
        forwarded_ids = [doc["source_message_id"] for doc in forwarded_cursor]
        
        # 2. Query movies that are NOT in this list
        query = {
            "file_size": {"$lte": max_size},
            "message_id": {"$nin": forwarded_ids}
        }
        
        return self.db["movies"].find(query).sort("message_id", 1)
    
    def close(self):
        self.client.close()
