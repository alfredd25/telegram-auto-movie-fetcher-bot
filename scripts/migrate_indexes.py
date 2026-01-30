
import sys
import os
from pymongo import ASCENDING

# Add app to path
sys.path.append(os.getcwd())

from app.db.connection import get_db
from app.db.models import MOVIES_COLLECTION

def migrate_indexes():
    print("🚀 Starting Index Migration...")
    db = get_db()
    movies = db[MOVIES_COLLECTION]
    
    # 1. Drop old index
    try:
        movies.drop_index("unique_file")
        print("✅ Dropped old index 'unique_file'")
    except Exception as e:
        print(f"⚠️ Could not drop 'unique_file' (might not exist): {e}")

    # 2. Create new index
    try:
        movies.create_index(
            [("file_unique_id", ASCENDING), ("channel_id", ASCENDING)],
            unique=True,
            name="unique_file_channel"
        )
        print("✅ Created new index 'unique_file_channel'")
    except Exception as e:
        print(f"❌ Failed to create new index: {e}")
        
    print("🏁 Migration Complete!")

if __name__ == "__main__":
    migrate_indexes()
