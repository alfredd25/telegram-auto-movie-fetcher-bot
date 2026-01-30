from app.forwarder.state import ForwarderState

def clear_history():
    print("Connecting to DB...")
    state = ForwarderState()
    
    count = state.collection.count_documents({})
    print(f"Found {count} forwarded records.")
    
    if count == 0:
        print("Nothing to clear.")
        return

    confirm = input("Type 'yes' to clear all forwarding history (this allows re-forwarding): ")
    if confirm.lower() == 'yes':
        state.collection.delete_many({})
        print("History cleared! You can now run the forwarder to re-forward files.")
    else:
        print("Operation cancelled.")
        
    state.close()

if __name__ == "__main__":
    clear_history()
