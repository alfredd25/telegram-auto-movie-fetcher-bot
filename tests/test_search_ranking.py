
import sys
import os
import asyncio
from pymongo import MongoClient
import logging

# Add app to path
sys.path.append(os.getcwd())

from app.db.queries import search_movies
from app.db.connection import get_db
from app.utils.config import MONGO_URI, DB_NAME

# Mock the collection name for testing
import app.db.queries
app.db.queries.MOVIES_COLLECTION = "test_movies_ranking"


# Redirect stdout to file
sys.stdout = open("test_output.txt", "w", encoding="utf-8")

async def test_ranking():
    print("🚀 Starting Search Ranking Verification...")
    
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["test_movies_ranking"]
    
    # 1. Clean up previous tests
    collection.drop()

    
    # 2. Insert Test Data
    # prioritizing "hit"
    test_data = [
        {"normalized_text": "shit", "file_name": "Shit.mkv", "message_id": 1, "channel_id": 1, "file_size": 100},              # Partial (Score 10)
        {"normalized_text": "hit", "file_name": "HIT.mkv", "message_id": 2, "channel_id": 1, "file_size": 100},               # Exact (Score 40)
        {"normalized_text": "white house", "file_name": "White House.mkv", "message_id": 3, "channel_id": 1, "file_size": 100}, # Partial (Score 10 or 0 depending on regex). 
                                                                                                                                # Note: "white house" does NOT contain "hit" with standard regex escape.
                                                                                                                                # We'll use "white hit" or "hitman" to test partials properly.
                                                                                                                                # "exhibit" contains "hit".
        {"normalized_text": "exhibit a", "file_name": "Exhibit A.mkv", "message_id": 3, "channel_id": 1, "file_size": 100},     # Partial (Score 10)
        {"normalized_text": "the hit list", "file_name": "The Hit List.mkv", "message_id": 4, "channel_id": 1, "file_size": 100}, # Word Boundary (Score 20)
        {"normalized_text": "hit 2", "file_name": "Hit 2.mkv", "message_id": 5, "channel_id": 1, "file_size": 100},             # Prefix (Score 30)
        {"normalized_text": "hitman", "file_name": "Hitman.mkv", "message_id": 6, "channel_id": 1, "file_size": 100},           # Partial (Score 10)
    ]
    
    collection.insert_many(test_data)
    print("✅ Inserted test data")
    
    # 3. Run Search
    results = search_movies("hit", limit=10, offset=0)
    
    # 4. Print Results
    print("\n🔍 Search Results for 'hit':")
    for idx, res in enumerate(results):
        print(f"   {idx+1}. {res['file_name']} (Score: {res.get('score', 'N/A')})")
        
    # 5. Assertions
    filenames = [r['file_name'] for r in results]
    
    # We expect:
    # 1. HIT (Exact - 40)
    # 2. Hit 2 (Prefix - 30)
    # 3. The Hit List (Word - 20)
    # 4. Exhibit A / Hitman / Shit (Partial - 10) -> Sorted by length then alpha
    
    # "HIT.mkv" (Exact)
    assert filenames[0] == "HIT.mkv", f"Expected HIT.mkv first, got {filenames[0]}"
    
    # "Hit 2.mkv" (Prefix)
    assert filenames[1] == "Hit 2.mkv", f"Expected Hit 2.mkv second, got {filenames[1]}"
    
    # "The Hit List.mkv" (Word)
    assert filenames[2] == "The Hit List.mkv", f"Expected The Hit List.mkv third, got {filenames[2]}"
    
    # Partials
    partials = filenames[3:]
    expected_partials = ["Shit.mkv", "Hitman.mkv", "Exhibit A.mkv"] # Sorted by length: Shit (4), Hitman (6), Exhibit A (9)
    # Wait, sort logic: score (-1), text_len (1), file_name (1)
    # "shit" len 4. "hitman" len 6. "exhibit a" len 9.
    # So order should be Shit, Hitman, Exhibit A.
    
    print(f"   Partials found: {partials}")
    assert "Shit.mkv" in partials, "Shit.mkv missing"
    assert "Hitman.mkv" in partials, "Hitman.mkv missing"
    assert "Exhibit A.mkv" in partials, "Exhibit A.mkv missing"
    
    assert partials[0] == "Shit.mkv", f"Expected Shit.mkv (shortest partial), got {partials[0]}"
    
    print("\n✅ RANKING LOGIC VERIFIED!")
    print("   Priority 4 (Exact): HIT")
    print("   Priority 3 (Prefix): Hit 2")
    print("   Priority 2 (Word): The Hit List")
    print("   Priority 1 (Partial): Shit (Shortest), Hitman, Exhibit A")

    # Clean up
    collection.drop()

if __name__ == "__main__":
    asyncio.run(test_ranking())
