import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  
ENV_PATH = BASE_DIR / ".env"
print("CONFIG FILE:", __file__)
print("ENV PATH:", ENV_PATH)
print("ENV EXISTS:", ENV_PATH.exists())


load_dotenv(dotenv_path=ENV_PATH)

print("BOT_TOKEN =", os.getenv("BOT_TOKEN"))

def _required(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required env variable: {key}")
    return value

BOT_TOKEN = _required("BOT_TOKEN")
MODE = _required("MODE").upper()

if MODE not in ("TEST", "PROD"):
    raise RuntimeError("MODE must be TEST or PROD")

DB_CHANNEL_ID = int(
    _required("TEST_DB_CHANNEL_ID") if MODE == "TEST"
    else _required("PROD_DB_CHANNEL_ID")
)

CLIENT_CHANNEL_ID = int(
    _required("TEST_CLIENT_CHANNEL_ID") if MODE == "TEST"
    else _required("PROD_CLIENT_CHANNEL_ID")
)

ADMIN_USER_IDS = {
    int(x.strip())
    for x in _required("ADMIN_USER_IDS").split(",")
}

DB_TYPE = _required("DB_TYPE").lower()
DB_URI = _required("DB_URI")

AUTO_DELETE_SECONDS = int(
    os.getenv("AUTO_DELETE_SECONDS", "120")
)

TG_API_ID = int(_required("TG_API_ID"))
TG_API_HASH = _required("TG_API_HASH")

