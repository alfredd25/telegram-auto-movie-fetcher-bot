"""
Reset Index Progress Only
=========================
Clears the indexing progress so the scanner starts from message 0.
Run this when you want to re-index from the beginning.
"""

import pymongo
from urllib.parse import urlparse
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

DB_URI = os.getenv("DB_URI")
if not DB_URI:
    print("❌ Error: DB_URI not found in .env file")
    exit(1)

def main():
    print("=" * 50)
    print("Reset Indexing Progress")
    print("=" * 50)
    
    client = pymongo.MongoClient(DB_URI)
    parsed = urlparse(DB_URI)
    db_name = parsed.path.lstrip("/")
    db = client[db_name]
    
    print(f"\n📦 Connected to: {db_name}")
    
    # Show current progress entries
    print("\n📊 Current index progress entries:")
    progress_docs = list(db["config"].find({"_id": {"$regex": "^index_progress_"}}))
    
    if progress_docs:
        for doc in progress_docs:
            print(f"   - {doc['_id']}: message_id={doc.get('last_message_id', 'N/A')}")
    else:
        print("   (none found)")
    
    # Also check movies count
    movies_count = db["movies"].count_documents({})
    print(f"\n📽️  Movies in database: {movies_count}")
    
    if not progress_docs and movies_count == 0:
        print("\n✅ Already clean! Nothing to reset.")
        client.close()
        return
    
    confirm = input("\nType 'yes' to reset progress and clear movies: ").strip().lower()
    
    if confirm != "yes":
        print("❌ Aborted.")
        client.close()
        return
    
    # Clear progress
    result = db["config"].delete_many({"_id": {"$regex": "^index_progress_"}})
    print(f"\n🗑️  Deleted {result.deleted_count} progress entries")
    
    # Clear movies collection
    result = db["movies"].delete_many({})
    print(f"🗑️  Deleted {result.deleted_count} movie documents")
    
    client.close()
    
    print("\n✅ Done! Now run: python run_indexer.py")
    print("=" * 50)

if __name__ == "__main__":
    main()
