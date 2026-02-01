"""
Reset MongoDB Collections Script
================================
Run this on the RDP server to clear all old collections
and prepare for fresh indexing from a new Telegram database.

Usage: python reset_collections.py
"""

import pymongo
from urllib.parse import urlparse

# Update this with your MongoDB connection string
DB_URI = "mongodb://telegram_movie_bot:gamenply@51.79.212.59:27017/telegram_movie_bot?authSource=telegram_movie_bot"

def main():
    print("=" * 60)
    print("MongoDB Collection Reset Script")
    print("=" * 60)
    
    # Connect to MongoDB
    client = pymongo.MongoClient(DB_URI)
    parsed = urlparse(DB_URI)
    db_name = parsed.path.lstrip("/")
    
    if not db_name:
        print("❌ Error: Could not parse database name from URI")
        return
    
    db = client[db_name]
    print(f"\n📦 Connected to database: {db_name}")
    
    # Show current collection stats
    print("\n📊 Current collection stats:")
    collections = ["movies", "forwarded_files", "config"]
    
    for coll_name in collections:
        try:
            count = db[coll_name].count_documents({})
            print(f"   - {coll_name}: {count} documents")
        except Exception as e:
            print(f"   - {coll_name}: 0 documents (collection doesn't exist yet - this is fine!)")
    
    # Confirm with user
    print("\n" + "=" * 60)
    print("⚠️  This will ensure all collections are clean for fresh indexing")
    print("=" * 60)
    
    confirm = input("\nType 'yes' to confirm: ").strip().lower()
    
    if confirm != "yes":
        print("\n❌ Aborted. No changes made.")
        client.close()
        return
    
    # Drop collections
    print("\n🗑️  Dropping collections...")
    
    # Drop movies collection
    try:
        db["movies"].drop()
        print("   ✅ Dropped 'movies' collection")
    except Exception as e:
        print(f"   ⚠️  Error dropping 'movies': {e}")
    
    # Drop forwarded_files collection
    try:
        db["forwarded_files"].drop()
        print("   ✅ Dropped 'forwarded_files' collection")
    except Exception as e:
        print(f"   ⚠️  Error dropping 'forwarded_files': {e}")
    
    # Clear indexing progress from config (but keep other config like ad_text)
    try:
        result = db["config"].delete_many({"_id": {"$regex": "^index_progress_"}})
        print(f"   ✅ Removed {result.deleted_count} indexing progress entries from 'config'")
    except Exception as e:
        print(f"   ⚠️  Error clearing config progress: {e}")
    
    # Close connection
    client.close()
    
    print("\n" + "=" * 60)
    print("✅ DONE! Collections have been reset.")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update your .env file with the new Telegram channel ID")
    print("2. Run: python run_indexer.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
