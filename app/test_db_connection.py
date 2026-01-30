import sys
from pathlib import Path

# Add project root to python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.utils.config import DB_URI
from app.db.connection import get_db

print(f"TEST: DB_URI loaded: {DB_URI}")

try:
    db = get_db()
    print("TEST: Successfully connected to database")
    client = db.client
    print(f"TEST: Server info: {client.address}")
except Exception as e:
    print(f"TEST: Connection failed: {e}")
