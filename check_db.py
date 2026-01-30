from app.forwarder.state import ForwarderState

def check_counts():
    print("Connecting to DB...")
    state = ForwarderState()
    
    movie_count = state.db["movies"].count_documents({})
    forwarded_count = state.collection.count_documents({})
    
    print(f"Total Movies in DB: {movie_count}")
    print(f"Total Forwarded Records: {forwarded_count}")
    
    # Check for pending efficiently-ish for this test
    # Get all forwarded IDs
    print("Fetching forwarded IDs...")
    forwarded_ids = set(doc["source_message_id"] for doc in state.collection.find({}, {"source_message_id": 1}))
    
    # Count movies not in forwarded_ids
    print("Checking pending movies...")
    pending_count = state.db["movies"].count_documents({"message_id": {"$nin": list(forwarded_ids)}})
    
    print(f"Pending Movies (Approx): {pending_count}")
    
    if pending_count > 0:
        print("First 5 pending IDs:")
        cursor = state.db["movies"].find({"message_id": {"$nin": list(forwarded_ids)}}).limit(5)
        for doc in cursor:
            print(f"- {doc.get('message_id')} : {doc.get('file_name', 'No Name')}")
            
    state.close()

if __name__ == "__main__":
    check_counts()
